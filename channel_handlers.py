"""
Multi-Channel Message Handlers for JoveHeal

Handles incoming messages from different channels:
- WhatsApp (via Twilio)
- Instagram (via Meta Graph API)
- Web widget (direct API)
"""

import os
import hashlib
import hmac
from datetime import datetime
from typing import Optional, Tuple

from chatbot_engine import generate_response, get_greeting_message
from conversation_logger import log_conversation
from database import is_database_available


class ChannelSession:
    """Manages conversation sessions across channels."""
    
    _sessions = {}
    
    @classmethod
    def get_session(cls, channel: str, user_id: str) -> dict:
        """Get or create a session for a channel/user combination."""
        key = f"{channel}:{user_id}"
        if key not in cls._sessions:
            cls._sessions[key] = {
                "id": f"{channel}_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "channel": channel,
                "user_id": user_id,
                "history": [],
                "created_at": datetime.now()
            }
        return cls._sessions[key]
    
    @classmethod
    def clear_session(cls, channel: str, user_id: str):
        """Clear a session (for /reset commands)."""
        key = f"{channel}:{user_id}"
        if key in cls._sessions:
            del cls._sessions[key]


def process_channel_message(
    channel: str,
    user_id: str,
    message: str,
    user_name: Optional[str] = None
) -> str:
    """
    Process a message from any channel and return a response.
    
    Args:
        channel: Channel identifier (whatsapp, instagram, web)
        user_id: Unique user identifier from the channel
        message: The user's message
        user_name: Optional user name for logging
    
    Returns:
        Response text to send back
    """
    message = message.strip()
    
    if message.lower() in ["/start", "hi", "hello", "hey"]:
        session = ChannelSession.get_session(channel, user_id)
        if len(session["history"]) == 0:
            return get_greeting_message()
    
    if message.lower() == "/reset":
        ChannelSession.clear_session(channel, user_id)
        return "Conversation cleared. How can I help you today?"
    
    session = ChannelSession.get_session(channel, user_id)
    
    result = generate_response(
        user_message=message,
        conversation_history=session["history"]
    )
    
    response = result["response"]
    sources = result.get("sources", [])
    safety_triggered = result.get("safety_triggered", False)
    
    session["history"].append({"role": "user", "content": message})
    session["history"].append({"role": "assistant", "content": response})
    
    if len(session["history"]) > 20:
        session["history"] = session["history"][-20:]
    
    log_conversation(
        session_id=session["id"],
        user_question=message,
        bot_answer=response,
        sources=sources,
        safety_flagged=safety_triggered,
        channel=channel
    )
    
    return response


class TwilioWhatsAppHandler:
    """Handler for WhatsApp messages via Twilio."""
    
    def __init__(self):
        self.account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
        self.auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
        self.whatsapp_number = os.environ.get("TWILIO_WHATSAPP_NUMBER")
    
    def is_configured(self) -> bool:
        """Check if Twilio is properly configured."""
        return all([self.account_sid, self.auth_token, self.whatsapp_number])
    
    def validate_request(self, signature: str, url: str, params: dict) -> bool:
        """Validate incoming Twilio webhook request."""
        if not self.auth_token:
            return False
        
        sorted_params = "".join(f"{k}{params[k]}" for k in sorted(params.keys()))
        data = url + sorted_params
        
        expected_sig = hmac.new(
            self.auth_token.encode(),
            data.encode(),
            hashlib.sha1
        ).digest()
        
        import base64
        expected_b64 = base64.b64encode(expected_sig).decode()
        
        return hmac.compare_digest(signature, expected_b64)
    
    def parse_incoming_message(self, data: dict) -> Tuple[str, str, Optional[str]]:
        """Parse incoming WhatsApp message from Twilio webhook."""
        from_number = data.get("From", "").replace("whatsapp:", "")
        message = data.get("Body", "")
        profile_name = data.get("ProfileName")
        
        return from_number, message, profile_name
    
    def send_message(self, to_number: str, message: str) -> bool:
        """Send a WhatsApp message via Twilio."""
        if not self.is_configured():
            print("Twilio not configured for WhatsApp")
            return False
        
        try:
            from twilio.rest import Client
            client = Client(self.account_sid, self.auth_token)
            
            client.messages.create(
                body=message,
                from_=f"whatsapp:{self.whatsapp_number}",
                to=f"whatsapp:{to_number}"
            )
            return True
        except ImportError:
            print("Twilio library not installed")
            return False
        except Exception as e:
            print(f"Error sending WhatsApp message: {e}")
            return False
    
    def handle_webhook(self, data: dict) -> str:
        """Process incoming WhatsApp webhook and return TwiML response."""
        user_id, message, user_name = self.parse_incoming_message(data)
        
        if not message:
            return self._twiml_response("")
        
        response = process_channel_message(
            channel="whatsapp",
            user_id=user_id,
            message=message,
            user_name=user_name
        )
        
        return self._twiml_response(response)
    
    def _twiml_response(self, message: str) -> str:
        """Generate TwiML response for Twilio."""
        if not message:
            return '<?xml version="1.0" encoding="UTF-8"?><Response></Response>'
        
        escaped_msg = (message
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))
        
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{escaped_msg}</Message>
</Response>'''


class InstagramHandler:
    """Handler for Instagram DM messages via Meta Graph API."""
    
    def __init__(self):
        self.access_token = os.environ.get("INSTAGRAM_ACCESS_TOKEN")
        self.verify_token = os.environ.get("INSTAGRAM_VERIFY_TOKEN")
        self.page_id = os.environ.get("INSTAGRAM_PAGE_ID")
    
    def is_configured(self) -> bool:
        """Check if Instagram is properly configured."""
        return all([self.access_token, self.page_id])
    
    def verify_webhook(self, mode: str, token: str, challenge: str) -> Tuple[bool, str]:
        """Verify webhook subscription from Meta."""
        if mode == "subscribe" and token == self.verify_token:
            return True, challenge
        return False, "Verification failed"
    
    def parse_incoming_message(self, data: dict) -> list:
        """Parse incoming Instagram messages from webhook payload.
        
        Handles both legacy 'messaging' format and current Graph API 'changes' format.
        """
        messages = []
        
        try:
            entries = data.get("entry", [])
            for entry in entries:
                messaging_events = entry.get("messaging", [])
                for event in messaging_events:
                    sender_id = event.get("sender", {}).get("id")
                    message_data = event.get("message", {})
                    text = message_data.get("text")
                    
                    if sender_id and text:
                        messages.append({
                            "user_id": sender_id,
                            "message": text,
                            "timestamp": event.get("timestamp")
                        })
                
                changes = entry.get("changes", [])
                for change in changes:
                    if change.get("field") == "messages":
                        value = change.get("value", {})
                        change_messages = value.get("messages", [])
                        for msg in change_messages:
                            sender_id = msg.get("from")
                            text = msg.get("text", {}).get("body") if isinstance(msg.get("text"), dict) else msg.get("text")
                            
                            if not text and msg.get("type") == "text":
                                text = msg.get("text")
                            
                            if sender_id and text:
                                messages.append({
                                    "user_id": sender_id,
                                    "message": text,
                                    "timestamp": msg.get("timestamp")
                                })
        except Exception as e:
            print(f"Error parsing Instagram message: {e}")
        
        return messages
    
    def send_message(self, user_id: str, message: str) -> bool:
        """Send an Instagram DM via Graph API."""
        if not self.is_configured():
            print("Instagram not configured")
            return False
        
        try:
            import requests
            
            url = f"https://graph.facebook.com/v18.0/{self.page_id}/messages"
            
            payload = {
                "recipient": {"id": user_id},
                "message": {"text": message},
                "messaging_type": "RESPONSE"
            }
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return True
            
        except Exception as e:
            print(f"Error sending Instagram message: {e}")
            return False
    
    def handle_webhook(self, data: dict) -> dict:
        """Process incoming Instagram webhook."""
        messages = self.parse_incoming_message(data)
        responses = []
        
        for msg in messages:
            response = process_channel_message(
                channel="instagram",
                user_id=msg["user_id"],
                message=msg["message"]
            )
            
            self.send_message(msg["user_id"], response)
            responses.append({
                "user_id": msg["user_id"],
                "response": response
            })
        
        return {"processed": len(responses), "responses": responses}


whatsapp_handler = TwilioWhatsAppHandler()
instagram_handler = InstagramHandler()


def get_channel_status() -> dict:
    """Get configuration status of all channels."""
    return {
        "whatsapp": {
            "configured": whatsapp_handler.is_configured(),
            "platform": "Twilio",
            "required_secrets": ["TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_WHATSAPP_NUMBER"]
        },
        "instagram": {
            "configured": instagram_handler.is_configured(),
            "platform": "Meta Graph API",
            "required_secrets": ["INSTAGRAM_ACCESS_TOKEN", "INSTAGRAM_PAGE_ID", "INSTAGRAM_VERIFY_TOKEN"]
        }
    }
