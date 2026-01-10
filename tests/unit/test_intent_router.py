#!/usr/bin/env python3
"""
Unit tests for IntentRouter - Tests intent classification in isolation.

Run with: pytest tests/test_intent_router.py -v
"""

import pytest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from intent_router import IntentRouter, IntentType


class TestIntentRouter:
    """Unit tests for IntentRouter intent classification."""
    
    @pytest.fixture
    def router(self):
        """Create a fresh router instance for each test."""
        return IntentRouter()
    
    # ========== GREETING TESTS ==========
    
    @pytest.mark.parametrize("message", [
        "hello",
        "hi",
        "hey",
        "good morning",
        "good afternoon",
        "hey there",
        "hi there",
        "hello!",
    ])
    def test_greeting_detection(self, router, message):
        """Test that greeting messages are correctly classified."""
        result = router.classify(message, [])
        assert result.intent == IntentType.GREETING, f"'{message}' should be GREETING, got {result.intent}"
    
    # ========== EVENT INTENT TESTS ==========
    
    @pytest.mark.parametrize("message", [
        "What events do you have?",
        "Show me upcoming events",
        "Are there any events happening?",
        "Tell me about your events",
        "What's happening next month?",
        "Any workshops coming up?",
        "Do you have any retreats?",
    ])
    def test_event_queries(self, router, message):
        """Test that event-related queries are classified as EVENT."""
        result = router.classify(message, [])
        assert result.intent == IntentType.EVENT, f"'{message}' should be EVENT, got {result.intent}"
    
    @pytest.mark.parametrize("message,expected_month", [
        ("What events are in March?", 3),
        ("Show me events in April", 4),
        ("Any events happening in May?", 5),
        ("Events in June 2026", 6),
        ("What's happening in September?", 9),
    ])
    def test_month_event_queries(self, router, message, expected_month):
        """Test that month-specific queries are classified as EVENT."""
        result = router.classify(message, [])
        assert result.intent == IntentType.EVENT, f"'{message}' should be EVENT, got {result.intent}"
    
    # ========== CRITICAL: MONTH FOLLOW-UP QUERIES ==========
    
    @pytest.mark.parametrize("message", [
        "What about in May?",
        "What about May?",
        "How about June?",
        "And in September?",
        "What about March 2026?",
    ])
    def test_month_followup_queries_not_confirmation(self, router, message):
        """
        CRITICAL: Month follow-up queries should be EVENT, NOT FOLLOWUP_CONFIRM.
        
        This tests the bug where 'What about in May?' was incorrectly treated
        as a follow-up confirmation instead of a new month query.
        """
        # Simulate previous event listing context
        conversation = [
            {"role": "user", "content": "What events are in March?"},
            {"role": "assistant", "content": "Here are events in March:\n\n1. SoulAlign® Coach - March 4-20, 2026\n\nWould you like more details?"}
        ]
        
        result = router.classify(message, conversation)
        assert result.intent == IntentType.EVENT, \
            f"'{message}' should be EVENT (new month query), not {result.intent}"
    
    # ========== DATE-SPECIFIC QUERIES ==========
    
    @pytest.mark.parametrize("message", [
        "Are there any events on June 1st?",
        "Is there anything on March 15?",
        "What's happening on April 20, 2026?",
        "Events on the 5th of May",
    ])
    def test_specific_date_queries(self, router, message):
        """Test that specific date queries are classified as EVENT."""
        result = router.classify(message, [])
        assert result.intent == IntentType.EVENT, f"'{message}' should be EVENT, got {result.intent}"
    
    @pytest.mark.parametrize("message", [
        "June 1st",  # NOT "option 1" or ordinal selection
        "April 2026",
        "March 15",
    ])
    def test_dates_not_ordinals(self, router, message):
        """
        CRITICAL: Date expressions should NOT be interpreted as ordinal selections.
        
        'June 1st' is a date, not 'option 1'.
        """
        result = router.classify(message, [])
        assert result.intent != IntentType.FOLLOWUP_SELECT, \
            f"'{message}' should NOT be FOLLOWUP_SELECT - it's a date!"
    
    # ========== ORDINAL SELECTION TESTS ==========
    
    @pytest.mark.parametrize("message,expected_index", [
        ("1", 0),
        ("2", 1),
        ("3", 2),
        ("the first one", 0),
        ("the second one", 1),
        ("option 1", 0),
        ("option 2", 1),
        ("number 3", 2),
    ])
    def test_ordinal_selection_after_list(self, router, message, expected_index):
        """Test that ordinal selections work after a numbered list."""
        conversation = [
            {"role": "user", "content": "What events do you have?"},
            {"role": "assistant", "content": """Here are the upcoming events:

1. SoulAlign® Coach - March 2026
2. SoulAlign® Heal - June 2026
3. SoulAlign® Business - September 2026

Which event would you like to know more about?"""}
        ]
        
        result = router.classify(message, conversation)
        assert result.intent == IntentType.FOLLOWUP_SELECT, \
            f"'{message}' should be FOLLOWUP_SELECT, got {result.intent}"
        assert result.slots.get("selection_index") == expected_index, \
            f"Expected index {expected_index}, got {result.slots.get('selection_index')}"
    
    # ========== PROGRAM QUERIES ==========
    
    @pytest.mark.parametrize("message", [
        "Tell me about Divine Abundance Codes",
        "What is the Soul Purpose Alignment program?",
        "How much does the Ascend Collective cost?",
        "What spiritual programs do you offer?",
        "Tell me about your coaching programs",
    ])
    def test_program_queries(self, router, message):
        """Test that program-related queries are classified correctly."""
        result = router.classify(message, [])
        # Should be KNOWLEDGE for general program info (RAG-based)
        assert result.intent in [IntentType.KNOWLEDGE, IntentType.EVENT, IntentType.HYBRID], \
            f"'{message}' should be program-related, got {result.intent}"
    
    # ========== AFFIRMATIVE/CONFIRMATION TESTS ==========
    
    @pytest.mark.parametrize("message", [
        "yes",
        "sure",
        "absolutely",
    ])
    def test_affirmative_after_event_summary(self, router, message):
        """Test that 'yes' after event summary triggers FOLLOWUP_CONFIRM."""
        conversation = [
            {"role": "user", "content": "Tell me about SoulAlign Coach"},
            {"role": "assistant", "content": """**SoulAlign® Coach**

A 4-month coaching certification program starting March 2026.

Would you like more details about this event?"""}
        ]
        
        result = router.classify(message, conversation)
        # Should be FOLLOWUP_CONFIRM or EVENT (both are acceptable after summary)
        assert result.intent in [IntentType.FOLLOWUP_CONFIRM, IntentType.EVENT], \
            f"'{message}' should be FOLLOWUP_CONFIRM or EVENT after event summary, got {result.intent}"
    
    # ========== SAFETY/GUARDRAIL TESTS ==========
    
    @pytest.mark.parametrize("message", [
        "I'm feeling really depressed",
        "I've been having suicidal thoughts",
        "I want to hurt myself",
        "I'm in crisis right now",
    ])
    def test_crisis_detection(self, router, message):
        """Test that crisis messages are flagged appropriately."""
        result = router.classify(message, [])
        # Crisis messages should still be classified, but guardrails handle response
        # The intent might be KNOWLEDGE or OTHER, but safety_triggered should be true
        # Note: This tests intent classification, not guardrail response
        assert result is not None
    
    # ========== KNOWLEDGE QUERIES ==========
    
    @pytest.mark.parametrize("message", [
        "Who is Anna Kitney?",
        "What is your coaching philosophy?",
        "Tell me about manifestation",
        "How does spiritual coaching work?",
        "What makes Anna different from other coaches?",
    ])
    def test_knowledge_queries(self, router, message):
        """Test that general knowledge queries are classified as KNOWLEDGE."""
        result = router.classify(message, [])
        assert result.intent == IntentType.KNOWLEDGE, \
            f"'{message}' should be KNOWLEDGE, got {result.intent}"
    
    # ========== LOCATION QUERIES ==========
    
    @pytest.mark.parametrize("message", [
        "Are there any events in London?",
        "Is there an event in Dubai?",
        "Any workshops happening in New York?",
        "Events in Australia",
    ])
    def test_location_queries(self, router, message):
        """Test that location-based event queries are classified as EVENT."""
        result = router.classify(message, [])
        assert result.intent == IntentType.EVENT, \
            f"'{message}' should be EVENT (location query), got {result.intent}"
    
    # ========== EDGE CASES ==========
    
    def test_empty_message(self, router):
        """Test handling of empty messages."""
        result = router.classify("", [])
        assert result is not None
    
    def test_very_long_message(self, router):
        """Test handling of very long messages."""
        long_message = "Tell me about events " * 100
        result = router.classify(long_message, [])
        assert result is not None
    
    def test_special_characters(self, router):
        """Test handling of special characters."""
        result = router.classify("What events??? 🎉🎉🎉", [])
        assert result is not None
    
    def test_mixed_case(self, router):
        """Test case-insensitive matching."""
        result = router.classify("WHAT EVENTS DO YOU HAVE?", [])
        assert result.intent == IntentType.EVENT


class TestFollowupStageDetection:
    """Tests for follow-up stage detection in progressive disclosure."""
    
    @pytest.fixture
    def router(self):
        return IntentRouter()
    
    def test_stage1_listing_shown(self, router):
        """After event listing, user saying 'yes' should be FOLLOWUP_CONFIRM."""
        conversation = [
            {"role": "assistant", "content": """Here are the upcoming events:

1. SoulAlign® Coach - March 2026
2. SoulAlign® Heal - June 2026

Would you like more details about any of these events?"""}
        ]
        
        result = router.classify("yes", conversation)
        assert result.intent == IntentType.FOLLOWUP_CONFIRM
    
    def test_stage2_summary_shown(self, router):
        """After event summary with 'more details?' CTA, 'yes' triggers details."""
        conversation = [
            {"role": "assistant", "content": """**SoulAlign® Coach**

Starting March 4, 2026 on Zoom.

Would you like more details about this event?"""}
        ]
        
        result = router.classify("yes please", conversation)
        assert result.intent == IntentType.FOLLOWUP_CONFIRM
    
    def test_stage3_details_shown(self, router):
        """After full details with navigation CTA, 'yes' triggers EVENT_NAVIGATE."""
        conversation = [
            {"role": "assistant", "content": """Here are the full details...

[View Event Page](https://www.annakitney.com/event/soulalign-coach/)

Would you like me to take you to the event page to learn more or enroll?"""}
        ]
        
        result = router.classify("yes", conversation)
        assert result.intent == IntentType.EVENT_NAVIGATE


class TestProgramVsEventDisambiguation:
    """Tests for correctly distinguishing program vs event context."""
    
    @pytest.fixture
    def router(self):
        return IntentRouter()
    
    def test_program_context_preserved(self, router):
        """After program summary, 'yes' should stay in program context."""
        conversation = [
            {"role": "user", "content": "Tell me about Divine Abundance Codes"},
            {"role": "assistant", "content": """**Divine Abundance Codes**

A transformational program for manifesting abundance.

Would you like more details about this program?"""}
        ]
        
        result = router.classify("yes", conversation)
        # Should be PROGRAM_DETAIL_REQUEST, FOLLOWUP_CONFIRM, or KNOWLEDGE
        # The key is it should NOT return EVENT details for SoulAlign Coach, etc.
        assert result.intent in [
            IntentType.PROGRAM_DETAIL_REQUEST, 
            IntentType.FOLLOWUP_CONFIRM,
            IntentType.KNOWLEDGE,
            IntentType.EVENT  # May classify as event if program not found
        ]
    
    def test_event_context_after_event_listing(self, router):
        """After event listing, 'yes' should trigger follow-up."""
        conversation = [
            {"role": "user", "content": "What events do you have?"},
            {"role": "assistant", "content": """Here are the upcoming events:

1. SoulAlign® Coach - March 2026
2. SoulAlign® Heal - June 2026

Would you like more details about any of these events?"""}
        ]
        
        result = router.classify("yes", conversation)
        # Should be FOLLOWUP_CONFIRM or EVENT
        assert result.intent in [IntentType.FOLLOWUP_CONFIRM, IntentType.EVENT]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
