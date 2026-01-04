"""
Chatbot Engine for Anna Kitney Wellness

This module handles the core chatbot logic:
- Query processing with RAG
- Integration with OpenAI for response generation
- Context management for multi-turn conversations
"""

import os
from typing import List, Optional

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception

from knowledge_base import search_knowledge_base, get_knowledge_base_stats
from safety_guardrails import apply_safety_filters, get_system_prompt, filter_response_for_safety, inject_program_links, inject_checkout_urls, append_contextual_links, format_numbered_lists, inject_dynamic_enrollment
from events_service import is_event_query, get_event_context_for_llm, process_calendar_action

_openai_client = None


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
    
    should_redirect, redirect_response = apply_safety_filters(user_message, is_anna=True)
    
    if should_redirect:
        return {
            "response": redirect_response,
            "sources": [],
            "safety_triggered": True,
            "safety_category": "safety_redirect"
        }
    
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
    
    event_context = ""
    if is_event_query(user_message):
        event_context = get_event_context_for_llm(user_message, conversation_history)
    
    augmented_system_prompt = f"""{system_prompt}
{personalization_context}

{event_context}

KNOWLEDGE BASE CONTEXT:
The following information is from Anna Kitney's official website and documents. Use this to answer the user's question accurately:

{context}

IMPORTANT GUIDELINES:
1. Only use information from the context above. If the answer is not in the context, politely say you don't have that specific information and offer to help them contact us at https://www.annakitney.com/contact
2. When describing programs, include key details like: what it is, who it's for, what's included, and the transformation it offers.
3. After providing program information, ALWAYS end with a follow-up question to invite deeper engagement.
4. For EVENTS: If event information is provided above, use that LIVE data from the calendar. Always offer to navigate to the event page or add to calendar.

FOLLOW-UP QUESTIONS (choose ONE that's most relevant):
- "Would you like to know more about the bonuses included, or how to enroll?"
- "Shall I share what past participants have experienced?"
- "Would you like details about investment and enrollment?"
- "Is there a specific aspect you'd like to explore deeper?"
"""

    messages = [{"role": "system", "content": augmented_system_prompt}]
    
    if conversation_history:
        formatted_history = format_conversation_history(conversation_history)
        messages.extend(formatted_history)
    
    messages.append({"role": "user", "content": user_message})
    
    try:
        # the newest OpenAI model is "gpt-5" which was released August 7, 2025.
        # do not change this unless explicitly requested by the user
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_completion_tokens=1024
        )
        
        assistant_message = response.choices[0].message.content
        
        formatted_response = format_numbered_lists(assistant_message)
        filtered_response, was_filtered = filter_response_for_safety(formatted_response)
        
        response_with_enrollment = inject_dynamic_enrollment(filtered_response, user_message, conversation_history)
        
        response_with_checkout_urls = inject_checkout_urls(response_with_enrollment, user_message)
        
        response_with_program_links = inject_program_links(response_with_checkout_urls)
        
        response_with_calendar = response_with_program_links
        calendar_action_taken = False
        if "[ADD_TO_CALENDAR:" in response_with_program_links:
            response_with_calendar, calendar_action_taken, _ = process_calendar_action(response_with_program_links, conversation_history)
        
        final_response = append_contextual_links(user_message, response_with_calendar)
        
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
            "calendar_action": calendar_action_taken
        }
        
    except Exception as e:
        error_msg = str(e)
        print(f"Error generating response: {error_msg}")
        
        if "rate limit" in error_msg.lower() or "429" in error_msg:
            return {
                "response": "I'm experiencing high demand right now. Please try again in a moment.",
                "sources": [],
                "safety_triggered": False,
                "error": "rate_limit"
            }
        
        return {
            "response": "I apologize, but I'm having trouble processing your question right now. Please try again, or contact us at https://www.annakitney.com/contact for assistance.",
            "sources": [],
            "safety_triggered": False,
            "error": str(e)
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
    if is_event_query(user_message):
        event_context_stream = get_event_context_for_llm(user_message, conversation_history)
    
    augmented_system_prompt = f"""{system_prompt}
{personalization_context}

{event_context_stream}

KNOWLEDGE BASE CONTEXT:
The following information is from Anna Kitney's official website and documents. Use this to answer the user's question accurately:

{context}

IMPORTANT GUIDELINES:
1. Only use information from the context above. If the answer is not in the context, politely say you don't have that specific information and offer to help them contact us at https://www.annakitney.com/contact
2. When describing programs, include key details like: what it is, who it's for, what's included, and the transformation it offers.
3. After providing program information, ALWAYS end with a follow-up question to invite deeper engagement.
4. For EVENTS: If event information is provided above, use that LIVE data from the calendar. Always offer to navigate to the event page or add to calendar.

FOLLOW-UP QUESTIONS (choose ONE that's most relevant):
- "Would you like to know more about the bonuses included, or how to enroll?"
- "Shall I share what past participants have experienced?"
- "Would you like details about investment and enrollment?"
- "Is there a specific aspect you'd like to explore deeper?"
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
        filtered_response, was_filtered = filter_response_for_safety(formatted_response)
        response_with_enrollment = inject_dynamic_enrollment(filtered_response, user_message, conversation_history)
        response_with_checkout_urls = inject_checkout_urls(response_with_enrollment, user_message)
        response_with_links = inject_program_links(response_with_checkout_urls)
        final_response = append_contextual_links(user_message, response_with_links)
        
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
    """Return the initial greeting message for new conversations."""
    return """Hi there, I'm Anna — your friendly guide here at Anna Kitney!

I'm here to help you explore our programs, understand our philosophy, and find what might be right for you.

Are you looking for:
- Program details (Elite Private Advisory, The Ascend Collective, SoulAlign courses)
- Spiritual business coaching and mentorship
- Manifestation and abundance work
- How to get started

What brings you here today?"""


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
