import streamlit as st
#import pandas as pd
import json
import random
from datetime import datetime, timedelta
#from sqlalchemy import func
from db import get_session, ExamSession, Examinee, Question, SessionStatus, QuestionAttempt
import streamlit.components.v1 as components

def focus_loss_tracker():
    """Wstrzykuje JavaScript wykrywający opuszczenie karty przez użytkownika."""
    # Uwaga: Aby Streamlit odebrał sygnał z JS, najskuteczniejszą metodą 
    # bez niestandardowych komponentów jest query_params lub callback.
    # Poniższy skrypt wysyła sygnał do nadrzędnego okna.
    js_code = """
    <script>
    const doc = window.parent.document;
    doc.addEventListener("visibilitychange", () => {
        if (doc.visibilityState === 'hidden') {
            window.parent.postMessage({type: 'focus_loss'}, "*");
        }
    });
    </script>
    """
    components.html(js_code, height=0)

def show_exam_ui():
    """Główny interfejs nawigacyjny dla egzaminowanego."""
    if "examinee_id" not in st.session_state:
        render_login_screen()
    elif st.session_state.get("exam_finished", False):
        render_result_page(st.session_state.examinee_id, st.session_state.session_id)
    else:
        render_exam_screen()

def render_login_screen():
    """Ekran logowania technicznego na podstawie numeru szkolenia i dziennika."""
    st.title("🚉 System Egzaminacyjny PKP PLK")
    st.subheader("Panel Logowania Uczestnika")
    
    with st.form("login_form"):
        train_num = st.text_input("Numer szkolenia / egzaminu", placeholder="np. 123/2026")
        journal_num = st.number_input("Numer z dziennika", min_value=1, step=1, value=1)
        token = st.text_input("Indywidualny token dostępu", type="password")
        
        if st.form_submit_button("ROZPOCZNIJ EGZAMIN", type="primary", use_container_width=True):
            session = get_session()
            # Weryfikacja czy sesja jest aktywna
            exam_session = session.query(ExamSession).filter_by(
                training_number=train_num, 
                status=SessionStatus.ACTIVE
            ).first()
            
            if not exam_session:
                st.error("Nie znaleziono aktywnej sesji o tym numerze.")
            else:
                # Weryfikacja uczestnika w tej sesji
                examinee = session.query(Examinee).filter_by(
                    session_id=exam_session.id,
                    journal_number=journal_num,
                    access_token=token
                ).first()
                
                if not examinee:
                    st.error("Błędne dane logowania lub nieprawidłowy token.")
                elif examinee.is_finished:
                    st.warning("Twój egzamin został już zakończony i przesłany do oceny.")
                elif examinee.is_active:
                    st.error("Ta sesja jest już aktywna na innym urządzeniu. Skontaktuj się z egzaminatorem.")
                else:
                    # Inicjalizacja podejścia
                    examinee.is_active = True
                    if not examinee.start_datetime:
                        examinee.start_datetime = datetime.now()
                    
                    session.commit()
                    
                    st.session_state.examinee_id = examinee.id
                    st.session_state.session_id = exam_session.id
                    st.rerun()
            session.close()

def render_exam_screen():
    """Główny arkusz egzaminacyjny z timerem i zabezpieczeniami."""
    session = get_session()
    examinee = session.query(Examinee).get(st.session_state.examinee_id)
    exam_session = session.query(ExamSession).get(st.session_state.session_id)
    
    # 1. Kontrola czasu
    time_elapsed = datetime.now() - examinee.start_datetime
    time_limit = timedelta(minutes=exam_session.time_limit)
    time_left = time_limit - time_elapsed
    
    if time_left.total_seconds() <= 0:
        finish_exam(session, examinee, exam_session, auto=True)
        st.rerun()

    # 2. Focus Loss Tracker (Zabezpieczenie przed ściąganiem)
    focus_loss_tracker()
    
    # Symulacja odbioru sygnału Focus Loss (wymaga integracji z frontendem Streamlit)
    if st.session_state.get("focus_lost_detected", False):
        examinee.focus_loss_counter += 1
        session.commit()
        st.session_state.focus_lost_detected = False
        
        if examinee.focus_loss_counter > exam_session.max_focus_loss:
            finish_exam(session, examinee, exam_session, cheat=True)
            st.rerun()

    # 3. Losowanie pytań (Proporcjonalne)
    if "current_test" not in st.session_state:
        draw_proportional_questions(session, exam_session)

    # 4. Nagłówek i Timer
    st.title(f"✍️ Egzamin: {exam_session.training_number}")
    
    t_col1, t_col2 = st.columns([3, 1])
    t_col1.write(f"Uczestnik: **Nr dziennika {examinee.journal_number}**")
    
    # Kolorowanie timera
    timer_color = "red" if time_left.total_seconds() < 300 else "black"
    t_col2.markdown(f"Pozostały czas: <span style='color:{timer_color}; font-weight:bold;'>"
                    f"{int(time_left.total_seconds() // 60):02d}:{int(time_left.total_seconds() % 60):02d}</span>", 
                    unsafe_allow_html=True)
    
    st.divider()

    # 5. Formularz z pytaniami
    with st.form("exam_questions_form"):
        for i, q_id in enumerate(st.session_state.current_test):
            q = session.query(Question).get(q_id)
            st.markdown(f"#### Pytanie {i+1}")
            st.write(q.content)
            
            if q.image_path:
                st.image(q.image_path, use_container_width=True)
            
            # Mapowanie opcji
            opts = {f"A) {q.ans_a}": "A", f"B) {q.ans_b}": "B", f"C) {q.ans_c}": "C"}
            # Odzyskiwanie zaznaczonej odpowiedzi z sesji
            saved_ans = st.session_state.answers.get(str(q_id), None)
            index = list(opts.values()).index(saved_ans) if saved_ans in opts.values() else 0
            
            choice = st.radio("Wybierz odpowiedź:", opts.keys(), key=f"rad_{q_id}", index=index)
            st.session_state.answers[str(q_id)] = opts[choice]
            
            st.write("---")
            
        if st.form_submit_button("🏁 ZAKOŃCZ I WYŚLIJ TEST", type="primary", use_container_width=True):
            finish_exam(session, examinee, exam_session)
            st.rerun()
    
    session.close()

def draw_proportional_questions(session, exam_session):
    """Losuje pytania proporcjonalnie z wybranych rodzajów testów."""
    test_types = exam_session.test_types
    q_per_type = exam_session.question_count // len(test_types)
    
    selected_ids = []
    for t_type in test_types:
        questions = session.query(Question.id).filter(
            Question.professions.any(id=exam_session.profession_id),
            Question.test_types.any(id=t_type.id)
        ).all()
        
        ids = [q[0] for q in questions]
        count = min(len(ids), q_per_type)
        selected_ids.extend(random.sample(ids, count))
    
    # Jeśli brakuje pytań do pełnej puli, dobieramy losowo z całości dostępnych
    if len(selected_ids) < exam_session.question_count:
        all_avail = session.query(Question.id).filter(
            Question.professions.any(id=exam_session.profession_id),
            Question.test_types.any(id=test_types[0].id) # Fallback
        ).all()
        avail_ids = [q[0] for q in all_avail if q[0] not in selected_ids]
        needed = exam_session.question_count - len(selected_ids)
        selected_ids.extend(random.sample(avail_ids, min(len(avail_ids), needed)))

    random.shuffle(selected_ids)
    st.session_state.current_test = selected_ids
    st.session_state.answers = {}

def finish_exam(session, examinee, exam_session, auto=False, cheat=False):
    """Zapisuje wyniki, statystyki QuestionAttempt i kończy sesję."""
    correct_count = 0
    results_map = {}
    
    for q_id in st.session_state.current_test:
        q = session.query(Question).get(q_id)
        user_ans = st.session_state.answers.get(str(q_id), "BRAK")
        is_correct = (q.correct_ans == user_ans)
        
        if is_correct:
            correct_count += 1
        
        # 1. Aktualizacja globalna w Question
        q.total_attempts += 1
        if is_correct:
            q.correct_attempts += 1
            
        # 2. Szczegółowy log QuestionAttempt
        attempt = QuestionAttempt(
            question_id=q.id,
            examinee_id=examinee.id,
            session_id=exam_session.id,
            is_correct=is_correct
        )
        session.add(attempt)
        results_map[str(q_id)] = {"user": user_ans, "correct": q.correct_ans}

    # 3. Finalizacja rekordu Examinee
    score = (correct_count / len(st.session_state.current_test)) * 100 if not cheat else 0.0
    examinee.score_percent = score
    examinee.is_finished = True
    examinee.is_active = False
    examinee.end_datetime = datetime.now()
    examinee.answers_json = json.dumps(results_map)
    
    session.commit()
    
    st.session_state.exam_finished = True
    if auto: 
        st.warning("Czas upłynął! Arkusz został wysłany automatycznie.")
    if cheat: 
        st.error("Egzamin przerwany z powodu naruszenia zasad (Focus Loss).")

def render_result_page(examinee_id, session_id):
    """Wyświetla podsumowanie egzaminu w stylu 'Klasycznego Testu'."""
    session = get_session()
    examinee = session.query(Examinee).get(examinee_id)
    exam_session = session.query(ExamSession).get(session_id)
    results = json.loads(examinee.answers_json)
    
    st.balloons() if examinee.score_percent >= exam_session.pass_threshold else st.snow()
    
    st.title("🏁 Koniec Egzaminu")
    st.header(f"Twój wynik: {examinee.score_percent:.2f}%")
    
    passed = examinee.score_percent >= exam_session.pass_threshold
    if passed:
        st.success(f"WYNIK POZYTYWNY (Próg: {exam_session.pass_threshold}%)")
    else:
        st.error(f"WYNIK NEGATYWNY (Próg: {exam_session.pass_threshold}%)")

    if exam_session.show_errors:
        st.divider()
        st.subheader("🧐 Przegląd Twoich odpowiedzi")
        
        for q_id_str, info in results.items():
            q = session.query(Question).get(int(q_id_str))
            with st.container():
                is_correct = info['user'] == info['correct']
                if is_correct:
                    with st.expander(f"✅ {q.content[:100]}...", expanded=False):
                        st.write(f"**Pytanie:** {q.content}")
                        st.write(f"Twoja odpowiedź: **{info['user']}** (Poprawna)")
                else:
                    st.error(f"❌ **BŁĄD: {q.content}**")
                    st.write(f"Twoja odpowiedź: **{info['user']}** | Poprawna: **{info['correct']}**")
                    if exam_session.show_comment and q.comment:
                        st.info(f"💡 Komentarz: {q.comment}")
                st.write("---")

    if st.button("WYLOGUJ I ZAKOŃCZ", type="primary", use_container_width=True):
        for key in ["examinee_id", "session_id", "current_test", "answers", "exam_finished"]:
            if key in st.session_state: 
                del st.session_state[key]
        st.rerun()
    
    session.close()