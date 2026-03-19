import os
import pandas as pd
import zipfile
from db import Question, ProfessionGroup, TestType, get_session
import config

def get_abs_image_path():
    """Składa bezwzględną ścieżkę do katalogu uploads."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    abs_path = os.path.join(base_dir, config.IMAGE_PATH)
    os.makedirs(abs_path, exist_ok=True)
    return abs_path

def import_questions_from_package(excel_file, zip_file=None):
    db_session = get_session()
    abs_upload_dir = get_abs_image_path()
    
    try:
        df = pd.read_excel(excel_file)
        if zip_file:
            with zipfile.ZipFile(zip_file, 'r') as zf:
                zf.extractall(abs_upload_dir)

        for _, row in df.iterrows():
            question = db_session.query(Question).filter_by(content=row['content']).first()
            if not question:
                question = Question(content=row['content'])
                db_session.add(question)

            question.ans_a = row['ans_a']
            question.ans_b = row['ans_b']
            question.ans_c = row['ans_c']
            question.correct_ans = str(row['correct_ans']).upper()
            
            # Mapowanie obrazków
            question.image_path = _process_img_val(row.get('image_q'))
            question.image_a = _process_img_val(row.get('image_a'))
            question.image_b = _process_img_val(row.get('image_b'))
            question.image_c = _process_img_val(row.get('image_c'))

            if 'profession_names' in row and pd.notna(row['profession_names']):
                names = [n.strip() for n in str(row['profession_names']).split(',')]
                question.professions = _get_or_create_refs(db_session, ProfessionGroup, names)

            if 'test_types' in row and pd.notna(row['test_types']):
                types = [t.strip() for t in str(row['test_types']).split(',')]
                question.test_types = _get_or_create_refs(db_session, TestType, types)

        db_session.commit()
        return True, "Baza pytań została zsynchronizowana."
    except Exception as e:
        db_session.rollback()
        return False, f"Błąd: {str(e)}"
    finally:
        db_session.close()

def _process_img_val(val):
    if pd.isna(val) or not str(val).strip():
        return None
    return os.path.join(config.IMAGE_PATH, str(val).strip())

def _get_or_create_refs(session, model, names):
    objects = []
    for name in names:
        obj = session.query(model).filter_by(name=name).first()
        if not obj:
            obj = model(name=name)
            session.add(obj)
            session.flush()
        objects.append(obj)
    return objects