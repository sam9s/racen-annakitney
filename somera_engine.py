"""
Somera Engine Stub Module

This is a placeholder module for Somera-specific functionality.
Not used in the Anna Kitney wellness chatbot.
"""

def generate_somera_response(message: str, session_id: str = None, **kwargs) -> dict:
    """Stub function for Somera response generation."""
    return {
        "response": "This feature is not available.",
        "sources": []
    }

def generate_somera_response_stream(message: str, session_id: str = None, **kwargs):
    """Stub generator for Somera streaming response."""
    yield {"type": "content", "content": "This feature is not available."}
    yield {"type": "done", "full_response": "This feature is not available.", "sources": []}

def is_booking_request(message: str) -> bool:
    """Stub function to check if message is a booking request."""
    return False

def get_voice_friendly_booking_response() -> str:
    """Stub function for voice-friendly booking response."""
    return "Booking functionality is not available."
