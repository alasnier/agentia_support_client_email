import asyncio

import streamlit as st

# Import de votre agent
from mcp_agent_orchestrator import GmailSupportAgent

st.set_page_config(
    page_title="Gmail Support Agent",
    page_icon="📧",
    layout="wide"
)

# CSS personnalisé pour améliorer l'apparence
st.markdown("""
<style>
    .security-danger {
        background-color: #ff4444;
        color: white;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .security-warning {
        background-color: #ffaa00;
        color: white;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .security-safe {
        background-color: #44ff44;
        color: white;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

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

    # Section sécurité
    st.subheader("🔒 Security Settings")
    enable_security = st.checkbox("Enable security scan", value=True)

    if enable_security:
        st.success("**Security features enabled:**")
        st.markdown("""
        - ✅ URL validation
        - ✅ HTML sanitization
        - ✅ Attachment scanning
        - ✅ Pattern detection
        - ✅ Sender verification
        - ✅ Invisible text removal
        """)
    else:
        st.warning("⚠️ Security scanning disabled")

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
        agent = GmailSupportAgent(
            min_confidence=min_confidence,
            enable_security=enable_security
        )

        # Exécuter de manière asynchrone
        try:
            asyncio.run(agent.process_emails(
                max_emails=max_emails,
                auto_reply=auto_reply,
                dry_run=dry_run
            ))
        except Exception as e:
            st.error(f"❌ Error processing emails: {e}")
            st.stop()

        # Afficher les résultats
        if agent.results:
            st.success(f"✅ Processed {len(agent.results)} emails")

            # Stats principales
            col1, col2, col3, col4 = st.columns(4)

            auto_count = sum(1 for r in agent.results if r["response"]["should_send_auto"])
            manual_count = len(agent.results) - auto_count

            # Compter les emails bloqués
            blocked_count = sum(1 for r in agent.results if r["classification"]["category"] == "BLOCKED")

            with col1:
                st.metric("Total Emails", len(agent.results))
            with col2:
                st.metric("Auto-reply", auto_count)
            with col3:
                st.metric("Manual Review", manual_count)
            with col4:
                st.metric("🔒 Blocked", blocked_count)

            st.markdown("---")

            # Stats de sécurité
            if enable_security:
                st.subheader("🔒 Security Analysis")

                sec_col1, sec_col2, sec_col3 = st.columns(3)

                safe_count = sum(1 for r in agent.results
                                 if r.get("security") and r["security"].get("security_level") == "SAFE")
                warning_count = sum(1 for r in agent.results
                                    if r.get("security") and r["security"].get("security_level") == "WARNING")
                danger_count = sum(1 for r in agent.results
                                   if r.get("security") and r["security"].get("security_level") == "DANGER")

                with sec_col1:
                    st.metric("✅ Safe", safe_count, delta=None)
                with sec_col2:
                    st.metric("⚠️ Warning", warning_count, delta=None)
                with sec_col3:
                    st.metric("⛔ Danger", danger_count, delta=None)

                # Graphique de répartition sécurité
                if safe_count + warning_count + danger_count > 0:
                    security_data = {
                        "Safe": safe_count,
                        "Warning": warning_count,
                        "Danger": danger_count
                    }
                    st.bar_chart(security_data)

                st.markdown("---")

            # Par catégorie
            categories = {}
            for r in agent.results:
                cat = r["classification"]["category"]
                categories[cat] = categories.get(cat, 0) + 1

            st.subheader("📊 By Category")

            # Créer un graphique
            if categories:
                st.bar_chart(categories)

                # Détails textuels
                for cat, count in sorted(categories.items()):
                    if cat == "BLOCKED":
                        st.error(f"🚫 **{cat}**: {count} email(s)")
                    else:
                        st.write(f"**{cat}**: {count} email(s)")

            st.markdown("---")

            # Détails des emails
            st.subheader("📧 Email Details")

            # Filtre par catégorie
            filter_category = st.selectbox(
                "Filter by category",
                ["All"] + list(set(r["classification"]["category"] for r in agent.results))
            )

            # Filtre par niveau de sécurité
            security_filter = "All"
            if enable_security:
                security_filter = st.selectbox(
                    "Filter by security level",
                    ["All", "SAFE", "WARNING", "DANGER", "BLOCKED"]
                )

            for i, result in enumerate(agent.results, 1):
                email = result["email"]
                classification = result["classification"]
                response = result["response"]
                security = result.get("security")

                # Appliquer les filtres
                if filter_category != "All" and classification["category"] != filter_category:
                    continue

                if enable_security and security_filter != "All":
                    if security and security.get("security_level") != security_filter:
                        if not (security_filter == "BLOCKED" and classification["category"] == "BLOCKED"):
                            continue

                # Déterminer la couleur du titre selon la sécurité
                title_prefix = ""
                if security:
                    sec_level = security.get("security_level", "UNKNOWN")
                    if sec_level == "DANGER" or classification["category"] == "BLOCKED":
                        title_prefix = "⛔ "
                    elif sec_level == "WARNING":
                        title_prefix = "⚠️ "
                    elif sec_level == "SAFE":
                        title_prefix = "✅ "

                with st.expander(f"{title_prefix}Email {i}: {email.get('subject', '(no subject)')}"):
                    # Informations principales
                    col1, col2 = st.columns([1, 1])

                    with col1:
                        st.write("**From:**", email.get("from"))
                        st.write("**Date:**", email.get("date"))
                        st.write("**Category:**", classification["category"])
                        st.write("**Confidence:**", f"{classification['confidence']:.1%}")

                    with col2:
                        st.write("**Priority:**", response["priority"])
                        st.write("**Action:**", response["action"])
                        st.write("**Auto-reply:**", "✅ Yes" if response["should_send_auto"] else "❌ No")

                    st.markdown("---")

                    # Afficher les infos de sécurité si disponibles
                    if enable_security and security:
                        st.markdown("### 🔒 Security Analysis")

                        security_level = security.get("security_level", "UNKNOWN")
                        security_score = security.get("security_score", 0)

                        # Badge de sécurité coloré
                        if security_level == "DANGER" or classification["category"] == "BLOCKED":
                            st.error(f"⛔ **DANGER** - Security Score: {security_score}/100")
                        elif security_level == "WARNING":
                            st.warning(f"⚠️ **WARNING** - Security Score: {security_score}/100")
                        elif security_level == "SAFE":
                            st.success(f"✅ **SAFE** - Security Score: {security_score}/100")
                        else:
                            st.info(f"❓ **UNKNOWN** - Security Score: {security_score}/100")

                        # Vérification expéditeur
                        if "is_sender_trusted" in security:
                            if security["is_sender_trusted"]:
                                st.success("✅ Sender is in trusted list")
                            else:
                                st.warning("⚠️ Sender is NOT in trusted list")

                        # Issues détectés
                        if security.get("issues"):
                            st.markdown("**🚨 Security Issues:**")
                            for issue in security["issues"]:
                                severity = issue.get("severity", "UNKNOWN")
                                issue_type = issue.get("type", "Unknown")
                                message = issue.get("message", "No details")

                                if severity == "HIGH":
                                    st.error(f"🔴 **{issue_type}**: {message}")
                                elif severity == "MEDIUM":
                                    st.warning(f"🟡 **{issue_type}**: {message}")
                                else:
                                    st.info(f"🔵 **{issue_type}**: {message}")

                        # URLs
                        if security.get("urls"):
                            urls_info = security["urls"]
                            if urls_info.get("dangerous_count", 0) > 0:
                                with st.expander(f"⚠️ Dangerous URLs ({urls_info['dangerous_count']})"):
                                    for url in urls_info.get("dangerous", []):
                                        st.code(url, language=None)

                            if urls_info.get("safe_count", 0) > 0:
                                with st.expander(f"✅ Safe URLs ({urls_info['safe_count']})"):
                                    for url in urls_info.get("safe", []):
                                        st.text(url)

                        # Pièces jointes
                        if security.get("attachments"):
                            attachments = security["attachments"]
                            if attachments.get("total_dangerous", 0) > 0:
                                st.error(f"🚨 {attachments['total_dangerous']} dangerous attachment(s) detected")
                                with st.expander("View dangerous attachments"):
                                    for att in attachments.get("dangerous_attachments", []):
                                        st.write(f"- **{att.get('filename')}** ({att.get('risk')} risk)")
                                        st.write(f"  Reason: {att.get('reason')}")

                            if attachments.get("total_safe", 0) > 0:
                                st.success(f"✅ {attachments['total_safe']} safe attachment(s)")

                        # Recommandations
                        if security.get("recommendations"):
                            st.markdown("**💡 Recommendations:**")
                            for rec in security["recommendations"]:
                                st.write(f"- {rec}")

                        st.markdown("---")

                    # Preview de l'email
                    st.markdown("**📧 Email Preview:**")
                    preview_text = email.get("snippet", "")[:300]
                    if enable_security and security and "sanitized_content" in security:
                        preview_text = security["sanitized_content"].get("text", preview_text)[:300]
                    st.text(preview_text)

                    # Réponse générée
                    if response.get("response_body"):
                        st.markdown("**📝 Generated Response:**")
                        st.text_area(
                            "",
                            response["response_body"],
                            height=200,
                            key=f"response_{i}",
                            disabled=True
                        )
                    elif classification["category"] == "BLOCKED":
                        st.error("🚫 No response generated - Email blocked for security reasons")
        else:
            st.warning("No emails processed")
else:
    # Page d'accueil
    st.info("👈 Configure settings in the sidebar and click 'Process Emails' to start")

    # Instructions
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        ## 📖 How to use

        1. **Configure** settings in the sidebar
        2. **Enable security** for safe email processing
        3. Click **Process Emails** button
        4. View results and generated responses
        5. Enable **auto-reply** when ready (disable dry-run to actually send)

        ## ⚙️ Configuration Options

        - **Max emails**: Number of emails to process
        - **Min confidence**: Threshold for auto-reply (0-1)
        - **Auto-reply**: Enable automatic responses
        - **Dry run**: Test mode (no emails sent)
        - **Security scan**: Enable security analysis
        """)

    with col2:
        st.markdown("""
        ## ⚡ Features

        ### 📧 Email Processing
        - ✅ Automatic email classification (5 categories)
        - ✅ AI-powered response generation
        - ✅ Confidence-based auto-reply
        - ✅ Priority management

        ### 🔒 Security Features
        - ✅ Sender whitelist verification
        - ✅ URL validation and filtering
        - ✅ HTML sanitization
        - ✅ Attachment scanning
        - ✅ Dangerous pattern detection
        - ✅ Invisible text removal
        - ✅ Security scoring (0-100)
        - ✅ Automatic blocking of dangerous emails
        """)

    # Statistiques du système
    st.markdown("---")
    st.subheader("📊 System Info")

    info_col1, info_col2, info_col3 = st.columns(3)

    with info_col1:
        st.info("""
        **🤖 Classification**
        - Model: BART-Large-MNLI
        - Categories: 5
        - Provider: Hugging Face
        """)

    with info_col2:
        st.info("""
        **🔒 Security**
        - URL Filtering: ✅
        - HTML Sanitization: ✅
        - Attachment Scan: ✅
        """)

    with info_col3:
        st.info("""
        **📤 Auto-Reply**
        - Smart Templates: ✅
        - Confidence-based: ✅
        - Dry-run mode: ✅
        """)
