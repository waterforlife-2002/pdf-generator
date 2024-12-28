from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

def upload_to_google_drive(file_path, folder_id):
    SCOPES = ['https://www.googleapis.com/auth/drive.file']
    creds = Credentials.from_service_account_file('service_account.json', scopes=SCOPES)
    service = build('drive', 'v3', credentials=creds)

    file_metadata = {
        'name': 'test.pdf',  # Testdatei
        'parents': [folder_id]
    }
    media = MediaFileUpload(file_path, mimetype='application/pdf')
    try:
        uploaded_file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        print(f"Erfolgreich hochgeladen. Datei-ID: {uploaded_file.get('id')}")
    except Exception as e:
        print(f"Fehler beim Hochladen: {e}")

if __name__ == "__main__":
    folder_id = "14IGXwu5OaCHM6qL4Frwe32OYcwRl70Av"  # Zielordner-ID
    file_path = "test.pdf"  # Beispiel: Testdatei
    upload_to_google_drive(file_path, folder_id)
