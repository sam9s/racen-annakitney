# Chat Regression Test Scenarios

Generated: 2026-01-07 07:36:15

This document describes all test scenarios used in the automated regression suite.

---

## 1. Basic Greeting

**ID:** `greeting_basic`

**Description:** Test that greetings are handled correctly

**Conversation Flow:**

- **Turn 1:**
  - User: "Hello!"
  - Expected Intent: `greeting`
  - Expected Keywords: hello, wellness, programs, events

---

## 2. Hi Greeting

**ID:** `greeting_hi`

**Description:** Test 'hi' as greeting

**Conversation Flow:**

- **Turn 1:**
  - User: "Hi there"
  - Expected Intent: `greeting`
  - Expected Keywords: hello, wellness

---

## 3. Specific Date Query - June 1st

**ID:** `date_specific_june1`

**Description:** CRITICAL: 'June 1st' should be a DATE query, NOT ordinal selection

**Conversation Flow:**

- **Turn 1:**
  - User: "Are there any events on June 1st?"
  - Expected Intent: `event`
  - Expected Keywords: event, June
  - Must NOT Contain: option, which one

---

## 4. Specific Date Query - June 26

**ID:** `date_specific_june26`

**Description:** Test specific date within multi-day event range

**Conversation Flow:**

- **Turn 1:**
  - User: "Is there anything happening on June 26?"
  - Expected Intent: `event`
  - Expected Keywords: SoulAlign, Heal

---

## 5. Month Query - March

**ID:** `date_month_query_march`

**Description:** Test month-based event filtering

**Conversation Flow:**

- **Turn 1:**
  - User: "What events are happening in March?"
  - Expected Intent: `event`
  - Expected Keywords: March, SoulAlign, Coach

---

## 6. Month Query - January

**ID:** `date_month_query_january`

**Description:** Test January events

**Conversation Flow:**

- **Turn 1:**
  - User: "Show me events in January"
  - Expected Intent: `event`
  - Expected Keywords: January, Identity Switch, Success Redefined

---

## 7. Ordinal Selection from List

**ID:** `ordinal_selection_after_list`

**Description:** User selects '1' after seeing a numbered list

**Conversation Flow:**

- **Turn 1:**
  - User: "What events do you have?"
  - Expected Intent: `event`
  - Expected Keywords: 1., 2.

- **Turn 2:**
  - User: "1"
  - Expected Intent: `followup_select`

---

## 8. Ordinal 'the first one'

**ID:** `ordinal_first_one`

**Description:** User says 'the first one' to select

**Conversation Flow:**

- **Turn 1:**
  - User: "Tell me about upcoming events"
  - Expected Intent: `event`
  - Expected Keywords: 1., 2.

- **Turn 2:**
  - User: "the first one"
  - Expected Intent: `followup_select`

---

## 9. Ordinal 'option 2'

**ID:** `ordinal_option_2`

**Description:** User says 'option 2' to select second item

**Conversation Flow:**

- **Turn 1:**
  - User: "What events are coming up?"
  - Expected Intent: `event`
  - Expected Keywords: 1., 2.

- **Turn 2:**
  - User: "option 2"
  - Expected Intent: `followup_select`

---

## 10. Follow-up 'yes' After Event

**ID:** `followup_yes_after_event`

**Description:** User confirms interest with 'yes'

**Conversation Flow:**

- **Turn 1:**
  - User: "Tell me about The Identity Switch"
  - Expected Intent: `event`
  - Expected Keywords: Identity Switch, January

- **Turn 2:**
  - User: "yes"
  - Expected Intent: `followup_confirm`

---

## 11. Follow-up 'tell me more'

**ID:** `followup_tell_me_more`

**Description:** User asks for more info

**Conversation Flow:**

- **Turn 1:**
  - User: "What's the Success Redefined meditation?"
  - Expected Intent: `event`
  - Expected Keywords: Success Redefined, Dubai

- **Turn 2:**
  - User: "tell me more"
  - Expected Intent: `followup_confirm`

---

## 12. Multi-day Event Query

**ID:** `multiday_event_range`

**Description:** Query about date within a multi-day event range

**Conversation Flow:**

- **Turn 1:**
  - User: "Is there an event on July 15th?"
  - Expected Intent: `event`
  - Expected Keywords: SoulAlign, Heal

---

## 13. Program Pricing Query

**ID:** `program_pricing`

**Description:** Test knowledge intent for pricing questions

**Conversation Flow:**

- **Turn 1:**
  - User: "How much does SoulAlign Coach cost?"
  - Expected Intent: `knowledge`
  - Expected Keywords: investment, price, $

---

## 14. Program Features Query

**ID:** `program_features`

**Description:** Test knowledge intent for program details

**Conversation Flow:**

- **Turn 1:**
  - User: "What's included in the SoulAlign Business program?"
  - Expected Intent: `knowledge`
  - Expected Keywords: business, coaching, program

---

## 15. Event Registration Intent

**ID:** `event_register`

**Description:** Test event action word 'register'

**Conversation Flow:**

- **Turn 1:**
  - User: "How do I register for The Identity Switch?"
  - Expected Intent: `event`
  - Expected Keywords: Identity Switch, register, ticket

---

## 16. Event Booking Intent

**ID:** `event_book`

**Description:** Test event action word 'book'

**Conversation Flow:**

- **Turn 1:**
  - User: "I want to book a spot at the Dubai meditation event"
  - Expected Intent: `event`
  - Expected Keywords: Dubai, meditation, Success Redefined

---

## 17. Program vs Event Disambiguation

**ID:** `disambiguation_soualign_heal`

**Description:** Test when name exists as both program and event

**Conversation Flow:**

- **Turn 1:**
  - User: "Tell me about SoulAlign Heal"
  - Expected Intent: `clarification or event or knowledge`
  - Expected Keywords: SoulAlign, Heal

---

## 18. Date '1st of June' Not Ordinal

**ID:** `date_1st_not_ordinal`

**Description:** CRITICAL: '1st of June' should be date, not ordinal

**Conversation Flow:**

- **Turn 1:**
  - User: "Any events on the 1st of June?"
  - Expected Intent: `event`
  - Expected Keywords: June
  - Must NOT Contain: option, which

---

## 19. Date '3rd July' Not Ordinal

**ID:** `date_3rd_july`

**Description:** CRITICAL: '3rd July' should be date, not ordinal selection

**Conversation Flow:**

- **Turn 1:**
  - User: "What's happening on 3rd July?"
  - Expected Intent: `event`
  - Expected Keywords: July, event
  - Must NOT Contain: third option

---

## 20. General Upcoming Events

**ID:** `upcoming_events_general`

**Description:** Test general event listing

**Conversation Flow:**

- **Turn 1:**
  - User: "What events are coming up?"
  - Expected Intent: `event`
  - Expected Keywords: event, 1., 2.

---

## 21. Event Location Query

**ID:** `event_location`

**Description:** Test event with location focus

**Conversation Flow:**

- **Turn 1:**
  - User: "Are there any events in Dubai?"
  - Expected Intent: `event`
  - Expected Keywords: Dubai, Success Redefined, meditation

---

## 22. Enrollment Intent

**ID:** `enrollment_query`

**Description:** Test enrollment question for programs

**Conversation Flow:**

- **Turn 1:**
  - User: "How do I enroll in SoulAlign Coach?"
  - Expected Intent: `knowledge or event`
  - Expected Keywords: enroll, SoulAlign Coach

---

## 23. Bare 'yes' Without Context

**ID:** `bare_yes_no_context`

**Description:** Test that bare 'yes' without event context doesn't misfire

**Conversation Flow:**

- **Turn 1:**
  - User: "Hello"
  - Expected Intent: `greeting`

- **Turn 2:**
  - User: "yes"
  - Expected Intent: `other or greeting or followup_confirm`

---

## 24. Add to Calendar Request

**ID:** `calendar_add`

**Description:** Test calendar add functionality

**Conversation Flow:**

- **Turn 1:**
  - User: "Can I add The Identity Switch to my calendar?"
  - Expected Intent: `event`
  - Expected Keywords: calendar, Identity Switch

---

## 25. September Events Query

**ID:** `september_events`

**Description:** Test month with multi-day events overlapping

**Conversation Flow:**

- **Turn 1:**
  - User: "What's happening in September 2026?"
  - Expected Intent: `event`
  - Expected Keywords: September, SoulAlign

---
