from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
import io
import os

# --- KONFIGURACJA ---
MARGIN = 1 * cm
WIDTH, HEIGHT = A4
FONT_NAME = "Helvetica" # Domyślna

def setup_fonts():
    """Rejestruje czcionkę FreeSans dla polskich znaków."""
    global FONT_NAME
    paths = [
        '/usr/share/fonts/truetype/freefont/FreeSans.ttf',
        'C:\\Windows\\Fonts\\arial.ttf' # Opcjonalnie dla Windows
    ]
    for p in paths:
        if os.path.exists(p):
            pdfmetrics.registerFont(TTFont('FreeSans', p))
            FONT_NAME = 'FreeSans'
            break

def draw_header(c, title, logo_file):
    """Nagłówek tylko na 1. stronie."""
    if logo_file:
        try:
            logo_file.seek(0)
            logo_img = ImageReader(logo_file)
            img_w, img_h = logo_img.getSize()
            aspect = img_h / img_w
            display_w = 3 * cm
            display_h = display_w * aspect
            # Logo w prawym górnym rogu
            c.drawImage(logo_img, WIDTH - MARGIN - display_w, HEIGHT - MARGIN - display_h + 0.5*cm, 
                        width=display_w, height=display_h, mask='auto')
        except:
            pass

    c.setFont(FONT_NAME, 16)
    c.drawCentredString(WIDTH / 2, HEIGHT - MARGIN - 1 * cm, title)
    c.setFont(FONT_NAME, 10)
    c.drawString(MARGIN, HEIGHT - MARGIN - 2.5 * cm, "Imię i nazwisko: ............................................................ Data: ....................")
    c.line(MARGIN, HEIGHT - MARGIN - 2.7 * cm, WIDTH - MARGIN, HEIGHT - MARGIN - 2.7 * cm)

def draw_footer(c, page_num, total_pages):
    """Stopka z numeracją Strona x z y."""
    c.setFont(FONT_NAME, 8)
    text = f"Strona {page_num} z {total_pages}"
    c.drawRightString(WIDTH - MARGIN, MARGIN / 2, text)

def generate_exam_content(c, questions, profession_name, logo_file, total_pages=None):
    """Główna logika rysowania pytań."""
    title = f"Arkusz Egzaminacyjny: {profession_name}"
    
    # 1. Strona - Nagłówek
    draw_header(c, title, logo_file)
    y = HEIGHT - MARGIN - 4 * cm
    
    for i, q in enumerate(questions):
        # Sprawdzanie miejsca (pytanie + margines bezpieczeństwa)
        needed = 2.5 * cm
        if q.image_path: needed += 5 * cm
        if any([q.image_a, q.image_b, q.image_c]): needed += 4 * cm
        
        if y < needed:
            if total_pages: draw_footer(c, c.getPageNumber(), total_pages)
            c.showPage()
            y = HEIGHT - MARGIN - 1 * cm # Brak nagłówka na kolejnych stronach

        # Treść pytania
        c.setFont(FONT_NAME, 11)
        c.drawString(MARGIN, y, f"{i+1}. {q.content}")
        y -= 0.8 * cm

        # Obrazek główny
        if q.image_path and os.path.exists(q.image_path):
            try:
                c.drawImage(q.image_path, MARGIN + 1*cm, y - 4.5*cm, width=WIDTH-2*MARGIN-2*cm, height=4.5*cm, preserveAspectRatio=True, anchor='sw')
                y -= 5 * cm
            except: y -= 0.5 * cm

        # Odpowiedzi
        c.setFont(FONT_NAME, 10)
        for label, text, img in [("A", q.ans_a, q.image_a), ("B", q.ans_b, q.image_b), ("C", q.ans_c, q.image_c)]:
            c.drawString(MARGIN + 0.5*cm, y, f"{label}) {text if text else ''}")
            if img and os.path.exists(img):
                try:
                    y -= 3.2 * cm
                    c.drawImage(img, MARGIN + 1*cm, y, width=4*cm, height=3*cm, preserveAspectRatio=True, anchor='sw')
                except: y -= 0.5 * cm
            y -= 0.7 * cm
        y -= 0.5 * cm

    if total_pages: draw_footer(c, c.getPageNumber(), total_pages)

def create_test_paper_pdf(questions, profession_name, logo_file=None):
    setup_fonts()
    
    # KROK 1: Przebieg próbny (liczenie stron)
    dummy_buffer = io.BytesIO()
    c_dummy = canvas.Canvas(dummy_buffer, pagesize=A4)
    generate_exam_content(c_dummy, questions, profession_name, logo_file, total_pages=None)
    total_pages = c_dummy.getPageNumber()
    c_dummy.save()

    # KROK 2: Właściwe generowanie
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    generate_exam_content(c, questions, profession_name, logo_file, total_pages=total_pages)
    c.save()
    
    buffer.seek(0)
    return buffer

def create_answer_key_pdf(questions, profession_name):
    setup_fonts()
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    
    c.setFont(FONT_NAME, 16)
    c.drawCentredString(WIDTH/2, HEIGHT - MARGIN - 1*cm, "KLUCZ ODPOWIEDZI")
    c.setFont(FONT_NAME, 10)
    c.drawCentredString(WIDTH/2, HEIGHT - MARGIN - 1.7*cm, f"Arkusz: {profession_name}")
    c.line(MARGIN, HEIGHT-MARGIN-2.2*cm, WIDTH-MARGIN, HEIGHT-MARGIN-2.2*cm)

    y = HEIGHT - MARGIN - 3*cm
    col = 0
    for i, q in enumerate(questions):
        x_pos = MARGIN + (col * 6 * cm)
        c.drawString(x_pos, y, f"{i+1}: [ {q.correct_ans} ]")
        y -= 0.8 * cm
        if y < MARGIN + 1*cm:
            if col < 2:
                col += 1
                y = HEIGHT - MARGIN - 3*cm
            else:
                c.showPage()
                col = 0
                y = HEIGHT - MARGIN - 3*cm
    
    c.save()
    buffer.seek(0)
    return buffer