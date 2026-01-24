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
