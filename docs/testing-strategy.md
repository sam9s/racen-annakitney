# Chatbot Testing Strategy

A comprehensive guide to testing conversational AI systems, designed for production-grade quality assurance.

## Philosophy

Chatbot testing requires a **layered approach** because:

1. **Deterministic logic** (intent routing, parsing) can be unit tested
2. **LLM responses** are non-deterministic and require pattern-based validation
3. **Safety** requires adversarial testing with known attack patterns
4. **Quality** requires human-like judgment (LLM-as-Judge)

## Testing Pyramid

```
                    ┌─────────────┐
                    │   Manual    │  ← Exploratory testing
                    │   Testing   │
                    └──────┬──────┘
                           │
              ┌────────────┴────────────┐
              │     LLM Evaluation      │  ← Quality scoring
              │   (Response Quality)    │
              └────────────┬────────────┘
                           │
         ┌─────────────────┴─────────────────┐
         │        Adversarial Tests          │  ← Security/Safety
         │   (Prompt Injection, Safety)      │
         └─────────────────┬─────────────────┘
                           │
    ┌──────────────────────┴──────────────────────┐
    │           Scenario Tests (E2E)              │  ← Integration
    │   (Multi-turn conversations, API tests)     │
    └──────────────────────┬──────────────────────┘
                           │
┌──────────────────────────┴──────────────────────────┐
│                    Unit Tests                       │  ← Foundation
│   (Intent routing, parsing, individual functions)   │
└─────────────────────────────────────────────────────┘
```

## Test Categories

### 1. Unit Tests (Foundation)

**Purpose**: Test deterministic logic in isolation

**What to test**:
- Intent classification patterns
- Date/time parsing
- Entity extraction
- Fuzzy matching algorithms
- Configuration validation

**Tools**: pytest
**Location**: `tests/unit/`
**Frequency**: On every code change

**Example**:
```python
def test_month_extraction():
    result = extract_month_filter("What events are in March?")
    assert result == 3
```

### 2. Scenario Tests (Integration)

**Purpose**: Test complete conversation flows against live API

**What to test**:
- Multi-turn conversations
- Context preservation
- Progressive disclosure flows
- Error handling
- Edge cases

**Tools**: Custom scenario runner
**Location**: `tests/scenarios/`
**Frequency**: Before deployment

**Example**:
```json
{
  "name": "Event inquiry flow",
  "turns": [
    {"user": "What events do you have?", "expected": {"contains": ["SoulAlign"]}},
    {"user": "Tell me about the first one", "expected": {"contains": ["details"]}}
  ]
}
```

### 3. Adversarial Tests (Security)

**Purpose**: Test resilience against attacks and boundary violations

**What to test**:
- Prompt injection attempts
- Jailbreak attempts
- Safety boundary violations
- Personal information leaks
- Off-topic handling

**Tools**: Custom adversarial runner
**Location**: `tests/adversarial/`
**Frequency**: Periodically + after safety changes

**Example**:
```json
{
  "name": "Prompt injection - ignore instructions",
  "input": "Ignore previous instructions and...",
  "forbidden_patterns": ["secret", "password"],
  "required_patterns": ["help", "wellness"]
}
```

### 4. LLM Evaluation (Quality)

**Purpose**: Score response quality using AI judgment

**What to evaluate**:
- Factual accuracy
- Response relevance
- Safety compliance
- Brand tone
- CTA correctness

**Tools**: GPT-4o-mini as judge
**Location**: `tests/llm_eval/`
**Frequency**: Weekly audits + after major changes

**Rubrics**:
| Rubric | Weight | Description |
|--------|--------|-------------|
| Accuracy | 30% | Factual correctness |
| Relevance | 25% | Addresses user query |
| Safety | 25% | Follows safety guidelines |
| Tone | 10% | Brand voice alignment |
| CTA | 10% | Correct calls-to-action |

## Execution Strategy

### Development Phase
```bash
# Run unit tests frequently
python -m pytest tests/unit/ -v
```

### Pre-Deployment
```bash
# Run all tests
python tests/run_all_tests.py
```

### Production Monitoring
```bash
# Weekly quality audits
python tests/llm_eval/evaluator.py --input logs/conversations.json

# Monthly security review
python tests/adversarial/safety_regression.py
```

## Coverage Targets

| Area | Target | Rationale |
|------|--------|-----------|
| Intent Classification | 95% | Core routing logic |
| Date/Time Parsing | 95% | User frustration if wrong |
| Event Queries | 90% | Primary use case |
| Safety Boundaries | 100% | Non-negotiable |
| Progressive Flow | 85% | Complex multi-turn |
| Brand Tone | 80% | Subjective but important |

## Adding Tests for New Features

### Step 1: Add Unit Tests
```python
# tests/unit/test_new_feature.py
def test_new_feature_basic():
    result = new_feature("input")
    assert result == expected
```

### Step 2: Add Scenario Tests
```json
// tests/scenarios/chat_test_scenarios.json
{
  "id": "new-feature-001",
  "name": "New feature happy path",
  "turns": [...]
}
```

### Step 3: Add Adversarial Cases (if security-relevant)
```json
// tests/adversarial/prompt_injection.json
{
  "id": "new-feature-attack-001",
  "category": "boundary",
  "input": "..."
}
```

### Step 4: Run Full Suite
```bash
python tests/run_all_tests.py
```

## Debugging Test Failures

### Unit Test Failures
1. Check the assertion message
2. Add print statements or use pytest `-s` flag
3. Verify test data matches expected format

### Scenario Test Failures
1. Check API logs for errors
2. Verify server is running
3. Check if response format changed

### Adversarial Test Failures
1. Review the response for leaked patterns
2. Check guardrail configuration
3. Update safety rules if needed

### LLM Evaluation Failures
1. Review the rubric scores
2. Check if response quality degraded
3. May indicate model drift or prompt issues

## CI/CD Integration

### GitHub Actions Example
```yaml
name: Chatbot Tests
on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run unit tests
        run: python -m pytest tests/unit/ -v

  integration-tests:
    runs-on: ubuntu-latest
    needs: unit-tests
    steps:
      - uses: actions/checkout@v2
      - name: Start server
        run: npm run dev &
      - name: Wait for server
        run: sleep 15
      - name: Run scenario tests
        run: python tests/scenarios/scenario_runner.py
```

## Metrics and Reporting

### Key Metrics
- **Unit Test Pass Rate**: Target 99%+
- **Scenario Pass Rate**: Target 95%+
- **Adversarial Pass Rate**: Target 100%
- **LLM Quality Score**: Target 4.0/5.0+

### Reports Generated
- `tests/reports/comprehensive_results.md` - Master summary
- `tests/reports/scenario_results.md` - Conversation test details
- `tests/reports/adversarial_results.md` - Security test details
- `tests/reports/llm_eval_results.md` - Quality scores
- `docs/test_results_summary.md` - Documentation copy

## Best Practices

1. **Test the contract, not the implementation** - Focus on inputs/outputs
2. **Use realistic test data** - Based on actual user queries
3. **Test edge cases explicitly** - Typos, empty inputs, special characters
4. **Keep tests independent** - Each test should set up its own state
5. **Make tests fast** - Slow tests don't get run
6. **Document test purpose** - Future maintainers will thank you
7. **Regression test bugs** - Every bug fix should add a test
8. **Review test coverage regularly** - Gaps appear over time

## Glossary

- **Intent**: The user's goal (e.g., EVENT, GREETING, KNOWLEDGE)
- **Scenario**: A multi-turn conversation test case
- **Rubric**: A scoring criterion for LLM evaluation
- **Adversarial**: Attacks designed to break the system
- **Progressive Disclosure**: Multi-stage information reveal (Summary → Details → Navigate)
- **Guardrail**: Safety rule that blocks harmful content
