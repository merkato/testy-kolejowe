import streamlit as st
import os
import uuid
import pandas as pd
from db import get_session, Question, ProfessionGroup, TestType
import config

def save_uploaded_file(uploaded_file):
    """Zapisuje wgraną grafikę na serwerze z unikalną nazwą."""
    if not os.path.exists(config.UPLOAD_DIR):
        os.makedirs(config.UPLOAD_DIR)
    
    extension = uploaded_file.name.split('.')[-1]
    unique_filename = f"{uuid.uuid4()}.{extension}"
    file_path = os.path.join(config.UPLOAD_DIR, unique_filename)
    
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    return file_path

def show_editor_ui():
    st.title("🛠️ Edytor Bazy Pytań")
    
    session = get_session()
    
    # Pobranie danych pomocniczych
    all_professions = session.query(ProfessionGroup).all()
    all_test_types = session.query(TestType).all()
    all_questions = session.query(Question).all()
    
    prof_options = {p.name: p for p in all_professions}
    type_options = {t.name: t for t in all_test_types}

    menu = ["Dodaj nowe pytanie", "Edytuj / Usuń istniejące"]
    choice = st.sidebar.selectbox("Menu Edytora", menu)

    # --- LOGIKA: DODAWANIE NOWEGO PYTANIA ---
    if choice == "Dodaj nowe pytanie":
        st.subheader("Nowe pytanie")
        
        with st.form("add_question_form", clear_on_submit=True):
            content = st.text_area("Treść pytania")
            col1, col2, col3 = st.columns(3)
            ans_a = col1.text_input("Odpowiedź A")
            ans_b = col2.text_input("Odpowiedź B")
            ans_c = col3.text_input("Odpowiedź C")
            
            correct_ans = st.selectbox("Poprawna odpowiedź", ["A", "B", "C"])
            
            uploaded_file = st.file_uploader("Dodaj grafikę (opcjonalnie)", type=config.ALLOWED_EXTENSIONS)
            
            selected_profs = st.multiselect("Grupy zawodowe", list(prof_options.keys()))
            selected_types = st.multiselect("Rodzaj testu", list(type_options.keys()))
            
            comment = st.text_area("Komentarz / Wyciąg z przepisów")
            
            submitted = st.form_submit_button("Zapisz pytanie")
            
            if submitted:
                if content and ans_a and ans_b and ans_c:
                    image_path = save_uploaded_file(uploaded_file) if uploaded_file else None
                    
                    new_q = Question(
                        content=content,
                        ans_a=ans_a,
                        ans_b=ans_b,
                        ans_c=ans_c,
                        correct_ans=correct_ans,
                        image_path=image_path,
                        comment=comment
                    )
                    
                    new_q.professions = [prof_options[name] for name in selected_profs]
                    new_q.test_types = [type_options[name] for name in selected_types]
                    
                    session.add(new_q)
                    session.commit()
                    st.success("Pytanie dodane pomyślnie!")
                    st.rerun()
                else:
                    st.error("Wypełnij wszystkie pola treści i odpowiedzi.")

    # --- LOGIKA: EDYCJA / USUWANIE ---
    else:
        st.subheader("Zarządzaj pytaniami")
        q_list = {f"ID {q.id}: {q.content[:50]}...": q for q in all_questions}
        
        selected_q_label = st.selectbox("Wybierz pytanie do edycji", [""] + list(q_list.keys()))
        
        if selected_q_label:
            q = q_list[selected_q_label]
            
            with st.expander("Statystyki szczegółowe", expanded=False):
                st.write(f"Zdawalność: **{q.pass_rate}%**")
                st.write(f"Liczba użyć: {q.total_attempts}")
                st.write(f"Poprawne odpowiedzi: {q.correct_attempts}")

            with st.form("edit_question_form"):
                new_content = st.text_area("Treść pytania", value=q.content)
                new_a = st.text_input("Odpowiedź A", value=q.ans_a)
                new_b = st.text_input("Odpowiedź B", value=q.ans_b)
                new_c = st.text_input("Odpowiedź C", value=q.ans_c)
                new_correct = st.selectbox("Poprawna", ["A", "B", "C"], index=["A", "B", "C"].index(q.correct_ans))
                
                if q.image_path:
                    st.image(q.image_path, width=200, caption="Obecna grafika")
                    if st.checkbox("Usuń obecną grafikę"):
                        q.image_path = None

                new_file = st.file_uploader("Zmień grafikę", type=config.ALLOWED_EXTENSIONS)
                
                current_prof_names = [p.name for p in q.professions]
                current_type_names = [t.name for t in q.test_types]
                
                new_profs = st.multiselect("Grupy zawodowe", list(prof_options.keys()), default=current_prof_names)
                new_types = st.multiselect("Rodzaj testu", list(type_options.keys()), default=current_type_names)
                
                new_comment = st.text_area("Komentarz", value=q.comment if q.comment else "")
                
                col_btn1, col_btn2 = st.columns(2)
                update_btn = col_btn1.form_submit_button("Zaktualizuj")
                delete_btn = col_btn2.form_submit_button("USUŃ PYTANIE", type="primary")

                if update_btn:
                    q.content = new_content
                    q.ans_a = new_a
                    q.ans_b = new_b
                    q.ans_c = new_c
                    q.correct_ans = new_correct
                    q.comment = new_comment
                    if new_file:
                        q.image_path = save_uploaded_file(new_file)
                    
                    q.professions = [prof_options[name] for name in new_profs]
                    q.test_types = [type_options[name] for name in new_types]
                    
                    session.commit()
                    st.success("Zaktualizowano.")
                    st.rerun()

                if delete_btn:
                    session.delete(q)
                    session.commit()
                    st.warning("Usunięto pytanie.")
                    st.rerun()

    # --- TABELA ISTNIEJĄCYCH PYTAŃ ---
    st.divider()
    st.subheader("📋 Lista pytań i statystyki")
    
    if all_questions:
        # Przygotowanie danych do tabeli (Dataframe)
        data = []
        for q in all_questions:
            data.append({
                "ID": q.id,
                "Treść pytania": q.content,
                "Zdawalność": f"{q.pass_rate}%",
                "Użyć": q.total_attempts
            })
        
        df = pd.DataFrame(data)
        # Wyświetlamy jako interaktywną tabelę (możliwość sortowania i szukania)
        st.dataframe(
            df, 
            column_config={
                "Treść pytania": st.column_config.TextColumn(width="large"),
                "Zdawalność": st.column_config.TextColumn(width="small"),
            },
            hide_index=True,
            use_container_width=True
        )
    else:
        st.info("Baza pytań jest pusta.")

    session.close()