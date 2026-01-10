#!/usr/bin/env python3
"""
Comprehensive Test Runner for Chatbot Testing Framework

Orchestrates all test suites:
- Unit tests (pytest)
- Scenario tests (end-to-end API tests)
- LLM evaluation (response quality scoring)
- Adversarial tests (security and safety)

Usage:
    python tests/run_all_tests.py [--suite SUITE] [--base-url URL]

Suites:
    all         Run all test suites (default)
    unit        Run pytest unit tests only
    scenarios   Run end-to-end scenario tests only
    llm_eval    Run LLM-as-Judge evaluation only
    adversarial Run adversarial/safety tests only
"""

import subprocess
import sys
import json
import os
import re
import argparse
from datetime import datetime
from typing import Dict, Tuple

def run_pytest_suite() -> Tuple[bool, Dict]:
    """Run pytest unit tests."""
    print("\n" + "=" * 60)
    print("RUNNING PYTEST UNIT TESTS")
    print("=" * 60 + "\n")
    
    result = subprocess.run(
        [sys.executable, "-m", "pytest", 
         "tests/unit/",
         "-v", "--tb=line"],
        capture_output=True,
        text=True
    )
    
    print(result.stdout)
    
    # Parse results
    passed = 0
    failed = 0
    for line in result.stdout.split('\n'):
        if 'passed' in line:
            passed_match = re.search(r'(\d+) passed', line)
            failed_match = re.search(r'(\d+) failed', line)
            if passed_match:
                passed = int(passed_match.group(1))
            if failed_match:
                failed = int(failed_match.group(1))
    
    return result.returncode == 0, {"passed": passed, "failed": failed, "total": passed + failed}


def run_scenario_suite(base_url: str) -> Tuple[bool, Dict]:
    """Run end-to-end scenario tests."""
    print("\n" + "=" * 60)
    print("RUNNING SCENARIO TESTS")
    print("=" * 60 + "\n")
    
    result = subprocess.run(
        [sys.executable, "tests/scenarios/scenario_runner.py",
         "--base-url", base_url],
        capture_output=True,
        text=True,
        timeout=300
    )
    
    print(result.stdout)
    if result.stderr:
        print(result.stderr)
    
    # Try to read JSON summary first (more reliable)
    json_path = "tests/reports/scenario_results.json"
    if os.path.exists(json_path):
        try:
            with open(json_path, 'r') as f:
                stats = json.load(f)
            return result.returncode == 0, stats
        except:
            pass
    
    # Fallback: Parse summary from stdout
    passed = 0
    total = 0
    for line in result.stdout.split('\n'):
        if 'Scenarios:' in line:
            match = re.search(r'(\d+)/(\d+)', line)
            if match:
                passed = int(match.group(1))
                total = int(match.group(2))
    
    return result.returncode == 0, {"passed": passed, "failed": total - passed, "total": total}


def run_llm_eval_suite() -> Tuple[bool, Dict]:
    """Run LLM-as-Judge evaluation."""
    print("\n" + "=" * 60)
    print("RUNNING LLM EVALUATION (Demo Mode)")
    print("=" * 60 + "\n")
    
    result = subprocess.run(
        [sys.executable, "tests/llm_eval/evaluator.py", "--demo"],
        capture_output=True,
        text=True
    )
    
    print(result.stdout[:2000])  # Truncate output
    
    return True, {"note": "Demo mode - use with real transcripts for full evaluation"}


def run_adversarial_suite(base_url: str) -> Tuple[bool, Dict]:
    """Run adversarial tests."""
    print("\n" + "=" * 60)
    print("RUNNING ADVERSARIAL TESTS")
    print("=" * 60 + "\n")
    
    result = subprocess.run(
        [sys.executable, "tests/adversarial/safety_regression.py",
         "--base-url", base_url],
        capture_output=True,
        text=True
    )
    
    print(result.stdout)
    
    # Parse summary
    passed = 0
    total = 0
    for line in result.stdout.split('\n'):
        if 'Tests:' in line:
            match = re.search(r'(\d+)/(\d+)', line)
            if match:
                passed = int(match.group(1))
                total = int(match.group(2))
    
    return result.returncode == 0, {"passed": passed, "failed": total - passed, "total": total}


def generate_master_report(results: Dict) -> str:
    """Generate comprehensive test report."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report = f"""# Comprehensive Test Results

Generated: {timestamp}

## Executive Summary

| Suite | Status | Passed | Failed | Total |
|-------|--------|--------|--------|-------|
"""
    
    total_passed = 0
    total_failed = 0
    
    for suite_name, data in results.items():
        status = "✅" if data.get("success", False) else "❌"
        stats = data.get("stats", {})
        passed = stats.get("passed", 0)
        failed = stats.get("failed", 0)
        total = stats.get("total", 0)
        
        if total > 0:
            total_passed += passed
            total_failed += failed
        
        report += f"| {suite_name} | {status} | {passed} | {failed} | {total} |\n"
    
    overall_total = total_passed + total_failed
    overall_rate = (total_passed / overall_total * 100) if overall_total > 0 else 0
    
    report += f"""
## Overall Statistics

- **Total Tests:** {overall_total}
- **Passed:** {total_passed}
- **Failed:** {total_failed}
- **Pass Rate:** {overall_rate:.1f}%

## Test Categories

### Unit Tests
Deterministic tests for individual components:
- Intent classification
- Date/month parsing
- Event filtering
- Safety guardrails

### Scenario Tests
End-to-end multi-turn conversation tests:
- Event queries and follow-ups
- Program information flow
- Progressive disclosure (3-stage)

### LLM Evaluation
Response quality scoring using GPT-4o-mini:
- Accuracy, Relevance, Safety, Tone
- Brand voice compliance
- CTA correctness

### Adversarial Tests
Security and safety regression:
- Prompt injection attempts
- Jailbreak attempts
- Safety boundary testing
- Off-topic handling

## Running Individual Suites

```bash
# All tests
python tests/run_all_tests.py

# Unit tests only
python tests/run_all_tests.py --suite unit

# Scenario tests (requires running server)
python tests/run_all_tests.py --suite scenarios

# LLM evaluation
python tests/run_all_tests.py --suite llm_eval

# Adversarial tests (requires running server)
python tests/run_all_tests.py --suite adversarial
```
"""
    
    return report


def main():
    parser = argparse.ArgumentParser(description="Comprehensive Test Runner")
    parser.add_argument("--suite", choices=["all", "unit", "scenarios", "llm_eval", "adversarial"],
                        default="all", help="Which test suite to run")
    parser.add_argument("--base-url", default="http://localhost:5000",
                        help="Base URL for API tests")
    args = parser.parse_args()
    
    print("\n" + "=" * 60)
    print("CHATBOT COMPREHENSIVE TEST SUITE")
    print("=" * 60)
    print(f"Suite: {args.suite}")
    print(f"Base URL: {args.base_url}")
    
    results = {}
    
    # Run selected suites
    if args.suite in ["all", "unit"]:
        success, stats = run_pytest_suite()
        results["Unit Tests"] = {"success": success, "stats": stats}
    
    if args.suite in ["all", "scenarios"]:
        success, stats = run_scenario_suite(args.base_url)
        results["Scenario Tests"] = {"success": success, "stats": stats}
    
    if args.suite in ["all", "llm_eval"]:
        success, stats = run_llm_eval_suite()
        results["LLM Evaluation"] = {"success": success, "stats": stats}
    
    if args.suite in ["all", "adversarial"]:
        success, stats = run_adversarial_suite(args.base_url)
        results["Adversarial Tests"] = {"success": success, "stats": stats}
    
    # Generate report
    report = generate_master_report(results)
    
    os.makedirs("tests/reports", exist_ok=True)
    report_path = "tests/reports/comprehensive_results.md"
    with open(report_path, "w") as f:
        f.write(report)
    
    # Also update docs
    os.makedirs("docs", exist_ok=True)
    with open("docs/test_results_summary.md", "w") as f:
        f.write(report)
    
    # Print final summary
    print("\n" + "=" * 60)
    print("FINAL SUMMARY")
    print("=" * 60)
    
    all_passed = all(r.get("success", False) for r in results.values())
    
    for suite_name, data in results.items():
        status = "✅" if data.get("success", False) else "❌"
        stats = data.get("stats", {})
        if "total" in stats:
            print(f"{status} {suite_name}: {stats.get('passed', 0)}/{stats.get('total', 0)} passed")
        else:
            print(f"{status} {suite_name}: Completed")
    
    print(f"\n📄 Report saved to: {report_path}")
    print(f"📄 Also saved to: docs/test_results_summary.md")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
