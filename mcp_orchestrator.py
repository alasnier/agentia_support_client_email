import asyncio
import json
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    print("=" * 60)
    print("🚀 Gmail Support Agent - MCP Pipeline")
    print("=" * 60)

    # Connexion au serveur Gmail
    print("\n📧 Connecting to Gmail MCP server...")
    gmail_params = StdioServerParameters(
        command="python",
        args=["gmail_mcp_server.py"],
        env=None
    )

    # Connexion au serveur de classification
    print("🤖 Connecting to Classification MCP server...")
    classifier_params = StdioServerParameters(
        command="python",
        args=["classification_mcp_server.py"],
        env=None
    )

    async with stdio_client(gmail_params) as (gmail_read, gmail_write):
        async with ClientSession(gmail_read, gmail_write) as gmail_session:

            async with stdio_client(classifier_params) as (class_read, class_write):
                async with ClientSession(class_read, class_write) as class_session:

                    # Initialiser les sessions
                    await gmail_session.initialize()
                    await class_session.initialize()

                    print("\n✅ Both servers connected!")
                    print("\n" + "=" * 60)

                    # Récupérer les emails
                    print("\n📥 Fetching emails from Gmail...")
                    emails_result = await gmail_session.call_tool(
                        "list_emails",
                        arguments={"max_results": 5}
                    )

                    # Parser la réponse MCP
                    if not emails_result.content:
                        print("❌ No content returned from Gmail server")
                        return

                    # Le contenu est dans le premier élément de content
                    emails_json = emails_result.content[0].text
                    emails_data = json.loads(emails_json)

                    print(f"✅ Found {len(emails_data)} emails\n")

                    # Traiter chaque email
                    results = []

                    for i, email in enumerate(emails_data, 1):
                        print("-" * 60)
                        print(f"\n📧 Email {i}/{len(emails_data)}")
                        print(f"   From: {email.get('from', 'Unknown')}")
                        print(f"   Subject: {email.get('subject', '(no subject)')}")
                        print(f"   Date: {email.get('date', 'Unknown')}")

                        text = email.get("bodyText", "") or email.get("snippet", "")

                        if not text.strip():
                            print("   ⚠️  No text to classify - skipping")
                            continue

                        preview = text[:100].replace('\n', ' ').replace('\r', '')
                        print(f"   Preview: {preview}...")

                        # Classifier l'email
                        print("\n   🤖 Classifying...")

                        try:
                            classification_result = await class_session.call_tool(
                                "classify_email",
                                arguments={"text": text}
                            )

                            # Parser le résultat
                            if not classification_result.content:
                                print("   ❌ No classification result")
                                continue

                            class_json = classification_result.content[0].text
                            class_data = json.loads(class_json)

                            category = class_data.get("category", "unknown")
                            confidence = class_data.get("confidence", 0.0)

                            print(f"   ✅ Category: {category}")
                            print(f"   📊 Confidence: {confidence:.2%}")

                            # Déterminer l'action selon la catégorie
                            action = determine_action(category, confidence)
                            print(f"   🎯 Action: {action}")

                            results.append({
                                "email": email,
                                "classification": class_data,
                                "action": action
                            })

                        except Exception as e:
                            print(f"   ❌ Error classifying: {e}")
                            import traceback
                            traceback.print_exc()

                    # Résumé final
                    print("\n" + "=" * 60)
                    print("📊 SUMMARY")
                    print("=" * 60)

                    if not results:
                        print("   No emails processed")
                    else:
                        category_counts = {}
                        for result in results:
                            cat = result["classification"].get("category", "unknown")
                            category_counts[cat] = category_counts.get(cat, 0) + 1

                        for cat, count in category_counts.items():
                            print(f"   {cat}: {count} email(s)")

                        print(f"\n   Total processed: {len(results)}/{len(emails_data)}")

                    print("=" * 60)


def determine_action(category: str, confidence: float) -> str:
    """Détermine l'action à prendre selon la catégorie et la confiance."""

    if confidence < 0.5:
        return "Manual review required (low confidence)"

    actions = {
        "support technique": "Send auto-reply + Create ticket",
        "question commerciale": "Forward to sales team",
        "demande information": "Send info pack",
        "spam": "Mark as spam + Delete",
        "urgence": "ALERT TEAM + Auto-reply + High priority ticket"
    }

    return actions.get(category, "Unknown action")


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
