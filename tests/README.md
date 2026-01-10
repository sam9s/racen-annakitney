# Chatbot Testing Framework

A comprehensive, production-grade testing framework for conversational AI chatbots.

## Overview

This framework provides multiple layers of testing to ensure chatbot quality:

| Layer | Purpose | Location |
|-------|---------|----------|
| **Unit Tests** | Deterministic component testing | `tests/unit/` |
| **Scenario Tests** | End-to-end conversation flows | `tests/scenarios/` |
| **LLM Evaluation** | Response quality scoring | `tests/llm_eval/` |
| **Adversarial Tests** | Security and safety testing | `tests/adversarial/` |

## Directory Structure

```
tests/
├── unit/                    # Pytest unit tests
│   ├── test_intent_router.py
│   ├── test_events_service.py
│   └── test_safety_guardrails.py (future)
├── scenarios/               # E2E conversation tests
│   ├── chat_test_scenarios.json
│   ├── comprehensive_test_scenarios.json
│   └── scenario_runner.py
├── llm_eval/                # LLM-as-Judge evaluation
│   ├── rubrics.json
│   ├── evaluator.py
│   └── gold_transcripts.json (future)
├── adversarial/             # Red-team/security tests
│   ├── prompt_injection.json
│   └── safety_regression.py
├── lib/                     # Shared utilities
│   └── chat_regression_suite.py
├── reports/                 # Generated test reports
│   └── (auto-generated)
├── run_all_tests.py         # Master test orchestrator
└── README.md                # This file
```

## Quick Start

### Run All Tests
```bash
python tests/run_all_tests.py
```

### Run Specific Suite
```bash
# Unit tests only (no server needed)
python tests/run_all_tests.py --suite unit

# Scenario tests (requires server running)
python tests/run_all_tests.py --suite scenarios

# LLM evaluation
python tests/run_all_tests.py --suite llm_eval

# Adversarial tests (requires server running)
python tests/run_all_tests.py --suite adversarial
```

### Run Individual Test Files
```bash
# Pytest unit tests
python -m pytest tests/unit/ -v

# Scenario runner
python tests/scenarios/scenario_runner.py

# Adversarial tests
python tests/adversarial/safety_regression.py

# LLM evaluator (demo mode)
python tests/llm_eval/evaluator.py --demo
```

## Test Categories

### 1. Unit Tests (`tests/unit/`)

Deterministic pytest tests for individual components:

- **Intent Router**: Classification accuracy, pattern matching
- **Events Service**: Date parsing, month filtering, fuzzy matching
- **Safety Guardrails**: Crisis detection, medical advice filtering

**When to use**: After any code changes to test logic remains correct.

### 2. Scenario Tests (`tests/scenarios/`)

Multi-turn conversation tests against the live API:

- Tests complete conversation flows
- Validates progressive disclosure (3-stage flow)
- Checks response content and patterns

**When to use**: Before deployment to validate end-to-end behavior.

### 3. LLM Evaluation (`tests/llm_eval/`)

Response quality scoring using GPT-4o-mini:

**Rubrics:**
- **Accuracy** (30%): Factual correctness
- **Relevance** (25%): How well response addresses query
- **Safety** (25%): Safety guideline compliance
- **Tone** (10%): Brand voice alignment
- **CTA Accuracy** (10%): Correct calls-to-action

**When to use**: For quality audits and regression detection.

### 4. Adversarial Tests (`tests/adversarial/`)

Security and safety regression testing:

- **Prompt Injection**: Tests for instruction bypass attempts
- **Jailbreaks**: Role-play and restriction removal attacks
- **Safety Boundaries**: Crisis content, medical advice
- **Off-Topic**: Political, unrelated questions

**When to use**: After safety-related changes or periodically.

## Writing New Tests

### Adding Unit Tests

```python
# tests/unit/test_my_component.py
import pytest
from my_component import MyFunction

class TestMyFunction:
    def test_basic_case(self):
        result = MyFunction("input")
        assert result == "expected"
    
    @pytest.mark.parametrize("input,expected", [
        ("a", "b"),
        ("c", "d"),
    ])
    def test_multiple_cases(self, input, expected):
        assert MyFunction(input) == expected
```

### Adding Scenario Tests

```json
// tests/scenarios/chat_test_scenarios.json
{
  "scenarios": [
    {
      "id": "my-test-001",
      "name": "Test greeting flow",
      "turns": [
        {
          "user": "Hello",
          "expected": {
            "contains": ["welcome", "help"],
            "not_contains": ["error"]
          }
        }
      ]
    }
  ]
}
```

### Adding Adversarial Tests

```json
// tests/adversarial/prompt_injection.json
{
  "test_cases": [
    {
      "id": "my-test-001",
      "category": "prompt_injection",
      "name": "Test case name",
      "input": "Malicious input here",
      "expected_behavior": "refuse_and_redirect",
      "forbidden_patterns": ["secret", "password"],
      "required_patterns": ["help", "wellness"]
    }
  ]
}
```

## Reports

Test reports are automatically generated in:
- `tests/reports/comprehensive_results.md` - Master report
- `tests/reports/scenario_results.md` - Scenario test details
- `tests/reports/adversarial_results.md` - Security test details
- `tests/reports/llm_eval_results.md` - Quality scores
- `docs/test_results_summary.md` - Copy for documentation

## Best Practices

1. **Run unit tests frequently** - They're fast and catch regressions
2. **Run scenario tests before deployment** - Catches integration issues
3. **Run adversarial tests periodically** - Security should be ongoing
4. **Use LLM eval for audits** - Catches quality drift over time
5. **Add tests for every bug fix** - Prevent regressions
6. **Keep scenarios realistic** - Based on actual user queries

## CI/CD Integration

Add to your deployment pipeline:

```yaml
# Example GitHub Actions
test:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v2
    - name: Run unit tests
      run: python -m pytest tests/unit/ -v
    - name: Start server
      run: npm run dev &
    - name: Wait for server
      run: sleep 10
    - name: Run scenario tests
      run: python tests/run_all_tests.py --suite scenarios
```

## Coverage Goals

| Category | Target | Current |
|----------|--------|---------|
| Intent Classification | 95% | 99% |
| Date/Month Parsing | 95% | 95% |
| Event Queries | 90% | 90% |
| Safety Boundaries | 100% | 90% |
| Progressive Flow | 85% | 85% |

## Contributing

1. Add tests for new features
2. Update scenarios for new conversation flows
3. Add adversarial cases for new attack vectors
4. Run full suite before submitting changes
