"""
Conversation Logging Module for JoveHeal Chatbot

Stores conversation logs in PostgreSQL database with fallback to file-based storage.
Includes:
- Conversation history
- Session tracking
- Safety flag logging
- Response feedback
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any

from database import (
    init_database, get_db_session, is_database_available,
    ChatSession, Conversation, ResponseFeedback, AnalyticsDaily
)
from sqlalchemy import func, desc, and_

LOG_DIR = Path("logs")
CONVERSATION_LOG_FILE = LOG_DIR / "conversations.json"


def ensure_log_directory():
    """Ensure the logs directory exists."""
    LOG_DIR.mkdir(exist_ok=True)


def load_conversation_logs_from_file() -> list:
    """Load existing conversation logs from file (fallback)."""
    ensure_log_directory()
    
    if CONVERSATION_LOG_FILE.exists():
        try:
            with open(CONVERSATION_LOG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    return []


def save_conversation_logs_to_file(logs: list):
    """Save conversation logs to file (fallback)."""
    ensure_log_directory()
    
    with open(CONVERSATION_LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(logs, f, indent=2, ensure_ascii=False, default=str)


def ensure_session_exists(session_id: str, channel: str = "web", user_id: int = None):
    """Ensure a chat session exists in the database and optionally link to user."""
    if not is_database_available():
        return
    
    with get_db_session() as db:
        if db is None:
            return
        
        existing = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
        if not existing:
            new_session = ChatSession(session_id=session_id, channel=channel, user_id=user_id)
            db.add(new_session)
        else:
            existing.last_activity = datetime.utcnow()
            if user_id and not existing.user_id:
                existing.user_id = user_id


def log_conversation(
    session_id: str,
    user_question: str,
    bot_answer: str,
    safety_flagged: bool = False,
    safety_category: str = None,
    sources: List[str] = None,
    response_time_ms: int = None,
    channel: str = "web"
) -> dict:
    """
    Log a single conversation exchange.
    
    Args:
        session_id: Unique identifier for the chat session
        user_question: The user's question
        bot_answer: The bot's response
        safety_flagged: Whether safety filters were triggered
        safety_category: Category of safety concern if flagged
        sources: List of sources used for the response
        response_time_ms: Response generation time in milliseconds
        channel: Channel (web, instagram, whatsapp)
    
    Returns:
        The logged entry dict with conversation_id
    """
    timestamp = datetime.utcnow()
    
    entry = {
        "timestamp": timestamp.isoformat(),
        "session_id": session_id,
        "user_question": user_question,
        "bot_answer": bot_answer,
        "safety_flagged": safety_flagged,
        "channel": channel
    }
    
    if safety_flagged and safety_category:
        entry["safety_category"] = safety_category
    
    if sources:
        entry["sources"] = sources
    
    if response_time_ms:
        entry["response_time_ms"] = response_time_ms
    
    conversation_id = None
    
    if is_database_available():
        try:
            with get_db_session() as db:
                if db is not None:
                    ensure_session_exists(session_id, channel)
                    
                    conv = Conversation(
                        session_id=session_id,
                        timestamp=timestamp,
                        user_question=user_question,
                        bot_answer=bot_answer,
                        safety_flagged=safety_flagged,
                        safety_category=safety_category,
                        sources_used=json.dumps(sources) if sources else None,
                        response_time_ms=response_time_ms
                    )
                    db.add(conv)
                    db.flush()
                    conversation_id = conv.id
                    entry["conversation_id"] = conversation_id
        except Exception as e:
            print(f"Database logging failed, using file fallback: {e}")
            _log_to_file(entry)
    else:
        _log_to_file(entry)
    
    return entry


def _log_to_file(entry: dict):
    """Fallback to file-based logging."""
    logs = load_conversation_logs_from_file()
    logs.append(entry)
    
    if len(logs) > 10000:
        logs = logs[-10000:]
    
    save_conversation_logs_to_file(logs)


def add_feedback(conversation_id: int, rating: int, comment: str = None) -> bool:
    """
    Add feedback for a conversation response.
    
    Args:
        conversation_id: The ID of the conversation
        rating: 1 (thumbs up) or -1 (thumbs down)
        comment: Optional feedback comment
    
    Returns:
        True if feedback was saved successfully
    """
    if not is_database_available():
        return False
    
    try:
        with get_db_session() as db:
            if db is None:
                return False
            
            existing = db.query(ResponseFeedback).filter(
                ResponseFeedback.conversation_id == conversation_id
            ).first()
            
            if existing:
                existing.rating = rating
                existing.comment = comment
            else:
                feedback = ResponseFeedback(
                    conversation_id=conversation_id,
                    rating=rating,
                    comment=comment
                )
                db.add(feedback)
            
            return True
    except Exception as e:
        print(f"Failed to save feedback: {e}")
        return False


def get_session_history(session_id: str) -> list:
    """Get all conversation logs for a specific session."""
    if is_database_available():
        try:
            with get_db_session() as db:
                if db is not None:
                    convs = db.query(Conversation).filter(
                        Conversation.session_id == session_id
                    ).order_by(Conversation.timestamp).all()
                    
                    return [{
                        "timestamp": c.timestamp.isoformat(),
                        "session_id": c.session_id,
                        "user_question": c.user_question,
                        "bot_answer": c.bot_answer,
                        "safety_flagged": c.safety_flagged,
                        "safety_category": c.safety_category,
                        "conversation_id": c.id
                    } for c in convs]
        except Exception as e:
            print(f"Database query failed: {e}")
    
    logs = load_conversation_logs_from_file()
    return [log for log in logs if log.get("session_id") == session_id]


def get_recent_logs(limit: int = 100) -> list:
    """Get the most recent conversation logs."""
    if is_database_available():
        try:
            with get_db_session() as db:
                if db is not None:
                    convs = db.query(Conversation).order_by(
                        desc(Conversation.timestamp)
                    ).limit(limit).all()
                    
                    return [{
                        "timestamp": c.timestamp.isoformat(),
                        "session_id": c.session_id,
                        "user_question": c.user_question,
                        "bot_answer": c.bot_answer,
                        "safety_flagged": c.safety_flagged,
                        "safety_category": c.safety_category,
                        "conversation_id": c.id
                    } for c in reversed(convs)]
        except Exception as e:
            print(f"Database query failed: {e}")
    
    logs = load_conversation_logs_from_file()
    return logs[-limit:] if logs else []


def get_flagged_conversations(limit: int = 100) -> list:
    """Get conversations that were flagged for safety concerns."""
    if is_database_available():
        try:
            with get_db_session() as db:
                if db is not None:
                    convs = db.query(Conversation).filter(
                        Conversation.safety_flagged == True
                    ).order_by(desc(Conversation.timestamp)).limit(limit).all()
                    
                    return [{
                        "timestamp": c.timestamp.isoformat(),
                        "session_id": c.session_id,
                        "user_question": c.user_question,
                        "bot_answer": c.bot_answer,
                        "safety_flagged": c.safety_flagged,
                        "safety_category": c.safety_category,
                        "conversation_id": c.id
                    } for c in convs]
        except Exception as e:
            print(f"Database query failed: {e}")
    
    logs = load_conversation_logs_from_file()
    return [log for log in logs if log.get("safety_flagged", False)]


def get_conversation_stats() -> dict:
    """Get statistics about conversations."""
    if is_database_available():
        try:
            with get_db_session() as db:
                if db is not None:
                    total = db.query(func.count(Conversation.id)).scalar() or 0
                    unique_sessions = db.query(func.count(func.distinct(Conversation.session_id))).scalar() or 0
                    safety_flags = db.query(func.count(Conversation.id)).filter(
                        Conversation.safety_flagged == True
                    ).scalar() or 0
                    
                    first_log = db.query(func.min(Conversation.timestamp)).scalar()
                    last_log = db.query(func.max(Conversation.timestamp)).scalar()
                    
                    avg_response_time = db.query(func.avg(Conversation.response_time_ms)).filter(
                        Conversation.response_time_ms != None
                    ).scalar()
                    
                    positive_feedback = db.query(func.count(ResponseFeedback.id)).filter(
                        ResponseFeedback.rating > 0
                    ).scalar() or 0
                    
                    negative_feedback = db.query(func.count(ResponseFeedback.id)).filter(
                        ResponseFeedback.rating < 0
                    ).scalar() or 0
                    
                    return {
                        "total_conversations": total,
                        "unique_sessions": unique_sessions,
                        "safety_flags": safety_flags,
                        "first_log": first_log.isoformat() if first_log else None,
                        "last_log": last_log.isoformat() if last_log else None,
                        "avg_response_time_ms": round(avg_response_time, 2) if avg_response_time else None,
                        "positive_feedback": positive_feedback,
                        "negative_feedback": negative_feedback,
                        "database": True
                    }
        except Exception as e:
            print(f"Database query failed: {e}")
    
    logs = load_conversation_logs_from_file()
    
    if not logs:
        return {
            "total_conversations": 0,
            "unique_sessions": 0,
            "safety_flags": 0,
            "first_log": None,
            "last_log": None,
            "database": False
        }
    
    unique_sessions = set(log.get("session_id") for log in logs)
    safety_flags = sum(1 for log in logs if log.get("safety_flagged", False))
    
    return {
        "total_conversations": len(logs),
        "unique_sessions": len(unique_sessions),
        "safety_flags": safety_flags,
        "first_log": logs[0].get("timestamp") if logs else None,
        "last_log": logs[-1].get("timestamp") if logs else None,
        "database": False
    }


def get_analytics_by_date(days: int = 30) -> List[Dict[str, Any]]:
    """Get daily analytics for the specified number of days."""
    if not is_database_available():
        return []
    
    try:
        with get_db_session() as db:
            if db is None:
                return []
            
            start_date = datetime.utcnow() - timedelta(days=days)
            
            from sqlalchemy import Integer, case
            results = db.query(
                func.date(Conversation.timestamp).label('date'),
                func.count(Conversation.id).label('conversations'),
                func.count(func.distinct(Conversation.session_id)).label('sessions'),
                func.sum(case((Conversation.safety_flagged == True, 1), else_=0)).label('safety_flags'),
                func.avg(Conversation.response_time_ms).label('avg_response_time')
            ).filter(
                Conversation.timestamp >= start_date
            ).group_by(
                func.date(Conversation.timestamp)
            ).order_by(
                func.date(Conversation.timestamp)
            ).all()
            
            return [{
                "date": str(r.date),
                "conversations": r.conversations,
                "sessions": r.sessions,
                "safety_flags": int(r.safety_flags or 0),
                "avg_response_time_ms": round(r.avg_response_time, 2) if r.avg_response_time else None
            } for r in results]
    except Exception as e:
        print(f"Analytics query failed: {e}")
        return []


def get_feedback_summary() -> Dict[str, Any]:
    """Get summary of user feedback."""
    if not is_database_available():
        return {"total": 0, "positive": 0, "negative": 0, "comments": []}
    
    try:
        with get_db_session() as db:
            if db is None:
                return {"total": 0, "positive": 0, "negative": 0, "comments": []}
            
            total = db.query(func.count(ResponseFeedback.id)).scalar() or 0
            positive = db.query(func.count(ResponseFeedback.id)).filter(
                ResponseFeedback.rating > 0
            ).scalar() or 0
            negative = db.query(func.count(ResponseFeedback.id)).filter(
                ResponseFeedback.rating < 0
            ).scalar() or 0
            
            recent_comments = db.query(ResponseFeedback).filter(
                ResponseFeedback.comment != None,
                ResponseFeedback.comment != ""
            ).order_by(desc(ResponseFeedback.created_at)).limit(10).all()
            
            comments = [{
                "rating": f.rating,
                "comment": f.comment,
                "created_at": f.created_at.isoformat()
            } for f in recent_comments]
            
            return {
                "total": total,
                "positive": positive,
                "negative": negative,
                "comments": comments
            }
    except Exception as e:
        print(f"Feedback query failed: {e}")
        return {"total": 0, "positive": 0, "negative": 0, "comments": []}


def log_feedback(session_id: str, is_positive: bool, comment: str = None) -> bool:
    """
    Log feedback for a session (simpler interface for the frontend).
    
    Args:
        session_id: Session identifier
        is_positive: True for thumbs up, False for thumbs down
        comment: Optional feedback comment
    
    Returns:
        True if feedback was saved successfully
    """
    if not is_database_available():
        return False
    
    try:
        with get_db_session() as db:
            if db is None:
                return False
            
            rating = 1 if is_positive else -1
            
            feedback = ResponseFeedback(
                conversation_id=None,
                rating=rating,
                comment=comment
            )
            db.add(feedback)
            return True
    except Exception as e:
        print(f"Failed to log feedback: {e}")
        return False


def clear_old_logs(days: int = 30) -> int:
    """Remove logs older than specified number of days."""
    if is_database_available():
        try:
            with get_db_session() as db:
                if db is not None:
                    cutoff = datetime.utcnow() - timedelta(days=days)
                    deleted = db.query(Conversation).filter(
                        Conversation.timestamp < cutoff
                    ).delete()
                    return deleted
        except Exception as e:
            print(f"Database cleanup failed: {e}")
    
    logs = load_conversation_logs_from_file()
    cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)
    
    filtered_logs = []
    for log in logs:
        try:
            log_time = datetime.fromisoformat(log.get("timestamp", "")).timestamp()
            if log_time > cutoff:
                filtered_logs.append(log)
        except (ValueError, TypeError):
            filtered_logs.append(log)
    
    save_conversation_logs_to_file(filtered_logs)
    return len(logs) - len(filtered_logs)


def migrate_file_logs_to_database() -> int:
    """
    Migrate existing file-based logs to the database.
    Checks for duplicates based on session_id, timestamp, and user_question.
    Clears migrated entries from the file after successful migration.
    """
    if not is_database_available():
        return 0
    
    logs = load_conversation_logs_from_file()
    if not logs:
        return 0
    
    migrated = 0
    migrated_indices = []
    
    try:
        with get_db_session() as db:
            if db is None:
                return 0
            
            for idx, log in enumerate(logs):
                try:
                    session_id = log.get("session_id", "migrated")
                    timestamp_str = log.get("timestamp", "")
                    user_question = log.get("user_question", "")
                    
                    if not timestamp_str or not user_question:
                        continue
                    
                    timestamp = datetime.fromisoformat(timestamp_str)
                    
                    existing_conv = db.query(Conversation).filter(
                        Conversation.session_id == session_id,
                        Conversation.timestamp == timestamp,
                        Conversation.user_question == user_question
                    ).first()
                    
                    if existing_conv:
                        migrated_indices.append(idx)
                        continue
                    
                    existing_session = db.query(ChatSession).filter(
                        ChatSession.session_id == session_id
                    ).first()
                    
                    if not existing_session:
                        new_session = ChatSession(
                            session_id=session_id,
                            channel=log.get("channel", "web")
                        )
                        db.add(new_session)
                        db.flush()
                    
                    conv = Conversation(
                        session_id=session_id,
                        timestamp=timestamp,
                        user_question=user_question,
                        bot_answer=log.get("bot_answer", ""),
                        safety_flagged=log.get("safety_flagged", False),
                        safety_category=log.get("safety_category")
                    )
                    db.add(conv)
                    migrated += 1
                    migrated_indices.append(idx)
                except Exception as e:
                    print(f"Failed to migrate log entry: {e}")
                    continue
            
            db.commit()
    except Exception as e:
        print(f"Migration failed: {e}")
        return 0
    
    if migrated_indices:
        remaining_logs = [log for idx, log in enumerate(logs) if idx not in migrated_indices]
        save_conversation_logs_to_file(remaining_logs)
        print(f"Cleared {len(migrated_indices)} migrated entries from file logs.")
    
    return migrated
