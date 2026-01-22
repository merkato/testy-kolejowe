from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
from PIL import Image as PILImage
import io
import os

# --- KONFIGURACJA MARGINESÓW ---
MARGIN = 1 * cm
WIDTH, HEIGHT = A4

class NumberedCanvas(canvas.Canvas):
    """Klasa obsługująca numerację stron typu 'Strona x z y'."""
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._start_new_page()

    def save(self):
        num_pages = len(self._saved_page_states)
        font_name = get_font_name()
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages, font_name)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count, font_name):
        self.setFont(font_name, 9)
        # Numeracja w dolnym prawym rogu, zachowując margines 1cm
        self.drawRightString(WIDTH - MARGIN, MARGIN / 2, f"Strona {self._pageNumber} z {page_count}")

def get_font_name():
    try:
        font_path = '/usr/share/fonts/truetype/freefont/FreeSans.ttf'
        if os.path.exists(font_path):
            pdfmetrics.registerFont(TTFont('FreeSans', font_path))
            return 'FreeSans'
    except Exception:
        pass
    return 'Helvetica'

def draw_first_page_header(c, font_name, title, logo_file=None):
    """Nagłówek wyświetlany TYLKO na pierwszej stronie."""
    # Logo w prawym górnym rogu (1cm od krawędzi)
    if logo_file:
        try:
            logo_img = ImageReader(logo_file)
            img_w, img_h = logo_img.getSize()
            aspect = img_h / img_w
            display_w = 3 * cm
            display_h = display_w * aspect
            c.drawImage(logo_img, WIDTH - MARGIN - display_w, HEIGHT - MARGIN - display_h + 0.5*cm, 
                        width=display_w, height=display_h, mask='auto')
        except:
            pass

    c.setFont(font_name, 16)
    c.drawCentredString(WIDTH / 2, HEIGHT - MARGIN - 1 * cm, title)
    c.setFont(font_name, 10)
    # Pola na dane (zachowując 1cm marginesu z lewej i prawej)
    c.drawString(MARGIN, HEIGHT - MARGIN - 2.5 * cm, "Imię i nazwisko: ............................................................ Data: ....................")
    c.line(MARGIN, HEIGHT - MARGIN - 2.7 * cm, WIDTH - MARGIN, HEIGHT - MARGIN - 2.7 * cm)

def create_test_paper_pdf(questions, profession_name, logo_file=None):
    buffer = io.BytesIO()
    # Używamy NumberedCanvas zamiast zwykłego canvas.Canvas
    c = NumberedCanvas(buffer, pagesize=A4)
    font_name = get_font_name()
    
    title = f"Arkusz Egzaminacyjny: {profession_name}"
    draw_first_page_header(c, font_name, title, logo_file)
    
    # Start pozycji Y na pierwszej stronie (niżej przez nagłówek)
    y = HEIGHT - MARGIN - 4 * cm
    
    for i, q in enumerate(questions):
        # Sprawdzanie miejsca na stronie
        needed_space = 2 * cm
        if q.image_path: needed_space += 5 * cm
        if q.image_a or q.image_b or q.image_c: needed_space += 4 * cm
        
        if y < needed_space:
            c.showPage()
            # Na kolejnych stronach startujemy od górnego marginesu (brak nagłówka)
            y = HEIGHT - MARGIN - 1 * cm

        # Treść pytania (zawijanie tekstu na szerokość WIDTH - 2*MARGIN)
        c.setFont(font_name, 11)
        c.drawString(MARGIN, y, f"{i+1}. {q.content}")
        y -= 0.8 * cm

        # Obrazek główny (skalowany do szerokości arkusza minus marginesy)
        if q.image_path and os.path.exists(q.image_path):
            try:
                c.drawImage(q.image_path, MARGIN + 1*cm, y - 4.5 * cm, width=WIDTH - 2*MARGIN - 2*cm, height=4.5 * cm, preserveAspectRatio=True, anchor='sw')
                y -= 5 * cm
            except:
                y -= 0.5 * cm

        # Odpowiedzi A, B, C
        c.setFont(font_name, 10)
        labels = [("A", q.ans_a, q.image_a), ("B", q.ans_b, q.image_b), ("C", q.ans_c, q.image_c)]
        
        for label, text, img_path in labels:
            c.drawString(MARGIN + 0.5 * cm, y, f"{label}) {text if text else ''}")
            
            if img_path and os.path.exists(img_path):
                try:
                    y -= 3.2 * cm
                    c.drawImage(img_path, MARGIN + 1 * cm, y, width=4 * cm, height=3 * cm, preserveAspectRatio=True, anchor='sw')
                except:
                    y -= 0.5 * cm
            y -= 0.7 * cm
        
        y -= 0.5 * cm # Odstęp między pytaniami

    c.save()
    buffer.seek(0)
    return buffer

def create_answer_key_pdf(questions, profession_name):
    """Osobny arkusz z kluczem odpowiedzi."""
    buffer = io.BytesIO()
    c = NumberedCanvas(buffer, pagesize=A4)
    font_name = get_font_name()
    
    c.setFont(font_name, 16)
    c.drawCentredString(WIDTH / 2, HEIGHT - MARGIN - 1 * cm, f"KLUCZ ODPOWIEDZI")
    c.setFont(font_name, 10)
    c.drawCentredString(WIDTH / 2, HEIGHT - MARGIN - 1.7 * cm, f"Arkusz: {profession_name}")
    c.line(MARGIN, HEIGHT - MARGIN - 2.2 * cm, WIDTH - MARGIN, HEIGHT - MARGIN - 2.2 * cm)

    y = HEIGHT - MARGIN - 3 * cm
    col = 0
    
    for i, q in enumerate(questions):
        c.setFont(font_name, 11)
        x_pos = MARGIN + (col * 6 * cm)
        c.drawString(x_pos, y, f"{i+1}: [ {q.correct_ans} ]")
        
        y -= 0.8 * cm
        if y < MARGIN + 1 * cm:
            if col < 2:
                col += 1
                y = HEIGHT - MARGIN - 3 * cm
            else:
                c.showPage()
                col = 0
                y = HEIGHT - MARGIN - 3 * cm

    c.save()
    buffer.seek(0)
    return buffer