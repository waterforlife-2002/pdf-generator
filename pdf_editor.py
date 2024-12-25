from PyPDF2 import PdfReader, PdfWriter
from fpdf import FPDF
from PIL import Image  # Hier wird Image importiert


# Funktion: Texthalter einfügen
def add_text_overlay(input_pdf, output_pdf, text_fields, page_number):
    reader = PdfReader(input_pdf)
    writer = PdfWriter()

    # Overlay erstellen
    overlay_pdf_path = "text_overlay.pdf"
    overlay = FPDF()
    overlay.add_page()
    overlay.set_font("Helvetica", style="B", size=20)
    overlay.set_text_color(0, 0, 0)

    for field in text_fields:
        overlay.set_xy(field["x"], field["y"])
        overlay.cell(0, 10, field["text"], ln=True)

    overlay.output(overlay_pdf_path)

    # Seiten kombinieren
    overlay_reader = PdfReader(overlay_pdf_path)
    for i, page in enumerate(reader.pages):
        if i == page_number:
            page.merge_page(overlay_reader.pages[0])
        writer.add_page(page)

    with open(output_pdf, "wb") as f:
        writer.write(f)


# Funktion: Bilder einfügen und leere Seiten entfernen
def add_images(input_pdf, output_pdf, image_paths, start_page):
    """
    Fügt Bilder ab der gewünschten Seite ein. Entfernt leere Seiten, falls keine Bilder vorhanden sind.
    """
    reader = PdfReader(input_pdf)
    writer = PdfWriter()

    # DIN A4 Maße und Ränder
    page_width, page_height = 210, 297
    margin = 20
    max_width, max_height = page_width - 2 * margin, page_height - 2 * margin

    # Kopiere alle Seiten vor der start_page
    for i in range(start_page - 1):  # Seitenindex: 0-basiert
        writer.add_page(reader.pages[i])

    # Bilder einfügen
    for i, image_path in enumerate(image_paths):
        overlay = FPDF()
        overlay.add_page()

        try:
            # Bild öffnen und skalieren
            with Image.open(image_path) as img:
                img_width, img_height = img.size

            scale = min(max_width / img_width, max_height / img_height)
            scaled_width, scaled_height = img_width * scale, img_height * scale

            x = (page_width - scaled_width) / 2
            y = (page_height - scaled_height) / 2

            overlay.image(image_path, x=x, y=y, w=scaled_width, h=scaled_height)

            # Overlay speichern
            overlay_pdf_path = f"image_overlay_{i}.pdf"
            overlay.output(overlay_pdf_path)

            # Seite kombinieren
            overlay_reader = PdfReader(overlay_pdf_path)
            writer.add_page(overlay_reader.pages[0])

        except Exception as e:
            print(f"Fehler beim Verarbeiten des Bildes {image_path}: {e}")

    # Restliche Seiten nach den Bildern kopieren (falls nötig)
    for i in range(start_page + len(image_paths), len(reader.pages)):
        writer.add_page(reader.pages[i])

    # Ergebnis speichern
    with open(output_pdf, "wb") as f:
        writer.write(f)


# Texthalter-Daten
text_fields = [
    {"x": 15, "y": 45, "text": "{{Spendername}}"},   # Spendername
    {"x": 155, "y": 255, "text": "{{Brunnen-Nr.}}"}  # Brunnen-Nr.
]

# Bildpfade
image_paths = [
    "image1.jpg",  # Seite 12
    "image2.jpg",  # Seite 13
    "image3.jpg",  # Seite 14
    "image4.jpg",  # Seite 15
    "image5.jpg",  # Seite 16
    "image6.jpg"   # Seite 17
]

# Schritt 1: Texthalter einfügen
add_text_overlay("Niger.pdf", "Niger_text.pdf", text_fields, page_number=2)

# Schritt 2: Bilder auf den Platzhaltern einfügen
add_images("Niger_text.pdf", "Niger_final.pdf", image_paths, start_page=12)
