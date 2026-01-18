import bcrypt
from sqlalchemy.orm import Session
from db import get_session, User, ProfessionGroup, TestType
import config

def hash_password(password: str) -> str:
    """Tworzy bezpieczny hash hasła."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Sprawdza czy podane hasło zgadza się z hashem."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def init_system_data():
    """Inicjalizuje grupy zawodowe i konto administratora przy pierwszym uruchomieniu."""
    session = get_session()
    try:
        # 1. Inicjalizacja Grup Zawodowych
        for prof_name in config.DEFAULT_PROFESSIONS:
            exists = session.query(ProfessionGroup).filter_by(name=prof_name).first()
            if not exists:
                session.add(ProfessionGroup(name=prof_name))
        
        # 2. Inicjalizacja domyślnego Rodzaju Testu (opcjonalnie)
        if not session.query(TestType).first():
            session.add(TestType(name="Ogólny"))

        # 3. Inicjalizacja Administratora
        admin_exists = session.query(User).filter_by(role=config.ROLE_ADMIN).first()
        if not admin_exists:
            hashed_pw = hash_password(config.DEFAULT_ADMIN_PASS)
            admin = User(
                username=config.DEFAULT_ADMIN_USER,
                password_hash=hashed_pw,
                role=config.ROLE_ADMIN
            )
            session.add(admin)
            print(f"Utworzono domyślne konto administratora: {config.DEFAULT_ADMIN_USER}")
        
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"Błąd inicjalizacji danych: {e}")
    finally:
        session.close()

def create_user(username, password, role, profession_ids=None):
    """Tworzy nowego użytkownika i przypisuje mu grupy zawodowe."""
    session = get_session()
    try:
        hashed_pw = hash_password(password)
        new_user = User(username=username, password_hash=hashed_pw, role=role)
        
        if profession_ids:
            professions = session.query(ProfessionGroup).filter(ProfessionGroup.id.in_(profession_ids)).all()
            new_user.professions = professions
            
        session.add(new_user)
        session.commit()
        return True, "Użytkownik utworzony pomyślnie."
    except Exception as e:
        session.rollback()
        return False, str(e)
    finally:
        session.close()

def authenticate_user(username, password):
    """Logowanie użytkownika - zwraca obiekt User lub None."""
    session = get_session()
    user = session.query(User).filter_by(username=username).first()
    if user and verify_password(password, user.password_hash):
        # Odłączamy od sesji, aby móc używać obiektu w session_state Streamlit
        session.expunge(user)
        session.close()
        return user
    session.close()
    return None

def get_all_professions():
    """Pobiera listę wszystkich grup zawodowych."""
    session = get_session()
    profs = session.query(ProfessionGroup).all()
    session.close()
    return profs

def add_new_profession(name):
    """Dodaje nową grupę zawodową (tylko dla Admina)."""
    session = get_session()
    try:
        if session.query(ProfessionGroup).filter_by(name=name).first():
            return False, "Grupa już istnieje."
        session.add(ProfessionGroup(name=name))
        session.commit()
        return True, "Dodano grupę."
    finally:
        session.close()