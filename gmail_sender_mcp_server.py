import base64
import json
import sys
from email.mime.text import MIMEText
from typing import Optional

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(name="GmailSender")


def _build_mime_message(
    to: str,
    subject: str,
    body: str,
    thread_id: Optional[str] = None,
    message_id: Optional[str] = None,
) -> MIMEText:
    """
    Construit un message MIME pour Gmail.

    Args:
        to: Destinataire
        subject: Sujet
        body: Corps du message
        thread_id: ID du thread (pour réponses)
        message_id: ID du message original (pour réponses)

    Returns:
        MIMEText message configuré
    """
    message = MIMEText(body, "plain", "utf-8")
    message["To"] = to

    # Si c'est une réponse, modifier le subject et ajouter les headers
    if message_id:
        if not subject.startswith("Re: "):
            message["Subject"] = f"Re: {subject}"
        else:
            message["Subject"] = subject
        message["In-Reply-To"] = message_id
        message["References"] = message_id
    else:
        message["Subject"] = subject

    return message


@mcp.tool()
async def create_draft(
    to: str, subject: str, body: str, thread_id: str = None, message_id: str = None
) -> str:
    """
    Crée un brouillon dans Gmail (ne l'envoie pas).

    Args:
        to: Destinataire
        subject: Sujet (utilisé si ce n'est pas une réponse)
        body: Corps de l'email
        thread_id: ID du thread pour répondre dans la conversation
        message_id: ID du message original pour répondre

    Returns:
        JSON string avec le statut de la création du brouillon
    """
    try:
        creds = Credentials.from_authorized_user_file("token.json")
        service = build("gmail", "v1", credentials=creds)

        # Créer le message MIME
        message = _build_mime_message(to, subject, body, thread_id, message_id)

        # Encoder le message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")

        # Construire le corps de la requête pour le brouillon
        draft_body = {"message": {"raw": raw_message}}

        # Ajouter le threadId si c'est une réponse
        if thread_id:
            draft_body["message"]["threadId"] = thread_id

        # Créer le brouillon
        draft = service.users().drafts().create(userId="me", body=draft_body).execute()

        result = {
            "success": True,
            "mode": "draft",
            "draft_id": draft["id"],
            "message_id": draft["message"]["id"],
            "thread_id": draft["message"].get("threadId", ""),
            "to": to,
            "subject": message["Subject"],
        }

        sys.stderr.write(f"✅ Draft created successfully: {draft['id']}\n")
        sys.stderr.flush()

    except Exception as e:
        result = {"success": False, "mode": "draft", "error": str(e), "to": to}
        sys.stderr.write(f"❌ Error creating draft: {e}\n")
        sys.stderr.flush()

    return json.dumps(result)


@mcp.tool()
async def send_email(
    to: str, subject: str, body: str, thread_id: str = None, message_id: str = None
) -> str:
    """
    Envoie un email via Gmail API (envoi direct, pas de brouillon).

    Args:
        to: Destinataire
        subject: Sujet (utilisé si ce n'est pas une réponse)
        body: Corps de l'email
        thread_id: ID du thread pour répondre dans la conversation
        message_id: ID du message original pour répondre

    Returns:
        JSON string avec le statut de l'envoi
    """
    try:
        creds = Credentials.from_authorized_user_file("token.json")
        service = build("gmail", "v1", credentials=creds)

        # Créer le message MIME
        message = _build_mime_message(to, subject, body, thread_id, message_id)

        # Encoder le message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")

        body_payload = {"raw": raw_message}

        # Ajouter le threadId si c'est une réponse
        if thread_id:
            body_payload["threadId"] = thread_id

        # Envoyer l'email
        sent_message = (
            service.users().messages().send(userId="me", body=body_payload).execute()
        )

        result = {
            "success": True,
            "mode": "sent",
            "message_id": sent_message["id"],
            "thread_id": sent_message.get("threadId", ""),
            "to": to,
            "subject": message["Subject"],
        }

        sys.stderr.write(f"✅ Email sent successfully: {sent_message['id']}\n")
        sys.stderr.flush()

    except Exception as e:
        result = {"success": False, "mode": "sent", "error": str(e), "to": to}
        sys.stderr.write(f"❌ Error sending email: {e}\n")
        sys.stderr.flush()

    return json.dumps(result)


@mcp.tool()
async def send_draft(draft_id: str) -> str:
    """
    Envoie un brouillon existant.

    Args:
        draft_id: ID du brouillon à envoyer

    Returns:
        JSON string avec le statut de l'envoi
    """
    try:
        creds = Credentials.from_authorized_user_file("token.json")
        service = build("gmail", "v1", credentials=creds)

        # Envoyer le brouillon
        sent_message = (
            service.users().drafts().send(userId="me", body={"id": draft_id}).execute()
        )

        result = {
            "success": True,
            "mode": "draft_sent",
            "message_id": sent_message["id"],
            "thread_id": sent_message.get("threadId", ""),
            "draft_id": draft_id,
        }

        sys.stderr.write(f"✅ Draft sent successfully: {draft_id}\n")
        sys.stderr.flush()

    except Exception as e:
        result = {
            "success": False,
            "mode": "draft_sent",
            "error": str(e),
            "draft_id": draft_id,
        }
        sys.stderr.write(f"❌ Error sending draft: {e}\n")
        sys.stderr.flush()

    return json.dumps(result)


if __name__ == "__main__":
    mcp.run()
