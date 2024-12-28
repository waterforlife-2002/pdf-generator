from dotenv import load_dotenv
import os

# .env-Datei laden
load_dotenv()

# Teste, ob GOOGLE_SERVICE_ACCOUNT gelesen wird
service_account = os.getenv("GOOGLE_SERVICE_ACCOUNT")

if service_account:
    print("GOOGLE_SERVICE_ACCOUNT erfolgreich geladen!")
else:
    print("Fehler: GOOGLE_SERVICE_ACCOUNT konnte nicht geladen werden.")
