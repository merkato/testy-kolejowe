import pandas as pd
import zipfile
import io
import os
from sqlalchemy.orm import Session
from db import Question, ProfessionGroup, TestType
import shutil

UPLOAD_FOLDER = "uploads"

def run_mass_import(excel_file, zip_file, session: Session):
    """
    excel_file: Obiekt file-like (Streamlit UploadedFile)
    zip_file: Obiekt file-like (Streamlit UploadedFile)
    """
    # 1. Odczyt Excela
    df = pd.read_excel(excel_file)
    
    # 2. Obsługa ZIP (rozpakowanie grafik)
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
        
    with zipfile.ZipFile(zip_file, 'r') as z:
        z.extractall(UPLOAD_FOLDER)

    summary = {"success": 0, "errors": 0}

    for _, row in df.iterrows():
        try:
            # Pobieranie lub tworzenie relacji (Rodzaje i Grupy)
            test_types = []
            if pd.notna(row.get('Rodzaje')):
                for t_name in str(row['Rodzaje']).split(','):
                    t_name = t_name.strip()
                    t_obj = session.query(TestType).filter_by(name=t_name).first()
                    if not t_obj:
                        t_obj = TestType(name=t_name)
                        session.add(t_obj)
                        session.flush()
                    test_types.append(t_obj)

            professions = []
            if pd.notna(row.get('Grupy')):
                for p_name in str(row['Grupy']).split(','):
                    p_name = p_name.strip()
                    p_obj = session.query(ProfessionGroup).filter_by(name=p_name).first()
                    if not p_obj:
                        p_obj = ProfessionGroup(name=p_name)
                        session.add(p_obj)
                        session.flush()
                    professions.append(p_obj)

            # Tworzenie obiektu pytania
            new_q = Question(
                content=str(row['Tresc']),
                ans_a=str(row['Odp_A']),
                image_a=os.path.join(UPLOAD_FOLDER, str(row['Grafika_A'])) if pd.notna(row.get('Grafika_A')) else None,
                ans_b=str(row['Odp_B']),
                image_b=os.path.join(UPLOAD_FOLDER, str(row['Grafika_B'])) if pd.notna(row.get('Grafika_B')) else None,
                ans_c=str(row['Odp_C']),
                image_c=os.path.join(UPLOAD_FOLDER, str(row['Grafika_C'])) if pd.notna(row.get('Grafika_C')) else None,
                correct_ans=str(row['Poprawna']).upper().strip(),
                image_path=os.path.join(UPLOAD_FOLDER, str(row['Grafika_Glowna'])) if pd.notna(row.get('Grafika_Glowna')) else None,
                test_types=test_types,
                professions=professions
            )
            
            session.add(new_q)
            summary["success"] += 1
            
        except Exception as e:
            print(f"Błąd przy wierszu: {e}")
            summary["errors"] += 1

    session.commit()
    return summary