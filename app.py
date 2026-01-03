"""
JoveHeal Wellness Chatbot - Main Streamlit Application

A RAG-based chatbot for JoveHeal wellness coaching business.
Provides information about programs, services, and offerings.
"""

import streamlit as st
import uuid
import os
from datetime import datetime

from chatbot_engine import (
    generate_response,
    get_greeting_message,
    check_knowledge_base_status
)
from knowledge_base import (
    initialize_knowledge_base,
    ingest_pdf_file,
    ingest_text_file,
    get_knowledge_base_stats,
    clear_knowledge_base,
    ingest_website_content
)
from conversation_logger import (
    log_conversation,
    get_recent_logs,
    get_flagged_conversations,
    get_conversation_stats,
    get_analytics_by_date,
    get_feedback_summary,
    add_feedback,
    migrate_file_logs_to_database
)
from database import init_database, is_database_available

st.set_page_config(
    page_title="JoveHeal Assistant",
    page_icon="🌿",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    .stApp {
        max-width: 800px;
        margin: 0 auto;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .user-message {
        background-color: #e3f2fd;
    }
    .assistant-message {
        background-color: #f5f5f5;
    }
    .source-tag {
        font-size: 0.75rem;
        color: #666;
        margin-top: 0.5rem;
    }
    .status-badge {
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-size: 0.8rem;
    }
    .status-ready {
        background-color: #c8e6c9;
        color: #2e7d32;
    }
    .status-loading {
        background-color: #fff3e0;
        color: #ef6c00;
    }
</style>
""", unsafe_allow_html=True)

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

if "kb_initialized" not in st.session_state:
    st.session_state.kb_initialized = False

if "show_admin" not in st.session_state:
    st.session_state.show_admin = False


def initialize_database_if_needed():
    """Initialize database on first run."""
    if "db_initialized" not in st.session_state:
        if is_database_available():
            init_database()
            st.session_state.db_initialized = True
        else:
            st.session_state.db_initialized = False


def initialize_kb_if_needed():
    """Initialize knowledge base on first run."""
    initialize_database_if_needed()
    
    if not st.session_state.kb_initialized:
        status = check_knowledge_base_status()
        if not status["ready"]:
            with st.spinner("Setting up knowledge base... This may take a few minutes on first run."):
                success = initialize_knowledge_base()
                st.session_state.kb_initialized = success
        else:
            st.session_state.kb_initialized = True


def render_chat_interface():
    """Render the main chat interface."""
    st.title("JoveHeal Assistant")
    st.markdown("*Your guide to wellness coaching programs and services*")
    
    status = check_knowledge_base_status()
    if status["ready"]:
        st.markdown(f'<span class="status-badge status-ready">Knowledge Base Ready ({status["chunks"]} documents)</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-badge status-loading">Knowledge Base Loading...</span>', unsafe_allow_html=True)
    
    st.divider()
    
    if not st.session_state.messages:
        greeting = get_greeting_message()
        st.session_state.messages.append({
            "role": "assistant",
            "content": greeting
        })
    
    for idx, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message.get("sources"):
                sources_text = " | ".join(message["sources"][:3])
                st.caption(f"Sources: {sources_text}")
            
            if message["role"] == "assistant" and message.get("conversation_id") and is_database_available():
                conv_id = message["conversation_id"]
                feedback_key = f"feedback_{conv_id}"
                comment_key = f"comment_{conv_id}"
                show_comment_key = f"show_comment_{conv_id}"
                
                if feedback_key not in st.session_state:
                    col1, col2, col3 = st.columns([1, 1, 8])
                    with col1:
                        if st.button("up", key=f"up_{idx}_{conv_id}"):
                            st.session_state[feedback_key] = 1
                            st.session_state[show_comment_key] = True
                            st.rerun()
                    with col2:
                        if st.button("down", key=f"down_{idx}_{conv_id}"):
                            st.session_state[feedback_key] = -1
                            st.session_state[show_comment_key] = True
                            st.rerun()
                elif st.session_state.get(show_comment_key, False):
                    rating = st.session_state[feedback_key]
                    comment = st.text_input(
                        "Any additional feedback? (optional)",
                        key=f"comment_input_{conv_id}",
                        placeholder="Tell us more..."
                    )
                    if st.button("Submit", key=f"submit_{idx}_{conv_id}"):
                        add_feedback(conv_id, rating, comment if comment else None)
                        st.session_state[show_comment_key] = False
                        st.session_state[comment_key] = comment
                        st.rerun()
                    if st.button("Skip", key=f"skip_{idx}_{conv_id}"):
                        add_feedback(conv_id, rating, None)
                        st.session_state[show_comment_key] = False
                        st.rerun()
                else:
                    feedback_val = st.session_state[feedback_key]
                    saved_comment = st.session_state.get(comment_key)
                    if feedback_val > 0:
                        st.caption("Thanks for the positive feedback!")
                    else:
                        st.caption("Thanks for letting us know. We'll work to improve.")
                    if saved_comment:
                        st.caption(f"Your comment: {saved_comment[:50]}...")
    
    if prompt := st.chat_input("Ask me about JoveHeal's programs and services..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                result = generate_response(
                    user_message=prompt,
                    conversation_history=st.session_state.messages[:-1]
                )
                
                response = result["response"]
                sources = result.get("sources", [])
                safety_triggered = result.get("safety_triggered", False)
                
                st.markdown(response)
                
                if sources and not safety_triggered:
                    sources_text = " | ".join(sources[:3])
                    st.caption(f"Sources: {sources_text}")
                
                log_result = log_conversation(
                    session_id=st.session_state.session_id,
                    user_question=prompt,
                    bot_answer=response,
                    safety_flagged=safety_triggered,
                    safety_category=result.get("safety_category"),
                    sources=sources
                )
                
                conversation_id = log_result.get("conversation_id")
                
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response,
                    "sources": sources,
                    "conversation_id": conversation_id
                })


def render_admin_panel():
    """Render the admin panel for knowledge base management."""
    st.title("Admin Panel")
    st.markdown("*Manage knowledge base and view conversation logs*")
    
    if st.button("Back to Chat", key="back_to_chat"):
        st.session_state.show_admin = False
        st.rerun()
    
    st.divider()
    
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(["Knowledge Base", "Upload Documents", "Conversation Logs", "Analytics", "Embed Widget", "Channels", "Monitoring"])
    
    with tab1:
        st.subheader("Knowledge Base Status")
        
        stats = get_knowledge_base_stats()
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Chunks", stats["total_chunks"])
            st.metric("Website Pages", stats.get("website_pages", 0))
        with col2:
            last_scrape = stats.get("last_scrape", "Never")
            if last_scrape and last_scrape != "Never":
                try:
                    dt = datetime.fromisoformat(last_scrape)
                    last_scrape = dt.strftime("%Y-%m-%d %H:%M")
                except:
                    pass
            st.metric("Last Website Scrape", last_scrape)
            st.metric("Documents Uploaded", len(stats.get("documents", [])))
        
        st.divider()
        
        st.subheader("Actions")
        
        if st.button("Clear Knowledge Base", type="secondary"):
            if st.session_state.get("confirm_clear"):
                clear_knowledge_base()
                st.session_state.kb_initialized = False
                st.session_state.confirm_clear = False
                st.success("Knowledge base cleared!")
                st.rerun()
            else:
                st.session_state.confirm_clear = True
                st.warning("Click again to confirm clearing all knowledge base content.")
        
        if stats.get("documents"):
            st.subheader("Uploaded Documents")
            for doc in stats["documents"]:
                st.text(f"- {doc['filename']} ({doc['type']}, {doc['chunks']} chunks)")
    
    with tab2:
        st.subheader("Upload Documents")
        st.markdown("Upload PDF or text files to expand the knowledge base.")
        
        uploaded_file = st.file_uploader(
            "Choose a file",
            type=["pdf", "txt"],
            help="Upload PDF or TXT files containing JoveHeal information"
        )
        
        if uploaded_file is not None:
            if st.button("Process Document"):
                with st.spinner(f"Processing {uploaded_file.name}..."):
                    import tempfile
                    
                    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        tmp_path = tmp_file.name
                    
                    try:
                        if uploaded_file.name.lower().endswith('.pdf'):
                            chunks = ingest_pdf_file(tmp_path, uploaded_file.name)
                        else:
                            chunks = ingest_text_file(tmp_path, uploaded_file.name)
                        
                        if chunks > 0:
                            st.success(f"Successfully added {chunks} chunks from {uploaded_file.name}!")
                        else:
                            st.warning("No content could be extracted from the file.")
                    finally:
                        os.unlink(tmp_path)
        
        st.divider()
        st.subheader("Instructions")
        st.markdown("""
        **How to update the knowledge base:**
        
        1. **PDF Documents**: Upload PDF files (brochures, program guides, FAQs)
        2. **Text Files**: Upload .txt files with additional information
        
        The chatbot will use all uploaded content to answer visitor questions.
        Files are validated to ensure they contain readable text content.
        """)
    
    with tab3:
        st.subheader("Conversation Statistics")
        
        conv_stats = get_conversation_stats()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Conversations", conv_stats["total_conversations"])
        with col2:
            st.metric("Unique Sessions", conv_stats["unique_sessions"])
        with col3:
            st.metric("Safety Flags", conv_stats["safety_flags"])
        
        st.divider()
        
        st.subheader("Recent Conversations")
        logs = get_recent_logs(limit=20)
        
        if logs:
            for log in reversed(logs[-10:]):
                with st.expander(f"{log['timestamp'][:19]} - {log['user_question'][:50]}..."):
                    st.markdown(f"**User:** {log['user_question']}")
                    st.markdown(f"**Bot:** {log['bot_answer']}")
                    if log.get("safety_flagged"):
                        st.warning(f"Safety flagged: {log.get('safety_category', 'Unknown')}")
        else:
            st.info("No conversation logs yet.")
        
        st.divider()
        
        st.subheader("Flagged Conversations")
        flagged = get_flagged_conversations()
        
        if flagged:
            for log in flagged[-10:]:
                with st.expander(f"[FLAGGED] {log['timestamp'][:19]}"):
                    st.markdown(f"**Category:** {log.get('safety_category', 'Unknown')}")
                    st.markdown(f"**User:** {log['user_question']}")
                    st.markdown(f"**Bot:** {log['bot_answer']}")
        else:
            st.success("No flagged conversations.")
    
    with tab4:
        st.subheader("Analytics Dashboard")
        
        db_available = is_database_available()
        if db_available:
            st.success("Database connected - Full analytics available")
        else:
            st.warning("Database not connected - Limited analytics from file logs")
        
        conv_stats = get_conversation_stats()
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Conversations", conv_stats["total_conversations"])
        with col2:
            st.metric("Unique Sessions", conv_stats["unique_sessions"])
        with col3:
            st.metric("Safety Flags", conv_stats["safety_flags"])
        with col4:
            if conv_stats.get("avg_response_time_ms"):
                st.metric("Avg Response Time", f"{conv_stats['avg_response_time_ms']}ms")
            else:
                st.metric("Avg Response Time", "N/A")
        
        st.divider()
        
        if db_available:
            st.subheader("User Feedback Summary")
            feedback = get_feedback_summary()
            
            if feedback["total"] > 0:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Feedback", feedback["total"])
                with col2:
                    st.metric("Positive", feedback["positive"])
                with col3:
                    st.metric("Negative", feedback["negative"])
                
                if feedback["comments"]:
                    st.markdown("**Recent Comments:**")
                    for comment in feedback["comments"][:5]:
                        rating_icon = "+" if comment["rating"] > 0 else "-"
                        st.text(f"[{rating_icon}] {comment['comment'][:100]}")
            else:
                st.info("No feedback collected yet. Users can rate responses in the chat.")
            
            st.divider()
            
            st.subheader("Daily Trends (Last 30 Days)")
            daily_data = get_analytics_by_date(days=30)
            
            if daily_data:
                import pandas as pd
                df = pd.DataFrame(daily_data)
                df['date'] = pd.to_datetime(df['date'])
                
                st.line_chart(df.set_index('date')[['conversations', 'sessions']])
                
                st.markdown("**Daily Breakdown:**")
                for row in daily_data[-7:]:
                    st.text(f"{row['date']}: {row['conversations']} conversations, {row['sessions']} sessions, {row['safety_flags']} flags")
            else:
                st.info("No daily analytics data available yet.")
            
            st.divider()
            
            st.subheader("Data Management")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Migrate File Logs to Database"):
                    with st.spinner("Migrating logs..."):
                        migrated = migrate_file_logs_to_database()
                        if migrated > 0:
                            st.success(f"Migrated {migrated} log entries to database!")
                        else:
                            st.info("No logs to migrate or migration already complete.")
        else:
            st.info("Connect a PostgreSQL database to unlock full analytics including daily trends, feedback tracking, and data migration.")
    
    with tab5:
        st.subheader("Embed Chatbot Widget")
        st.markdown("Add the JoveHeal chatbot to your website using the embed code below.")
        
        replit_url = os.environ.get("REPLIT_DEV_DOMAIN", "your-replit-url.replit.dev")
        widget_url = f"https://{replit_url}/widget"
        
        st.markdown("### Widget Preview")
        st.info(f"Widget URL: {widget_url}")
        st.markdown("*Note: The widget runs on a separate endpoint for embedding.*")
        
        st.divider()
        
        st.markdown("### Embed Code")
        st.markdown("Copy and paste this code into your website's HTML:")
        
        iframe_code = f'''<iframe
    src="{widget_url}"
    width="400"
    height="600"
    style="border: none; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);"
    title="JoveHeal Chat Assistant">
</iframe>'''
        
        st.code(iframe_code, language="html")
        
        st.divider()
        
        st.markdown("### Floating Button Widget")
        st.markdown("For a floating chat button in the corner of your website:")
        
        floating_code = f'''<style>
.joveheal-chat-button {{
    position: fixed;
    bottom: 20px;
    right: 20px;
    width: 60px;
    height: 60px;
    border-radius: 50%;
    background: linear-gradient(135deg, #4a7c59 0%, #2d5a3d 100%);
    color: white;
    border: none;
    cursor: pointer;
    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    font-size: 24px;
    z-index: 9999;
}}
.joveheal-chat-widget {{
    position: fixed;
    bottom: 90px;
    right: 20px;
    width: 380px;
    height: 550px;
    border: none;
    border-radius: 12px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.2);
    z-index: 9998;
    display: none;
}}
.joveheal-chat-widget.open {{
    display: block;
}}
</style>
<button class="joveheal-chat-button" onclick="toggleJoveHealChat()">💬</button>
<iframe class="joveheal-chat-widget" id="joveheal-widget" src="{widget_url}"></iframe>
<script>
function toggleJoveHealChat() {{
    var widget = document.getElementById('joveheal-widget');
    widget.classList.toggle('open');
}}
</script>'''
        
        st.code(floating_code, language="html")
        
        st.divider()
        
        st.markdown("### Customization Tips")
        st.markdown("""
        - **Size**: Adjust `width` and `height` in the iframe to fit your design
        - **Position**: Modify `bottom` and `right` values for floating button placement
        - **Colors**: Update the gradient colors to match your brand
        - **Mobile**: Consider using responsive widths (e.g., `width="100%"`)
        """)
    
    with tab6:
        st.subheader("Multi-Channel Integration")
        st.markdown("Connect your JoveHeal chatbot to messaging platforms.")
        
        try:
            from channel_handlers import get_channel_status
            status = get_channel_status()
        except ImportError:
            status = {}
        
        replit_url = os.environ.get("REPLIT_DEV_DOMAIN", "your-replit-url.replit.dev")
        
        st.markdown("### WhatsApp (via Twilio)")
        wa_status = status.get("whatsapp", {})
        if wa_status.get("configured"):
            st.success("WhatsApp is configured and ready")
        else:
            st.warning("WhatsApp is not configured")
            st.markdown("**Required secrets:**")
            for secret in wa_status.get("required_secrets", []):
                st.code(secret)
        
        st.markdown("**Webhook URL:**")
        whatsapp_webhook = f"https://{replit_url}/webhook/whatsapp"
        st.code(whatsapp_webhook)
        
        with st.expander("WhatsApp Setup Instructions"):
            st.markdown("""
            1. **Create a Twilio account** at [twilio.com](https://www.twilio.com)
            2. **Enable WhatsApp** in your Twilio console
            3. **Get your credentials:**
               - Account SID
               - Auth Token
               - WhatsApp sandbox or approved number
            4. **Add secrets** to this project:
               - `TWILIO_ACCOUNT_SID`
               - `TWILIO_AUTH_TOKEN`
               - `TWILIO_WHATSAPP_NUMBER`
            5. **Configure webhook** in Twilio console:
               - Set the webhook URL above as your message handler
               - Select POST method
            
            **Security Note:** Webhook requests are validated using Twilio's signature verification.
            For custom deployments, set `WEBHOOK_BASE_URL` to your trusted base URL.
            """)
        
        st.divider()
        
        st.markdown("### Instagram (via Meta Graph API)")
        ig_status = status.get("instagram", {})
        if ig_status.get("configured"):
            st.success("Instagram is configured and ready")
        else:
            st.warning("Instagram is not configured")
            st.markdown("**Required secrets:**")
            for secret in ig_status.get("required_secrets", []):
                st.code(secret)
        
        st.markdown("**Webhook URL:**")
        instagram_webhook = f"https://{replit_url}/webhook/instagram"
        st.code(instagram_webhook)
        
        with st.expander("Instagram Setup Instructions"):
            st.markdown("""
            1. **Create a Meta Developer account** at [developers.facebook.com](https://developers.facebook.com)
            2. **Create a new app** with Messenger product
            3. **Connect your Instagram Business account**
            4. **Get your credentials:**
               - Page Access Token
               - Page ID
               - Create a Verify Token (any string you choose)
            5. **Add secrets** to this project:
               - `INSTAGRAM_ACCESS_TOKEN`
               - `INSTAGRAM_PAGE_ID`
               - `INSTAGRAM_VERIFY_TOKEN`
            6. **Configure webhook** in Meta developer console:
               - Set the webhook URL above
               - Enter your verify token
               - Subscribe to `messages` events
            """)
        
        st.divider()
        
        st.markdown("### Direct API Integration")
        st.markdown("For custom integrations, use the chat API endpoint:")
        
        api_url = f"https://{replit_url}/api/chat"
        st.code(api_url)
        
        st.markdown("**Example request:**")
        api_example = '''{
    "message": "What programs do you offer?",
    "user_id": "user123",
    "channel": "custom_app"
}'''
        st.code(api_example, language="json")
        
        st.markdown("**Response format:**")
        response_example = '''{
    "response": "JoveHeal offers several wellness programs...",
    "user_id": "user123",
    "channel": "custom_app"
}'''
        st.code(response_example, language="json")
        
        st.divider()
        
        st.markdown("### Webhook Server Status")
        st.info("The webhook server runs on port 8080 to handle incoming messages from external platforms.")
        st.markdown("Make sure to start the webhook server workflow for multi-channel messaging to work.")
    
    with tab7:
        st.subheader("Production Monitoring")
        st.markdown("Real-time uptime and performance monitoring via UptimeRobot.")
        
        uptimerobot_api_key = os.environ.get("UPTIMEROBOT_API_KEY")
        
        if not uptimerobot_api_key:
            st.warning("UptimeRobot API key not configured.")
            st.markdown("""
            **To enable monitoring:**
            1. Sign up at [uptimerobot.com](https://uptimerobot.com) (free)
            2. Add monitors for your production URLs
            3. Get your API key from Dashboard > Integrations & API
            4. Add `UPTIMEROBOT_API_KEY` to your Replit secrets
            """)
        else:
            import requests
            
            if st.button("Refresh Monitoring Data"):
                st.rerun()
            
            with st.spinner("Fetching monitoring data..."):
                try:
                    url = "https://api.uptimerobot.com/v2/getMonitors"
                    payload = {
                        "api_key": uptimerobot_api_key,
                        "format": "json",
                        "logs": "1",
                        "logs_limit": "10",
                        "response_times": "1",
                        "response_times_limit": "24",
                        "custom_uptime_ratios": "1-7-30-90"
                    }
                    
                    response = requests.post(url, data=payload, timeout=10)
                    data = response.json()
                    
                    if data.get("stat") == "ok":
                        monitors = data.get("monitors", [])
                        
                        if not monitors:
                            st.info("No monitors configured in UptimeRobot yet.")
                        else:
                            status_map = {0: "Paused", 1: "Not checked", 2: "Up", 8: "Seems down", 9: "Down"}
                            status_colors = {0: "gray", 1: "gray", 2: "green", 8: "orange", 9: "red"}
                            
                            st.markdown("### Current Status")
                            
                            cols = st.columns(len(monitors))
                            for idx, monitor in enumerate(monitors):
                                status = monitor.get("status", 0)
                                status_text = status_map.get(status, "Unknown")
                                
                                with cols[idx]:
                                    if status == 2:
                                        st.success(f"**{monitor.get('friendly_name', 'Monitor')}**")
                                    elif status in [8, 9]:
                                        st.error(f"**{monitor.get('friendly_name', 'Monitor')}**")
                                    else:
                                        st.warning(f"**{monitor.get('friendly_name', 'Monitor')}**")
                                    st.caption(status_text)
                            
                            st.divider()
                            
                            st.markdown("### Uptime Statistics")
                            
                            for monitor in monitors:
                                uptime_ratios = monitor.get("custom_uptime_ratio", "").split("-")
                                friendly_name = monitor.get("friendly_name", "Monitor")
                                
                                with st.expander(f"{friendly_name}", expanded=True):
                                    col1, col2, col3, col4 = st.columns(4)
                                    
                                    periods = ["24h", "7d", "30d", "90d"]
                                    for i, (col, period) in enumerate(zip([col1, col2, col3, col4], periods)):
                                        with col:
                                            if i < len(uptime_ratios):
                                                uptime = float(uptime_ratios[i])
                                                st.metric(period, f"{uptime:.2f}%")
                                            else:
                                                st.metric(period, "N/A")
                                    
                                    st.caption(f"URL: {monitor.get('url', 'N/A')}")
                                    
                                    response_times = monitor.get("response_times", [])
                                    if response_times:
                                        avg_response = sum(rt.get("value", 0) for rt in response_times) / len(response_times)
                                        st.markdown(f"**Avg Response Time:** {avg_response:.0f}ms")
                            
                            st.divider()
                            
                            st.markdown("### Recent Incidents")
                            
                            has_incidents = False
                            for monitor in monitors:
                                logs = monitor.get("logs", [])
                                down_logs = [log for log in logs if log.get("type") in [1, 2]]
                                
                                if down_logs:
                                    has_incidents = True
                                    st.markdown(f"**{monitor.get('friendly_name')}:**")
                                    for log in down_logs[:5]:
                                        log_type = "Down" if log.get("type") == 1 else "Up"
                                        timestamp = datetime.fromtimestamp(log.get("datetime", 0))
                                        duration_mins = log.get("duration", 0) // 60
                                        st.text(f"  {timestamp.strftime('%Y-%m-%d %H:%M')} - {log_type} (Duration: {duration_mins} min)")
                            
                            if not has_incidents:
                                st.success("No incidents recorded in recent history.")
                    else:
                        st.error(f"API Error: {data.get('error', {}).get('message', 'Unknown error')}")
                        
                except requests.exceptions.Timeout:
                    st.error("Request timed out. Please try again.")
                except Exception as e:
                    st.error(f"Failed to fetch monitoring data: {str(e)}")
            
            st.divider()
            
            st.markdown("### Monitoring Setup")
            st.markdown("""
            **Recommended monitors for JoveHeal:**
            - Homepage: `https://your-app.replit.app/`
            - Health Check: `https://your-app.replit.app/health`
            - Widget: `https://your-app.replit.app/widget.js`
            
            **Alert Configuration:**
            - Set up Pushover for instant push notifications
            - Configure email alerts as backup
            - Use 5-minute check intervals for production
            """)


def main():
    """Main application entry point."""
    initialize_kb_if_needed()
    
    with st.sidebar:
        st.markdown("### Navigation")
        if st.button("Chat", use_container_width=True):
            st.session_state.show_admin = False
            st.rerun()
        if st.button("Admin Panel", use_container_width=True):
            st.session_state.show_admin = True
            st.rerun()
        
        st.divider()
        
        st.markdown("### About")
        st.markdown("""
        This chatbot provides information about JoveHeal's wellness coaching programs and services.
        
        For bookings or personal inquiries, please visit [joveheal.com](https://www.joveheal.com)
        """)
        
        if st.button("New Conversation"):
            st.session_state.messages = []
            st.session_state.session_id = str(uuid.uuid4())
            st.rerun()
    
    if st.session_state.show_admin:
        render_admin_panel()
    else:
        render_chat_interface()


if __name__ == "__main__":
    main()
