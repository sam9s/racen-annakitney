# Anna Kitney Chatbot Architecture Decisions

## Overview

This document explains the architectural design of the Anna Kitney wellness chatbot, specifically addressing **why certain logic is handled by Python code vs LLM prompting**.

## Design Philosophy

The chatbot uses a **hybrid approach**:
- **Deterministic logic** (Python code) → For accuracy-critical operations
- **LLM prompting** → For conversational tone, explanations, and natural language

## What is Handled by Code (Deterministic)

These operations require 100% accuracy and cannot be left to LLM interpretation:

| Component | File | Why Code is Required |
|-----------|------|---------------------|
| **Intent Classification** | `intent_router.py` | Must classify EVENT vs KNOWLEDGE queries BEFORE database access to prevent RAG pollution |
| **Event Date Filtering** | `events_service.py` | Date math (e.g., "events in January", "June 26 falls within June 3-Sept 30") |
| **Enrollment URL Selection** | `safety_guardrails.py` | Different programs have different checkout pages with payment plan variants |
| **Payment Gating** | `safety_guardrails.py` | Checkout links must ONLY appear after explicit enrollment intent |
| **Crisis Detection** | `safety_guardrails.py` | Safety-critical: must never miss crisis keywords |
| **Follow-up Detection** | `intent_router.py` | "Yes" after event list must reference the correct event from history |
| **URL Injection** | `safety_guardrails.py` | Correct URLs must be inserted (LLM often hallucinates URLs) |

### Why Not LLM Prompting?

1. **Enrollment URLs** - There are 15+ checkout URLs with payment variants. LLM cannot reliably pick the right one.
2. **Date Queries** - "Any events on June 26?" requires checking if June 26 falls within a date RANGE. This is pure math.
3. **Safety Guardrails** - Crisis detection is too important to leave to LLM interpretation. False negatives are dangerous.
4. **Payment Gating** - Business rule: checkout links should ONLY appear after explicit intent. This must be enforced.

## What is Handled by LLM (Conversational)

These are appropriate for LLM because they benefit from natural language generation:

| Element | Approach |
|---------|----------|
| **Program descriptions** | LLM synthesizes from RAG context |
| **Conversational tone** | LLM adapts to user's language style |
| **Follow-up questions** | LLM chooses contextually appropriate questions |
| **Explanations** | LLM explains concepts naturally |
| **Empathy/warmth** | LLM provides supportive responses |

## Data Flow Architecture

```
User Query
    │
    ▼
┌─────────────────┐
│  IntentRouter   │ ← Python: Classifies query type
│  (intent_router)│
└────────┬────────┘
         │
         ├──► EVENT: SQL query only (no RAG)
         ├──► KNOWLEDGE: RAG query only (no SQL)
         ├──► HYBRID: Both with priority rules
         ├──► FOLLOWUP_SELECT: Parse from history
         └──► FOLLOWUP_CONFIRM: Use previous context
         │
         ▼
┌─────────────────┐
│  Data Fetch     │ ← Python: Deterministic data retrieval
│  (events_service│
│   knowledge_base)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  LLM Generation │ ← LLM: Natural language response
│  (OpenAI API)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Post-Processing│ ← Python: Safety filters, URL injection
│  (safety_guard) │
└────────┬────────┘
         │
         ▼
    Final Response
```

## Key Data Structures

### PROGRAM_ENROLLMENT_DATA (safety_guardrails.py)

Single source of truth for enrollment flows:

```python
{
    "SoulAlign Heal": {
        "enrollment_mode": "direct_checkout",  # vs "clarity_call_only"
        "clarity_call_required": False,
        "payment_options": [
            {"label": "Pay in Full", "price": "$5,555", "checkout_url": "..."},
            {"label": "12 Monthly Payments", "price": "$553/month", "checkout_url": "..."}
        ],
        "info_page": "https://www.annakitney.com/soulalign-heal/"
    },
    "Elite Private Advisory": {
        "enrollment_mode": "clarity_call_only",
        "clarity_call_required": True,
        "payment_options": [],  # No direct checkout
        "clarity_call_url": "https://www.annakitney.com/clarity-call/"
    }
}
```

### IntentType (intent_router.py)

Classification categories for query routing:

| Intent | Description | Data Sources |
|--------|-------------|--------------|
| EVENT | Date queries, event registration | SQL only |
| KNOWLEDGE | Program info, pricing, philosophy | RAG only |
| HYBRID | General questions needing both | SQL + RAG |
| CLARIFICATION | Ambiguous (same name for program and event) | Asks user |
| FOLLOWUP_SELECT | User selecting from numbered list | History |
| FOLLOWUP_CONFIRM | User confirming interest | Context |

## Post-Processing Pipeline

After LLM generates response, Python applies these transformations IN ORDER:

1. `format_numbered_lists()` - Consistent list formatting
2. `fix_compound_trailing_questions()` - Simplify "X or Y?" to single question
3. `filter_response_for_safety()` - Remove medical/psychiatric advice
4. `inject_dynamic_enrollment()` - Add checkout options after enrollment intent
5. `inject_checkout_urls()` - Replace placeholders with actual URLs
6. `inject_program_links()` - Add program page links
7. `append_contextual_links()` - Add relevant footer links

## Comparison with JoveHeal

| Aspect | JoveHeal | Anna Kitney |
|--------|----------|-------------|
| Programs | ~3-4 | 8+ with variants |
| Enrollment flows | Uniform | Mixed (direct checkout, clarity call, hybrid) |
| Events | Static/none | Live Google Calendar sync |
| Content size | Small | Large (many pages) |
| Payment options | Simple | Multiple variants per program |
| Date queries | None | Complex (multi-day events, ranges) |

**Conclusion**: JoveHeal's simpler scope allows more LLM-driven logic. Anna Kitney's complexity requires deterministic code for accuracy-critical paths.

## When to Add New Code vs Prompt Logic

**Add Code When:**
- Operation requires 100% accuracy (URLs, dates, safety)
- Business rules must be enforced (payment gating)
- Data comes from external sources (calendar, database)
- Errors have financial or safety implications

**Use Prompting When:**
- Response needs natural language variation
- Tone/empathy is important
- Information synthesis from context
- Creative explanations or analogies

## File Responsibilities

| File | Primary Responsibility |
|------|----------------------|
| `intent_router.py` | Query classification BEFORE data access |
| `events_service.py` | PostgreSQL event queries, date filtering |
| `knowledge_base.py` | ChromaDB RAG queries |
| `safety_guardrails.py` | Safety filters, URL/enrollment data, post-processing |
| `chatbot_engine.py` | Orchestration, LLM calls, response pipeline |
| `webhook_server.py` | Flask API endpoints |
