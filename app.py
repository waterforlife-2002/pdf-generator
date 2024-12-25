import os
import json
from flask import Flask, request, render_template, send_file, session, redirect, url_for
from PyPDF2 import PdfReader, PdfWriter
from fpdf import FPDF
from PIL import Image
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

app = Flask(__name__)
app.secret_key = "dein_sicherer_schlüssel"  # Geheimschlüssel für Sitzungen
app.config['UPLOAD_FOLDER'] = 'uploads'

# Passwort für die Google-Tabelle
PASSWORD = "Ahmadiyya"

# Sicherstellen, dass der Upload-Ordner existiert
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Google Sheets-Konfiguration
SPREADSHEET_ID = '1elVTaKWwoYO5yXnFkd-OTEjdukYqWQXpU5GO23lIurI'
RANGE_NAME = 'Tabellenblatt1!A1:Z1000'

# Funktion: Daten aus der Google-Tabelle abrufen
def get_google_sheet_data():
    try:
        # JSON-Inhalt aus der Umgebungsvariable laden
        SERVICE_ACCOUNT_JSON = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
        if not SERVICE_ACCOUNT_JSON:
            raise ValueError("GOOGLE_SERVICE_ACCOUNT_JSON Umgebungsvariable ist nicht gesetzt")

        creds = Credentials.from_service_account_info(
            json.loads(SERVICE_ACCOUNT_JSON),
            scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
        )
        service = build('sheets', 'v4', credentials=creds)
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
        return result.get('values', [])
    except Exception as e:
        print(f"Fehler beim Abrufen der Google-Tabelle: {e}")
        return [["Fehler beim Abrufen der Google-Tabelle: " + str(e)]]


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

        max_width = 80
        line_height = 10
        words = text.split()
        current_line = ""
        for word in words:
            if overlay.get_string_width(current_line + word + " ") > max_width:
                overlay.set_xy(x, y)
                overlay.cell(0, line_height, current_line, ln=True)
                y += line_height
                current_line = word + " "
            else:
                current_line += word + " "
        overlay.set_xy(x, y)
        overlay.cell(0, line_height, current_line, ln=True)

    overlay.output(overlay_pdf_path)

    overlay_reader = PdfReader(overlay_pdf_path)
    for i, page in enumerate(reader.pages):
        if i == page_number:
            page.merge_page(overlay_reader.pages[0])
        writer.add_page(page)

    with open(output_pdf, "wb") as f:
        writer.write(f)


# Funktion: Brunnen-Bild einfügen
def add_well_image(input_pdf, output_pdf, image_path, page_number):
    reader = PdfReader(input_pdf)
    writer = PdfWriter()

    page_width, page_height = 210, 297
    max_width, max_height = 160, 125

    overlay = FPDF()
    overlay.add_page()

    with Image.open(image_path) as img:
        image_width, image_height = img.size

    scale = min(max_width / image_width, max_height / image_height)
    scaled_width, scaled_height = image_width * scale, image_height * scale

    x = (page_width - scaled_width) / 2
    y = (page_height * (2 / 3)) - 85

    overlay.image(image_path, x=x, y=y, w=scaled_width, h=scaled_height)
    overlay_pdf_path = "well_image_overlay.pdf"
    overlay.output(overlay_pdf_path)

    overlay_reader = PdfReader(overlay_pdf_path)
    for i, page in enumerate(reader.pages):
        if i == page_number:
            page.merge_page(overlay_reader.pages[0])
        writer.add_page(page)

    with open(output_pdf, "wb") as f:
        writer.write(f)

# Funktion: Signboard-Bild und -Text einfügen
def add_signboard_content(input_pdf, output_pdf, image_path, text, image_x, image_y, image_w, image_h, text_x, text_y, text_w, page_number):
    reader = PdfReader(input_pdf)
    writer = PdfWriter()

    overlay_pdf_path = "signboard_content_overlay.pdf"
    overlay = FPDF()
    overlay.add_page()

    try:
        overlay.add_font("Impact", "", "fonts/impact.ttf", uni=True)
        overlay.set_font("Impact", size=21)
    except:
        overlay.set_font("Helvetica", style="B", size=21)

    overlay.set_text_color(50, 50, 50)

    if image_path and os.path.exists(image_path):
        overlay.image(image_path, x=image_x, y=image_y, w=image_w, h=image_h)

    if text:
        overlay.set_xy(text_x, text_y)
        overlay.multi_cell(text_w, 10, text)

    overlay.output(overlay_pdf_path)

    overlay_reader = PdfReader(overlay_pdf_path)
    for i, page in enumerate(reader.pages):
        if i == page_number:
            page.merge_page(overlay_reader.pages[0])
        writer.add_page(page)

    with open(output_pdf, "wb") as f:
        writer.write(f)

# Funktion: Zentrierte Bilder einfügen
def add_centered_images_with_scaling(input_pdf, output_pdf, image_paths, start_page, end_page):
    reader = PdfReader(input_pdf)
    writer = PdfWriter()

    page_width, page_height = 210, 297
    margin = 20
    max_width, max_height = page_width - 2 * margin, page_height - 2 * margin

    for i in range(start_page - 1):
        writer.add_page(reader.pages[i])

    for i, image_path in enumerate(image_paths):
        if i >= (end_page - start_page + 1):
            break

        overlay = FPDF()
        overlay.add_page()

        try:
            with Image.open(image_path) as img:
                img_width, img_height = img.size

            scale = min(max_width / img_width, max_height / img_height)
            scaled_width, scaled_height = img_width * scale, img_height * scale

            x = (page_width - scaled_width) / 2
            y = (page_height - scaled_height) / 2

            overlay.image(image_path, x=x, y=y, w=scaled_width, h=scaled_height)

            overlay_pdf_path = f"image_overlay_{i}.pdf"
            overlay.output(overlay_pdf_path)

            overlay_reader = PdfReader(overlay_pdf_path)
            writer.add_page(overlay_reader.pages[0])

        except Exception as e:
            print(f"Fehler beim Verarbeiten des Bildes {image_path}: {e}")

    if len(reader.pages) >= 18:
        writer.add_page(reader.pages[17])

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
        # Prüfen, ob das Passwort gesendet wurde
        entered_password = request.form.get("password")
        if entered_password:
            if entered_password == PASSWORD:
                session["google_data_authorized"] = True
                is_authenticated = True
            else:
                return render_template("index.html", templates=templates, error="Falsches Passwort!", is_authenticated=False)

        # Anderer POST-Logik
        selected_template = request.form.get("template")
        if selected_template:
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

            text_fields = [{"x": 15, "y": 40, "text": spendername}, {"x": 172, "y": 257, "text": brunnen_nr}]
            text_pdf = f"{selected_template}_text.pdf"
            add_text_overlay(input_pdf, text_pdf, text_fields, page_number=2)

            files = request.files.getlist("images")
            uploaded_images = [os.path.join(app.config['UPLOAD_FOLDER'], file.filename) for file in files if file.filename]
            for file, path in zip(files, uploaded_images):
                file.save(path)

            final_pdf = f"{brunnen_nr}.pdf"
            return send_file(final_pdf, as_attachment=True)

    # Abrufen der Google-Tabelle, falls authentifiziert
    data = []
    if is_authenticated:
        try:
            data = get_google_sheet_data()
        except Exception as e:
            data = [["Fehler beim Abrufen der Tabelle: " + str(e)]]

    return render_template("index.html", templates=templates, data=data, is_authenticated=is_authenticated)


@app.route("/google-data", methods=["GET", "POST"])
def google_data():
    if "google_data_authorized" not in session:
        if request.method == "POST":
            entered_password = request.form.get("password")
            if entered_password == PASSWORD:
                session["google_data_authorized"] = True
                return redirect(url_for("google_data"))
            else:
                return render_template("login.html", error="Falsches Passwort!")
        return render_template("login.html")

    # Abruf der Google-Tabelle
    try:
        data = get_google_sheet_data()
        if not data:  # Wenn keine Daten vorhanden sind
            data = [["Keine Daten verfügbar"]]  # Platzhalter-Tabelle
    except Exception as e:
        data = [["Fehler beim Abrufen der Tabelle: " + str(e)]]

    return render_template("google_table.html", data=data)

@app.route("/google-logout")
def google_logout():
    session.pop("google_data_authorized", None)
    return redirect(url_for("index"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=True)