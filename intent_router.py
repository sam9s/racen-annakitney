"""
Intent Router for Anna Kitney Wellness Chatbot

This module implements a scalable intent-first architecture that:
1. Classifies user queries BEFORE hitting any database
2. Routes to appropriate handlers (Event, Knowledge, Hybrid)
3. Triggers clarification when intent is ambiguous
4. Is fully data-driven - no hardcoded program/event names

ARCHITECTURE:
User Query → IntentRouter.classify() → Handler
    ├── EventIntent (confidence > threshold) → SQL only (PostgreSQL)
    ├── KnowledgeIntent (confidence > threshold) → RAG only (ChromaDB)
    ├── HybridIntent → Both with priority rules
    └── AmbiguousIntent (low confidence) → Ask clarifying question

FUTURE EXTENSIBILITY:
Adding new intents (booking, email, payment) is simple:
1. Add new IntentType enum value
2. Add detection logic in classify()
3. Add handler in chatbot_engine.py
"""

import re
from enum import Enum
from typing import Optional, Tuple, List, Dict
from dataclasses import dataclass
from datetime import datetime

# Import canonical CTA patterns from events_service to ensure router detection stays in sync
# This is the single source of truth - if CTAs change in events_service, router automatically adapts
def _cta_to_regex(cta_text: str) -> str:
    """
    Convert a CTA string to a flexible regex pattern.
    Handles markdown links, whitespace variations, and punctuation.
    
    Strategy: 
    1. Find markdown link, split text into before/after/link_text segments
    2. Escape each literal segment separately
    3. Build regex by concatenating escaped literals with regex patterns
    
    Args:
        cta_text: The CTA string to convert
    
    Returns:
        Regex pattern string derived from the CTA
    """
    text = cta_text.lower().rstrip("?!.")
    
    # Check for markdown link: [text](url)
    markdown_match = re.search(r'\[([^\]]+)\]\([^)]*\)', text)
    
    if markdown_match:
        # Split into parts: before, link_text, after
        before = text[:markdown_match.start()]
        link_text = markdown_match.group(1)
        after = text[markdown_match.end():]
        
        # Escape and make whitespace flexible for each literal part
        def escape_and_flex(s):
            escaped = re.escape(s)
            return escaped.replace(r'\ ', r'\s+')
        
        before_regex = escape_and_flex(before)
        after_regex = escape_and_flex(after)
        link_text_regex = escape_and_flex(link_text)
        
        # Build markdown pattern: optional [, link text, optional ], optional (url)
        markdown_pattern = r'\[?' + link_text_regex + r'\]?\s*(?:\([^)]*\))?'
        
        # Combine: before + markdown + after + optional punctuation
        result = before_regex + markdown_pattern + after_regex + r'[\?\!\.]?'
    else:
        # No markdown - just escape and make whitespace flexible
        escaped = re.escape(text)
        result = escaped.replace(r'\ ', r'\s+') + r'[\?\!\.]?'
    
    return result


def _get_cta_regex_patterns():
    """
    Get REGEX patterns derived directly from canonical CTAs in events_service.
    Lazy import to avoid circular dependency issues.
    
    ALL patterns are programmatically generated from the source CTAs using _cta_to_regex().
    This ensures any changes to CTA constants automatically update detection patterns.
    """
    try:
        from events_service import (
            STAGE1_CTA, STAGE2_CTA_TEMPLATE, STAGE2_CTA_NO_URL,
            PROGRAM_STAGE1_CTA, PROGRAM_STAGE2_CTA_TEMPLATE, PROGRAM_STAGE2_CTA_NO_URL,
            PROGRAM_ENROLLMENT_CTA
        )
        
        return {
            # Event CTAs
            "stage1_regex": _cta_to_regex(STAGE1_CTA),
            "stage2_url_regex": _cta_to_regex(STAGE2_CTA_TEMPLATE),
            "stage2_no_url_regex": _cta_to_regex(STAGE2_CTA_NO_URL),
            # Program CTAs (parallel flow)
            "program_stage1_regex": _cta_to_regex(PROGRAM_STAGE1_CTA),
            "program_stage2_url_regex": _cta_to_regex(PROGRAM_STAGE2_CTA_TEMPLATE),
            "program_stage2_no_url_regex": _cta_to_regex(PROGRAM_STAGE2_CTA_NO_URL),
            "program_enrollment_regex": _cta_to_regex(PROGRAM_ENROLLMENT_CTA),
        }
    except ImportError:
        # Fallback only if events_service import fails
        return {
            "stage1_regex": r"would\s+you\s+like\s+more\s+details\s+about\s+this\s+event[\?\!\.]?",
            "stage2_url_regex": r"would\s+you\s+like\s+me\s+to\s+take\s+you\s+to\s+the\s+\[?event\s+page\]?\s*(?:\([^)]*\))?\s+to\s+learn\s+more\s+or\s+enroll[\?\!\.]?",
            "stage2_no_url_regex": r"would\s+you\s+like\s+to\s+add\s+this\s+event\s+to\s+your\s+calendar[\?\!\.]?",
            "program_stage1_regex": r"would\s+you\s+like\s+more\s+details\s+about\s+this\s+program[\?\!\.]?",
            "program_stage2_url_regex": r"would\s+you\s+like\s+me\s+to\s+take\s+you\s+to\s+the\s+\[?program\s+page\]?\s*(?:\([^)]*\))?\s+to\s+learn\s+more[\?\!\.]?",
            "program_stage2_no_url_regex": r"would\s+you\s+like\s+to\s+know\s+more[\?\!\.]?",
            "program_enrollment_regex": r"would\s+you\s+like\s+to\s+know\s+how\s+to\s+enroll[\?\!\.]?",
        }


class IntentType(Enum):
    """Types of user intents. Extensible for future features."""
    EVENT = "event"              # Schedule, dates, registration
    KNOWLEDGE = "knowledge"      # Program details, pricing, what's included
    HYBRID = "hybrid"            # Could be either (e.g., "SoulAlign Heal")
    CLARIFICATION = "clarification"  # Need to ask user for clarity
    GREETING = "greeting"        # Hi, hello, etc.
    BOOKING = "booking"          # Future: Book an event
    FOLLOWUP_SELECT = "followup_select"  # User selecting from a numbered list
    FOLLOWUP_CONFIRM = "followup_confirm"  # User confirming (yes/tell me more)
    EVENT_DETAIL_REQUEST = "event_detail_request"  # User asking about specific event after listing
    EVENT_NAVIGATE = "event_navigate"  # User confirming navigation to event page
    # Program flow intents (parallel to event flow)
    PROGRAM_DETAIL_REQUEST = "program_detail_request"  # User wants more details about program
    PROGRAM_NAVIGATE = "program_navigate"  # User confirming navigation to program page
    PROGRAM_ENROLLMENT = "program_enrollment"  # User explicitly asking about enrollment
    OTHER = "other"              # Catch-all


# Event follow-up stages (tracked in conversation)
class EventFollowupStage:
    """Stages for progressive event detail disclosure."""
    NONE = "none"                    # No event follow-up in progress
    LISTING_SHOWN = "listing_shown"  # Bot showed event listing
    SUMMARY_SHOWN = "summary_shown"  # Bot showed event summary, offered "more details?"
    DETAILS_SHOWN = "details_shown"  # Bot showed full details, offered "event page?"


class ProgramFollowupStage:
    """Stages for progressive program detail disclosure (parallel to EventFollowupStage)."""
    NONE = "none"                    # No program follow-up in progress
    SUMMARY_SHOWN = "summary_shown"  # Bot showed program summary, offered "more details?"
    DETAILS_SHOWN = "details_shown"  # Bot showed full details, offered "navigate to page?"
    NAVIGATE_OFFERED = "navigate_offered"  # Bot offered navigation, waiting for response


# Patterns for detecting numbered lists in bot messages
NUMBERED_LIST_PATTERNS = [
    r'\b1\.\s+\*?\*?\[?\*?\*?[A-Za-z]',  # "1. SoulAlign" or "1. **SoulAlign**" or "1. [**SoulAlign"
    r'\b1\)\s+[A-Za-z]',  # "1) SoulAlign"
    r'(?:here are|these are|following).*(?:options|programs|events|choices)',  # List introduction
]

# Patterns for bare ordinal selections (user picking from list)
ORDINAL_SELECTION_PATTERNS = [
    r'^[1-9]$',  # Just a number
    r'^#[1-9]$',  # #1, #2, etc.
    r'^(?:the\s+)?(?:first|second|third|fourth|fifth|1st|2nd|3rd|4th|5th)(?:\s+one)?$',  # "the first one"
    r'^(?:option|number|choice)\s*[1-9]$',  # "option 1"
]

# Bare affirmatives for follow-up confirmation
AFFIRMATIVE_PATTERNS = [
    r'^(?:yes|yeah|yep|yup|sure|ok|okay|please|definitely|absolutely|of course|go ahead|sounds good)$',
    r'^(?:tell me more|more details|more info|i\'m interested|that sounds good)$',
]


@dataclass
class IntentResult:
    """Result of intent classification."""
    intent: IntentType
    confidence: float  # 0.0 to 1.0
    slots: Dict  # Extracted entities (date, program name, etc.)
    clarification_question: Optional[str] = None
    reasoning: str = ""  # For debugging/telemetry


# Confidence thresholds
HIGH_CONFIDENCE = 0.8
MEDIUM_CONFIDENCE = 0.6
LOW_CONFIDENCE = 0.4

# Date-related patterns (indicates EVENT intent)
DATE_PATTERNS = [
    r'\b\d{1,2}(?:st|nd|rd|th)?\s+(?:of\s+)?(?:january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec)\b',
    r'\b(?:january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec)\s+\d{1,2}(?:st|nd|rd|th)?\b',
    r'\b(?:january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec)\s+\d{4}\b',
    r'\b\d{1,2}/\d{1,2}/\d{2,4}\b',
    r'\b\d{4}-\d{2}-\d{2}\b',
]

# Time-related patterns (indicates EVENT intent)
TIME_PATTERNS = [
    r'\bwhen\s+is\b',
    r'\bwhat\s+time\b',
    r'\bwhat\s+date\b',
    r'\bupcoming\b',
    r'\bschedule\b',
    r'\bcalendar\b',
    r'\bnext\s+(?:week|month|year)\b',
    r'\bthis\s+(?:week|month|year)\b',
    # Month-based event queries (flexible patterns)
    r'\bevents?\s+(?:\w+\s+)*(?:in|for|during)\s+(?:january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec)\b',
    r'\b(?:january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec)\s+events?\b',
    r'\bhappening\s+in\s+(?:january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec)\b',
    r'\bin\s+(?:january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec)\b.*\bevents?\b',
    # Generic event queries
    r'\bwhat\s+(?:events?|workshops?|sessions?)\b',
    r'\bany\s+(?:events?|workshops?|sessions?)\b',
    r'\blist\s+(?:of\s+)?(?:events?|workshops?|sessions?)\b',
    r'\bshow\s+(?:me\s+)?(?:events?|workshops?|sessions?)\b',
    r'\bhave\s+any\s+events?\b',
    r'\bdo\s+you\s+have\s+(?:any\s+)?(?:events?|workshops?|sessions?)\b',
    r'\bgive\s+me\s+(?:the\s+)?events?\b',
    # Location queries (about events)
    r'\bwhere\s+is\s+(?:the\s+)?(?:\w+\s+)+(?:held|happening|taking\s+place|located)\b',
    r'\blocation\s+(?:of|for)\b',
    r'\bwhere\s+(?:does|will)\s+(?:the\s+)?\w+\s+(?:take\s+place|happen|be\s+held)\b',
    # "Is there an event in [location]?" patterns - FULLY DYNAMIC (no hardcoded locations)
    r'\b(?:is\s+there|are\s+there)\s+(?:an?y?\s+)?(?:events?|workshops?|sessions?)\s+(?:in|at)\s+\w+',
    r'\bevents?\s+(?:in|at)\s+\w+\b',  # "events in [any location]"
]

# Event action patterns (indicates EVENT intent)
EVENT_ACTION_PATTERNS = [
    r'\bregister\b',
    r'\bsign\s*up\b',
    r'\bjoin\b',
    r'\battend\b',
    r'\bbook\s*(?:a|the|this)?\s*(?:event|session|workshop)?\b',
    r'\badd\s+to\s+(?:my\s+)?calendar\b',
    r'\bsave\s+(?:the\s+)?event\b',
    r'\bin\s*-?\s*person\b',
    r'\blive\s+(?:event|session|workshop)\b',
    r'\bretreat\b',
]

# Knowledge/Program patterns (indicates KNOWLEDGE intent)
KNOWLEDGE_PATTERNS = [
    r'\bhow\s+much\b',
    r'\bwhat\s+is\s+(?:the\s+)?(?:cost|price|investment)\b',
    r'\bpric(?:e|ing)\b',
    r'\bcost\b',
    r'\binvestment\b',
    r'\bwhat\s+(?:is|are)\s+(?:the\s+)?(?:program|course)\b',
    r'\bwhat\s+does\s+(?:it|the\s+program)\s+include\b',
    r'\bwhat\'?s?\s+included\b',
    r'\btell\s+me\s+about\s+(?:the\s+)?(?:program|course)\b',
    r'\blearn\s+(?:more\s+)?about\b',
    r'\bdetails\s+(?:about|of)\b',
    r'\bbenefits\b',
    r'\bfor\s+whom\b',
    r'\bwho\s+is\s+(?:it|this)\s+for\b',
    r'\btransformation\b',
    r'\bresults\b',
    r'\btestimonial\b',
    r'\breview\b',
]

# Greeting patterns
GREETING_PATTERNS = [
    r'^(?:hi|hello|hey|good\s+(?:morning|afternoon|evening)|howdy|greetings)\b',
    r'^(?:what\'?s?\s+up|sup)\b',
]

# Explicit program keywords - when present, prioritize PROGRAM intent over EVENT
# even when event and program names overlap
PROGRAM_KEYWORDS = [
    r'\bprogram\b',
    r'\bcourse\b',
    r'\bmembership\b',
    r'\btraining\b',
    r'\bcertification\b',
    r'\bself[- ]?paced\b',
    r'\bonline\s+(?:course|program)\b',
]


class IntentRouter:
    """
    Routes user queries to appropriate handlers based on intent classification.
    
    This is the FIRST thing called before any database queries.
    All detection is data-driven - no hardcoded program/event names.
    """
    
    def __init__(self, event_titles: List[str] = None, program_names: List[str] = None):
        """
        Initialize router with optional pre-loaded data.
        
        Args:
            event_titles: List of current event titles from database
            program_names: List of program names from knowledge base
        
        If not provided, router will fetch dynamically when needed.
        """
        self._event_titles = event_titles or []
        self._program_names = program_names or []
        self._last_refresh = None
    
    def set_event_titles(self, titles: List[str]):
        """Update event titles (call after calendar sync)."""
        self._event_titles = titles
        self._last_refresh = datetime.now()
    
    def set_program_names(self, names: List[str]):
        """Update program names (call after knowledge base update)."""
        self._program_names = names
    
    def classify(
        self,
        message: str,
        conversation_history: List[Dict] = None
    ) -> IntentResult:
        """
        Classify user intent BEFORE any database queries.
        
        This is the main entry point. Called at the very start of processing.
        
        Returns IntentResult with:
        - intent: The classified intent type
        - confidence: How confident we are (0.0-1.0)
        - slots: Extracted entities (date, name, etc.)
        - clarification_question: If ambiguous, the question to ask
        """
        message_lower = message.lower().strip()
        slots = {}
        
        # Check for greeting first (simple pattern)
        if self._is_greeting(message_lower):
            return IntentResult(
                intent=IntentType.GREETING,
                confidence=1.0,
                slots={},
                reasoning="Greeting pattern detected"
            )
        
        # ========== FOLLOW-UP DETECTION (PRIORITY CHECK) ==========
        # Check for follow-up BEFORE other intent detection
        # This is the SINGLE decision point - downstream handlers should NOT re-check
        # IMPORTANT: Only applies if message does NOT contain a date (date queries are new queries)
        has_date_early, _ = self._extract_date_signals(message_lower)
        if not has_date_early:
            followup_result = self._check_followup_context(message, conversation_history or [])
            if followup_result:
                return followup_result
        
        # Check for explicit date/time (strong EVENT signal)
        has_date, date_info = self._extract_date_signals(message_lower)
        if has_date:
            slots["date_info"] = date_info
        
        # Check for event action words
        has_event_action = self._has_event_action(message_lower)
        
        # Check for knowledge/program patterns
        has_knowledge_pattern = self._has_knowledge_pattern(message_lower)
        
        # Check for time-related patterns
        has_time_pattern = self._has_time_pattern(message_lower)
        
        # Check if message matches known event titles
        event_match, event_score = self._match_event_title(message)
        if event_match:
            slots["matched_event"] = event_match
        
        # Check if message matches known program names
        program_match, program_score = self._match_program_name(message)
        if program_match:
            slots["matched_program"] = program_match
        
        # Decision logic
        
        # Case 1: Explicit date + no knowledge patterns = EVENT (high confidence)
        if has_date and not has_knowledge_pattern:
            return IntentResult(
                intent=IntentType.EVENT,
                confidence=HIGH_CONFIDENCE,
                slots=slots,
                reasoning="Explicit date detected, no knowledge patterns"
            )
        
        # Case 2: Event action words = EVENT (high confidence)
        if has_event_action:
            return IntentResult(
                intent=IntentType.EVENT,
                confidence=HIGH_CONFIDENCE,
                slots=slots,
                reasoning="Event action pattern detected (register, book, attend, etc.)"
            )
        
        # Case 3: Time pattern without date = EVENT (medium confidence)
        if has_time_pattern and not has_knowledge_pattern:
            return IntentResult(
                intent=IntentType.EVENT,
                confidence=MEDIUM_CONFIDENCE,
                slots=slots,
                reasoning="Time-related pattern detected"
            )
        
        # Case 4: Knowledge pattern + no date/event signals = KNOWLEDGE (high confidence)
        if has_knowledge_pattern and not has_date and not has_event_action and not has_time_pattern:
            return IntentResult(
                intent=IntentType.KNOWLEDGE,
                confidence=HIGH_CONFIDENCE,
                slots=slots,
                reasoning="Knowledge pattern detected (price, cost, details, etc.)"
            )
        
        # Case 5: Name matches BOTH event and program with HIGH scores = CLARIFICATION
        if event_match and program_match and event_score > 0.7 and program_score > 0.7:
            # Same name exists in both with high confidence - need clarification
            if not has_date and not has_event_action and not has_knowledge_pattern:
                return IntentResult(
                    intent=IntentType.CLARIFICATION,
                    confidence=LOW_CONFIDENCE,
                    slots=slots,
                    clarification_question=self._generate_clarification(event_match),
                    reasoning=f"'{event_match}' exists as both event and program"
                )
        
        # Case 6: Strong event match, weak/no program match = EVENT_DETAIL_REQUEST
        # When user directly asks about a specific event, route to EVENT_DETAIL_REQUEST
        # to ensure the deterministic Stage-1 summary with correct CTA is used
        # IMPORTANT: If user explicitly mentions "program", "course", etc., prioritize PROGRAM intent
        has_program_keyword = self._has_program_keyword(message_lower)
        
        # If user explicitly says "program", ALWAYS route to KNOWLEDGE (even without program_match)
        # This respects the user's explicit intent and lets RAG handle the program lookup
        if has_program_keyword:
            return IntentResult(
                intent=IntentType.KNOWLEDGE,
                confidence=program_score if program_match else MEDIUM_CONFIDENCE,
                slots=slots,
                reasoning=f"User explicitly mentioned 'program' keyword - routing to KNOWLEDGE for program info"
            )
        
        if event_match and event_score > 0.5 and (not program_match or program_score < 0.5 or event_score - program_score > 0.3):
            return IntentResult(
                intent=IntentType.EVENT_DETAIL_REQUEST,
                confidence=event_score,
                slots=slots,
                reasoning=f"Message matches event title '{event_match}' - using deterministic summary"
            )
        
        # Case 7: Strong program match, weak/no event match = KNOWLEDGE
        if program_match and program_score > 0.5 and (not event_match or event_score < 0.5 or program_score - event_score > 0.3):
            return IntentResult(
                intent=IntentType.KNOWLEDGE,
                confidence=program_score,
                slots=slots,
                reasoning=f"Message matches program name '{program_match}'"
            )
        
        # Case 8: Both match with similar scores = HYBRID
        if event_match or program_match:
            return IntentResult(
                intent=IntentType.HYBRID,
                confidence=MEDIUM_CONFIDENCE,
                slots=slots,
                reasoning="Could be event or knowledge query"
            )
        
        # Case 9: Check conversation history for follow-up context
        if conversation_history:
            history_intent = self._check_conversation_context(conversation_history)
            if history_intent:
                return IntentResult(
                    intent=history_intent,
                    confidence=MEDIUM_CONFIDENCE,
                    slots=slots,
                    reasoning="Intent inferred from conversation history"
                )
        
        # Default: KNOWLEDGE (most queries are about program info)
        return IntentResult(
            intent=IntentType.KNOWLEDGE,
            confidence=LOW_CONFIDENCE,
            slots=slots,
            reasoning="Default to knowledge intent"
        )
    
    def _is_greeting(self, message: str) -> bool:
        """Check if message is a greeting."""
        for pattern in GREETING_PATTERNS:
            if re.search(pattern, message, re.IGNORECASE):
                return True
        return False
    
    def _extract_date_signals(self, message: str) -> Tuple[bool, Optional[str]]:
        """
        Check for date patterns in message.
        Returns (has_date, date_info) where date_info is the matched text.
        """
        for pattern in DATE_PATTERNS:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                return True, match.group()
        return False, None
    
    def _has_event_action(self, message: str) -> bool:
        """Check for event action patterns (book, register, attend, etc.)."""
        for pattern in EVENT_ACTION_PATTERNS:
            if re.search(pattern, message, re.IGNORECASE):
                return True
        return False
    
    def _has_knowledge_pattern(self, message: str) -> bool:
        """Check for knowledge/program inquiry patterns."""
        for pattern in KNOWLEDGE_PATTERNS:
            if re.search(pattern, message, re.IGNORECASE):
                return True
        return False
    
    def _has_time_pattern(self, message: str) -> bool:
        """Check for time-related patterns."""
        for pattern in TIME_PATTERNS:
            if re.search(pattern, message, re.IGNORECASE):
                return True
        return False
    
    def _has_program_keyword(self, message: str) -> bool:
        """
        Check if message contains explicit program keywords like 'program', 'course', 'membership'.
        Used to prioritize program intent when event and program names overlap.
        """
        for pattern in PROGRAM_KEYWORDS:
            if re.search(pattern, message, re.IGNORECASE):
                return True
        return False
    
    def _match_event_title(self, message: str) -> Tuple[Optional[str], float]:
        """
        Check if message fuzzy-matches any event title.
        Returns (matched_title, score) or (None, 0).
        
        Scoring:
        - Exact substring match: 0.95
        - All title words in message: 0.85
        - Majority of title words in message: percentage * 0.85
        """
        if not self._event_titles:
            return None, 0
        
        message_lower = message.lower()
        # Normalize special characters (® → empty)
        message_normalized = re.sub(r'[®™©]', '', message_lower)
        best_match = None
        best_score = 0
        
        for title in self._event_titles:
            title_lower = title.lower()
            # Normalize special characters in title too
            title_normalized = re.sub(r'[®™©]', '', title_lower)
            
            # Exact substring match (after normalization)
            if title_normalized in message_normalized or message_normalized in title_normalized:
                score = 0.95
            else:
                # Check if all title words are present in message
                msg_words = set(re.findall(r'\w+', message_normalized))
                title_words = set(re.findall(r'\w+', title_normalized))
                
                if not msg_words or not title_words:
                    continue
                
                # Score based on % of title words found in message
                # This way "Tell me about SoulAlign Coach" scores high for "SoulAlign® Coach"
                common = msg_words & title_words
                title_coverage = len(common) / len(title_words)
                score = title_coverage * 0.85  # Max 0.85 for word overlap
            
            if score > best_score:
                best_score = score
                best_match = title
        
        return (best_match, best_score) if best_score > 0.3 else (None, 0)
    
    def _match_program_name(self, message: str) -> Tuple[Optional[str], float]:
        """
        Check if message fuzzy-matches any program name.
        Returns (matched_name, score) or (None, 0).
        
        Scoring:
        - Exact substring match: 0.95
        - All program name words in message: 0.85
        - Majority of name words in message: percentage * 0.85
        """
        if not self._program_names:
            return None, 0
        
        message_lower = message.lower()
        # Normalize special characters
        message_normalized = re.sub(r'[®™©]', '', message_lower)
        best_match = None
        best_score = 0
        
        for name in self._program_names:
            name_lower = name.lower()
            name_normalized = re.sub(r'[®™©]', '', name_lower)
            
            # Exact substring match (after normalization)
            if name_normalized in message_normalized or message_normalized in name_normalized:
                score = 0.95
            else:
                # Check if all name words are present in message
                msg_words = set(re.findall(r'\w+', message_normalized))
                name_words = set(re.findall(r'\w+', name_normalized))
                
                if not msg_words or not name_words:
                    continue
                
                # Score based on % of name words found in message
                common = msg_words & name_words
                name_coverage = len(common) / len(name_words)
                score = name_coverage * 0.85
            
            if score > best_score:
                best_score = score
                best_match = name
        
        return (best_match, best_score) if best_score > 0.3 else (None, 0)
    
    def _generate_clarification(self, name: str) -> str:
        """Generate a clarification question for ambiguous queries."""
        return (
            f"I see '{name}' is both a program and an upcoming event. "
            f"Are you asking about:\n"
            f"1. **Program details** - What's included, pricing, and how to enroll\n"
            f"2. **Event dates** - When it's happening and how to register\n\n"
            f"Just let me know which one you'd like to explore!"
        )
    
    def _has_numbered_list(self, message: str) -> bool:
        """Check if a message contains a numbered list."""
        for pattern in NUMBERED_LIST_PATTERNS:
            if re.search(pattern, message, re.IGNORECASE):
                return True
        return False
    
    def _is_bare_ordinal(self, message: str) -> Tuple[bool, Optional[int]]:
        """
        Check if message is a bare ordinal selection (NOT part of a date).
        
        Returns (is_ordinal, selection_index) where index is 0-based.
        """
        msg = message.strip()
        
        # First, check if message contains date patterns - if so, NOT a bare ordinal
        has_date, _ = self._extract_date_signals(msg.lower())
        if has_date:
            return False, None
        
        # Check for ordinal patterns
        for pattern in ORDINAL_SELECTION_PATTERNS:
            if re.match(pattern, msg, re.IGNORECASE):
                # Extract the index
                return True, self._extract_ordinal_index(msg)
        
        return False, None
    
    def _extract_ordinal_index(self, message: str) -> int:
        """Extract 0-based index from ordinal message."""
        msg = message.lower().strip()
        
        # Direct numbers
        if re.match(r'^[1-9]$', msg):
            return int(msg) - 1
        
        # #1, #2, etc.
        match = re.match(r'^#([1-9])$', msg)
        if match:
            return int(match.group(1)) - 1
        
        # Ordinals
        ordinals = {"first": 0, "1st": 0, "second": 1, "2nd": 1, "third": 2, "3rd": 2,
                    "fourth": 3, "4th": 3, "fifth": 4, "5th": 4}
        for ordinal, idx in ordinals.items():
            if ordinal in msg:
                return idx
        
        return 0  # Default to first
    
    def _is_affirmative(self, message: str) -> bool:
        """Check if message is a bare affirmative/confirmation."""
        msg = message.strip().lower()
        for pattern in AFFIRMATIVE_PATTERNS:
            if re.match(pattern, msg, re.IGNORECASE):
                return True
        return False
    
    def _check_followup_context(self, message: str, conversation_history: List[Dict]) -> Optional[IntentResult]:
        """
        Check if user is responding to a previous bot message (selection or confirmation).
        
        This is the SINGLE decision point for follow-up detection.
        Returns IntentResult if it's a follow-up, None otherwise.
        
        EVENT FOLLOW-UP STAGES:
        1. After event listing + user mentions event name → EVENT_DETAIL_REQUEST (show summary)
        2. After "more details?" + user confirms → FOLLOWUP_CONFIRM with stage=summary_shown (show full details)
        3. After "event page?" + user confirms → EVENT_NAVIGATE (emit navigation)
        """
        if not conversation_history:
            return None
        
        # Get last assistant message
        last_bot_msg = None
        for msg in reversed(conversation_history):
            if msg.get("role") == "assistant":
                last_bot_msg = msg.get("content", "")
                break
        
        if not last_bot_msg:
            return None
        
        last_msg_lower = last_bot_msg.lower()
        
        # Check if user is selecting from a numbered list
        is_ordinal, selection_idx = self._is_bare_ordinal(message)
        if is_ordinal and self._has_numbered_list(last_bot_msg):
            return IntentResult(
                intent=IntentType.FOLLOWUP_SELECT,
                confidence=HIGH_CONFIDENCE,
                slots={"selection_index": selection_idx, "last_bot_message": last_bot_msg[:500]},
                reasoning=f"User selected item {selection_idx + 1} from numbered list"
            )
        
        # ========== EVENT FOLLOW-UP STAGE DETECTION ==========
        # Detect current stage based on last bot message CTAs
        current_stage = self._detect_event_followup_stage(last_msg_lower)
        
        # Check if user is confirming/asking for more info
        if self._is_affirmative(message):
            # STAGE 3: User confirming navigation to event page
            if current_stage == EventFollowupStage.DETAILS_SHOWN:
                # Extract event URL from last message if available
                event_url = self._extract_event_url_from_message(last_bot_msg)
                return IntentResult(
                    intent=IntentType.EVENT_NAVIGATE,
                    confidence=HIGH_CONFIDENCE,
                    slots={
                        "context": "event", 
                        "stage": EventFollowupStage.DETAILS_SHOWN,
                        "event_url": event_url,
                        "last_bot_message": last_bot_msg[:500]
                    },
                    reasoning="User confirming navigation to event page"
                )
            
            # STAGE 2: User confirming they want more details (after summary)
            if current_stage == EventFollowupStage.SUMMARY_SHOWN:
                return IntentResult(
                    intent=IntentType.FOLLOWUP_CONFIRM,
                    confidence=HIGH_CONFIDENCE,
                    slots={
                        "context": "event", 
                        "stage": EventFollowupStage.SUMMARY_SHOWN,
                        "last_bot_message": last_bot_msg[:500]
                    },
                    reasoning="User confirming interest in full event details"
                )
            
            # STAGE 1: User confirming after event listing (wants to hear about specific event)
            if current_stage == EventFollowupStage.LISTING_SHOWN:
                # Extract event name from user's message if present (e.g., "yes, the SoulAlign Business")
                event_match, event_score = self._match_event_title(message)
                return IntentResult(
                    intent=IntentType.FOLLOWUP_CONFIRM,
                    confidence=HIGH_CONFIDENCE,
                    slots={
                        "context": "event", 
                        "stage": EventFollowupStage.LISTING_SHOWN,
                        "matched_event": event_match if event_score >= 0.3 else "",
                        "last_bot_message": last_bot_msg[:500]
                    },
                    reasoning="User confirming interest after event listing"
                )
            
            # Check if last message was about programs (non-event)
            if any(word in last_msg_lower for word in ["program", "course", "enroll", "investment", "pricing"]):
                return IntentResult(
                    intent=IntentType.FOLLOWUP_CONFIRM,
                    confidence=HIGH_CONFIDENCE,
                    slots={"context": "program", "last_bot_message": last_bot_msg[:500]},
                    reasoning="User confirming interest in previously discussed program"
                )
        
        # ========== EVENT NAME AFTER LISTING ==========
        # If last message was an event listing and user mentions an event name, route to EVENT_DETAIL_REQUEST
        if current_stage == EventFollowupStage.LISTING_SHOWN:
            # Check if user's message contains an event title
            event_match, event_score = self._match_event_title(message)
            if event_match and event_score >= 0.4:
                return IntentResult(
                    intent=IntentType.EVENT_DETAIL_REQUEST,
                    confidence=HIGH_CONFIDENCE,
                    slots={
                        "matched_event": event_match,
                        "stage": EventFollowupStage.LISTING_SHOWN,
                        "last_bot_message": last_bot_msg[:500]
                    },
                    reasoning=f"User asking about '{event_match}' after event listing"
                )
        
        return None
    
    def _detect_event_followup_stage(self, last_msg_lower: str) -> str:
        """
        Detect the current event follow-up stage based on the last bot message.
        Returns one of EventFollowupStage values.
        
        Uses REGEX patterns derived from canonical CTAs in events_service.py.
        Patterns are generated dynamically to stay in sync with CTA constants.
        """
        cta_patterns = _get_cta_regex_patterns()
        
        # DETAILS_SHOWN: Bot showed full details and offered next action
        # Use patterns derived from STAGE2_CTA_TEMPLATE and STAGE2_CTA_NO_URL
        details_shown_patterns = [
            cta_patterns["stage2_url_regex"],     # Derived from STAGE2_CTA_TEMPLATE
            cta_patterns["stage2_no_url_regex"],  # Derived from STAGE2_CTA_NO_URL
            r"\[navigate:",                        # Navigation marker already emitted
        ]
        for pattern in details_shown_patterns:
            if re.search(pattern, last_msg_lower):
                print(f"[_detect_event_followup_stage] Matched DETAILS_SHOWN via pattern derived from canonical CTA", flush=True)
                return EventFollowupStage.DETAILS_SHOWN
        
        # SUMMARY_SHOWN: Bot showed summary and offered more details  
        # Use pattern derived from STAGE1_CTA
        summary_shown_patterns = [
            cta_patterns["stage1_regex"],          # Derived from STAGE1_CTA
            r"would you like more details\??",     # Short fallback
        ]
        for pattern in summary_shown_patterns:
            if re.search(pattern, last_msg_lower):
                print(f"[_detect_event_followup_stage] Matched SUMMARY_SHOWN via pattern derived from canonical CTA", flush=True)
                return EventFollowupStage.SUMMARY_SHOWN
        
        # LISTING_SHOWN: Bot showed event listing with numbered items
        # Look for numbered lists with event-related content
        if self._has_numbered_list(last_msg_lower) and any(word in last_msg_lower for word in [
            "event", "upcoming", "here are", "schedule", "workshop", "session"
        ]):
            return EventFollowupStage.LISTING_SHOWN
        
        return EventFollowupStage.NONE
    
    def _extract_event_url_from_message(self, message: str) -> Optional[str]:
        """
        Extract event page URL from bot message if present.
        Handles Markdown links [text](url) and raw URLs.
        """
        import re
        
        # Pattern 1: [event page](url) - case insensitive
        match = re.search(r'\[event page\]\((https?://[^)\s]+)\)', message, re.IGNORECASE)
        if match:
            url = match.group(1).rstrip('.,')  # Clean trailing punctuation
            print(f"[_extract_event_url] Found via [event page]: {url}", flush=True)
            return url
        
        # Pattern 2: [View Event Page](url) - case insensitive
        match = re.search(r'\[View Event Page\]\((https?://[^)\s]+)\)', message, re.IGNORECASE)
        if match:
            url = match.group(1).rstrip('.,')
            print(f"[_extract_event_url] Found via [View Event Page]: {url}", flush=True)
            return url
        
        # Pattern 3: Any Markdown link with annakitney.com/event/
        match = re.search(r'\[[^\]]+\]\((https?://[^)\s]*annakitney\.com/event[^)\s]*)\)', message)
        if match:
            url = match.group(1).rstrip('.,')
            print(f"[_extract_event_url] Found via Markdown link: {url}", flush=True)
            return url
        
        # Pattern 4: Raw annakitney.com/event/ URL (not in Markdown)
        match = re.search(r'(https?://(?:www\.)?annakitney\.com/event/[^\s\)\]]+)', message)
        if match:
            url = match.group(1).rstrip('.,')
            print(f"[_extract_event_url] Found via raw URL: {url}", flush=True)
            return url
        
        print(f"[_extract_event_url] No URL found in message (length: {len(message)})", flush=True)
        return None
    
    def _check_conversation_context(self, history: List[Dict]) -> Optional[IntentType]:
        """
        Check conversation history to infer intent for follow-up questions.
        """
        if not history:
            return None
        
        # Look at last few messages
        for msg in reversed(history[-4:]):
            content = msg.get("content", "").lower()
            
            # If last assistant message mentioned events/dates
            if msg.get("role") == "assistant":
                if any(word in content for word in ["event", "calendar", "schedule", "register", "attend"]):
                    return IntentType.EVENT
                if any(word in content for word in ["program", "course", "enroll", "investment", "includes"]):
                    return IntentType.KNOWLEDGE
        
        return None


# Singleton instance
_router_instance = None


def get_intent_router() -> IntentRouter:
    """Get the singleton IntentRouter instance."""
    global _router_instance
    if _router_instance is None:
        _router_instance = IntentRouter()
    return _router_instance


def refresh_router_data():
    """
    Refresh the router with current event titles and program names.
    Call this after calendar sync or knowledge base updates.
    """
    from events_service import get_upcoming_events
    
    router = get_intent_router()
    
    # Load event titles from database
    try:
        events = get_upcoming_events(50)
        titles = [e.get("title", "") for e in events if e.get("title")]
        router.set_event_titles(titles)
    except Exception as e:
        print(f"[IntentRouter] Error loading event titles: {e}")
    
    # Load program names - these could come from DB or config
    # For now, we'll extract from knowledge base or use common names
    # This list should ideally come from a database table
    program_names = [
        "Elite Private Advisory",
        "The Ascend Collective",
        "VIP Day",
        "SoulAlign Heal",
        "SoulAlign Manifestation Mastery",
        "SoulAlign Money",
        "Divine Abundance Codes",
        "Avatar",
        "Soul Align Business Course",
        "Launch and Grow Live",
        "Get Clients Fast Masterclass",
        "SoulAlign Business",
    ]
    router.set_program_names(program_names)
    
    print(f"[IntentRouter] Refreshed with {len(titles)} events and {len(program_names)} programs")
