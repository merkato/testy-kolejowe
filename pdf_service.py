from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph
import io
import os
import html

# --- KONFIGURACJA ---
MARGIN = 1 * cm
WIDTH, HEIGHT = A4
FONT_NAME = "Helvetica"

def setup_fonts():
    """Konfiguruje czcionkę z obsługą polskich znaków."""
    global FONT_NAME
    paths = ['/usr/share/fonts/truetype/freefont/FreeSans.ttf', 'FreeSans.ttf']
    for p in paths:
        if os.path.exists(p):
            pdfmetrics.registerFont(TTFont('FreeSans', p))
            FONT_NAME = 'FreeSans'
            break

def draw_header(c, title, logo_file):
    """Nagłówek na 1. stronie (logo, tytuł, dane osobowe)."""
    if logo_file:
        try:
            logo_file.seek(0)
            logo_img = ImageReader(logo_file)
            img_w, img_h = logo_img.getSize()
            aspect = img_h / img_w
            display_w = 2.5 * cm
            display_h = display_w * aspect
            c.drawImage(logo_img, WIDTH - MARGIN - display_w, HEIGHT - MARGIN - display_h + 0.5*cm, 
                        width=display_w, height=display_h, mask='auto')
        except: pass

    c.setFont(FONT_NAME, 16)
    c.drawCentredString(WIDTH / 2, HEIGHT - MARGIN - 1 * cm, title)
    c.setFont(FONT_NAME, 10)
    c.drawString(MARGIN, HEIGHT - MARGIN - 2.5 * cm, "Imię i nazwisko: ............................................................ Data: ....................")
    c.line(MARGIN, HEIGHT - MARGIN - 2.7 * cm, WIDTH - MARGIN, HEIGHT - MARGIN - 2.7 * cm)

def draw_footer(c, page_num, total_pages):
    """Stopka 'Strona x z y'."""
    c.setFont(FONT_NAME, 9)
    text = f"Strona {page_num} z {total_pages}"
    c.drawRightString(WIDTH - MARGIN, MARGIN / 2, text)

def generate_exam_content(c, questions, profession_name, logo_file, total_pages=None):
    """Główna logika z zawijaniem tekstu Paragraph."""
    styles = getSampleStyleSheet()
    q_style = ParagraphStyle('Quest', fontName=FONT_NAME, fontSize=11, leading=13, spaceAfter=4)
    a_style = ParagraphStyle('Ans', fontName=FONT_NAME, fontSize=10, leading=12, leftIndent=0.5*cm)
    
    available_width = WIDTH - 2 * MARGIN
    title = f"Arkusz Egzaminacyjny: {profession_name}"
    
    draw_header(c, title, logo_file)
    y = HEIGHT - MARGIN - 4 * cm

    for i, q in enumerate(questions):
        # Przygotowanie paragrafów
        q_p = Paragraph(f"<b>{i+1}. {html.escape(q.content)}</b>", q_style)
        ans_p = [
            Paragraph(f"A) {html.escape(q.ans_a if q.ans_a else '')}", a_style),
            Paragraph(f"B) {html.escape(q.ans_b if q.ans_b else '')}", a_style),
            Paragraph(f"C) {html.escape(q.ans_c if q.ans_c else '')}", a_style)
        ]

        # Obliczanie wysokości bloku
        _, h_q = q_p.wrap(available_width, HEIGHT)
        h_ans = sum([p.wrap(available_width, HEIGHT)[1] for p in ans_p])
        
        needed = h_q + h_ans + 1.5 * cm
        if q.image_path: needed += 5 * cm
        # Dodajemy miejsce na grafiki w odpowiedziach
        for img in [q.image_a, q.image_b, q.image_c]:
            if img: needed += 3.5 * cm

        # Nowa strona jeśli brak miejsca
        if y < needed:
            if total_pages: draw_footer(c, c.getPageNumber(), total_pages)
            c.showPage()
            y = HEIGHT - MARGIN - 1 * cm

        # Rysowanie pytania
        q_p.drawOn(c, MARGIN, y - h_q)
        y -= (h_q + 0.3 * cm)

        # Obrazek główny pytania
        if q.image_path and os.path.exists(q.image_path):
            try:
                c.drawImage(q.image_path, MARGIN + 1*cm, y - 4.5*cm, width=available_width-2*cm, height=4.5*cm, preserveAspectRatio=True, anchor='sw')
                y -= 5 * cm
            except: y -= 0.5 * cm

        # Rysowanie odpowiedzi
        img_fields = [q.image_a, q.image_b, q.image_c]
        for idx, p in enumerate(ans_p):
            _, h = p.wrap(available_width, HEIGHT)
            p.drawOn(c, MARGIN, y - h)
            y -= h
            
            # Grafika w odpowiedzi (jeśli istnieje)
            img_path = img_fields[idx]
            if img_path and os.path.exists(img_path):
                try:
                    y -= 3.2 * cm
                    c.drawImage(img_path, MARGIN + 1*cm, y, width=4*cm, height=3*cm, preserveAspectRatio=True, anchor='sw')
                    y -= 0.2 * cm
                except: y -= 0.5 * cm
            y -= 0.2 * cm
        
        y -= 0.6 * cm # Odstęp między pytaniami

    if total_pages: draw_footer(c, c.getPageNumber(), total_pages)

def create_test_paper_pdf(questions, profession_name, logo_file=None):
    setup_fonts()
    # Przebieg próbny do zliczenia stron
    tmp = io.BytesIO()
    c_tmp = canvas.Canvas(tmp, pagesize=A4)
    generate_exam_content(c_tmp, questions, profession_name, logo_file, total_pages=None)
    total_pages = c_tmp.getPageNumber()
    c_tmp.save()

    # Przebieg właściwy
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
    c.setFont(FONT_NAME, 16); c.drawCentredString(WIDTH/2, HEIGHT-MARGIN-1*cm, "KLUCZ ODPOWIEDZI")
    c.setFont(FONT_NAME, 10); c.drawCentredString(WIDTH/2, HEIGHT-MARGIN-1.7*cm, f"Arkusz: {profession_name}")
    c.line(MARGIN, HEIGHT-MARGIN-2.2*cm, WIDTH-MARGIN, HEIGHT-MARGIN-2.2*cm)
    y = HEIGHT - MARGIN - 3*cm; col = 0
    for i, q in enumerate(questions):
        x = MARGIN + (col * 6 * cm)
        c.drawString(x, y, f"{i+1}: [ {q.correct_ans} ]")
        y -= 0.8 * cm
        if y < MARGIN + 1*cm:
            if col < 2: col += 1; y = HEIGHT - MARGIN - 3*cm
            else: c.showPage(); col = 0; y = HEIGHT - MARGIN - 3*cm
    c.save(); buffer.seek(0)
    return buffer