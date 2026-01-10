# Comprehensive Test Results

Generated: 2026-01-10 00:45:46

## Executive Summary

| Suite | Status | Passed | Failed | Total |
|-------|--------|--------|--------|-------|
| Unit Tests | ❌ | 112 | 1 | 113 |

## Overall Statistics

- **Total Tests:** 113
- **Passed:** 112
- **Failed:** 1
- **Pass Rate:** 99.1%

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
