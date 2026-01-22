from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
from PIL import Image as PILImage
import io
import os

def get_font_name():
    """Rejestruje i zwraca nazwę czcionki obsługującej polskie znaki."""
    try:
        # Ścieżka standardowa dla kontenerów debianopodobnych (Ubuntu/slim)
        font_path = '/usr/share/fonts/truetype/freefont/FreeSans.ttf'
        if os.path.exists(font_path):
            pdfmetrics.registerFont(TTFont('FreeSans', font_path))
            return 'FreeSans'
    except Exception:
        pass
    return 'Helvetica'

def draw_header(c, width, height, font_name, title, logo_file=None):
    """Rysuje nagłówek arkusza z poprawioną obsługą logo."""
    if logo_file:
        try:
            # KLUCZOWA POPRAWKA:
            # Streamlit UploadedFile musi być opakowany w ImageReader
            logo_img = ImageReader(logo_file)
            
            # Pobieramy rozmiar obrazu do obliczenia proporcji
            img_w, img_h = logo_img.getSize()
            aspect = img_h / img_w
            display_w = 2.5 * cm
            display_h = display_w * aspect
            
            # Rysujemy używając ImageReader
            c.drawImage(logo_img, width - 3.5 * cm, height - 2.5 * cm, 
                        width=display_w, height=display_h, mask='auto')
        except Exception as e:
            # Jeśli logo jest uszkodzone, wypisz błąd w logach, ale nie przerywaj PDF
            print(f"Problem z logotypem: {e}")

    c.setFont(font_name, 16)
    c.drawCentredString(width / 2, height - 2 * cm, title)
    c.setFont(font_name, 10)
    c.drawString(2 * cm, height - 3 * cm, "Imię i nazwisko: ............................................................ Data: ....................")
    c.line(2 * cm, height - 3.2 * cm, width - 2 * cm, height - 3.2 * cm)

def create_test_paper_pdf(questions, profession_name, logo_file=None):
    """Generuje PDF z samymi pytaniami i ilustracjami."""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    font_name = get_font_name()
    
    title = f"Arkusz Egzaminacyjny: {profession_name}"
    draw_header(c, width, height, font_name, title, logo_file)
    
    y = height - 4.5 * cm
    
    for i, q in enumerate(questions):
        # Sprawdzenie miejsca na stronie (bezpieczny margines dla pytania z obrazkiem)
        needed_space = 2 * cm
        if q.image_path: needed_space += 5 * cm
        if q.image_a or q.image_b or q.image_c: needed_space += 4 * cm
        
        if y < needed_space:
            c.showPage()
            draw_header(c, width, height, font_name, title, logo_file)
            y = height - 4.5 * cm

        # Treść pytania
        c.setFont(font_name, 11)
        c.drawString(2 * cm, y, f"{i+1}. {q.content}")
        y -= 0.8 * cm

        # Ilustracja do pytania
        if q.image_path and os.path.exists(q.image_path):
            try:
                c.drawImage(q.image_path, 3 * cm, y - 4.5 * cm, width=12 * cm, height=4.5 * cm, preserveAspectRatio=True, anchor='sw')
                y -= 5 * cm
            except:
                c.drawString(3 * cm, y, "[Błąd wczytywania grafiki pytania]")
                y -= 0.8 * cm

        # Odpowiedzi
        c.setFont(font_name, 10)
        labels = [("A", q.ans_a, q.image_a), ("B", q.ans_b, q.image_b), ("C", q.ans_c, q.image_c)]
        
        for label, text, img_path in labels:
            # Tekst odpowiedzi
            c.drawString(2.5 * cm, y, f"{label}) {text if text else ''}")
            
            # Obrazek do odpowiedzi (jeśli istnieje)
            if img_path and os.path.exists(img_path):
                try:
                    y -= 3.2 * cm
                    c.drawImage(img_path, 3 * cm, y, width=4 * cm, height=3 * cm, preserveAspectRatio=True, anchor='sw')
                except:
                    y -= 0.5 * cm
                    c.drawString(3.5 * cm, y, "[Błąd grafiki]")
            
            y -= 0.7 * cm
        
        y -= 0.5 * cm # Odstęp między pytaniami

    c.save()
    buffer.seek(0)
    return buffer

def create_answer_key_pdf(questions, profession_name):
    """Generuje osobny PDF z kluczem odpowiedzi."""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    font_name = get_font_name()
    
    c.setFont(font_name, 16)
    c.drawCentredString(width / 2, height - 2 * cm, f"KLUCZ ODPOWIEDZI")
    c.setFont(font_name, 12)
    c.drawCentredString(width / 2, height - 2.7 * cm, f"Dla arkusza: {profession_name}")
    c.line(2 * cm, height - 3.2 * cm, width - 2 * cm, height - 3.2 * cm)

    y = height - 4.5 * cm
    col = 0
    
    for i, q in enumerate(questions):
        c.setFont(font_name, 11)
        # Rozmieszczenie w 3 kolumnach dla oszczędności miejsca
        x_pos = 2 * cm + (col * 5 * cm)
        c.drawString(x_pos, y, f"Pytanie {i+1}:   [ {q.correct_ans} ]")
        
        y -= 0.8 * cm
        if y < 2 * cm:
            if col < 2:
                col += 1
                y = height - 4.5 * cm
            else:
                c.showPage()
                col = 0
                y = height - 4.5 * cm

    c.save()
    buffer.seek(0)
    return buffer