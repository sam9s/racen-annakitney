# Chat Regression Test Results

**Run Date:** 2026-01-07 07:37:36

## Summary

| Metric | Value |
|--------|-------|
| Total Tests | 31 |
| Passed | 23 |
| Failed | 8 |
| Pass Rate | 74.2% |

---

## Detailed Results

### Basic Greeting

*Test that greetings are handled correctly*

**Turn 1:** PASS

- **User:** "Hello!"
- **Expected Intent:** `greeting`
- **Actual Intent:** `greeting`
- **Response Time:** 1177ms
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
- **Response Time:** 419ms
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
- **Response Time:** 549ms
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
- **Response Time:** 2685ms
- **Keywords Found:** SoulAlign, Heal

**Response Excerpt:**
```
Yes! On June 26, 2026, we are hosting **SoulAlign® Heal**. Here are the details:

**When:** June 03 - September 30, 2026 | Sessions at 4:00 PM (London time)

**Where:** Zoom

---

**About this event:**

*SOULALIGN® QUANTUM HEALING THROUGH GOD CONSCIOUSNESS TO HAVE IT ALL!*

SoulAlign® Heal is a mult...
```

### Month Query - March

*Test month-based event filtering*

**Turn 1:** FAIL

- **User:** "What events are happening in March?"
- **Expected Intent:** `event`
- **Actual Intent:** `knowledge`
- **Response Time:** 2125ms
- **Keywords Found:** March, SoulAlign
- **Keywords Missing:** Coach

**Response Excerpt:**
```
Here are our upcoming events in March:

**[SoulAlign Manifestation Mastery](https://www.annakitney.com/soulalign-manifestation-mastery/)**  
Starts: March 5, 2026  
Time: 5:00 PM GMT  
Description: A 12-week mastermind experience to expand your energetic capacity to receive abundant overflow into ev...
```

### Month Query - January

*Test January events*

**Turn 1:** FAIL

- **User:** "Show me events in January"
- **Expected Intent:** `event`
- **Actual Intent:** `knowledge`
- **Response Time:** 2094ms
- **Keywords Found:** January
- **Keywords Missing:** Identity Switch, Success Redefined

**Response Excerpt:**
```
Here are our upcoming events in January:

**The Identity Overflow**
- **Date:** January 9-11, 2026
- **Time:** Check event page for start times
- **Description:** This 3-Part Challenge focuses on personal growth and understanding.

Would you like to know more about this event or any others?

---

*I...
```

### Ordinal Selection from List

*User selects '1' after seeing a numbered list*

**Turn 1:** FAIL

- **User:** "What events do you have?"
- **Expected Intent:** `event`
- **Actual Intent:** `knowledge`
- **Response Time:** 2144ms
- **Keywords Missing:** 1., 2.

**Response Excerpt:**
```
Here are our upcoming events:

- **The Identity Overflow**: A 3-Part Challenge happening January 9-11, 2026 on Zoom.

Would you like more details about any of these?
```

**Turn 2:** PASS

- **User:** "1"
- **Expected Intent:** `followup_select`
- **Actual Intent:** `followup_select`
- **Response Time:** 60ms

**Response Excerpt:**
```
**The Identity Overflow**

**When:** January 09 - January 11, 2026 | Sessions at 9:00 PM (Dubai time)

**Where:** Zoom

---

**About this event:**

9-11TH JANUARY 2026 | A 3-Part Challenge With Anna Kitney for Soul-Led Entrepreneurs
Manifest Consistently. Expand Effortlessly. Lead From Overflow.
Rew...
```

### Ordinal 'the first one'

*User says 'the first one' to select*

**Turn 1:** PASS

- **User:** "Tell me about upcoming events"
- **Expected Intent:** `event`
- **Actual Intent:** `event`
- **Response Time:** 3895ms
- **Keywords Found:** 1., 2.

**Response Excerpt:**
```
Here are our upcoming events:

1. [**The Identity Overflow**](https://www.annakitney.com/event/the-identity-overflow/) - Jan 09 - Jan 11, 2026 (Zoom)

2. [**SoulAlign® Manifestation Mastery**](https://www.annakitney.com/event/soulalign-manifestation-mastery/) - Jan 20 - Apr 07, 2026 (Zoom)

3. [**Th...
```

**Turn 2:** PASS

- **User:** "the first one"
- **Expected Intent:** `followup_select`
- **Actual Intent:** `followup_select`
- **Response Time:** 369ms

**Response Excerpt:**
```
**The Identity Overflow**

**When:** January 09 - January 11, 2026 | Sessions at 9:00 PM (Dubai time)

**Where:** Zoom

---

**About this event:**

9-11TH JANUARY 2026 | A 3-Part Challenge With Anna Kitney for Soul-Led Entrepreneurs
Manifest Consistently. Expand Effortlessly. Lead From Overflow.
Rew...
```

### Ordinal 'option 2'

*User says 'option 2' to select second item*

**Turn 1:** FAIL

- **User:** "What events are coming up?"
- **Expected Intent:** `event`
- **Actual Intent:** `knowledge`
- **Response Time:** 1942ms
- **Keywords Missing:** 1., 2.

**Response Excerpt:**
```
Here are our upcoming events:

**The Identity Overflow**  
Date: January 9-11, 2026  
Description: Join us for a transformative 3-Part Challenge designed to enhance your self-discovery and growth.

Would you like more details about any of these?
```

**Turn 2:** PASS

- **User:** "option 2"
- **Expected Intent:** `followup_select`
- **Actual Intent:** `followup_select`
- **Response Time:** 385ms

**Response Excerpt:**
```
**The Identity Overflow**

**When:** January 09 - January 11, 2026 | Sessions at 9:00 PM (Dubai time)

**Where:** Zoom

---

**About this event:**

9-11TH JANUARY 2026 | A 3-Part Challenge With Anna Kitney for Soul-Led Entrepreneurs
Manifest Consistently. Expand Effortlessly. Lead From Overflow.
Rew...
```

### Follow-up 'yes' After Event

*User confirms interest with 'yes'*

**Turn 1:** PASS

- **User:** "Tell me about The Identity Switch"
- **Expected Intent:** `event`
- **Actual Intent:** `event`
- **Response Time:** 426ms
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

**Turn 2:** PASS

- **User:** "yes"
- **Expected Intent:** `followup_confirm`
- **Actual Intent:** `followup_confirm`
- **Response Time:** 618ms

**Response Excerpt:**
```
**The Identity Switch**

**When:** Saturday, January 24, 2026 from 12:00 PM - 7:00 PM (Dubai time)

**Where:** Zoom

---

**About this event:**

*WITH SELF-MADE 7-FIGURE SPIRITUAL BUSINESS COACH, ANNA KITNEY*

Manifestation Isn’t Magic — It’s Identity.
And You’re About to Switch Timelines.
1-Day Liv...
```

### Follow-up 'tell me more'

*User asks for more info*

**Turn 1:** FAIL

- **User:** "What's the Success Redefined meditation?"
- **Expected Intent:** `event`
- **Actual Intent:** `hybrid`
- **Response Time:** 2406ms
- **Keywords Found:** Success Redefined, Dubai

**Response Excerpt:**
```
**Success Redefined - The Meditation: LIVE IN DUBAI** is an immersive live event designed to explore the deeper aspects of success through meditation. This experience invites participants to redefine success on their own terms, aligning with their true purpose and intentions. 

Would you like me to ...
```

**Turn 2:** PASS

- **User:** "tell me more"
- **Expected Intent:** `followup_confirm`
- **Actual Intent:** `followup_confirm`
- **Response Time:** 475ms

**Response Excerpt:**
```
**Success Redefined - The Meditation: LIVE IN DUBAI**

**When:** Sunday, January 25, 2026 from 9:30 AM - 12:00 PM (Dubai time)

**Where:** Trove Best Shisha Lounge In Dubai Ground floor,Fashion avenue, The Dubai Mall – Burj Khalifa – Downtown Dubai – Dubai – United Arab Emirates, Trove Best Shisha L...
```

### Multi-day Event Query

*Query about date within a multi-day event range*

**Turn 1:** PASS

- **User:** "Is there an event on July 15th?"
- **Expected Intent:** `event`
- **Actual Intent:** `event`
- **Response Time:** 3639ms
- **Keywords Found:** SoulAlign, Heal

**Response Excerpt:**
```
Here are our upcoming events:

**SoulAlign® Heal**

**When:** June 03 - September 30, 2026 | Sessions at 4:00 PM (London time)

**Where:** Zoom

---

**About this event:**

*SOULALIGN® QUANTUM HEALING THROUGH GOD CONSCIOUSNESS TO HAVE IT ALL!*

SoulAlign® Heal

*WITH ANNA KITNEY*

**$150M+**

*COMBI...
```

### Program Pricing Query

*Test knowledge intent for pricing questions*

**Turn 1:** PASS

- **User:** "How much does SoulAlign Coach cost?"
- **Expected Intent:** `knowledge`
- **Actual Intent:** `knowledge`
- **Response Time:** 1564ms
- **Keywords Missing:** investment, price, $

**Response Excerpt:**
```
I don’t have specific information about the cost of the SoulAlign Coach program. I recommend reaching out to our team for the most accurate details. You can contact us at https://www.annakitney.com/contact. We're here to help!
```

### Program Features Query

*Test knowledge intent for program details*

**Turn 1:** PASS

- **User:** "What's included in the SoulAlign Business program?"
- **Expected Intent:** `knowledge`
- **Actual Intent:** `knowledge`
- **Response Time:** 3067ms
- **Keywords Found:** business, coaching, program

**Response Excerpt:**
```
The SoulAlign® Business program is designed to help start-ups and established coaches, healers, therapists, and spiritual teachers serve their soul-aligned clients. Here’s what’s included:

1. **Lifetime access to the online course** - Learn at your own pace with all self-study materials.

2. **8 we...
```

### Event Registration Intent

*Test event action word 'register'*

**Turn 1:** PASS

- **User:** "How do I register for The Identity Switch?"
- **Expected Intent:** `event`
- **Actual Intent:** `event`
- **Response Time:** 450ms
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
- **Response Time:** 425ms
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
- **Response Time:** 3137ms
- **Keywords Found:** SoulAlign, Heal

**Response Excerpt:**
```
SoulAlign® Heal is a multidimensional recalibration experience designed for those ready to step beyond traditional healing and embrace their divine consciousness. Here's what it offers:

1. **Radical Shift** - Transition from fixing the past to remembering your inherent wholeness and divinity.

2. *...
```

### Date '1st of June' Not Ordinal

*CRITICAL: '1st of June' should be date, not ordinal*

**Turn 1:** PASS

- **User:** "Any events on the 1st of June?"
- **Expected Intent:** `event`
- **Actual Intent:** `event`
- **Response Time:** 392ms
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
- **Response Time:** 3934ms
- **Keywords Found:** event
- **Keywords Missing:** July

**Response Excerpt:**
```
Here are our upcoming events: 

**SoulAlign® Heal**  
**When:** June 03 - September 30, 2026 | Sessions at 4:00 PM (London time)  
**Where:** Zoom  

---

**About this event:**

*SOULALIGN® QUANTUM HEALING THROUGH GOD CONSCIOUSNESS TO HAVE IT ALL!*

SoulAlign® Heal

*WITH ANNA KITNEY*

**$150M+**  
...
```

### General Upcoming Events

*Test general event listing*

**Turn 1:** FAIL

- **User:** "What events are coming up?"
- **Expected Intent:** `event`
- **Actual Intent:** `knowledge`
- **Response Time:** 1677ms
- **Keywords Found:** event
- **Keywords Missing:** 1., 2.

**Response Excerpt:**
```
Here are our upcoming events:

**The Identity Overflow**  
Date: January 9-11, 2026  
Location: Zoom  
Description: Join us for a transformative 3-Part Challenge designed to explore and expand your identity. 

Would you like more details about any of these?
```

### Event Location Query

*Test event with location focus*

**Turn 1:** FAIL

- **User:** "Are there any events in Dubai?"
- **Expected Intent:** `event`
- **Actual Intent:** `knowledge`
- **Response Time:** 2366ms
- **Keywords Found:** Dubai
- **Keywords Missing:** Success Redefined, meditation

**Response Excerpt:**
```
Here are our upcoming events in Dubai:

1. **The Identity Overflow**  
   Date: January 9-11, 2026  
   Description: A 3-Part Challenge focused on unlocking your potential.

Would you like more details about this event or any other upcoming events?
```

### Enrollment Intent

*Test enrollment question for programs*

**Turn 1:** PASS

- **User:** "How do I enroll in SoulAlign Coach?"
- **Expected Intent:** `knowledge, event`
- **Actual Intent:** `knowledge`
- **Response Time:** 1923ms
- **Keywords Found:** enroll
- **Keywords Missing:** SoulAlign Coach

**Response Excerpt:**
```
Wonderful! To enroll in the SoulAlign® Coach program, the first step is to schedule a complimentary [Clarity Call](https://www.annakitney.com/clarity-call/) with us. This will help us understand your goals and see how this program can best support you. Would you like me to take you to the Clarity Ca...
```

### Bare 'yes' Without Context

*Test that bare 'yes' without event context doesn't misfire*

**Turn 1:** PASS

- **User:** "Hello"
- **Expected Intent:** `greeting`
- **Actual Intent:** `greeting`
- **Response Time:** 392ms

**Response Excerpt:**
```
Hello! I'm Anna's wellness assistant. I'm here to help you learn about our transformational programs and upcoming events. What would you like to explore today?
```

**Turn 2:** PASS

- **User:** "yes"
- **Expected Intent:** `other, greeting, followup_confirm`
- **Actual Intent:** `followup_confirm`
- **Response Time:** 1354ms

**Response Excerpt:**
```
I'm glad you're here! What specific questions or topics are you interested in? We can discuss our programs, upcoming events, or anything else on your mind.
```

### Add to Calendar Request

*Test calendar add functionality*

**Turn 1:** PASS

- **User:** "Can I add The Identity Switch to my calendar?"
- **Expected Intent:** `event`
- **Actual Intent:** `event`
- **Response Time:** 2086ms
- **Keywords Found:** calendar, Identity Switch

**Response Excerpt:**
```
I've added The Identity Switch to your calendar!
```

### September Events Query

*Test month with multi-day events overlapping*

**Turn 1:** PASS

- **User:** "What's happening in September 2026?"
- **Expected Intent:** `event`
- **Actual Intent:** `event`
- **Response Time:** 1643ms
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
| ordinal_option_2 | 1 | What events are coming up?... | event | knowledge |
| followup_tell_me_more | 1 | What's the Success Redefined m... | event | hybrid |
| disambiguation_soualign_heal | 1 | Tell me about SoulAlign Heal... | clarification, event, knowledge | hybrid |
| upcoming_events_general | 1 | What events are coming up?... | event | knowledge |
| event_location | 1 | Are there any events in Dubai?... | event | knowledge |
