"""
Webhook Server for Multi-Channel Messaging

Flask-based API server handling:
- WhatsApp webhooks (via Twilio)
- Instagram webhooks (via Meta Graph API)
- Direct API access for custom integrations
- React frontend API endpoints
"""

import os
import json
from flask import Flask, request, jsonify, Response
from flask_cors import CORS

from channel_handlers import (
    whatsapp_handler,
    instagram_handler,
    process_channel_message,
    get_channel_status
)
from chatbot_engine import generate_response, generate_response_stream, generate_conversation_summary, fix_typos_with_llm
from intent_router import refresh_router_data
from somera_engine import generate_somera_response, generate_somera_response_stream
from conversation_logger import log_feedback, log_conversation, ensure_session_exists
from database import get_or_create_user, get_user_conversation_history, get_conversation_summary, upsert_conversation_summary, init_database, is_database_available, get_db_session, ChatSession, Conversation
from knowledge_base import initialize_knowledge_base, get_knowledge_base_stats
from rate_limiter import rate_limiter, get_client_ip

app = Flask(__name__)
CORS(app)

# Initialize database tables on startup (ensures tables exist in production)
try:
    if init_database():
        print("[Startup] Database tables initialized successfully")
    else:
        print("[Startup] Warning: Database not available")
except Exception as e:
    print(f"[Startup] Warning: Database initialization error: {e}")

KNOWLEDGE_BASE_READY = False

def init_knowledge_base_on_startup():
    """Initialize knowledge base on startup if empty (for autoscale cold starts).
    
    FAIL FAST: If knowledge base cannot be initialized, exit with error.
    This prevents serving degraded traffic with missing vectors.
    """
    global KNOWLEDGE_BASE_READY
    try:
        stats = get_knowledge_base_stats()
        if stats["total_chunks"] == 0:
            print("[Startup] Knowledge base is empty, rebuilding from website...")
            initialize_knowledge_base(force_refresh=False, enable_web_scrape=True)
            stats = get_knowledge_base_stats()
            if stats["total_chunks"] == 0:
                print("[CRITICAL] Knowledge base rebuild failed - no chunks available!")
                print("[CRITICAL] Exiting to prevent serving degraded traffic.")
                import sys
                sys.exit(1)
            print(f"[Startup] Knowledge base rebuilt with {stats['total_chunks']} chunks")
        else:
            print(f"[Startup] Knowledge base ready with {stats['total_chunks']} chunks")
        KNOWLEDGE_BASE_READY = True
    except Exception as e:
        print(f"[CRITICAL] Failed to initialize knowledge base: {e}")
        print("[CRITICAL] Exiting to prevent serving degraded traffic.")
        import sys
        sys.exit(1)

init_knowledge_base_on_startup()

# Initialize IntentRouter with current event titles and program names
try:
    refresh_router_data()
    print("[Startup] IntentRouter initialized with event/program data")
except Exception as e:
    print(f"[Startup] Warning: IntentRouter initialization failed: {e}")

conversation_histories = {}


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint.
    
    Returns unhealthy if knowledge base is not ready.
    """
    if not KNOWLEDGE_BASE_READY:
        return jsonify({
            "status": "unhealthy",
            "service": "Anna Kitney API Server",
            "reason": "Knowledge base not initialized"
        }), 503
    return jsonify({"status": "healthy", "service": "Anna Kitney API Server"})


@app.route("/api/admin/db-health", methods=["GET"])
def db_health_check():
    """Database health check endpoint with table stats."""
    if not validate_internal_api_key():
        return jsonify({"error": "Unauthorized"}), 401
    
    result = {
        "database_available": is_database_available(),
        "database_url_set": bool(os.environ.get("DATABASE_URL")),
        "tables": {}
    }
    
    if is_database_available():
        try:
            from sqlalchemy import func
            with get_db_session() as db:
                if db:
                    result["tables"]["chat_sessions"] = db.query(func.count(ChatSession.id)).scalar() or 0
                    result["tables"]["conversations"] = db.query(func.count(Conversation.id)).scalar() or 0
                    
                    latest = db.query(Conversation).order_by(Conversation.timestamp.desc()).first()
                    if latest:
                        result["latest_conversation"] = latest.timestamp.isoformat() if latest.timestamp else None
                    else:
                        result["latest_conversation"] = None
                    
                    result["connection_status"] = "connected"
                else:
                    result["connection_status"] = "session_failed"
        except Exception as e:
            result["connection_status"] = "error"
            result["error"] = str(e)
    else:
        result["connection_status"] = "unavailable"
    
    return jsonify(result)


@app.route("/api/channels/status", methods=["GET"])
def channel_status():
    """Get configuration status of all messaging channels."""
    return jsonify(get_channel_status())


@app.route("/api/admin/rate-limiter/stats", methods=["GET"])
def rate_limiter_stats():
    """Get rate limiter statistics for monitoring.
    
    Protected endpoint - requires internal API key.
    """
    if not validate_internal_api_key():
        return jsonify({"error": "Unauthorized"}), 401
    
    return jsonify(rate_limiter.get_stats())


def get_canonical_webhook_url(endpoint: str) -> str:
    """Get the canonical webhook URL for signature validation.
    
    Priority:
    1. WEBHOOK_BASE_URL - Trusted, explicitly configured base URL (most secure)
    2. REPLIT_DEV_DOMAIN - Replit's trusted domain environment variable
    3. Fallback error - Requires explicit configuration for security
    """
    webhook_base = os.environ.get("WEBHOOK_BASE_URL")
    if webhook_base:
        return f"{webhook_base.rstrip('/')}/{endpoint}"
    
    replit_domain = os.environ.get("REPLIT_DEV_DOMAIN")
    if replit_domain:
        return f"https://{replit_domain}/{endpoint}"
    
    return None


@app.route("/webhook/whatsapp", methods=["POST"])
def whatsapp_webhook():
    """Handle incoming WhatsApp messages via Twilio."""
    if not whatsapp_handler.is_configured():
        return "WhatsApp not configured", 503
    
    signature = request.headers.get("X-Twilio-Signature", "")
    
    if not signature:
        print(f"WhatsApp webhook: Rejected request - missing X-Twilio-Signature header. Remote: {request.remote_addr}")
        return "Missing signature", 403
    
    canonical_url = get_canonical_webhook_url("webhook/whatsapp")
    if not canonical_url:
        print("WhatsApp webhook: WEBHOOK_BASE_URL or REPLIT_DEV_DOMAIN must be set for signature validation")
        return "Server configuration error", 500
    
    if not whatsapp_handler.validate_request(signature, canonical_url, request.form.to_dict()):
        print(f"WhatsApp webhook: Rejected request - invalid signature. URL: {canonical_url}, Remote: {request.remote_addr}")
        return "Invalid signature", 403
    
    twiml_response = whatsapp_handler.handle_webhook(request.form.to_dict())
    
    return twiml_response, 200, {"Content-Type": "application/xml"}


@app.route("/webhook/instagram", methods=["GET"])
def instagram_verify():
    """Handle Instagram webhook verification."""
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    
    success, response = instagram_handler.verify_webhook(mode, token, challenge)
    
    if success:
        return response, 200
    return response, 403


@app.route("/webhook/instagram", methods=["POST"])
def instagram_webhook():
    """Handle incoming Instagram messages."""
    if not instagram_handler.is_configured():
        return jsonify({"error": "Instagram not configured"}), 503
    
    data = request.get_json()
    
    result = instagram_handler.handle_webhook(data)
    
    return jsonify(result), 200


def validate_internal_api_key():
    """Validate the internal API key from trusted Next.js server."""
    expected_key = os.environ.get("INTERNAL_API_KEY")
    if not expected_key:
        return False
    provided_key = request.headers.get("X-Internal-Api-Key", "")
    return provided_key == expected_key


@app.route("/api/chat", methods=["POST"])
def api_chat():
    """Direct API endpoint for chat integration - used by React frontend."""
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    message = data.get("message")
    session_id = data.get("session_id", "anonymous")
    conversation_history = data.get("conversation_history", [])
    
    is_trusted_request = validate_internal_api_key()
    verified_user = data.get("verified_user") if is_trusted_request else None
    
    if not message:
        return jsonify({"error": "Message is required"}), 400
    
    original_message = message
    message = fix_typos_with_llm(message)
    
    user_id = None
    is_returning_user = False
    user_name = None
    
    if verified_user and session_id.startswith("user_"):
        email = verified_user.get("email")
        name = verified_user.get("name")
        image = verified_user.get("image")
        
        if email:
            user_data, created = get_or_create_user(
                channel="google",
                external_id=email,
                email=email,
                display_name=name,
                profile_image=image
            )
            if user_data:
                user_id = user_data['id']
                user_name = name.split()[0] if name else None
                is_returning_user = not created and session_id not in conversation_histories
    
    ensure_session_exists(session_id, channel="web", user_id=user_id)
    
    last_topic_summary = None
    stored_summary = None
    
    if session_id not in conversation_histories:
        conversation_histories[session_id] = []
        
        if is_returning_user and user_id:
            stored_summary = get_conversation_summary(user_id)
            
            past_history = get_user_conversation_history(user_id, limit=50)
            if past_history:
                for conv in past_history:
                    conversation_histories[session_id].append({"role": "user", "content": conv['question']})
                    conversation_histories[session_id].append({"role": "assistant", "content": conv['answer']})
            
            if stored_summary:
                summary_parts = []
                if stored_summary.get('emotional_themes'):
                    summary_parts.append(f"emotional issues: {stored_summary['emotional_themes']}")
                if stored_summary.get('recommended_programs'):
                    summary_parts.append(f"programs suggested: {stored_summary['recommended_programs']}")
                if stored_summary.get('last_topics'):
                    summary_parts.append(f"topic: {stored_summary['last_topics']}")
                last_topic_summary = " | ".join(summary_parts) if summary_parts else None
                
                if last_topic_summary:
                    conversation_histories[session_id] = conversation_histories[session_id][-4:]
    
    if conversation_history and not conversation_histories[session_id]:
        conversation_histories[session_id] = conversation_history
    
    result = generate_response(
        message, 
        conversation_histories[session_id],
        user_name=user_name,
        is_returning_user=is_returning_user,
        last_topic_summary=last_topic_summary
    )
    
    response_text = result.get("response", "")
    
    logged_entry = log_conversation(
        session_id=session_id,
        user_question=message,
        bot_answer=response_text,
        safety_flagged=result.get("safety_triggered", False),
        safety_category=result.get("safety_category"),
        sources=result.get("sources", []),
        channel="web"
    )
    
    conversation_id = logged_entry.get("conversation_id") if logged_entry else None
    
    conversation_histories[session_id].append({"role": "user", "content": message})
    conversation_histories[session_id].append({"role": "assistant", "content": response_text})
    
    if len(conversation_histories[session_id]) > 100:
        conversation_histories[session_id] = conversation_histories[session_id][-100:]
    
    if user_id and len(conversation_histories[session_id]) >= 4:
        try:
            summary = generate_conversation_summary(conversation_histories[session_id])
            if summary:
                upsert_conversation_summary(
                    user_id=user_id,
                    emotional_themes=summary.get('emotional_themes'),
                    recommended_programs=summary.get('recommended_programs'),
                    last_topics=summary.get('last_topics'),
                    conversation_status=summary.get('conversation_status')
                )
        except Exception as e:
            print(f"Error updating conversation summary: {e}")
    
    return jsonify({
        "response": result.get("response", "I apologize, but I encountered an issue. Please try again."),
        "sources": result.get("sources", []),
        "safety_triggered": result.get("safety_triggered", False),
        "session_id": session_id,
        "user_id": user_id,
        "is_returning_user": is_returning_user,
        "intent": result.get("intent", "unknown"),
        "conversation_id": conversation_id
    })


@app.route("/api/chat/stream", methods=["POST"])
def api_chat_stream():
    """Streaming chat endpoint using Server-Sent Events."""
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    message = data.get("message")
    session_id = data.get("session_id", "anonymous")
    conversation_history = data.get("conversation_history", [])
    
    client_ip = get_client_ip(request)
    captcha_answer = data.get("captcha_answer")
    
    if captcha_answer:
        if rate_limiter.verify_captcha(session_id, captcha_answer):
            pass
        else:
            return jsonify({
                "error": "Incorrect answer. Please try again.",
                "captcha_failed": True
            }), 400
    
    allowed, reason, captcha = rate_limiter.check_rate_limit(client_ip, session_id)
    if not allowed:
        if captcha:
            return jsonify({
                "error": reason,
                "captcha_required": True,
                "captcha": captcha
            }), 429
        return jsonify({"error": reason, "rate_limited": True}), 429
    
    rate_limiter.log_request(client_ip, session_id, "/api/chat/stream", message[:50] if message else "")
    rate_limiter.record_request(client_ip, session_id)
    
    is_trusted_request = validate_internal_api_key()
    verified_user = data.get("verified_user") if is_trusted_request else None
    
    if not message:
        return jsonify({"error": "Message is required"}), 400
    
    original_message = message
    message = fix_typos_with_llm(message)
    
    user_id = None
    is_returning_user = False
    user_name = None
    
    if verified_user and session_id.startswith("user_"):
        email = verified_user.get("email")
        name = verified_user.get("name")
        image = verified_user.get("image")
        
        if email:
            user_data, created = get_or_create_user(
                channel="google",
                external_id=email,
                email=email,
                display_name=name,
                profile_image=image
            )
            if user_data:
                user_id = user_data['id']
                user_name = name.split()[0] if name else None
                is_returning_user = not created and session_id not in conversation_histories
    
    ensure_session_exists(session_id, channel="web", user_id=user_id)
    
    last_topic_summary = None
    stored_summary = None
    
    if session_id not in conversation_histories:
        conversation_histories[session_id] = []
        
        if is_returning_user and user_id:
            stored_summary = get_conversation_summary(user_id)
            
            past_history = get_user_conversation_history(user_id, limit=50)
            if past_history:
                for conv in past_history:
                    conversation_histories[session_id].append({"role": "user", "content": conv['question']})
                    conversation_histories[session_id].append({"role": "assistant", "content": conv['answer']})
            
            if stored_summary:
                summary_parts = []
                if stored_summary.get('emotional_themes'):
                    summary_parts.append(f"emotional issues: {stored_summary['emotional_themes']}")
                if stored_summary.get('recommended_programs'):
                    summary_parts.append(f"programs suggested: {stored_summary['recommended_programs']}")
                if stored_summary.get('last_topics'):
                    summary_parts.append(f"topic: {stored_summary['last_topics']}")
                last_topic_summary = " | ".join(summary_parts) if summary_parts else None
                
                if last_topic_summary:
                    conversation_histories[session_id] = conversation_histories[session_id][-4:]
    
    if conversation_history and not conversation_histories[session_id]:
        conversation_histories[session_id] = conversation_history
    
    def generate():
        full_response = ""
        sources = []
        safety_triggered = False
        
        for chunk in generate_response_stream(
            message, 
            conversation_histories[session_id],
            user_name=user_name,
            is_returning_user=is_returning_user,
            last_topic_summary=last_topic_summary
        ):
            if chunk["type"] == "content":
                full_response += chunk["content"]
                yield f"data: {json.dumps(chunk)}\n\n"
            elif chunk["type"] == "done":
                sources = chunk.get("sources", [])
                safety_triggered = chunk.get("safety_triggered", False)
                full_response = chunk.get("full_response", full_response)
                yield f"data: {json.dumps(chunk)}\n\n"
            elif chunk["type"] == "error":
                yield f"data: {json.dumps(chunk)}\n\n"
                return
        
        log_conversation(
            session_id=session_id,
            user_question=message,
            bot_answer=full_response,
            safety_flagged=safety_triggered,
            sources=sources,
            channel="web"
        )
        
        conversation_histories[session_id].append({"role": "user", "content": message})
        conversation_histories[session_id].append({"role": "assistant", "content": full_response})
        
        if len(conversation_histories[session_id]) > 100:
            conversation_histories[session_id] = conversation_histories[session_id][-100:]
        
        if user_id and len(conversation_histories[session_id]) >= 4:
            try:
                summary = generate_conversation_summary(conversation_histories[session_id])
                if summary:
                    upsert_conversation_summary(
                        user_id=user_id,
                        emotional_themes=summary.get('emotional_themes'),
                        recommended_programs=summary.get('recommended_programs'),
                        last_topics=summary.get('last_topics'),
                        conversation_status=summary.get('conversation_status')
                    )
            except Exception as e:
                print(f"Error updating conversation summary: {e}")
    
    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no'
        }
    )


# ============================================================================
# ANNA ENDPOINTS - Empathetic Coaching Assistant
# ============================================================================

somera_conversation_histories = {}

@app.route("/api/somera", methods=["POST"])
def api_somera():
    """ANNA coaching endpoint - empathetic responses using Anna's coaching style."""
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    message = data.get("message")
    session_id = data.get("session_id", "anonymous")
    user_name = data.get("user_name")
    
    if not message:
        return jsonify({"error": "Message is required"}), 400
    
    message = fix_typos_with_llm(message)
    
    if session_id not in somera_conversation_histories:
        somera_conversation_histories[session_id] = []
    
    result = generate_somera_response(
        message, 
        somera_conversation_histories[session_id],
        user_name=user_name
    )
    
    answer = result.get("response", "I'm here to support you. Could you tell me more?")
    sources = result.get("sources", [])
    
    somera_conversation_histories[session_id].append({"role": "user", "content": message})
    somera_conversation_histories[session_id].append({"role": "assistant", "content": answer})
    
    if len(somera_conversation_histories[session_id]) > 50:
        somera_conversation_histories[session_id] = somera_conversation_histories[session_id][-50:]
    
    return jsonify({
        "response": answer,
        "sources": sources,
        "session_id": session_id
    })


@app.route("/api/somera/stream", methods=["POST"])
def api_somera_stream():
    """Streaming ANNA coaching endpoint using Server-Sent Events."""
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    message = data.get("message")
    session_id = data.get("session_id", "anonymous")
    user_name = data.get("user_name")
    
    client_ip = get_client_ip(request)
    captcha_answer = data.get("captcha_answer")
    
    if captcha_answer:
        if rate_limiter.verify_captcha(session_id, captcha_answer):
            pass
        else:
            return jsonify({
                "error": "Incorrect answer. Please try again.",
                "captcha_failed": True
            }), 400
    
    allowed, reason, captcha = rate_limiter.check_rate_limit(client_ip, session_id)
    if not allowed:
        if captcha:
            return jsonify({
                "error": reason,
                "captcha_required": True,
                "captcha": captcha
            }), 429
        return jsonify({"error": reason, "rate_limited": True}), 429
    
    rate_limiter.log_request(client_ip, session_id, "/api/somera/stream", message[:50] if message else "")
    rate_limiter.record_request(client_ip, session_id)
    
    if not message:
        return jsonify({"error": "Message is required"}), 400
    
    message = fix_typos_with_llm(message)
    
    if session_id not in somera_conversation_histories:
        somera_conversation_histories[session_id] = []
    
    def generate():
        full_response = ""
        sources = []
        
        for chunk in generate_somera_response_stream(
            message, 
            somera_conversation_histories[session_id],
            user_name=user_name
        ):
            if chunk["type"] == "content":
                full_response += chunk["content"]
                yield f"data: {json.dumps(chunk)}\n\n"
            elif chunk["type"] == "done":
                sources = chunk.get("sources", [])
                full_response = chunk.get("full_response", full_response)
                yield f"data: {json.dumps(chunk)}\n\n"
            elif chunk["type"] == "error":
                yield f"data: {json.dumps(chunk)}\n\n"
        
        somera_conversation_histories[session_id].append({"role": "user", "content": message})
        somera_conversation_histories[session_id].append({"role": "assistant", "content": full_response})
        
        if len(somera_conversation_histories[session_id]) > 50:
            somera_conversation_histories[session_id] = somera_conversation_histories[session_id][-50:]
    
    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no'
        }
    )


@app.route("/api/chat/manychat", methods=["POST"])
def api_chat_manychat():
    """ManyChat Dynamic Content endpoint for Instagram/Facebook integration."""
    data = request.get_json()
    
    if not data:
        return jsonify({
            "version": "v2",
            "content": {
                "messages": [{"type": "text", "text": "Sorry, I couldn't process your request."}],
                "actions": [],
                "quick_replies": []
            }
        })
    
    message = data.get("message", "").strip()
    user_id = data.get("user_id", "anonymous")
    first_name = data.get("first_name", "")
    
    if not message:
        return jsonify({
            "version": "v2",
            "content": {
                "messages": [{"type": "text", "text": "Hi! I'm Anna, your guide for Anna Kitney's wellness programs. How can I help you today?"}],
                "actions": [],
                "quick_replies": []
            }
        })
    
    session_id = f"manychat_{user_id}"
    
    original_message = message
    message = fix_typos_with_llm(message)
    
    if session_id not in conversation_histories:
        conversation_histories[session_id] = []
    
    ensure_session_exists(session_id, channel="instagram", user_id=None)
    
    try:
        result = generate_response(
            message, 
            conversation_histories[session_id],
            user_name=first_name if first_name else None,
            is_returning_user=len(conversation_histories[session_id]) > 0,
            last_topic_summary=None
        )
        
        answer = result.get("response", "I'm sorry, I couldn't generate a response.")
        sources = result.get("sources", [])
        safety_triggered = result.get("safety_triggered", False)
        
        conversation_histories[session_id].append({"role": "user", "content": message})
        conversation_histories[session_id].append({"role": "assistant", "content": answer})
        
        if len(conversation_histories[session_id]) > 20:
            conversation_histories[session_id] = conversation_histories[session_id][-20:]
        
        log_conversation(
            session_id=session_id,
            user_question=original_message,
            bot_answer=answer,
            sources=sources,
            safety_flagged=safety_triggered
        )
        
        return jsonify({
            "version": "v2",
            "content": {
                "messages": [{"type": "text", "text": answer}],
                "actions": [],
                "quick_replies": []
            }
        })
        
    except Exception as e:
        print(f"ManyChat endpoint error: {e}")
        return jsonify({
            "version": "v2",
            "content": {
                "messages": [{"type": "text", "text": "I'm having trouble right now. Please try again in a moment."}],
                "actions": [],
                "quick_replies": []
            }
        })


@app.route("/api/chat/reset", methods=["POST"])
def api_chat_reset():
    """Reset conversation for a session."""
    data = request.get_json()
    session_id = data.get("session_id", "anonymous")
    
    if session_id in conversation_histories:
        del conversation_histories[session_id]
    
    return jsonify({
        "status": "success",
        "message": "Conversation reset"
    })


@app.route("/api/feedback", methods=["POST"])
def api_feedback():
    """Submit feedback for a response."""
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    session_id = data.get("session_id", "anonymous")
    message_id = data.get("message_id", "")
    feedback = data.get("feedback", "")
    comment = data.get("comment", "")
    
    if feedback not in ["up", "down"]:
        return jsonify({"error": "Invalid feedback value"}), 400
    
    is_positive = feedback == "up"
    
    try:
        log_feedback(
            session_id=session_id,
            is_positive=is_positive,
            comment=comment if comment else None
        )
        
        return jsonify({
            "status": "success",
            "message": "Feedback recorded"
        })
    except Exception as e:
        print(f"Error logging feedback: {e}")
        return jsonify({
            "status": "error",
            "message": "Failed to record feedback"
        }), 500


# =============================================================================
# Admin Dashboard API Endpoints
# =============================================================================

from conversation_logger import (
    get_conversation_stats, get_analytics_by_date, get_feedback_summary,
    get_recent_logs, get_session_history
)
from database import ChatSession, Conversation, UserAccount, get_db_session, is_database_available
from sqlalchemy import func, desc

@app.route("/api/admin/stats", methods=["GET"])
def admin_stats():
    """Get dashboard statistics."""
    if not validate_internal_api_key():
        return jsonify({"error": "Unauthorized"}), 401
    
    range_param = request.args.get("range", "7d")
    
    days = 7
    if range_param == "24h":
        days = 1
    elif range_param == "30d":
        days = 30
    
    try:
        stats = get_conversation_stats()
        daily_data = get_analytics_by_date(days)
        feedback = get_feedback_summary()
        
        total_feedback = feedback.get("positive", 0) + feedback.get("negative", 0)
        satisfaction = 0
        if total_feedback > 0:
            satisfaction = round((feedback.get("positive", 0) / total_feedback) * 100)
        
        channel_dist = []
        if is_database_available():
            with get_db_session() as db:
                if db:
                    channels = db.query(
                        ChatSession.channel,
                        func.count(ChatSession.id).label('count')
                    ).group_by(ChatSession.channel).all()
                    channel_dist = [{"channel": c.channel or "web", "count": c.count} for c in channels]
        
        conversations_by_day = []
        for d in daily_data:
            date_str = d.get("date", "")
            if date_str:
                from datetime import datetime
                try:
                    dt = datetime.strptime(date_str, "%Y-%m-%d")
                    formatted = dt.strftime("%b %d")
                except:
                    formatted = date_str
                conversations_by_day.append({
                    "date": formatted,
                    "count": d.get("conversations", 0)
                })
        
        top_queries = []
        
        return jsonify({
            "totalConversations": stats.get("total_conversations", 0),
            "totalSessions": stats.get("unique_sessions", 0),
            "avgResponseTime": round((stats.get("avg_response_time_ms") or 0) / 1000, 1),
            "positiveRating": satisfaction,
            "conversationsByDay": conversations_by_day,
            "channelDistribution": channel_dist if channel_dist else [{"channel": "Widget", "count": stats.get("total_conversations", 0)}],
            "topQueries": top_queries
        })
    except Exception as e:
        print(f"Admin stats error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/admin/conversations", methods=["GET"])
def admin_conversations():
    """Get list of chat sessions for the conversation viewer."""
    if not validate_internal_api_key():
        return jsonify({"error": "Unauthorized"}), 401
    
    range_param = request.args.get("range", "7d")
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 50))
    
    days = 7
    if range_param == "24h":
        days = 1
    elif range_param == "30d":
        days = 30
    
    if not is_database_available():
        return jsonify({"sessions": [], "total": 0})
    
    try:
        from datetime import datetime, timedelta
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        with get_db_session() as db:
            if db is None:
                return jsonify({"sessions": [], "total": 0})
            
            total = db.query(func.count(ChatSession.id)).filter(
                ChatSession.created_at >= cutoff
            ).scalar() or 0
            
            sessions = db.query(ChatSession).filter(
                ChatSession.created_at >= cutoff
            ).order_by(desc(ChatSession.last_activity)).offset((page - 1) * limit).limit(limit).all()
            
            result = []
            for s in sessions:
                msg_count = db.query(func.count(Conversation.id)).filter(
                    Conversation.session_id == s.session_id
                ).scalar() or 0
                
                first_msg = db.query(Conversation.user_question).filter(
                    Conversation.session_id == s.session_id
                ).order_by(Conversation.timestamp).first()
                
                user_name = "Anonymous"
                user_email = None
                if s.user_id:
                    user = db.query(UserAccount).filter(UserAccount.id == s.user_id).first()
                    if user:
                        user_name = user.display_name or user.email or "User"
                        user_email = user.email
                
                result.append({
                    "sessionId": s.session_id,
                    "userName": user_name,
                    "userEmail": user_email,
                    "channel": s.channel or "web",
                    "messageCount": msg_count,
                    "firstMessage": first_msg[0][:100] + "..." if first_msg and len(first_msg[0]) > 100 else (first_msg[0] if first_msg else ""),
                    "createdAt": s.created_at.isoformat() if s.created_at else None,
                    "lastActivity": s.last_activity.isoformat() if s.last_activity else None
                })
            
            return jsonify({
                "sessions": result,
                "total": total,
                "page": page,
                "limit": limit,
                "totalPages": (total + limit - 1) // limit
            })
    except Exception as e:
        print(f"Admin conversations error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/admin/conversations/<session_id>", methods=["GET"])
def admin_conversation_detail(session_id):
    """Get full conversation history for a specific session."""
    if not validate_internal_api_key():
        return jsonify({"error": "Unauthorized"}), 401
    
    if not is_database_available():
        return jsonify({"messages": [], "session": None})
    
    try:
        with get_db_session() as db:
            if db is None:
                return jsonify({"messages": [], "session": None})
            
            session = db.query(ChatSession).filter(
                ChatSession.session_id == session_id
            ).first()
            
            if not session:
                return jsonify({"error": "Session not found"}), 404
            
            user_name = "Anonymous"
            user_email = None
            if session.user_id:
                user = db.query(UserAccount).filter(UserAccount.id == session.user_id).first()
                if user:
                    user_name = user.display_name or user.email or "User"
                    user_email = user.email
            
            messages = db.query(Conversation).filter(
                Conversation.session_id == session_id
            ).order_by(Conversation.timestamp).all()
            
            message_list = []
            for m in messages:
                message_list.append({
                    "id": m.id,
                    "userQuestion": m.user_question,
                    "botAnswer": m.bot_answer,
                    "timestamp": m.timestamp.isoformat() if m.timestamp else None,
                    "safetyFlagged": m.safety_flagged,
                    "responseTimeMs": m.response_time_ms
                })
            
            return jsonify({
                "session": {
                    "sessionId": session.session_id,
                    "userName": user_name,
                    "userEmail": user_email,
                    "channel": session.channel or "web",
                    "createdAt": session.created_at.isoformat() if session.created_at else None,
                    "lastActivity": session.last_activity.isoformat() if session.last_activity else None
                },
                "messages": message_list
            })
    except Exception as e:
        print(f"Admin conversation detail error: {e}")
        return jsonify({"error": str(e)}), 500


# ═══════════════════════════════════════════════════════════════════════════
# CONVERSATION FLAGGING & EXPORT FOR TEST GENERATION
# ═══════════════════════════════════════════════════════════════════════════

# Rate limiting for flag endpoint (prevent abuse)
_flag_rate_limit = {}
FLAG_RATE_LIMIT_WINDOW = 60  # seconds
FLAG_RATE_LIMIT_MAX = 10  # max flags per session per minute

@app.route("/api/conversation/flag", methods=["POST"])
def flag_conversation():
    """Flag a specific bot response for review.
    
    Used by end users to report issues with bot responses.
    Rate-limited to prevent abuse.
    """
    data = request.get_json()
    session_id = data.get("session_id")
    conversation_id = data.get("conversation_id")
    reason = data.get("reason", "other")
    notes = data.get("notes", "")
    
    if not session_id or not conversation_id:
        return jsonify({"error": "Missing session_id or conversation_id"}), 400
    
    # Rate limiting
    import time
    current_time = time.time()
    if session_id in _flag_rate_limit:
        timestamps = [t for t in _flag_rate_limit[session_id] if current_time - t < FLAG_RATE_LIMIT_WINDOW]
        if len(timestamps) >= FLAG_RATE_LIMIT_MAX:
            return jsonify({"error": "Rate limit exceeded. Please try again later."}), 429
        _flag_rate_limit[session_id] = timestamps + [current_time]
    else:
        _flag_rate_limit[session_id] = [current_time]
    
    if not is_database_available():
        return jsonify({"error": "Database unavailable"}), 503
    
    try:
        from database import ConversationFlag
        with get_db_session() as db:
            if db is None:
                return jsonify({"error": "Database session unavailable"}), 503
            
            # Verify conversation exists
            conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
            if not conv:
                return jsonify({"error": "Conversation not found"}), 404
            
            # Create flag
            flag = ConversationFlag(
                conversation_id=conversation_id,
                session_id=session_id,
                flag_reason=reason,
                flag_notes=notes
            )
            db.add(flag)
            db.commit()
            
            print(f"[Flag] Conversation {conversation_id} flagged: {reason}", flush=True)
            return jsonify({"success": True, "flag_id": flag.id})
    except Exception as e:
        print(f"Flag conversation error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/admin/flags", methods=["GET"])
def admin_get_flags():
    """Get all flagged conversations for review."""
    if not validate_internal_api_key():
        return jsonify({"error": "Unauthorized"}), 401
    
    if not is_database_available():
        return jsonify({"flags": [], "total": 0})
    
    try:
        from database import ConversationFlag
        reviewed = request.args.get("reviewed", "all")
        
        with get_db_session() as db:
            if db is None:
                return jsonify({"flags": [], "total": 0})
            
            query = db.query(ConversationFlag)
            if reviewed == "pending":
                query = query.filter(ConversationFlag.reviewed == False)
            elif reviewed == "reviewed":
                query = query.filter(ConversationFlag.reviewed == True)
            
            flags = query.order_by(desc(ConversationFlag.created_at)).limit(100).all()
            
            result = []
            for f in flags:
                conv = db.query(Conversation).filter(Conversation.id == f.conversation_id).first()
                result.append({
                    "id": f.id,
                    "conversationId": f.conversation_id,
                    "sessionId": f.session_id,
                    "reason": f.flag_reason,
                    "notes": f.flag_notes,
                    "createdAt": f.created_at.isoformat() if f.created_at else None,
                    "reviewed": f.reviewed,
                    "issueCategory": f.issue_category,
                    "userQuestion": conv.user_question if conv else None,
                    "botAnswer": conv.bot_answer if conv else None
                })
            
            return jsonify({"flags": result, "total": len(result)})
    except Exception as e:
        print(f"Admin get flags error: {e}")
        return jsonify({"error": str(e)}), 500


def _anonymize_pii(text: str) -> str:
    """Anonymize PII in text for export."""
    import re
    import hashlib
    
    # Email addresses -> hashed placeholder
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    emails = re.findall(email_pattern, text)
    for email in emails:
        hash_val = hashlib.sha256(email.encode()).hexdigest()[:8]
        text = text.replace(email, f"{{{{email_{hash_val}}}}}")
    
    # Phone numbers -> placeholder
    phone_pattern = r'(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}'
    text = re.sub(phone_pattern, "{{phone}}", text)
    
    # Names after common patterns (My name is X, I'm X, I am X)
    name_pattern = r"(?:my name is|i'm|i am|call me)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)"
    for match in re.finditer(name_pattern, text, re.IGNORECASE):
        name = match.group(1)
        text = text.replace(name, "{{user}}")
    
    return text


def _anonymize_session_id(session_id: str) -> str:
    """Hash session ID for export."""
    import hashlib
    return f"session_{hashlib.sha256(session_id.encode()).hexdigest()[:12]}"


@app.route("/api/admin/conversations/export", methods=["GET"])
def admin_export_conversations():
    """Export flagged conversations with PII scrubbing for test generation.
    
    Returns anonymized conversation data suitable for creating regression tests.
    """
    if not validate_internal_api_key():
        return jsonify({"error": "Unauthorized"}), 401
    
    if not is_database_available():
        return jsonify({"error": "Database unavailable"}), 503
    
    try:
        from database import ConversationFlag
        from datetime import datetime
        
        only_flagged = request.args.get("flagged", "true").lower() == "true"
        limit = min(int(request.args.get("limit", 100)), 500)  # Max 500 per export
        
        with get_db_session() as db:
            if db is None:
                return jsonify({"error": "Database session unavailable"}), 503
            
            if only_flagged:
                # Get flagged conversations
                flags = db.query(ConversationFlag).filter(
                    ConversationFlag.exported == False
                ).order_by(desc(ConversationFlag.created_at)).limit(limit).all()
                
                conversation_ids = [f.conversation_id for f in flags]
                conversations = db.query(Conversation).filter(
                    Conversation.id.in_(conversation_ids)
                ).all()
            else:
                # Get recent conversations
                from datetime import timedelta
                cutoff = datetime.utcnow() - timedelta(days=7)
                conversations = db.query(Conversation).filter(
                    Conversation.timestamp >= cutoff
                ).order_by(desc(Conversation.timestamp)).limit(limit).all()
            
            # Build export data with PII scrubbing
            export_data = []
            session_contexts = {}
            
            for conv in conversations:
                anon_session = _anonymize_session_id(conv.session_id)
                
                # Get full conversation context for this session
                if conv.session_id not in session_contexts:
                    full_history = db.query(Conversation).filter(
                        Conversation.session_id == conv.session_id
                    ).order_by(Conversation.timestamp).all()
                    session_contexts[conv.session_id] = full_history
                
                # Find flag info if exists
                flag_info = None
                if only_flagged:
                    flag = db.query(ConversationFlag).filter(
                        ConversationFlag.conversation_id == conv.id
                    ).first()
                    if flag:
                        flag_info = {
                            "reason": flag.flag_reason,
                            "notes": _anonymize_pii(flag.flag_notes or ""),
                            "category": flag.issue_category
                        }
                        # Mark as exported
                        flag.exported = True
                
                # Build conversation history up to this point
                history = []
                for h in session_contexts[conv.session_id]:
                    if h.timestamp <= conv.timestamp:
                        history.append({
                            "role": "user",
                            "content": _anonymize_pii(h.user_question)
                        })
                        history.append({
                            "role": "assistant",
                            "content": _anonymize_pii(h.bot_answer)
                        })
                    if h.id == conv.id:
                        break
                
                export_data.append({
                    "id": conv.id,
                    "anonymizedSessionId": anon_session,
                    "timestamp": conv.timestamp.isoformat() if conv.timestamp else None,
                    "userQuestion": _anonymize_pii(conv.user_question),
                    "botAnswer": _anonymize_pii(conv.bot_answer),
                    "safetyFlagged": conv.safety_flagged,
                    "conversationHistory": history,
                    "flagInfo": flag_info
                })
            
            if only_flagged:
                db.commit()  # Save exported=True flags
            
            # Log export
            print(f"[Export] Exported {len(export_data)} conversations", flush=True)
            
            return jsonify({
                "exportedAt": datetime.utcnow().isoformat(),
                "count": len(export_data),
                "conversations": export_data
            })
    except Exception as e:
        print(f"Admin export error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/transcribe", methods=["POST"])
def transcribe_audio():
    """Transcribe audio/video file using OpenAI Whisper API."""
    import tempfile
    import subprocess
    import math
    from openai import OpenAI
    
    if not validate_internal_api_key():
        return jsonify({"error": "Unauthorized"}), 401
    
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    output_name = request.form.get('outputName', 'transcript')
    
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return jsonify({"error": "OpenAI API key not configured"}), 500
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = os.path.join(temp_dir, file.filename)
            file.save(input_path)
            
            video_extensions = [".mp4", ".mov", ".avi", ".mkv", ".webm"]
            file_ext = os.path.splitext(file.filename)[1].lower()
            
            audio_path = os.path.join(temp_dir, "audio.mp3")
            cmd = [
                "ffmpeg", "-i", input_path,
                "-vn", "-acodec", "libmp3lame", "-ab", "64k", "-ar", "16000",
                "-y", audio_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            if result.returncode != 0:
                print(f"FFmpeg error: {result.stderr}")
                return jsonify({"error": f"Failed to extract audio: {result.stderr[:200]}"}), 500
            
            if not os.path.exists(audio_path):
                return jsonify({"error": "Failed to extract audio - output file not created"}), 500
            
            def get_audio_duration(path):
                try:
                    cmd = [
                        "ffprobe", "-v", "error",
                        "-show_entries", "format=duration",
                        "-of", "default=noprint_wrappers=1:nokey=1",
                        path
                    ]
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                    if result.returncode != 0:
                        print(f"FFprobe error: {result.stderr}")
                        return 0
                    return float(result.stdout.strip())
                except Exception as e:
                    print(f"Duration detection error: {e}")
                    return 0
            
            duration = get_audio_duration(audio_path)
            chunk_duration = 600
            num_chunks = max(1, math.ceil(duration / chunk_duration))
            
            if num_chunks == 1:
                chunks = [audio_path]
            else:
                chunks = []
                for i in range(num_chunks):
                    start_time = i * chunk_duration
                    chunk_path = os.path.join(temp_dir, f"chunk_{i:03d}.mp3")
                    cmd = [
                        "ffmpeg", "-i", audio_path,
                        "-ss", str(start_time),
                        "-t", str(chunk_duration),
                        "-acodec", "libmp3lame", "-ab", "64k", "-ar", "16000",
                        "-y", chunk_path
                    ]
                    chunk_result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                    if chunk_result.returncode != 0:
                        print(f"Chunk {i} ffmpeg error: {chunk_result.stderr}")
                    if os.path.exists(chunk_path):
                        chunks.append(chunk_path)
            
            client = OpenAI(api_key=api_key)
            all_transcripts = []
            
            for chunk_path in chunks:
                with open(chunk_path, "rb") as audio_file:
                    transcript = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        response_format="text"
                    )
                    all_transcripts.append(transcript)
            
            full_transcript = "\n\n".join(all_transcripts)
            
            transcript_path = os.path.join("transcripts", f"{output_name}_transcript.txt")
            os.makedirs("transcripts", exist_ok=True)
            with open(transcript_path, "w") as f:
                f.write(full_transcript)
            
            return jsonify({
                "transcript": full_transcript,
                "duration_minutes": duration / 60,
                "chunks": len(chunks),
                "saved_to": transcript_path
            })
    
    except Exception as e:
        print(f"Transcription error: {e}")
        return jsonify({"error": str(e)}), 500


vapi_conversation_histories = {}


def validate_vapi_request() -> bool:
    """
    Validate that the request is from VAPI.
    
    Checks for VAPI secret in Authorization header or x-vapi-secret header.
    If VAPI_WEBHOOK_SECRET is not configured, allows all requests (dev mode).
    """
    vapi_secret = os.environ.get("VAPI_WEBHOOK_SECRET", "")
    
    if not vapi_secret:
        return True
    
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        if auth_header[7:] == vapi_secret:
            return True
    
    vapi_header = request.headers.get("x-vapi-secret", "")
    if vapi_header == vapi_secret:
        return True
    
    return False


@app.route("/api/vapi/webhook", methods=["POST"])
def vapi_webhook():
    """
    VAPI Voice AI Webhook Endpoint
    
    Handles incoming requests from VAPI for ANNA Voice Assistant.
    Supports:
    - tool-calls: Custom function calls to get ANNA coaching responses
    - conversation-update: Track conversation state
    - end-of-call-report: Log completed calls
    - Other events: Acknowledge without action
    
    Security: Validates VAPI_WEBHOOK_SECRET if configured.
    """
    if not validate_vapi_request():
        print(f"[VAPI] Rejected request - invalid or missing authentication")
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        data = request.get_json()
        if not data or "message" not in data:
            return jsonify({"error": "Invalid request format"}), 400
        
        message = data["message"]
        message_type = message.get("type", "")
        call_id = message.get("call", {}).get("id", "unknown")
        
        print(f"[VAPI] Received {message_type} for call {call_id}")
        
        if message_type == "tool-calls":
            return handle_vapi_tool_calls(message, call_id)
        
        elif message_type == "conversation-update":
            return handle_vapi_conversation_update(message, call_id)
        
        elif message_type == "end-of-call-report":
            return handle_vapi_end_of_call(message, call_id)
        
        elif message_type == "assistant-request":
            return handle_vapi_assistant_request(message, call_id)
        
        elif message_type == "status-update":
            status = message.get("status", "")
            print(f"[VAPI] Call {call_id} status: {status}")
            return jsonify({}), 200
        
        elif message_type == "transcript":
            transcript = message.get("transcript", "")
            role = message.get("role", "")
            print(f"[VAPI] Transcript ({role}): {transcript[:100]}...")
            return jsonify({}), 200
        
        else:
            print(f"[VAPI] Unhandled message type: {message_type}")
            return jsonify({}), 200
            
    except Exception as e:
        print(f"[VAPI] Webhook error: {e}")
        return jsonify({"error": str(e)}), 500


def handle_vapi_tool_calls(message: dict, call_id: str):
    """
    Handle VAPI tool/function calls.
    
    When VAPI's LLM decides to call our custom tool (e.g., get_somera_response),
    this function processes the request and returns the ANNA response.
    
    Uses response_type: "final" to make VAPI speak our response verbatim
    without LLM reformulation, ensuring guardrails are followed exactly.
    """
    tool_calls = message.get("toolCallList", [])
    tool_with_call_list = message.get("toolWithToolCallList", [])
    
    if not tool_calls and tool_with_call_list:
        tool_calls = []
        for item in tool_with_call_list:
            tool_call = item.get("toolCall", {})
            tool_call["name"] = item.get("name", tool_call.get("name", ""))
            tool_calls.append(tool_call)
    
    results = []
    
    for tool_call in tool_calls:
        tool_call_id = tool_call.get("id", "")
        tool_name = tool_call.get("name", "")
        params = tool_call.get("parameters", {})
        
        print(f"[VAPI] Tool call: {tool_name} with params: {params}")
        
        if tool_name == "get_somera_response":
            user_message = params.get("user_message", params.get("message", ""))
            
            if not user_message:
                results.append({
                    "toolCallId": tool_call_id,
                    "result": "I didn't catch that. Could you please repeat?"
                })
                continue
            
            history = vapi_conversation_histories.get(call_id, [])
            
            try:
                response_data = generate_somera_response(
                    user_message=user_message,
                    conversation_history=history,
                    delivery_mode="voice"
                )
                response_text = response_data.get("response", "I'm here to listen. Could you tell me more?")
                response_text = optimize_response_for_voice(response_text)
                
                history.append({"role": "user", "content": user_message})
                history.append({"role": "assistant", "content": response_text})
                vapi_conversation_histories[call_id] = history[-20:]
                
                print(f"[VAPI] ANNA response (voice mode): {response_text[:100]}...")
                
                results.append({
                    "toolCallId": tool_call_id,
                    "result": response_text,
                    "message": response_text
                })
                
            except Exception as e:
                print(f"[VAPI] ANNA error: {e}")
                results.append({
                    "toolCallId": tool_call_id,
                    "result": "I'm having a moment. Could you share that with me again?"
                })
        
        else:
            results.append({
                "toolCallId": tool_call_id,
                "result": f"Unknown tool: {tool_name}"
            })
    
    return jsonify({"results": results}), 200


def handle_vapi_conversation_update(message: dict, call_id: str):
    """Track conversation updates from VAPI."""
    messages = message.get("messagesOpenAIFormatted", [])
    if messages:
        vapi_conversation_histories[call_id] = messages[-20:]
        print(f"[VAPI] Updated conversation history for call {call_id}: {len(messages)} messages")
    return jsonify({}), 200


def handle_vapi_end_of_call(message: dict, call_id: str):
    """Handle end of call report - log and clean up."""
    ended_reason = message.get("endedReason", "unknown")
    artifact = message.get("artifact", {})
    transcript = artifact.get("transcript", "")
    duration = message.get("call", {}).get("duration", 0)
    
    print(f"[VAPI] Call {call_id} ended. Reason: {ended_reason}, Duration: {duration}s")
    print(f"[VAPI] Transcript preview: {transcript[:200]}...")
    
    if call_id in vapi_conversation_histories:
        del vapi_conversation_histories[call_id]
    
    return jsonify({}), 200


def handle_vapi_assistant_request(message: dict, call_id: str):
    """
    Handle dynamic assistant configuration request.
    
    This is called when VAPI needs to know which assistant to use.
    We return a transient assistant configuration with ANNA's persona.
    """
    elevenlabs_voice_id = os.environ.get("ELEVENLABS_VOICE_ID", "")
    
    webhook_base = os.environ.get("WEBHOOK_BASE_URL", "")
    if not webhook_base:
        replit_domain = os.environ.get("REPLIT_DEV_DOMAIN", "")
        if replit_domain:
            webhook_base = f"https://{replit_domain}"
    
    webhook_url = f"{webhook_base}/api/vapi/webhook"
    
    assistant_config = {
        "assistant": {
            "name": "ANNA Voice",
            "firstMessage": "Hello, this is Somera. I'm here to listen and support you. What's on your mind today?",
            "model": {
                "provider": "openai",
                "model": "gpt-4o-mini",
                "messages": [
                    {
                        "role": "system",
                        "content": get_somera_voice_system_prompt()
                    }
                ],
                "tools": [
                    {
                        "type": "endCall"
                    },
                    {
                        "type": "function",
                        "function": {
                            "name": "get_somera_response",
                            "description": "Get a coaching response from ANNA based on what the user shared. Call this for every user message to provide empathetic coaching.",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "user_message": {
                                        "type": "string",
                                        "description": "What the user said"
                                    }
                                },
                                "required": ["user_message"]
                            }
                        },
                        "async": False,
                        "server": {
                            "url": webhook_url
                        }
                    }
                ]
            },
            "voice": {
                "provider": "11labs",
                "voiceId": elevenlabs_voice_id or "21m00Tcm4TlvDq8ikWAM"
            },
            "transcriber": {
                "provider": "deepgram",
                "model": "nova-2",
                "language": "en"
            },
            "server": {
                "url": webhook_url
            },
            "silenceTimeoutSeconds": 30,
            "responseDelaySeconds": 0.4,
            "endCallMessage": "Thank you for sharing with me today. Take care of yourself, and remember, you're not alone on this journey.",
            "endCallPhrases": [
                "goodbye", "bye", "bye bye", "bye-bye",
                "thank you bye", "thanks bye", "thank you goodbye",
                "that's all", "that is all", "that will be all",
                "end call", "end the call", "hang up",
                "no thank you", "no thanks", "no that's it",
                "have a nice day", "have a good day", "have a great day",
                "take care", "see you", "see you later",
                "I'm done", "I am done", "we're done", "we are done",
                "nothing else", "nothing more", "that's everything",
                "I'll let you go", "let me go", "I should go",
                "I have to go", "I need to go", "gotta go"
            ]
        }
    }
    
    print(f"[VAPI] Returning assistant config for call {call_id}")
    return jsonify(assistant_config), 200


def get_somera_voice_system_prompt() -> str:
    """Get the system prompt optimized for voice interactions."""
    return """You are ANNA, Anna's empathetic AI coaching assistant for Anna Kitney, speaking with someone on a phone call.

YOUR VOICE PERSONA:
- Warm, calm, and genuinely caring - like a trusted friend who truly sees them
- Speak naturally as if in a real conversation
- Use short, conversational sentences (2-3 sentences max per turn)
- Never sound robotic or scripted
- Your tone should feel like a cozy chat over tea

VARIETY IN LANGUAGE:
- Avoid overusing any single phrase - vary your language naturally
- Don't use the same acknowledgment in back-to-back responses
- Let your responses flow naturally - forced variety sounds robotic too

SHWETA'S ACKNOWLEDGMENT PHRASES (vary these naturally):
- "I see you..." - seeing their full self
- "I also see the version of you that no one talks about..."
- "I know that version of you as well..."
- "That makes so much sense..."
- "That's landing deeply..."
- "I can feel that..."
- "I've got you here..."
- "Yes..." / "Mmm..." / "Absolutely..."
- Simply reflecting back what they said in your own words

SHWETA'S PATTERN-RECOGNITION LANGUAGE:
- "You don't have separate problems - you have one pattern showing up everywhere"
- "Once you see it, it becomes easier to work with"
- "This pattern has been protecting you - it kept you safe"
- "What kept you safe at five years old might be keeping you stuck now"
- "Does that resonate with you?"
- "Notice what feels familiar..."

SHWETA'S COACHING QUESTIONS (use sparingly, one at a time):
- "Where do you feel that in your body right now?"
- "What do you think might be underneath that?"
- "Would you feel comfortable sharing more about that?"
- "How long have you been carrying this?"
- "What would it feel like to let that go?"

COACHING APPROACH - SHWETA'S 4-STEP FRAMEWORK:
Step 1 (Acknowledgment): Help them SEE and NAME the pattern
Step 2 (Decision): Gently ask if they're ready to release it
Steps 3-4 (Release/Recalibrate): These require live sessions - guide to Discovery Call

VOICE CONVERSATION RULES:
- Keep responses to 2-3 sentences maximum - this is a phone call
- Ask ONE question per turn, then listen
- Don't give advice - guide them to their own insights
- For deep healing (chakra work, energy healing, regression): warmly suggest a Discovery Call
- Never speak URLs - offer to share the link another way

OPENING GREETING:
"Hi there, welcome. I'm so glad you're here. This is a safe space to share whatever's on your mind. What's bringing you here today?"

CLOSING THE CALL:
When the user says goodbye or wants to end:
1. Say: "Thank you for sharing with me today. Take gentle care of yourself."
2. IMMEDIATELY use the endCall tool

IMPORTANT:
- Use get_somera_response tool for EVERY message to get coaching context
- When user says goodbye, YOU MUST use endCall tool after your closing
- Keep energy warm and unhurried - never rush
- Never say "as an AI" or break character"""


def optimize_response_for_voice(text: str) -> str:
    """
    Optimize text response for voice/TTS output.
    
    - Remove markdown formatting
    - Shorten for conversational flow
    - Remove URLs (can't speak them naturally)
    - Add natural pauses
    """
    import re
    
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    text = re.sub(r'__([^_]+)__', r'\1', text)
    text = re.sub(r'_([^_]+)_', r'\1', text)
    
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    
    text = re.sub(r'https?://[^\s]+', '', text)
    
    text = re.sub(r'^\s*[-*•]\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*\d+\.\s*', '', text, flags=re.MULTILINE)
    
    text = text.replace('💙', '').replace('❤️', '').replace('✨', '').replace('🌟', '')
    text = re.sub(r'[^\w\s.,!?\'"-]', '', text)
    
    text = re.sub(r'\n+', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    
    sentences = text.split('. ')
    if len(sentences) > 4:
        text = '. '.join(sentences[:4]) + '.'
    
    return text


custom_llm_conversation_histories = {}
voice_call_turn_counts = {}

# CRITICAL: Graceful error message for VAPI when backend fails
# This ensures ANNA speaks an error message instead of VAPI falling back to GPT
ANNA_ERROR_MESSAGE = "I'm sorry, I'm experiencing some technical difficulties right now. Please try again in a moment, or reach out to our team directly for support."


def log_backend_error(error_type: str, endpoint: str, error_message: str, request_data: str = None, call_id: str = None):
    """Log backend errors to database for monitoring and alerting.
    
    Falls back to file logging if database is unavailable to ensure
    no error evidence is lost during outages.
    """
    import threading
    import datetime
    
    def _log():
        db_logged = False
        try:
            import psycopg2
            database_url = os.environ.get("DATABASE_URL")
            if database_url:
                conn = psycopg2.connect(database_url)
                cur = conn.cursor()
                
                cur.execute("""
                    INSERT INTO backend_error_logs (error_type, endpoint, error_message, request_data, call_id)
                    VALUES (%s, %s, %s, %s, %s)
                """, (error_type, endpoint, error_message, request_data, call_id))
                
                conn.commit()
                cur.close()
                conn.close()
                db_logged = True
                
                print(f"[ERROR LOG] Logged {error_type} error for call {call_id}: {error_message[:100]}")
                
        except Exception as db_error:
            print(f"[ERROR LOG] Database logging failed: {db_error}")
        
        # Fallback: Always log to file as backup
        if not db_logged:
            try:
                os.makedirs("logs", exist_ok=True)
                timestamp = datetime.datetime.now().isoformat()
                with open("logs/backend_errors.log", "a") as f:
                    f.write(f"\n[{timestamp}] {error_type} | {endpoint} | call_id={call_id}\n")
                    f.write(f"Error: {error_message}\n")
                    if request_data:
                        f.write(f"Request: {request_data[:500]}\n")
                    f.write("-" * 50 + "\n")
                print(f"[ERROR LOG] Fallback file logging completed for {error_type}")
            except Exception as file_error:
                print(f"[ERROR LOG] CRITICAL - Both DB and file logging failed: {file_error}")
    
    thread = threading.Thread(target=_log, daemon=True)
    thread.start()


def save_voice_message_async(call_id: str, role: str, content: str, readiness_score: float = None, readiness_recommendation: str = None, latency_ms: int = None, closure_type: str = None, sources: list = None):
    """Save a voice message to the database in a background thread (non-blocking for latency)."""
    import threading
    import json
    
    turn_number = voice_call_turn_counts.get(call_id, 0)
    if role == "user":
        turn_number += 1
        voice_call_turn_counts[call_id] = turn_number
    
    sources_json = json.dumps(sources) if sources else None
    
    def _save():
        try:
            import psycopg2
            database_url = os.environ.get("DATABASE_URL")
            if not database_url:
                return
            
            conn = psycopg2.connect(database_url)
            cur = conn.cursor()
            
            cur.execute("""
                INSERT INTO voice_conversations (call_id, started_at)
                VALUES (%s, CURRENT_TIMESTAMP)
                ON CONFLICT (call_id) DO NOTHING
            """, (call_id,))
            
            cur.execute("""
                INSERT INTO voice_messages (call_id, turn_number, role, content, readiness_score, readiness_recommendation, latency_ms, closure_type, sources, timestamp)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            """, (call_id, turn_number, role, content, readiness_score, readiness_recommendation, latency_ms, closure_type, sources_json))
            
            conn.commit()
            cur.close()
            conn.close()
            
        except Exception as e:
            print(f"[Voice DB Async] Error: {e}")
    
    thread = threading.Thread(target=_save, daemon=True)
    thread.start()


def save_voice_message_to_db(call_id: str, role: str, content: str, readiness_score: float = None, readiness_recommendation: str = None):
    """Save a voice conversation message to the database."""
    try:
        import psycopg2
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            print("[Voice DB] DATABASE_URL not found, skipping save")
            return
        
        turn_number = voice_call_turn_counts.get(call_id, 0)
        if role == "user":
            turn_number += 1
            voice_call_turn_counts[call_id] = turn_number
        
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO voice_messages (call_id, turn_number, role, content, readiness_score, readiness_recommendation)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (call_id, turn_number, role, content, readiness_score, readiness_recommendation))
        
        conn.commit()
        cur.close()
        conn.close()
        
        print(f"[Voice DB] Saved {role} message for call {call_id}, turn {turn_number}")
        
    except Exception as e:
        print(f"[Voice DB] Error saving message: {e}")


def save_voice_call_summary(call_id: str, total_turns: int, full_transcript: str):
    """Save a summary of the voice call to the database."""
    try:
        import psycopg2
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            return
        
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO voice_conversations (call_id, total_turns, full_transcript, ended_at)
            VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (call_id) DO UPDATE SET
                total_turns = EXCLUDED.total_turns,
                full_transcript = EXCLUDED.full_transcript,
                ended_at = CURRENT_TIMESTAMP
        """, (call_id, total_turns, full_transcript))
        
        conn.commit()
        cur.close()
        conn.close()
        
        print(f"[Voice DB] Saved call summary for {call_id}")
        
    except Exception as e:
        print(f"[Voice DB] Error saving call summary: {e}")


@app.route("/api/vapi/chat/completions", methods=["POST"])
def vapi_custom_llm():
    """
    VAPI Custom LLM Endpoint - OpenAI-compatible /chat/completions
    
    This endpoint REPLACES VAPI's LLM entirely. VAPI sends us:
    - Deepgram transcription in OpenAI message format
    - We process with ANNA engine
    - Return response that VAPI speaks with ElevenLabs
    
    NO VAPI LLM INTERFERENCE - we have full control.
    
    CRITICAL SAFETY: ALL exceptions are caught and converted to graceful
    error responses. We NEVER return 5xx which would trigger VAPI fallback to GPT.
    
    Security: Validates VAPI_WEBHOOK_SECRET if configured.
    """
    import time as timing_module
    
    # Helper function to return graceful error response
    def graceful_error_response(stream_mode=False, call_id_val=None):
        """Return a valid OpenAI response with error message - VAPI will speak this."""
        if stream_mode:
            return stream_openai_response(ANNA_ERROR_MESSAGE, call_id_val or "error", end_call=False)
        return jsonify({
            "id": f"chatcmpl-error-{timing_module.time()}",
            "object": "chat.completion",
            "created": int(timing_module.time()),
            "model": "somera-voice-1",
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": ANNA_ERROR_MESSAGE},
                "finish_reason": "stop"
            }],
            "usage": {"prompt_tokens": 0, "completion_tokens": 20, "total_tokens": 20}
        })
    
    # Auth check - still return 401 for security (VAPI will handle this)
    if not validate_vapi_request():
        print(f"[VAPI Custom LLM] Rejected request - invalid or missing authentication")
        return jsonify({"error": "Unauthorized"}), 401
    
    request_start = timing_module.time()
    
    # SAFE PARSING: Wrap all request parsing in try-except
    try:
        data = request.get_json(silent=True) or {}
    except Exception as parse_error:
        print(f"[VAPI Custom LLM] Request parse error: {parse_error}")
        try:
            log_backend_error("request_parse_error", "/api/vapi/chat/completions", str(parse_error))
        except:
            pass
        return graceful_error_response(stream_mode=False)
    
    try:
        if data:
            print(f"[VAPI Custom LLM] Raw request keys: {list(data.keys())}")
        messages = data.get("messages", [])
        stream = data.get("stream", False)
        
        call_metadata = data.get("call", {})
        call_id = call_metadata.get("id", "custom-llm-" + str(hash(str(messages)))[:8])
        
        print(f"[VAPI Custom LLM] Received request for call {call_id}, stream={stream}")
        
        user_message = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_message = msg.get("content", "")
                break
        
        if not user_message:
            response_text = "Hello! I'm ANNA, your coaching companion. How are you feeling today?"
            save_voice_message_async(call_id, "assistant", response_text)
        else:
            history = custom_llm_conversation_histories.get(call_id, [])
            
            try:
                from readiness_scoring import calculate_readiness_score
                from somera_engine import is_booking_request, get_voice_friendly_booking_response
                
                readiness_result = calculate_readiness_score(user_message, history)
                readiness_score = readiness_result.get("total_score", 0)
                readiness_rec = readiness_result.get("recommendation", "explore")
                
                save_voice_message_async(call_id, "user", user_message, readiness_score, readiness_rec)
                
                booking = is_booking_request(user_message)
                
                print(f"[VAPI Custom LLM] Booking check: {booking}")
                
                skip_voice_optimization = False
                closure_type_str = None
                sources = None
                
                if booking:
                    response_text = get_voice_friendly_booking_response()
                    skip_voice_optimization = True
                    closure_type_str = "booking_request"
                    print(f"[VAPI Custom LLM] Booking request detected - providing voice-friendly booking info")
                else:
                    response_data = generate_somera_response(
                        user_message=user_message,
                        conversation_history=history,
                        delivery_mode="voice"
                    )
                    response_text = response_data.get("response", "I'm here to listen. Could you tell me more?")
                    sources = response_data.get("sources", [])
                
                if not skip_voice_optimization:
                    response_text = optimize_response_for_voice(response_text)
                
                elapsed_ms = int((timing_module.time() - request_start) * 1000)
                
                save_voice_message_async(call_id, "assistant", response_text, latency_ms=elapsed_ms, closure_type=closure_type_str, sources=sources)
                
                history.append({"role": "user", "content": user_message})
                history.append({"role": "assistant", "content": response_text})
                custom_llm_conversation_histories[call_id] = history[-20:]
                
                print(f"[VAPI Custom LLM] ANNA response: {response_text[:100]}...")
                print(f"[VAPI Custom LLM] Readiness: {readiness_score:.0%} ({readiness_rec})")
                print(f"[VAPI Custom LLM] Response latency: {elapsed_ms}ms")
                
            except Exception as e:
                print(f"[VAPI Custom LLM] ANNA processing error: {e}")
                import traceback
                log_backend_error(
                    error_type="somera_processing_error",
                    endpoint="/api/vapi/chat/completions",
                    error_message=f"{str(e)}\n{traceback.format_exc()}",
                    request_data=user_message[:500] if user_message else None,
                    call_id=call_id
                )
                response_text = "I'm here with you. Could you share that with me again?"
        
        if stream:
            return stream_openai_response(response_text, call_id, end_call=False)
        else:
            return jsonify({
                "id": f"chatcmpl-{call_id}",
                "object": "chat.completion",
                "created": int(__import__('time').time()),
                "model": "somera-voice-1",
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": response_text
                    },
                    "finish_reason": "stop"
                }],
                "usage": {
                    "prompt_tokens": len(user_message.split()),
                    "completion_tokens": len(response_text.split()),
                    "total_tokens": len(user_message.split()) + len(response_text.split())
                }
            })
            
    except Exception as e:
        # CRITICAL: Never return 500 - this triggers VAPI fallback to GPT!
        # Instead, return a graceful spoken error message
        print(f"[VAPI Custom LLM] CRITICAL ERROR - Returning graceful error response: {e}")
        
        # Log error (wrapped in try-except to never interfere with response)
        try:
            import traceback
            error_details = traceback.format_exc()
            try:
                raw_data = request.data.decode('utf-8')[:1000] if request.data else None
            except:
                raw_data = None
            log_backend_error(
                error_type="vapi_endpoint_critical_error",
                endpoint="/api/vapi/chat/completions",
                error_message=f"{str(e)}\n{error_details}",
                request_data=raw_data,
                call_id=None
            )
        except:
            pass  # Never let logging failure prevent graceful response
        
        # Return graceful error using helper function
        return graceful_error_response(stream_mode=False)


def stream_openai_response(response_text: str, call_id: str, end_call: bool = False):
    """
    Stream response in OpenAI SSE format for real-time voice.
    
    VAPI expects SSE with 'data: {...}' format matching OpenAI's streaming.
    First chunk MUST include 'role: assistant' for OpenAI-compatible clients.
    
    CRITICAL: All errors are caught and converted to graceful error messages
    to prevent VAPI from falling back to its own GPT.
    
    Args:
        response_text: The text to speak
        call_id: Unique call identifier
        end_call: If True, include endCall tool call to terminate the VAPI call
    """
    import time
    import json
    
    def generate():
        try:
            chunk_id = f"chatcmpl-{call_id}"
            
            role_chunk = {
                "id": chunk_id,
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": "somera-voice-1",
                "choices": [{
                    "index": 0,
                    "delta": {
                        "role": "assistant",
                        "content": ""
                    },
                    "finish_reason": None
                }]
            }
            yield f"data: {json.dumps(role_chunk)}\n\n"
            
            words = response_text.split()
            chunk_size = 3
            
            for i in range(0, len(words), chunk_size):
                chunk_words = words[i:i + chunk_size]
                chunk_text = " ".join(chunk_words)
                if i > 0:
                    chunk_text = " " + chunk_text
                
                chunk_data = {
                    "id": chunk_id,
                    "object": "chat.completion.chunk",
                    "created": int(time.time()),
                    "model": "somera-voice-1",
                    "choices": [{
                        "index": 0,
                        "delta": {
                            "content": chunk_text
                        },
                        "finish_reason": None
                    }]
                }
                yield f"data: {json.dumps(chunk_data)}\n\n"
            
            if end_call:
                tool_call_chunk = {
                    "id": chunk_id,
                    "object": "chat.completion.chunk",
                    "created": int(time.time()),
                    "model": "somera-voice-1",
                    "choices": [{
                        "index": 0,
                        "delta": {
                            "tool_calls": [{
                                "id": f"call_endCall_{call_id[:8]}",
                                "type": "function",
                                "function": {
                                    "name": "endCall",
                                    "arguments": "{}"
                                }
                            }]
                        },
                        "finish_reason": "tool_calls"
                    }]
                }
                yield f"data: {json.dumps(tool_call_chunk)}\n\n"
                print(f"[VAPI Custom LLM] Sent endCall tool call to terminate call {call_id}")
            else:
                done_data = {
                    "id": chunk_id,
                    "object": "chat.completion.chunk",
                    "created": int(time.time()),
                    "model": "somera-voice-1",
                    "choices": [{
                        "index": 0,
                        "delta": {},
                        "finish_reason": "stop"
                    }]
                }
                yield f"data: {json.dumps(done_data)}\n\n"
            
            yield "data: [DONE]\n\n"
            
        except Exception as stream_error:
            # CRITICAL: Catch any streaming errors and return graceful error message
            print(f"[VAPI Custom LLM] Streaming error - sending graceful error: {stream_error}")
            log_backend_error(
                error_type="streaming_error",
                endpoint="/api/vapi/chat/completions",
                error_message=str(stream_error),
                call_id=call_id
            )
            # Send error message as valid SSE chunks
            error_chunk_id = f"chatcmpl-error-{call_id}"
            error_role = {
                "id": error_chunk_id,
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": "somera-voice-1",
                "choices": [{"index": 0, "delta": {"role": "assistant", "content": ""}, "finish_reason": None}]
            }
            yield f"data: {json.dumps(error_role)}\n\n"
            
            error_content = {
                "id": error_chunk_id,
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": "somera-voice-1",
                "choices": [{"index": 0, "delta": {"content": ANNA_ERROR_MESSAGE}, "finish_reason": None}]
            }
            yield f"data: {json.dumps(error_content)}\n\n"
            
            error_done = {
                "id": error_chunk_id,
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": "somera-voice-1",
                "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]
            }
            yield f"data: {json.dumps(error_done)}\n\n"
            yield "data: [DONE]\n\n"
    
    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@app.route("/api/admin/somera/stats", methods=["GET"])
def somera_admin_stats():
    """Get ANNA Voice statistics for admin dashboard."""
    try:
        range_param = request.args.get('range', '30d')
        days = 30
        if range_param == '7d':
            days = 7
        elif range_param == '24h':
            days = 1
        
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
        
        cur = conn.cursor()
        
        cur.execute("""
            SELECT 
                COUNT(DISTINCT call_id) as total_calls,
                COUNT(*) as total_messages,
                AVG(CASE WHEN latency_ms > 0 THEN latency_ms END) as avg_latency,
                MAX(readiness_score) as peak_readiness,
                AVG(readiness_score) as avg_readiness,
                COUNT(CASE WHEN closure_type = 'booking_request' THEN 1 END) as booking_requests
            FROM voice_messages
            WHERE timestamp >= NOW() - INTERVAL '%s days'
        """, (days,))
        row = cur.fetchone()
        
        total_calls = row[0] or 0
        total_messages = row[1] or 0
        avg_latency = float(row[2]) if row[2] else 0
        peak_readiness = float(row[3]) if row[3] else 0
        avg_readiness = float(row[4]) if row[4] else 0
        booking_requests = row[5] or 0
        
        booking_rate = (booking_requests / total_calls * 100) if total_calls > 0 else 0
        
        cur.execute("""
            SELECT 
                DATE(timestamp) as date,
                MIN(CASE WHEN latency_ms > 0 THEN latency_ms END) as min_latency,
                AVG(CASE WHEN latency_ms > 0 THEN latency_ms END) as avg_latency,
                MAX(CASE WHEN latency_ms > 0 THEN latency_ms END) as max_latency
            FROM voice_messages
            WHERE timestamp >= NOW() - INTERVAL '%s days'
            GROUP BY DATE(timestamp)
            ORDER BY date
        """, (days,))
        latency_rows = cur.fetchall()
        
        latency_trends = []
        for lr in latency_rows:
            latency_trends.append({
                "date": lr[0].strftime('%b %d') if lr[0] else '',
                "min": float(lr[1]) if lr[1] else 0,
                "avg": float(lr[2]) if lr[2] else 0,
                "max": float(lr[3]) if lr[3] else 0
            })
        
        cur.execute("""
            SELECT 
                CASE 
                    WHEN readiness_score < 0.20 THEN 'explore'
                    WHEN readiness_score < 0.35 THEN 'transition'
                    ELSE 'guide'
                END as zone,
                COUNT(*) as count
            FROM voice_messages
            WHERE role = 'user' AND readiness_score IS NOT NULL
                AND timestamp >= NOW() - INTERVAL '%s days'
            GROUP BY zone
        """, (days,))
        zone_rows = cur.fetchall()
        
        readiness_distribution = {"explore": 0, "transition": 0, "guide": 0}
        for zr in zone_rows:
            if zr[0] in readiness_distribution:
                readiness_distribution[zr[0]] = zr[1]
        
        cur.close()
        conn.close()
        
        return jsonify({
            "totalCalls": total_calls,
            "totalMessages": total_messages,
            "avgLatency": round(avg_latency, 1),
            "peakReadiness": round(peak_readiness * 100, 1),
            "avgReadiness": round(avg_readiness * 100, 1),
            "bookingRate": round(booking_rate, 1),
            "latencyTrends": latency_trends,
            "readinessDistribution": readiness_distribution
        })
        
    except Exception as e:
        print(f"[ANNA Admin] Stats error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/admin/somera/calls", methods=["GET"])
def somera_admin_calls():
    """Get list of ANNA Voice calls for admin dashboard."""
    try:
        range_param = request.args.get('range', '30d')
        days = 30
        if range_param == '7d':
            days = 7
        elif range_param == '24h':
            days = 1
        
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
        
        cur = conn.cursor()
        
        cur.execute("""
            SELECT 
                call_id,
                MIN(timestamp) as started_at,
                MAX(timestamp) as ended_at,
                COUNT(*) as message_count,
                AVG(CASE WHEN latency_ms > 0 THEN latency_ms END) as avg_latency,
                MAX(readiness_score) as peak_readiness,
                BOOL_OR(closure_type = 'booking_request') as had_booking
            FROM voice_messages
            WHERE timestamp >= NOW() - INTERVAL '%s days'
            GROUP BY call_id
            ORDER BY MIN(timestamp) DESC
            LIMIT 50
        """, (days,))
        rows = cur.fetchall()
        
        calls = []
        for row in rows:
            calls.append({
                "callId": row[0],
                "startedAt": row[1].isoformat() if row[1] else None,
                "endedAt": row[2].isoformat() if row[2] else None,
                "messageCount": row[3] or 0,
                "avgLatency": float(row[4]) if row[4] else None,
                "peakReadiness": float(row[5]) if row[5] else 0,
                "hadBooking": row[6] or False
            })
        
        cur.close()
        conn.close()
        
        return jsonify({"calls": calls})
        
    except Exception as e:
        print(f"[ANNA Admin] Calls error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/admin/somera/calls/<call_id>", methods=["GET"])
def somera_admin_call_detail(call_id):
    """Get detailed transcript for a specific ANNA Voice call."""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
        
        cur = conn.cursor()
        
        cur.execute("""
            SELECT 
                role, content, readiness_score, readiness_recommendation,
                latency_ms, closure_type, timestamp, sources
            FROM voice_messages
            WHERE call_id = %s
            ORDER BY timestamp ASC
        """, (call_id,))
        rows = cur.fetchall()
        
        import json
        messages = []
        for row in rows:
            sources_data = None
            if row[7]:
                try:
                    sources_data = json.loads(row[7]) if isinstance(row[7], str) else row[7]
                except:
                    sources_data = None
            
            messages.append({
                "role": row[0],
                "content": row[1],
                "readinessScore": float(row[2]) if row[2] else None,
                "readinessRecommendation": row[3],
                "latencyMs": float(row[4]) if row[4] else None,
                "closureType": row[5],
                "timestamp": row[6].isoformat() if row[6] else None,
                "sources": sources_data
            })
        
        cur.close()
        conn.close()
        
        return jsonify({
            "callId": call_id,
            "messages": messages
        })
        
    except Exception as e:
        print(f"[ANNA Admin] Call detail error: {e}")
        return jsonify({"error": str(e)}), 500


def get_db_connection():
    """Get PostgreSQL database connection."""
    import psycopg2
    try:
        conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None


@app.route("/api/admin/somera/export", methods=["GET"])
def somera_admin_export_csv():
    """Export ANNA Voice calls and transcripts as CSV."""
    try:
        import csv
        import io
        from datetime import datetime, timedelta
        
        range_param = request.args.get("range", "30d")
        days = 30
        if range_param == "24h":
            days = 1
        elif range_param == "7d":
            days = 7
        elif range_param == "30d":
            days = 30
        
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
        
        cur = conn.cursor()
        
        cur.execute("""
            SELECT 
                vc.call_id,
                vc.started_at,
                vc.ended_at,
                vm.role,
                vm.content,
                vm.readiness_score,
                vm.readiness_recommendation,
                vm.latency_ms,
                vm.timestamp
            FROM voice_conversations vc
            LEFT JOIN voice_messages vm ON vc.call_id = vm.call_id
            WHERE vc.started_at >= CURRENT_TIMESTAMP - INTERVAL '%s days'
            ORDER BY vc.started_at DESC, vm.timestamp ASC
        """, (days,))
        rows = cur.fetchall()
        
        cur.close()
        conn.close()
        
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            'Call ID', 'Call Started', 'Call Ended', 
            'Role', 'Message', 'Readiness Score', 
            'Readiness Zone', 'Latency (ms)', 'Timestamp'
        ])
        
        for row in rows:
            writer.writerow([
                row[0],
                row[1].strftime('%Y-%m-%d %H:%M:%S') if row[1] else '',
                row[2].strftime('%Y-%m-%d %H:%M:%S') if row[2] else '',
                row[3] or '',
                row[4] or '',
                f"{float(row[5]) * 100:.1f}%" if row[5] else '',
                row[6] or '',
                int(row[7]) if row[7] else '',
                row[8].strftime('%Y-%m-%d %H:%M:%S') if row[8] else ''
            ])
        
        output.seek(0)
        
        from flask import Response
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename=somera_transcripts_{datetime.now().strftime("%Y%m%d")}.csv'
            }
        )
        
    except Exception as e:
        print(f"[ANNA Admin] Export error: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("WEBHOOK_PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
