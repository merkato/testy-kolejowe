import io
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from db import Question # Potrzebne do odczytu treści błędów jeśli trzeba
import json
import datetime

def generate_session_report(session_obj, examiner_user):
    """
    Tworzy PDF z raportem zbiorczym z sesji egzaminacyjnej.
    """
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    margin = 1.5 * cm

    # --- NAGŁÓWEK ---
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width / 2, height - 2 * cm, "RAPORT Z EGZAMINU")
    
    c.setFont("Helvetica", 10)
    c.drawString(margin, height - 3.5 * cm, f"Egzaminator: {examiner_user.username}")
    c.drawRightString(width - margin, height - 3.5 * cm, f"Data: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    c.drawString(margin, height - 4.0 * cm, f"Numer szkolenia/egzaminu: {session_obj.training_number}")
    c.drawRightString(width - margin, height - 4.0 * cm, f"Status: {session_obj.status.value.upper()}")
    
    c.setLineWidth(1)
    c.line(margin, height - 4.5 * cm, width - margin, height - 4.5 * cm)

    # --- STATYSTYKI OGÓLNE ---
    finished_examinees = [e for e in session_obj.examinees if e.is_finished]
    passed_count = sum(1 for e in finished_examinees if e.score_percent >= session_obj.pass_threshold)
    
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin, height - 5.5 * cm, "Podsumowanie wyników:")
    c.setFont("Helvetica", 10)
    c.drawString(margin + 0.5 * cm, height - 6.2 * cm, f"Liczba uczestników: {len(session_obj.examinees)}")
    c.drawString(margin + 0.5 * cm, height - 6.7 * cm, f"Egzamin ukończyło: {len(finished_examinees)}")
    c.drawString(margin + 0.5 * cm, height - 7.2 * cm, f"Wynik pozytywny: {passed_count}")
    c.drawString(margin + 0.5 * cm, height - 7.7 * cm, f"Wynik negatywny: {len(finished_examinees) - passed_count}")

    # --- TABELA WYNIKÓW ---
    data = [["Nr Dziennika", "Start", "Czas pracy", "Błędy/Focus", "Wynik %", "Status"]]
    
    for e in session_obj.examinees:
        start_t = e.start_datetime.strftime("%H:%M") if e.start_datetime else "---"
        
        # Obliczanie czasu pracy
        duration = "---"
        if e.start_datetime and e.end_datetime:
            diff = e.end_datetime - e.start_datetime
            duration = f"{int(diff.total_seconds() // 60)}m {int(diff.total_seconds() % 60)}s"
        
        status_text = "ZALICZONY" if e.score_percent >= session_obj.pass_threshold else "NIEZALICZONY"
        if not e.is_finished:
            status_text = "NIEUKOŃCZONY"
            
        data.append([
            str(e.journal_number),
            start_t,
            duration,
            f"F: {e.focus_loss_counter}",
            f"{e.score_percent:.1f}%",
            status_text
        ])

    # Stylizacja tabeli
    table = Table(data, colWidths=[3*cm, 3*cm, 3*cm, 3*cm, 3*cm, 3.5*cm])
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
    ])
    
    # Warunkowe kolorowanie statusu (Zielony/Czerwony)
    for i in range(1, len(data)):
        if data[i][5] == "ZALICZONY":
            style.add('TEXTCOLOR', (5, i), (5, i), colors.green)
        elif data[i][5] == "NIEZALICZONY":
            style.add('TEXTCOLOR', (5, i), (5, i), colors.red)

    table.setStyle(style)
    
    # Rysowanie tabeli
    tw, th, _ = table.wrapOn(c, margin, margin)
    table.drawOn(c, margin, height - 9 * cm - th)

    c.save()
    buffer.seek(0)
    return buffer