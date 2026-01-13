import base64
import json
from email.mime.text import MIMEText

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(name="GmailSender")


@mcp.tool()
async def send_email(
        to: str,
        subject: str,
        body: str,
        thread_id: str = None,
        message_id: str = None
) -> str:
    """
    Envoie un email via Gmail API.

    Args:
        to: Destinataire
        subject: Sujet (utilisé si ce n'est pas une réponse)
        body: Corps de l'email
        thread_id: ID du thread pour répondre dans la conversation
        message_id: ID du message original pour répondre

    Returns:
        JSON string avec le statut de l'envoi
    """
    creds = Credentials.from_authorized_user_file("token.json")
    service = build("gmail", "v1", credentials=creds)

    # Créer le message MIME
    message = MIMEText(body, 'plain', 'utf-8')
    message['To'] = to

    # Si c'est une réponse, modifier le subject et ajouter les headers
    if message_id:
        if not subject.startswith('Re: '):
            message['Subject'] = f"Re: {subject}"
        else:
            message['Subject'] = subject
        message['In-Reply-To'] = message_id
        message['References'] = message_id
    else:
        message['Subject'] = subject

    # Encoder le message
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')

    body_payload = {'raw': raw_message}

    # Ajouter le threadId si c'est une réponse
    if thread_id:
        body_payload['threadId'] = thread_id

    try:
        sent_message = service.users().messages().send(
            userId='me',
            body=body_payload
        ).execute()

        result = {
            "success": True,
            "message_id": sent_message['id'],
            "thread_id": sent_message.get('threadId', ''),
            "to": to,
            "subject": message['Subject']
        }
    except Exception as e:
        result = {
            "success": False,
            "error": str(e),
            "to": to
        }

    return json.dumps(result)


if __name__ == "__main__":
    mcp.run()
