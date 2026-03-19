import enum
import os
from datetime import datetime
from sqlalchemy import (
    create_engine, Column, Integer, String, Boolean, 
    Text, Float, DateTime, ForeignKey, Enum, Table
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

Base = declarative_base()

# --- TABELE ASOCJACYJNE (Relacje Many-to-Many) ---

# Powiązanie pytań z grupami zawodowymi
question_profession = Table(
    'question_profession', Base.metadata,
    Column('question_id', Integer, ForeignKey('questions.id'), primary_key=True),
    Column('profession_id', Integer, ForeignKey('profession_groups.id'), primary_key=True)
)

# Powiązanie pytań z rodzajami testów (np. Ie-1, Ruch)
question_test_type = Table(
    'question_test_type', Base.metadata,
    Column('question_id', Integer, ForeignKey('questions.id'), primary_key=True),
    Column('test_type_id', Integer, ForeignKey('test_types.id'), primary_key=True)
)

# Powiązanie sesji egzaminacyjnej z wieloma kategoriami pytań
session_test_type = Table(
    'session_test_type', Base.metadata,
    Column('session_id', Integer, ForeignKey('exam_sessions.id'), primary_key=True),
    Column('test_type_id', Integer, ForeignKey('test_types.id'), primary_key=True)
)

# Uprawnienia egzaminatora do zarządzania konkretnymi zawodami
examiner_profession = Table(
    'examiner_profession', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('profession_id', Integer, ForeignKey('profession_groups.id'), primary_key=True)
)

# --- ENUMERACJE (Słowniki systemowe) ---

class UserRole(enum.Enum):
    ADMIN = "admin"
    EXAMINER = "egzaminator"
    USER = "uzytkownik"

class SessionStatus(enum.Enum):
    PLANNED = "zaplanowana"
    ACTIVE = "w toku"
    FINISHED = "zakonczona"

# --- MODELE BAZODANOWE ---

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.USER)
    
    # Grupy zawodowe, do których egzaminator ma uprawnienia (filtrowanie sesji/wyników)
    managed_professions = relationship(
        "ProfessionGroup", 
        secondary=examiner_profession,
        backref="authorized_examiners"
    )

class ProfessionGroup(Base):
    __tablename__ = 'profession_groups'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)

class TestType(Base):
    __tablename__ = 'test_types'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)

class Question(Base):
    __tablename__ = 'questions'
    id = Column(Integer, primary_key=True)
    content = Column(Text, nullable=False)
    ans_a = Column(Text)
    ans_b = Column(Text)
    ans_c = Column(Text)
    correct_ans = Column(String(1)) # A, B lub C
    
    # Ścieżki do plików graficznych
    image_path = Column(String(255)) # Główne zdjęcie do pytania
    image_a = Column(String(255))
    image_b = Column(String(255))
    image_c = Column(String(255))
    
    comment = Column(Text) # Komentarz dydaktyczny wyświetlany po błędzie
    
    # Globalne liczniki zdawalności
    total_attempts = Column(Integer, default=0)
    correct_attempts = Column(Integer, default=0)
    
    professions = relationship("ProfessionGroup", secondary=question_profession)
    test_types = relationship("TestType", secondary=question_test_type)

class ExamSession(Base):
    __tablename__ = 'exam_sessions'
    id = Column(Integer, primary_key=True)
    training_number = Column(String(25), unique=True, nullable=False) # Nr szkolenia/egzaminu
    
    # Konfiguracja sesji
    profession_id = Column(Integer, ForeignKey('profession_groups.id'))
    question_count = Column(Integer, default=20)
    pass_threshold = Column(Integer, default=80) # Próg w % (0-100)
    time_limit = Column(Integer, default=30)     # Limit w minutach
    max_focus_loss = Column(Integer, default=3)  # Dopuszczalne opuszczenia okna
    
    # Ustawienia widoczności dla egzaminowanego
    show_errors = Column(Boolean, default=True)
    show_comment = Column(Boolean, default=True)
    
    # Czas i przebieg
    scheduled_start = Column(DateTime, nullable=False) # Data wprowadzona ręcznie
    actual_end = Column(DateTime, nullable=True)       # Ustawiana przy "Zakończ sesję"
    status = Column(Enum(SessionStatus), default=SessionStatus.PLANNED)
    
    # Powiązania
    examiner_id = Column(Integer, ForeignKey('users.id'))
    test_types = relationship("TestType", secondary=session_test_type)
    examinees = relationship("Examinee", backref="session", cascade="all, delete-orphan")

class Examinee(Base):
    __tablename__ = 'examinees'
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey('exam_sessions.id'))
    journal_number = Column(Integer, nullable=False)
    
    # Bezpieczeństwo i dostęp
    access_token = Column(String(64), unique=True) # Unikalny klucz logowania technicznego
    is_active = Column(Boolean, default=False)     # Blokada wielokrotnego zalogowania
    is_finished = Column(Boolean, default=False)   # Czy zakończył i oddał arkusz
    focus_loss_counter = Column(Integer, default=0) # Licznik przełączeń okien
    
    # Statystyki indywidualne
    start_datetime = Column(DateTime, nullable=True)
    end_datetime = Column(DateTime, nullable=True)
    score_percent = Column(Float, default=0.0)
    # Zapis odpowiedzi w formacie JSON: {"pytanie_id": "odp_uzytkownika"}
    answers_json = Column(Text) 

# Dodaj do db.py pod tabelą Examinee

class QuestionAttempt(Base):
    __tablename__ = 'question_attempts'
    id = Column(Integer, primary_key=True)
    question_id = Column(Integer, ForeignKey('questions.id'))
    examinee_id = Column(Integer, ForeignKey('examinees.id'))
    session_id = Column(Integer, ForeignKey('exam_sessions.id'))
    is_correct = Column(Boolean, nullable=False)
    timestamp = Column(DateTime, default=datetime.now)

    # Relacje dla łatwiejszego wyciągania danych
    question = relationship("Question", backref="attempts")
    session = relationship("ExamSession", backref="question_logs")

# --- INICJALIZACJA I FUNKCJE POMOCNICZE ---

DB_PATH = 'database.db'
engine = create_engine(f'sqlite:///{DB_PATH}', echo=False)

def init_db():
    """Tworzy tabele w bazie danych, jeśli jeszcze nie istnieją."""
    Base.metadata.create_all(engine)

SessionLocal = sessionmaker(bind=engine)

def get_session():
    """Zwraca nową sesję połączenia z bazą danych."""
    return SessionLocal()

# Automatyczna inicjalizacja przy imporcie modułu
if not os.path.exists(DB_PATH):
    init_db()