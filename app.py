import os
from flask import Flask, request, render_template, send_file, jsonify, redirect, url_for, session
from PyPDF2 import PdfReader, PdfWriter
from fpdf import FPDF
from PIL import Image
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

app = Flask(__name__)
app.secret_key = "geheim"  # Für Sitzungen notwendig
app.config['UPLOAD_FOLDER'] = 'uploads'

# Sicherstellen, dass der Upload-Ordner existiert
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Google Sheets-Konfiguration
SPREADSHEET_ID = '1elVTaKWwoYO5yXnFkd-OTEjdukYqWQXpU5GO23lIurI'
RANGE_NAME = 'Tabellenblatt1!A1:Z1000'
SERVICE_ACCOUNT_FILE = 'config/google_service_account.json'

# Passwort für die Anmeldung
ADMIN_PASSWORD = "Ahmadiyya"

# Funktion: Daten aus der Google-Tabelle abrufen
def get_google_sheet_data():
    try:
        creds = Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE,
            scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
        )
        service = build('sheets', 'v4', credentials=creds)
        sheet = service.spreadsheets()

        print(f"Tabellenblattname: Tabellenblatt1, Bereich: Tabellenblatt1!A1:Z1000")
        
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range='Tabellenblatt1!A1:Z1000').execute()
        return result.get('values', [])
    except Exception as e:
        print(f"Fehler beim Abrufen der Google-Tabelle: {e}")
        return []
    
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
        if i == page_number - 1:  # Index-basiert (Seite 3 ist Index 2)
            page.merge_page(overlay_reader.pages[0])
        writer.add_page(page)

    with open(output_pdf, "wb") as f:
        writer.write(f)

# Funktion: Brunnen-Bild einfügen
def add_well_image(input_pdf, output_pdf, image_path, page_number):
    reader = PdfReader(input_pdf)
    writer = PdfWriter()

    page_width, page_height = 210, 297
    overlay = FPDF()
    overlay.add_page()

    with Image.open(image_path) as img:
        img_width, img_height = img.size
    scale = min(160 / img_width, 125 / img_height)
    x = (page_width - img_width * scale) / 2
    y = (page_height * (2 / 3)) - 85

    overlay.image(image_path, x=x, y=y, w=img_width * scale, h=img_height * scale)
    overlay_pdf_path = "well_image_overlay.pdf"
    overlay.output(overlay_pdf_path)

    overlay_reader = PdfReader(overlay_pdf_path)
    for i, page in enumerate(reader.pages):
        if i == page_number - 1:  # Seite 3 ist Index 2
            page.merge_page(overlay_reader.pages[0])
        writer.add_page(page)

    with open(output_pdf, "wb") as f:
        writer.write(f)

# Funktion: Signboard-Text oder -Bild einfügen
def add_signboard_content(input_pdf, output_pdf, image_path, text, page_number):
    reader = PdfReader(input_pdf)
    writer = PdfWriter()

    overlay_pdf_path = "signboard_overlay.pdf"
    overlay = FPDF()
    overlay.add_page()

    if image_path and os.path.exists(image_path):
        # Bild einfügen (rechts oben)
        overlay.image(image_path, x=121, y=29, w=70, h=40)
    elif text:  # Text einfügen, wenn kein Bild vorhanden ist
        try:
            overlay.add_font("Impact", "", "fonts/impact.ttf", uni=True)
            overlay.set_font("Impact", size=21)
        except:
            overlay.set_font("Helvetica", style="B", size=21)

        overlay.set_text_color(50, 50, 50)
        overlay.set_xy(121, 40)  # X wie beim Bild, Y wie beim Spendername
        overlay.multi_cell(70, 10, text)

    overlay.output(overlay_pdf_path)

    # Überlagern des PDFs mit dem Overlay
    overlay_reader = PdfReader(overlay_pdf_path)
    for i, page in enumerate(reader.pages):
        if i == page_number - 1:  # Seite 3 ist Index 2
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
    if request.method == "POST":
        if not session.get("logged_in"):  # Passwortprüfung
            password = request.form.get("password")
            if password == ADMIN_PASSWORD:
                session["logged_in"] = True
                return redirect(url_for("index"))
            else:
                return render_template("index.html", error="Falsches Passwort", is_authenticated=False)

        # Verarbeitung des Formulars für Vorlagen und Bilder
        template_files = {
            "Niger": "Niger.pdf",
            "Benin": "Benin.pdf",
            "Togo": "Togo.pdf",
            "Cambodia": "Cambodia.pdf",
            "Chad": "Chad.pdf"
        }
        selected_template = request.form.get("template")
        if selected_template not in template_files:
            return "Vorlage nicht gefunden", 400

        input_pdf = template_files[selected_template]
        spendername = request.form.get("spendername")
        brunnen_nr = request.form.get("brunnen_nr")
        signboard_text = request.form.get("signboard_text", "")
        if not brunnen_nr:
            return "Brunnen-Nr. fehlt", 400

        text_pdf = f"{selected_template}_text.pdf"
        text_fields = [{"x": 15, "y": 40, "text": spendername}, {"x": 172, "y": 257, "text": brunnen_nr}]
        add_text_overlay(input_pdf, text_pdf, text_fields, page_number=3)

        well_image = request.files["well_image"]
        well_image_path = os.path.join(app.config["UPLOAD_FOLDER"], well_image.filename)
        well_image.save(well_image_path)
        add_well_image(text_pdf, text_pdf, well_image_path, page_number=3)

        signboard_image = request.files["signboard_image"]
        if signboard_image and signboard_image.filename:
            signboard_path = os.path.join(app.config["UPLOAD_FOLDER"], signboard_image.filename)
            signboard_image.save(signboard_path)
            add_signboard_content(text_pdf, text_pdf, signboard_path, "", page_number=3)
        else:
            add_signboard_content(text_pdf, text_pdf, None, signboard_text, page_number=3)

        files = request.files.getlist("images")
        uploaded_images = [os.path.join(app.config['UPLOAD_FOLDER'], file.filename) for file in files if file.filename]
        for file, path in zip(files, uploaded_images):
            file.save(path)

        final_pdf = f"{brunnen_nr}.pdf"
        if selected_template == "Cambodia":
            add_centered_images_with_scaling(text_pdf, final_pdf, uploaded_images, start_page=13, end_page=17)
        else:
            add_centered_images_with_scaling(text_pdf, final_pdf, uploaded_images, start_page=12, end_page=17)

        return send_file(final_pdf, as_attachment=True)

    # Startseite rendern
    templates = ["Niger", "Benin", "Togo", "Cambodia", "Chad"]
    data = get_google_sheet_data()
    is_authenticated = session.get("logged_in", False)
    return render_template("index.html", templates=templates, data=data, is_authenticated=is_authenticated)

@app.route("/logout", methods=["GET"])
def logout():
    session.clear()
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)