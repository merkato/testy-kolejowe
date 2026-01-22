import bcrypt
import random
from sqlalchemy.sql import func
from sqlalchemy.orm import Session, joinedload
from db import get_session, User, ProfessionGroup, TestType
import config

def hash_password(password):
    """Zmienia czyste hasło na bezpieczny hash."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def init_system_data():
    """Inicjalizuje grupy zawodowe i konto administratora przy pierwszym uruchomieniu."""
    session = get_session()
    try:
        for prof_name in config.DEFAULT_PROFESSIONS:
            exists = session.query(ProfessionGroup).filter_by(name=prof_name).first()
            if not exists:
                session.add(ProfessionGroup(name=prof_name))
        
        if not session.query(TestType).first():
            session.add(TestType(name="Ogólny"))

        admin_exists = session.query(User).filter_by(role=config.ROLE_ADMIN).first()
        if not admin_exists:
            hashed_pw = hash_password(config.DEFAULT_ADMIN_PASS)
            admin = User(
                username=config.DEFAULT_ADMIN_USER,
                password_hash=hashed_pw,
                role=config.ROLE_ADMIN
            )
            session.add(admin)
        
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
    session = get_session()
    try:
        user = session.query(User).options(joinedload(User.professions)).filter_by(username=username).first()
        if user and user.password_hash:
            if bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
                session.expunge(user)
                return user
        return None
    except Exception as e:
        print(f"Błąd logowania: {e}")
        return None
    finally:
        session.close()

def update_user_password(user_id, new_password):
    """Zmienia hasło użytkownika - poprawiona nazwa kolumny."""
    session = get_session()
    try:
        user = session.query(User).filter_by(id=user_id).first()
        if user:
            # KLUCZOWA POPRAWKA: password_hash zamiast password
            user.password_hash = hash_password(new_password)
            session.commit()
            return True
        return False
    except Exception:
        session.rollback()
        return False
    finally:
        session.close()

def update_user_role(user_id, new_role):
    session = get_session()
    try:
        user = session.query(User).filter_by(id=user_id).first()
        if user:
            user.role = new_role
            session.commit()
            return True
        return False
    finally:
        session.close()

def get_all_users():
    session = get_session()
    try:
        return session.query(User).options(joinedload(User.professions)).all()
    finally:
        session.close()

def get_all_professions():
    session = get_session()
    profs = session.query(ProfessionGroup).all()
    session.close()
    return profs

def get_balanced_questions(profession_id, topic_ids, total_count):
    """Pobiera zbalansowaną liczbę pytań z wybranych kategorii."""
    session = get_session()
    questions_per_topic = total_count // len(topic_ids)
    remainder = total_count % len(topic_ids)
    
    final_questions = []
    
    for i, t_id in enumerate(topic_ids):
        # Określamy ile pytań wziąć z tej kategorii
        count_to_take = questions_per_topic + (1 if i < remainder else 0)
        
        query = session.query(Question).join(Question.professions).join(Question.test_types)
        query = query.filter(ProfessionGroup.id == profession_id)
        query = query.filter(TestType.id == t_id)
        
        # Losowanie po stronie bazy danych dla wydajności
        topic_pool = query.order_by(func.rand()).limit(count_to_take).all()
        final_questions.extend(topic_pool)
        
    session.close()
    random.shuffle(final_questions) # Mieszamy, żeby nie były pogrupowane kategoriami
    return final_questions