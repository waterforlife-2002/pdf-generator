import os
from flask import Flask, request, render_template, send_file, session
from PyPDF2 import PdfReader, PdfWriter
from fpdf import FPDF
from PIL import Image
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Flask App-Initialisierung
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
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

# Funktion zum Senden von E-Mails
def send_email_with_attachment(receiver_email, subject, body, attachment_path):
    sender_email = "waterforlife@humanityfirst.de"
    sender_password = "gaktys-devxoK-0guwha"  # Passwort des E-Mail-Kontos

    # E-Mail konfigurieren
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject

    # Nachrichtentext hinzufügen
    msg.attach(MIMEText(body, 'plain'))

    # PDF-Anhang hinzufügen
    with open(attachment_path, "rb") as attachment:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment.read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', f'attachment; filename={attachment_path}')
    msg.attach(part)

    # E-Mail senden
    try:
        with smtplib.SMTP('smtp.ionos.de', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
            print(f"E-Mail erfolgreich an {receiver_email} gesendet!")
    except Exception as e:
        print(f"Fehler beim Senden der E-Mail: {e}")

# Funktion zum Hochladen in Google-Drive Ordner
def upload_to_google_drive(file_path, folder_id):
    SCOPES = ['https://www.googleapis.com/auth/drive.file']
    import json
    service_account_info = json.loads(os.getenv("GOOGLE_SERVICE_ACCOUNT"))
    creds = Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
    service = build('drive', 'v3', credentials=creds)

    file_metadata = {
        'name': os.path.basename(file_path),
        'parents': [folder_id]
    }
    media = MediaFileUpload(file_path, mimetype='application/pdf')
    uploaded_file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id'
    ).execute()

    print(f"Datei hochgeladen: {uploaded_file.get('id')}")
    return uploaded_file.get('id')

@app.route("/", methods=["GET", "POST"])
def index():

    # Erfolgsmeldung initialisieren
    success_message = ""

    # Standard-Templates
    templates = ["Niger", "Benin", "Togo", "Cambodia", "Chad"]

    # POST-Anfrage für die Formularverarbeitung
    if request.method == "POST":
        # Template-Auswahl und Eingabedaten abrufen
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
        receiver_email = request.form.get("receiver_email")

        # Validierung der Eingaben
        if not brunnen_nr:
            return "Brunnen-Nr. fehlt", 400 
        
        if receiver_email and not is_valid_email(receiver_email):
            return "Ungültige E-Mail-Adresse", 400

        # Textfelder hinzufügen
        text_fields = [
            {"x": 15, "y": 40, "text": spendername},
            {"x": 172, "y": 257, "text": brunnen_nr}
        ]
        text_pdf = f"{selected_template}_text.pdf"
        add_text_overlay(input_pdf, text_pdf, text_fields, page_number=3)

        # Brunnen-Bild einfügen
        well_image_file = request.files.get("well_image")
        if well_image_file and well_image_file.filename:
            well_image_path = os.path.join(app.config['UPLOAD_FOLDER'], well_image_file.filename)
            well_image_file.save(well_image_path)
            add_well_image(text_pdf, text_pdf, well_image_path, page_number=3)

        # Signboard-Bild oder -Text einfügen
        signboard_file = request.files.get("signboard_image")
        signboard_text = request.form.get("signboard_text")

        if signboard_file and signboard_file.filename:
            signboard_image_path = os.path.join(app.config['UPLOAD_FOLDER'], signboard_file.filename)
            signboard_file.save(signboard_image_path)
            add_signboard_content(
                text_pdf, text_pdf, 
                signboard_image_path, None, 
                image_x=123, image_y=20, image_w=70, image_h=50, 
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

        # Zusätzliche Bilder hochladen und einfügen
        files = request.files.getlist("images")
        uploaded_images = [os.path.join(app.config['UPLOAD_FOLDER'], file.filename) for file in files if file.filename]
        for file, path in zip(files, uploaded_images):
            file.save(path)

        # Bilder in PDF einfügen
        start_page = 12 if selected_template != "Cambodia" else 13
        end_page = 17
        final_pdf = f"{brunnen_nr}.pdf"
        add_centered_images_with_scaling(text_pdf, final_pdf, uploaded_images, start_page=start_page, end_page=end_page)

        # Speichern des finalen PDFs im UPLOAD_FOLDER
        final_pdf = os.path.join(app.config['UPLOAD_FOLDER'], f"{brunnen_nr}.pdf")
        add_centered_images_with_scaling(text_pdf, final_pdf, uploaded_images, start_page=start_page, end_page=end_page)

        # ID des freigegebenen Google Drive-Ordners
        folder_id = "14IGXwu5OaCHM6qL4Frwe32OYcwRl70Av"

        # Datei in Google Drive hochladen
        try:
            uploaded_file_id = upload_to_google_drive(final_pdf, folder_id)
            drive_link = f"https://drive.google.com/file/d/{uploaded_file_id}/view"
            print(f"Bericht erfolgreich in Google Drive hochgeladen: {drive_link}")
        except Exception as e:
            print(f"Fehler beim Hochladen in Google Drive: {e}")
            drive_link = None

        # Rückmeldung für den Benutzer
        if drive_link:
            success_message += f" Sie können den Bericht auch hier ansehen: {drive_link}"

        # E-Mail senden
        if receiver_email:
            subject = f"Ihr Brunnen {brunnen_nr}"
            body = f"""Assalamo-Aleikum warahmatullah-e-wabarakatehu!

Sehr geehrter Spender,
wir freuen uns, Ihnen mitteilen zu können, dass Ihr Projekt einen großen positiven Einfluss auf die ansässige Gemeinschaft im {selected_template} hat.

Wir möchten Ihnen unsere aufrichtige Dankbarkeit für Ihre großzügige Spende an Humanity First zum Ausdruck bringen, die dazu beigetragen hat, den Bedarf an sauberem Wasser in {selected_template} zu decken.

Als Zeichen unserer Wertschätzung freuen wir uns, Ihnen einen umfassenden Bericht über unsere Organisation, unsere Aktivitäten und das Zielgebiet {selected_template} zu präsentieren, in dem Ihre Spende einen bedeutenden Einfluss auf das Leben derjenigen hatte, die am stärksten gefährdet sind.

Wir hoffen, dass diese Informationen Ihnen einen umfassenden Einblick in die Bedeutung und den Einfluss Ihres gespendeten Wasserbrunnens geben.

Nochmals Alhamdulillah, Jazzakumullah für Ihre Großzügigkeit und Ihr Mitgefühl. Sie haben das Leben vieler Menschen zum Besseren verändert.

Mit freundlichen Grüßen

Ummad Ahmad
Water for Life
Humanity First Deutschland
            """
            send_email_with_attachment(receiver_email, subject, body, final_pdf)
            success_message = "Der Bericht wurde erfolgreich generiert und per E-Mail versandt!"
        else:
            success_message = "Der Bericht wurde erfolgreich generiert!"

        # Rückgabe des Erfolgsstatus und Download-Links als JSON
        if receiver_email:
            success_message = "E-Mail wurde erfolgreich versandt! Der Bericht steht auch zum Download bereit."
        else:
            success_message = "Der Bericht steht nun zum Download bereit. Bitte laden Sie den Bericht im Google-Drive Ordner und Asana hoch."

        return {
            "status": "success",
            "message": success_message,
            "download_url": f"/download/{os.path.basename(final_pdf)}",
            "drive_url": drive_link if drive_link else None
}



    print("Anfrage-Methode:", request.method)  # Debugging
    if request.method == "POST":
        print("POST-Daten:", request.form)  # Debugging
        print("Dateien:", request.files)  # Debugging
    return render_template("index.html", templates=["Niger", "Benin", "Togo", "Cambodia", "Chad"])

@app.route("/download/<filename>")
def download(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        return "Datei nicht gefunden", 404


# Helferfunktion zur Validierung von E-Mail-Adressen
def is_valid_email(email):
    import re
    regex = r'^\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    return re.match(regex, email)

if __name__ == "__main__":
    app.secret_key = os.urandom(24)  # Sicherstellen, dass die Sitzung sicher ist
    app.run(host="0.0.0.0", port=8000, debug=True)
