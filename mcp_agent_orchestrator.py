import asyncio
import json
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class GmailSupportAgent:
    """Agent de support client Gmail avec MCP."""

    def __init__(
        self,
        min_confidence: float = 0.5,
        enable_security: bool = True,
        draft_mode: bool = True,
    ):
        self.min_confidence = min_confidence
        self.enable_security = enable_security
        self.draft_mode = draft_mode  # NOUVEAU : Mode brouillon par défaut
        self.results = []

    async def process_emails(
        self, max_emails: int = 10, auto_reply: bool = False, dry_run: bool = True
    ):
        """
        Pipeline complet de traitement des emails.

        Args:
            max_emails: Nombre maximum d'emails à traiter
            auto_reply: Activer les réponses automatiques
            dry_run: Mode simulation (ne pas envoyer vraiment les emails)
        """
        print("=" * 70)
        print("🚀 Gmail Support Agent - MCP Pipeline")
        print("=" * 70)
        print(
            f"📊 Config: max_emails={max_emails}, auto_reply={auto_reply}, dry_run={dry_run}"
        )
        print(f"🎯 Min confidence: {self.min_confidence:.0%}")
        print(f"🔒 Security: {'ENABLED' if self.enable_security else 'DISABLED'}")
        print(f"📝 Mode: {'DRAFT' if self.draft_mode else 'DIRECT SEND'}")  # NOUVEAU
        print("=" * 70)

        # Paramètres des serveurs MCP
        gmail_params = StdioServerParameters(
            command="python", args=["gmail_mcp_server.py"], env=None
        )
        classifier_params = StdioServerParameters(
            command="python", args=["classification_mcp_server.py"], env=None
        )
        response_gen_params = StdioServerParameters(
            command="python", args=["response_generator_mcp_server.py"], env=None
        )
        sender_params = StdioServerParameters(
            command="python", args=["gmail_sender_mcp_server.py"], env=None
        )
        security_params = StdioServerParameters(
            command="python", args=["security_mcp_server.py"], env=None
        )

        # Connexion aux serveurs MCP
        async with stdio_client(gmail_params) as (gr, gw):
            async with ClientSession(gr, gw) as gmail_session:
                async with stdio_client(classifier_params) as (cr, cw):
                    async with ClientSession(cr, cw) as class_session:
                        async with stdio_client(response_gen_params) as (rr, rw):
                            async with ClientSession(rr, rw) as response_session:
                                async with stdio_client(sender_params) as (sr, sw):
                                    async with ClientSession(sr, sw) as sender_session:
                                        async with stdio_client(security_params) as (
                                            secr,
                                            secw,
                                        ):
                                            async with ClientSession(
                                                secr, secw
                                            ) as security_session:
                                                # Initialiser les sessions
                                                await gmail_session.initialize()
                                                await class_session.initialize()
                                                await response_session.initialize()
                                                await sender_session.initialize()

                                                if self.enable_security:
                                                    await security_session.initialize()
                                                    print(
                                                        "\n✅ All MCP servers connected (including security)!\n"
                                                    )
                                                else:
                                                    print(
                                                        "\n✅ All MCP servers connected!\n"
                                                    )

                                                # Traiter les emails
                                                await self._process_pipeline(
                                                    gmail_session,
                                                    class_session,
                                                    response_session,
                                                    sender_session,
                                                    security_session
                                                    if self.enable_security
                                                    else None,
                                                    max_emails,
                                                    auto_reply,
                                                    dry_run,
                                                )

    async def _process_pipeline(
        self,
        gmail_session,
        class_session,
        response_session,
        sender_session,
        security_session,
        max_emails,
        auto_reply,
        dry_run,
    ):
        """Pipeline de traitement."""

        # 1. Récupérer les emails
        print("📥 Fetching emails from Gmail...")
        emails_result = await gmail_session.call_tool(
            "list_emails", arguments={"max_results": max_emails}
        )

        try:
            emails_json = emails_result.content[0].text
            emails_data = json.loads(emails_json)

            # Vérifier si c'est une erreur
            if isinstance(emails_data, dict) and "error" in emails_data:
                print(f"❌ Gmail error: {emails_data['error']}")
                return

        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse Gmail response: {e}")
            print(f"Response was: {emails_result.content[0].text[:500]}")
            return

        print(f"✅ Found {len(emails_data)} emails\n")

        # Compteurs de sécurité
        blocked_count = 0
        warning_count = 0
        safe_count = 0
        draft_created_count = 0
        sent_count = 0

        # 2. Traiter chaque email
        for i, email in enumerate(emails_data, 1):
            print("-" * 70)
            print(f"\n📧 Email {i}/{len(emails_data)}")
            print(f"   From: {email.get('from', 'Unknown')}")
            print(f"   Subject: {email.get('subject', '(no subject)')}")

            text = email.get("bodyText", "") or email.get("snippet", "")

            security_data = None

            # === SCAN DE SÉCURITÉ ===
            if self.enable_security and security_session:
                print("   🔒 Security scan...")
                try:
                    security_result = await security_session.call_tool(
                        "scan_email_security",
                        arguments={
                            "sender": email.get("from", ""),
                            "body_text": text,
                            "body_html": email.get("bodyHtml", ""),
                            "metadata": {
                                "id": email.get("id"),
                                "subject": email.get("subject"),
                                "date": email.get("date"),
                            },
                        },
                    )
                    security_data = json.loads(security_result.content[0].text)

                    security_level = security_data["security_level"]
                    security_score = security_data["security_score"]

                    # Affichage du niveau de sécurité
                    if security_level == "DANGER":
                        print(f"   ⛔ DANGER - Security Score: {security_score}/100")
                        blocked_count += 1

                        # Afficher les problèmes détectés
                        for issue in security_data.get("issues", [])[:3]:
                            print(f"      🚨 {issue['type']}: {issue['message']}")

                        print("   🚫 Blocking this email from processing")

                        # Ne pas traiter les emails dangereux
                        self.results.append(
                            {
                                "email": email,
                                "classification": {
                                    "category": "BLOCKED",
                                    "confidence": 0,
                                },
                                "response": {
                                    "action": "Email blocked for security",
                                    "priority": "blocked",
                                    "should_send_auto": False,
                                    "response_body": None,
                                },
                                "security": security_data,
                            }
                        )
                        continue  # Passer à l'email suivant

                    elif security_level == "WARNING":
                        print(f"   ⚠️  WARNING - Security Score: {security_score}/100")
                        warning_count += 1
                        for rec in security_data.get("recommendations", [])[:2]:
                            print(f"      {rec}")
                    else:
                        print(f"   ✅ SAFE - Security Score: {security_score}/100")
                        safe_count += 1

                    # Utiliser le contenu nettoyé pour la classification
                    if (
                        "sanitized_content" in security_data
                        and "text" in security_data["sanitized_content"]
                    ):
                        text = security_data["sanitized_content"]["text"]

                except Exception as e:
                    print(f"   ❌ Security scan failed: {e}")
                    print("   ⚠️  Proceeding with caution")
                    security_data = {
                        "security_level": "UNKNOWN",
                        "security_score": 0,
                        "error": str(e),
                    }
            # === FIN SCAN DE SÉCURITÉ ===

            if not text.strip():
                print("   ⚠️  No text - skipping")
                continue

            # 2a. Classifier
            print("   🤖 Classifying...")
            try:
                class_result = await class_session.call_tool(
                    "classify_email", arguments={"text": text}
                )
                class_data = json.loads(class_result.content[0].text)

                category = class_data["category"]
                confidence = class_data["confidence"]

                print(f"   ✅ Category: {category} ({confidence:.1%})")
            except Exception as e:
                print(f"   ❌ Classification failed: {e}")
                continue

            # 2b. Générer réponse
            print("   📝 Generating response...")
            try:
                response_result = await response_session.call_tool(
                    "generate_response",
                    arguments={
                        "category": category,
                        "subject": email.get("subject", ""),
                        "confidence": confidence,
                        "min_confidence": self.min_confidence,
                    },
                )
                response_data = json.loads(response_result.content[0].text)

                should_send = response_data["should_send_auto"]
                priority = response_data["priority"]
                action = response_data["action"]

                print(f"   🎯 Priority: {priority}")
                print(f"   🎯 Action: {action}")
            except Exception as e:
                print(f"   ❌ Response generation failed: {e}")
                continue

            # 2c. Créer brouillon ou envoyer si auto_reply activé
            # Ne pas envoyer si l'email a un niveau de sécurité WARNING
            if security_data and security_data.get("security_level") == "WARNING":
                print("   ⚠️  Auto-reply disabled for security WARNING")
                should_send = False

            if auto_reply and should_send and response_data["response_body"]:
                if dry_run:
                    # Mode simulation
                    if self.draft_mode:
                        print("   🧪 [DRY RUN] Would create draft")
                    else:
                        print("   🧪 [DRY RUN] Would send email directly")
                else:
                    # Mode réel
                    try:
                        # NOUVEAU : Choix entre draft et envoi direct
                        if self.draft_mode:
                            print("   📝 Creating draft...")
                            result = await sender_session.call_tool(
                                "create_draft",
                                arguments={
                                    "to": email.get("from", ""),
                                    "subject": email.get("subject", ""),
                                    "body": response_data["response_body"],
                                    "thread_id": email.get("threadId"),
                                    "message_id": email.get("id"),
                                },
                            )
                            result_data = json.loads(result.content[0].text)

                            if result_data["success"]:
                                print("   ✅ Draft created successfully!")
                                print(f"      Draft ID: {result_data.get('draft_id')}")
                                draft_created_count += 1
                            else:
                                print(
                                    f"   ❌ Failed to create draft: {result_data.get('error')}"
                                )
                        else:
                            print("   📤 Sending email directly...")
                            result = await sender_session.call_tool(
                                "send_email",
                                arguments={
                                    "to": email.get("from", ""),
                                    "subject": email.get("subject", ""),
                                    "body": response_data["response_body"],
                                    "thread_id": email.get("threadId"),
                                    "message_id": email.get("id"),
                                },
                            )
                            result_data = json.loads(result.content[0].text)

                            if result_data["success"]:
                                print("   ✅ Email sent successfully!")
                                sent_count += 1
                            else:
                                print(
                                    f"   ❌ Failed to send: {result_data.get('error')}"
                                )
                    except Exception as e:
                        print(f"   ❌ Error: {e}")
            elif should_send and not auto_reply:
                print("   ℹ️  Auto-reply disabled (use --auto-reply to enable)")

            # Sauvegarder les résultats
            self.results.append(
                {
                    "email": email,
                    "classification": class_data,
                    "response": response_data,
                    "security": security_data,
                }
            )

        # 3. Résumé
        self._print_summary(
            blocked_count, warning_count, safe_count, draft_created_count, sent_count
        )

    def _print_summary(
        self,
        blocked_count: int = 0,
        warning_count: int = 0,
        safe_count: int = 0,
        draft_count: int = 0,
        sent_count: int = 0,
    ):
        """Affiche le résumé."""
        print("\n" + "=" * 70)
        print("📊 SUMMARY")
        print("=" * 70)

        if not self.results:
            print("   No emails processed")
            return

        # Stats de sécurité
        if self.enable_security:
            print("\n🔒 Security Statistics:")
            print(f"   ✅ Safe emails: {safe_count}")
            print(f"   ⚠️  Warning emails: {warning_count}")
            print(f"   ⛔ Blocked emails: {blocked_count}")
            print(f"   📊 Total scanned: {safe_count + warning_count + blocked_count}")

        # Stats par catégorie
        category_counts = {}
        auto_reply_count = 0
        manual_review_count = 0

        for result in self.results:
            cat = result["classification"]["category"]
            category_counts[cat] = category_counts.get(cat, 0) + 1

            if result["response"]["should_send_auto"]:
                auto_reply_count += 1
            else:
                manual_review_count += 1

        print("\n📦 By Category:")
        for cat, count in sorted(category_counts.items()):
            print(f"   • {cat}: {count} email(s)")

        # NOUVEAU : Stats drafts/sent
        if draft_count > 0 or sent_count > 0:
            print("\n📧 Actions Taken:")
            if draft_count > 0:
                print(f"   📝 Drafts created: {draft_count}")
            if sent_count > 0:
                print(f"   📤 Emails sent: {sent_count}")

        print(f"\n🤖 Auto-reply candidates: {auto_reply_count}")
        print(f"👤 Manual review needed: {manual_review_count}")
        print(f"📧 Total processed: {len(self.results)}")
        print("=" * 70)


async def main():
    """Point d'entrée principal."""
    import argparse

    parser = argparse.ArgumentParser(description="Gmail Support Agent with MCP")
    parser.add_argument(
        "--max-emails", type=int, default=10, help="Max emails to process"
    )
    parser.add_argument("--auto-reply", action="store_true", help="Enable auto-reply")
    parser.add_argument(
        "--no-dry-run", action="store_true", help="Actually send emails/drafts"
    )
    parser.add_argument(
        "--min-confidence", type=float, default=0.5, help="Min confidence (0-1)"
    )
    parser.add_argument(
        "--no-security", action="store_true", help="Disable security scanning"
    )
    parser.add_argument(
        "--send-direct",
        action="store_true",
        help="Send emails directly instead of creating drafts",
    )  # NOUVEAU

    args = parser.parse_args()

    agent = GmailSupportAgent(
        min_confidence=args.min_confidence,
        enable_security=not args.no_security,
        draft_mode=not args.send_direct,  # NOUVEAU : Mode brouillon par défaut
    )

    await agent.process_emails(
        max_emails=args.max_emails,
        auto_reply=args.auto_reply,
        dry_run=not args.no_dry_run,
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
