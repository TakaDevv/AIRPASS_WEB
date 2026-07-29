import os
import uuid
import qrcode
from datetime import datetime
from reportlab.lib.pagesizes import A5
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.pdfgen import canvas

from config import Config


def ensure_folders():
    os.makedirs(Config.QRCODES_FOLDER, exist_ok=True)
    os.makedirs(Config.TICKETS_PDF_FOLDER, exist_ok=True)


def generate_ticket_code():
    """Génère un identifiant unique de billet (simule un ID crypté)."""
    return f"AIRPASS-{uuid.uuid4().hex[:10].upper()}"


def generate_qr_code(ticket_code):
    """Génère une image QR Code représentant le billet et retourne le nom de fichier."""
    ensure_folders()
    filename = f"qr_{ticket_code}.png"
    filepath = os.path.join(Config.QRCODES_FOLDER, filename)

    img = qrcode.make(ticket_code)
    img.save(filepath)
    return filename


def generate_ticket_pdf(ticket, user, event, stadium, seat, parking=None):
    """Génère un PDF de billet et retourne le nom de fichier."""
    ensure_folders()
    filename = f"ticket_{ticket.code}.pdf"
    filepath = os.path.join(Config.TICKETS_PDF_FOLDER, filename)

    c = canvas.Canvas(filepath, pagesize=A5)
    width, height = A5

    # Bandeau d'en-tête bleu foncé
    c.setFillColor(colors.HexColor("#0B1F3A"))
    c.rect(0, height - 30 * mm, width, 30 * mm, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 20)
    c.drawString(15 * mm, height - 20 * mm, "AIRPASS")
    c.setFont("Helvetica", 10)
    c.drawString(15 * mm, height - 26 * mm, "Billet electronique officiel")

    y = height - 42 * mm
    c.setFillColor(colors.HexColor("#0B1F3A"))
    c.setFont("Helvetica-Bold", 13)
    c.drawString(15 * mm, y, event.title)

    y -= 8 * mm
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.black)
    c.drawString(15 * mm, y, f"Stade : {stadium.name} - {stadium.city}")
    y -= 6 * mm
    c.drawString(15 * mm, y, f"Date : {event.date.strftime('%d/%m/%Y %H:%M')}")
    y -= 6 * mm
    c.drawString(15 * mm, y, f"Spectateur : {user.fullname}")
    y -= 6 * mm
    c.drawString(15 * mm, y, f"Place : {seat.label}")
    y -= 6 * mm
    c.setFillColor(colors.HexColor("#C8102E"))
    c.setFont("Helvetica-Bold", 10)
    c.drawString(15 * mm, y, f"Code billet : {ticket.code}")

    if parking:
        y -= 6 * mm
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 10)
        c.drawString(15 * mm, y, f"Parking attribue : {parking.parking_number}")

    # QR code
    qr_path = os.path.join(Config.QRCODES_FOLDER, ticket.qr_code)
    if os.path.exists(qr_path):
        c.drawImage(qr_path, width - 55 * mm, 15 * mm, width=40 * mm, height=40 * mm)

    c.setFont("Helvetica-Oblique", 8)
    c.setFillColor(colors.grey)
    c.drawString(15 * mm, 10 * mm, "Ce billet est personnel et non transferable. Presentez-le a l'entree du stade.")

    c.showPage()
    c.save()
    return filename
