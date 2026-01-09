#!/usr/bin/env python3
"""
Test script to verify all event page URLs are correct.
Tests the full conversation flow for each event.
"""

import requests
import json
import re
import time
from typing import Dict, List, Tuple

API_URL = "http://localhost:5000/api/chat"

EXPECTED_URLS = {
    "The Identity Overflow": "https://www.annakitney.com/event/the-identity-overflow/",
    "SoulAlign® Manifestation Mastery": "https://www.annakitney.com/event/phoenixrising/",
    "Success Redefined - The Meditation: LIVE IN DUBAI": "https://www.annakitney.com/event/success-redefined-the-meditation/",
    "SoulAlign® Coach": "https://www.annakitney.com/event/soulalign-manifestation-mastery/",
    "SoulAlign® Heal": "https://www.annakitney.com/event/soulalign-heal/",
    "SoulAlign® Business 2026": "https://www.annakitney.com/event/soulalign-business-2026/",
    "The Identity Switch": "https://www.annakitney.com/event/theidentityswitch/",
}

def send_message(message: str, session_id: str, history: List[Dict]) -> Tuple[str, List[Dict]]:
    """Send a message to the chatbot and return the response."""
    payload = {
        "message": message,
        "session_id": session_id,
        "conversation_history": history
    }
    
    response = requests.post(API_URL, json=payload, timeout=30)
    response.raise_for_status()
    data = response.json()
    
    bot_response = data.get("response", "")
    
    new_history = history + [
        {"role": "user", "content": message},
        {"role": "assistant", "content": bot_response}
    ]
    
    return bot_response, new_history

def extract_navigate_url(response: str) -> str:
    """Extract the NAVIGATE URL from the response."""
    match = re.search(r'\[NAVIGATE:(https?://[^\]]+)\]', response)
    return match.group(1) if match else ""

def test_event_url(event_name: str, expected_url: str) -> Tuple[bool, str, str]:
    """
    Test the full conversation flow for an event.
    Returns (passed, actual_url, error_message)
    """
    session_id = f"test_{event_name.replace(' ', '_')}_{int(time.time())}"
    history = []
    
    try:
        response1, history = send_message(f"Tell me about {event_name}", session_id, history)
        print(f"  Step 1: Asked about event -> Got summary")
        time.sleep(0.5)
        
        response2, history = send_message("yes", session_id, history)
        print(f"  Step 2: Said yes -> Got details")
        time.sleep(0.5)
        
        response3, history = send_message("yes", session_id, history)
        print(f"  Step 3: Said yes again -> Should navigate")
        
        actual_url = extract_navigate_url(response3)
        
        if not actual_url:
            markdown_link = re.search(r'\[(?:event page|View Event Page)\]\((https?://[^)]+)\)', response3, re.IGNORECASE)
            if markdown_link:
                actual_url = markdown_link.group(1)
        
        if not actual_url:
            return False, "", f"No NAVIGATE URL found in response: {response3[:200]}..."
        
        if actual_url == expected_url:
            return True, actual_url, ""
        else:
            return False, actual_url, f"URL mismatch: expected {expected_url}, got {actual_url}"
            
    except Exception as e:
        return False, "", str(e)

def main():
    print("=" * 60)
    print("EVENT URL VERIFICATION TEST")
    print("=" * 60)
    print()
    
    print("Checking database URLs...")
    try:
        db_response = requests.get("http://localhost:5000/api/events/db", timeout=10)
        db_response.raise_for_status()
        db_events = db_response.json().get("events", [])
        print(f"Found {len(db_events)} events in database:\n")
        
        for event in db_events:
            title = event.get("title", "Unknown")
            url = event.get("eventPageUrl", "NOT SET")
            print(f"  {title}")
            print(f"    DB URL: {url}")
            if title in EXPECTED_URLS:
                expected = EXPECTED_URLS[title]
                match = "MATCH" if url == expected else "MISMATCH"
                print(f"    Expected: {expected}")
                print(f"    Status: {match}")
            print()
    except Exception as e:
        print(f"Error fetching database events: {e}")
        return
    
    print("\n" + "=" * 60)
    print("CONVERSATION FLOW TESTS")
    print("=" * 60)
    print()
    
    results = []
    
    for event_name, expected_url in EXPECTED_URLS.items():
        print(f"\nTesting: {event_name}")
        print("-" * 40)
        
        passed, actual_url, error = test_event_url(event_name, expected_url)
        
        if passed:
            print(f"  PASSED - URL: {actual_url}")
        else:
            print(f"  FAILED - {error}")
            if actual_url:
                print(f"    Actual URL: {actual_url}")
                print(f"    Expected URL: {expected_url}")
        
        results.append((event_name, passed, actual_url, expected_url, error))
        
        time.sleep(1)
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    passed_count = sum(1 for r in results if r[1])
    total_count = len(results)
    
    print(f"\nPassed: {passed_count}/{total_count}")
    print()
    
    if passed_count < total_count:
        print("FAILED TESTS:")
        for name, passed, actual, expected, error in results:
            if not passed:
                print(f"  - {name}")
                print(f"    Expected: {expected}")
                print(f"    Actual: {actual}")
                print(f"    Error: {error}")
                print()
    else:
        print("All tests passed!")
    
    return passed_count == total_count

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
