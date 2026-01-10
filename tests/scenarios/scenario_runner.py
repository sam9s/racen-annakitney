#!/usr/bin/env python3
"""
End-to-End Scenario Runner

Executes multi-turn conversation scenarios against the live chatbot API.
Validates responses match expected patterns and behaviors.

Usage:
    python tests/scenarios/scenario_runner.py [--scenario-file FILE] [--base-url URL]
"""

import json
import re
import sys
import os
import requests
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

@dataclass
class ScenarioResult:
    """Result of running a single scenario."""
    scenario_id: str
    scenario_name: str
    passed: bool
    turns_passed: int
    turns_total: int
    failures: List[str]
    duration_ms: float

@dataclass
class TestSuiteResult:
    """Result of running the full test suite."""
    total_scenarios: int
    passed_scenarios: int
    failed_scenarios: int
    total_turns: int
    passed_turns: int
    results: List[ScenarioResult]
    duration_seconds: float


class ScenarioRunner:
    """Runs multi-turn conversation scenarios against the chatbot API."""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url.rstrip("/")
        self.chat_endpoint = f"{self.base_url}/api/chat"
        self.session_id = None
    
    def _new_session(self) -> str:
        """Generate a new session ID."""
        import uuid
        return str(uuid.uuid4())
    
    def _send_message(self, message: str, session_id: str) -> Tuple[bool, str]:
        """Send a message to the chatbot and return the response."""
        try:
            response = requests.post(
                self.chat_endpoint,
                json={"message": message, "session_id": session_id},
                timeout=30
            )
            if response.status_code == 200:
                data = response.json()
                return True, data.get("response", "")
            else:
                return False, f"HTTP {response.status_code}: {response.text}"
        except requests.exceptions.ConnectionError:
            return False, "Connection refused - is the server running?"
        except Exception as e:
            return False, str(e)
    
    def _check_response(self, response: str, expected: Dict) -> Tuple[bool, str]:
        """Check if response matches expected criteria."""
        failures = []
        
        # Check required patterns (must contain)
        if "contains" in expected:
            for pattern in expected["contains"]:
                if pattern.lower() not in response.lower():
                    failures.append(f"Missing expected text: '{pattern}'")
        
        # Check regex patterns
        if "matches" in expected:
            for pattern in expected["matches"]:
                if not re.search(pattern, response, re.IGNORECASE):
                    failures.append(f"Missing expected pattern: '{pattern}'")
        
        # Check forbidden patterns (must NOT contain)
        if "not_contains" in expected:
            for pattern in expected["not_contains"]:
                if pattern.lower() in response.lower():
                    failures.append(f"Contains forbidden text: '{pattern}'")
        
        # Check response is non-empty
        if not response.strip():
            failures.append("Empty response")
        
        if failures:
            return False, "; ".join(failures)
        return True, ""
    
    def run_scenario(self, scenario: Dict) -> ScenarioResult:
        """Run a single multi-turn scenario."""
        start_time = datetime.now()
        
        scenario_id = scenario.get("id", "unknown")
        scenario_name = scenario.get("name", scenario_id)
        turns = scenario.get("turns", [])
        
        session_id = self._new_session()
        failures = []
        turns_passed = 0
        
        for i, turn in enumerate(turns):
            user_message = turn.get("user", "")
            expected = turn.get("expected", {})
            
            # Send message
            success, response = self._send_message(user_message, session_id)
            
            if not success:
                failures.append(f"Turn {i+1}: API error - {response}")
                continue
            
            # Check response
            passed, failure_msg = self._check_response(response, expected)
            if passed:
                turns_passed += 1
            else:
                failures.append(f"Turn {i+1} ('{user_message[:30]}...'): {failure_msg}")
        
        duration_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        return ScenarioResult(
            scenario_id=scenario_id,
            scenario_name=scenario_name,
            passed=len(failures) == 0,
            turns_passed=turns_passed,
            turns_total=len(turns),
            failures=failures,
            duration_ms=duration_ms
        )
    
    def run_suite(self, scenarios: List[Dict]) -> TestSuiteResult:
        """Run all scenarios in the test suite."""
        start_time = datetime.now()
        results = []
        
        for scenario in scenarios:
            result = self.run_scenario(scenario)
            results.append(result)
            
            # Print progress
            status = "✅" if result.passed else "❌"
            print(f"{status} {result.scenario_name}: {result.turns_passed}/{result.turns_total} turns")
        
        duration_seconds = (datetime.now() - start_time).total_seconds()
        
        passed = sum(1 for r in results if r.passed)
        total_turns = sum(r.turns_total for r in results)
        passed_turns = sum(r.turns_passed for r in results)
        
        return TestSuiteResult(
            total_scenarios=len(results),
            passed_scenarios=passed,
            failed_scenarios=len(results) - passed,
            total_turns=total_turns,
            passed_turns=passed_turns,
            results=results,
            duration_seconds=duration_seconds
        )
    
    def generate_report(self, result: TestSuiteResult) -> str:
        """Generate a markdown report from test results."""
        report = f"""# Scenario Test Results

Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Summary

| Metric | Value |
|--------|-------|
| Total Scenarios | {result.total_scenarios} |
| Passed | {result.passed_scenarios} |
| Failed | {result.failed_scenarios} |
| Pass Rate | {result.passed_scenarios/result.total_scenarios*100:.1f}% |
| Total Turns | {result.total_turns} |
| Passed Turns | {result.passed_turns} |
| Duration | {result.duration_seconds:.2f}s |

## Results

"""
        for r in result.results:
            status = "✅ PASS" if r.passed else "❌ FAIL"
            report += f"### {r.scenario_name}\n"
            report += f"- Status: {status}\n"
            report += f"- Turns: {r.turns_passed}/{r.turns_total}\n"
            report += f"- Duration: {r.duration_ms:.0f}ms\n"
            
            if r.failures:
                report += "- Failures:\n"
                for f in r.failures:
                    report += f"  - {f}\n"
            report += "\n"
        
        return report


def load_scenarios(file_path: str) -> List[Dict]:
    """Load scenarios from a JSON file."""
    with open(file_path, "r") as f:
        data = json.load(f)
    return data.get("scenarios", data) if isinstance(data, dict) else data


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Run chatbot scenario tests")
    parser.add_argument("--scenario-file", default="tests/scenarios/chat_test_scenarios.json",
                        help="Path to scenario JSON file")
    parser.add_argument("--base-url", default="http://localhost:5000",
                        help="Base URL for the chatbot API")
    parser.add_argument("--output", default="tests/reports/scenario_results.md",
                        help="Output file for the report")
    args = parser.parse_args()
    
    print("=" * 60)
    print("SCENARIO TEST RUNNER")
    print("=" * 60)
    print(f"Scenario file: {args.scenario_file}")
    print(f"Base URL: {args.base_url}")
    print()
    
    # Load scenarios
    try:
        scenarios = load_scenarios(args.scenario_file)
        print(f"Loaded {len(scenarios)} scenarios")
    except FileNotFoundError:
        print(f"Error: Scenario file not found: {args.scenario_file}")
        return 1
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in scenario file: {e}")
        return 1
    
    # Run tests
    runner = ScenarioRunner(args.base_url)
    result = runner.run_suite(scenarios)
    
    # Generate and save report
    report = runner.generate_report(result)
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w") as f:
        f.write(report)
    print(f"\nReport saved to: {args.output}")
    
    # Print summary
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Scenarios: {result.passed_scenarios}/{result.total_scenarios} passed")
    print(f"Turns: {result.passed_turns}/{result.total_turns} passed")
    print(f"Duration: {result.duration_seconds:.2f}s")
    
    return 0 if result.failed_scenarios == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
