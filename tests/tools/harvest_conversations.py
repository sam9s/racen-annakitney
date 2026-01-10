#!/usr/bin/env python3
"""
Conversation Harvest Tool

Imports exported conversations from the admin dashboard and generates test fixtures.
This automates the process of turning real-world user interactions into regression tests.

Usage:
    python tests/tools/harvest_conversations.py --input export.json --output tests/scenarios/regression/
    python tests/tools/harvest_conversations.py --fetch --output tests/scenarios/regression/
"""

import argparse
import json
import os
import re
import hashlib
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from pathlib import Path


# Issue categories based on flag reasons and heuristics
ISSUE_CATEGORIES = {
    "cta_decline": "User declined a follow-up CTA but bot continued anyway",
    "wrong_event": "Bot showed wrong event or confused event context",
    "date_parse": "Date/time parsing or interpretation error",
    "context_switch": "Bot failed to handle topic/context switch",
    "extrapolation": "Bot extrapolated answer from loosely related info",
    "wrong_answer": "Factually incorrect or inaccurate response",
    "confusing": "Response was unclear or hard to understand",
    "not_helpful": "Response didn't address user's question",
    "repeated_info": "Bot repeated information unnecessarily",
    "technical_issue": "Technical error in response formatting",
    "other": "Other issue"
}

# Heuristic patterns for auto-categorization
CATEGORY_PATTERNS = {
    "cta_decline": [
        r"\b(no|nope|nah|not now|maybe later|no thanks?)\b",
    ],
    "date_parse": [
        r"\b(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{4}\b",
        r"\b\d{1,2}/\d{1,2}/\d{2,4}\b",
    ],
    "context_switch": [
        r"\b(actually|instead|never ?mind|forget that|different|change)\b",
    ],
}


def load_export_file(filepath: str) -> Dict:
    """Load exported conversations from JSON file."""
    with open(filepath, 'r') as f:
        return json.load(f)


def detect_issue_category(conversation: Dict) -> Tuple[str, float]:
    """
    Detect issue category from conversation using flag info and heuristics.
    Returns (category, confidence).
    """
    # Priority 1: Use flag reason if available
    flag_info = conversation.get("flagInfo")
    if flag_info:
        reason = flag_info.get("reason", "other")
        category = flag_info.get("category")
        if category:
            return category, 1.0
        if reason in ISSUE_CATEGORIES:
            return reason, 0.9
    
    # Priority 2: Heuristic detection from user question
    user_q = conversation.get("userQuestion", "").lower()
    bot_a = conversation.get("botAnswer", "").lower()
    
    for category, patterns in CATEGORY_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, user_q, re.IGNORECASE):
                # Check if it looks like a problem scenario
                if category == "cta_decline" and "event" in bot_a:
                    return category, 0.7
                if category == "date_parse":
                    return category, 0.6
                if category == "context_switch":
                    return category, 0.5
    
    return "other", 0.3


def generate_test_id(conversation: Dict) -> str:
    """Generate a unique test ID from conversation content."""
    content = f"{conversation.get('userQuestion', '')}{conversation.get('timestamp', '')}"
    hash_val = hashlib.sha256(content.encode()).hexdigest()[:8]
    return f"regression_{hash_val}"


def conversation_to_scenario(conversation: Dict, category: str) -> Dict:
    """
    Convert a single conversation exchange to a test scenario.
    
    The scenario format matches the existing scenario runner structure.
    """
    history = conversation.get("conversationHistory", [])
    
    # Build conversation turns
    turns = []
    for i in range(0, len(history), 2):
        if i + 1 < len(history):
            turn = {
                "user": history[i].get("content", ""),
                "expected_patterns": [],  # Will need manual review
                "unexpected_patterns": [],
            }
            turns.append(turn)
    
    # Add the flagged turn
    flagged_turn = {
        "user": conversation.get("userQuestion", ""),
        "expected_patterns": [],  # Needs manual review
        "unexpected_patterns": [],
        "notes": f"FLAGGED: {conversation.get('flagInfo', {}).get('notes', 'No notes')}"
    }
    turns.append(flagged_turn)
    
    scenario = {
        "id": generate_test_id(conversation),
        "name": f"Regression: {category} - {conversation.get('userQuestion', '')[:50]}",
        "description": f"Auto-generated from flagged conversation. Category: {category}",
        "category": category,
        "source": "harvest",
        "original_timestamp": conversation.get("timestamp"),
        "conversation": turns,
        "validation": {
            "requires_manual_review": True,
            "expected_intent": None,
            "critical": category in ["wrong_event", "extrapolation", "wrong_answer"],
        },
        "metadata": {
            "flag_reason": conversation.get("flagInfo", {}).get("reason"),
            "flag_notes": conversation.get("flagInfo", {}).get("notes"),
            "anonymized_session": conversation.get("anonymizedSessionId"),
        }
    }
    
    return scenario


def generate_unit_test_stub(conversation: Dict, category: str) -> str:
    """Generate a Python unit test stub for the intent router."""
    test_id = generate_test_id(conversation)
    user_q = conversation.get("userQuestion", "").replace('"', '\\"')
    
    # Build history for context
    history = conversation.get("conversationHistory", [])
    history_str = json.dumps(history[-4:], indent=8) if history else "[]"
    
    test_code = f'''
def test_{test_id}():
    """
    Regression test for {category} issue.
    User question: {user_q[:80]}
    """
    from intent_router import get_intent_router, IntentType
    
    router = get_intent_router()
    history = {history_str}
    
    result = router.classify("{user_q}", history)
    
    # TODO: Add assertions based on expected behavior
    # Current behavior produced a {category} issue
    # Expected intent: ???
    # assert result.intent == IntentType.???
    pass
'''
    return test_code


def process_export(export_data: Dict, output_dir: str) -> Dict:
    """
    Process exported conversations and generate test fixtures.
    
    Returns summary of generated files.
    """
    conversations = export_data.get("conversations", [])
    
    if not conversations:
        return {"error": "No conversations in export", "count": 0}
    
    # Create output directories
    scenario_dir = Path(output_dir) / "scenarios"
    unit_dir = Path(output_dir) / "unit"
    scenario_dir.mkdir(parents=True, exist_ok=True)
    unit_dir.mkdir(parents=True, exist_ok=True)
    
    # Group by category
    by_category: Dict[str, List] = {}
    unit_tests = []
    
    for conv in conversations:
        category, confidence = detect_issue_category(conv)
        
        if category not in by_category:
            by_category[category] = []
        
        scenario = conversation_to_scenario(conv, category)
        scenario["detection_confidence"] = confidence
        by_category[category].append(scenario)
        
        # Generate unit test stub
        unit_tests.append(generate_unit_test_stub(conv, category))
    
    # Write scenario files by category
    scenario_files = []
    for category, scenarios in by_category.items():
        filename = f"regression_{category}.json"
        filepath = scenario_dir / filename
        
        output = {
            "generated_at": datetime.utcnow().isoformat(),
            "category": category,
            "description": ISSUE_CATEGORIES.get(category, "Unknown category"),
            "scenarios": scenarios,
            "requires_review": True,
        }
        
        with open(filepath, 'w') as f:
            json.dump(output, f, indent=2)
        
        scenario_files.append(str(filepath))
    
    # Write unit test stubs
    unit_filepath = unit_dir / "test_regression_stubs.py"
    with open(unit_filepath, 'w') as f:
        f.write('"""Auto-generated regression test stubs. Requires manual review."""\n\n')
        f.write("import pytest\n\n")
        for test in unit_tests:
            f.write(test)
            f.write("\n")
    
    return {
        "count": len(conversations),
        "categories": {cat: len(scenarios) for cat, scenarios in by_category.items()},
        "scenario_files": scenario_files,
        "unit_test_file": str(unit_filepath),
    }


def fetch_from_api(base_url: str = "http://localhost:5000") -> Dict:
    """Fetch flagged conversations from the API."""
    import requests
    
    # This requires admin authentication - for now just provide instructions
    print("To fetch from API, you need admin authentication.")
    print("Alternative: Export from admin dashboard and use --input flag.")
    return {"conversations": []}


def main():
    parser = argparse.ArgumentParser(description="Harvest conversations for test generation")
    parser.add_argument("--input", "-i", help="Path to exported JSON file")
    parser.add_argument("--fetch", "-f", action="store_true", help="Fetch from API (requires auth)")
    parser.add_argument("--output", "-o", default="tests/scenarios/regression", help="Output directory")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    if not args.input and not args.fetch:
        parser.print_help()
        print("\nError: Must specify --input file or --fetch flag")
        return 1
    
    # Load data
    if args.input:
        if not os.path.exists(args.input):
            print(f"Error: File not found: {args.input}")
            return 1
        export_data = load_export_file(args.input)
        print(f"Loaded {len(export_data.get('conversations', []))} conversations from {args.input}")
    else:
        export_data = fetch_from_api()
    
    # Process and generate
    result = process_export(export_data, args.output)
    
    if "error" in result:
        print(f"Error: {result['error']}")
        return 1
    
    print(f"\n=== Harvest Complete ===")
    print(f"Processed: {result['count']} conversations")
    print(f"Categories: {result['categories']}")
    print(f"\nGenerated files:")
    for f in result.get('scenario_files', []):
        print(f"  - {f}")
    print(f"  - {result.get('unit_test_file')}")
    print(f"\nNOTE: Generated tests require manual review before running!")
    
    return 0


if __name__ == "__main__":
    exit(main())
