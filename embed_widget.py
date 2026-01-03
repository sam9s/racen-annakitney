"""
JoveHeal Chatbot - Embeddable Widget

A lightweight version of the chatbot designed for embedding on external websites.
Provides a simpler interface focused on the chat functionality.
"""

import streamlit as st
import uuid
import os

from chatbot_engine import generate_response, get_greeting_message, check_knowledge_base_status
from knowledge_base import initialize_knowledge_base
from conversation_logger import log_conversation
from database import init_database, is_database_available

st.set_page_config(
    page_title="JoveHeal Chat",
    page_icon="🌿",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    .stApp {
        max-width: 100%;
        margin: 0 auto;
        padding: 0.5rem;
    }
    
    [data-testid="stSidebar"] {
        display: none !important;
    }
    
    header[data-testid="stHeader"] {
        display: none !important;
    }
    
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    
    .widget-header {
        text-align: center;
        padding: 0.5rem;
        background: linear-gradient(135deg, #4a7c59 0%, #2d5a3d 100%);
        color: white;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
    
    .widget-title {
        font-size: 1.2rem;
        margin: 0;
        font-weight: 600;
    }
    
    .widget-subtitle {
        font-size: 0.8rem;
        opacity: 0.9;
        margin: 0;
    }
    
    .chat-container {
        max-height: 400px;
        overflow-y: auto;
    }
    
    .powered-by {
        text-align: center;
        font-size: 0.7rem;
        color: #666;
        margin-top: 0.5rem;
    }
    
    .powered-by a {
        color: #4a7c59;
        text-decoration: none;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="widget-header">
    <p class="widget-title">JoveHeal Assistant</p>
    <p class="widget-subtitle">Ask me about our wellness programs</p>
</div>
""", unsafe_allow_html=True)

if "widget_session_id" not in st.session_state:
    st.session_state.widget_session_id = str(uuid.uuid4())

if "widget_messages" not in st.session_state:
    st.session_state.widget_messages = []

if "widget_kb_initialized" not in st.session_state:
    st.session_state.widget_kb_initialized = False

if "widget_db_initialized" not in st.session_state:
    if is_database_available():
        init_database()
        st.session_state.widget_db_initialized = True
    else:
        st.session_state.widget_db_initialized = False

if not st.session_state.widget_kb_initialized:
    status = check_knowledge_base_status()
    if not status["ready"]:
        with st.spinner("Initializing..."):
            success = initialize_knowledge_base()
            st.session_state.widget_kb_initialized = success
    else:
        st.session_state.widget_kb_initialized = True

if not st.session_state.widget_messages:
    greeting = get_greeting_message()
    st.session_state.widget_messages.append({
        "role": "assistant",
        "content": greeting
    })

st.markdown('<div class="chat-container">', unsafe_allow_html=True)

for message in st.session_state.widget_messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

st.markdown('</div>', unsafe_allow_html=True)

if prompt := st.chat_input("Type your question..."):
    st.session_state.widget_messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        with st.spinner("..."):
            result = generate_response(
                user_message=prompt,
                conversation_history=st.session_state.widget_messages[:-1]
            )
            
            response = result["response"]
            safety_triggered = result.get("safety_triggered", False)
            sources = result.get("sources", [])
            
            st.markdown(response)
            
            log_conversation(
                session_id=st.session_state.widget_session_id,
                user_question=prompt,
                bot_answer=response,
                safety_flagged=safety_triggered,
                safety_category=result.get("safety_category"),
                sources=sources,
                channel="widget"
            )
            
            st.session_state.widget_messages.append({
                "role": "assistant",
                "content": response
            })

st.markdown("""
<div class="powered-by">
    Powered by <a href="https://www.joveheal.com" target="_blank">JoveHeal</a>
</div>
""", unsafe_allow_html=True)
