import streamlit as st
import pandas as pd
import os
import uuid
import config
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
    st.title("🛠️ Edytor Bazy Pytań")
    
    session = get_session()
    
    all_professions = session.query(ProfessionGroup).all()
    all_test_types = session.query(TestType).all()
    all_questions = session.query(Question).all()
    
    prof_options = {p.name: p for p in all_professions}
    type_options = {t.name: t for t in all_test_types}

    menu = ["Dodaj nowe pytanie", "Edytuj / Usuń istniejące" , "Tabela pytań", "🚀 Masowy Import"]
    choice = st.sidebar.selectbox("Menu Edytora", menu)

    # --- LOGIKA: DODAWANIE NOWEGO PYTANIA ---
    if choice == "Dodaj nowe pytanie":
        st.subheader("Nowe pytanie")
        
        with st.form("add_question_form", clear_on_submit=True):
            # 1. Treść pytania i obraz do pytania
            q_col1, q_col2 = st.columns([2, 1])
            with q_col1:
                content = st.text_area("Treść pytania")
            with q_col2:
                img_q = st.file_uploader("Obraz do pytania", type=config.ALLOWED_EXTENSIONS, key="add_img_q")

            st.divider()
            
            # 2. Odpowiedzi A, B, C z obrazami
            st.write("**Opcje odpowiedzi (Tekst i/lub Obraz):**")
            
            ans_data = {}
            for label in ["A", "B", "C"]:
                col_txt, col_img = st.columns([2, 1])
                with col_txt:
                    ans_data[f'txt_{label}'] = st.text_input(f"Odpowiedź {label}")
                with col_img:
                    ans_data[f'img_{label}'] = st.file_uploader(f"Obraz {label}", type=config.ALLOWED_EXTENSIONS, key=f"add_img_{label}")

            st.divider()
            
            # 3. Metadane
            col_m1, col_m2 = st.columns(2)
            with col_m1:
                correct_ans = st.selectbox("Poprawna odpowiedź", ["A", "B", "C"])
                selected_profs = st.multiselect("Grupy zawodowe", list(prof_options.keys()))
            with col_m2:
                selected_types = st.multiselect("Rodzaj testu", list(type_options.keys()))
                comment = st.text_area("Komentarz / Przepis")
            
            submitted = st.form_submit_button("Zapisz pytanie")
            
            if submitted:
                if content or img_q: # Pytanie musi mieć albo tekst, albo obraz
                    new_q = Question(
                        content=content,
                        ans_a=ans_data['txt_A'],
                        ans_b=ans_data['txt_B'],
                        ans_c=ans_data['txt_C'],
                        correct_ans=correct_ans,
                        image_q=save_uploaded_file(img_q),
                        image_a=save_uploaded_file(ans_data['img_A']),
                        image_b=save_uploaded_file(ans_data['img_B']),
                        image_c=save_uploaded_file(ans_data['img_C']),
                        comment=comment
                    )
                    new_q.professions = [prof_options[name] for name in selected_profs]
                    new_q.test_types = [type_options[name] for name in selected_types]
                    
                    session.add(new_q)
                    session.commit()
                    st.success("Pytanie dodane!")
                    st.rerun()

    # --- LOGIKA: EDYCJA / USUWANIE ---
    elif choice == "Edytuj / Usuń istniejące":
        st.subheader("Zarządzaj pytaniami")
        q_list = {f"ID {q.id}: {q.content[:50]}...": q for q in all_questions}
        selected_q_label = st.selectbox("Wybierz do edycji", [""] + list(q_list.keys()))
        
        if selected_q_label:
            q = q_list[selected_q_label]
            
            with st.form("edit_question_form"):
                # Edycja treści i obrazu pytania
                e_q_col1, e_q_col2 = st.columns([2, 1])
                with e_q_col1:
                    new_content = st.text_area("Treść", value=q.content)
                with e_q_col2:
                    if q.image_path: st.image(q.image_path, width=100)
                    new_img_q = st.file_uploader("Zmień obraz pytania", type=config.ALLOWED_EXTENSIONS)

                st.divider()
                
                # Edycja odpowiedzi
                new_ans = {}
                for label, field_txt, field_img in [("A", q.ans_a, q.image_a), ("B", q.ans_b, q.image_b), ("C", q.ans_c, q.image_c)]:
                    c_txt, c_img = st.columns([2, 1])
                    with c_txt:
                        new_ans[f'txt_{label}'] = st.text_input(f"Odp {label}", value=field_txt if field_txt else "")
                    with c_img:
                        if field_img: st.image(field_img, width=80)
                        new_ans[f'img_{label}'] = st.file_uploader(f"Zmień obraz {label}", type=config.ALLOWED_EXTENSIONS, key=f"edit_img_{label}")

                st.divider()

                # Metadane
                new_correct = st.selectbox("Poprawna", ["A", "B", "C"], index=["A", "B", "C"].index(q.correct_ans))
                new_profs = st.multiselect("Grupy", list(prof_options.keys()), default=[p.name for p in q.professions])
                new_types = st.multiselect("Rodzaje", list(type_options.keys()), default=[t.name for t in q.test_types])
                new_comment = st.text_area("Komentarz", value=q.comment if q.comment else "")

                col_b1, col_b2 = st.columns(2)
                if col_b1.form_submit_button("Zaktualizuj"):
                    q.content = new_content
                    q.ans_a, q.ans_b, q.ans_c = new_ans['txt_A'], new_ans['txt_B'], new_ans['txt_C']
                    q.correct_ans = new_correct
                    q.comment = new_comment
                    
                    if new_img_q: q.image_path = save_uploaded_file(new_img_q)
                    if new_ans['img_A']: q.image_a = save_uploaded_file(new_ans['img_A'])
                    if new_ans['img_B']: q.image_b = save_uploaded_file(new_ans['img_B'])
                    if new_ans['img_C']: q.image_c = save_uploaded_file(new_ans['img_C'])
                    
                    q.professions = [prof_options[name] for name in new_profs]
                    q.test_types = [type_options[name] for name in new_types]
                    session.commit()
                    st.success("Zapisano zmiany!")
                    st.rerun()

                if col_b2.form_submit_button("USUŃ", type="primary"):
                    session.delete(q)
                    session.commit()
                    st.rerun()
    # --- LOGIKA: TABELA PYTAŃ (NASZ NOWY KROK) ---
    elif choice == "Tabela pytań":
        st.subheader("📊 Tabela statystyk i zdawalności")
        # 1. FILTRACJA: Rodzaj testu
        type_names = ["Wszystkie"] + [t.name for t in all_test_types]
        selected_type_name = st.selectbox("Filtruj według rodzaju testu:", type_names)

        # 2. LOGIKA FILTROWANIA ZAPYTANIA
        query = session.query(Question)
        if selected_type_name != "Wszystkie":
            selected_type_obj = type_options[selected_type_name]
            query = query.filter(Question.test_types.any(id=selected_type_obj.id))
        
        filtered_questions = query.all()

        # 3. WYŚWIETLANIE TABELI
        if filtered_questions:
            data = []
            for q in filtered_questions:
                data.append({
                    "ID": q.id,
                    "Pytanie": q.content,
                    "Użyć": q.total_attempts,
                    "Zdawalność": f"{q.pass_rate}%"
                })
            
            df = pd.DataFrame(data)
            st.dataframe(
                df,
                column_config={
                    "Pytanie": st.column_config.TextColumn("Treść pytania", width="large"),
                    "Zdawalność": st.column_config.ProgressColumn(
                        "Zdawalność",
                        help="Procent poprawnych odpowiedzi",
                        format="%s",
                        min_value=0,
                        max_value=100
                    ),
                },
                use_container_width=True,
                hide_index=True
            )

            st.divider()

            # 4. RESETOWANIE STATYSTYK
            st.write("### ⚠️ Zarządzanie danymi")
            num_q = len(filtered_questions)
            
            # Przycisk inicjujący reset
            if st.button(f"Zresetuj statystyki dla tych {num_q} pytań", type="secondary"):
                st.session_state.confirm_reset = True

            # Mechanizm potwierdzenia
            if st.session_state.get("confirm_reset", False):
                st.warning(f"Czy na pewno chcesz wyzerować statystyki dla {num_q} pytań w kategorii '{selected_type_name}'? Te dane zostaną bezpowrotnie usunięte.")
                
                col_c1, col_c2 = st.columns(2)
                if col_c1.button("✅ TAK, POTWIERDZAM RESET", type="primary"):
                    try:
                        for q in filtered_questions:
                            q.total_attempts = 0
                            q.correct_attempts = 0
                            q.pass_rate = 0.0
                        session.commit()
                        st.session_state.confirm_reset = False
                        st.success("Statystyki zostały zresetowane!")
                        st.rerun()
                    except Exception as e:
                        session.rollback()
                        st.error(f"Błąd podczas resetowania: {e}")
                
                if col_c2.button("❌ ANULUJ"):
                    st.session_state.confirm_reset = False
                    st.rerun()
        else:
            st.info("Brak pytań w wybranej kategorii.")
    elif choice == "🚀 Masowy Import":
        st.subheader("🚀 Masowy Import (XLSX + ZIP)")
        st.write("Wgraj plik Excel z pytaniami oraz paczkę ZIP ze zdjęciami.")
    
        col1, col2 = st.columns(2)
        with col1:
            excel_file = st.file_uploader("Wybierz plik Excel (.xlsx)", type=["xlsx"])
        with col2:
            zip_file = st.file_uploader("Wybierz paczkę zdjęć (.zip)", type=["zip"])
        
        if st.button("Uruchom import danych", type="primary"):
            if excel_file and zip_file:
                with st.spinner("Trwa importowanie..."):
                    summary = run_mass_import(excel_file, zip_file, session)
                    st.success(f"Import zakończony! Sukcesy: {summary['success']}, Błędy: {summary['errors']}")
                    st.rerun()
            else:
                st.error("Musisz wgrać oba pliki!")

    session.close()