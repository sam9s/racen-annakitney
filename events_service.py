"""
Events Service for Anna Kitney Wellness Chatbot

Fetches event data from Google Calendar via the Express API.
Provides formatted event information for chatbot responses.
"""

import os
import requests
from typing import List, Optional, Dict
from datetime import datetime

EXPRESS_API_URL = os.environ.get("EXPRESS_API_URL", "http://localhost:5000")

class CalendarServiceError(Exception):
    """Raised when the calendar service is unavailable."""
    pass


def get_upcoming_events(limit: int = 10) -> List[Dict]:
    """Fetch upcoming events from the calendar API."""
    try:
        response = requests.get(
            f"{EXPRESS_API_URL}/api/events",
            params={"limit": limit},
            timeout=10
        )
        
        if response.status_code >= 500:
            raise CalendarServiceError("Calendar service temporarily unavailable")
        
        response.raise_for_status()
        data = response.json()
        
        if "error" in data:
            raise CalendarServiceError(data.get("error", "Unknown error"))
        
        return data.get("events", [])
    except requests.exceptions.Timeout:
        print("[Events Service] Request timeout")
        raise CalendarServiceError("Calendar service timeout")
    except requests.exceptions.ConnectionError:
        print("[Events Service] Connection error")
        raise CalendarServiceError("Calendar service unavailable")
    except CalendarServiceError:
        raise
    except Exception as e:
        print(f"[Events Service] Error fetching events: {e}")
        return []


def search_events(query: str) -> List[Dict]:
    """Search events by query string."""
    try:
        response = requests.get(
            f"{EXPRESS_API_URL}/api/events/search",
            params={"q": query},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        return data.get("events", [])
    except Exception as e:
        print(f"[Events Service] Error searching events: {e}")
        return []


def get_event_by_title(title: str) -> Optional[Dict]:
    """Get a specific event by title (fuzzy match)."""
    try:
        response = requests.get(
            f"{EXPRESS_API_URL}/api/events/by-title/{title}",
            timeout=10
        )
        if response.status_code == 404:
            return None
        response.raise_for_status()
        data = response.json()
        return data.get("event")
    except Exception as e:
        print(f"[Events Service] Error fetching event by title: {e}")
        return None


def book_event_to_calendar(event: Dict, calendar_id: str = "primary") -> Dict:
    """Book/add an event to the user's calendar."""
    try:
        response = requests.post(
            f"{EXPRESS_API_URL}/api/events/book",
            json={
                "title": event.get("title"),
                "description": event.get("description", ""),
                "start": event.get("start"),
                "end": event.get("end"),
                "location": event.get("location", "Online"),
                "calendarId": calendar_id
            },
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"[Events Service] Error booking event: {e}")
        return {"success": False, "error": str(e)}


def format_date_friendly(iso_date: str) -> str:
    """Format ISO date string to friendly format."""
    try:
        dt = datetime.fromisoformat(iso_date.replace('Z', '+00:00'))
        return dt.strftime("%A, %B %d, %Y at %I:%M %p")
    except:
        return iso_date


def format_event_for_chat(event: Dict) -> str:
    """Format a single event for chatbot response."""
    title = event.get("title", "Untitled Event")
    start = format_date_friendly(event.get("start", ""))
    end = format_date_friendly(event.get("end", ""))
    location = event.get("location", "Online")
    description = event.get("description", "")
    event_url = event.get("eventPageUrl", "")
    
    response = f"**{title}**\n\n"
    response += f"**When:** {start}\n"
    
    start_date = event.get("start", "")[:10] if event.get("start") else ""
    end_date = event.get("end", "")[:10] if event.get("end") else ""
    if start_date != end_date:
        response += f"**To:** {end}\n"
    
    response += f"\n**Where:** {location}\n\n"
    
    if description:
        short_desc = description[:600] + "..." if len(description) > 600 else description
        short_desc = short_desc.split("REGISTER NOW")[0].strip()
        response += f"**About this event:**\n{short_desc}\n\n"
    
    return response


def format_events_list(events: List[Dict]) -> str:
    """Format multiple events as a list for chatbot response."""
    if not events:
        return "I don't see any upcoming events at the moment. Please check back soon or visit the events page at https://www.annakitney.com/events/ for the latest updates!"
    
    response = "Here are the upcoming events:\n\n"
    
    for i, event in enumerate(events, 1):
        title = event.get("title", "Untitled")
        start = event.get("start", "")
        location = event.get("location", "Online")
        
        try:
            dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
            date_str = dt.strftime("%b %d, %Y")
        except:
            date_str = start[:10] if start else "TBD"
        
        response += f"{i}. **{title}** - {date_str} ({location})\n"
    
    response += "\nWould you like more details about any of these events?"
    
    return response


def is_event_query(message: str) -> bool:
    """Detect if user message is asking about events."""
    message_lower = message.lower()
    
    event_keywords = [
        "event", "events", "workshop", "workshops", "webinar", "webinars",
        "challenge", "live", "session", "sessions", "retreat", "retreats",
        "upcoming", "schedule", "calendar", "when is", "what's happening",
        "identity overflow", "manifestation mastery live", "meditation live",
        "success redefined", "in person", "in-person", "dubai",
        "add to calendar", "book event", "add event", "save event",
        "add to my calendar", "put it in my calendar"
    ]
    
    return any(keyword in message_lower for keyword in event_keywords)


def is_booking_request(message: str) -> bool:
    """Detect if user wants to add event to their calendar."""
    message_lower = message.lower()
    
    booking_keywords = [
        "add to calendar", "add to my calendar", "put in my calendar",
        "save to calendar", "book this event", "book event",
        "add this event", "reminder", "save event", "add it"
    ]
    
    return any(keyword in message_lower for keyword in booking_keywords)


def get_event_context_for_llm(user_message: str, conversation_history: List[Dict] = None) -> str:
    """
    Get event context to inject into the LLM prompt.
    Returns formatted event information based on user's query.
    Handles calendar service errors gracefully.
    """
    try:
        return _get_event_context_internal(user_message, conversation_history)
    except CalendarServiceError as e:
        print(f"[Events Service] Calendar service error: {e}")
        return """
CALENDAR SERVICE NOTICE:
The live event calendar is temporarily unavailable. Please direct the user to:
- Events page: https://www.annakitney.com/events/
- Say: "I'm having trouble loading live event data right now. You can view all upcoming events at https://www.annakitney.com/events/"
"""
    except Exception as e:
        print(f"[Events Service] Unexpected error: {e}")
        return ""


def _get_event_context_internal(user_message: str, conversation_history: List[Dict] = None) -> str:
    """Internal implementation of get_event_context_for_llm."""
    message_lower = user_message.lower()
    
    if is_booking_request(message_lower):
        last_event = None
        if conversation_history:
            for msg in reversed(conversation_history):
                content = msg.get("content", "").lower()
                if "identity overflow" in content:
                    last_event = get_event_by_title("Identity Overflow")
                    break
                elif "manifestation mastery" in content:
                    last_event = get_event_by_title("Manifestation Mastery")
                    break
                elif "meditation" in content or "dubai" in content:
                    last_event = get_event_by_title("Meditation")
                    break
        
        if last_event:
            return f"""
EVENT BOOKING REQUEST:
The user wants to add the following event to their calendar:
{format_event_for_chat(last_event)}

Event URL: {last_event.get('eventPageUrl', '')}

IMPORTANT: Tell the user you can add this event to their calendar. 
Then use: [ADD_TO_CALENDAR:{last_event.get('title')}]
"""
        else:
            events = get_upcoming_events(5)
            return f"""
EVENT BOOKING REQUEST:
The user wants to add an event to their calendar, but no specific event was mentioned.
Here are the upcoming events they might be interested in:

{format_events_list(events)}

Ask them which event they'd like to add to their calendar.
"""
    
    specific_events = [
        ("identity overflow", "Identity Overflow"),
        ("manifestation mastery", "Manifestation Mastery"),
        ("meditation", "Meditation"),
        ("success redefined", "Success Redefined"),
        ("dubai", "Dubai")
    ]
    
    for keyword, search_term in specific_events:
        if keyword in message_lower:
            event = get_event_by_title(search_term)
            if event:
                return f"""
LIVE EVENT INFORMATION (from Anna's calendar):
{format_event_for_chat(event)}

Event Page: {event.get('eventPageUrl', '')}

IMPORTANT INSTRUCTIONS:
1. Share these event details with the user
2. End with: "Would you like me to navigate you to the event page, or add this event to your calendar?"
3. If they want to navigate, use: [NAVIGATE:{event.get('eventPageUrl', '')}]
4. If they want to add to calendar, use: [ADD_TO_CALENDAR:{event.get('title')}]
"""
    
    if any(kw in message_lower for kw in ["events", "upcoming", "what's happening", "schedule", "calendar"]):
        events = get_upcoming_events(10)
        return f"""
LIVE EVENT INFORMATION (from Anna's calendar):
{format_events_list(events)}

Events Page: https://www.annakitney.com/events/

IMPORTANT INSTRUCTIONS:
1. Share this list of upcoming events with the user
2. Ask which event they'd like to know more about
3. If they ask for more details on a specific event, provide the full information
4. You can offer to navigate them to the events page: [NAVIGATE:https://www.annakitney.com/events/]
"""
    
    return ""


def process_calendar_action(response: str, conversation_history: List[Dict] = None) -> tuple:
    """
    Process calendar booking actions in the response.
    Returns (processed_response, action_taken, action_result)
    """
    import re
    
    add_pattern = r'\[ADD_TO_CALENDAR:([^\]]+)\]'
    match = re.search(add_pattern, response)
    
    if match:
        event_title = match.group(1)
        event = get_event_by_title(event_title)
        
        if event:
            result = book_event_to_calendar(event)
            
            cleaned_response = re.sub(add_pattern, '', response).strip()
            
            if "added" in cleaned_response.lower() and event_title.lower() in cleaned_response.lower():
                return cleaned_response, result.get("success", False), result
            
            if result.get("success"):
                action_message = f"I've added **{event_title}** to your calendar! You should see it there now."
                if cleaned_response:
                    return cleaned_response + "\n\n" + action_message, True, result
                return action_message, True, result
            else:
                action_message = f"I wasn't able to add the event to your calendar right now. You can still register at: {event.get('eventPageUrl', '')}"
                if cleaned_response:
                    return cleaned_response + "\n\n" + action_message, False, result
                return action_message, False, result
        else:
            cleaned_response = re.sub(add_pattern, '', response).strip()
            return cleaned_response, False, {"error": "Event not found"}
    
    return response, False, None
