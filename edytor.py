import os
import uuid
import streamlit as st
import pandas as pd
from sqlalchemy import func, Integer
import config
import style
import exporter

# Importujemy modele oraz funkcje pomocnicze z db.py
from db import (
    get_session, 
    Question, 
    ProfessionGroup, 
    TestType, 
    UserRole, 
    SessionStatus, 
    ExamSession,
    QuestionAttempt
)
from importer import import_questions_from_package

def save_uploaded_file(uploaded_file):
    """Pomocnicza funkcja do zapisu plików graficznych."""
    if uploaded_file is not None:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        upload_dir = os.path.join(base_dir, config.IMAGE_PATH)
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir, exist_ok=True)
            
        ext = uploaded_file.name.split('.')[-1]
        filename = f"{uuid.uuid4()}.{ext}"
        filepath = os.path.join(upload_dir, filename)
        with open(filepath, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return os.path.join(config.IMAGE_PATH, filename)
    return None

def show_editor_ui():
    """Główny interfejs edytora bazy pytań."""
    style.apply_custom_css()
    st.title("🛠️ Edytor Bazy Pytań")
    
    session = get_session()
    user_role = st.session_state.get("user_role", UserRole.USER)

    # Pre-fetching danych
    all_professions = session.query(ProfessionGroup).all()
    all_test_types = session.query(TestType).all()
    all_questions = session.query(Question).all()
    
    prof_options = {p.name: p for p in all_professions}
    type_options = {t.name: t for t in all_test_types}
    
    # Budowa menu na podstawie ról
    menu = []
    if user_role in [UserRole.USER, UserRole.ADMIN]:
        menu.extend(["Dodaj nowe pytanie", "Edytuj / Usuń istniejące", "🚀 Masowy Import"])
    
    menu.extend(["Tabela pytań", "📥 Eksport Bazy"])
    
    if user_role in [UserRole.EXAMINER, UserRole.ADMIN]:
        menu.append("🎓 SESJA EGZAMINACYJNA")
    
    choice = st.sidebar.selectbox("Wybierz moduł", menu)

    # --- 1. DODAWANIE NOWEGO PYTANIA ---
    if choice == "Dodaj nowe pytanie":
        st.subheader("🆕 Nowe pytanie")
        with st.form("add_question_form", clear_on_submit=True):
            q_col1, q_col2 = st.columns([2, 1])
            with q_col1:
                content = st.text_area("Treść", placeholder="Wpisz treść pytania...")
            with q_col2:
                img_q = st.file_uploader("Obraz główny", type=config.ALLOWED_EXTENSIONS)

            st.divider()
            ans_data = {}
            for label in ["A", "B", "C"]:
                col_txt, col_img = st.columns([2, 1])
                with col_txt:
                    ans_data[f'txt_{label}'] = st.text_input(f"Odpowiedź {label}")
                with col_img:
                    ans_data[f'img_{label}'] = st.file_uploader(f"Grafika {label}", type=config.ALLOWED_EXTENSIONS, key=f"add_img_{label}")

            st.divider()
            col_m1, col_m2 = st.columns(2)
            with col_m1:
                correct_ans = st.selectbox("Poprawna", ["A", "B", "C"])
                selected_profs = st.multiselect("Grupy zawodowe", list(prof_options.keys()))
            with col_m2:
                selected_types = st.multiselect("Rodzaj testu", list(type_options.keys()))
                comment = st.text_area("Komentarz dydaktyczny")
            
            if st.form_submit_button("ZAPISZ PYTANIE", type="primary", use_container_width=True):
                if content or img_q:
                    new_q = Question(
                        content=content, ans_a=ans_data['txt_A'], ans_b=ans_data['txt_B'], ans_c=ans_data['txt_C'],
                        correct_ans=correct_ans, image_path=save_uploaded_file(img_q),
                        image_a=save_uploaded_file(ans_data['img_A']), image_b=save_uploaded_file(ans_data['img_B']),
                        image_c=save_uploaded_file(ans_data['img_C']), comment=comment
                    )
                    new_q.professions = [prof_options[name] for name in selected_profs]
                    new_q.test_types = [type_options[name] for name in selected_types]
                    session.add(new_q)
                    session.commit()
                    st.success("Dodano pomyślnie!")
                    st.rerun()

    # --- 2. EDYCJA / USUWANIE ---
    elif choice == "Edytuj / Usuń istniejące":
        st.subheader("✏️ Zarządzanie pytaniami")
        q_list = {f"ID {q.id}: {q.content[:60]}...": q for q in all_questions}
        selected_q_label = st.selectbox("Wybierz pytanie", [""] + list(q_list.keys()))
        if selected_q_label:
            q = q_list[selected_q_label]
            with st.form("edit_question_form"):
                e_q_col1, e_q_col2 = st.columns([2, 1])
                with e_q_col1:
                    new_content = st.text_area("Treść", value=q.content)
                with e_q_col2:
                    if q.image_path:
                        style.st_responsive_image(q.image_path, caption="Obecny obraz", width_percent=0.8)
                    new_img_q = st.file_uploader("Zmień obraz", type=config.ALLOWED_EXTENSIONS)
                st.divider()
                new_ans = {}
                for lbl, f_txt, f_img in [("A", q.ans_a, q.image_a), ("B", q.ans_b, q.image_b), ("C", q.ans_c, q.image_c)]:
                    c_txt, c_img = st.columns([2, 1])
                    with c_txt:
                        new_ans[f'txt_{lbl}'] = st.text_input(f"Odp {lbl}", value=f_txt if f_txt else "")
                    with c_img:
                        if f_img:
                            st.image(f_img, width=100)
                        new_ans[f'img_{lbl}'] = st.file_uploader(f"Grafika {lbl}", type=config.ALLOWED_EXTENSIONS, key=f"edit_img_{lbl}")
                st.divider()
                col_m1, col_m2 = st.columns(2)
                with col_m1:
                    new_correct = st.selectbox("Poprawna", ["A", "B", "C"], index=["A", "B", "C"].index(q.correct_ans))
                    new_profs = st.multiselect("Grupy", list(prof_options.keys()), default=[p.name for p in q.professions])
                with col_m2:
                    new_types = st.multiselect("Rodzaje", list(type_options.keys()), default=[t.name for t in q.test_types])
                    new_comment = st.text_area("Komentarz", value=q.comment if q.comment else "")
                
                col_b1, col_b2 = st.columns(2)
                if col_b1.form_submit_button("ZAKTUALIZUJ", type="primary", use_container_width=True):
                    q.content, q.correct_ans, q.comment = new_content, new_correct, new_comment
                    q.ans_a, q.ans_b, q.ans_c = new_ans['txt_A'], new_ans['txt_B'], new_ans['txt_C']
                    if new_img_q:
                        q.image_path = save_uploaded_file(new_img_q)
                    if new_ans['img_A']:
                        q.image_a = save_uploaded_file(new_ans['img_A'])
                    if new_ans['img_B']:
                        q.image_b = save_uploaded_file(new_ans['img_B'])
                    if new_ans['img_C']:
                        q.image_c = save_uploaded_file(new_ans['img_C'])
                    q.professions = [prof_options[name] for name in new_profs]
                    q.test_types = [type_options[name] for name in new_types]
                    session.commit()
                    st.success("Zapisano zmiany.")
                    st.rerun()
                if col_b2.form_submit_button("USUŃ", use_container_width=True):
                    session.delete(q)
                    session.commit()
                    st.warning("Usunięto.")
                    st.rerun()

    # --- 3. TABELA PYTAŃ ---
    elif choice == "Tabela pytań":
        st.subheader("📊 Analityka Pytania vs Sesja")
        
        # 1. Pobranie sesji do filtra
        all_sessions = session.query(ExamSession).filter_by(status=SessionStatus.FINISHED).all()
        session_map = {s.training_number: s.id for s in all_sessions}
        
        f_col1, f_col2, f_col3 = st.columns(3)
        with f_col1:
            sel_prof = st.selectbox("Zawód:", ["Wszystkie"] + list(prof_options.keys()))
        with f_col2:
            sel_type = st.selectbox("Rodzaj:", ["Wszystkie"] + list(type_options.keys()))
        with f_col3:
            sel_session = st.selectbox("Numer Szkolenia:", ["Globalne (Wszystkie)"] + list(session_map.keys()))

        # 2. Agregacja danych
        from sqlalchemy import func
        from db import QuestionAttempt

        if sel_session == "Globalne (Wszystkie)":
            # Logika oparta na licznikach w Question
            query = session.query(Question)
            if sel_prof != "Wszystkie":
                query = query.filter(Question.professions.any(id=prof_options[sel_prof].id))
            if sel_type != "Wszystkie":
                query = query.filter(Question.test_types.any(id=type_options[sel_type].id))
            questions = query.all()
            
            results = []
            for q in questions:
                rate = (q.correct_attempts / q.total_attempts * 100) if q.total_attempts > 0 else 0.0
                results.append({
                    "ID": q.id, "Pytanie": q.content, "Próby": q.total_attempts, 
                    "Zdawalność": rate, "Sesja": "Globalna"
                })
        else:
            # DYNAMICZNA ANALIZA SESJI z QuestionAttempt
            target_session_id = session_map[sel_session]
            # Agregujemy poprawne/wszystkie dla tej sesji
            stats = session.query(
                QuestionAttempt.question_id,
                func.count(QuestionAttempt.id).label('total'),
                func.sum(func.cast(QuestionAttempt.is_correct, Integer)).label('correct')
            ).filter(QuestionAttempt.session_id == target_session_id).group_by(QuestionAttempt.question_id).all()
            
            results = []
            for q_id, total, correct in stats:
                q = session.query(Question).get(q_id)
                rate = (correct / total * 100) if total > 0 else 0.0
                results.append({
                    "ID": q.id, "Pytanie": q.content, "Próby": total, 
                    "Zdawalność": rate, "Sesja": sel_session
                })

        # 3. Renderowanie tabeli
        if results:
            df = pd.DataFrame(results)
            st.dataframe(df, column_config={
                "Zdawalność": st.column_config.ProgressColumn("Skuteczność", format="%.2f%%", min_value=0, max_value=100)
            }, use_container_width=True, hide_index=True)
        else:
            st.info("Brak danych dla wybranych filtrów.")

    # --- 4. MASOWY IMPORT ---
    elif choice == "🚀 Masowy Import":
        st.subheader("🚀 Masowy Import")
        excel_file = st.file_uploader("Excel (.xlsx)", type=["xlsx"])
        zip_file = st.file_uploader("Zdjęcia (.zip)", type=["zip"])
        if st.button("IMPORTUJ", type="primary"):
            if excel_file:
                success, msg = import_questions_from_package(excel_file, zip_file)
                st.success(msg) if success else st.error(msg)
            else:
                st.error("Brak pliku Excel!")

    # --- 5. EKSPORT BAZY ---
    elif choice == "📥 Eksport Bazy":
        st.subheader("📥 Eksport bazy")
        ex_profs = st.multiselect("Filtruj grupy zawodowe", list(prof_options.keys()))
        ex_types = st.multiselect("Filtruj rodzaje testu", list(type_options.keys()))
        if st.button("PRZYGOTUJ EKSPORT", type="primary"):
            p_ids = [prof_options[n].id for n in ex_profs] if ex_profs else None
            t_ids = [type_options[n].id for n in ex_types] if ex_types else None
            result, message = exporter.export_questions_to_zip(p_ids, t_ids)
            if result:
                buf, fname = result
                st.download_button("💾 POBIERZ ZIP", buf, fname, "application/zip", use_container_width=True)

    # --- 6. SESJA EGZAMINACYJNA ---
    elif choice == "🎓 SESJA EGZAMINACYJNA":
        try:
            from examiner_panel import show_exam_session_manager
            show_exam_session_manager(session)
        except ImportError:
            st.error("Moduł examiner_panel nie został jeszcze utworzony.")
    
    session.close()