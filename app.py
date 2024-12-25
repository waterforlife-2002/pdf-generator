import os
from flask import Flask, request, render_template, send_file, session, redirect, url_for
from PyPDF2 import PdfReader, PdfWriter
from fpdf import FPDF
from PIL import Image
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# Pfad zur Service Account Datei
SERVICE_ACCOUNT_FILE = '/Users/imranrana/Desktop/brunnen-projekt/config/google_service_account.json'

# Google Sheets API-Scopes und die Service Account Anmeldeinformationen laden
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

# Credentials aus der Service Account Datei laden
creds = Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)

# Verbindung zur Google Sheets API herstellen
service = build('sheets', 'v4', credentials=creds)

# Die Spreadsheet-ID (ID aus der URL deines Sheets)
SPREADSHEET_ID = '1elVTaKWwoYO5yXnFkd-OTEjdukYqWQXpU5GO23lIurI'

# Der Bereich, den du abrufen möchtest (z.B. A1 bis Z1000)
RANGE_NAME = 'Tabellenblatt1!A1:Z1000'

# Daten aus der Tabelle abrufen
sheet = service.spreadsheets()
result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
values = result.get('values', [])

# Ausgabe der Daten (optional)
if not values:
    print('Keine Daten gefunden.')
else:
    for row in values:
        print(row)

# Sicherstellen, dass der Upload-Ordner existiert
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Funktion: Texthalter einfügen
def add_text_overlay(input_pdf, output_pdf, text_fields, page_number):
    reader = PdfReader(input_pdf)
    writer = PdfWriter()

    overlay_pdf_path = "text_overlay.pdf"
    overlay = FPDF()
    overlay.add_page()

    try:
        overlay.add_font("Impact", "", "fonts/impact.ttf", uni=True)
        overlay.set_font("Impact", size=21)
    except:
        overlay.set_font("Helvetica", style="B", size=21)

    overlay.set_text_color(50, 50, 50)

    for field in text_fields:
        x, y = field["x"], field["y"]
        text = field["text"]

        overlay.set_xy(x, y)
        overlay.cell(0, 10, text)

    overlay.output(overlay_pdf_path)

    overlay_reader = PdfReader(overlay_pdf_path)
    for i, page in enumerate(reader.pages):
        if i == page_number - 1:  # Seite korrekt wählen (Seite 3 ist Index 2)
            page.merge_page(overlay_reader.pages[0])
        writer.add_page(page)

    with open(output_pdf, "wb") as f:
        writer.write(f)

# Funktion: Brunnen-Bild einfügen
def add_well_image(input_pdf, output_pdf, image_path, page_number):
    reader = PdfReader(input_pdf)
    writer = PdfWriter()

    page_width, page_height = 210, 297
    max_width, max_height = 160, 125  # Etwas größer als vorher

    overlay = FPDF()
    overlay.add_page()

    with Image.open(image_path) as img:
        image_width, image_height = img.size  # Verwende image_width und image_height

    # Skaliere das Bild mit maximalen Maßen
    scale = min(max_width / image_width, max_height / image_height)
    scaled_width, scaled_height = image_width * scale, image_height * scale

    # Zentriere das Bild im unteren zwei Dritteln (leicht nach unten verschoben)
    x = (page_width - scaled_width) / 2
    y = (page_height * (2 / 3)) - 85  # Weiter unten

    overlay.image(image_path, x=x, y=y, w=image_width * scale, h=image_height * scale)  # Ändere img_width und img_height
    overlay_pdf_path = "well_image_overlay.pdf"
    overlay.output(overlay_pdf_path)

    overlay_reader = PdfReader(overlay_pdf_path)
    for i, page in enumerate(reader.pages):
        if i == page_number - 1:  # Seite 3 ist Index 2
            page.merge_page(overlay_reader.pages[0])
        writer.add_page(page)

    with open(output_pdf, "wb") as f:
        writer.write(f)

# Funktion: Signboard-Bild und -Text mit fester Position einfügen
def add_signboard_content(input_pdf, output_pdf, image_path, text, image_x, image_y, image_w, image_h, text_x, text_y, text_w, page_number):
    reader = PdfReader(input_pdf)
    writer = PdfWriter()

    overlay_pdf_path = "signboard_overlay.pdf"
    overlay = FPDF()
    overlay.add_page()

    if image_path and os.path.exists(image_path):
        # Bild einfügen
        overlay.image(image_path, x=image_x, y=image_y, w=image_w, h=image_h)
    elif text:  # Text einfügen, wenn kein Bild vorhanden ist
        try:
            overlay.add_font("Impact", "", "fonts/impact.ttf", uni=True)
            overlay.set_font("Impact", size=21)
        except:
            overlay.set_font("Helvetica", style="B", size=21)

    overlay.set_text_color(50, 50, 50)

    # Text einfügen
    if text:
        overlay.set_xy(text_x, text_y)
        overlay.multi_cell(text_w, 10, text)

    overlay.output(overlay_pdf_path)

    # Überlagern des PDFs mit dem Overlay
    overlay_reader = PdfReader(overlay_pdf_path)
    for i, page in enumerate(reader.pages):
        if i == page_number - 1:  # Seite korrekt wählen (Seite 3 ist Index 2)
            page.merge_page(overlay_reader.pages[0])
        writer.add_page(page)

    with open(output_pdf, "wb") as f:
        writer.write(f)

# Funktion: Bilder platzieren oder leere Seiten entfernen
def add_centered_images_with_scaling(input_pdf, output_pdf, image_paths, start_page, end_page):
    reader = PdfReader(input_pdf)
    writer = PdfWriter()

    for i, page in enumerate(reader.pages):
        if i < start_page - 1 or i >= end_page:
            writer.add_page(page)
        elif start_page - 1 <= i < end_page:
            if i - (start_page - 1) < len(image_paths):
                image_path = image_paths[i - (start_page - 1)]
                overlay = FPDF()
                overlay.add_page()

                with Image.open(image_path) as img:
                    img_width, img_height = img.size
                scale = min(160 / img_width, 125 / img_height)
                x = (210 - img_width * scale) / 2
                y = (297 - img_height * scale) / 2

                overlay.image(image_path, x=x, y=y, w=img_width * scale, h=img_height * scale)
                overlay_pdf_path = f"image_overlay_{i}.pdf"
                overlay.output(overlay_pdf_path)

                overlay_reader = PdfReader(overlay_pdf_path)
                writer.add_page(overlay_reader.pages[0])
            else:
                print(f"Leere Seite {i + 1} entfernt")

    with open(output_pdf, "wb") as f:
        writer.write(f)

@app.route("/", methods=["GET", "POST"])
def index():
    # Standard-Templates
    templates = ["Niger", "Benin", "Togo", "Cambodia", "Chad"]

    # Überprüfen, ob der Benutzer authentifiziert ist
    is_authenticated = session.get("google_data_authorized", False)

    # POST-Anfrage für Passwort oder andere Formulare
    if request.method == "POST":
        # Entfernte Passwortüberprüfung
        
        # Template-Auswahl und Daten von der Benutzeroberfläche
        selected_template = request.form.get("template")
        template_files = {
            "Niger": "Niger.pdf",
            "Benin": "Benin.pdf",
            "Togo": "Togo.pdf",
            "Cambodia": "Cambodia.pdf",
            "Chad": "Chad.pdf"
        }

        if selected_template not in template_files:
            return "Vorlage nicht gefunden", 400

        input_pdf = template_files[selected_template]
        spendername = request.form.get("spendername")
        brunnen_nr = request.form.get("brunnen_nr")

        if not brunnen_nr:
            return "Brunnen-Nr. fehlt", 400

        # Textfelder auf der richtigen Seite hinzufügen (Seite 3 statt Seite 2)
        text_fields = [{"x": 15, "y": 40, "text": spendername}, {"x": 172, "y": 257, "text": brunnen_nr}]
        text_pdf = f"{selected_template}_text.pdf"
        add_text_overlay(input_pdf, text_pdf, text_fields, page_number=3)

        well_image_file = request.files.get("well_image")
        if well_image_file and well_image_file.filename:
            well_image_path = os.path.join(app.config['UPLOAD_FOLDER'], well_image_file.filename)
            well_image_file.save(well_image_path)
            add_well_image(text_pdf, text_pdf, well_image_path, page_number=3)

        signboard_file = request.files.get("signboard_image")
        signboard_text = request.form.get("signboard_text")
        if signboard_file and signboard_file.filename:
            signboard_image_path = os.path.join(app.config['UPLOAD_FOLDER'], signboard_file.filename)
            signboard_file.save(signboard_image_path)
            add_signboard_content(
                text_pdf, text_pdf, 
                signboard_image_path, None, 
                image_x=123, image_y=20, image_w=70, image_h=50,  # Bild angepasst
                text_x=123, text_y=40, text_w=70, 
                page_number=3
            )
        elif signboard_text:
            add_signboard_content(
                text_pdf, text_pdf, 
                None, signboard_text, 
                image_x=123, image_y=20, image_w=70, image_h=50, 
                text_x=123, text_y=40, text_w=70, 
                page_number=3
            )

        # Hochgeladene Bilder skalieren und einfügen
        files = request.files.getlist("images")
        uploaded_images = [os.path.join(app.config['UPLOAD_FOLDER'], file.filename) for file in files if file.filename]
        for file, path in zip(files, uploaded_images):
            file.save(path)

        start_page = 12 if selected_template != "Cambodia" else 13
        end_page = 17
        final_pdf = f"{brunnen_nr}.pdf"
        add_centered_images_with_scaling(text_pdf, final_pdf, uploaded_images, start_page=start_page, end_page=end_page)

        return send_file(final_pdf, as_attachment=True)

    return render_template("index.html", templates=templates)

if __name__ == "__main__":
    app.secret_key = os.urandom(24)  # Sicherstellen, dass die Sitzung sicher ist
    app.run(host="0.0.0.0", port=8000, debug=True)
