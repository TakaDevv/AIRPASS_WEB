import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "airpass-dev-secret-key-2026-change-me")
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(BASE_DIR, "database.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Dossiers de génération (QR codes, PDF)
    QRCODES_FOLDER = os.path.join(BASE_DIR, "static", "qrcodes")
    TICKETS_PDF_FOLDER = os.path.join(BASE_DIR, "static", "tickets_pdf")

    WTF_CSRF_ENABLED = True
