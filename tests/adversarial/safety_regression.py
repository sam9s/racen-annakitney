#!/usr/bin/env python3
"""
Adversarial and Safety Regression Tests

Tests the chatbot's resilience against prompt injection, jailbreaks,
and safety boundary violations.

Usage:
    python tests/adversarial/safety_regression.py [--base-url URL]
"""

import json
import os
import re
import sys
import requests
from typing import Dict, List, Tuple
from dataclasses import dataclass
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

@dataclass
class AdversarialResult:
    """Result of a single adversarial test."""
    test_id: str
    name: str
    category: str
    input_message: str
    response: str
    passed: bool
    failures: List[str]

@dataclass
class AdversarialSummary:
    """Summary of adversarial test results."""
    total_tests: int
    passed: int
    failed: int
    by_category: Dict[str, Dict[str, int]]
    results: List[AdversarialResult]


class AdversarialTester:
    """Runs adversarial tests against the chatbot."""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url.rstrip("/")
        self.chat_endpoint = f"{self.base_url}/api/chat"
    
    def _send_message(self, message: str) -> Tuple[bool, str]:
        """Send a message to the chatbot."""
        try:
            import uuid
            response = requests.post(
                self.chat_endpoint,
                json={"message": message, "session_id": str(uuid.uuid4())},
                timeout=30
            )
            if response.status_code == 200:
                return True, response.json().get("response", "")
            return False, f"HTTP {response.status_code}"
        except requests.exceptions.ConnectionError:
            return False, "Connection refused"
        except Exception as e:
            return False, str(e)
    
    def run_test(self, test_case: Dict) -> AdversarialResult:
        """Run a single adversarial test case."""
        test_id = test_case["id"]
        name = test_case["name"]
        category = test_case["category"]
        input_message = test_case["input"]
        
        success, response = self._send_message(input_message)
        
        if not success:
            return AdversarialResult(
                test_id=test_id,
                name=name,
                category=category,
                input_message=input_message,
                response=response,
                passed=False,
                failures=[f"API error: {response}"]
            )
        
        failures = []
        response_lower = response.lower()
        
        # Check forbidden patterns
        for pattern in test_case.get("forbidden_patterns", []):
            if pattern.lower() in response_lower:
                failures.append(f"Contains forbidden pattern: '{pattern}'")
        
        # Check required patterns
        for pattern in test_case.get("required_patterns", []):
            if pattern.lower() not in response_lower:
                failures.append(f"Missing required pattern: '{pattern}'")
        
        return AdversarialResult(
            test_id=test_id,
            name=name,
            category=category,
            input_message=input_message,
            response=response,
            passed=len(failures) == 0,
            failures=failures
        )
    
    def run_suite(self, test_cases: List[Dict]) -> AdversarialSummary:
        """Run all adversarial test cases."""
        results = []
        by_category = {}
        
        for test_case in test_cases:
            result = self.run_test(test_case)
            results.append(result)
            
            # Track by category
            cat = result.category
            if cat not in by_category:
                by_category[cat] = {"passed": 0, "failed": 0}
            if result.passed:
                by_category[cat]["passed"] += 1
            else:
                by_category[cat]["failed"] += 1
            
            # Print progress
            status = "✅" if result.passed else "❌"
            print(f"{status} [{result.category}] {result.name}")
            if result.failures:
                for f in result.failures:
                    print(f"   └─ {f}")
        
        passed = sum(1 for r in results if r.passed)
        
        return AdversarialSummary(
            total_tests=len(results),
            passed=passed,
            failed=len(results) - passed,
            by_category=by_category,
            results=results
        )
    
    def generate_report(self, summary: AdversarialSummary) -> str:
        """Generate markdown report."""
        report = f"""# Adversarial Test Results

Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Summary

| Metric | Value |
|--------|-------|
| Total Tests | {summary.total_tests} |
| Passed | {summary.passed} |
| Failed | {summary.failed} |
| Pass Rate | {summary.passed/summary.total_tests*100:.1f}% |

## Results by Category

| Category | Passed | Failed | Rate |
|----------|--------|--------|------|
"""
        for cat, stats in summary.by_category.items():
            total = stats["passed"] + stats["failed"]
            rate = stats["passed"] / total * 100 if total > 0 else 0
            report += f"| {cat} | {stats['passed']} | {stats['failed']} | {rate:.0f}% |\n"
        
        report += "\n## Detailed Results\n\n"
        
        for r in summary.results:
            status = "✅ PASS" if r.passed else "❌ FAIL"
            report += f"### {r.test_id}: {r.name}\n"
            report += f"- **Category:** {r.category}\n"
            report += f"- **Status:** {status}\n"
            report += f"- **Input:** `{r.input_message[:80]}...`\n"
            
            if r.failures:
                report += "- **Failures:**\n"
                for f in r.failures:
                    report += f"  - {f}\n"
            
            report += f"- **Response:** {r.response[:200]}...\n\n"
        
        return report


def load_test_cases(file_path: str) -> List[Dict]:
    """Load test cases from JSON file."""
    with open(file_path, "r") as f:
        data = json.load(f)
    return data.get("test_cases", [])


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Run adversarial tests")
    parser.add_argument("--test-file", default="tests/adversarial/prompt_injection.json",
                        help="Path to test cases JSON")
    parser.add_argument("--base-url", default="http://localhost:5000",
                        help="Base URL for chatbot API")
    parser.add_argument("--output", default="tests/reports/adversarial_results.md",
                        help="Output file for report")
    args = parser.parse_args()
    
    print("=" * 60)
    print("ADVERSARIAL TEST RUNNER")
    print("=" * 60)
    print(f"Test file: {args.test_file}")
    print(f"Base URL: {args.base_url}")
    print()
    
    # Load test cases
    try:
        test_cases = load_test_cases(args.test_file)
        print(f"Loaded {len(test_cases)} test cases\n")
    except FileNotFoundError:
        print(f"Error: Test file not found: {args.test_file}")
        return 1
    
    # Run tests
    tester = AdversarialTester(args.base_url)
    summary = tester.run_suite(test_cases)
    
    # Generate report
    report = tester.generate_report(summary)
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w") as f:
        f.write(report)
    
    # Print summary
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Tests: {summary.passed}/{summary.total_tests} passed")
    print(f"Report saved to: {args.output}")
    
    return 0 if summary.failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
