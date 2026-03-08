import streamlit as st
import random
from db import get_session, Question, ProfessionGroup, TestType, update_question_stats
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

def draw_questions(profession_id, test_type_id):
    """Logika losowania 30 pytań."""
    session = get_session()
    query = session.query(Question).join(Question.professions).join(Question.test_types)
    query = query.filter(ProfessionGroup.id == profession_id)
    query = query.filter(TestType.id == test_type_id)
    pool = query.all()
    session.close()

    if not pool:
        return []

    if len(pool) >= 30:
        return random.sample(pool, 30)
    else:
        return random.choices(pool, k=30)
    
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
    # 1. Aplikujemy pastelowe style na starcie
    style.apply_custom_css()
    init_test_state()

    # --- FAZA 1: SETUP ---
    if st.session_state.test_phase == 'setup':
        st.title("📝 Nowy Egzamin")
        session = get_session()
        profs = session.query(ProfessionGroup).all()
        user_profs = st.session_state.user.professions if st.session_state.user.role == config.ROLE_USER else profs
        
        prof_opt = {p.name: p.id for p in user_profs}
        type_opt = {t.name: t.id for t in session.query(TestType).all()}
        session.close()

        sel_prof = st.selectbox("Wybierz grupę zawodową", list(prof_opt.keys()))
        sel_type = st.selectbox("Wybierz rodzaj testu", list(type_opt.keys()))

        if st.button("ROZPOCZNIJ TEST", type="primary", use_container_width=True):
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
        
        # Treść pytania
        st.write(f"### {q.content}")

        # Główna grafika pytania (Responsywna 60% PC / 100% Mobile)
        if q.image_path:
            style.st_responsive_image(q.image_path)
        
        st.divider()

        # Układ odpowiedzi z grafikami (Tekst obok obrazka)
        options = {
            "A": (q.ans_a, q.image_a),
            "B": (q.ans_b, q.image_b),
            "C": (q.ans_c, q.image_c)
        }

        # Wyświetlamy wizualny podgląd odpowiedzi (z obrazkami)
        for label in ["A", "B", "C"]:
            text, img = options[label]
            style.st_answer_layout(label, text, img)

        # Wybór odpowiedzi (Radio)
        current_choice = st.session_state.user_answers.get(idx)
        choice = st.radio(
            "Twoja decyzja:", 
            ["A", "B", "C"], 
            index=None if current_choice is None else ["A", "B", "C"].index(current_choice),
            horizontal=True,
            key=f"q_{idx}"
        )

        # Nawigacja
        col1, col2 = st.columns(2)
        if col1.button("Zatwierdź i dalej", disabled=(choice is None), type="primary", use_container_width=True):
            st.session_state.user_answers[idx] = choice
            next_idx = next((i for i in range(30) if i not in st.session_state.user_answers), None)
            if next_idx is not None:
                st.session_state.current_idx = next_idx
            st.rerun()

        if col2.button("Pomiń / Poprzednie", use_container_width=True):
            st.session_state.current_idx = (idx + 1) % 30
            st.rerun()

        # Stopka testu
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

    # --- FAZA 3: PRZEGLĄD ---
    elif st.session_state.test_phase == 'review':
        idx = st.session_state.current_idx
        q = st.session_state.test_questions[idx]
        st.subheader(f"Przegląd pytań - {idx + 1}/30")
        
        # Powtarzamy układ responsywny
        st.write(f"**{q.content}**")
        if q.image_path:
            style.st_responsive_image(q.image_path)

        current_val = st.session_state.user_answers.get(idx)
        new_choice = st.radio("Zmień odpowiedź:", ["A", "B", "C"], 
                              index=["A", "B", "C"].index(current_val) if current_val else None,
                              key=f"rev_{idx}")
        
        if st.button("Zapisz korektę", use_container_width=True):
            st.session_state.user_answers[idx] = new_choice
            st.toast("Zmiana zapisana!")

        c1, c2, c3 = st.columns(3)
        if c1.button("Wstecz", use_container_width=True) and idx > 0:
            st.session_state.current_idx -= 1
            st.rerun()
        if c2.button("Dalej", use_container_width=True) and idx < 29:
            st.session_state.current_idx += 1
            st.rerun()
        if c3.button("ZAKOŃCZ", type="primary", use_container_width=True):
            finish_test()
            st.rerun()

    # --- FAZA 4: WYNIKI ---
    elif st.session_state.test_phase == 'finished':
        st.title("📊 Wynik Twojego Egzaminu")
        score = st.session_state.score
        percent = round((score / 30) * 100, 2)
        
        # Metric w pastelowym stylu
        st.metric("Skuteczność", f"{percent}%", f"{score} / 30")
        
        if percent >= 90:
            st.balloons()
            st.success("Gratulacje! Egzamin zaliczony.")
        else:
            st.error("Niestety, wynik poniżej progu zaliczeniowego (90%).")

        st.subheader("Analiza błędów:")
        for i, q in enumerate(st.session_state.test_questions):
            user_ans = st.session_state.user_answers.get(i)
            if user_ans != q.correct_ans:
                with st.expander(f"❌ Pytanie nr {i+1}: {q.content[:50]}..."):
                    st.write(f"**Pełna treść:** {q.content}")
                    if q.image_path:
                        style.st_responsive_image(q.image_path, width_percent=0.4)
                    
                    st.error(f"Twoja odpowiedź: {user_ans}")
                    st.success(f"Poprawna odpowiedź: {q.correct_ans}")
                    if q.comment:
                        st.info(f"💡 **Wyjaśnienie:** {q.comment}")

        if st.button("Powrót do strony głównej", use_container_width=True):
            for key in list(st.session_state.keys()):
                if key not in ['user', 'logged_in']:
                    del st.session_state[key]
            st.rerun()