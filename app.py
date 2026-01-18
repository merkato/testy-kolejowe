import streamlit as st
import config
import db
import manager
import edytor
import test

# 1. Inicjalizacja bazy danych i danych startowych (Admin, Grupy)
db.init_db()
manager.init_system_data()

# 2. Konfiguracja strony (optymalizacja pod mobile)
st.set_page_config(
    page_title="System Testów Kolejowych",
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

def login_screen():
    """Ekran logowania."""
    st.title("🚉 System Testów")
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
                st.success("Zalogowano pomyślnie!")
                st.rerun()
            else:
                st.error("Nieprawidłowy login lub hasło.")

def admin_user_management():
    """Interfejs zarządzania użytkownikami dla Administratora."""
    st.header("👥 Zarządzanie Użytkownikami")
    
    with st.expander("Dodaj nowego użytkownika"):
        with st.form("new_user_form"):
            new_username = st.text_input("Nazwa użytkownika")
            new_password = st.text_input("Hasło", type="password")
            new_role = st.selectbox("Rola", [config.ROLE_USER, config.ROLE_EDITOR, config.ROLE_ADMIN])
            
            all_profs = manager.get_all_professions()
            prof_map = {p.name: p.id for p in all_profs}
            selected_profs = st.multiselect("Dostęp do grup zawodowych", list(prof_map.keys()))
            
            if st.form_submit_button("Utwórz konto"):
                if new_username and new_password:
                    prof_ids = [prof_map[name] for name in selected_profs]
                    success, msg = manager.create_user(new_username, new_password, new_role, prof_ids)
                    if success: st.success(msg)
                    else: st.error(msg)
                else:
                    st.warning("Uzupełnij login i hasło.")

def admin_profession_management():
    """Interfejs dodawania grup zawodowych."""
    st.header("🏗️ Grupy Zawodowe i Testy")
    
    col1, col2 = st.columns(2)
    with col1:
        new_prof = st.text_input("Nowa grupa zawodowa (np. Rewident)")
        if st.button("Dodaj Grupę"):
            if new_prof:
                success, msg = manager.add_new_profession(new_prof)
                if success: st.success(msg); st.rerun()
                else: st.error(msg)
    
    with col2:
        # Zarządzanie rodzajami testów
        new_test_type = st.text_input("Nowy rodzaj testu (np. Handlowe)")
        if st.button("Dodaj Rodzaj Testu"):
            session = db.get_session()
            session.add(db.TestType(name=new_test_type))
            session.commit()
            session.close()
            st.success("Dodano rodzaj testu.")
            st.rerun()

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
        menu_options = ["🏠 Start", "📝 Rozwiąż Test", "🛠️ Edytor Pytań", "👥 Użytkownicy", "🏗️ Grupy i Kategorie"]
    elif user.role == config.ROLE_EDITOR:
        menu_options = ["🏠 Start", "📝 Rozwiąż Test", "🛠️ Edytor Pytań"]
    else:
        menu_options = ["🏠 Start", "📝 Rozwiąż Test"]

    choice = st.sidebar.radio("Nawigacja", menu_options)

    # Logout
    if st.sidebar.button("Wyloguj"):
        st.session_state.logged_in = False
        st.session_state.user = None
        st.rerun()

    # Routing podstron
    if choice == "🏠 Start":
        st.title("System Testów Wiedzy Kolejowej")
        st.write(f"Zalogowano jako: **{user.role}**")
        st.write("Wybierz opcję z menu po lewej stronie, aby rozpocząć.")
        
        if user.role == config.ROLE_USER:
            st.info(f"Twoje uprawnienia obejmują grupy: {', '.join([p.name for p in user.professions])}")

    elif choice == "📝 Rozwiąż Test":
        test.show_test_ui()

    elif choice == "🛠️ Edytor Pytań":
        edytor.show_editor_ui()

    elif choice == "👥 Użytkownicy" and user.role == config.ROLE_ADMIN:
        admin_user_management()

    elif choice == "🏗️ Grupy i Kategorie" and user.role == config.ROLE_ADMIN:
        admin_profession_management()

if __name__ == "__main__":
    main()