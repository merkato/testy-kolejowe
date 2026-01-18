from sqlalchemy import create_engine, Column, Integer, String, Float, Text, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from config import DATABASE_URL  # Import konfiguracji

Base = declarative_base()

# --- TABELE POWIĄZAŃ (Many-to-Many) ---

# Powiązanie Użytkowników z Grupami Zawodowymi
user_profession_m2m = Table(
    'user_profession', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id', ondelete="CASCADE"), primary_key=True),
    Column('profession_id', Integer, ForeignKey('profession_groups.id', ondelete="CASCADE"), primary_key=True)
)

# Powiązanie Pytań z Grupami Zawodowymi
question_profession_m2m = Table(
    'question_profession', Base.metadata,
    Column('question_id', Integer, ForeignKey('questions.id', ondelete="CASCADE"), primary_key=True),
    Column('profession_id', Integer, ForeignKey('profession_groups.id', ondelete="CASCADE"), primary_key=True)
)

# Powiązanie Pytań z Rodzajami Testów
question_test_type_m2m = Table(
    'question_test_type', Base.metadata,
    Column('question_id', Integer, ForeignKey('questions.id', ondelete="CASCADE"), primary_key=True),
    Column('test_type_id', Integer, ForeignKey('test_types.id', ondelete="CASCADE"), primary_key=True)
)

# --- MODELE ---

class ProfessionGroup(Base):
    """Grupy zawodowe: Maszynista, Kierownik, Konduktor, Rewident."""
    __tablename__ = 'profession_groups'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)

    def __repr__(self):
        return self.name

class TestType(Base):
    """Rodzaje testów: Ruchowe, Taborowe, Handlowe itp."""
    __tablename__ = 'test_types'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)

    def __repr__(self):
        return self.name

class User(Base):
    """Użytkownicy systemu z rolami i przypisanymi grupami zawodowymi."""
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False) # Administrator, Edytor, Użytkownik
    
    # Relacja do grup zawodowych (Użytkownik może należeć do wielu)
    professions = relationship("ProfessionGroup", secondary=user_profession_m2m, backref="users")

class Question(Base):
    """Baza pytań z pełną informacją o odpowiedziach i statystykach."""
    __tablename__ = 'questions'
    id = Column(Integer, primary_key=True)
    content = Column(Text, nullable=False)
    ans_a = Column(String(500), nullable=False)
    ans_b = Column(String(500), nullable=False)
    ans_c = Column(String(500), nullable=False)
    correct_ans = Column(String(1), nullable=False) # A, B lub C
    image_path = Column(String(255), nullable=True) # Ścieżka do pliku w /uploads
    comment = Column(Text, nullable=True)
    
    # Statystyki zdawalności
    total_attempts = Column(Integer, default=0)
    correct_attempts = Column(Integer, default=0)
    pass_rate = Column(Float, default=0.0)

    # Relacje Many-to-Many
    professions = relationship("ProfessionGroup", secondary=question_profession_m2m, backref="questions")
    test_types = relationship("TestType", secondary=question_test_type_m2m, backref="questions")

# --- ZARZĄDZANIE SILNIKIEM I SESJĄ ---

engine = create_engine(
    DATABASE_URL, 
    pool_pre_ping=True,  # Automatyczne odświeżanie połączenia (ważne dla MariaDB)
    echo=False           # Ustaw na True podczas debugowania
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Inicjalizuje tabele. Wywoływane przy starcie app.py."""
    Base.metadata.create_all(bind=engine)

def get_session():
    """Tworzy i zwraca nową sesję bazy danych."""
    return SessionLocal()

def update_question_stats(question_id, is_correct):
    """Aktualizuje statystyki pytania po zakończeniu testu."""
    session = get_session()
    try:
        q = session.query(Question).filter(Question.id == question_id).first()
        if q:
            q.total_attempts += 1
            if is_correct:
                q.correct_attempts += 1
            # Wyliczenie procentowe
            q.pass_rate = round((q.correct_attempts / q.total_attempts) * 100, 2)
            session.commit()
    except Exception as e:
        session.rollback()
        print(f"Błąd aktualizacji statystyk: {e}")
    finally:
        session.close()