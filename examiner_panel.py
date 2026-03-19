import streamlit as st
import pandas as pd
import secrets
import re
from datetime import datetime, combine
from db import get_session, ExamSession, Examinee, ProfessionGroup, TestType, SessionStatus, User
import config

def generate_access_token():
    """Generuje bezpieczny, unikalny token dostępu dla egzaminowanego."""
    return secrets.token_urlsafe(16)

def validate_training_number(text):
    """Walidacja numeru szkolenia: max 25 znaków, dopuszczalne: alfanumeryczne, -, /, \\."""
    pattern = r'^[a-zA-Z0-9\-\/\\ ]{1,25}$'
    return re.match(pattern, text) is not None

def show_examiner_ui():
    """Główny interfejs panelu egzaminatora."""
    st.subheader("🎓 Panel Zarządzania Sesjami Egzaminacyjnymi")
    
    session = get_session()
    # Pobieramy ID aktualnie zalogowanego egzaminatora z sesji Streamlit
    user_id = st.session_state.get("user_id")
    user = session.query(User).get(user_id)
    
    if not user:
        st.error("Błąd autoryzacji. Zaloguj się ponownie.")
        return

    # Filtrowanie grup zawodowych, do których egzaminator ma uprawnienia
    managed_profs = user.managed_professions
    if not managed_profs:
        st.warning("Nie masz przypisanych żadnych grup zawodowych. Skontaktuj się z administratorem.")
        return

    tab1, tab2 = st.tabs(["🆕 Utwórz Sesję", "📋 Lista i Wyniki Sesji"])

    # --- TAB 1: TWORZENIE NOWEJ SESJI ---
    with tab1:
        with st.form("create_session_form"):
            st.write("### Parametry nowego egzaminu")
            
            t_col1, t_col2 = st.columns(2)
            with t_col1:
                training_num = st.text_input("Numer szkolenia / egzaminu", help="Max 25 znaków: A-Z, 0-9, -, /, \\")
                prof_names = [p.name for p in managed_profs]
                selected_prof_name = st.selectbox("Grupa zawodowa (zawód)", prof_names)
            with t_col2:
                all_types = session.query(TestType).all()
                type_names = [t.name for t in all_types]
                selected_types = st.multiselect("Rodzaje testów w sesji", type_names)

            st.divider()
            
            p_col1, p_col2, p_col3 = st.columns(3)
            with p_col1:
                q_count = st.number_input("Ilość pytań", min_value=1, max_value=100, value=20)
                threshold = st.slider("Próg zdawalności (%)", 0, 100, 80)
            with p_col2:
                time_lim = st.number_input("Limit czasu (minuty)", min_value=1, max_value=240, value=30)
                focus_lim = st.number_input("Limit opuszczenia okna", min_value=0, max_value=999, value=3)
            with p_col3:
                show_err = st.checkbox("Pokaż błędy po teście", value=True)
                show_comm = st.checkbox("Pokaż komentarz dydaktyczny", value=True)

            st.divider()
            
            d_col1, d_col2 = st.columns(2)
            with d_col1:
                start_date = st.date_input("Data rozpoczęcia", datetime.now())
                start_time = st.time_input("Godzina rozpoczęcia", datetime.now().time())
            with d_col2:
                journal_input = st.text_area("Numery z dziennika (rozdzielone przecinkiem)", 
                                           placeholder="np. 1, 2, 3, 4, 5")

            if st.form_submit_button("✅ UTWÓRZ SESJĘ I GENERUJ TOKENY", type="primary", use_container_width=True):
                # Walidacje
                if not validate_training_number(training_num):
                    st.error("Nieprawidłowy numer szkolenia (niedozwolone znaki lub za długi tekst).")
                elif not selected_types:
                    st.error("Wybierz przynajmniej jeden rodzaj testu.")
                elif not journal_input.strip():
                    st.error("Wprowadź numery z dziennika.")
                else:
                    try:
                        # 1. Tworzenie sesji
                        new_session = ExamSession(
                            training_number=training_num,
                            profession_id=next(p.id for p in managed_profs if p.name == selected_prof_name),
                            question_count=q_count,
                            pass_threshold=threshold,
                            time_limit=time_lim,
                            max_focus_loss=focus_lim,
                            show_errors=show_err,
                            show_comment=show_comm,
                            scheduled_start=combine(start_date, start_time),
                            examiner_id=user.id,
                            status=SessionStatus.PLANNED
                        )
                        # Dodanie typów testów
                        target_types = session.query(TestType).filter(TestType.name.in_(selected_types)).all()
                        new_session.test_types = target_types
                        session.add(new_session)
                        session.flush()

                        # 2. Tworzenie kont technicznych dla uczestników
                        journals = [int(x.strip()) for x in journal_input.split(',') if x.strip().isdigit()]
                        for j_num in journals:
                            examinee = Examinee(
                                session_id=new_session.id,
                                journal_number=j_num,
                                access_token=generate_access_token()
                            )
                            session.add(examinee)
                        
                        session.commit()
                        st.success(f"Sesja {training_num} została utworzona pomyślnie!")
                        st.rerun()
                    except Exception as e:
                        session.rollback()
                        st.error(f"Błąd bazy danych: {str(e)}")

    # --- TAB 2: LISTA SESJI I WYNIKI ---
    with tab2:
        # Widzimy sesje tylko dla zawodów, którymi zarządzamy
        managed_prof_ids = [p.id for p in managed_profs]
        sessions = session.query(ExamSession).filter(ExamSession.profession_id.in_(managed_prof_ids)).order_by(ExamSession.scheduled_start.desc()).all()
        
        if not sessions:
            st.info("Brak utworzonych sesji egzaminacyjnych.")
        else:
            for s in sessions:
                with st.expander(f"📌 {s.training_number} | {s.status.value} | Start: {s.scheduled_start.strftime('%Y-%m-%d %H:%M')}"):
                    c1, c2, c3 = st.columns([2, 1, 1])
                    with c1:
                        st.write(f"**Zawód:** {session.query(ProfessionGroup).get(s.profession_id).name}")
                        st.write(f"**Kategorie:** {', '.join([t.name for t in s.test_types])}")
                    with c2:
                        # Zarządzanie statusem
                        if s.status == SessionStatus.PLANNED:
                            if st.button("▶️ Aktywuj Egzamin", key=f"act_{s.id}"):
                                s.status = SessionStatus.ACTIVE
                                session.commit()
                                st.rerun()
                        elif s.status == SessionStatus.ACTIVE:
                            if st.button("⏹️ Zakończ Sesję", key=f"fin_{s.id}"):
                                s.status = SessionStatus.FINISHED
                                s.actual_end = datetime.now()
                                session.commit()
                                st.rerun()
                    with c3:
                        if s.status == SessionStatus.FINISHED:
                            st.button("📄 Pobierz Raport PDF", key=f"pdf_{s.id}")

                    # Tabela uczestników
                    st.write("### Lista uczestników i wyniki")
                    part_data = []
                    with st.expander("Zarządzanie uczestnikami"):
                        for e in s.examinees:
                            col_j, col_st, col_act = st.columns([1, 2, 2])
                            col_j.write(f"Dziennik: {e.journal_number}")
                            col_st.write("W trakcie 📝" if e.is_active else ("Zakończył ✅" if e.is_finished else "Oczekuje 💤"))
                            
                            # RESET UCZESTNIKA (Jeśli jest zablokowany lub aktywny)
                            if e.is_active or (not e.is_finished and e.start_datetime):
                                if col_act.button("🔓 Odblokuj / Reset", key=f"res_{e.id}", help="Umożliwia ponowne zalogowanie uczestnika"):
                                    e.is_active = False
                                    # Opcjonalnie: e.focus_loss_counter = 0 
                                    session.commit()
                                    st.toast(f"Zresetowano dostęp dla numeru {e.journal_number}")
                                    st.rerun()

                    # PRZYCISK RAPORTU (Widoczny gdy sesja jest zakończona)
                    if s.status == SessionStatus.FINISHED:
                        import report_service
                        pdf_report = report_service.generate_session_report(s, user)
                        st.download_button(
                            label="📥 Pobierz oficjalny Raport PDF",
                            data=pdf_report,
                            file_name=f"Raport_Egzamin_{s.training_number}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                    
                    st.table(pd.DataFrame(part_data))
                    
                    if s.status == SessionStatus.ACTIVE:
                        st.info("Przekaż uczestnikom ich tokeny dostępu, aby mogli rozpocząć egzamin.")

    session.close()