from dotenv import load_dotenv
import os
import json

# Lade die .env-Datei
load_dotenv()

# GOOGLE_SERVICE_ACCOUNT laden
service_account_json = os.getenv("GOOGLE_SERVICE_ACCOUNT")

if not service_account_json:
    raise EnvironmentError("GOOGLE_SERVICE_ACCOUNT ist nicht gesetzt.")

# Debug-Ausgabe: Zeige die Rohdaten der Umgebungsvariablen
print("Rohdaten der Umgebungsvariablen (repr):")
print(repr(service_account_json))  # Zeigt alle Escape-Sequenzen

# Ersetze Escape-Sequenzen
service_account_json = service_account_json.replace("\\n", "\n")

# Debug-Ausgabe: Zeige den Wert nach der Umwandlung
print("Nach Ersetzung von \\n:")
print(service_account_json)

try:
    # JSON parsen
    service_account_info = json.loads(service_account_json)
    print("Service Account erfolgreich geladen.")
except json.JSONDecodeError as e:
    print(f"JSONDecodeError: {e}")
    raise
