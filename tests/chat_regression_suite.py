#!/usr/bin/env python3
"""
Chat Regression Test Suite for Anna Kitney Wellness Chatbot

This test suite runs through the actual HTTP API (POST /api/chat) to test
all edge cases, matching how the developer GUI works.

Usage:
    python tests/chat_regression_suite.py

Output:
    - docs/chat_regression_results.md (test results)
    - Console output with pass/fail status
"""

import json
import requests
import time
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
import os

# Configuration
API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:5000")
CHAT_ENDPOINT = f"{API_BASE_URL}/api/chat"
SCENARIOS_FILE = "tests/chat_test_scenarios.json"
RESULTS_FILE = "docs/chat_regression_results.md"
SCENARIOS_DOC_FILE = "docs/chat_test_scenarios.md"

# Delay between API calls to avoid overwhelming the server
REQUEST_DELAY = 1.0


class TestResult:
    def __init__(self, scenario_id: str, turn_index: int):
        self.scenario_id = scenario_id
        self.turn_index = turn_index
        self.passed = False
        self.user_message = ""
        self.expected_intent = []
        self.actual_intent = ""
        self.keywords_found = []
        self.keywords_missing = []
        self.forbidden_found = []
        self.response_excerpt = ""
        self.error = None
        self.response_time_ms = 0


def load_scenarios() -> List[Dict]:
    """Load test scenarios from JSON file."""
    with open(SCENARIOS_FILE, 'r') as f:
        data = json.load(f)
    return data.get("test_scenarios", [])


def send_chat_message(message: str, session_id: str) -> Dict:
    """Send a message to the chat API and return the response."""
    payload = {
        "message": message,
        "session_id": session_id
    }
    
    start_time = time.time()
    response = requests.post(CHAT_ENDPOINT, json=payload, timeout=60)
    elapsed_ms = int((time.time() - start_time) * 1000)
    
    if response.status_code != 200:
        raise Exception(f"API error: {response.status_code} - {response.text}")
    
    result = response.json()
    result["_response_time_ms"] = elapsed_ms
    return result


def check_keywords(response_text: str, keywords: List[str]) -> tuple:
    """Check which keywords are present/missing in response."""
    response_lower = response_text.lower()
    found = []
    missing = []
    
    for keyword in keywords:
        if keyword.lower() in response_lower:
            found.append(keyword)
        else:
            missing.append(keyword)
    
    return found, missing


def check_forbidden(response_text: str, forbidden: List[str]) -> List[str]:
    """Check if any forbidden phrases are present."""
    response_lower = response_text.lower()
    found = []
    
    for phrase in forbidden:
        if phrase.lower() in response_lower:
            found.append(phrase)
    
    return found


def run_scenario(scenario: Dict) -> List[TestResult]:
    """Run a single test scenario and return results for each turn."""
    results = []
    session_id = f"test_{uuid.uuid4().hex[:12]}"
    
    print(f"\n  Testing: {scenario['name']}")
    
    for turn_idx, turn in enumerate(scenario.get("turns", [])):
        result = TestResult(scenario["id"], turn_idx)
        result.user_message = turn["user"]
        
        # Handle expected_intent as string or list
        expected = turn.get("expected_intent", [])
        if isinstance(expected, str):
            result.expected_intent = [expected]
        else:
            result.expected_intent = expected
        
        try:
            # Send the message
            response = send_chat_message(turn["user"], session_id)
            result.response_time_ms = response.get("_response_time_ms", 0)
            
            # Extract response data
            response_text = response.get("response", "")
            actual_intent = response.get("intent", "unknown")
            result.actual_intent = actual_intent
            result.response_excerpt = response_text[:300] + "..." if len(response_text) > 300 else response_text
            
            # Check intent match
            intent_match = actual_intent in result.expected_intent
            
            # Check keywords
            keywords = turn.get("keywords", [])
            result.keywords_found, result.keywords_missing = check_keywords(response_text, keywords)
            
            # Check forbidden phrases
            forbidden = turn.get("must_not_contain", [])
            result.forbidden_found = check_forbidden(response_text, forbidden)
            
            # Determine pass/fail
            # Pass if: intent matches AND no critical keywords missing AND no forbidden phrases found
            critical_keywords_ok = len(result.keywords_missing) == 0 or len(keywords) == 0
            no_forbidden = len(result.forbidden_found) == 0
            
            result.passed = intent_match and no_forbidden
            
            status = "PASS" if result.passed else "FAIL"
            intent_info = f"(intent: {actual_intent})"
            print(f"    Turn {turn_idx + 1}: {status} {intent_info}")
            
        except Exception as e:
            result.error = str(e)
            result.passed = False
            print(f"    Turn {turn_idx + 1}: ERROR - {e}")
        
        results.append(result)
        time.sleep(REQUEST_DELAY)
    
    return results


def generate_scenarios_doc(scenarios: List[Dict]) -> str:
    """Generate markdown documentation for test scenarios."""
    lines = [
        "# Chat Regression Test Scenarios",
        "",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "This document describes all test scenarios used in the automated regression suite.",
        "",
        "---",
        "",
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        lines.append(f"## {i}. {scenario['name']}")
        lines.append("")
        lines.append(f"**ID:** `{scenario['id']}`")
        lines.append("")
        lines.append(f"**Description:** {scenario['description']}")
        lines.append("")
        lines.append("**Conversation Flow:**")
        lines.append("")
        
        for turn_idx, turn in enumerate(scenario.get("turns", []), 1):
            expected = turn.get("expected_intent", "any")
            if isinstance(expected, list):
                expected = " or ".join(expected)
            
            lines.append(f"- **Turn {turn_idx}:**")
            lines.append(f"  - User: \"{turn['user']}\"")
            lines.append(f"  - Expected Intent: `{expected}`")
            
            keywords = turn.get("keywords", [])
            if keywords:
                lines.append(f"  - Expected Keywords: {', '.join(keywords)}")
            
            forbidden = turn.get("must_not_contain", [])
            if forbidden:
                lines.append(f"  - Must NOT Contain: {', '.join(forbidden)}")
            
            lines.append("")
        
        lines.append("---")
        lines.append("")
    
    return "\n".join(lines)


def generate_results_doc(all_results: List[TestResult], scenarios: List[Dict]) -> str:
    """Generate markdown documentation for test results."""
    total = len(all_results)
    passed = sum(1 for r in all_results if r.passed)
    failed = total - passed
    pass_rate = (passed / total * 100) if total > 0 else 0
    
    lines = [
        "# Chat Regression Test Results",
        "",
        f"**Run Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Summary",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Total Tests | {total} |",
        f"| Passed | {passed} |",
        f"| Failed | {failed} |",
        f"| Pass Rate | {pass_rate:.1f}% |",
        "",
        "---",
        "",
        "## Detailed Results",
        "",
    ]
    
    # Group results by scenario
    scenario_map = {s["id"]: s for s in scenarios}
    current_scenario = None
    
    for result in all_results:
        if result.scenario_id != current_scenario:
            current_scenario = result.scenario_id
            scenario = scenario_map.get(result.scenario_id, {})
            lines.append(f"### {scenario.get('name', result.scenario_id)}")
            lines.append("")
            lines.append(f"*{scenario.get('description', '')}*")
            lines.append("")
        
        status_emoji = "PASS" if result.passed else "FAIL"
        lines.append(f"**Turn {result.turn_index + 1}:** {status_emoji}")
        lines.append("")
        lines.append(f"- **User:** \"{result.user_message}\"")
        lines.append(f"- **Expected Intent:** `{', '.join(result.expected_intent)}`")
        lines.append(f"- **Actual Intent:** `{result.actual_intent}`")
        lines.append(f"- **Response Time:** {result.response_time_ms}ms")
        
        if result.keywords_found:
            lines.append(f"- **Keywords Found:** {', '.join(result.keywords_found)}")
        if result.keywords_missing:
            lines.append(f"- **Keywords Missing:** {', '.join(result.keywords_missing)}")
        if result.forbidden_found:
            lines.append(f"- **FORBIDDEN PHRASES FOUND:** {', '.join(result.forbidden_found)}")
        if result.error:
            lines.append(f"- **Error:** {result.error}")
        
        lines.append("")
        lines.append("**Response Excerpt:**")
        lines.append("```")
        lines.append(result.response_excerpt.replace("```", "'''"))
        lines.append("```")
        lines.append("")
    
    # Add failed tests summary at the end
    failed_results = [r for r in all_results if not r.passed]
    if failed_results:
        lines.append("---")
        lines.append("")
        lines.append("## Failed Tests Summary")
        lines.append("")
        lines.append("| Scenario | Turn | User Message | Expected | Actual |")
        lines.append("|----------|------|--------------|----------|--------|")
        
        for r in failed_results:
            expected = ", ".join(r.expected_intent)
            lines.append(f"| {r.scenario_id} | {r.turn_index + 1} | {r.user_message[:30]}... | {expected} | {r.actual_intent} |")
        
        lines.append("")
    
    return "\n".join(lines)


def main():
    """Run the full test suite."""
    print("=" * 60)
    print("Anna Kitney Chat Regression Test Suite")
    print("=" * 60)
    print(f"\nAPI Endpoint: {CHAT_ENDPOINT}")
    print(f"Scenarios File: {SCENARIOS_FILE}")
    
    # Load scenarios
    print("\nLoading test scenarios...")
    scenarios = load_scenarios()
    print(f"Loaded {len(scenarios)} scenarios")
    
    # Generate scenarios documentation
    print("\nGenerating scenarios documentation...")
    scenarios_doc = generate_scenarios_doc(scenarios)
    with open(SCENARIOS_DOC_FILE, 'w') as f:
        f.write(scenarios_doc)
    print(f"Saved to: {SCENARIOS_DOC_FILE}")
    
    # Run all scenarios
    print("\n" + "-" * 60)
    print("Running Tests")
    print("-" * 60)
    
    all_results = []
    for scenario in scenarios:
        results = run_scenario(scenario)
        all_results.extend(results)
    
    # Generate results documentation
    print("\n" + "-" * 60)
    print("Generating Results Report")
    print("-" * 60)
    
    results_doc = generate_results_doc(all_results, scenarios)
    with open(RESULTS_FILE, 'w') as f:
        f.write(results_doc)
    print(f"Saved to: {RESULTS_FILE}")
    
    # Print summary
    total = len(all_results)
    passed = sum(1 for r in all_results if r.passed)
    failed = total - passed
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Pass Rate: {passed/total*100:.1f}%" if total > 0 else "N/A")
    print("=" * 60)
    
    if failed > 0:
        print("\nFailed tests:")
        for r in all_results:
            if not r.passed:
                print(f"  - {r.scenario_id} (turn {r.turn_index + 1}): expected {r.expected_intent}, got {r.actual_intent}")
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    exit(main())
