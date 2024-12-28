from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import json

def test_google_drive_upload():
    SCOPES = ['https://www.googleapis.com/auth/drive.file']
    
    # Lade die JSON-Datei
    with open("service_account.json", "r") as f:
        service_account_info = json.load(f)
    
    creds = Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
    service = build('drive', 'v3', credentials=creds)

    file_metadata = {
        'name': 'test_upload.pdf',
        'parents': ['14IGXwu5OaCHM6qL4Frwe32OYcwRl70Av']  # Deine Ordner-ID
    }
    media = MediaFileUpload('test_upload.pdf', mimetype='application/pdf')
    
    try:
        uploaded_file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        print(f"Datei erfolgreich hochgeladen: {uploaded_file.get('id')}")
    except Exception as e:
        print(f"Fehler beim Test-Upload: {e}")

test_google_drive_upload()
