"""
Chatbot Engine for Anna Kitney Wellness

This module handles the core chatbot logic:
- Intent-first routing (EVENT vs KNOWLEDGE vs HYBRID)
- Query processing with RAG (for knowledge queries)
- SQL event queries (for event queries)
- Integration with OpenAI for response generation
- Context management for multi-turn conversations

ARCHITECTURE:
User Query → IntentRouter.classify() → Appropriate Handler
    ├── EVENT → SQL only (skip RAG)
    ├── KNOWLEDGE → RAG only (skip events)
    ├── HYBRID → Both with priority rules
    └── CLARIFICATION → Ask clarifying question
"""

import os
import re
from typing import List, Optional

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception

from knowledge_base import search_knowledge_base, get_knowledge_base_stats
from safety_guardrails import apply_safety_filters, get_system_prompt, filter_response_for_safety, inject_program_links, inject_checkout_urls, append_contextual_links, format_numbered_lists, inject_dynamic_enrollment, fix_compound_trailing_questions, enforce_trailing_cta
from events_service import is_event_query, get_event_context_for_llm, process_calendar_action, fix_navigation_urls
from intent_router import get_intent_router, IntentType, EventFollowupStage, ProgramFollowupStage, refresh_router_data

_openai_client = None
_router_initialized = False

def _ensure_router_initialized():
    """Ensure the intent router is initialized with event titles and program names."""
    global _router_initialized
    if not _router_initialized:
        try:
            refresh_router_data()
            _router_initialized = True
            print("[ChatbotEngine] Intent router initialized with event/program data", flush=True)
        except Exception as e:
            print(f"[ChatbotEngine] Warning: Could not initialize router data: {e}", flush=True)


def _extract_program_from_numbered_list(message: str, selection_idx: int) -> Optional[str]:
    """
    Extract the program name from a numbered list at the given index.
    
    Parses messages like:
    1. **[The Ascend Collective](url)** - description
    2. **[SoulAlign Heal](url)** - description
    
    Returns the program name at selection_idx (0-based).
    """
    # Pattern to match numbered list items with markdown links
    # Matches: 1. **[Program Name](url)** or 1. [Program Name](url) or 1. **Program Name**
    patterns = [
        r'^\s*\d+\.\s*\*\*\[([^\]]+)\]\([^)]+\)\*\*',  # 1. **[Name](url)**
        r'^\s*\d+\.\s*\[([^\]]+)\]\([^)]+\)',           # 1. [Name](url)
        r'^\s*\d+\.\s*\*\*([^*]+)\*\*',                  # 1. **Name**
        r'^\s*\d+\.\s*([^-\n]+)',                        # 1. Name - description
    ]
    
    lines = message.split('\n')
    extracted_items = []
    
    for line in lines:
        for pattern in patterns:
            match = re.match(pattern, line)
            if match:
                name = match.group(1).strip()
                # Clean up any trailing special chars
                name = re.sub(r'[\*\[\]]', '', name).strip()
                if name:
                    extracted_items.append(name)
                    break
    
    if selection_idx < len(extracted_items):
        return extracted_items[selection_idx]
    
    return None


def get_openai_client():
    """Lazy initialization of OpenAI client with validation."""
    global _openai_client
    
    if _openai_client is not None:
        return _openai_client
    
    api_key = os.environ.get("AI_INTEGRATIONS_OPENAI_API_KEY")
    base_url = os.environ.get("AI_INTEGRATIONS_OPENAI_BASE_URL")
    
    if not api_key or not base_url:
        return None
    
    try:
        from openai import OpenAI
        _openai_client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        return _openai_client
    except Exception as e:
        print(f"Error initializing OpenAI client: {e}")
        return None


def is_openai_available() -> bool:
    """Check if OpenAI is properly configured."""
    return get_openai_client() is not None


def is_rate_limit_error(exception: BaseException) -> bool:
    """Check if the exception is a rate limit or quota violation error."""
    error_msg = str(exception)
    return (
        "429" in error_msg
        or "RATELIMIT_EXCEEDED" in error_msg
        or "quota" in error_msg.lower()
        or "rate limit" in error_msg.lower()
        or (hasattr(exception, "status_code") and exception.status_code == 429)
    )


def format_context_from_docs(documents: List[dict]) -> str:
    """Format retrieved documents into context for the LLM."""
    if not documents:
        return "No relevant information found in the knowledge base."
    
    context_parts = []
    for i, doc in enumerate(documents, 1):
        source = doc.get("source", "Unknown source")
        content = doc.get("content", "")
        context_parts.append(f"[Source {i}: {source}]\n{content}")
    
    return "\n\n---\n\n".join(context_parts)


def format_conversation_history(messages: List[dict]) -> List[dict]:
    """Format conversation history for the API call."""
    formatted = []
    for msg in messages[-6:]:
        if msg.get("role") in ["user", "assistant", "system"]:
            formatted.append({
                "role": msg["role"],
                "content": msg["content"]
            })
    return formatted


def build_context_aware_query(user_message: str, conversation_history: List[dict] = None) -> str:
    """
    Build a search query that includes context from conversation history.
    This helps with follow-up questions like "tell me more about that program".
    
    Uses robust detection that handles:
    - Typos (e.g., "programm", "progam")
    - Various follow-up patterns
    - Short queries that reference previous context
    """
    if not conversation_history:
        return user_message
    
    program_names = [
        "Elite Private Advisory", "The Ascend Collective", "VIP Day",
        "SoulAlign Heal", "SoulAlign Manifestation Mastery", "SoulAlign Money",
        "Divine Abundance Codes", "Avatar", "Soul Align Business Course",
        "Launch and Grow Live", "Get Clients Fast Masterclass"
    ]
    
    message_lower = user_message.lower()
    
    follow_up_indicators = [
        "this", "that", "it", "the program", "the course",
        "more details", "more information", "tell me more",
        "details", "about it", "learn more", "know more",
        "give me", "share more", "explain", "what is it",
        "how does it", "how much", "price", "cost", "duration",
        "sign up", "enroll", "join", "register"
    ]
    
    program_typo_patterns = ["program", "progam", "programm", "programme", "prog"]
    
    has_follow_up = any(phrase in message_lower for phrase in follow_up_indicators)
    has_program_reference = any(pattern in message_lower for pattern in program_typo_patterns)
    is_short_query = len(user_message.split()) <= 8
    
    should_add_context = has_follow_up or (has_program_reference and is_short_query)
    
    if not should_add_context:
        return user_message
    
    recent_programs = []
    for msg in reversed(conversation_history[-6:]):
        content = msg.get("content", "")
        for program in program_names:
            if program.lower() in content.lower():
                if program not in recent_programs:
                    recent_programs.append(program)
    
    if recent_programs:
        context_str = " ".join(recent_programs[:3])
        return f"{user_message} {context_str}"
    
    return user_message


def fix_typos_with_llm(user_message: str) -> str:
    """
    Use GPT-3.5-turbo to fix typos in user message before processing.
    
    This is a fast, lightweight call that:
    - Corrects spelling mistakes
    - Preserves original intent and meaning
    - Does NOT change the language or add/remove content
    
    Returns the original message if LLM is unavailable or on error.
    """
    if len(user_message.strip()) < 3:
        return user_message
    
    client = get_openai_client()
    if client is None:
        return user_message
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """You are a typo correction assistant. Your ONLY job is to fix spelling mistakes.

RULES:
1. Fix spelling errors and typos
2. DO NOT change the meaning or intent
3. DO NOT add or remove words
4. DO NOT change the language
5. DO NOT add punctuation unless fixing obvious errors
6. Return ONLY the corrected text, nothing else

Examples:
Input: "plese give me detials of this programm"
Output: "please give me details of this program"

Input: "waht is beynd the hustle"
Output: "what is beyond the hustle"

Input: "tell me abot balace mastery"
Output: "tell me about balance mastery"

Input: "hi how are you"
Output: "hi how are you" (no changes needed)"""
                },
                {
                    "role": "user",
                    "content": user_message
                }
            ],
            max_tokens=200,
            temperature=0
        )
        
        corrected = response.choices[0].message.content.strip()
        
        if corrected and len(corrected) < len(user_message) * 3:
            if corrected.lower() != user_message.lower():
                print(f"[Typo Fixer] '{user_message}' -> '{corrected}'")
            return corrected
        
        return user_message
        
    except Exception as e:
        print(f"[Typo Fixer] Error: {e}, using original message")
        return user_message


def generate_response(
    user_message: str,
    conversation_history: List[dict] = None,
    n_context_docs: int = 8,
    user_name: str = None,
    is_returning_user: bool = False,
    last_topic_summary: str = None
) -> dict:
    """
    Generate a response to the user's message using RAG.
    
    Args:
        user_message: The user's question
        conversation_history: Previous messages in the conversation
        n_context_docs: Number of context documents to retrieve
        user_name: User's first name for personalized greeting
        is_returning_user: Whether this is a returning user
        last_topic_summary: Summary of user's last conversation topic (for returning users)
    
    Returns:
        dict with 'response', 'sources', and 'safety_triggered' keys
    """
    client = get_openai_client()
    if client is None:
        return {
            "response": "I'm temporarily unavailable. Please try again later or contact us at https://www.annakitney.com/contact for assistance.",
            "sources": [],
            "safety_triggered": False,
            "error": "openai_not_configured"
        }
    
    # Ensure intent router has event titles and program names loaded
    _ensure_router_initialized()
    
    should_redirect, redirect_response = apply_safety_filters(user_message, is_anna=True)
    
    if should_redirect:
        return {
            "response": redirect_response,
            "sources": [],
            "safety_triggered": True,
            "safety_category": "safety_redirect"
        }
    
    # ═══════════════════════════════════════════════════════════════════════
    # INTENT-FIRST ROUTING: Classify intent BEFORE any database queries
    # This prevents RAG from polluting event queries and vice versa
    # ═══════════════════════════════════════════════════════════════════════
    router = get_intent_router()
    intent_result = router.classify(user_message, conversation_history)
    
    print(f"[IntentRouter] Intent: {intent_result.intent.value}, Confidence: {intent_result.confidence:.2f}, Reason: {intent_result.reasoning}", flush=True)
    
    # Handle CLARIFICATION intent - ask user before proceeding
    if intent_result.intent == IntentType.CLARIFICATION and intent_result.clarification_question:
        return {
            "response": intent_result.clarification_question,
            "sources": [],
            "safety_triggered": False,
            "safety_category": None,
            "intent": "clarification"
        }
    
    # Handle GREETING intent - use the curated greeting message (fast, consistent, brand-approved)
    if intent_result.intent == IntentType.GREETING:
        return {
            "response": get_greeting_message(),
            "sources": [],
            "safety_triggered": False,
            "intent": "greeting"
        }
    
    # Handle FOLLOWUP_SELECT intent - user selected from a numbered list
    if intent_result.intent == IntentType.FOLLOWUP_SELECT:
        selection_idx = intent_result.slots.get("selection_index", 0)
        last_bot_msg = intent_result.slots.get("last_bot_message", "")
        context_type = intent_result.slots.get("context", "event")  # Default to event for backwards compat
        print(f"[IntentRouter] User selected item {selection_idx + 1} from {context_type} list", flush=True)
        
        # ====== PROGRAM SELECTION ======
        if context_type == "program":
            # Extract the program name from the numbered list in last_bot_msg
            program_name = _extract_program_from_numbered_list(last_bot_msg, selection_idx)
            print(f"[IntentRouter] Program selection: extracted '{program_name}'", flush=True)
            
            if program_name:
                # Query RAG for this specific program
                search_query = f"{program_name} program details what's included benefits"
                relevant_docs = search_knowledge_base(search_query, n_results=5, prefer_programs=True)
                
                if relevant_docs:
                    context = format_context_from_docs(relevant_docs)
                    
                    # Get program URL for the navigation CTA
                    from safety_guardrails import ANNA_PROGRAM_URLS
                    program_url = None
                    for name, url in ANNA_PROGRAM_URLS.items():
                        if program_name and (program_name.lower() in name.lower() or name.lower() in program_name.lower()):
                            program_url = url
                            break
                    
                    # SIMPLE FLOW (like JoveHeal): Summary → Navigation CTA
                    # User selects program → Bot shows summary → "Would you like me to take you to the page?"
                    program_summary_prompt = f"""Based on the following context about {program_name}, provide a brief summary of what this program offers. Format as:

1. A 2-3 sentence overview of the program
2. 3-5 key features as a bulleted list

Do NOT include any trailing question - the system will add one automatically.

Context:
{context}

Respond with just the summary and features, nothing else."""
                    
                    messages = [
                        {"role": "system", "content": "You are Anna, a warm wellness coach. Be concise and helpful."},
                        {"role": "user", "content": program_summary_prompt}
                    ]
                    
                    client = get_openai_client()
                    if client:
                        try:
                            response = client.chat.completions.create(
                                model="gpt-4o-mini",
                                messages=messages,
                                max_tokens=400,
                                temperature=0.7
                            )
                            summary = response.choices[0].message.content.strip()
                            # Inject program link
                            summary = inject_program_links(summary)
                            
                            # SIMPLE NAVIGATION CTA (like JoveHeal)
                            # After summary, ask: "Would you like me to take you to the [Program] page?"
                            if program_url:
                                summary += f"\n\nWould you like me to take you to the [{program_name}]({program_url}) page?"
                            else:
                                summary += f"\n\nWould you like to learn more about {program_name}?"
                            
                            print(f"[FOLLOWUP_SELECT] Program summary with navigation CTA for {program_name}", flush=True)
                            return {
                                "response": summary,
                                "sources": [doc.get("source", "") for doc in relevant_docs[:3]],
                                "safety_triggered": False,
                                "intent": "program_select"
                            }
                        except Exception as e:
                            print(f"[Program Select] LLM error: {e}", flush=True)
            
            # Fallback if program extraction failed
            return {
                "response": f"I'd be happy to tell you more about that program! Could you please tell me which program from the list you're most interested in?",
                "sources": [],
                "safety_triggered": False,
                "intent": "clarification"
            }
        
        # ====== EVENT SELECTION ======
        # Extract the selected item from the last bot message
        # Pass to events service with selection context (get_event_context_for_llm imported at top)
        followup_event_context = get_event_context_for_llm(
            user_message, 
            conversation_history,
            selection_index=selection_idx
        )
        
        if followup_event_context and "{{DIRECT_EVENT}}" in followup_event_context:
            direct_match = re.search(r'\{\{DIRECT_EVENT\}\}(.*?)\{\{/DIRECT_EVENT\}\}', followup_event_context, re.DOTALL)
            if direct_match:
                return {
                    "response": format_numbered_lists(direct_match.group(1).strip()),
                    "sources": [],
                    "safety_triggered": False,
                    "intent": "followup_select"
                }
        
        # If we couldn't match the selection, ask for clarification
        # This handles cases where the parsed list doesn't match what was shown
        if not followup_event_context or "{{DIRECT_EVENT}}" not in followup_event_context:
            print(f"[IntentRouter] Could not match selection {selection_idx + 1}, asking for clarification", flush=True)
            return {
                "response": f"I'm not sure which option #{selection_idx + 1} refers to. Could you please tell me the name of the event or program you're interested in?",
                "sources": [],
                "safety_triggered": False,
                "intent": "clarification"
            }
    
    # Handle EVENT_NAVIGATE intent - user confirming they want to go to event page
    if intent_result.intent == IntentType.EVENT_NAVIGATE:
        print(f"[IntentRouter] User wants to navigate to event page", flush=True)
        
        # ALWAYS use database URL - never trust URL extracted from message
        # This ensures 100% accuracy by using eventPageUrl from PostgreSQL
        from events_service import _find_event_from_history
        last_event = _find_event_from_history(conversation_history)
        
        if last_event and last_event.get("eventPageUrl"):
            event_url = last_event.get("eventPageUrl")
            print(f"[EVENT_NAVIGATE] Using database URL: {event_url}", flush=True)
            response = f"Taking you to the event page now!\n\n[NAVIGATE:{event_url}]"
            return {
                "response": response,
                "sources": [],
                "safety_triggered": False,
                "intent": "event_navigate"
            }
        else:
            # Fallback: try URL from message if database lookup failed
            extracted_url = intent_result.slots.get("event_url", "")
            if extracted_url:
                print(f"[EVENT_NAVIGATE] Fallback to extracted URL: {extracted_url}", flush=True)
                response = f"Taking you to the event page now!\n\n[NAVIGATE:{extracted_url}]"
                return {
                    "response": response,
                    "sources": [],
                    "safety_triggered": False,
                    "intent": "event_navigate"
                }
            
            return {
                "response": "I'm sorry, I couldn't find the event page URL. Could you tell me which event you'd like to learn more about?",
                "sources": [],
                "safety_triggered": False,
                "intent": "clarification"
            }
    
    # ========== PROGRAM FOLLOW-UP HANDLERS ==========
    # Handle PROGRAM_NAVIGATE intent - user confirming they want to go to program page
    if intent_result.intent == IntentType.PROGRAM_NAVIGATE:
        program_name = intent_result.slots.get("program_name", "")
        program_url = intent_result.slots.get("program_url", "")
        print(f"[IntentRouter] User wants to navigate to program page: {program_name}", flush=True)
        
        # Try to get URL from known program URLs if not extracted
        if not program_url and program_name:
            from safety_guardrails import ANNA_PROGRAM_URLS
            for name, url in ANNA_PROGRAM_URLS.items():
                if program_name.lower() in name.lower() or name.lower() in program_name.lower():
                    program_url = url
                    break
        
        if program_url:
            print(f"[PROGRAM_NAVIGATE] Using URL: {program_url}", flush=True)
            response = f"Taking you to the {program_name} page now!\n\n[NAVIGATE:{program_url}]"
            return {
                "response": response,
                "sources": [],
                "safety_triggered": False,
                "intent": "program_navigate"
            }
        else:
            return {
                "response": f"I'd love to help you learn more about {program_name}. Let me find the right page for you. Could you tell me a bit more about what you're looking for?",
                "sources": [],
                "safety_triggered": False,
                "intent": "clarification"
            }
    
    # Handle PROGRAM_DETAIL_REQUEST intent - user wants more details about a program
    if intent_result.intent == IntentType.PROGRAM_DETAIL_REQUEST:
        program_name = intent_result.slots.get("program_name", "")
        print(f"[IntentRouter] User asking for program details: {program_name}", flush=True)
        
        # Query RAG for program information
        if program_name:
            search_query = f"{program_name} program details what's included enrollment"
        else:
            # Fallback: use the last bot message to find context
            last_msg = intent_result.slots.get("last_bot_message", "")
            search_query = f"program details {last_msg[:100]}"
        
        program_docs = search_knowledge_base(search_query, n_results=5)
        program_context = format_context_from_docs(program_docs)
        
        if program_context:
            # Let LLM generate response with program context
            print(f"[PROGRAM_DETAIL_REQUEST] Found RAG context for: {program_name}", flush=True)
            # Fall through to LLM with this context (don't return early)
            # We'll set up the context and let the normal LLM flow handle it
        else:
            print(f"[PROGRAM_DETAIL_REQUEST] No RAG context found for: {program_name}", flush=True)
    
    # Handle EVENT_DETAIL_REQUEST intent - user asking about specific event after listing
    if intent_result.intent == IntentType.EVENT_DETAIL_REQUEST:
        matched_event = intent_result.slots.get("matched_event", "")
        print(f"[IntentRouter] User asking for event details: {matched_event}", flush=True)
        
        # Use centralized deterministic summary generator
        from events_service import get_deterministic_event_summary
        
        summary_response = get_deterministic_event_summary(matched_event, conversation_history)
        
        if summary_response:
            print(f"[EVENT_DETAIL_REQUEST] Returning deterministic summary", flush=True)
            return {
                "response": format_numbered_lists(summary_response),
                "sources": [],
                "safety_triggered": False,
                "intent": "event_detail_request"
            }
        
        # Couldn't find the event
        return {
            "response": f"I couldn't find details for '{matched_event}'. Could you please specify which event you're interested in?",
            "sources": [],
            "safety_triggered": False,
            "intent": "clarification"
        }
    
    # Handle FOLLOWUP_CONFIRM intent - user confirming interest
    if intent_result.intent == IntentType.FOLLOWUP_CONFIRM:
        context_type = intent_result.slots.get("context", "event")
        stage = intent_result.slots.get("stage", "")
        matched_event = intent_result.slots.get("matched_event", "")
        print(f"[IntentRouter] User confirming interest in {context_type}, stage: {stage}, matched: {matched_event}", flush=True)
        
        # STAGE 1: After listing, user selected an event → Show deterministic summary
        if context_type == "event" and stage == EventFollowupStage.LISTING_SHOWN:
            print(f"[FOLLOWUP_CONFIRM] Stage 1 triggered - showing summary for: {matched_event}", flush=True)
            
            from events_service import get_deterministic_event_summary
            
            summary_response = get_deterministic_event_summary(matched_event, conversation_history)
            
            if summary_response:
                print(f"[FOLLOWUP_CONFIRM] Returning Stage-1 summary", flush=True)
                return {
                    "response": format_numbered_lists(summary_response),
                    "sources": [],
                    "safety_triggered": False,
                    "intent": "followup_confirm_summary"
                }
        
        # STAGE 2: After summary, user wants full details → Show VERBATIM from database
        if context_type == "event" and stage == EventFollowupStage.SUMMARY_SHOWN:
            # CRITICAL: Use the event name extracted by the router, not fuzzy matching
            extracted_event = intent_result.slots.get("matched_event", "")
            print(f"[FOLLOWUP_CONFIRM] Stage 2 triggered - getting full VERBATIM details for: {extracted_event}", flush=True)
            
            # Get full VERBATIM details from calendar using extracted event name
            # Pass the event name so it doesn't need to guess from user message "y"
            from events_service import get_event_details_by_name
            confirm_event_context = get_event_details_by_name(extracted_event) if extracted_event else get_event_context_for_llm(user_message, conversation_history)
            print(f"[FOLLOWUP_CONFIRM] Got event context: {len(confirm_event_context) if confirm_event_context else 0} chars", flush=True)
            
            if confirm_event_context and "{{DIRECT_EVENT}}" in confirm_event_context:
                direct_match = re.search(r'\{\{DIRECT_EVENT\}\}(.*?)\{\{/DIRECT_EVENT\}\}', confirm_event_context, re.DOTALL)
                if direct_match:
                    response_text = direct_match.group(1).strip()
                    # Format the response properly
                    response_text = format_numbered_lists(response_text)
                    print(f"[FOLLOWUP_CONFIRM] Returning Stage-2 VERBATIM details", flush=True)
                    return {
                        "response": response_text,
                        "sources": [],
                        "safety_triggered": False,
                        "intent": "followup_confirm_details"
                    }
            else:
                print(f"[FOLLOWUP_CONFIRM] No DIRECT_EVENT marker found in context", flush=True)
        
        # Fallback: Get event context and return
        if context_type == "event":
            confirm_event_context = get_event_context_for_llm(user_message, conversation_history)
            if confirm_event_context and "{{DIRECT_EVENT}}" in confirm_event_context:
                direct_match = re.search(r'\{\{DIRECT_EVENT\}\}(.*?)\{\{/DIRECT_EVENT\}\}', confirm_event_context, re.DOTALL)
                if direct_match:
                    response_text = format_numbered_lists(direct_match.group(1).strip())
                    return {
                        "response": response_text,
                        "sources": [],
                        "safety_triggered": False,
                        "intent": "followup_confirm"
                    }
    
    # ═══════════════════════════════════════════════════════════════════════
    # INTENT-BASED DATABASE ROUTING
    # EVENT → SQL only (skip RAG to avoid pollution)
    # KNOWLEDGE → RAG only (skip events)
    # HYBRID/OTHER → Both sources
    # EVENT_DETAIL_REQUEST → Event summary for LLM to generate friendly summary
    # ═══════════════════════════════════════════════════════════════════════
    
    context = ""
    relevant_docs = []
    event_context = ""
    direct_event_content = None
    
    # Only query RAG for KNOWLEDGE, HYBRID, or OTHER intents
    if intent_result.intent in [IntentType.KNOWLEDGE, IntentType.HYBRID, IntentType.OTHER]:
        search_query = build_context_aware_query(user_message, conversation_history)
        relevant_docs = search_knowledge_base(search_query, n_results=n_context_docs)
        context = format_context_from_docs(relevant_docs)
        print(f"[IntentRouter] Queried RAG (knowledge base)", flush=True)
    
    # Note: EVENT_DETAIL_REQUEST returns early with deterministic summary above
    # Only query SQL events for EVENT or HYBRID intents
    elif intent_result.intent in [IntentType.EVENT, IntentType.HYBRID]:
        event_context = get_event_context_for_llm(user_message, conversation_history)
        print(f"[IntentRouter] Queried SQL (events database)", flush=True)
        
        # Check for DIRECT_EVENT marker - bypass LLM paraphrasing
        if "{{DIRECT_EVENT}}" in event_context and "{{/DIRECT_EVENT}}" in event_context:
            direct_match = re.search(r'\{\{DIRECT_EVENT\}\}(.*?)\{\{/DIRECT_EVENT\}\}', event_context, re.DOTALL)
            if direct_match:
                direct_event_content = direct_match.group(1).strip()
                event_context = event_context.split("{{/DIRECT_EVENT}}")[1] if "{{/DIRECT_EVENT}}" in event_context else ""
    
    # If we have direct event content for EVENT intent, return immediately without LLM
    if direct_event_content and intent_result.intent == IntentType.EVENT:
        if "I don't have any events scheduled" in direct_event_content or "No events" in direct_event_content:
            final_response = format_numbered_lists(direct_event_content)
        else:
            intro = "Here are the details for this event:\n\n"
            final_response = format_numbered_lists(intro + direct_event_content)
        
        return {
            "response": final_response,
            "sources": [],
            "safety_triggered": False,
            "safety_category": None,
            "calendar_action": False,
            "direct_event": True,
            "intent": intent_result.intent.value
        }
    
    system_prompt = get_system_prompt()
    
    personalization_context = ""
    if user_name:
        personalization_context = f"\nUSER CONTEXT:\nThe user's name is {user_name}. Address them by name naturally."
        if is_returning_user and last_topic_summary:
            personalization_context += f"""

**** CRITICAL RETURNING USER INSTRUCTION ****
This user has spoken with you before. You MUST greet them with specific details from their previous conversation.

PREVIOUS CONVERSATION SUMMARY:
{last_topic_summary}

YOUR GREETING MUST INCLUDE:
1. Their name ({user_name})
2. Acknowledge you remember them ("Great to see you back!" or similar)
3. SPECIFICALLY mention what they shared from the summary above
4. Ask if they want to continue where they left off

DO NOT give a generic greeting like "How can I help you today?" 
DO mention their specific issues and programs from the summary.
**** END CRITICAL INSTRUCTION ****
"""
        elif is_returning_user:
            personalization_context += f"""
This is a returning user but you have NO RECORD of their previous conversation topics.
Welcome them back warmly and ask how you can help today.
DO NOT mention any specific topics like "stress", "career", "relationships" or any programs as if you discussed them before.
ONLY say something like: "Great to see you back! How can I help you today?"
"""
    
    augmented_system_prompt = f"""{system_prompt}
{personalization_context}

{event_context}

KNOWLEDGE BASE CONTEXT:
The following information is from Anna Kitney's official website and documents. Use this to answer the user's question accurately:

{context}

IMPORTANT GUIDELINES:
1. STRICT KNOWLEDGE BOUNDS: Only answer questions that are EXPLICITLY addressed in the context above. If the exact topic is not covered, say: "I don't have specific information about that. Would you like me to help you connect with our team at https://www.annakitney.com/contact for more details?"
2. NO EXTRAPOLATION: Do NOT infer, guess, or extrapolate answers from loosely related information. Example: If context mentions "lifetime access to replays" but user asks about "pre-recorded sessions" - these are NOT the same thing. Do not assume one implies the other.
3. When describing programs, include key details like: what it is, who it's for, what's included, and the transformation it offers.
4. After providing program information, ALWAYS end with a follow-up question to invite deeper engagement.
5. For EVENTS: If event information is provided above, use that LIVE data from the calendar. Always offer to navigate to the event page or add to calendar.

WHEN TO DECLINE ANSWERING:
- Topic not explicitly covered in context
- User asks about specific features/offerings not clearly mentioned
- Information would require inference or assumption
In these cases, gracefully redirect to contact page or ask clarifying questions.

FOLLOW-UP QUESTIONS (choose ONE that's most relevant):
- "Would you like me to take you to the program page to learn more?"
- "Shall I share what past participants have experienced?"
- "Is there a specific aspect you'd like to explore deeper?"
- "Would you like more details about this program?"

IMPORTANT: Only ask about enrollment if the user EXPLICITLY asks about enrolling, signing up, pricing, or payment options. Do NOT proactively offer enrollment information - let them navigate to the page first.
"""

    messages = [{"role": "system", "content": augmented_system_prompt}]
    
    if conversation_history:
        formatted_history = format_conversation_history(conversation_history)
        messages.extend(formatted_history)
    
    messages.append({"role": "user", "content": user_message})
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_completion_tokens=1024
        )
        
        assistant_message = response.choices[0].message.content
        
        formatted_response = format_numbered_lists(assistant_message)
        fixed_questions_response, _ = fix_compound_trailing_questions(formatted_response)
        filtered_response, was_filtered = filter_response_for_safety(fixed_questions_response)
        
        response_with_enrollment = inject_dynamic_enrollment(filtered_response, user_message, conversation_history)
        
        response_with_checkout_urls = inject_checkout_urls(response_with_enrollment, user_message)
        
        response_with_program_links = inject_program_links(response_with_checkout_urls)
        
        response_with_calendar = response_with_program_links
        calendar_action_taken = False
        
        # Fix any hallucinated navigation URLs with correct eventPageUrl
        if "[NAVIGATE:" in response_with_program_links:
            response_with_program_links = fix_navigation_urls(response_with_program_links, conversation_history)
        
        if "[ADD_TO_CALENDAR:" in response_with_program_links:
            response_with_calendar, calendar_action_taken, _ = process_calendar_action(response_with_program_links, conversation_history)
        else:
            response_with_calendar = response_with_program_links
        
        final_response = append_contextual_links(user_message, response_with_calendar)
        
        # CRITICAL: Enforce canonical CTAs for program responses
        # This prevents the LLM from freestyling CTAs that include "enroll" prematurely
        # ONLY apply when router explicitly sets a stage - don't guess stages
        program_stage = intent_result.slots.get("stage", None)
        if program_stage and program_stage != ProgramFollowupStage.NONE:
            # Map ProgramFollowupStage enum values to enforce_trailing_cta stage strings
            # Stage indicates what was shown in PREVIOUS message
            # Map to what CTA should appear in CURRENT message
            stage_map = {
                ProgramFollowupStage.SUMMARY_SHOWN: 'details_shown',     # Previous showed summary → NOW show details + Stage 2 CTA
                ProgramFollowupStage.DETAILS_SHOWN: None,                # Previous showed details → NOW navigate (no CTA needed)
                ProgramFollowupStage.NAVIGATE_OFFERED: None,             # Navigation already offered → no CTA needed
            }
            cta_stage = stage_map.get(program_stage, None)
            if cta_stage:
                program_url = intent_result.slots.get("program_url", None)
                # Look up program URL if not provided
                if not program_url:
                    program_name = intent_result.slots.get("program_name", "")
                    from safety_guardrails import ANNA_PROGRAM_URLS
                    for name, url in ANNA_PROGRAM_URLS.items():
                        if program_name and (program_name.lower() in name.lower() or name.lower() in program_name.lower()):
                            program_url = url
                            break
                print(f"[CTA Enforcement] Applying stage: {cta_stage}, url: {program_url}", flush=True)
                final_response = enforce_trailing_cta(final_response, stage=cta_stage, program_url=program_url)
        
        sources = []
        for doc in relevant_docs:
            source = doc.get("source", "Unknown")
            if source not in sources:
                sources.append(source)
        
        return {
            "response": final_response,
            "sources": sources[:3],
            "safety_triggered": was_filtered,
            "safety_category": "output_filtered" if was_filtered else None,
            "calendar_action": calendar_action_taken,
            "intent": intent_result.intent.value
        }
        
    except Exception as e:
        error_msg = str(e)
        print(f"Error generating response: {error_msg}")
        
        if "rate limit" in error_msg.lower() or "429" in error_msg:
            return {
                "response": "I'm experiencing high demand right now. Please try again in a moment.",
                "sources": [],
                "safety_triggered": False,
                "error": "rate_limit",
                "intent": "error"
            }
        
        return {
            "response": "I apologize, but I'm having trouble processing your question right now. Please try again, or contact us at https://www.annakitney.com/contact for assistance.",
            "sources": [],
            "safety_triggered": False,
            "error": str(e),
            "intent": "error"
        }


def generate_response_stream(
    user_message: str,
    conversation_history: List[dict] = None,
    n_context_docs: int = 8,
    user_name: str = None,
    is_returning_user: bool = False,
    last_topic_summary: str = None
):
    """
    Generate a streaming response to the user's message using RAG.
    
    Yields chunks of text as they are generated by the LLM.
    Final yield is a special dict with metadata (sources, etc).
    """
    client = get_openai_client()
    if client is None:
        yield {"type": "error", "content": "I'm temporarily unavailable. Please try again later."}
        return
    
    should_redirect, redirect_response = apply_safety_filters(user_message, is_anna=True)
    
    if should_redirect:
        yield {"type": "content", "content": redirect_response}
        yield {"type": "done", "sources": [], "safety_triggered": True}
        return
    
    search_query = build_context_aware_query(user_message, conversation_history)
    relevant_docs = search_knowledge_base(search_query, n_results=n_context_docs)
    context = format_context_from_docs(relevant_docs)
    
    system_prompt = get_system_prompt()
    
    personalization_context = ""
    if user_name:
        personalization_context = f"\nUSER CONTEXT:\nThe user's name is {user_name}. Address them by name naturally."
        if is_returning_user and last_topic_summary:
            personalization_context += f"""

**** CRITICAL RETURNING USER INSTRUCTION ****
This user has spoken with you before. You MUST greet them with specific details from their previous conversation.

PREVIOUS CONVERSATION SUMMARY:
{last_topic_summary}

YOUR GREETING MUST INCLUDE:
1. Their name ({user_name})
2. Acknowledge you remember them ("Great to see you back!" or similar)
3. SPECIFICALLY mention what they shared from the summary above
4. Ask if they want to continue where they left off

DO NOT give a generic greeting like "How can I help you today?" 
DO mention their specific issues and programs from the summary.
**** END CRITICAL INSTRUCTION ****
"""
        elif is_returning_user:
            personalization_context += f"""
This is a returning user but you have NO RECORD of their previous conversation topics.
Welcome them back warmly and ask how you can help today.
DO NOT mention any specific topics like "stress", "career", "relationships" or any programs as if you discussed them before.
ONLY say something like: "Great to see you back! How can I help you today?"
"""
    
    event_context_stream = ""
    direct_event_content_stream = None
    
    if is_event_query(user_message, conversation_history):
        event_context_stream = get_event_context_for_llm(user_message, conversation_history)
        
        # Check for DIRECT_EVENT marker - bypass LLM paraphrasing
        if "{{DIRECT_EVENT}}" in event_context_stream and "{{/DIRECT_EVENT}}" in event_context_stream:
            direct_match = re.search(r'\{\{DIRECT_EVENT\}\}(.*?)\{\{/DIRECT_EVENT\}\}', event_context_stream, re.DOTALL)
            if direct_match:
                direct_event_content_stream = direct_match.group(1).strip()
                event_context_stream = event_context_stream.split("{{/DIRECT_EVENT}}")[1] if "{{/DIRECT_EVENT}}" in event_context_stream else ""
    
    # If we have direct event content, yield it immediately without LLM
    if direct_event_content_stream:
        intro = "Here are the details for this event:\n\n"
        final_response = format_numbered_lists(intro + direct_event_content_stream)
        
        # Yield as single chunk for direct event responses
        yield {"type": "content", "content": final_response}
        yield {"type": "done", "sources": [], "safety_triggered": False, "direct_event": True}
        return
    
    augmented_system_prompt = f"""{system_prompt}
{personalization_context}

{event_context_stream}

KNOWLEDGE BASE CONTEXT:
The following information is from Anna Kitney's official website and documents. Use this to answer the user's question accurately:

{context}

IMPORTANT GUIDELINES:
1. STRICT KNOWLEDGE BOUNDS: Only answer questions that are EXPLICITLY addressed in the context above. If the exact topic is not covered, say: "I don't have specific information about that. Would you like me to help you connect with our team at https://www.annakitney.com/contact for more details?"
2. NO EXTRAPOLATION: Do NOT infer, guess, or extrapolate answers from loosely related information. Example: If context mentions "lifetime access to replays" but user asks about "pre-recorded sessions" - these are NOT the same thing. Do not assume one implies the other.
3. When describing programs, include key details like: what it is, who it's for, what's included, and the transformation it offers.
4. After providing program information, ALWAYS end with a follow-up question to invite deeper engagement.
5. For EVENTS: If event information is provided above, use that LIVE data from the calendar. Always offer to navigate to the event page or add to calendar.

WHEN TO DECLINE ANSWERING:
- Topic not explicitly covered in context
- User asks about specific features/offerings not clearly mentioned
- Information would require inference or assumption
In these cases, gracefully redirect to contact page or ask clarifying questions.

FOLLOW-UP QUESTIONS (choose ONE that's most relevant):
- "Would you like me to take you to the program page to learn more?"
- "Shall I share what past participants have experienced?"
- "Is there a specific aspect you'd like to explore deeper?"
- "Would you like more details about this program?"

IMPORTANT: Only ask about enrollment if the user EXPLICITLY asks about enrolling, signing up, pricing, or payment options. Do NOT proactively offer enrollment information - let them navigate to the page first.
"""

    messages = [{"role": "system", "content": augmented_system_prompt}]
    
    if conversation_history:
        formatted_history = format_conversation_history(conversation_history)
        messages.extend(formatted_history)
    
    messages.append({"role": "user", "content": user_message})
    
    try:
        stream = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_completion_tokens=1024,
            stream=True
        )
        
        full_response = ""
        for chunk in stream:
            if chunk.choices and len(chunk.choices) > 0:
                delta = chunk.choices[0].delta
                if hasattr(delta, 'content') and delta.content:
                    content = delta.content
                    full_response += content
                    yield {"type": "content", "content": content}
        
        formatted_response = format_numbered_lists(full_response)
        fixed_questions_response, _ = fix_compound_trailing_questions(formatted_response)
        filtered_response, was_filtered = filter_response_for_safety(fixed_questions_response)
        response_with_enrollment = inject_dynamic_enrollment(filtered_response, user_message, conversation_history)
        response_with_checkout_urls = inject_checkout_urls(response_with_enrollment, user_message)
        response_with_links = inject_program_links(response_with_checkout_urls)
        final_response = append_contextual_links(user_message, response_with_links)
        
        # CRITICAL: Enforce canonical CTAs for program responses (streaming path)
        # ONLY apply when router explicitly sets a stage - don't guess stages
        program_stage = intent_result.slots.get("stage", None)
        if program_stage and program_stage != ProgramFollowupStage.NONE:
            # Stage indicates what was shown in PREVIOUS message
            # Map to what CTA should appear in CURRENT message
            stage_map = {
                ProgramFollowupStage.SUMMARY_SHOWN: 'details_shown',     # Previous showed summary → NOW show details + Stage 2 CTA
                ProgramFollowupStage.DETAILS_SHOWN: None,                # Previous showed details → NOW navigate (no CTA needed)
                ProgramFollowupStage.NAVIGATE_OFFERED: None,             # Navigation already offered → no CTA needed
            }
            cta_stage = stage_map.get(program_stage, None)
            if cta_stage:
                program_url = intent_result.slots.get("program_url", None)
                if not program_url:
                    program_name = intent_result.slots.get("program_name", "")
                    from safety_guardrails import ANNA_PROGRAM_URLS
                    for name, url in ANNA_PROGRAM_URLS.items():
                        if program_name and (program_name.lower() in name.lower() or name.lower() in program_name.lower()):
                            program_url = url
                            break
                print(f"[CTA Enforcement Stream] Applying stage: {cta_stage}", flush=True)
                final_response = enforce_trailing_cta(final_response, stage=cta_stage, program_url=program_url)
        
        sources = []
        for doc in relevant_docs:
            source = doc.get("source", "Unknown")
            if source not in sources:
                sources.append(source)
        
        yield {
            "type": "done",
            "full_response": final_response,
            "sources": sources[:3],
            "safety_triggered": was_filtered
        }
        
    except Exception as e:
        error_msg = str(e)
        print(f"Error in streaming response: {error_msg}")
        
        if "rate limit" in error_msg.lower() or "429" in error_msg:
            yield {"type": "error", "content": "I'm experiencing high demand right now. Please try again in a moment."}
        else:
            yield {"type": "error", "content": "I apologize, but I'm having trouble processing your question. Please try again."}


def get_greeting_message() -> str:
    """
    Return the curated greeting message for new conversations.
    
    IMPORTANT: This is a brand-approved curated greeting. DO NOT replace this with 
    LLM generation - the LLM produces generic responses. This structured message 
    was specifically designed to be warm and helpful.
    """
    return """Hi there! ✨ I'm Anna — your friendly guide here at Anna Kitney!

I'm here to help you explore our programs, understand our philosophy, and find what might be right for you. 💫

Are you looking for:
- Program details (Elite Private Advisory, The Ascend Collective, SoulAlign courses)
- Spiritual business coaching and mentorship
- Manifestation and abundance work
- How to get started

What brings you here today? 🌟"""


def check_knowledge_base_status() -> dict:
    """Check if the knowledge base is ready."""
    stats = get_knowledge_base_stats()
    return {
        "ready": stats["total_chunks"] > 0,
        "chunks": stats["total_chunks"],
        "last_updated": stats.get("last_scrape")
    }


def generate_conversation_summary(conversation_history: List[dict]) -> dict:
    """
    Generate a structured summary of the conversation using LLM.
    Extracts emotional themes, recommended programs, and last topics.
    """
    client = get_openai_client()
    if not client or not conversation_history:
        return None
    
    history_text = ""
    for msg in conversation_history[-10:]:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        history_text += f"{role.upper()}: {content}\n\n"
    
    summary_prompt = """Analyze this conversation and extract key information in a structured format.

CONVERSATION:
{history}

Respond in this EXACT format (use "None" if not applicable):
EMOTIONAL_THEMES: [List any emotional issues or feelings the user shared, e.g., "feeling disconnected from society", "stressed at work", "relationship struggles"]
RECOMMENDED_PROGRAMS: [List any Anna Kitney programs mentioned as recommendations, e.g., "Elite Private Advisory", "The Ascend Collective", "SoulAlign Heal"]
LAST_TOPICS: [Summarize in 1-2 sentences what the conversation was about]
CONVERSATION_STATUS: [One of: "exploring programs", "shared personal issue", "asked for contact info", "general inquiry", "follow-up needed"]

Be concise. Focus on the most important emotional themes and program recommendations."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a conversation analyzer. Extract key themes from conversations accurately and concisely."},
                {"role": "user", "content": summary_prompt.format(history=history_text)}
            ],
            temperature=0.3,
            max_tokens=300
        )
        
        summary_text = response.choices[0].message.content.strip()
        
        result = {
            'emotional_themes': None,
            'recommended_programs': None,
            'last_topics': None,
            'conversation_status': None
        }
        
        for line in summary_text.split('\n'):
            line = line.strip()
            if line.startswith('EMOTIONAL_THEMES:'):
                value = line.replace('EMOTIONAL_THEMES:', '').strip()
                if value.lower() != 'none' and value != '[]':
                    result['emotional_themes'] = value
            elif line.startswith('RECOMMENDED_PROGRAMS:'):
                value = line.replace('RECOMMENDED_PROGRAMS:', '').strip()
                if value.lower() != 'none' and value != '[]':
                    result['recommended_programs'] = value
            elif line.startswith('LAST_TOPICS:'):
                value = line.replace('LAST_TOPICS:', '').strip()
                if value.lower() != 'none':
                    result['last_topics'] = value
            elif line.startswith('CONVERSATION_STATUS:'):
                value = line.replace('CONVERSATION_STATUS:', '').strip()
                if value.lower() != 'none':
                    result['conversation_status'] = value
        
        return result
        
    except Exception as e:
        print(f"Error generating conversation summary: {e}")
        return None
