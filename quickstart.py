import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Si vous modifiez ces scopes, supprimez token.json
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.modify'
]


def main():
    """Authentifie l'utilisateur et génère token.json"""
    creds = None

    # Le fichier token.json stocke les tokens d'accès et de rafraîchissement
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    # Si pas de credentials valides, demander à l'utilisateur de se connecter
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                print("✅ Token refreshed successfully!")
            except Exception as e:
                print(f"❌ Failed to refresh token: {e}")
                print("🔄 Starting new authentication flow...")
                creds = None

        if not creds:
            if not os.path.exists('credentials.json'):
                print("❌ Error: credentials.json not found!")
                print("📥 Please download it from Google Cloud Console:")
                print("   1. Go to https://console.cloud.google.com/")
                print("   2. Select your project: agentia-support-client-email")
                print("   3. Go to APIs & Services > Credentials")
                print("   4. Download your OAuth 2.0 Client ID as 'credentials.json'")
                return

            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
            print("✅ Authentication successful!")

        # Sauvegarder les credentials pour la prochaine fois
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
        print("✅ Token saved to token.json")

    # Tester la connexion
    try:
        service = build('gmail', 'v1', credentials=creds)
        results = service.users().labels().list(userId='me').execute()
        labels = results.get('labels', [])

        print("\n✅ Gmail API connection successful!")
        print(f"📧 Found {len(labels)} labels in your Gmail account")
        print("\n🎉 You're all set! You can now run:")
        print("   python mcp_agent_orchestrator.py --max-emails 5")

    except Exception as e:
        print(f"❌ Error testing Gmail connection: {e}")


if __name__ == '__main__':
    main()