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
        st.title("Testy Kolejowe")
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
    
    st.markdown('</div>', unsafe_allow_html=True) # Zamknięcie kontenera treści
    
    render_footer()

if __name__ == "__main__":
    main()