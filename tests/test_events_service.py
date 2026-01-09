#!/usr/bin/env python3
"""
Unit tests for events_service.py - Tests date parsing, month filtering, fuzzy matching.

Run with: pytest tests/test_events_service.py -v
"""

import pytest
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from events_service import (
    extract_month_filter,
    filter_events_by_month,
    is_date_in_event_range,
    extract_specific_date,
    find_matching_events,
)


class TestMonthExtraction:
    """Tests for extract_month_filter function."""
    
    @pytest.mark.parametrize("query,expected_month", [
        ("What events are in March?", 3),
        ("Show me events in April", 4),
        ("Any events happening in May?", 5),
        ("Events in June 2026", 6),
        ("What's happening in September?", 9),
        ("January events", 1),
        ("February workshops", 2),
        ("events in march", 3),  # lowercase
        ("EVENTS IN DECEMBER", 12),  # uppercase
    ])
    def test_month_extraction_basic(self, query, expected_month):
        """Test basic month extraction from queries."""
        result = extract_month_filter(query)
        assert result == expected_month, f"Expected month {expected_month} for '{query}', got {result}"
    
    @pytest.mark.parametrize("query,expected_month", [
        ("What about in May?", 5),
        ("How about June?", 6),
        ("And in September?", 9),
        ("What about March 2026?", 3),
        ("And what about April?", 4),
    ])
    def test_month_followup_queries(self, query, expected_month):
        """
        CRITICAL: Follow-up queries like 'What about in May?' should extract month.
        
        This was a bug where these queries fell through to conversation history.
        """
        result = extract_month_filter(query)
        assert result == expected_month, \
            f"Follow-up '{query}' should extract month {expected_month}, got {result}"
    
    @pytest.mark.parametrize("query", [
        "What events do you have?",
        "Tell me about SoulAlign Coach",
        "Hello",
        "Yes please",
        "1",
    ])
    def test_no_month_extraction(self, query):
        """Test that queries without months return None."""
        result = extract_month_filter(query)
        assert result is None, f"'{query}' should not extract a month, got {result}"


class TestDateParsing:
    """Tests for date parsing from queries."""
    
    @pytest.mark.parametrize("query", [
        "Events on June 15",
        "What's happening on March 20?",
        "Is there anything on April 5th?",
        "Events on the 10th of May",
    ])
    def test_specific_date_extraction(self, query):
        """Test extraction of specific dates from queries."""
        result = extract_specific_date(query)
        # Should return a tuple (year, month, day) or similar
        assert result is not None, f"Should extract date from '{query}'"
    
    @pytest.mark.parametrize("query", [
        "April 2026",  # Month + year, NOT April 20
        "March 2026",
        "June 2026",
    ])
    def test_month_year_not_parsed_as_date(self, query):
        """
        CRITICAL: 'April 2026' should NOT be parsed as 'April 20, 2026'.
        
        The '20' in '2026' should not be captured as a day number.
        """
        result = extract_specific_date(query)
        if result:
            year, month, day = result
            # If parsed, the day should NOT be 20
            assert day != 20 or month != 4, \
                f"'{query}' parsed incorrectly - '2026' was captured as day 20"
    
    def test_date_with_ordinal_suffix(self):
        """Test dates with ordinal suffixes (1st, 2nd, 3rd, etc.)."""
        result = extract_specific_date("Events on June 1st")
        assert result is not None
        if result:
            year, month, day = result
            assert day == 1
            assert month == 6
    
    def test_date_range_query(self):
        """Test date range queries."""
        result = extract_specific_date("Events between March 1 and March 15")
        # May or may not extract - depends on implementation
        # Just verify it doesn't crash


class TestDateRangeMatching:
    """Tests for checking if a date falls within an event's date range."""
    
    def test_date_within_range(self):
        """Test that a date within event range returns True."""
        event = {
            "startDate": "2026-03-04T00:00:00Z",
            "endDate": "2026-05-20T00:00:00Z"
        }
        
        # March 15 should be within range - tuple format: (year, month, day)
        query_date = (2026, 3, 15)
        result = is_date_in_event_range(query_date, event)
        assert result is True, "March 15 should be within March 4 - May 20 range"
    
    def test_date_outside_range(self):
        """Test that a date outside event range returns False."""
        event = {
            "startDate": "2026-03-04T00:00:00Z",
            "endDate": "2026-05-20T00:00:00Z"
        }
        
        # June 1 should be outside range
        query_date = (2026, 6, 1)
        result = is_date_in_event_range(query_date, event)
        assert result is False, "June 1 should be outside March 4 - May 20 range"
    
    def test_date_on_start_boundary(self):
        """Test that start date is included in range."""
        event = {
            "startDate": "2026-03-04T00:00:00Z",
            "endDate": "2026-05-20T00:00:00Z"
        }
        
        query_date = (2026, 3, 4)
        result = is_date_in_event_range(query_date, event)
        assert result is True, "Start date should be included in range"
    
    def test_date_on_end_boundary(self):
        """Test that end date is included in range."""
        event = {
            "startDate": "2026-03-04T00:00:00Z",
            "endDate": "2026-05-20T00:00:00Z"
        }
        
        query_date = (2026, 5, 20)
        result = is_date_in_event_range(query_date, event)
        assert result is True, "End date should be included in range"


class TestMonthFiltering:
    """Tests for filter_events_by_month function."""
    
    @pytest.fixture
    def sample_events(self):
        """Sample events for testing."""
        return [
            {
                "id": 1,
                "title": "SoulAlign® Coach",
                "startDate": "2026-03-04T00:00:00Z",
                "endDate": "2026-05-20T00:00:00Z"
            },
            {
                "id": 2,
                "title": "SoulAlign® Heal",
                "startDate": "2026-06-03T00:00:00Z",
                "endDate": "2026-09-30T00:00:00Z"
            },
            {
                "id": 3,
                "title": "SoulAlign® Business",
                "startDate": "2026-09-08T00:00:00Z",
                "endDate": "2026-10-27T00:00:00Z"
            }
        ]
    
    def test_filter_march(self, sample_events):
        """Test filtering events for March."""
        result = filter_events_by_month(sample_events, 3)
        assert len(result) == 1
        assert result[0]["title"] == "SoulAlign® Coach"
    
    def test_filter_may_spans_event(self, sample_events):
        """Test that May finds event that spans March-May."""
        result = filter_events_by_month(sample_events, 5)
        assert len(result) == 1
        assert result[0]["title"] == "SoulAlign® Coach"
    
    def test_filter_june(self, sample_events):
        """Test filtering events for June."""
        result = filter_events_by_month(sample_events, 6)
        assert len(result) == 1
        assert result[0]["title"] == "SoulAlign® Heal"
    
    def test_filter_september_multiple(self, sample_events):
        """Test September finds multiple overlapping events."""
        result = filter_events_by_month(sample_events, 9)
        assert len(result) == 2
        titles = [e["title"] for e in result]
        assert "SoulAlign® Heal" in titles
        assert "SoulAlign® Business" in titles
    
    def test_filter_no_events(self, sample_events):
        """Test filtering for month with no events."""
        result = filter_events_by_month(sample_events, 1)  # January
        assert len(result) == 0


class TestFuzzyMatching:
    """Tests for find_matching_events fuzzy matching."""
    
    @pytest.fixture
    def sample_events(self):
        """Sample events for fuzzy matching tests."""
        return [
            {"id": 1, "title": "SoulAlign® Coach", "description": "Coaching certification"},
            {"id": 2, "title": "SoulAlign® Heal", "description": "Healing program"},
            {"id": 3, "title": "SoulAlign® Business 2026", "description": "Business training"},
        ]
    
    def test_exact_match(self, sample_events):
        """Test exact title matching."""
        matches = find_matching_events("SoulAlign Coach", sample_events)
        assert len(matches) > 0
        assert matches[0][0]["title"] == "SoulAlign® Coach"
    
    def test_partial_match(self, sample_events):
        """Test partial matching."""
        matches = find_matching_events("coach", sample_events)
        assert len(matches) > 0
        # Coach should be the top match
        assert "Coach" in matches[0][0]["title"]
    
    def test_fuzzy_match_typo(self, sample_events):
        """Test fuzzy matching with typos."""
        matches = find_matching_events("SoulAlign Couch", sample_events)  # typo
        # Should still find Coach as close match
        assert len(matches) > 0
    
    def test_no_match(self, sample_events):
        """Test query with no matches."""
        matches = find_matching_events("completely random text xyz", sample_events)
        # Should return empty or very low scores
        if matches:
            assert matches[0][1] < 0.3  # Low confidence


class TestEventContextGeneration:
    """Tests for get_event_context_for_llm function."""
    
    def test_month_query_returns_month_events(self):
        """Test that month queries return month-filtered events."""
        from events_service import get_event_context_for_llm
        
        result = get_event_context_for_llm("What about in May?", [])
        
        # Should contain month-related content
        assert "MAY" in result.upper() or "May" in result, \
            f"Month query should mention May in response: {result[:200]}"
    
    def test_general_event_query_returns_list(self):
        """Test that general event queries return event list."""
        from events_service import get_event_context_for_llm
        
        result = get_event_context_for_llm("What events do you have?", [])
        
        # Should contain event list
        assert "1." in result or "event" in result.lower(), \
            f"Should return event list: {result[:200]}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
