import asyncio
import json
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class GmailSupportAgent:
    """Agent de support client Gmail avec MCP."""

    def __init__(self, min_confidence: float = 0.5):
        self.min_confidence = min_confidence
        self.results = []

    async def process_emails(
            self,
            max_emails: int = 10,
            auto_reply: bool = False,
            dry_run: bool = True
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
        print(f"📊 Config: max_emails={max_emails}, auto_reply={auto_reply}, dry_run={dry_run}")
        print(f"🎯 Min confidence: {self.min_confidence:.0%}")
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

        # Connexion aux serveurs MCP
        async with stdio_client(gmail_params) as (gr, gw):
            async with ClientSession(gr, gw) as gmail_session:
                async with stdio_client(classifier_params) as (cr, cw):
                    async with ClientSession(cr, cw) as class_session:
                        async with stdio_client(response_gen_params) as (rr, rw):
                            async with ClientSession(rr, rw) as response_session:
                                async with stdio_client(sender_params) as (sr, sw):
                                    async with ClientSession(sr, sw) as sender_session:
                                        # Initialiser les sessions
                                        await gmail_session.initialize()
                                        await class_session.initialize()
                                        await response_session.initialize()
                                        await sender_session.initialize()

                                        print("\n✅ All MCP servers connected!\n")

                                        # Traiter les emails
                                        await self._process_pipeline(
                                            gmail_session,
                                            class_session,
                                            response_session,
                                            sender_session,
                                            max_emails,
                                            auto_reply,
                                            dry_run
                                        )

    async def _process_pipeline(
            self,
            gmail_session,
            class_session,
            response_session,
            sender_session,
            max_emails,
            auto_reply,
            dry_run
    ):
        """Pipeline de traitement."""

        # 1. Récupérer les emails
        print("📥 Fetching emails from Gmail...")
        emails_result = await gmail_session.call_tool(
            "list_emails", arguments={"max_results": max_emails}
        )

        emails_data = json.loads(emails_result.content[0].text)
        print(f"✅ Found {len(emails_data)} emails\n")

        # 2. Traiter chaque email
        for i, email in enumerate(emails_data, 1):
            print("-" * 70)
            print(f"\n📧 Email {i}/{len(emails_data)}")
            print(f"   From: {email.get('from', 'Unknown')}")
            print(f"   Subject: {email.get('subject', '(no subject)')}")

            text = email.get("bodyText", "") or email.get("snippet", "")

            if not text.strip():
                print("   ⚠️  No text - skipping")
                continue

            # 2a. Classifier
            print("   🤖 Classifying...")
            class_result = await class_session.call_tool(
                "classify_email", arguments={"text": text}
            )
            class_data = json.loads(class_result.content[0].text)

            category = class_data["category"]
            confidence = class_data["confidence"]

            print(f"   ✅ Category: {category} ({confidence:.1%})")

            # 2b. Générer réponse
            print("   📝 Generating response...")
            response_result = await response_session.call_tool(
                "generate_response",
                arguments={
                    "category": category,
                    "subject": email.get("subject", ""),
                    "confidence": confidence,
                    "min_confidence": self.min_confidence
                }
            )
            response_data = json.loads(response_result.content[0].text)

            should_send = response_data["should_send_auto"]
            priority = response_data["priority"]
            action = response_data["action"]

            print(f"   🎯 Priority: {priority}")
            print(f"   🎯 Action: {action}")

            # 2c. Envoyer si auto_reply activé
            if auto_reply and should_send and response_data["response_body"]:
                if dry_run:
                    print(f"   🧪 [DRY RUN] Would send auto-reply")
                else:
                    print(f"   📤 Sending auto-reply...")
                    try:
                        send_result = await sender_session.call_tool(
                            "send_email",
                            arguments={
                                "to": email.get("from", ""),
                                "subject": email.get("subject", ""),
                                "body": response_data["response_body"],
                                "thread_id": email.get("threadId"),
                                "message_id": email.get("id")
                            }
                        )
                        send_data = json.loads(send_result.content[0].text)

                        if send_data["success"]:
                            print(f"   ✅ Email sent successfully!")
                        else:
                            print(f"   ❌ Failed to send: {send_data.get('error')}")
                    except Exception as e:
                        print(f"   ❌ Error sending: {e}")
            elif should_send and not auto_reply:
                print(f"   ℹ️  Auto-reply disabled (use --auto-reply to enable)")

            # Sauvegarder les résultats
            self.results.append({
                "email": email,
                "classification": class_data,
                "response": response_data
            })

        # 3. Résumé
        self._print_summary()

    def _print_summary(self):
        """Affiche le résumé."""
        print("\n" + "=" * 70)
        print("📊 SUMMARY")
        print("=" * 70)

        if not self.results:
            print("   No emails processed")
            return

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

        print(f"\n🤖 Auto-reply candidates: {auto_reply_count}")
        print(f"👤 Manual review needed: {manual_review_count}")
        print(f"📧 Total processed: {len(self.results)}")
        print("=" * 70)


async def main():
    """Point d'entrée principal."""
    import argparse

    parser = argparse.ArgumentParser(description="Gmail Support Agent with MCP")
    parser.add_argument("--max-emails", type=int, default=10, help="Max emails to process")
    parser.add_argument("--auto-reply", action="store_true", help="Enable auto-reply")
    parser.add_argument("--no-dry-run", action="store_true", help="Actually send emails")
    parser.add_argument("--min-confidence", type=float, default=0.5, help="Min confidence (0-1)")

    args = parser.parse_args()

    agent = GmailSupportAgent(min_confidence=args.min_confidence)

    await agent.process_emails(
        max_emails=args.max_emails,
        auto_reply=args.auto_reply,
        dry_run=not args.no_dry_run
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
