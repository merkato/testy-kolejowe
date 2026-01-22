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
# config.py

CUSTOM_CSS = """
<style>
    /* Główny kontener - jasne tło i ciemny tekst */
    .stApp {
        background-color: #f8f9fa !important;
        color: #1a1a1a !important;
    }

    /* Wszystkie etykiety (Labels) i nagłówki */
    label, p, h1, h2, h3, .stMarkdown {
        color: #1a1a1a !important;
    }

    /* Pola input (tekstowe, liczbowe, hasła) */
    div[data-baseweb="input"] {
        background-color: #ffffff !important;
        border: 1px solid #ced4da !important;
    }
    
    input {
        color: #1a1a1a !important; /* Wymuszenie czarnego tekstu w polach */
        -webkit-text-fill-color: #1a1a1a !important; /* Dla Chrome w Windows */
    }

    /* Selectboxy (listy rozwijane) */
    div[data-baseweb="select"] {
        background-color: #ffffff !important;
    }
    
    div[data-baseweb="select"] div {
        color: #1a1a1a !important;
    }

    /* Przyciski */
    .stButton>button {
        background-color: #004a99 !important;
        color: white !important;
        border-radius: 5px;
        border: none;
    }
    
    .stButton>button:hover {
        background-color: #003366 !important;
        color: #ffffff !important;
    }

    /* Kontenery formularzy */
    [data-testid="stForm"] {
        background-color: #ffffff !important;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }

    /* Stopka */
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #f1f1f1;
        color: #666666 !important;
        text-align: center;
        padding: 10px;
        font-size: 12px;
    }
    /* Naprawa kontrastu tekstu na przyciskach */
    div.stButton > button {
        background-color: #004a99 !important;
        color: white !important; /* Biały tekst zawsze! */
        border-radius: 5px;
        font-weight: 600;
    }

    /* Przycisk wyloguj - czerwony akcent */
    [data-testid="stSidebar"] div.stButton > button {
        background-color: #c0392b !important;
        color: white !important;
    }

    /* Poprawa czytelności w sidebarze */
    [data-testid="stSidebar"] {
        color: #1c1c1c;
    }
</style>
"""