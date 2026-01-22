# pdf_service.py
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image as PILImage
import io

def create_test_pdf(questions, profession_name, logo_file=None):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # Próba załadowania czcionki z polskimi znakami
    try:
        pdfmetrics.registerFont(TTFont('FreeSans', '/usr/share/fonts/truetype/freefont/FreeSans.ttf'))
        font_name = 'FreeSans'
    except:
        font_name = 'Helvetica'

    def draw_header(current_canvas, current_y):
        # Obsługa logotypu, jeśli został przesłany
        if logo_file:
            img = PILImage.open(logo_file)
            img_w, img_h = img.size
            aspect = img_h / img_w
            display_w = 3 * cm
            display_h = display_w * aspect
            
            # Rysowanie logo w prawym górnym rogu
            c.saveState()
            c.drawImage(logo_file, width - 4*cm, height - 2.5*cm, width=display_w, height=display_h, mask='auto')
            c.restoreState()

        current_canvas.setFont(font_name, 16)
        current_canvas.drawCentredString(width/2, height - 2*cm, f"Arkusz Egzaminacyjny: {profession_name}")
        current_canvas.setFont(font_name, 10)
        current_canvas.drawString(2*cm, height - 3*cm, "Imię i nazwisko: ............................................................ Data: ....................")
        current_canvas.line(2*cm, height - 3.2*cm, width - 2*cm, height - 3.2*cm)

    draw_header(c, height)
    y = height - 4.5*cm
    
    # Renderowanie pytań
    for i, q in enumerate(questions):
        if y < 3*cm:
            c.showPage()
            draw_header(c, height)
            y = height - 4.5*cm
            
        c.setFont(font_name, 11)
        c.drawString(2*cm, y, f"{i+1}. {q.content}")
        y -= 0.6*cm
        
        c.setFont(font_name, 10)
        c.drawString(2.5*cm, y, f"A) {q.ans_a}")
        y -= 0.5*cm
        c.drawString(2.5*cm, y, f"B) {q.ans_b}")
        y -= 0.5*cm
        c.drawString(2.5*cm, y, f"C) {q.ans_c}")
        y -= 1.2*cm

    # Klucz odpowiedzi na nowej stronie
    c.showPage()
    c.setFont(font_name, 14)
    c.drawCentredString(width/2, height - 2*cm, "KLUCZ ODPOWIEDZI")
    y = height - 4*cm
    
    col = 0
    for i, q in enumerate(questions):
        c.setFont(font_name, 10)
        c.drawString(2*cm + (col * 3.5*cm), y, f"{i+1}: [ {q.correct_ans} ]")
        y -= 0.6*cm
        if y < 2*cm:
            y = height - 4*cm
            col += 1

    c.save()
    buffer.seek(0)
    return buffer