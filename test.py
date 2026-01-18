import streamlit as st
import random
from db import get_session, Question, ProfessionGroup, TestType, update_question_stats
import config

def init_test_state():
    """Inicjalizacja zmiennych sesyjnych dla testu."""
    if 'test_questions' not in st.session_state:
        st.session_state.test_questions = [] # Lista 30 obiektów pytań
        st.session_state.user_answers = {}    # {idx: 'A'/'B'/'C'}
        st.session_state.current_idx = 0
        st.session_state.test_phase = 'setup' # setup, testing, finished, review
        st.session_state.results_calculated = False

def draw_questions(profession_id, test_type_id):
    """Logika losowania 30 pytań zgodnie z wymaganiami."""
    session = get_session()
    query = session.query(Question).join(Question.professions).join(Question.test_types)
    query = query.filter(ProfessionGroup.id == profession_id)
    query = query.filter(TestType.id == test_type_id)
    pool = query.all()
    session.close()

    if not pool:
        return []

    if len(pool) >= 30:
        return random.sample(pool, 30) # Bez powtórzeń
    else:
        # Losuj z powtórzeniami, aż będzie 30
        return random.choices(pool, k=30)

def finish_test():
    """Obliczanie wyników i aktualizacja bazy."""
    correct_count = 0
    for i, q in enumerate(st.session_state.test_questions):
        user_ans = st.session_state.user_answers.get(i)
        is_correct = (user_ans == q.correct_ans)
        if is_correct:
            correct_count += 1
        # Aktualizacja statystyk w DB
        update_question_stats(q.id, is_correct)
    
    st.session_state.score = correct_count
    st.session_state.test_phase = 'finished'

def show_test_ui():
    st.markdown(config.CUSTOM_CSS, unsafe_allow_html=True)
    init_test_state()

    # --- FAZA 1: SETUP ---
    if st.session_state.test_phase == 'setup':
        st.title("📝 Rozpocznij nowy test")
        session = get_session()
        profs = session.query(ProfessionGroup).all()
        # Filtracja grup dla zwykłego użytkownika (z implementacji manager.py/app.py)
        user_profs = st.session_state.user.professions if st.session_state.user.role == config.ROLE_USER else profs
        
        prof_opt = {p.name: p.id for p in user_profs}
        type_opt = {t.name: t.id for t in session.query(TestType).all()}
        session.close()

        sel_prof = st.selectbox("Wybierz grupę zawodową", list(prof_opt.keys()))
        sel_type = st.selectbox("Wybierz rodzaj testu", list(type_opt.keys()))

        if st.button("START"):
            questions = draw_questions(prof_opt[sel_prof], type_opt[sel_type])
            if questions:
                st.session_state.test_questions = questions
                st.session_state.test_phase = 'testing'
                st.rerun()
            else:
                st.error("Brak pytań dla wybranej konfiguracji.")

    # --- FAZA 2: TESTOWANIE ---
    elif st.session_state.test_phase == 'testing':
        idx = st.session_state.current_idx
        q = st.session_state.test_questions[idx]

        st.subheader(f"Pytanie {idx + 1} z 30")
        if q.image_path:
            st.image(q.image_path, use_container_width=True)
        
        st.write(f"### {q.content}")
        
        # Opcje odpowiedzi
        options = {"A": q.ans_a, "B": q.ans_b, "C": q.ans_c}
        current_choice = st.session_state.user_answers.get(idx)
        
        choice = st.radio("Wybierz odpowiedź:", ["A", "B", "C"], 
                          index=None if current_choice is None else ["A", "B", "C"].index(current_choice),
                          format_func=lambda x: f"{x}: {options[x]}",
                          key=f"q_{idx}")

        col1, col2 = st.columns(2)

        # Przycisk Odpowiedź (aktywny tylko po zaznaczeniu)
        if col1.button("Zatwierdź Odpowiedź", disabled=(choice is None), use_container_width=True):
            st.session_state.user_answers[idx] = choice
            # Szukaj następnego pytania bez odpowiedzi
            next_idx = next((i for i in range(30) if i not in st.session_state.user_answers), None)
            if next_idx is not None:
                st.session_state.current_idx = next_idx
            st.rerun()

        # Przycisk Pomiń
        if col2.button("Pomiń", use_container_width=True):
            st.session_state.current_idx = (idx + 1) % 30
            st.rerun()

        # Jeśli na wszystkie odpowiedziano
        if len(st.session_state.user_answers) == 30:
            st.divider()
            c1, c2 = st.columns(2)
            if c1.button("ZAKOŃCZ TEST", type="primary", use_container_width=True):
                finish_test()
                st.rerun()
            if c2.button("Przejrzyj odpowiedzi", use_container_width=True):
                st.session_state.test_phase = 'review'
                st.session_state.current_idx = 0
                st.rerun()

    # --- FAZA 3: PRZEGLĄD (Przed zakończeniem) ---
    elif st.session_state.test_phase == 'review':
        idx = st.session_state.current_idx
        q = st.session_state.test_questions[idx]
        st.subheader(f"Przegląd - Pytanie {idx + 1}")
        
        options = {"A": q.ans_a, "B": q.ans_b, "C": q.ans_c}
        current_val = st.session_state.user_answers.get(idx)
        
        new_choice = st.radio("Zmień odpowiedź:", ["A", "B", "C"], 
                              index=["A", "B", "C"].index(current_val) if current_val else None,
                              format_func=lambda x: f"{x}: {options[x]}", key=f"rev_{idx}")
        
        if st.button("Zapisz zmianę"):
            st.session_state.user_answers[idx] = new_choice
            st.success("Zmieniono.")

        c1, c2, c3 = st.columns(3)
        if c1.button("Poprzednie") and idx > 0:
            st.session_state.current_idx -= 1
            st.rerun()
        if c2.button("Następne") and idx < 29:
            st.session_state.current_idx += 1
            st.rerun()
        if c3.button("ZAKOŃCZ TEST", type="primary"):
            finish_test()
            st.rerun()

    # --- FAZA 4: WYNIKI ---
    elif st.session_state.test_phase == 'finished':
        st.title("📊 Wynik Testu")
        score = st.session_state.score
        percent = round((score / 30) * 100, 1)
        
        st.metric("Poprawne odpowiedzi", f"{score} / 30", f"{percent}%")
        
        st.subheader("Błędne odpowiedzi i komentarze:")
        
        for i, q in enumerate(st.session_state.test_questions):
            user_ans = st.session_state.user_answers.get(i)
            if user_ans != q.correct_ans:
                with st.container(border=True):
                    st.write(f"**Pytanie:** {q.content}")
                    st.markdown(f"Twoja odpowiedź: <span class='wrong-ans'>{user_ans}</span>", unsafe_allow_html=True)
                    st.markdown(f"Poprawna odpowiedź: <span class='correct-ans'>{q.correct_ans}</span>", unsafe_allow_html=True)
                    if q.comment:
                        st.info(f"💡 **Komentarz:** {q.comment}")

        if st.button("Wyjdź do menu głównego"):
            for key in list(st.session_state.keys()):
                if key not in ['user', 'logged_in']: # Zachowaj sesję użytkownika
                    del st.session_state[key]
            st.rerun()