import os

# --- KONFIGURACJA BAZY DANYCH (Zgodna z Docker-compose) ---
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "your_password")
DB_HOST = os.getenv("DB_HOST", "db-testy")
DB_NAME = os.getenv("DB_NAME", "testy_db")

# URL dla SQLAlchemy (PyMySQL jako sterownik)
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

# --- KONFIGURACJA PLIKÓW ---
UPLOAD_DIR = "uploads"
ALLOWED_EXTENSIONS = ["png", "jpg", "jpeg", "webp"]

# --- DANE STARTOWE SYSTEMU ---
DEFAULT_ADMIN_USER = os.getenv("ADMIN_USER", "admin")
DEFAULT_ADMIN_PASS = os.getenv("ADMIN_PASS", "admin123")

# Domyślne grupy zawodowe (tworzone przy starcie)
DEFAULT_PROFESSIONS = ["Maszynista", "Kierownik pociągu", "Konduktor", "Rewident"]

# Role w systemie
ROLE_ADMIN = "Administrator"
ROLE_EDITOR = "Edytor"
ROLE_USER = "Użytkownik"

FOOTER_TEXT = "By SQ9NIT and AJ, 2026. Stworzone z dużą ilością kawy"

# --- WARSTWA WIZUALNA (CSS) ---
# Optymalizacja pod urządzenia mobilne, jasne tło, pastelowe przyciski
QUESTION_IMAGE_SIZE = 200
CUSTOM_CSS = """
<style>
    /* Globalne ustawienia tła i tekstu */
    .stApp {
        background-color: #ffffff;
        color: #000000;
    }

    /* Stylizacja przycisków - pastele */
    .stButton>button {
        background-color: #E3F2FD; /* Jasny błękit pastelowy */
        color: #0D47A1;
        border-radius: 12px;
        border: 1px solid #BBDEFB;
        font-weight: 600;
        height: 3em;
        width: 100%;
        transition: all 0.3s ease;
    }

    .stButton>button:hover {
        background-color: #BBDEFB;
        border-color: #90CAF9;
    }

    /* Przyciski typu 'Primary' (np. Zakończ Test, Usuń) */
    .stButton>button[kind="primary"] {
        background-color: #FFEBEE; /* Jasny róż pastelowy */
        color: #C62828;
        border: 1px solid #FFCDD2;
    }

    /* Kolory wyników w podsumowaniu testu */
    .correct-ans {
        color: #000080 !important; /* Navy Blue */
        font-weight: bold;
        background-color: #E8F5E9;
        padding: 2px 5px;
        border-radius: 4px;
    }

    .wrong-ans {
        color: #D32F2F !important; /* Red */
        font-weight: bold;
        background-color: #FFEBEE;
        padding: 2px 5px;
        border-radius: 4px;
    }

    /* Optymalizacja pod mobile - większe odstępy w radio buttons */
    .stRadio [data-testid="stWidgetLabel"] p {
        font-size: 1.1rem;
        font-weight: bold;
        margin-bottom: 10px;
    }

    div[data-testid="stMarkdownContainer"] p {
        font-size: 1rem;
        line-height: 1.6;
    }

    /* Styl dla sekcji komentarza/interpretacji */
    .stInfo {
        background-color: #F3E5F5; /* Pastelowy fiolet */
        color: #4A148C;
        border: none;
    }
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #ffffff;
        color: #666666;
        text-align: center;
        padding: 10px 0;
        font-size: 0.8rem;
        border-top: 1px solid #eeeeee;
        z-index: 999;
    }
    
    /* Odstęp dla głównego kontentu, żeby stopka go nie zasłaniała */
    .main-content {
        margin-bottom: 60px;
    }
</style>
"""