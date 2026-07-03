"""
Configuration initiale du bot YouTube Shorts.
Exécute ce script UNE SEULE FOIS sur ton PC pour authentifier YouTube.
"""
import os
import sys
import pickle
import subprocess
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
CLIENT_SECRETS_FILE = "client_secret.json"
TOKEN_FILE = "token.pickle"

def main():
    print("=" * 60)
    print("CONFIGURATION DU BOT YOUTUBE SHORTS")
    print("=" * 60)
    print()
    print("AVANT DE COMMENCER, assure-toi d'avoir:")
    print("  1. Un compte Google Cloud avec l'API YouTube activée")
    print("  2. Le fichier client_secret.json téléchargé")
    print("  3. Une clé API Gemini (https://aistudio.google.com/apikey)")
    print()

    if not os.path.exists(CLIENT_SECRETS_FILE):
        print(f"ERREUR: {CLIENT_SECRETS_FILE} introuvable!")
        print()
        print("Pour obtenir ce fichier:")
        print("  1. Va sur https://console.cloud.google.com/")
        print("  2. Crée un projet → APIs & Services")
        print("  3. Active YouTube Data API v3")
        print("  4. Crée un OAuth consent screen (External)")
        print("  5. Crée des identifiants OAuth 2.0 (Application de bureau)")
        print("  6. Télécharge le JSON et renomme-le en client_secret.json")
        print(f"  7. Place-le dans: {os.getcwd()}")
        sys.exit(1)

    print("1/3 - Authentification YouTube...")
    print("Un navigateur va s'ouvrir. Connecte-toi et autorise l'accès.")

    credentials = None
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "rb") as f:
            credentials = pickle.load(f)

    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRETS_FILE, SCOPES
            )
            credentials = flow.run_local_server(port=0)

        with open(TOKEN_FILE, "wb") as f:
            pickle.dump(credentials, f)

    print("✅ Authentification YouTube réussie!")
    print()

    gemini_key = input("2/3 - Entre ta clé API Gemini (ou laisse vide): ").strip()
    if gemini_key:
        print("✅ Clé Gemini enregistrée")

    print()
    print("3/3 - Configuration terminée!")
    print()
    print("Étapes suivantes:")
    print("  1. Crée un dépôt GitHub: https://github.com/new")
    print("  2. Ajoute ces secrets GitHub:")
    print("     - GEMINI_API_KEY: ta clé Gemini")
    print("     - YOUTUBE_TOKEN: le contenu de token.pickle (base64)")
    print("  3. Pousse le code sur GitHub")
    print("  4. Active GitHub Actions (le bot tournera automatiquement)")
    print()
    print("Pour encoder le token en base64 (Windows PowerShell):")
    print("  [Convert]::ToBase64String([IO.File]::ReadAllBytes('token.pickle'))")
    print()

if __name__ == "__main__":
    main()
