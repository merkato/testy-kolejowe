import io
import os
import zipfile
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import simpleSplit, ImageReader

# --- KONFIGURACJA CZCIONEK (FreeSans z Dockera) ---
def register_fonts():
    font_dir = "/usr/share/fonts/truetype/freefont/"
    reg = os.path.join(font_dir, "FreeSans.ttf")
    bold = os.path.join(font_dir, "FreeSansBold.ttf")
    if os.path.exists(reg):
        pdfmetrics.registerFont(TTFont('FreeSans', reg))
        pdfmetrics.registerFont(TTFont('FreeSansBold', bold))
        return 'FreeSans', 'FreeSansBold'
    return 'Helvetica', 'Helvetica-Bold'

FONT_NAME, FONT_BOLD = register_fonts()
WIDTH, HEIGHT = A4
MARGIN = 1.5 * cm
DRAW_WIDTH = WIDTH - 2 * MARGIN
LOGO_LIMIT = 2.5 * cm
Q_IMG_SIZE = 5.5 * cm 
A_IMG_SIZE = 2.5 * cm

def draw_page_info(c, page_num):
    """Rysuje numerację stron w stopce."""
    c.saveState()
    c.setFont(FONT_NAME, 8)
    c.drawRightString(WIDTH - MARGIN, MARGIN / 2, f"Strona {page_num}")
    c.restoreState()

def calculate_question_height(q, draw_width):
    """Oblicza wysokość całego bloku pytania przed rysowaniem."""
    q_lines = len(simpleSplit(f"X. {q.content}", FONT_BOLD, 10, draw_width))
    total_h = q_lines * 0.45 * cm
    
    has_q_img = bool(q.image_path)
    total_ans_len = len(str(q.ans_a) + str(q.ans_b) + str(q.ans_c))
    # Układ poziomy: krótkie teksty + grafiki we wszystkich odp + brak głównego obrazka
    use_horiz = all([q.image_a, q.image_b, q.image_c]) and total_ans_len < 50 and not has_q_img
    
    ans_limit_w = draw_width - (Q_IMG_SIZE + 0.5*cm) if has_q_img else draw_width
    
    if use_horiz:
        ans_h = 0.45 * cm + A_IMG_SIZE + 0.3 * cm
    else:
        ans_h = 0
        for txt, img in [(q.ans_a, q.image_a), (q.ans_b, q.image_b), (q.ans_c, q.image_c)]:
            lines = len(simpleSplit(f"X) {txt}", FONT_NAME, 10, ans_limit_w - 0.6 * cm))
            ans_h += lines * 0.45 * cm
            if img:
                ans_h += A_IMG_SIZE + 0.3 * cm
    
    q_img_h = Q_IMG_SIZE if has_q_img else 0
    return total_h + max(ans_h, q_img_h) + 1.0 * cm

def draw_header_elements(c, profession_name, topics_str, group_label, logo_file, is_key, page_num):
    """Nagłówek: logo i metryczka tylko na 1. stronie."""
    c.saveState()
    top_y = HEIGHT - MARGIN
    
    # 1. LOGO (Tylko 1. strona, obniżone o 0.2cm względem marginesu)
    logo_bottom_y = top_y
    if logo_file and page_num == 1:
        try:
            logo_file.seek(0)
            img = ImageReader(logo_file)
            logo_bottom_y = top_y - LOGO_LIMIT - 0.2 * cm
            c.drawImage(img, WIDTH - MARGIN - LOGO_LIMIT, logo_bottom_y, 
                        width=LOGO_LIMIT, height=LOGO_LIMIT, preserveAspectRatio=True, mask='auto')
        except Exception:
            pass

    if page_num == 1:
        if not is_key:
            # Dane kandydata
            c.setFont(FONT_NAME, 10)
            c.drawString(MARGIN, top_y, "Imię i nazwisko: ..................................................................................")
            
            # Grupa i Data pod logo
            y_labels = min(logo_bottom_y, top_y - 1.2 * cm) - 0.5 * cm
            c.setFont(FONT_BOLD, 11)
            c.drawRightString(WIDTH - MARGIN - 0.2*cm, y_labels, f"Test ({group_label})")
            c.setFont(FONT_NAME, 10)
            c.drawRightString(WIDTH - MARGIN - 0.2*cm, y_labels - 0.6 * cm, "Data: ....................................")
            start_y = y_labels - 1.2 * cm
        else:
            start_y = top_y - 1.0 * cm

        # Tytuł i Tematyka
        c.setFont(FONT_BOLD, 14)
        c.drawCentredString(WIDTH / 2, start_y, f"Arkusz: {profession_name}")
        c.setFont(FONT_NAME, 9)
        c.drawCentredString(WIDTH / 2, start_y - 0.6 * cm, f"Tematyka: {topics_str}")
        
        # Linia oddzielająca (dynamiczna wysokość pod tematyką)
        line_y = start_y - 1.2 * cm
        c.setLineWidth(0.5)
        c.line(MARGIN, line_y, WIDTH - MARGIN, line_y)
        res_y = line_y - 0.8 * cm
    else:
        # Kolejne strony zaczynają się od razu u góry
        res_y = top_y - 0.5 * cm

    c.restoreState()
    return res_y

def draw_img(c, src, x, y, size):
    """Rysuje i skaluje obrazki w treści."""
    if not src: 
        return y
    try:
        img = ImageReader(src)
        c.drawImage(img, x, y - size, width=size, height=size, preserveAspectRatio=True, mask='auto')
        return y - size - 0.3 * cm
    except Exception: 
        return y

# --- GŁÓWNE FUNKCJE GENERUJĄCE ---

def create_test_paper_pdf(questions, profession, topics_str, logo_file=None, group_label="A"):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    page_num = 1
    y = draw_header_elements(c, profession.name, topics_str, group_label, logo_file, False, page_num)
    draw_page_info(c, page_num)
    
    for i, q in enumerate(questions):
        # Sprawdzanie czy pytanie się zmieści
        q_h = calculate_question_height(q, DRAW_WIDTH)
        if y - q_h < 1.5 * cm:
            c.showPage()
            page_num += 1
            y = draw_header_elements(c, profession.name, topics_str, group_label, logo_file, False, page_num)
            draw_page_info(c, page_num)

        c.setFont(FONT_BOLD, 10)
        lines = simpleSplit(f"{i+1}. {q.content}", FONT_BOLD, 10, DRAW_WIDTH)
        for line in lines:
            c.drawString(MARGIN, y, line)
            y -= 0.45 * cm
        
        y_start = y
        has_q_img = bool(q.image_path)
        total_ans_len = len(str(q.ans_a) + str(q.ans_b) + str(q.ans_c))
        use_horiz = all([q.image_a, q.image_b, q.image_c]) and total_ans_len < 50 and not has_q_img

        if use_horiz:
            col_w = DRAW_WIDTH / 3
            for idx, (lbl, txt, img) in enumerate([("A", q.ans_a, q.image_a), ("B", q.ans_b, q.image_b), ("C", q.ans_c, q.image_c)]):
                cur_x = MARGIN + (idx * col_w)
                c.setFont(FONT_NAME, 10)
                c.drawString(cur_x, y_start, f"{lbl}) {txt}")
                draw_img(c, img, cur_x + 0.5*cm, y_start - 0.2*cm, A_IMG_SIZE)
            y_ans = y_start - A_IMG_SIZE - 0.8 * cm
        else:
            ans_w = DRAW_WIDTH - (Q_IMG_SIZE + 0.5*cm) if has_q_img else DRAW_WIDTH
            y_cur = y_start
            c.setFont(FONT_NAME, 10)
            for lbl, txt, img in [("A", q.ans_a, q.image_a), ("B", q.ans_b, q.image_b), ("C", q.ans_c, q.image_c)]:
                ans_lines = simpleSplit(f"{lbl}) {txt}", FONT_NAME, 10, ans_w - 0.6 * cm)
                for al in ans_lines:
                    c.drawString(MARGIN + 0.6*cm, y_cur, al)
                    y_cur -= 0.45 * cm
                if img: 
                    y_cur = draw_img(c, img, MARGIN + 1.2*cm, y_cur, A_IMG_SIZE)
            y_ans = y_cur
        
        y_q_img = y_start
        if has_q_img:
            y_q_img = draw_img(c, q.image_path, WIDTH - MARGIN - Q_IMG_SIZE, y_start, Q_IMG_SIZE)
        
        y = min(y_ans, y_q_img) - 0.6 * cm
            
    c.save()
    buffer.seek(0)
    return buffer

def create_answer_key_pdf(questions, profession, group_label="A"):
    """Generuje klucz odpowiedzi jako lista."""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    y = draw_header_elements(c, f"KLUCZ ODPOWIEDZI - {profession.name}", "Klucz", group_label, None, True, 1)
    draw_page_info(c, 1)
    
    c.setFont(FONT_NAME, 11)
    for i, q in enumerate(questions):
        if y < 2*cm:
            c.showPage()
            y = HEIGHT - MARGIN - 1 * cm
            draw_page_info(c, "cd.")
        c.drawString(MARGIN, y, f"Pytanie {i+1}: Poprawna odpowiedź {q.correct_ans}")
        y -= 0.7 * cm
    c.save()
    buffer.seek(0)
    return buffer

def create_full_export_zip(all_sets):
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        for s in all_sets:
            zf.writestr(f"Arkusz_Grupa_{s['label']}.pdf", s['test'].getvalue())
            zf.writestr(f"Klucz_Grupa_{s['label']}.pdf", s['key'].getvalue())
    zip_buffer.seek(0)
    return zip_buffer