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
    For multi-day events, shows the full date range.
    """
    if not events:
        return "I don't see any upcoming events at the moment. Please check back soon or visit the events page at https://www.annakitney.com/events/ for the latest updates!"
    
    response = "Here are the upcoming events:\n\n"
    
    for i, event in enumerate(events, 1):
        title = event.get("title", "Untitled")
        start = event.get("start", "")
        end = event.get("end", "")
        location = event.get("location", "Online")
        event_url = event.get("eventPageUrl", "")
        
        try:
            start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end.replace('Z', '+00:00')) if end else None
            
            # Check if this is a multi-day event (more than 1 day difference)
            if end_dt and (end_dt.date() - start_dt.date()).days > 1:
                # Multi-day event - show date range
                start_str = start_dt.strftime("%b %d")
                end_str = end_dt.strftime("%b %d, %Y")
                date_str = f"{start_str} - {end_str}"
            else:
                # Single day or short event
                date_str = start_dt.strftime("%b %d, %Y")
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
            # Follow-up patterns: "How about June?", "What about April?", "And what about May?"
            rf"\bhow\s+about\s+{month_name}\b",
            rf"\bwhat\s+about\s+(?:in\s+)?{month_name}\b",
            rf"\band\s+(?:what\s+about\s+)?(?:in\s+)?{month_name}\b",
            rf"\b{month_name}\?",  # Just "June?" at end
        ]
        for pattern in patterns:
            if re.search(pattern, message_lower):
                return month_num
    
    return None


def parse_event_date(date_str: str) -> Optional[datetime]:
    """Parse an event date string to datetime object."""
    if not date_str:
        return None
    try:
        if isinstance(date_str, str):
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return date_str
    except Exception:
        return None


def extract_specific_date(message: str, default_year: int = 2026) -> Optional[Tuple[int, int, int]]:
    """
    Extract a specific date from user message (e.g., "June 26", "1st of June", "26th June 2026").
    Returns (year, month, day) tuple or None if no specific date found.
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
    
    # Patterns for specific dates
    # IMPORTANT: Use negative lookahead to avoid matching "April 2026" as "April 20" (day from year)
    patterns = [
        # "June 26", "June 26th", "June 26, 2026" - day must NOT be followed by more digits
        r"(january|jan|february|feb|march|mar|april|apr|may|june|jun|july|jul|august|aug|september|sept|sep|october|oct|november|nov|december|dec)\s+(\d{1,2})(?:st|nd|rd|th)?(?!\d)(?:,?\s*(\d{4}))?",
        # "26 June", "26th of June", "26th June 2026"
        r"(\d{1,2})(?:st|nd|rd|th)?\s+(?:of\s+)?(january|jan|february|feb|march|mar|april|apr|may|june|jun|july|jul|august|aug|september|sept|sep|october|oct|november|nov|december|dec)(?:\s+(\d{4}))?",
        # "1st of June", "2nd of march"
        r"(\d{1,2})(?:st|nd|rd|th)\s+of\s+(january|jan|february|feb|march|mar|april|apr|may|june|jun|july|jul|august|aug|september|sept|sep|october|oct|november|nov|december|dec)(?:\s+(\d{4}))?",
    ]
    
    for pattern in patterns:
        match = re.search(pattern, message_lower)
        if match:
            groups = match.groups()
            # Determine which group is month vs day
            if groups[0].isdigit() if groups[0] else False:
                # Day first pattern (e.g., "26 June")
                day = int(groups[0])
                month_str = groups[1]
                year = int(groups[2]) if groups[2] else default_year
            else:
                # Month first pattern (e.g., "June 26")
                month_str = groups[0]
                day = int(groups[1])
                year = int(groups[2]) if len(groups) > 2 and groups[2] else default_year
            
            month = month_names.get(month_str)
            if month and 1 <= day <= 31:
                return (year, month, day)
    
    return None


def is_date_in_event_range(target_date: Tuple[int, int, int], event: Dict) -> bool:
    """
    Check if a specific date falls within an event's date range.
    target_date is (year, month, day) tuple.
    Handles multi-day events like SoulAlign® Heal (June 3 - Sept 30).
    """
    start_str = event.get("start") or event.get("startDate", "")
    end_str = event.get("end") or event.get("endDate", "")
    
    start_dt = parse_event_date(start_str)
    end_dt = parse_event_date(end_str)
    
    if not start_dt:
        return False
    
    # Create target datetime (use noon to avoid timezone issues)
    target_dt = datetime(target_date[0], target_date[1], target_date[2], 12, 0, 0, tzinfo=start_dt.tzinfo)
    
    # If no end date, treat as single-day event (just check start date)
    if not end_dt:
        return start_dt.date() == target_dt.date()
    
    # Check if target date falls within the event's range (inclusive)
    return start_dt.date() <= target_dt.date() <= end_dt.date()


def filter_events_by_specific_date(events: List[Dict], target_date: Tuple[int, int, int]) -> List[Dict]:
    """
    Filter events to include those that are active on a specific date.
    Handles both single-day and multi-day/recurring events.
    """
    return [event for event in events if is_date_in_event_range(target_date, event)]


def is_month_in_event_range(month: int, year: int, event: Dict) -> bool:
    """
    Check if any day of the given month falls within an event's date range.
    Used for month-based filtering of multi-day events.
    """
    import calendar
    
    start_str = event.get("start") or event.get("startDate", "")
    end_str = event.get("end") or event.get("endDate", "")
    
    start_dt = parse_event_date(start_str)
    end_dt = parse_event_date(end_str)
    
    if not start_dt:
        return False
    
    # Get first and last day of the target month
    _, last_day = calendar.monthrange(year, month)
    month_start = datetime(year, month, 1, tzinfo=start_dt.tzinfo)
    month_end = datetime(year, month, last_day, 23, 59, 59, tzinfo=start_dt.tzinfo)
    
    # If no end date, just check if event starts in this month
    if not end_dt:
        return start_dt.month == month and start_dt.year == year
    
    # Check if event range overlaps with the month
    # Event is in month if: event starts before month ends AND event ends after month starts
    return start_dt <= month_end and end_dt >= month_start


def filter_events_by_month(events: List[Dict], month: int, year: int = 2026) -> List[Dict]:
    """
    Filter events list to include events that are active during the specified month.
    Handles both single-day and multi-day events spanning across months.
    """
    filtered = []
    for event in events:
        if is_month_in_event_range(month, year, event):
            filtered.append(event)
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
    
    IMPORTANT: If the message contains a specific date, it's NOT a follow-up,
    it's a fresh date query that should be processed independently.
    """
    msg_lower = message.lower().strip()
    
    # ========== DATE EXCLUSION ==========
    # If the message contains a specific date, it's a NEW query, not a follow-up
    # This prevents "June 1st" from matching "1st" as an ordinal selection
    date_patterns = [
        r"(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2}",  # "June 1", "June 15"
        r"\d{1,2}(st|nd|rd|th)?\s+(of\s+)?(january|february|march|april|may|june|july|august|september|october|november|december)",  # "1st of June"
        r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}",  # 01/15/2026
        r"on\s+(january|february|march|april|may|june|july|august|september|october|november|december)",  # "on June"
        r"any\s+event",  # "any event on..."
        r"events?\s+(on|in|for|during)",  # "event on June 1st"
    ]
    for pattern in date_patterns:
        if re.search(pattern, msg_lower):
            return False  # NOT a follow-up, it's a fresh date query
    
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
    
    # NOTE: Ordinal detection is now handled by IntentRouter
    # Ordinals like "1", "first", "1st" are only treated as selections when:
    # 1. The previous bot message contains a numbered list
    # 2. The message does NOT contain a date pattern
    # This logic is implemented in IntentRouter._check_followup_context()
    
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


def _extract_events_from_history(conversation_history: List[Dict]) -> List[Dict]:
    """
    Extract events that were listed in the previous bot message.
    Used when user selects from a numbered list (e.g., "1", "the first one").
    
    Parses numbered items from the last assistant message and matches them to events.
    Uses multiple pattern strategies to handle various formatting styles.
    """
    if not conversation_history:
        return []
    
    # Find the last assistant message
    last_bot_msg = None
    for msg in reversed(conversation_history):
        if msg.get("role") == "assistant":
            last_bot_msg = msg.get("content", "")
            break
    
    if not last_bot_msg:
        return []
    
    # Get all events to match against
    all_events = get_upcoming_events(20)
    if not all_events:
        return []
    
    # Multiple patterns for numbered lists
    patterns = [
        # "1. Event Name" or "**1. Event Name**" or "1) Event Name"
        r'(?:^|\n)\s*\**\s*([1-9])[.)\]]\s*\**\s*([^\n]+)',
        # "**1.** Event Name" (bold number, text after)
        r'(?:^|\n)\s*\*\*([1-9])\.\*\*\s*([^\n]+)',
        # "1. **Event Name**" (bold event name)
        r'(?:^|\n)\s*([1-9])\.\s*\*\*([^*]+)\*\*',
    ]
    
    # Try each pattern and merge results
    all_matches = {}  # dict to dedupe by number
    for pattern in patterns:
        matches = re.findall(pattern, last_bot_msg)
        for num, item_text in matches:
            num = int(num)
            if num not in all_matches:
                all_matches[num] = item_text.strip()
    
    if not all_matches:
        return []
    
    # Sort by number and match to events
    extracted_events = []
    for num in sorted(all_matches.keys()):
        item_text = all_matches[num]
        
        # Try exact title match first
        matched = False
        for event in all_events:
            event_title = event.get('title', '')
            # Check if event title is in the item text (or vice versa)
            if event_title.lower() in item_text.lower() or item_text.lower().strip() in event_title.lower():
                extracted_events.append(event)
                matched = True
                break
        
        if not matched:
            # Fuzzy matching if exact match fails
            event_matches = find_matching_events(item_text, all_events)
            if event_matches and event_matches[0][1] >= 0.4:
                extracted_events.append(event_matches[0][0])
            else:
                # Add None as placeholder to preserve index alignment
                extracted_events.append(None)
    
    # Filter out None entries but log if there were gaps
    result = [e for e in extracted_events if e is not None]
    if len(result) != len(extracted_events):
        print(f"[Events Service] Warning: Some numbered items couldn't be matched to events", flush=True)
    
    return result


def _find_event_from_history(conversation_history: List[Dict]) -> Optional[Dict]:
    """
    Find the last discussed event from conversation history.
    Uses FUZZY MATCHING - NO HARDCODED EVENT NAMES.
    
    Searches conversation in reverse order to find the most recently discussed event.
    """
    if not conversation_history:
        print("[_find_event_from_history] No conversation history", flush=True)
        return None
    
    # Get all events from the database to match against
    all_events = get_upcoming_events(20)
    if not all_events:
        print("[_find_event_from_history] No events in database", flush=True)
        return None
    
    print(f"[_find_event_from_history] Searching {len(conversation_history)} messages for events", flush=True)
    
    # Search in reverse order (most recent first)
    for msg in reversed(conversation_history[-10:]):
        content = msg.get("content", "")
        role = msg.get("role", "")
        
        # For user messages, use fuzzy matching to find event mentions
        if role == "user":
            # Use the same fuzzy matching function
            matches = find_matching_events(content, all_events)
            if matches and matches[0][1] >= FUZZY_MATCH_THRESHOLD:
                print(f"[_find_event_from_history] Found via user message: {matches[0][0].get('title')}", flush=True)
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
                    print(f"[_find_event_from_history] Found via assistant message: {title}", flush=True)
                    return event
    
    print("[_find_event_from_history] No event found in history", flush=True)
    return None


# Canonical CTAs for progressive event flow - MUST match router detection patterns
STAGE1_CTA = "Would you like more details about this event?"
# Note: Stage-2 CTA includes markdown link, router pattern checks for "take you to the event page"
STAGE2_CTA_TEMPLATE = "Would you like me to take you to the [event page]({url}) to learn more or enroll?"
STAGE2_CTA_NO_URL = "Would you like to add this event to your calendar, or do you have any questions about it?"

# ============================================================================
# PROGRAM CTA CONSTANTS (Single Source of Truth for Program Flow)
# ============================================================================
# These constants define the CTAs for the progressive program disclosure flow.
# The intent_router will derive detection patterns from these programmatically.
# If you change the wording here, the router patterns will automatically update.

PROGRAM_STAGE1_CTA = "Would you like more details about this program?"
# Note: Stage-2 CTA offers navigation FIRST (not enrollment) per user requirement
PROGRAM_STAGE2_CTA_TEMPLATE = "Would you like me to take you to the [program page]({url}) to learn more?"
PROGRAM_STAGE2_CTA_NO_URL = "Would you like to know more, or do you have any questions about this program?"
# Stage-3: Enrollment only comes after navigation or on explicit request
PROGRAM_ENROLLMENT_CTA = "Would you like to know how to enroll in this program?"


def _find_event_for_stage1(event_name: str, conversation_history: List[Dict] = None) -> Optional[Dict]:
    """
    Shared helper to find an event for Stage-1 summary.
    Used by both deterministic and LLM summary functions to ensure consistent lookup.
    
    Returns:
        Event dict if found, None otherwise
    """
    try:
        events = get_upcoming_events(20)
        if not events:
            return None
        
        matches = find_matching_events(event_name, events) if event_name else []
        
        if not matches:
            last_event = _find_event_from_history(conversation_history)
            if last_event:
                return last_event
            return None
        
        return matches[0][0]
    except Exception as e:
        print(f"[Events Service] Error finding event: {e}")
        return None


def _format_event_date_range(event: Dict) -> str:
    """
    Shared helper to format event date range consistently.
    """
    start = event.get("start", "")
    end = event.get("end", "")
    
    try:
        start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end.replace('Z', '+00:00'))
        return f"{start_dt.strftime('%B %d')} - {end_dt.strftime('%B %d, %Y')}"
    except:
        return "Dates TBD"


def get_deterministic_event_summary(event_name: str, conversation_history: List[Dict] = None) -> Optional[str]:
    """
    Get a DETERMINISTIC Stage-1 summary for an event (bypasses LLM).
    
    This is STAGE 1 of the progressive event detail flow:
    - Returns formatted summary with exact CTA for reliable stage detection
    - Uses STAGE1_CTA constant to ensure router patterns stay in sync
    - Uses shared helpers for event lookup and formatting
    
    Args:
        event_name: The event name/title to look up
        conversation_history: Previous conversation messages
    
    Returns:
        Formatted summary string with CTA, or None if not found
    """
    event = _find_event_for_stage1(event_name, conversation_history)
    if not event:
        return None
    
    title = event.get("title", "")
    location = event.get("location", "Online")
    date_str = _format_event_date_range(event)
    
    # Return deterministic summary with exact CTA
    return f"**{title}** is scheduled from {date_str} at {location}.\n\nThis transformative program covers powerful topics designed to create lasting change and help you align with your highest potential.\n\n{STAGE1_CTA}"


def get_event_summary_for_llm(event_name: str, conversation_history: List[Dict] = None) -> str:
    """
    Get event summary context for LLM to generate a friendly summary.
    
    This is STAGE 1 of the progressive event detail flow:
    - Returns basic event info (title, dates, location) 
    - LLM generates a nice summary with STAGE1_CTA
    - NOT the full VERBATIM details - those come in STAGE 2
    - Uses shared helpers for consistent event lookup and formatting
    
    Args:
        event_name: The event name/title to look up
        conversation_history: Previous conversation messages
    
    Returns:
        Context string for LLM to generate summary, or empty string if not found
    """
    event = _find_event_for_stage1(event_name, conversation_history)
    if not event:
        return ""
    
    title = event.get("title", "")
    location = event.get("location", "Online")
    date_str = _format_event_date_range(event)
    
    # Return context for LLM to generate a summary
    # Uses STAGE1_CTA constant to ensure exact CTA matching in router
    return f"""
EVENT SUMMARY CONTEXT (for generating a friendly summary):
The user is asking about this event:

Event Title (use EXACTLY as written): {title}
Dates: {date_str}
Location: {location}

CRITICAL INSTRUCTIONS:
1. You MUST include the EXACT event title "{title}" in your response (verbatim, no abbreviations)
2. Provide a brief, friendly summary of this event (2-3 sentences max)
3. Mention when and where it's happening
4. End with EXACTLY this phrase: "{STAGE1_CTA}"
5. Do NOT include the full event description yet - that comes if they say yes
6. Do NOT offer to take them to the event page yet - that comes after they see full details

REQUIRED response format (must start with exact title):
"{title} is happening from {date_str} at {location}. [Brief 1-2 sentence description]. {STAGE1_CTA}"
"""


def get_event_context_for_llm(user_message: str, conversation_history: List[Dict] = None, selection_index: int = None) -> str:
    """
    Get event context to inject into the LLM prompt.
    Returns formatted event information based on user's query.
    Handles calendar service errors gracefully.
    
    Args:
        user_message: The user's message
        conversation_history: Previous conversation messages
        selection_index: If set, user is selecting from a numbered list (0-based index)
    """
    try:
        return _get_event_context_internal(user_message, conversation_history, selection_index)
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


def _get_event_context_internal(user_message: str, conversation_history: List[Dict] = None, selection_index: int = None) -> str:
    """
    Internal implementation of get_event_context_for_llm.
    
    DYNAMIC ARCHITECTURE:
    1. If selection_index is provided, user is picking from a list shown in conversation
    2. Check if this is a follow-up response (yes, tell me more) - NOTE: Router now handles ordinals
    3. Otherwise, use fuzzy matching
    4. If fuzzy matching fails, STILL fall back to conversation history
    
    This works with ANY event name and ANY follow-up phrase - no hardcoding.
    """
    message_lower = user_message.lower()
    
    # ========== SELECTION FROM LIST (from IntentRouter) ==========
    # If selection_index is provided, user is picking from a numbered list
    # This is now the PRIMARY way to handle selections - router handles ordinal detection
    if selection_index is not None:
        # Find events that were listed in the previous bot message
        events_from_list = _extract_events_from_history(conversation_history)
        if events_from_list and 0 <= selection_index < len(events_from_list):
            selected_event = events_from_list[selection_index]
            print(f"[Events Service] Selected event #{selection_index + 1}: {selected_event.get('title')}", flush=True)
            return _build_single_event_response(selected_event)
        else:
            # Fallback: get upcoming events and use the index
            events = get_upcoming_events(10)
            if events and 0 <= selection_index < len(events):
                selected_event = events[selection_index]
                print(f"[Events Service] Selected event #{selection_index + 1} from upcoming: {selected_event.get('title')}", flush=True)
                return _build_single_event_response(selected_event)
    
    # ========== FOLLOW-UP DETECTION (for non-ordinal follow-ups) ==========
    # NOTE: Ordinal detection is now handled by IntentRouter
    # This only handles bare affirmatives like "yes", "tell me more"
    if is_followup_response(user_message):
        last_event = _find_event_from_history(conversation_history)
        if last_event:
            print(f"[Events Service] Follow-up detected, using last event: {last_event.get('title')}", flush=True)
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
    
    # ========== SPECIFIC DATE QUERY HANDLING ==========
    # Check if user is asking about events on a specific date (e.g., "June 26", "1st of June")
    # This MUST come before the general "events" keyword check
    specific_date = extract_specific_date(user_message)
    if specific_date:
        year, month, day = specific_date
        month_names = ["", "January", "February", "March", "April", "May", "June", 
                      "July", "August", "September", "October", "November", "December"]
        date_str = f"{month_names[month]} {day}, {year}"
        
        events = get_upcoming_events(20)
        matching_events = filter_events_by_specific_date(events, specific_date)
        
        if matching_events:
            if len(matching_events) == 1:
                # Single event on this date - use SUMMARY for Stage-1 progressive disclosure
                event = matching_events[0]
                return _build_event_summary_response(event)
            else:
                # Multiple events on this date
                events_list = format_events_list(matching_events)
                return f"""
=== VERBATIM EVENT LIST FOR {date_str.upper()} (DO NOT PARAPHRASE) ===
{events_list}
=== END VERBATIM DATA ===

CRITICAL: These events are happening on/include {date_str}.
Copy the event list EXACTLY as shown above.
Ask which event they'd like to know more about.
"""
        else:
            # No events on this specific date - return with DIRECT marker to bypass LLM
            # This prevents fuzzy matching or RAG from overriding the "no events" response
            return f"""
{{{{DIRECT_EVENT}}}}
I don't have any events scheduled for {date_str}.

Here are all upcoming events you might be interested in:

{format_events_list(events[:10])}
{{{{/DIRECT_EVENT}}}}
"""
    
    # ========== MONTH FILTER CHECK (MUST BE BEFORE EVENT KEYWORD CHECK) ==========
    # This handles queries like "What about in May?" or "events in April"
    # Must run first so month queries aren't caught by fuzzy matching or history fallback
    month_filter = extract_month_filter(user_message)
    if month_filter:
        events = get_upcoming_events(20)
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
    
    # Check if user is asking about upcoming events list
    # Include both singular "event" and plural "events", plus common phrasings
    if any(kw in message_lower for kw in ["event", "events", "upcoming", "what's happening", "happening in", "schedule", "calendar"]):
        events = get_upcoming_events(20)  # Get more events to allow for filtering
        
        # Check if user is asking about a specific program's events
        # E.g., "Are there any events happening for SoulAlign Business Course?"
        # Use fuzzy matching against full titles, not keyword buckets
        program_keywords = [
            "soulalign business", "soul align business", "business course",
            "soulalign heal", "soul align heal",
            "soulalign coach", "soul align coach", 
            "soulalign manifestation", "soul align manifestation", "manifestation mastery",
            "identity overflow", "identity switch",
            "ascend collective", "elite private", "vip day",
        ]
        
        for keyword in program_keywords:
            if keyword in message_lower:
                # Use fuzzy matching to find the BEST matching event
                # Be strict: require confidence OR clear gap, else disambiguate
                matches = find_matching_events(keyword, events)
                
                if matches:
                    top_match, top_score = matches[0]
                    
                    # CONFIDENT: High score means we're sure this is the right event
                    # Use SUMMARY for Stage-1 progressive disclosure (not full details)
                    if top_score >= CONFIDENT_MATCH_THRESHOLD:
                        return _build_event_summary_response(top_match)
                    
                    # SINGLE MATCH: Only one result, but require minimum confidence
                    if len(matches) == 1:
                        if top_score >= FUZZY_MATCH_THRESHOLD:
                            return _build_event_summary_response(top_match)
                        # Too low confidence even for single match - fall through
                    
                    # MULTIPLE MATCHES: Check if top is clearly better with significant gap
                    if len(matches) > 1:
                        second_score = matches[1][1]
                        if top_score >= FUZZY_MATCH_THRESHOLD and top_score - second_score > 0.2:
                            return _build_event_summary_response(top_match)
                    
                    # INSUFFICIENT CONFIDENCE: Ask for clarification
                    return _build_disambiguation_response(matches[:3])
                break  # Only use first matching keyword
        
        # Note: Month filter already handled above, no need to check again here
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
    
    # ========== LOCATION QUERY HANDLING ==========
    # Handle queries like "Where is the Dubai event held?" or "Is there an event in Dubai?"
    # Search for location keywords in both event titles AND location fields
    # ALL patterns are DYNAMIC - they capture any location word, not hardcoded cities
    location_patterns = [
        r'\bwhere\s+(?:is|are)\s+(?:the\s+)?(\w+)\s+event',
        r'\b(\w+)\s+event\s+location',
        r'\blocation\s+(?:of|for)\s+(?:the\s+)?(\w+)',
        r'\bwhere\s+(?:does|will)\s+(?:the\s+)?(\w+)\s+(?:take\s+place|happen|be\s+held)',
        # Dynamic "is there an event in [location]" patterns
        r'\b(?:is\s+there|are\s+there)\s+(?:an?y?\s+)?(?:events?|workshops?|sessions?)\s+(?:in|at)\s+(\w+)',
        r'\bevents?\s+(?:in|at)\s+(\w+)\b',  # "events in [location]" - fully dynamic
        r'\b(\w+)\s+events?\b',  # "[location] events" - fully dynamic (will match many things, last resort)
    ]
    
    for pattern in location_patterns:
        match = re.search(pattern, message_lower)
        if match:
            location_keyword = match.group(1).lower()
            all_events = get_upcoming_events(20)
            
            # Search for events with this keyword in title OR location
            matching_events = []
            for event in all_events:
                title = event.get("title", "").lower()
                location = event.get("location", "").lower()
                if location_keyword in title or location_keyword in location:
                    matching_events.append(event)
            
            if matching_events:
                if len(matching_events) == 1:
                    # Use SUMMARY for Stage-1 progressive disclosure
                    return _build_event_summary_response(matching_events[0])
                else:
                    return _build_disambiguation_response([(e, 1.0) for e in matching_events[:5]])
            break  # Only try first matching pattern
    
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
        
        # If top match is confident enough, use SUMMARY for Stage-1
        if len(matches) == 1 or top_score >= CONFIDENT_MATCH_THRESHOLD:
            return _build_event_summary_response(top_match)
        
        # Multiple matches - check if top is clearly better
        if len(matches) > 1:
            second_score = matches[1][1]
            score_gap = top_score - second_score
            
            if score_gap > 0.2:
                return _build_event_summary_response(top_match)
            
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


def _build_event_summary_response(event: Dict) -> str:
    """
    Build Stage-1 SUMMARY response for a single matched event.
    Returns brief event summary with STAGE1_CTA asking if they want more details.
    
    This is the FIRST stage of progressive disclosure:
    - Stage 1: Summary + "Would you like more details?" (this function)
    - Stage 2: Full VERBATIM details + navigation CTA (_build_single_event_response)
    """
    title = event.get('title', 'Event')
    start_date = event.get('startDate', '')
    location = event.get('location', '')
    event_page = event.get('eventPageUrl', '')
    
    # Format date nicely
    date_str = ""
    if start_date:
        try:
            dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            date_str = dt.strftime('%B %d, %Y')
        except:
            date_str = start_date
    
    # Build concise summary
    summary_parts = [f"**{title}**"]
    if date_str:
        summary_parts.append(f"Date: {date_str}")
    if location:
        # Truncate very long locations
        loc_short = location.split(',')[0] if ',' in location else location
        summary_parts.append(f"Location: {loc_short}")
    
    summary = "\n".join(summary_parts)
    
    # Add STAGE1_CTA for progressive disclosure
    follow_up = "\n\n" + STAGE1_CTA
    
    # Return WITHOUT DIRECT_EVENT marker - let LLM add a friendly intro
    return f"""
=== EVENT SUMMARY ===
{summary}
{follow_up}

EVENT_METADATA (for router tracking):
- Title: {event.get('title', '')}
- Event Page: {event_page}
- Stage: SUMMARY_SHOWN
"""


def _build_single_event_response(event: Dict) -> str:
    """
    Build Stage-2 FULL DETAILS response for a single matched event.
    Returns formatted event data with DIRECT_EVENT marker for bypassing LLM paraphrasing.
    
    Uses canonical STAGE2_CTA_TEMPLATE/STAGE2_CTA_NO_URL to ensure router pattern matching.
    This is called AFTER user confirms they want more details from Stage-1.
    """
    formatted_event = format_event_for_chat(event)
    event_page = event.get('eventPageUrl', '')
    event_title = event.get('title', '')
    
    # Build follow-up using canonical CTA templates for router pattern matching
    if event_page:
        follow_up = "\n\n" + STAGE2_CTA_TEMPLATE.format(url=event_page)
    else:
        follow_up = "\n\n" + STAGE2_CTA_NO_URL
    
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
