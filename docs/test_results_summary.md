# Chatbot Test Results Summary

Generated: 2026-01-10 00:16:31

## Overview

| Test Suite | Status | Details |
|------------|--------|---------|
| Pytest Unit Tests | ⚠️ PARTIAL | 105/113 passed |
| API Regression Tests | ⏸️ SKIPPED | Requires running server |

## Test Categories

### Unit Tests (pytest)
- **Intent Router Tests**: Classification, follow-up detection, stage handling
- **Events Service Tests**: Date parsing, month filtering, fuzzy matching
- **Coverage**: Greetings, events, programs, ordinals, dates, safety

### API Regression Tests
- **End-to-end chat scenarios**: Multi-turn conversations
- **Progressive disclosure**: 3-stage event/program flow
- **Edge cases**: Date parsing, follow-ups, context preservation

## Critical Test Cases

| Test Case | Status | Description |
|-----------|--------|-------------|
| Month Follow-up Queries | ✅ | "What about in May?" correctly returns May events |
| Date Parsing | ✅ | "April 2026" not parsed as "April 20" |
| Event vs Program Context | ✅ | Follow-ups stay in correct domain |
| Ordinal Selection | ✅ | "1", "the first one" work after lists |

## Running Tests

```bash
# Unit tests only
python -m pytest tests/test_intent_router.py tests/test_events_service.py -v

# Full regression suite (requires server)
python tests/chat_regression_suite.py

# All tests
python tests/run_all_tests.py
```

## Adding New Tests

1. **Unit tests**: Add to `tests/test_intent_router.py` or `tests/test_events_service.py`
2. **API tests**: Add scenarios to `tests/chat_test_scenarios.json`
3. **Run**: `python tests/run_all_tests.py`
