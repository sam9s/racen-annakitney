"""
Events Service for Anna Kitney Wellness Chatbot

Fetches event data from Google Calendar via the Express API.
Provides formatted event information for chatbot responses.

CRITICAL: This service uses FUZZY MATCHING for event lookup.
- No hardcoded event names - works with any event in the database
- Returns event data DIRECTLY without LLM paraphrasing
- Disambiguation prompt when multiple events match
"""

import os
import re
import requests
from typing import List, Optional, Dict, Tuple
from datetime import datetime, timezone, timedelta
from difflib import SequenceMatcher

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

# Fuzzy matching threshold - events scoring above this are considered matches
FUZZY_MATCH_THRESHOLD = 0.4  # 40% similarity minimum
CONFIDENT_MATCH_THRESHOLD = 0.6  # 60%+ means high confidence single match


def fuzzy_match_score(query: str, text: str) -> float:
    """
    Calculate fuzzy match score between query and text.
    Uses multiple strategies for robust matching:
    1. Exact substring match (highest score)
    2. Word overlap ratio
    3. Sequence similarity
    
    Returns score between 0.0 and 1.0
    """
    query_lower = query.lower().strip()
    text_lower = text.lower().strip()
    
    # Exact substring match = perfect score
    if query_lower in text_lower:
        return 1.0
    
    # Check if all query words appear in text
    query_words = set(re.findall(r'\w+', query_lower))
    text_words = set(re.findall(r'\w+', text_lower))
    
    if query_words and query_words.issubset(text_words):
        return 0.95
    
    # Word overlap ratio
    common_words = query_words & text_words
    if query_words:
        word_overlap = len(common_words) / len(query_words)
    else:
        word_overlap = 0
    
    # Sequence similarity (handles typos, partial matches)
    sequence_score = SequenceMatcher(None, query_lower, text_lower).ratio()
    
    # Combined score (weighted average)
    return max(word_overlap * 0.7 + sequence_score * 0.3, sequence_score)


def find_matching_events(query: str, events: List[Dict]) -> List[Tuple[Dict, float]]:
    """
    Find all events that match the query using fuzzy matching.
    Returns list of (event, score) tuples sorted by score descending.
    
    This works with ANY event name - no hardcoding required.
    """
    matches = []
    
    for event in events:
        title = event.get("title", "")
        
        # Calculate match score against title
        score = fuzzy_match_score(query, title)
        
        # Only include events above threshold
        if score >= FUZZY_MATCH_THRESHOLD:
            matches.append((event, score))
    
    # Sort by score descending
    matches.sort(key=lambda x: x[1], reverse=True)
    
    return matches


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


def format_description_for_display(description: str) -> str:
    """
    Format calendar description for better readability in chat:
    - Convert ALL CAPS lines to *italics* (emphasis headings)
    - Mark date/subtitle lines with special {{SUBTITLE:...}} marker for teal styling
    - Add spacing between sections
    - Bold key terms like prices, dates
    - Clean up excessive whitespace
    """
    import re
    
    if not description:
        return ""
    
    lines = description.split('\n')
    formatted_lines = []
    first_content_line = True  # Track first non-empty content line
    
    for line in lines:
        stripped = line.strip()
        
        # Skip empty lines but preserve structure
        if not stripped:
            formatted_lines.append('')
            continue
        
        # Detect event subtitle pattern: "DATE | Description" format
        # This is typically the first content line containing date and pipe separator
        date_subtitle_pattern = r'^(\d{1,2}(?:ST|ND|RD|TH)?[\s\-]+[A-Z]+(?:[\s\-]+\d{4})?)\s*\|\s*(.+)$'
        subtitle_match = re.match(date_subtitle_pattern, stripped, re.IGNORECASE)
        if subtitle_match and first_content_line:
            # Mark as subtitle for special styling in frontend
            formatted_lines.append(f"{{{{SUBTITLE:{stripped}}}}}")
            first_content_line = False
            continue
        
        first_content_line = False
        
        # Detect ALL CAPS lines (headings/emphasis) - at least 3 chars, >70% caps
        if len(stripped) >= 3:
            alpha_chars = [c for c in stripped if c.isalpha()]
            if alpha_chars:
                upper_ratio = sum(1 for c in alpha_chars if c.isupper()) / len(alpha_chars)
                # If >70% uppercase letters, treat as heading - make italic
                # KEEP ORIGINAL CASING to preserve brand names
                if upper_ratio > 0.7 and len(alpha_chars) > 3:
                    formatted_lines.append(f"\n*{stripped}*\n")
                    continue
        
        # Bold price patterns like $150M+, £2,500, $7M+
        line_formatted = re.sub(
            r'([\$£€]\d[\d,\.]*[MKk]?\+?)',
            r'**\1**',
            stripped
        )
        
        # Bold "Pay in Full" type patterns
        line_formatted = re.sub(
            r'(Pay in Full|PAY IN FULL|ENROL NOW|I\'M READY)',
            r'**\1**',
            line_formatted,
            flags=re.IGNORECASE
        )
        
        formatted_lines.append(line_formatted)
    
    # Join and clean up excessive newlines
    result = '\n'.join(formatted_lines)
    result = re.sub(r'\n{4,}', '\n\n\n', result)  # Max 3 newlines
    
    return result.strip()


def format_event_for_chat(event: Dict, include_full_description: bool = True) -> str:
    """
    Format a single event for chatbot response with comprehensive details.
    Includes timezone information and FULL event description from calendar.
    Uses enhanced formatting for better readability.
    """
    title = event.get("title", "Untitled Event")
    start_iso = event.get("start", "")
    end_iso = event.get("end", "")
    timezone = event.get("startTimeZone", "")
    location = event.get("location", "Online")
    description = event.get("description", "")
    event_url = event.get("eventPageUrl", "")
    checkout_url = event.get("checkoutUrl", "")
    
    # Start with title as main heading
    response = f"**{title}**\n\n"
    
    # Event metadata section
    if start_iso and end_iso:
        time_str = format_time_range(start_iso, end_iso, timezone)
        response += f"**When:** {time_str}\n\n"
    elif start_iso:
        response += f"**When:** {format_date_friendly(start_iso, timezone)}\n\n"
    
    response += f"**Where:** {location}\n\n"
    
    # Section divider before description
    response += "---\n\n"
    response += "**About this event:**\n\n"
    
    # Include formatted description
    if description and include_full_description:
        formatted_desc = format_description_for_display(description)
        response += f"{formatted_desc}\n\n"
    elif description:
        short_desc = description[:500] + "..." if len(description) > 500 else description
        response += f"{short_desc}\n\n"
    
    # Section divider before links
    response += "---\n\n"
    
    # Include event page link if available
    if event_url:
        response += f"[**View Event Page**]({event_url})\n\n"
    
    # Include checkout link if available
    if checkout_url:
        response += f"[**Enroll Now**]({checkout_url})\n\n"
    
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


def is_event_query(message: str, conversation_history: list = None) -> bool:
    """
    Detect if user message is asking about events.
    
    Uses THREE strategies:
    1. Keyword matching for common event-related words
    2. Fuzzy matching against actual event titles in the database
    3. Follow-up detection (only when conversation history has an event)
    
    This is DYNAMIC - works with any event name.
    """
    message_lower = message.lower()
    
    # Strategy 1: Common event keywords
    event_keywords = [
        "event", "events", "workshop", "workshops", "webinar", "webinars",
        "challenge", "live", "session", "sessions", "retreat", "retreats",
        "upcoming", "schedule", "calendar", "when is", "what's happening",
        "in person", "in-person", "dubai",
        "add to calendar", "book event", "add event", "save event",
        "add to my calendar", "put it in my calendar"
    ]
    
    if any(keyword in message_lower for keyword in event_keywords):
        return True
    
    # Strategy 2: Check if message fuzzy-matches any event title
    # This makes the detection DYNAMIC - works with any event name
    try:
        all_events = get_upcoming_events(20)
        if all_events:
            matches = find_matching_events(message, all_events)
            if matches and matches[0][1] >= FUZZY_MATCH_THRESHOLD:
                return True
    except Exception:
        pass  # If there's an error, fall back to keyword-only detection
    
    # Strategy 3: Check for follow-up responses (yes, tell me more, etc.)
    # ONLY trigger if there's actually an event in conversation history
    # This prevents misclassifying generic "yes" as an event query
    if is_followup_response(message) and conversation_history:
        # Check if there's an event in history before treating as event query
        try:
            last_event = _find_event_from_history(conversation_history)
            if last_event:
                return True
        except Exception:
            pass
    
    return False


def extract_month_filter(message: str) -> Optional[int]:
    """
    Extract month number from user message if they're asking about a specific month.
    Returns 1-12 for month, or None if no specific month mentioned.
    """
    message_lower = message.lower()
    
    # Month name to number mapping
    month_names = {
        "january": 1, "jan": 1,
        "february": 2, "feb": 2,
        "march": 3, "mar": 3,
        "april": 4, "apr": 4,
        "may": 5,
        "june": 6, "jun": 6,
        "july": 7, "jul": 7,
        "august": 8, "aug": 8,
        "september": 9, "sept": 9, "sep": 9,
        "october": 10, "oct": 10,
        "november": 11, "nov": 11,
        "december": 12, "dec": 12
    }
    
    # Check for month names with context (e.g., "in June", "events in March")
    for month_name, month_num in month_names.items():
        # Match patterns like "in june", "during june", "for june", "june events"
        patterns = [
            rf"\bin\s+{month_name}\b",
            rf"\bduring\s+{month_name}\b",
            rf"\bfor\s+{month_name}\b",
            rf"\b{month_name}\s+events?\b",
            rf"\bevents?\s+in\s+{month_name}\b",
            rf"\bhappening\s+in\s+{month_name}\b",
            rf"\b{month_name}\s+\d{{4}}\b",  # "June 2026"
        ]
        for pattern in patterns:
            if re.search(pattern, message_lower):
                return month_num
    
    return None


def filter_events_by_month(events: List[Dict], month: int) -> List[Dict]:
    """Filter events list to only include events in the specified month."""
    from datetime import datetime
    filtered = []
    for event in events:
        # Check both "start" (transformed format) and "startDate" (raw format)
        start_date = event.get("start") or event.get("startDate", "")
        if start_date:
            try:
                # Parse the date and check month
                if isinstance(start_date, str):
                    # Try ISO format
                    dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
                else:
                    dt = start_date
                if dt.month == month:
                    filtered.append(event)
            except Exception as e:
                print(f"[Events Service] Date parse error for {event.get('title', 'unknown')}: {e}")
    return filtered


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


def is_followup_response(message: str) -> bool:
    """
    Detect if user message is a follow-up response to a previous question.
    This is DYNAMIC - works with any affirmative/selection phrase.
    """
    msg_lower = message.lower().strip()
    
    # Direct affirmatives
    affirmatives = ["yes", "yeah", "yep", "yup", "sure", "ok", "okay", "please", 
                    "definitely", "absolutely", "of course", "go ahead", "sounds good"]
    if msg_lower in affirmatives:
        return True
    
    # Phrases that indicate wanting more info about previously discussed topic
    more_info_phrases = ["tell me more", "more details", "more info", "more information",
                         "i want to know", "i'd like to know", "interested", "sounds interesting",
                         "that one", "this one", "that sounds good", "let's do it"]
    if any(phrase in msg_lower for phrase in more_info_phrases):
        return True
    
    # Ordinal/number selections (for picking from a list)
    # "the first one", "number 1", "1", "option 2", etc.
    ordinal_patterns = [
        r"^[1-9]$",  # Just a number
        r"^#[1-9]$",  # #1, #2, etc.
        r"(first|second|third|fourth|fifth|1st|2nd|3rd|4th|5th)",
        r"(option|number|choice)\s*[1-9]",
        r"the\s*(first|second|third|1st|2nd|3rd)\s*(one)?",
    ]
    for pattern in ordinal_patterns:
        if re.search(pattern, msg_lower):
            return True
    
    return False


def extract_selection_index(message: str) -> Optional[int]:
    """
    Extract which item the user selected from a list.
    Returns 0-based index, or None if not a selection.
    """
    msg_lower = message.lower().strip()
    
    # Direct numbers
    if re.match(r"^[1-9]$", msg_lower):
        return int(msg_lower) - 1
    
    # #1, #2, etc.
    match = re.match(r"^#([1-9])$", msg_lower)
    if match:
        return int(match.group(1)) - 1
    
    # Ordinals
    ordinals = {"first": 0, "1st": 0, "second": 1, "2nd": 1, "third": 2, "3rd": 2,
                "fourth": 3, "4th": 3, "fifth": 4, "5th": 4}
    for ordinal, idx in ordinals.items():
        if ordinal in msg_lower:
            return idx
    
    return None


def _find_event_from_history(conversation_history: List[Dict]) -> Optional[Dict]:
    """
    Find the last discussed event from conversation history.
    Uses FUZZY MATCHING - NO HARDCODED EVENT NAMES.
    
    Searches conversation in reverse order to find the most recently discussed event.
    """
    if not conversation_history:
        return None
    
    # Get all events from the database to match against
    all_events = get_upcoming_events(20)
    if not all_events:
        return None
    
    # Search in reverse order (most recent first)
    for msg in reversed(conversation_history[-10:]):
        content = msg.get("content", "")
        role = msg.get("role", "")
        
        # For user messages, use fuzzy matching to find event mentions
        if role == "user":
            # Use the same fuzzy matching function
            matches = find_matching_events(content, all_events)
            if matches and matches[0][1] >= FUZZY_MATCH_THRESHOLD:
                return matches[0][0]
    
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
    """
    Internal implementation of get_event_context_for_llm.
    
    DYNAMIC ARCHITECTURE:
    1. Check if this is a follow-up response (yes, tell me more, ordinals)
    2. If follow-up, use conversation history to find the last discussed event
    3. Otherwise, use fuzzy matching
    4. If fuzzy matching fails, STILL fall back to conversation history
    
    This works with ANY event name and ANY follow-up phrase - no hardcoding.
    """
    message_lower = user_message.lower()
    
    # ========== FOLLOW-UP DETECTION (DYNAMIC) ==========
    # If user is responding to a previous question about events, use conversation history
    # IMPORTANT: Only trigger for bare affirmatives when there's actually an event in history
    # This prevents misclassifying generic "yes" responses unrelated to events
    if is_followup_response(user_message):
        last_event = _find_event_from_history(conversation_history)
        if last_event:
            print(f"[Events Service] Follow-up detected, using last event: {last_event.get('title')}")
            return _build_single_event_response(last_event)
        # If no event in history, don't treat this as an event follow-up
        # Let the LLM handle it as a general response
    
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
    
    # Check if user is asking about upcoming events list
    if any(kw in message_lower for kw in ["events", "upcoming", "what's happening", "schedule", "calendar"]):
        events = get_upcoming_events(20)  # Get more events to allow for filtering
        
        # Check if user is asking about a specific month
        month_filter = extract_month_filter(user_message)
        if month_filter:
            events = filter_events_by_month(events, month_filter)
            month_names = ["", "January", "February", "March", "April", "May", "June", 
                          "July", "August", "September", "October", "November", "December"]
            month_name = month_names[month_filter]
            
            if not events:
                return f"""
No events found for {month_name}. Here are all upcoming events:

{format_events_list(get_upcoming_events(10))}

Would you like details about any of these events?
"""
            
            events_list = format_events_list(events)
            return f"""
=== VERBATIM EVENT LIST FOR {month_name.upper()} (DO NOT PARAPHRASE) ===
{events_list}
=== END VERBATIM DATA ===

CRITICAL INSTRUCTIONS FOR THIS RESPONSE:
1. Copy the event list above EXACTLY as shown - DO NOT rewrite or paraphrase
2. State clearly that these are the events happening in {month_name}
3. Preserve ALL markdown formatting including **bold**, [links](url), and numbered list format
4. Each event MUST include its clickable link as shown above
5. Keep all dates, times, and locations exactly as formatted
6. After the list, ask which event they'd like to know more about

Events Page: https://www.annakitney.com/events/
"""
        
        # No month filter - show all upcoming events
        events_list = format_events_list(events[:10])
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
    
    # ========== FUZZY MATCHING (DYNAMIC) ==========
    # This works with ANY event name - no hardcoding required
    all_events = get_upcoming_events(20)
    
    if not all_events:
        return ""
    
    # Use fuzzy matching to find relevant events
    matches = find_matching_events(user_message, all_events)
    
    # If fuzzy matching found confident results, use them
    if matches:
        top_match, top_score = matches[0]
        
        # If top match is confident enough, use it directly
        if len(matches) == 1 or top_score >= CONFIDENT_MATCH_THRESHOLD:
            return _build_single_event_response(top_match)
        
        # Multiple matches - check if top is clearly better
        if len(matches) > 1:
            second_score = matches[1][1]
            score_gap = top_score - second_score
            
            if score_gap > 0.2:
                return _build_single_event_response(top_match)
            
            # Close scores - ask for disambiguation
            return _build_disambiguation_response(matches[:5])
    
    # ========== FALLBACK TO CONVERSATION HISTORY ==========
    # If fuzzy matching failed, check if there's a recent event in history
    # This handles cases where user refers to an event indirectly
    last_event = _find_event_from_history(conversation_history)
    if last_event:
        print(f"[Events Service] Fuzzy match failed, falling back to history: {last_event.get('title')}")
        return _build_single_event_response(last_event)
    
    return ""


def _build_single_event_response(event: Dict) -> str:
    """
    Build response for a single matched event.
    Returns formatted event data with DIRECT_EVENT marker for bypassing LLM paraphrasing.
    """
    formatted_event = format_event_for_chat(event)
    event_page = event.get('eventPageUrl', '')
    event_title = event.get('title', '')
    
    # Build follow-up instruction based on available URLs
    if event_page:
        follow_up = f"""

Would you like me to take you to the [event page]({event_page}) to learn more or enroll?"""
    else:
        follow_up = """

Would you like to add this event to your calendar, or do you have any questions about it?"""
    
    # DIRECT_EVENT marker tells chatbot_engine to inject this directly
    return f"""{{{{DIRECT_EVENT}}}}
{formatted_event}{follow_up}
{{{{/DIRECT_EVENT}}}}

EVENT_METADATA:
- Title: {event_title}
- Event Page: {event_page}
- For navigation: [NAVIGATE:{event_page}]
- For calendar: [ADD_TO_CALENDAR:{event_title}]
"""


def _build_disambiguation_response(matches: List[Tuple[Dict, float]]) -> str:
    """
    Build response asking user to clarify which event they mean.
    Used when multiple events match the query with similar scores.
    """
    options = []
    for i, (event, score) in enumerate(matches, 1):
        title = event.get("title", "Unknown")
        start = event.get("start", "")
        location = event.get("location", "Online")
        
        try:
            dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
            date_str = dt.strftime("%b %d, %Y")
        except:
            date_str = "TBD"
        
        options.append(f"{i}. **{title}** - {date_str} ({location})")
    
    options_text = "\n".join(options)
    
    return f"""
DISAMBIGUATION REQUIRED:
Multiple events match what the user is asking about. Ask them to clarify:

{options_text}

INSTRUCTIONS:
1. Tell the user you found multiple events that might match
2. List the options above and ask which one they'd like details about
3. DO NOT make assumptions - wait for user to clarify
"""


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
