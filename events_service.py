"""
Events Service for Anna Kitney Wellness Chatbot

Fetches event data from Google Calendar via the Express API.
Provides formatted event information for chatbot responses.
"""

import os
import requests
from typing import List, Optional, Dict
from datetime import datetime, timezone, timedelta

# Common timezone offsets (hours from UTC)
TIMEZONE_OFFSETS = {
    "Asia/Dubai": 4,
    "Asia/Kolkata": 5.5,
    "Australia/Sydney": 11,  # AEDT (summer)
    "Australia/Melbourne": 11,
    "Europe/London": 0,
    "America/New_York": -5,
    "America/Los_Angeles": -8,
    "UTC": 0,
}

EXPRESS_API_URL = os.environ.get("EXPRESS_API_URL", "http://localhost:5000")

class CalendarServiceError(Exception):
    """Raised when the calendar service is unavailable."""
    pass


def get_upcoming_events(limit: int = 10) -> List[Dict]:
    """Fetch upcoming events from PostgreSQL database (synced from Google Calendar)."""
    try:
        # Use the database endpoint for events (synced from Google Calendar)
        response = requests.get(
            f"{EXPRESS_API_URL}/api/events/db",
            timeout=10
        )
        
        if response.status_code >= 500:
            raise CalendarServiceError("Calendar service temporarily unavailable")
        
        response.raise_for_status()
        data = response.json()
        
        if "error" in data:
            raise CalendarServiceError(data.get("error", "Unknown error"))
        
        events = data.get("events", [])
        
        # Transform database format to match expected format
        transformed = []
        for event in events[:limit]:
            transformed.append({
                "title": event.get("title"),
                "start": event.get("startDate"),
                "end": event.get("endDate"),
                "startTimeZone": event.get("timezone"),
                "location": event.get("location", "Online"),
                "description": event.get("description", ""),
                "eventPageUrl": event.get("eventPageUrl", ""),
                "checkoutUrl": event.get("checkoutUrl", ""),
                "checkoutUrl6Month": event.get("checkoutUrl6Month", ""),
                "checkoutUrl12Month": event.get("checkoutUrl12Month", ""),
                "programPageUrl": event.get("programPageUrl", ""),
            })
        
        return transformed
    except requests.exceptions.Timeout:
        print("[Events Service] Request timeout")
        raise CalendarServiceError("Calendar service timeout")
    except requests.exceptions.ConnectionError:
        print("[Events Service] Connection error")
        raise CalendarServiceError("Calendar service unavailable")
    except CalendarServiceError:
        raise
    except Exception as e:
        print(f"[Events Service] Error fetching events from database: {e}")
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
    """Get a specific event by title from PostgreSQL database (fuzzy match)."""
    try:
        response = requests.get(
            f"{EXPRESS_API_URL}/api/events/db/by-title/{title}",
            timeout=10
        )
        if response.status_code == 404:
            return None
        response.raise_for_status()
        data = response.json()
        
        event = data.get("event")
        if not event:
            return None
        
        # Transform to expected format
        return {
            "title": event.get("title"),
            "start": event.get("startDate"),
            "end": event.get("endDate"),
            "startTimeZone": event.get("timezone"),
            "location": event.get("location", "Online"),
            "description": event.get("description", ""),
            "eventPageUrl": event.get("eventPageUrl", ""),
            "checkoutUrl": event.get("checkoutUrl", ""),
            "checkoutUrl6Month": event.get("checkoutUrl6Month", ""),
            "checkoutUrl12Month": event.get("checkoutUrl12Month", ""),
            "programPageUrl": event.get("programPageUrl", ""),
        }
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


def convert_to_timezone(dt_utc: datetime, timezone_str: str) -> datetime:
    """
    Convert a UTC datetime to the specified timezone.
    Uses the TIMEZONE_OFFSETS mapping for common timezones.
    """
    offset_hours = TIMEZONE_OFFSETS.get(timezone_str, 0)
    offset = timedelta(hours=offset_hours)
    return dt_utc + offset


def get_timezone_display_name(timezone_str: str) -> str:
    """Get a human-readable timezone name."""
    if not timezone_str or timezone_str == 'UTC':
        return ''
    
    # Map common timezone names to display names
    tz_display = {
        "Asia/Dubai": "Dubai",
        "Asia/Kolkata": "IST",
        "Australia/Sydney": "Sydney",
        "Europe/London": "London",
        "America/New_York": "Eastern",
        "America/Los_Angeles": "Pacific",
    }
    
    if timezone_str in tz_display:
        return tz_display[timezone_str]
    
    # Extract city name from timezone string
    if '/' in timezone_str:
        return timezone_str.split('/')[-1].replace('_', ' ')
    
    return timezone_str


def format_date_friendly(iso_date: str, timezone_str: str = None) -> str:
    """
    Format ISO date string to friendly format.
    If timezone is provided, converts the time to that timezone for display.
    """
    try:
        # Parse as UTC
        dt = datetime.fromisoformat(iso_date.replace('Z', '+00:00'))
        
        # Convert to target timezone if provided
        if timezone_str and timezone_str != 'UTC':
            dt = convert_to_timezone(dt, timezone_str)
        
        # Format the date/time
        formatted = dt.strftime("%A, %B %d, %Y at %I:%M %p")
        
        # Add timezone info if available
        tz_name = get_timezone_display_name(timezone_str)
        if tz_name:
            formatted += f" ({tz_name} time)"
        
        return formatted
    except:
        return iso_date


def format_time_range(start_iso: str, end_iso: str, timezone_str: str = None) -> str:
    """
    Format start and end times as a range with timezone.
    Converts UTC times to the specified timezone for display.
    Handles multi-day/multi-week events properly.
    """
    try:
        # Parse as UTC
        start_dt = datetime.fromisoformat(start_iso.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end_iso.replace('Z', '+00:00'))
        
        # Convert to target timezone if provided
        if timezone_str and timezone_str != 'UTC':
            start_dt = convert_to_timezone(start_dt, timezone_str)
            end_dt = convert_to_timezone(end_dt, timezone_str)
        
        # Check if this is a multi-day event
        start_date = start_dt.date()
        end_date = end_dt.date()
        
        if start_date == end_date:
            # Same day event: "Sunday, January 25, 2026 from 11:00 AM - 1:30 PM"
            date_str = start_dt.strftime("%A, %B %d, %Y")
            start_time = start_dt.strftime("%I:%M %p").lstrip('0')
            end_time = end_dt.strftime("%I:%M %p").lstrip('0')
            result = f"{date_str} from {start_time} - {end_time}"
        else:
            # Multi-day event: Include the session time too
            # "March 4 - May 20, 2026 | Sessions at 5:00 PM"
            start_str = start_dt.strftime("%B %d")
            end_str = end_dt.strftime("%B %d, %Y")
            session_time = start_dt.strftime("%I:%M %p").lstrip('0')
            result = f"{start_str} - {end_str} | Sessions at {session_time}"
        
        # Add timezone if provided
        tz_name = get_timezone_display_name(timezone_str)
        if tz_name:
            result += f" ({tz_name} time)"
        
        return result
    except:
        return format_date_friendly(start_iso, timezone_str)


def format_event_for_chat(event: Dict, include_full_description: bool = True) -> str:
    """
    Format a single event for chatbot response with comprehensive details.
    Includes timezone information and FULL event description from calendar.
    NO TRUNCATION - show everything from the calendar.
    """
    title = event.get("title", "Untitled Event")
    start_iso = event.get("start", "")
    end_iso = event.get("end", "")
    timezone = event.get("startTimeZone", "")
    location = event.get("location", "Online")
    description = event.get("description", "")
    event_url = event.get("eventPageUrl", "")
    checkout_url = event.get("checkoutUrl", "")
    
    response = f"**{title}**\n\n"
    
    # Use time range format with timezone (handles multi-day events)
    if start_iso and end_iso:
        time_str = format_time_range(start_iso, end_iso, timezone)
        response += f"**When:** {time_str}\n\n"
    elif start_iso:
        response += f"**When:** {format_date_friendly(start_iso, timezone)}\n\n"
    
    response += f"**Where:** {location}\n\n"
    
    # Include FULL description - no truncation, no CTA removal
    # The full calendar description should be shown to the user
    if description and include_full_description:
        # Only clean up excessive whitespace
        clean_desc = description.replace('\n\n\n', '\n\n').strip()
        response += f"**About this event:**\n\n{clean_desc}\n\n"
    elif description:
        # Short version for listings only
        short_desc = description[:500] + "..." if len(description) > 500 else description
        response += f"**About:** {short_desc}\n\n"
    
    # Include event page link
    if event_url:
        response += f"**Event Page:** [{title}]({event_url})\n\n"
    
    # Include checkout link if available
    if checkout_url:
        response += f"**Enroll Now:** [Register Here]({checkout_url})\n\n"
    
    return response


def format_events_list(events: List[Dict], include_links: bool = True) -> str:
    """
    Format multiple events as a list for chatbot response.
    Each event includes a clickable link to its event page.
    """
    if not events:
        return "I don't see any upcoming events at the moment. Please check back soon or visit the events page at https://www.annakitney.com/events/ for the latest updates!"
    
    response = "Here are the upcoming events:\n\n"
    
    for i, event in enumerate(events, 1):
        title = event.get("title", "Untitled")
        start = event.get("start", "")
        location = event.get("location", "Online")
        event_url = event.get("eventPageUrl", "")
        
        try:
            dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
            date_str = dt.strftime("%b %d, %Y")
        except:
            date_str = start[:10] if start else "TBD"
        
        # Format with clickable link
        if include_links and event_url:
            response += f"{i}. [**{title}**]({event_url}) - {date_str} ({location})\n"
        else:
            response += f"{i}. **{title}** - {date_str} ({location})\n"
    
    response += "\nWould you like more details about any of these events?"
    
    return response


def format_no_events_response(query_context: str = None) -> str:
    """
    Format a response when no events match the query.
    Provides clear messaging and directs to upcoming events.
    """
    if query_context:
        return f"I don't have any events matching '{query_context}' in the calendar. Here are the events I do have coming up - would you like to see those instead? You can also check the events page at https://www.annakitney.com/events/ for the latest updates."
    
    return "I don't see any events matching that timeframe. Would you like to see all upcoming events instead? You can also visit https://www.annakitney.com/events/ for the full calendar."


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


def is_navigation_request(message: str) -> bool:
    """Detect if user wants to navigate to an event page."""
    message_lower = message.lower()
    
    nav_keywords = [
        "navigate", "take me", "go to", "show me the page",
        "event page", "yes please", "yes", "go there",
        "open the page", "visit", "link"
    ]
    
    return any(keyword in message_lower for keyword in nav_keywords)


def _find_event_from_history(conversation_history: List[Dict]) -> Optional[Dict]:
    """
    Find the last discussed event from conversation history.
    Searches for the MOST RECENTLY mentioned specific event title.
    Prioritizes user messages asking about specific events.
    """
    if not conversation_history:
        return None
    
    # Get all events from the database to match against
    all_events = get_upcoming_events(20)
    if not all_events:
        return None
    
    # Search in reverse order (most recent first)
    # Focus on user messages asking about specific events
    for msg in reversed(conversation_history[-10:]):
        content = msg.get("content", "").lower()
        role = msg.get("role", "")
        
        # For user messages, look for specific event mentions
        if role == "user":
            # Match against actual event titles from the database
            for event in all_events:
                title = event.get("title", "").lower()
                # Check for title matches (partial is fine)
                title_words = title.replace("®", "").split()
                # Check if significant words from title are in the message
                if any(word.lower() in content for word in title_words if len(word) > 3):
                    # More specific check - ensure it's really about this event
                    if "coach" in content and "coach" in title.lower():
                        return event
                    if "heal" in content and "heal" in title.lower():
                        return event
                    if "business" in content and "business" in title.lower():
                        return event
                    if "manifestation" in content and "manifestation" in title.lower():
                        return event
                    if "identity" in content and "identity" in title.lower():
                        return event
                    if "overflow" in content and "overflow" in title.lower():
                        return event
                    if "meditation" in content and "meditation" in title.lower():
                        return event
                    if "dubai" in content and "dubai" in title.lower():
                        return event
                    if "success" in content and "success" in title.lower():
                        return event
    
    # Fallback: check assistant messages for the last detailed event response
    for msg in reversed(conversation_history[-10:]):
        content = msg.get("content", "").lower()
        role = msg.get("role", "")
        
        if role == "assistant":
            for event in all_events:
                title = event.get("title", "")
                # Check if this event was discussed in detail (full title mentioned)
                if title.lower() in content:
                    return event
    
    return None


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
    
    # Handle navigation requests (user wants to go to event page)
    if is_navigation_request(message_lower):
        last_event = _find_event_from_history(conversation_history)
        if last_event:
            event_url = last_event.get('eventPageUrl', '')
            return f"""
NAVIGATION REQUEST:
The user wants to navigate to the event page for: {last_event.get('title')}

IMPORTANT: Use this EXACT URL for navigation: {event_url}
Use: [NAVIGATE:{event_url}]

Do NOT generate or guess the URL. Use the exact URL provided above.
"""
    
    if is_booking_request(message_lower):
        last_event = _find_event_from_history(conversation_history)
        
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
    
    # Check if user is asking about a specific event by searching all events from database
    all_events = get_upcoming_events(20)
    
    # Keywords that indicate user is asking about an event
    event_detail_keywords = ["details", "about", "tell me", "what is", "give me", "info", "information"]
    is_asking_for_details = any(kw in message_lower for kw in event_detail_keywords)
    
    # Try to match against actual event titles from database
    for event in all_events:
        title = event.get("title", "")
        title_lower = title.lower().replace("®", "")
        
        # Extract key identifying words from the title
        key_words = []
        if "identity overflow" in title_lower:
            key_words = ["identity", "overflow"]
        elif "manifestation mastery" in title_lower:
            key_words = ["manifestation", "mastery"]
        elif "success redefined" in title_lower or "meditation" in title_lower:
            key_words = ["meditation", "success", "dubai"]
        elif "soulalign" in title_lower and "coach" in title_lower:
            key_words = ["coach", "soulalign coach", "soul align coach"]
        elif "soulalign" in title_lower and "heal" in title_lower:
            key_words = ["heal", "soulalign heal", "soul align heal"]
        elif "soulalign" in title_lower and "business" in title_lower:
            key_words = ["business", "soulalign business", "soul align business"]
        
        # Check if user message mentions this event
        if key_words and any(kw in message_lower for kw in key_words):
            formatted_event = format_event_for_chat(event)
            return f"""
=== VERBATIM EVENT DATA (DO NOT PARAPHRASE) ===
{formatted_event}
=== END VERBATIM DATA ===

CRITICAL INSTRUCTIONS FOR THIS RESPONSE:
1. Copy the event information above EXACTLY as shown - DO NOT rewrite, summarize, or paraphrase
2. Preserve ALL markdown formatting including **bold** text and [links](url)
3. Keep EVERY detail including dates, times, locations, and the full description
4. DO NOT drop any information or shorten the content
5. After the event details, ask: "Would you like me to navigate you to the event page, or add this event to your calendar?"

For navigation use: [NAVIGATE:{event.get('eventPageUrl', '')}]
For calendar add use: [ADD_TO_CALENDAR:{event.get('title')}]
"""
    
    if any(kw in message_lower for kw in ["events", "upcoming", "what's happening", "schedule", "calendar"]):
        events = get_upcoming_events(10)
        events_list = format_events_list(events)
        return f"""
=== VERBATIM EVENT LIST (DO NOT PARAPHRASE) ===
{events_list}
=== END VERBATIM DATA ===

CRITICAL INSTRUCTIONS FOR THIS RESPONSE:
1. Copy the event list above EXACTLY as shown - DO NOT rewrite or paraphrase
2. Preserve ALL markdown formatting including **bold**, [links](url), and numbered list format
3. Each event MUST include its clickable link as shown above
4. Keep all dates, times, and locations exactly as formatted
5. After the list, ask which event they'd like to know more about

Events Page: https://www.annakitney.com/events/
"""
    
    return ""


def fix_navigation_urls(response: str, conversation_history: List[Dict] = None) -> str:
    """
    Post-process response to replace hallucinated event URLs with correct eventPageUrl.
    This ensures 100% accuracy for event page navigation by overriding any LLM-generated URLs.
    """
    import re
    
    # Pattern to match [NAVIGATE:url] where url is an event page
    nav_pattern = r'\[NAVIGATE:(https://www\.annakitney\.com/event/[^\]]+)\]'
    match = re.search(nav_pattern, response)
    
    if match:
        # Find the last discussed event from conversation history
        last_event = _find_event_from_history(conversation_history)
        
        if last_event:
            correct_url = last_event.get('eventPageUrl', '')
            if correct_url:
                # Replace the hallucinated URL with the correct one
                generated_url = match.group(1)
                if generated_url != correct_url:
                    print(f"[Events Service] Correcting URL: {generated_url} -> {correct_url}")
                    response = re.sub(nav_pattern, f'[NAVIGATE:{correct_url}]', response)
    
    return response


def process_calendar_action(response: str, conversation_history: List[Dict] = None) -> tuple:
    """
    Process calendar booking actions in the response.
    Returns (processed_response, action_taken, action_result)
    """
    import re
    
    # First, fix any hallucinated navigation URLs
    response = fix_navigation_urls(response, conversation_history)
    
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
