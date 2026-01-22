import streamlit as st
import pandas as pd
import config
import db
import manager
import edytor
import test
import pdf_service

# 1. Inicjalizacja bazy danych i danych startowych (Admin, Grupy)
db.init_db()
manager.init_system_data()

# 2. Konfiguracja strony (optymalizacja pod mobile)
st.set_page_config(
    page_title="Testy kolejowe",
    page_icon="logo.png", # Opcjonalnie
    layout="wide",
    initial_sidebar_state="expanded"
)

# Wstrzyknięcie stylów CSS z config.py
st.markdown(config.CUSTOM_CSS, unsafe_allow_html=True)

# 3. Zarządzanie stanem sesji logowania
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user' not in st.session_state:
    st.session_state.user = None

def render_footer():
    """Renderuje stopkę na dole strony."""
    st.markdown(f'<div class="footer">{config.FOOTER_TEXT}</div>', unsafe_allow_html=True)

def login_screen():
    """Ekran logowania."""
    st.title("🚉 Testy Kolejowe")
    st.subheader("Zaloguj się, aby kontynuować")
    
    with st.form("login_form"):
        username = st.text_input("Użytkownik")
        password = st.text_input("Hasło", type="password")
        submit = st.form_submit_button("Zaloguj")
        
        if submit:
            user = manager.authenticate_user(username, password)
            if user:
                st.session_state.logged_in = True
                st.session_state.user = user
                st.rerun()
            else:
                st.error("Nieprawidłowy login lub hasło.")
    
    render_footer()  # Wywołanie stopki na ekranie logowania

def user_profile_page():
    st.header("👤 Ustawienia konta")
    user = st.session_state.user
    st.write(f"Zalogowany jako: **{user.username}**")
    st.write(f"Rola: **{user.role}**")
    
    with st.form("change_password_form"):
        new_pass = st.text_input("Nowe hasło", type="password")
        confirm_pass = st.text_input("Powtórz nowe hasło", type="password")
        submit = st.form_submit_button("Zmień hasło")
        
        if submit:
            if len(new_pass) < 6:
                st.error("Hasło musi mieć co najmniej 6 znaków.")
            elif new_pass != confirm_pass:
                st.error("Hasła nie są identyczne.")
            else:
                if manager.update_user_password(user.id, new_pass):
                    st.success("Hasło zostało zmienione!")
                else:
                    st.error("Błąd podczas zmiany hasła.")

def admin_user_management():
    st.header("👥 Zarządzanie Użytkownikami")
    
    # --- SEKCJA 1: DODAWANIE NOWEGO UŻYTKOWNIKA ---
    with st.expander("➕ Dodaj Nowego Użytkownika", expanded=False):
        with st.form("add_user_form"):
            new_username = st.text_input("Nazwa użytkownika (Login)")
            new_password = st.text_input("Hasło", type="password")
            new_role = st.selectbox("Rola", [config.ROLE_USER, config.ROLE_EDITOR, config.ROLE_ADMIN])
            
            # Pobranie grup zawodowych do wyboru
            all_profs = manager.get_all_professions()
            prof_map = {p.name: p.id for p in all_profs}
            selected_prof_names = st.multiselect("Przypisz Grupy Zawodowe", list(prof_map.keys()))
            
            submit_user = st.form_submit_button("Stwórz Użytkownika")
            
            if submit_user:
                if not new_username or not new_password:
                    st.error("Login i hasło są wymagane!")
                else:
                    sel_ids = [prof_map[name] for name in selected_prof_names]
                    success, msg = manager.create_user(new_username, new_password, new_role, sel_ids)
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(f"Błąd: {msg}")

    st.divider()
    
    # --- SEKCJA 2: LISTA I EDYCJA ---
    users = manager.get_all_users()
    
    st.subheader("Lista Użytkowników")
    user_data = []
    for u in users:
        user_data.append({
            "ID": u.id,
            "Login": u.username,
            "Rola": u.role,
            "Grupy": ", ".join([p.name for p in u.professions])
        })
    st.dataframe(pd.DataFrame(user_data), use_container_width=True, hide_index=True)
    
    st.subheader("Edytuj / Resetuj Hasło")
    user_map = {u.username: u for u in users}
    selected_username = st.selectbox("Wybierz użytkownika do modyfikacji", ["-- wybierz --"] + list(user_map.keys()))
    
    if selected_username != "-- wybierz --":
        target_user = user_map[selected_username]
        col1, col2 = st.columns(2)
        
        with col1:
            current_role_idx = [config.ROLE_USER, config.ROLE_EDITOR, config.ROLE_ADMIN].index(target_user.role)
            new_role_edit = st.selectbox("Zmień rolę", 
                                        [config.ROLE_USER, config.ROLE_EDITOR, config.ROLE_ADMIN], 
                                        index=current_role_idx)
            if st.button("Aktualizuj rolę"):
                manager.update_user_role(target_user.id, new_role_edit)
                st.success(f"Rola zmieniona!")
                st.rerun()
                
        with col2:
            new_pass_admin = st.text_input("Resetuj hasło", type="password")
            if st.button("Zapisz nowe hasło"):
                if len(new_pass_admin) >= 6:
                    manager.update_user_password(target_user.id, new_pass_admin)
                    st.success(f"Hasło dla {selected_username} zresetowane.")
                else:
                    st.error("Za krótkie hasło.")

def admin_profession_management():
    """Interfejs dodawania grup zawodowych i rodzajów testów z tabelami podglądu."""
    st.header("🏗️ Zarządzanie Strukturą Systemu")
    
    session = db.get_session()
    
    # Pobieramy aktualne dane do wyświetlenia w tabelach
    all_professions = session.query(db.ProfessionGroup).all()
    all_test_types = session.query(db.TestType).all()
    
    col1, col2 = st.columns(2)
    
    # --- KOLUMNA 1: GRUPY ZAWODOWE ---
    with col1:
        st.subheader("Grupy Zawodowe")
        new_prof = st.text_input("Nazwa nowej grupy (np. Rewident)", key="add_prof_input")
        if st.button("Dodaj Grupę"):
            if new_prof:
                # Sprawdzenie duplikatu przed próbą zapisu
                exists = session.query(db.ProfessionGroup).filter_by(name=new_prof).first()
                if exists:
                    st.error(f"Grupa '{new_prof}' już istnieje!")
                else:
                    session.add(db.ProfessionGroup(name=new_prof))
                    session.commit()
                    st.success(f"Dodano grupę: {new_prof}")
                    st.rerun() # Odświeżenie, aby nowa pozycja pojawiła się w tabeli poniżej
        
        st.write("---")
        st.write("**Istniejące grupy:**")
        if all_professions:
            # Wyświetlamy jako prostą listę/tabelę
            prof_data = [p.name for p in all_professions]
            st.table(prof_data)
        else:
            st.info("Brak zdefiniowanych grup.")

    # --- KOLUMNA 2: RODZAJE TESTÓW ---
    with col2:
        st.subheader("Rodzaje Testów")
        new_test_type = st.text_input("Nowy rodzaj testu (np. Sygnalizacja)", key="add_type_input")
        if st.button("Dodaj Rodzaj Testu"):
            if new_test_type:
                # Sprawdzenie duplikatu
                exists = session.query(db.TestType).filter_by(name=new_test_type).first()
                if exists:
                    st.error(f"Rodzaj testu '{new_test_type}' już istnieje!")
                else:
                    session.add(db.TestType(name=new_test_type))
                    session.commit()
                    st.success(f"Dodano rodzaj testu: {new_test_type}")
                    st.rerun() # Odświeżenie tabeli
        
        st.write("---")
        st.write("**Istniejące rodzaje testów:**")
        if all_test_types:
            type_data = [t.name for t in all_test_types]
            st.table(type_data)
        else:
            st.info("Brak zdefiniowanych rodzajów testów.")

    session.close()

def show_pdf_generator():
    st.header("🖨️ Generator Arkuszy PDF")
    st.write("Skonfiguruj parametry arkusza egzaminacyjnego do druku.")
    
    # Pobieramy dane z bazy
    all_profs = manager.get_all_professions()
    # Pobieramy rodzaje testów (tematy)
    session = db.get_session()
    all_topics = session.query(db.TestType).all()
    session.close()

    # Tworzymy słowniki mapujące Nazwa -> ID, aby Streamlit operował na prostych typach
    prof_map = {p.name: p.id for p in all_profs}
    topic_map = {t.name: t.id for t in all_topics}

    col1, col2 = st.columns(2)
    
    with col1:
        selected_prof_name = st.selectbox("Grupa zawodowa", list(prof_map.keys()))
        selected_prof_id = prof_map[selected_prof_name]
        
        count = st.number_input("Całkowita liczba pytań", min_value=1, max_value=200, value=30)
    
    with col2:
        # Używamy list nazw jako opcji - to naprawi problem z wybieraniem
        selected_topic_names = st.multiselect(
            "Kategorie tematyczne (rodzaje testu)", 
            options=list(topic_map.keys()),
            help="Wybierz jedną lub więcej kategorii. Pytania zostaną rozdzielone równomiernie."
        )
        logo_file = st.file_uploader("Wgraj logotyp (PNG/JPG)", type=['png', 'jpg', 'jpeg'])

    st.divider()

    if st.button("Przygotuj arkusze"):
        if not selected_topic_names:
            st.error("Proszę wybrać przynajmniej jedną kategorię tematyczną (Rodzaj testu)!")
        else:
            # Zamieniamy wybrane nazwy na ID
            selected_topic_ids = [topic_map[name] for name in selected_topic_names]
            
            with st.spinner("Losowanie pytań i generowanie plików..."):
                # Pobranie pytań z manager.py
                questions = manager.get_balanced_questions(selected_prof_id, selected_topic_ids, count)
                
                if questions:
                    # Generowanie dwóch osobnych plików PDF
                    paper_pdf = pdf_service.create_test_paper_pdf(questions, selected_prof_name, logo_file)
                    key_pdf = pdf_service.create_answer_key_pdf(questions, selected_prof_name)
                    
                    st.success(f"Pomyślnie wygenerowano arkusz z {len(questions)} pytaniami.")
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        st.download_button(
                            label="📥 Pobierz ARKUSZ PYTAŃ",
                            data=paper_pdf,
                            file_name=f"Egzamin_{selected_prof_name.replace(' ', '_')}.pdf",
                            mime="application/pdf"
                        )
                    with c2:
                        st.download_button(
                            label="🔑 Pobierz KLUCZ ODPOWIEDZI",
                            data=key_pdf,
                            file_name=f"Klucz_{selected_prof_name.replace(' ', '_')}.pdf",
                            mime="application/pdf"
                        )
                else:
                    st.error("Nie znaleziono żadnych pytań spełniających wybrane kryteria.")

def main():
    if not st.session_state.logged_in:
        login_screen()
        return

    # Pasek boczny - Nawigacja
    user = st.session_state.user
    st.sidebar.title(f"Witaj, {user.username}")
    st.sidebar.info(f"Rola: {user.role}")

    menu_options = []
    
    # Definicja menu na podstawie ról
    if user.role == config.ROLE_ADMIN:
        menu_options = ["🏠 Start", "📝 Rozwiąż Test", "🛠️ Edytor Pytań", "🖨️ Generator PDF", "👥 Użytkownicy", "🏗️ Grupy i Kategorie", "👤 Profil"]
    elif user.role == config.ROLE_EDITOR:
        menu_options = ["🏠 Start", "📝 Rozwiąż Test", "🛠️ Edytor Pytań", "🖨️ Generator PDF", "👤 Profil"]
    else:
        menu_options = ["🏠 Start", "📝 Rozwiąż Test", "👤 Profil"]

    choice = st.sidebar.radio("Nawigacja", menu_options)

    # Logout
    if st.sidebar.button("Wyloguj"):
        st.session_state.logged_in = False
        st.session_state.user = None
        st.rerun()

    # Routing podstron
    if choice == "🏠 Start":
        st.title("Testy Kolejowe")
        st.write(f"Zalogowano jako: **{user.role}**")
        st.write("Wybierz opcję z menu po lewej stronie, aby rozpocząć.")
        
        if user.role == config.ROLE_USER:
            st.info(f"Twoje uprawnienia obejmują grupy: {', '.join([p.name for p in user.professions])}")
    elif choice == "📝 Rozwiąż Test":
        test.show_test_ui()
    elif choice == "🛠️ Edytor Pytań":
        edytor.show_editor_ui()
    elif choice == "🖨️ Generator PDF" and user.role in [config.ROLE_ADMIN, config.ROLE_EDITOR]:
        show_pdf_generator()
    elif choice == "👥 Użytkownicy" and user.role == config.ROLE_ADMIN:
        admin_user_management()
    elif choice == "🏗️ Grupy i Kategorie" and user.role == config.ROLE_ADMIN:
        admin_profession_management()
    elif choice == "👤 Profil":
        user_profile_page()
    st.markdown('</div>', unsafe_allow_html=True) # Zamknięcie kontenera treści
    
    render_footer()

if __name__ == "__main__":
    main()