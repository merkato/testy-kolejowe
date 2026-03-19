import io
import os
import zipfile
import pandas as pd
from datetime import datetime
from sqlalchemy.orm import joinedload
from db import get_session, Question, ProfessionGroup, TestType
import config

def get_abs_upload_path():
    """Zwraca bezwzględną ścieżkę do katalogu z obrazami."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, config.IMAGE_PATH)

def export_questions_to_zip(profession_ids=None, test_type_ids=None):
    """
    Generuje paczkę ZIP zawierającą plik Excel oraz powiązane obrazy.
    Filtruje pytania według wybranych grup zawodowych i rodzajów testu.
    """
    session = get_session()
    abs_image_dir = get_abs_upload_path()
    
    try:
        # 1. Budowanie zapytania z filtrowaniem i eager loadingiem relacji
        query = session.query(Question).options(
            joinedload(Question.professions),
            joinedload(Question.test_types)
        )
        
        if profession_ids:
            query = query.filter(Question.professions.any(ProfessionGroup.id.in_(profession_ids)))
        if test_type_ids:
            query = query.filter(Question.test_types.any(TestType.id.in_(test_type_ids)))
            
        questions = query.all()
        
        if not questions:
            return None, "Brak pytań spełniających kryteria eksportu."

        # 2. Przygotowanie danych do Excela
        data = []
        images_to_pack = set() # Zbiór unikalnych ścieżek do spakowania

        for q in questions:
            # Mapowanie nazw plików (wycinamy ścieżkę, zostawiamy samą nazwę dla Excela)
            img_q = os.path.basename(q.image_path) if q.image_path else ""
            img_a = os.path.basename(q.image_a) if q.image_a else ""
            img_b = os.path.basename(q.image_b) if q.image_b else ""
            img_c = os.path.basename(q.image_c) if q.image_c else ""

            # Dodawanie istniejących plików do kolejki pakowania
            for path in [q.image_path, q.image_a, q.image_b, q.image_c]:
                if path and os.path.exists(os.path.join(os.path.dirname(abs_image_dir), path)):
                    images_to_pack.add(path)

            data.append({
                "content": q.content,
                "ans_a": q.ans_a,
                "ans_b": q.ans_b,
                "ans_c": q.ans_c,
                "correct_ans": q.correct_ans,
                "profession_names": ", ".join([p.name for p in q.professions]),
                "test_types": ", ".join([t.name for t in q.test_types]),
                "image_q": img_q,
                "image_a": img_a,
                "image_b": img_b,
                "image_c": img_c
            })

        df = pd.DataFrame(data)

        # 3. Tworzenie archiwum ZIP w pamięci
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            
            # Dodawanie Excela
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Pytania')
            zf.writestr("pytania_eksport.xlsx", excel_buffer.getvalue())

            # Dodawanie obrazów (zachowując ich nazwy bazowe)
            base_app_dir = os.path.dirname(abs_image_dir)
            for rel_path in images_to_pack:
                full_path = os.path.join(base_app_dir, rel_path)
                try:
                    zf.write(full_path, arcname=os.path.basename(rel_path))
                except Exception:
                    # Pomijamy pliki, których nie da się odczytać
                    continue

        zip_buffer.seek(0)
        timestamp = datetime.now().strftime("%Y%m%d%H%M")
        filename = f"{timestamp}_export_bazy.zip"
        
        return (zip_buffer, filename), f"Wyeksportowano {len(questions)} pytań."

    except Exception as e:
        return None, f"Błąd podczas eksportu: {str(e)}"
    finally:
        session.close()