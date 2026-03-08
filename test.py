import streamlit as st
import random
import db
from db import Question, ProfessionGroup, TestType, update_question_stats
import config
import style

def init_test_state():
    """Inicjalizacja zmiennych sesyjnych dla testu."""
    if 'test_questions' not in st.session_state:
        st.session_state.test_questions = []
        st.session_state.user_answers = {}
        st.session_state.current_idx = 0
        st.session_state.test_phase = 'setup'
        st.session_state.results_calculated = False

def draw_questions(session, profession_id, test_type_ids, limit):
    """
    Losuje pytania dbając o równomierny rozkład między wybranymi rodzajami testów.
    Unika powtórek, chyba że pula jest mniejsza niż wymagana liczba pytań.
    """
    if not test_type_ids:
        return []

    target_per_type = limit // len(test_type_ids)
    remainder = limit % len(test_type_ids)
    
    selected_questions = []

    for i, t_id in enumerate(test_type_ids):
        # Używamy profession_id (zgodnie z błędem AttributeError)
        pool = session.query(Question).filter(
            Question.profession_id == profession_id,
            Question.test_type_id == t_id
        ).all()
        
        if not pool:
            continue

        count_to_draw = target_per_type + (1 if i < remainder else 0)
        
        # Próba unikalnego losowania
        if len(pool) >= count_to_draw:
            selected_questions.extend(random.sample(pool, count_to_draw))
        else:
            # Jeśli w bazie jest za mało pytań tego rodzaju, bierzemy wszystkie 
            # i dobieramy resztę losowo (powtórki), aby dobić do limitu
            selected_questions.extend(pool)
            needed = count_to_draw - len(pool)
            if pool:
                selected_questions.extend(random.choices(pool, k=needed))

    random.shuffle(selected_questions)
    return selected_questions[:limit]

def finish_test():
    """Obliczanie wyników i aktualizacja bazy."""
    correct_count = 0
    for i, q in enumerate(st.session_state.test_questions):
        user_ans = st.session_state.user_answers.get(i)
        is_correct = (user_ans == q.correct_ans)
        if is_correct:
            correct_count += 1
        update_question_stats(q.id, is_correct)
    
    st.session_state.score = correct_count
    st.session_state.test_phase = 'finished'

def show_test_ui():
    style.apply_custom_css()
    init_test_state()

    # --- FAZA 1: SETUP ---
    if st.session_state.test_phase == 'setup':
        st.title("📝 Nowy Egzamin")
        
        # Pobieramy sesję bazy danych
        db_sess = db.get_session()
        try:
            profs = db_sess.query(ProfessionGroup).all()
            user_profs = st.session_state.user.professions if st.session_state.user.role == config.ROLE_USER else profs
            
            prof_opt = {p.name: p.id for p in user_profs}
            type_opt = {t.name: t.id for t in db_sess.query(TestType).all()}

            sel_prof_name = st.selectbox("Wybierz grupę zawodową", list(prof_opt.keys()))
            sel_type_name = st.selectbox("Wybierz rodzaj testu", list(type_opt.keys()))

            if st.button("ROZPOCZNIJ TEST", type="primary", use_container_width=True):
                # POPRAWKA: Pobieramy ID ze słowników i przekazujemy limit 30
                p_id = prof_opt[sel_prof_name]
                t_id = type_opt[sel_type_name]
                
                questions = draw_questions(db_sess, p_id, [t_id], limit=30)

                if questions:
                    st.session_state.test_questions = questions
                    st.session_state.test_phase = 'testing'
                    st.rerun()
                else:
                    st.error("Brak pytań dla wybranej konfiguracji.")
        finally:
            db_sess.close()

    # --- FAZA 2: TESTOWANIE ---
    elif st.session_state.test_phase == 'testing':
        idx = st.session_state.current_idx
        q = st.session_state.test_questions[idx]

        st.subheader(f"Pytanie {idx + 1} z 30")
        st.write(f"### {q.content}")

        if q.image_path:
            style.st_responsive_image(q.image_path)
        
        st.divider()

        # Układ odpowiedzi
        options = {"A": (q.ans_a, q.image_a), "B": (q.ans_b, q.image_b), "C": (q.ans_c, q.image_c)}
        for label in ["A", "B", "C"]:
            text, img = options[label]
            style.st_answer_layout(label, text, img)

        current_choice = st.session_state.user_answers.get(idx)
        choice = st.radio("Twoja decyzja:", ["A", "B", "C"], 
                          index=None if current_choice is None else ["A", "B", "C"].index(current_choice),
                          horizontal=True, key=f"q_{idx}")

        col1, col2 = st.columns(2)
        if col1.button("Zatwierdź i dalej", disabled=(choice is None), type="primary", use_container_width=True):
            st.session_state.user_answers[idx] = choice
            # Szukamy następnego nieodpowiedzianego pytania
            next_idx = next((i for i in range(30) if i not in st.session_state.user_answers), None)
            if next_idx is not None:
                st.session_state.current_idx = next_idx
            st.rerun()

        if col2.button("Pomiń / Następne", use_container_width=True):
            st.session_state.current_idx = (idx + 1) % 30
            st.rerun()

        if len(st.session_state.user_answers) == 30:
            st.success("Wszystkie odpowiedzi udzielone!")
            c1, c2 = st.columns(2)
            if c1.button("ZAKOŃCZ I OCEŃ", type="primary", use_container_width=True):
                finish_test()
                st.rerun()
            if c2.button("Przejrzyj wszystko", use_container_width=True):
                st.session_state.test_phase = 'review'
                st.session_state.current_idx = 0
                st.rerun()

    # --- FAZA 4: WYNIKI (Z TWOIMI POPRAWKAMI) ---
    elif st.session_state.test_phase == 'finished':
        st.title("📊 Wynik Twojego Egzaminu")
        score = st.session_state.score
        percent = round((score / 30) * 100, 2)
        
        st.metric("Skuteczność", f"{percent}%", f"{score} / 30")
        
        if percent >= 90:
            st.balloons()
            st.success("Gratulacje! Egzamin zaliczony.")
        else:
            st.error("Niestety, wynik poniżej progu zaliczeniowego (90%).")

        st.subheader("Analiza błędów:")
        for i, q in enumerate(st.session_state.test_questions):
            user_ans = st.session_state.user_answers.get(i)
            
            # Mapowanie liter na pełną treść odpowiedzi
            ans_map = {"A": q.ans_a, "B": q.ans_b, "C": q.ans_c}
            
            if user_ans != q.correct_ans:
                with st.expander(f"❌ Pytanie nr {i+1}: {q.content[:60]}..."):
                    st.write(f"**Treść pytania:** {q.content}")
                    if q.image_path:
                        style.st_responsive_image(q.image_path, width_percent=0.4)
                    
                    st.divider()
                    # Wyświetlamy treści odpowiedzi, a nie tylko literki
                    st.error(f"Twoja odpowiedź ({user_ans}): {ans_map.get(user_ans, 'Brak')}")
                    st.success(f"Poprawna odpowiedź ({q.correct_ans}): {ans_map.get(q.correct_ans)}")
                    
                    if q.comment:
                        st.info(f"💡 **Wyjaśnienie:** {q.comment}")
        
        # Przycisk powrotu czyści sesję testu
        if st.button("Powrót do strony głównej", use_container_width=True):
            for key in list(st.session_state.keys()):
                if key not in ['user', 'logged_in']:
                    del st.session_state[key]
            st.rerun()