import json
import sys
from typing import List, Dict, Any

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from mcp.server.fastmcp import FastMCP

# Initialiser le serveur MCP
mcp = FastMCP(name="GmailSupportAgent")


@mcp.tool()
async def list_emails(max_results: int = 10) -> str:
    """
    Récupère les derniers emails de la boîte Gmail INBOX.
    Retourne un JSON string avec la liste des emails.
    """
    try:
        creds = Credentials.from_authorized_user_file("token.json")
        service = build("gmail", "v1", credentials=creds)

        results = service.users().messages().list(
            userId="me",
            labelIds=["INBOX"],
            maxResults=max_results
        ).execute()

        messages = results.get("messages", [])
        emails: List[Dict[str, Any]] = []

        for m in messages:
            msg_full = service.users().messages().get(
                userId="me", id=m["id"], format="full"
            ).execute()

            headers = {h["name"]: h["value"] for h in msg_full["payload"]["headers"]}

            # Extraire le body text
            body_text = ""
            body_html = ""

            if "parts" in msg_full["payload"]:
                for part in msg_full["payload"]["parts"]:
                    if part["mimeType"] == "text/plain" and "data" in part["body"]:
                        import base64
                        body_text = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors='ignore')
                        break
                    elif part["mimeType"] == "text/html" and "data" in part["body"]:
                        import base64
                        body_html = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors='ignore')
            elif "body" in msg_full["payload"] and "data" in msg_full["payload"]["body"]:
                import base64
                body_text = base64.urlsafe_b64decode(msg_full["payload"]["body"]["data"]).decode("utf-8",
                                                                                                 errors='ignore')

            email_data = {
                "id": msg_full["id"],
                "threadId": msg_full.get("threadId", ""),
                "from": headers.get("From", ""),
                "to": headers.get("To", ""),
                "subject": headers.get("Subject", ""),
                "date": headers.get("Date", ""),
                "snippet": msg_full.get("snippet", ""),
                "bodyText": body_text or msg_full.get("snippet", ""),
                "bodyHtml": body_html
            }
            emails.append(email_data)

        # Retourner comme JSON string
        return json.dumps(emails)

    except Exception as e:
        sys.stderr.write(f"Error in list_emails: {e}\n")
        sys.stderr.flush()
        # Retourner un JSON d'erreur
        return json.dumps({"error": str(e), "emails": []})


# Point d'entrée pour lancer le serveur
if __name__ == "__main__":
    mcp.run()
