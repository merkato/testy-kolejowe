import streamlit as st
import db
from db import Question, update_question_stats
import manager
import config
import style

def init_test_state():
    """Inicjalizuje wszystkie zmienne sesji dla testu."""
    if 'test_phase' not in st.session_state:
        st.session_state.test_phase = 'setup'
    if 'current_idx' not in st.session_state:
        st.session_state.current_idx = 0
    if 'user_answers' not in st.session_state:
        st.session_state.user_answers = {}
    if 'test_questions' not in st.session_state:
        st.session_state.test_questions = []

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
        
        db_sess = db.get_session()
        try:
            from db import ProfessionGroup, TestType
            profs = db_sess.query(ProfessionGroup).all()
            user_profs = st.session_state.user.professions if st.session_state.user.role == config.ROLE_USER else profs
            
            prof_opt = {p.name: p.id for p in user_profs}
            type_opt = {t.name: t.id for t in db_sess.query(TestType).all()}

            sel_p = st.selectbox("Wybierz grupę zawodową", list(prof_opt.keys()))
            sel_t = st.selectbox("Wybierz rodzaj testu", list(type_opt.keys()))

            if st.button("ROZPOCZNIJ TEST", type="primary", use_container_width=True):
                # Kluczowy moment: Pobieramy pytania
                questions = manager.get_balanced_questions(
                    profession_id=prof_opt[sel_p],
                    topic_ids=[type_opt[sel_t]],
                    total_count=30
                )

                if questions:
                    st.session_state.test_questions = questions
                    st.session_state.test_phase = 'testing'
                    st.session_state.current_idx = 0  # Reset indeksu
                    st.session_state.user_answers = {} # Reset odpowiedzi
                    st.rerun()
                else:
                    st.error("Brak pytań dla tej konfiguracji.")
        finally:
            db_sess.close()

    # --- FAZA 2: TESTOWANIE ---
    elif st.session_state.test_phase == 'testing':
        questions = st.session_state.test_questions
        idx = st.session_state.current_idx
        
        if not questions:
            st.session_state.test_phase = 'setup'
            st.rerun()

        q = questions[idx]
        st.subheader(f"Pytanie {idx + 1} z {len(questions)}")
        st.write(f"### {q.content}")

        if q.image_path:
            style.st_responsive_image(q.image_path)
        
        st.divider()

        # Mapowanie treści odpowiedzi
        options_data = {"A": q.ans_a, "B": q.ans_b, "C": q.ans_c}
        options_images = {"A": q.image_a, "B": q.image_b, "C": q.image_c}

        for label in ["A", "B", "C"]:
            style.st_answer_layout(label, options_data[label], options_images[label])

        current_choice = st.session_state.user_answers.get(idx)
        choice = st.radio("Twoja decyzja:", ["A", "B", "C"], 
                          index=None if current_choice is None else ["A", "B", "C"].index(current_choice),
                          horizontal=True, key=f"q_radio_{idx}")

        col1, col2 = st.columns(2)
        if col1.button("Zatwierdź i dalej", disabled=(choice is None), type="primary", use_container_width=True):
            st.session_state.user_answers[idx] = choice
            if idx + 1 < len(questions):
                st.session_state.current_idx += 1
            st.rerun()

        if col2.button("Poprzednie / Pomiń", use_container_width=True):
            st.session_state.current_idx = (idx + 1) % len(questions)
            st.rerun()

        if len(st.session_state.user_answers) == len(questions):
            if st.button("ZAKOŃCZ I OCEŃ", type="primary", use_container_width=True):
                # Obliczanie wyniku
                score = sum(1 for i, q_obj in enumerate(questions) if st.session_state.user_answers.get(i) == q_obj.correct_ans)
                st.session_state.score = score
                st.session_state.test_phase = 'finished'
                st.rerun()

    # --- FAZA 4: WYNIKI (Z pełną treścią odpowiedzi) ---
    elif st.session_state.test_phase == 'finished':
        st.title("📊 Wyniki")
        score = st.session_state.score
        total = len(st.session_state.test_questions)
        percent = round((score / total) * 100, 2)
        
        st.metric("Skuteczność", f"{percent}%", f"{score} / {total}")

        st.subheader("Analiza błędnych odpowiedzi:")
        for i, q in enumerate(st.session_state.test_questions):
            user_ans = st.session_state.user_answers.get(i)
            ans_map = {"A": q.ans_a, "B": q.ans_b, "C": q.ans_c}
            
            if user_ans != q.correct_ans:
                with st.expander(f"❌ Pytanie nr {i+1}: {q.content[:60]}..."):
                    st.write(f"**Treść pytania:** {q.content}")
                    st.divider()
                    # TU WYŚWIETLAMY TREŚĆ, O KTÓRĄ PROSIŁEŚ
                    st.error(f"**Twoja odpowiedź ({user_ans}):** {ans_map.get(user_ans, 'Brak')}")
                    st.success(f"**Poprawna odpowiedź ({q.correct_ans}):** {ans_map.get(q.correct_ans)}")
                    if q.comment:
                        st.info(f"💡 Wyjaśnienie: {q.comment}")

        if st.button("Powrót do menu", use_container_width=True):
            st.session_state.test_phase = 'setup'
            st.rerun()