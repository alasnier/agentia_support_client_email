import asyncio
from typing import List, Dict, Any

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from mcp.server.fastmcp import FastMCP, Context

# Initialiser le serveur MCP
mcp = FastMCP(name="GmailSupportAgent")


async def fetch_emails(ctx: Context = None, max_results: int = 10) -> List[Dict[str, Any]]:
    """
    Récupère les derniers emails de la boîte Gmail INBOX.
    Si ctx est fourni, utilise ctx.info() pour afficher les infos.
    """
    if ctx:
        await ctx.info("Fetching emails from Gmail …")
    else:
        print("Fetching emails from Gmail …")

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
            userId="me", id=m["id"]
        ).execute()

        headers = {h["name"]: h["value"] for h in msg_full["payload"]["headers"]}

        email_data = {
            "id": msg_full["id"],
            "from": headers.get("From", ""),
            "to": headers.get("To", ""),
            "subject": headers.get("Subject", ""),
            "date": headers.get("Date", ""),
            "snippet": msg_full.get("snippet", "")
        }
        emails.append(email_data)

    if ctx:
        await ctx.info(f"Fetched {len(emails)} emails.")
    else:
        print(f"Fetched {len(emails)} emails.")

    return emails


# Définition de l'outil MCP
@mcp.tool()
async def list_emails(ctx: Context, max_results: int = 10) -> List[Dict[str, Any]]:
    return await fetch_emails(ctx, max_results)


if __name__ == "__main__":
    # Si lancé directement, affiche les emails dans la console
    emails = asyncio.run(fetch_emails(max_results=10, ctx=None))
    for e in emails:
        print(f"{e['date']} - {e['from']} -> {e['subject']}")
