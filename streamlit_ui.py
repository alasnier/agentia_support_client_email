import asyncio

import streamlit as st

# Import de votre agent
from mcp_agent_orchestrator import GmailSupportAgent

st.set_page_config(
    page_title="Gmail Support Agent",
    page_icon="📧",
    layout="wide"
)

st.title("📧 Gmail Support Agent - MCP")
st.markdown("---")

# Sidebar configuration
with st.sidebar:
    st.header("⚙️ Configuration")

    max_emails = st.slider("Max emails to process", 1, 50, 10)
    min_confidence = st.slider("Min confidence threshold", 0.0, 1.0, 0.5, 0.05)
    auto_reply = st.checkbox("Enable auto-reply", value=False)
    dry_run = st.checkbox("Dry run (simulation)", value=True)

    st.markdown("---")
    st.info("**Dry run**: Test mode - no emails sent")

    if st.button("🚀 Process Emails", type="primary"):
        st.session_state.run_agent = True

# Main content
if "run_agent" not in st.session_state:
    st.session_state.run_agent = False

if st.session_state.run_agent:
    st.session_state.run_agent = False

    with st.spinner("Processing emails..."):
        # Créer et exécuter l'agent
        agent = GmailSupportAgent(min_confidence=min_confidence)

        # Exécuter de manière asynchrone
        asyncio.run(agent.process_emails(
            max_emails=max_emails,
            auto_reply=auto_reply,
            dry_run=dry_run
        ))

        # Afficher les résultats
        if agent.results:
            st.success(f"✅ Processed {len(agent.results)} emails")

            # Stats
            col1, col2, col3 = st.columns(3)

            auto_count = sum(1 for r in agent.results if r["response"]["should_send_auto"])
            manual_count = len(agent.results) - auto_count

            with col1:
                st.metric("Total Emails", len(agent.results))
            with col2:
                st.metric("Auto-reply", auto_count)
            with col3:
                st.metric("Manual Review", manual_count)

            st.markdown("---")

            # Par catégorie
            categories = {}
            for r in agent.results:
                cat = r["classification"]["category"]
                categories[cat] = categories.get(cat, 0) + 1

            st.subheader("📊 By Category")
            for cat, count in categories.items():
                st.write(f"**{cat}**: {count} email(s)")

            st.markdown("---")

            # Détails des emails
            st.subheader("📧 Email Details")

            for i, result in enumerate(agent.results, 1):
                email = result["email"]
                classification = result["classification"]
                response = result["response"]

                with st.expander(f"Email {i}: {email.get('subject', '(no subject)')}"):
                    col1, col2 = st.columns([1, 1])

                    with col1:
                        st.write("**From:**", email.get("from"))
                        st.write("**Date:**", email.get("date"))
                        st.write("**Category:**", classification["category"])
                        st.write("**Confidence:**", f"{classification['confidence']:.1%}")

                    with col2:
                        st.write("**Priority:**", response["priority"])
                        st.write("**Action:**", response["action"])
                        st.write("**Auto-reply:**", "✅" if response["should_send_auto"] else "❌")

                    st.markdown("**Preview:**")
                    st.text(email.get("snippet", "")[:200])

                    if response["response_body"]:
                        st.markdown("**Generated Response:**")
                        st.text_area("", response["response_body"], height=200, key=f"response_{i}")
        else:
            st.warning("No emails processed")
else:
    st.info("👈 Configure settings in the sidebar and click 'Process Emails' to start")

    # Instructions
    st.markdown("""
    ## 📖 How to use

    1. **Configure** settings in the sidebar
    2. Click **Process Emails** button
    3. View results and generated responses
    4. Enable **auto-reply** when ready (disable dry-run to actually send)

    ## ⚡ Features

    - ✅ Automatic email classification (5 categories)
    - ✅ AI-powered response generation
    - ✅ Confidence-based auto-reply
    - ✅ Dry-run mode for testing
    - ✅ Priority management
    """)
