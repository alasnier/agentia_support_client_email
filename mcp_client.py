import asyncio

from mcp.client.session import ClientSession
from mcp.client.transport import StdioTransport


async def connect_process(cmd):
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
    )
    transport = StdioTransport(proc.stdout, proc.stdin)
    session = ClientSession(transport)
    await session.start()
    return session


async def main():
    print("🚀 Starting Gmail MCP server...")
    gmail = await connect_process(["python", "gmail_mcp_server.py", "--port", "8080"])

    print("🚀 Starting classification MCP server...")
    classifier = await connect_process(["python", "classification_mcp_server.py", "--port", "8081"])

    print("📩 Fetching emails...")
    emails = await gmail.call_tool("list_emails", {"max_results": 5})

    for email in emails:
        subject = email.get("subject", "(no subject)")
        text = email.get("snippet", "") or ""

        print(f"\n📧 Email: {subject}")

        if not text.strip():
            print("⚠️ No text to classify.")
            continue

        print("🤖 Classifying...")
        result = await classifier.call_tool("classify_email", {"text": text})

        print(f" 🏷️ Category: {result['category']} ({result['confidence']:.2f})")
        print("-" * 40)


asyncio.run(main())
