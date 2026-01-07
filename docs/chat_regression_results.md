# Chat Regression Test Results

**Run Date:** 2026-01-07 07:25:20

## Summary

| Metric | Value |
|--------|-------|
| Total Tests | 31 |
| Passed | 18 |
| Failed | 13 |
| Pass Rate | 58.1% |

---

## Detailed Results

### Basic Greeting

*Test that greetings are handled correctly*

**Turn 1:** PASS

- **User:** "Hello!"
- **Expected Intent:** `greeting`
- **Actual Intent:** `greeting`
- **Response Time:** 530ms
- **Keywords Found:** hello, wellness, programs, events

**Response Excerpt:**
```
Hello! I'm Anna's wellness assistant. I'm here to help you learn about our transformational programs and upcoming events. What would you like to explore today?
```

### Hi Greeting

*Test 'hi' as greeting*

**Turn 1:** PASS

- **User:** "Hi there"
- **Expected Intent:** `greeting`
- **Actual Intent:** `greeting`
- **Response Time:** 409ms
- **Keywords Found:** hello, wellness

**Response Excerpt:**
```
Hello! I'm Anna's wellness assistant. I'm here to help you learn about our transformational programs and upcoming events. What would you like to explore today?
```

### Specific Date Query - June 1st

*CRITICAL: 'June 1st' should be a DATE query, NOT ordinal selection*

**Turn 1:** PASS

- **User:** "Are there any events on June 1st?"
- **Expected Intent:** `event`
- **Actual Intent:** `event`
- **Response Time:** 682ms
- **Keywords Found:** event, June

**Response Excerpt:**
```
I don't have any events scheduled for June 1, 2026.

Here are all upcoming events you might be interested in:

Here are the upcoming events:

1. [**The Identity Overflow**](https://www.annakitney.com/event/the-identity-overflow/) - Jan 09 - Jan 11, 2026 (Zoom)
2. [**SoulAlign® Manifestation Mastery*...
```

### Specific Date Query - June 26

*Test specific date within multi-day event range*

**Turn 1:** PASS

- **User:** "Is there anything happening on June 26?"
- **Expected Intent:** `event`
- **Actual Intent:** `event`
- **Response Time:** 3065ms
- **Keywords Found:** SoulAlign, Heal

**Response Excerpt:**
```
Yes! On June 26, 2026, we have the **SoulAlign® Heal** event. Here are the details:

**When:** June 03 - September 30, 2026 | Sessions at 4:00 PM (London time)

**Where:** Zoom

---

**About this event:**

*SOULALIGN® QUANTUM HEALING THROUGH GOD CONSCIOUSNESS TO HAVE IT ALL!*

SoulAlign® Heal is des...
```

### Month Query - March

*Test month-based event filtering*

**Turn 1:** FAIL

- **User:** "What events are happening in March?"
- **Expected Intent:** `event`
- **Actual Intent:** `knowledge`
- **Response Time:** 2318ms
- **Keywords Found:** March
- **Keywords Missing:** SoulAlign, Coach

**Response Excerpt:**
```
I don’t have any specific events listed for March at the moment, but if you're interested in future events or workshops, feel free to reach out to us or check our events page for updates! Would you like to know more about any specific topics or areas of interest?

---

*Feel free to explore more whe...
```

### Month Query - January

*Test January events*

**Turn 1:** FAIL

- **User:** "Show me events in January"
- **Expected Intent:** `event`
- **Actual Intent:** `knowledge`
- **Response Time:** 1649ms
- **Keywords Found:** January
- **Keywords Missing:** Identity Switch, Success Redefined

**Response Excerpt:**
```
Here are our upcoming events in January:

1. **The Identity Overflow**  
   Date: January 9-11, 2026  
   Time: 5 PM GMT  

Would you like more details about this event or anything else?
```

### Ordinal Selection from List

*User selects '1' after seeing a numbered list*

**Turn 1:** FAIL

- **User:** "What events do you have?"
- **Expected Intent:** `event`
- **Actual Intent:** `knowledge`
- **Response Time:** 1918ms
- **Keywords Found:** 1.
- **Keywords Missing:** 2.

**Response Excerpt:**
```
Here are our upcoming events:

1. **The Identity Overflow**  
   **Dates:** January 9-11, 2026  
   **Location:** Zoom  
   **Description:** A 3-Part Challenge to elevate your manifesting abilities and align with your true desires.

Would you like more details about any of these?
```

**Turn 2:** FAIL

- **User:** "1"
- **Expected Intent:** `followup_select`
- **Actual Intent:** ``
- **Response Time:** 0ms
- **Error:** API error: 500 - {"error":"Chat API error"}

**Response Excerpt:**
```

```

### Ordinal 'the first one'

*User says 'the first one' to select*

**Turn 1:** PASS

- **User:** "Tell me about upcoming events"
- **Expected Intent:** `event`
- **Actual Intent:** `event`
- **Response Time:** 3912ms
- **Keywords Found:** 1., 2.

**Response Excerpt:**
```
Here are our upcoming events:

1. [**The Identity Overflow**](https://www.annakitney.com/event/the-identity-overflow/) - Jan 09 - Jan 11, 2026 (Zoom)

2. [**SoulAlign® Manifestation Mastery**](https://www.annakitney.com/event/soulalign-manifestation-mastery/) - Jan 20 - Apr 07, 2026 (Zoom)

3. [**Th...
```

**Turn 2:** FAIL

- **User:** "the first one"
- **Expected Intent:** `followup_select`
- **Actual Intent:** ``
- **Response Time:** 0ms
- **Error:** API error: 500 - {"error":"Chat API error"}

**Response Excerpt:**
```

```

### Ordinal 'option 2'

*User says 'option 2' to select second item*

**Turn 1:** FAIL

- **User:** "What events are coming up?"
- **Expected Intent:** `event`
- **Actual Intent:** `knowledge`
- **Response Time:** 1538ms
- **Keywords Missing:** 1., 2.

**Response Excerpt:**
```
Here are our upcoming events:

- **The Identity Overflow**: A 3-Part Challenge happening January 9-11, 2026 on Zoom.

Would you like more details about any of these?
```

**Turn 2:** FAIL

- **User:** "option 2"
- **Expected Intent:** `followup_select`
- **Actual Intent:** ``
- **Response Time:** 0ms
- **Error:** API error: 500 - {"error":"Chat API error"}

**Response Excerpt:**
```

```

### Follow-up 'yes' After Event

*User confirms interest with 'yes'*

**Turn 1:** PASS

- **User:** "Tell me about The Identity Switch"
- **Expected Intent:** `event`
- **Actual Intent:** `event`
- **Response Time:** 401ms
- **Keywords Found:** Identity Switch, January

**Response Excerpt:**
```
Here are the details for this event:

**The Identity Switch**

**When:** Saturday, January 24, 2026 from 12:00 PM - 7:00 PM (Dubai time)

**Where:** Zoom

---

**About this event:**

*WITH SELF-MADE 7-FIGURE SPIRITUAL BUSINESS COACH, ANNA KITNEY*

Manifestation Isn’t Magic — It’s Identity.
And You’r...
```

**Turn 2:** FAIL

- **User:** "yes"
- **Expected Intent:** `followup_confirm`
- **Actual Intent:** ``
- **Response Time:** 0ms
- **Error:** API error: 500 - {"error":"Chat API error"}

**Response Excerpt:**
```

```

### Follow-up 'tell me more'

*User asks for more info*

**Turn 1:** FAIL

- **User:** "What's the Success Redefined meditation?"
- **Expected Intent:** `event`
- **Actual Intent:** `hybrid`
- **Response Time:** 2041ms
- **Keywords Found:** Success Redefined, Dubai

**Response Excerpt:**
```
**Success Redefined - The Meditation: LIVE IN DUBAI** is an event designed to elevate your understanding of what success truly means through guided meditation. It focuses on harnessing your inner power and reshaping your beliefs around achievement and fulfillment. 

If you'd like to learn more about...
```

**Turn 2:** FAIL

- **User:** "tell me more"
- **Expected Intent:** `followup_confirm`
- **Actual Intent:** ``
- **Response Time:** 0ms
- **Error:** API error: 500 - {"error":"Chat API error"}

**Response Excerpt:**
```

```

### Multi-day Event Query

*Query about date within a multi-day event range*

**Turn 1:** PASS

- **User:** "Is there an event on July 15th?"
- **Expected Intent:** `event`
- **Actual Intent:** `event`
- **Response Time:** 5918ms
- **Keywords Found:** SoulAlign, Heal

**Response Excerpt:**
```
Yes, there is an event on July 15,

2026. **SoulAlign® Heal**

**When:** June 03 - September 30, 2026 | Sessions at 4:00 PM (London time)

**Where:** Zoom

---

**About this event:**

*SOULALIGN® QUANTUM HEALING THROUGH GOD CONSCIOUSNESS TO HAVE IT ALL!*

SoulAlign® Heal

*WITH ANNA KITNEY*

**$150M...
```

### Program Pricing Query

*Test knowledge intent for pricing questions*

**Turn 1:** PASS

- **User:** "How much does SoulAlign Coach cost?"
- **Expected Intent:** `knowledge`
- **Actual Intent:** `knowledge`
- **Response Time:** 1787ms
- **Keywords Missing:** investment, price, $

**Response Excerpt:**
```
I'm sorry, but I don't have specific information about the SoulAlign Coach program. For details about pricing and enrollment, I'd recommend contacting us directly at https://www.annakitney.com/contact. We’re here to help!
```

### Program Features Query

*Test knowledge intent for program details*

**Turn 1:** PASS

- **User:** "What's included in the SoulAlign Business program?"
- **Expected Intent:** `knowledge`
- **Actual Intent:** `knowledge`
- **Response Time:** 3692ms
- **Keywords Found:** business, coaching, program

**Response Excerpt:**
```
The SoulAlign® Business program is designed to help start-ups and established coaches, healers, therapists, and spiritual teachers serve their soul-aligned clients. Here’s what’s included:

1. **Lifetime access** to the SoulAlign® Business online course.

2. **8 Weeks of Live Group Coaching Calls** ...
```

### Event Registration Intent

*Test event action word 'register'*

**Turn 1:** PASS

- **User:** "How do I register for The Identity Switch?"
- **Expected Intent:** `event`
- **Actual Intent:** `event`
- **Response Time:** 412ms
- **Keywords Found:** Identity Switch
- **Keywords Missing:** register, ticket

**Response Excerpt:**
```
Here are the details for this event:

**The Identity Switch**

**When:** Saturday, January 24, 2026 from 12:00 PM - 7:00 PM (Dubai time)

**Where:** Zoom

---

**About this event:**

*WITH SELF-MADE 7-FIGURE SPIRITUAL BUSINESS COACH, ANNA KITNEY*

Manifestation Isn’t Magic — It’s Identity.
And You’r...
```

### Event Booking Intent

*Test event action word 'book'*

**Turn 1:** PASS

- **User:** "I want to book a spot at the Dubai meditation event"
- **Expected Intent:** `event`
- **Actual Intent:** `event`
- **Response Time:** 514ms
- **Keywords Found:** Dubai, meditation, Success Redefined

**Response Excerpt:**
```
Here are the details for this event:

**Success Redefined - The Meditation: LIVE IN DUBAI**

**When:** Sunday, January 25, 2026 from 9:30 AM - 12:00 PM (Dubai time)

**Where:** Trove Best Shisha Lounge In Dubai Ground floor,Fashion avenue, The Dubai Mall – Burj Khalifa – Downtown Dubai – Dubai – Uni...
```

### Program vs Event Disambiguation

*Test when name exists as both program and event*

**Turn 1:** FAIL

- **User:** "Tell me about SoulAlign Heal"
- **Expected Intent:** `clarification, event, knowledge`
- **Actual Intent:** `hybrid`
- **Response Time:** 3063ms
- **Keywords Found:** SoulAlign, Heal

**Response Excerpt:**
```
SoulAlign® Heal is a multidimensional recalibration experience designed for those who are ready to exit the healing loop and step into their divine consciousness. It's not about fixing what was never broken; instead, it focuses on remembering that you are not just the body — you are the frequency th...
```

### Date '1st of June' Not Ordinal

*CRITICAL: '1st of June' should be date, not ordinal*

**Turn 1:** PASS

- **User:** "Any events on the 1st of June?"
- **Expected Intent:** `event`
- **Actual Intent:** `event`
- **Response Time:** 582ms
- **Keywords Found:** June

**Response Excerpt:**
```
I don't have any events scheduled for June 1, 2026.

Here are all upcoming events you might be interested in:

Here are the upcoming events:

1. [**The Identity Overflow**](https://www.annakitney.com/event/the-identity-overflow/) - Jan 09 - Jan 11, 2026 (Zoom)
2. [**SoulAlign® Manifestation Mastery*...
```

### Date '3rd July' Not Ordinal

*CRITICAL: '3rd July' should be date, not ordinal selection*

**Turn 1:** PASS

- **User:** "What's happening on 3rd July?"
- **Expected Intent:** `event`
- **Actual Intent:** `event`
- **Response Time:** 5605ms
- **Keywords Found:** July, event

**Response Excerpt:**
```
Here are our upcoming events on July 3, 2026:

**SoulAlign® Heal**

**When:** June 03 - September 30, 2026 | Sessions at 4:00 PM (London time)

**Where:** Zoom

---

**About this event:**

*SOULALIGN® QUANTUM HEALING THROUGH GOD CONSCIOUSNESS TO HAVE IT ALL!*

SoulAlign® Heal

*WITH ANNA KITNEY*

**...
```

### General Upcoming Events

*Test general event listing*

**Turn 1:** FAIL

- **User:** "What events are coming up?"
- **Expected Intent:** `event`
- **Actual Intent:** `knowledge`
- **Response Time:** 1667ms
- **Keywords Found:** event
- **Keywords Missing:** 1., 2.

**Response Excerpt:**
```
Here are our upcoming events:

- **The Identity Overflow**: A 3-Part Challenge happening January 9-11, 2026 on Zoom!

Would you like more details about any of these events?
```

### Event Location Query

*Test event with location focus*

**Turn 1:** FAIL

- **User:** "Are there any events in Dubai?"
- **Expected Intent:** `event`
- **Actual Intent:** `knowledge`
- **Response Time:** 1943ms
- **Keywords Found:** Dubai
- **Keywords Missing:** Success Redefined, meditation

**Response Excerpt:**
```
Here are our upcoming events in Dubai:

1. **[SoulAlign Manifestation Mastery](https://www.annakitney.com/soulalign-manifestation-mastery/)** 
   - Date: June 18, 2025 – September 3, 2025
   - Time: 6:30 PM – 8 PM (GMT)

Would you like more details about any of these events?
```

### Enrollment Intent

*Test enrollment question for programs*

**Turn 1:** PASS

- **User:** "How do I enroll in SoulAlign Coach?"
- **Expected Intent:** `knowledge, event`
- **Actual Intent:** `knowledge`
- **Response Time:** 1805ms
- **Keywords Found:** enroll, SoulAlign Coach

**Response Excerpt:**
```
Thank you for your interest in our SoulAlign Coach program! To enroll, the first step is to book a complimentary [Clarity Call](https://www.annakitney.com/clarity-call/). During this call, we can discuss how the program can support your goals. Would you like me to take you to the Clarity Call bookin...
```

### Bare 'yes' Without Context

*Test that bare 'yes' without event context doesn't misfire*

**Turn 1:** PASS

- **User:** "Hello"
- **Expected Intent:** `greeting`
- **Actual Intent:** `greeting`
- **Response Time:** 317ms

**Response Excerpt:**
```
Hello! I'm Anna's wellness assistant. I'm here to help you learn about our transformational programs and upcoming events. What would you like to explore today?
```

**Turn 2:** PASS

- **User:** "yes"
- **Expected Intent:** `other, greeting, followup_confirm`
- **Actual Intent:** `followup_confirm`
- **Response Time:** 971ms

**Response Excerpt:**
```
Great! What specifically would you like to know? Are you interested in our programs, upcoming events, or something else? I'm here to help!
```

### Add to Calendar Request

*Test calendar add functionality*

**Turn 1:** PASS

- **User:** "Can I add The Identity Switch to my calendar?"
- **Expected Intent:** `event`
- **Actual Intent:** `event`
- **Response Time:** 1937ms
- **Keywords Found:** calendar, Identity Switch

**Response Excerpt:**
```
I've added The Identity Switch to your calendar! If you need anything else or have questions about the event, feel free to ask!
```

### September Events Query

*Test month with multi-day events overlapping*

**Turn 1:** PASS

- **User:** "What's happening in September 2026?"
- **Expected Intent:** `event`
- **Actual Intent:** `event`
- **Response Time:** 1736ms
- **Keywords Found:** SoulAlign
- **Keywords Missing:** September

**Response Excerpt:**
```
Here are the upcoming events:

1. [**SoulAlign® Heal**](https://www.annakitney.com/event/soulalign-heal/) - Jun 03 - Sep 30, 2026 (Zoom)

2. [**SoulAlign® Business 2026**](https://www.annakitney.com/event/soulalign-business/) - Sep 08 - Oct 27, 2026 (Zoom)

Would you like more details about any of t...
```

---

## Failed Tests Summary

| Scenario | Turn | User Message | Expected | Actual |
|----------|------|--------------|----------|--------|
| date_month_query_march | 1 | What events are happening in M... | event | knowledge |
| date_month_query_january | 1 | Show me events in January... | event | knowledge |
| ordinal_selection_after_list | 1 | What events do you have?... | event | knowledge |
| ordinal_selection_after_list | 2 | 1... | followup_select |  |
| ordinal_first_one | 2 | the first one... | followup_select |  |
| ordinal_option_2 | 1 | What events are coming up?... | event | knowledge |
| ordinal_option_2 | 2 | option 2... | followup_select |  |
| followup_yes_after_event | 2 | yes... | followup_confirm |  |
| followup_tell_me_more | 1 | What's the Success Redefined m... | event | hybrid |
| followup_tell_me_more | 2 | tell me more... | followup_confirm |  |
| disambiguation_soualign_heal | 1 | Tell me about SoulAlign Heal... | clarification, event, knowledge | hybrid |
| upcoming_events_general | 1 | What events are coming up?... | event | knowledge |
| event_location | 1 | Are there any events in Dubai?... | event | knowledge |
