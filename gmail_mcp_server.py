import json
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
        if "parts" in msg_full["payload"]:
            for part in msg_full["payload"]["parts"]:
                if part["mimeType"] == "text/plain" and "data" in part["body"]:
                    import base64
                    body_text = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8")
                    break
        elif "body" in msg_full["payload"] and "data" in msg_full["payload"]["body"]:
            import base64
            body_text = base64.urlsafe_b64decode(msg_full["payload"]["body"]["data"]).decode("utf-8")

        email_data = {
            "id": msg_full["id"],
            "threadId": msg_full.get("threadId", ""),
            "from": headers.get("From", ""),
            "to": headers.get("To", ""),
            "subject": headers.get("Subject", ""),
            "date": headers.get("Date", ""),
            "snippet": msg_full.get("snippet", ""),
            "bodyText": body_text or msg_full.get("snippet", "")
        }
        emails.append(email_data)

    # Retourner comme JSON string
    return json.dumps(emails)


# Point d'entrée pour lancer le serveur
if __name__ == "__main__":
    mcp.run()
