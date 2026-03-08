import streamlit as st
import pandas as pd
import os
import uuid
import config
import style  # <--- NASZ NOWY MODUŁ STYLÓW
from db import get_session, Question, ProfessionGroup, TestType
from importer import run_mass_import

def save_uploaded_file(uploaded_file):
    """Pomocnicza funkcja do zapisu plików graficznych."""
    if uploaded_file is not None:
        if not os.path.exists("uploads"):
            os.makedirs("uploads")
        ext = uploaded_file.name.split('.')[-1]
        filename = f"{uuid.uuid4()}.{ext}"
        filepath = os.path.join("uploads", filename)
        with open(filepath, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return filepath
    return None

def show_editor_ui():
    # 1. Aplikujemy pastelowe style i kontrastowe napisy
    style.apply_custom_css()
    
    st.title("🛠️ Edytor Bazy Pytań")
    
    session = get_session()
    
    # Pobranie danych do filtrów i list
    all_professions = session.query(ProfessionGroup).all()
    all_test_types = session.query(TestType).all()
    all_questions = session.query(Question).all()
    
    prof_options = {p.name: p for p in all_professions}
    type_options = {t.name: t for t in all_test_types}

    # Menu boczne (Pastelowe przyciski dzięki style.py)
    menu = ["Dodaj nowe pytanie", "Edytuj / Usuń istniejące", "Tabela pytań", "🚀 Masowy Import"]
    choice = st.sidebar.selectbox("Menu Edytora", menu)

    # --- LOGIKA: DODAWANIE NOWEGO PYTANIA ---
    if choice == "Dodaj nowe pytanie":
        st.subheader("🆕 Nowe pytanie")
        
        with st.form("add_question_form", clear_on_submit=True):
            q_col1, q_col2 = st.columns([2, 1])
            with q_col1:
                content = st.text_area("Treść pytania", placeholder="Wpisz treść pytania...")
            with q_col2:
                img_q = st.file_uploader("Obraz główny", type=config.ALLOWED_EXTENSIONS)

            st.divider()
            st.write("**Opcje odpowiedzi:**")
            
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
                correct_ans = st.selectbox("Poprawna odpowiedź", ["A", "B", "C"])
                selected_profs = st.multiselect("Grupy zawodowe", list(prof_options.keys()))
            with col_m2:
                selected_types = st.multiselect("Rodzaj testu", list(type_options.keys()))
                comment = st.text_area("Komentarz dydaktyczny")
            
            # Przycisk typu primary - będzie zielony pastelowy
            submitted = st.form_submit_button("ZAPISZ PYTANIE W BAZIE", type="primary", use_container_width=True)
            
            if submitted:
                if content or img_q:
                    new_q = Question(
                        content=content,
                        ans_a=ans_data['txt_A'],
                        ans_b=ans_data['txt_B'],
                        ans_c=ans_data['txt_C'],
                        correct_ans=correct_ans,
                        image_path=save_uploaded_file(img_q), # Zgodnie z modelem image_path
                        image_a=save_uploaded_file(ans_data['img_A']),
                        image_b=save_uploaded_file(ans_data['img_B']),
                        image_c=save_uploaded_file(ans_data['img_C']),
                        comment=comment
                    )
                    new_q.professions = [prof_options[name] for name in selected_profs]
                    new_q.test_types = [type_options[name] for name in selected_types]
                    
                    session.add(new_q)
                    session.commit()
                    st.success("Pytanie zostało pomyślnie dodane!")
                    st.rerun()

    # --- LOGIKA: EDYCJA / USUWANIE ---
    elif choice == "Edytuj / Usuń istniejące":
        st.subheader("✏️ Zarządzanie pytaniami")
        q_list = {f"ID {q.id}: {q.content[:60]}...": q for q in all_questions}
        selected_q_label = st.selectbox("Wybierz pytanie do modyfikacji", [""] + list(q_list.keys()))
        
        if selected_q_label:
            q = q_list[selected_q_label]
            
            with st.form("edit_question_form"):
                e_q_col1, e_q_col2 = st.columns([2, 1])
                with e_q_col1:
                    new_content = st.text_area("Treść", value=q.content)
                with e_q_col2:
                    if q.image_path:
                        # Responsywny podgląd (40% szerokości w kolumnie)
                        style.st_responsive_image(q.image_path, caption="Obecny obraz", width_percent=0.8)
                    new_img_q = st.file_uploader("Zmień obraz główny", type=config.ALLOWED_EXTENSIONS)

                st.divider()
                
                new_ans = {}
                for label, field_txt, field_img in [("A", q.ans_a, q.image_a), ("B", q.ans_b, q.image_b), ("C", q.ans_c, q.image_c)]:
                    c_txt, c_img = st.columns([2, 1])
                    with c_txt:
                        new_ans[f'txt_{label}'] = st.text_input(f"Odp {label}", value=field_txt if field_txt else "")
                    with c_img:
                        if field_img:
                            st.image(field_img, width=100)
                        new_ans[f'img_{label}'] = st.file_uploader(f"Zmień grafikę {label}", type=config.ALLOWED_EXTENSIONS, key=f"edit_img_{label}")

                st.divider()

                col_m1, col_m2 = st.columns(2)
                with col_m1:
                    new_correct = st.selectbox("Poprawna", ["A", "B", "C"], index=["A", "B", "C"].index(q.correct_ans))
                    new_profs = st.multiselect("Grupy", list(prof_options.keys()), default=[p.name for p in q.professions])
                with col_m2:
                    new_types = st.multiselect("Rodzaje", list(type_options.keys()), default=[t.name for t in q.test_types])
                    new_comment = st.text_area("Komentarz", value=q.comment if q.comment else "")

                col_b1, col_b2 = st.columns(2)
                if col_b1.form_submit_button("ZAKTUALIZUJ DANE", type="primary", use_container_width=True):
                    q.content = new_content
                    q.ans_a, q.ans_b, q.ans_c = new_ans['txt_A'], new_ans['txt_B'], new_ans['txt_C']
                    q.correct_ans = new_correct
                    q.comment = new_comment
                    
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
                    st.success("Zmiany zostały zapisane.")
                    st.rerun()

                # Przycisk Usuń będzie pastelowy czerwony dzięki CSS w style.py
                if col_b2.form_submit_button("USUŃ PYTANIE", use_container_width=True):
                    session.delete(q)
                    session.commit()
                    st.warning("Pytanie zostało usunięte z bazy.")
                    st.rerun()

    # --- LOGIKA: TABELA PYTAŃ ---
    elif choice == "Tabela pytań":
        st.subheader("📊 Statystyki zdawalności pytań")
        type_names = ["Wszystkie"] + [t.name for t in all_test_types]
        selected_type_name = st.selectbox("Filtruj według rodzaju testu:", type_names)

        query = session.query(Question)
        if selected_type_name != "Wszystkie":
            selected_type_obj = type_options[selected_type_name]
            query = query.filter(Question.test_types.any(id=selected_type_obj.id))
        
        filtered_questions = query.all()

        if filtered_questions:
            data = []
            for q in filtered_questions:
                calc_pass_rate = (q.correct_attempts / q.total_attempts * 100) if q.total_attempts > 0 else 0.0
                data.append({
                    "ID": q.id,
                    "Pytanie": q.content,
                    "Użyć": q.total_attempts,
                    "Zdawalność": calc_pass_rate
                })
            
            df = pd.DataFrame(data)
            st.dataframe(
                df,
                column_config={
                    "Pytanie": st.column_config.TextColumn("Treść pytania", width="large"),
                    "Użyć": st.column_config.NumberColumn("Podejścia", format="%d"),
                    "Zdawalność": st.column_config.NumberColumn("Zdawalność (%)", format="%.2f%%"),
                },
                use_container_width=True,
                hide_index=True
            )

            st.divider()
            st.write("### ⚠️ Administracja statystykami")
            num_q = len(filtered_questions)
            
            if st.button(f"Zresetuj statystyki dla {num_q} pytań", type="secondary"):
                st.session_state.confirm_reset = True

            if st.session_state.get("confirm_reset", False):
                st.warning(f"Czy na pewno wyzerować dane dla kategorii '{selected_type_name}'?")
                c1, c2 = st.columns(2)
                if c1.button("TAK, RESETUJ", type="primary", use_container_width=True):
                    for q in filtered_questions:
                        q.total_attempts = 0
                        q.correct_attempts = 0
                        q.pass_rate = 0.0
                    session.commit()
                    st.session_state.confirm_reset = False
                    st.success("Zresetowano pomyślnie.")
                    st.rerun()
                if c2.button("ANULUJ", use_container_width=True):
                    st.session_state.confirm_reset = False
                    st.rerun()
        else:
            st.info("Brak pytań w tej kategorii.")

    # --- LOGIKA: MASOWY IMPORT ---
    elif choice == "🚀 Masowy Import":
        st.subheader("🚀 Masowy Import (XLSX + ZIP)")
        st.info("Przygotuj plik Excel z kolumnami oraz paczkę ZIP ze zdjęciami.")
    
        col1, col2 = st.columns(2)
        with col1:
            excel_file = st.file_uploader("Plik Excel (.xlsx)", type=["xlsx"])
        with col2:
            zip_file = st.file_uploader("Paczka zdjęć (.zip)", type=["zip"])
        
        if st.button("URUCHOM IMPORT", type="primary", use_container_width=True):
            if excel_file and zip_file:
                with st.spinner("Przetwarzanie danych..."):
                    summary = run_mass_import(excel_file, zip_file, session)
                    st.success(f"Import zakończony! Sukcesy: {summary['success']}, Błędy: {summary['errors']}")
                    st.rerun()
            else:
                st.error("Wymagane oba pliki do poprawnego importu!")

    session.close()