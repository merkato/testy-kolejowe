from db import (
    get_session, init_db, User, ProfessionGroup, 
    TestType, UserRole, examiner_profession
)

def seed_database():
    """Inicjalizuje bazę danych i tworzy pierwszego administratora."""
    # 1. Upewniamy się, że tabele istnieją
    init_db()
    session = get_session()

    try:
        # 2. Tworzymy podstawowe grupy zawodowe
        profs = [
            ProfessionGroup(name="Maszynista"),
            ProfessionGroup(name="Dyżurny Ruchu"),
            ProfessionGroup(name="Rewident Taboru"),
            ProfessionGroup(name="Automatyk")
        ]
        for p in profs:
            # Sprawdzamy czy już nie istnieje, żeby nie dublować przy re-runie
            if not session.query(ProfessionGroup).filter_by(name=p.name).first():
                session.add(p)
        
        # 3. Tworzymy podstawowe kategorie testów
        types = [
            TestType(name="Sygnalizacja Ie-1"),
            TestType(name="Przepisy Ruchu Ir-1"),
            TestType(name="Budowa Pojazdów"),
            TestType(name="BHP i PPOŻ")
        ]
        for t in types:
            if not session.query(TestType).filter_by(name=t.name).first():
                session.add(t)
        
        session.flush()

        # 4. Tworzymy głównego Administratora / Egzaminatora
        # W 2026 r. zalecane jest haszowanie, ale na start używamy jawnego tekstu
        admin_username = "admin"
        existing_admin = session.query(User).filter_by(username=admin_username).first()

        if not existing_admin:
            new_admin = User(
                username=admin_username,
                password="admin123",  # Zmień przy pierwszej okazji!
                role=UserRole.ADMIN
            )
            
            # Przypisujemy mu uprawnienia do zarządzania wszystkimi grupami
            all_profs = session.query(ProfessionGroup).all()
            new_admin.managed_professions = all_profs
            
            session.add(new_admin)
            print(f"✅ Utworzono użytkownika: {admin_username} (Hasło: admin123)")
        else:
            print(f"ℹ️ Użytkownik {admin_username} już istnieje.")

        session.commit()
        print("🚀 Baza danych została pomyślnie zainicjalizowana!")

    except Exception as e:
        session.rollback()
        print(f"❌ Błąd podczas inicjalizacji: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    seed_database()