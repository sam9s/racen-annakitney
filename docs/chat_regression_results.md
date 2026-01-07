# Chat Regression Test Results

**Run Date:** 2026-01-07 07:46:18

## Summary

| Metric | Value |
|--------|-------|
| Total Tests | 31 |
| Passed | 31 |
| Failed | 0 |
| Pass Rate | 100.0% |

---

## Detailed Results

### Basic Greeting

*Test that greetings are handled correctly*

**Turn 1:** PASS

- **User:** "Hello!"
- **Expected Intent:** `greeting`
- **Actual Intent:** `greeting`
- **Response Time:** 373ms
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
- **Response Time:** 524ms
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
- **Response Time:** 744ms
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
- **Response Time:** 1999ms
- **Keywords Found:** SoulAlign, Heal

**Response Excerpt:**
```
Yes, we have an exciting event happening on June 26, 2026:

**SoulAlign® Heal**

**When:** June 03 - September 30, 2026 | Sessions at 4:00 PM (London time)

**Where:** Zoom

**About this event:** 
SoulAlign® Heal is an expansive healing journey designed to transition from limited human identities in...
```

### Month Query - March

*Test month-based event filtering*

**Turn 1:** PASS

- **User:** "What events are happening in March?"
- **Expected Intent:** `event`
- **Actual Intent:** `event`
- **Response Time:** 2534ms
- **Keywords Found:** March, SoulAlign, Coach

**Response Excerpt:**
```
Here are the upcoming events happening in March:

1. [**SoulAlign® Manifestation Mastery**](https://www.annakitney.com/event/soulalign-manifestation-mastery/) - Jan 20 - Apr 07, 2026 (Zoom)

2. [**SoulAlign® Coach**](https://www.annakitney.com/event/soulalign-coach/) - Mar 04 - May 20, 2026 (Zoom)

...
```

### Month Query - January

*Test January events*

**Turn 1:** PASS

- **User:** "Show me events in January"
- **Expected Intent:** `event`
- **Actual Intent:** `event`
- **Response Time:** 2465ms
- **Keywords Found:** January, Identity Switch, Success Redefined

**Response Excerpt:**
```
Here are the upcoming events happening in January:

1. [**The Identity Overflow**](https://www.annakitney.com/event/the-identity-overflow/) - Jan 09 - Jan 11, 2026 (Zoom)

2. [**SoulAlign® Manifestation Mastery**](https://www.annakitney.com/event/soulalign-manifestation-mastery/) - Jan 20 - Apr 07, ...
```

### Ordinal Selection from List

*User selects '1' after seeing a numbered list*

**Turn 1:** PASS

- **User:** "What events do you have?"
- **Expected Intent:** `event`
- **Actual Intent:** `event`
- **Response Time:** 4160ms
- **Keywords Found:** 1., 2.

**Response Excerpt:**
```
Here are our upcoming events:

1. [**The Identity Overflow**](https://www.annakitney.com/event/the-identity-overflow/) - Jan 09 - Jan 11, 2026 (Zoom)

2. [**SoulAlign® Manifestation Mastery**](https://www.annakitney.com/event/soulalign-manifestation-mastery/) - Jan 20 - Apr 07, 2026 (Zoom)

3. [**Th...
```

**Turn 2:** PASS

- **User:** "1"
- **Expected Intent:** `followup_select`
- **Actual Intent:** `followup_select`
- **Response Time:** 67ms

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
- **Response Time:** 3685ms
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
- **Response Time:** 367ms

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

**Turn 1:** PASS

- **User:** "What events are coming up?"
- **Expected Intent:** `event`
- **Actual Intent:** `event`
- **Response Time:** 4806ms
- **Keywords Found:** 1., 2.

**Response Excerpt:**
```
Here are the upcoming events:

1. [**The Identity Overflow**](https://www.annakitney.com/event/the-identity-overflow/) - Jan 09 - Jan 11, 2026 (Zoom)

2. [**SoulAlign® Manifestation Mastery**](https://www.annakitney.com/event/soulalign-manifestation-mastery/) - Jan 20 - Apr 07, 2026 (Zoom)

3. [**Th...
```

**Turn 2:** PASS

- **User:** "option 2"
- **Expected Intent:** `followup_select`
- **Actual Intent:** `followup_select`
- **Response Time:** 396ms

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
- **Response Time:** 329ms
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
- **Response Time:** 459ms

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

**Turn 1:** PASS

- **User:** "What's the Success Redefined meditation?"
- **Expected Intent:** `event, hybrid`
- **Actual Intent:** `hybrid`
- **Response Time:** 3750ms
- **Keywords Found:** Success Redefined, Dubai

**Response Excerpt:**
```
**Success Redefined - The Meditation: LIVE IN DUBAI** is a transformational live event designed to help participants shift their mindset and connect with their true potential. Through guided meditation and powerful teachings, attendees will explore a redefined perspective on success, tapping into th...
```

**Turn 2:** PASS

- **User:** "tell me more"
- **Expected Intent:** `followup_confirm`
- **Actual Intent:** `followup_confirm`
- **Response Time:** 321ms

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
- **Response Time:** 2656ms
- **Keywords Found:** SoulAlign, Heal

**Response Excerpt:**
```
Yes, we do have an event on July 15,

2026. Here are the details:

**SoulAlign® Heal**

**When:** June 03 - September 30, 2026 | Sessions at 4:00 PM (London time)

**Where:** Zoom

---

**About this event:**

*SOULALIGN® QUANTUM HEALING THROUGH GOD CONSCIOUSNESS TO HAVE IT ALL!*

SoulAlign® Heal is ...
```

### Program Pricing Query

*Test knowledge intent for pricing questions*

**Turn 1:** PASS

- **User:** "How much does SoulAlign Coach cost?"
- **Expected Intent:** `knowledge`
- **Actual Intent:** `knowledge`
- **Response Time:** 2667ms
- **Keywords Missing:** investment, price, $

**Response Excerpt:**
```
I don’t have specific information about a program called "SoulAlign Coach." However, we do offer other fantastic programs like SoulAlign Business and [SoulAlign Money](https://www.annakitney.com/soulalign-money/) which have their own pricing. If you're interested, I can provide details about those o...
```

### Program Features Query

*Test knowledge intent for program details*

**Turn 1:** PASS

- **User:** "What's included in the SoulAlign Business program?"
- **Expected Intent:** `knowledge`
- **Actual Intent:** `knowledge`
- **Response Time:** 3393ms
- **Keywords Found:** business, coaching, program

**Response Excerpt:**
```
The SoulAlign® Business program is designed to help start-ups and established coaches, healers, and spiritual teachers serve their soul-aligned clients. Here’s what's included:

1. **Online Course** - Lifetime access to the SoulAlign® Business Online course, designed to assist you in building your b...
```

### Event Registration Intent

*Test event action word 'register'*

**Turn 1:** PASS

- **User:** "How do I register for The Identity Switch?"
- **Expected Intent:** `event`
- **Actual Intent:** `event`
- **Response Time:** 465ms
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
- **Response Time:** 447ms
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

**Turn 1:** PASS

- **User:** "Tell me about SoulAlign Heal"
- **Expected Intent:** `clarification, event, knowledge, hybrid`
- **Actual Intent:** `hybrid`
- **Response Time:** 3727ms
- **Keywords Found:** SoulAlign, Heal

**Response Excerpt:**
```
SoulAlign® Heal is a transformative multidimensional recalibration experience designed for those ready to leave behind the patterns of trauma and step into their God Consciousness. It's about shifting from merely healing the body to recognizing that you are the frequency broadcasting through it.

He...
```

### Date '1st of June' Not Ordinal

*CRITICAL: '1st of June' should be date, not ordinal*

**Turn 1:** PASS

- **User:** "Any events on the 1st of June?"
- **Expected Intent:** `event`
- **Actual Intent:** `event`
- **Response Time:** 472ms
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
- **Response Time:** 10374ms
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

**...
```

### General Upcoming Events

*Test general event listing*

**Turn 1:** PASS

- **User:** "What events are coming up?"
- **Expected Intent:** `event`
- **Actual Intent:** `event`
- **Response Time:** 4369ms
- **Keywords Found:** event, 1., 2.

**Response Excerpt:**
```
Here are our upcoming events:

1. [**The Identity Overflow**](https://www.annakitney.com/event/the-identity-overflow/) - Jan 09 - Jan 11, 2026 (Zoom)

2. [**SoulAlign® Manifestation Mastery**](https://www.annakitney.com/event/soulalign-manifestation-mastery/) - Jan 20 - Apr 07, 2026 (Zoom)

3. [**Th...
```

### Event Location Query

*Test event with location focus*

**Turn 1:** PASS

- **User:** "Are there any events in Dubai?"
- **Expected Intent:** `event`
- **Actual Intent:** `event`
- **Response Time:** 4481ms
- **Keywords Found:** Dubai, Success Redefined, meditation

**Response Excerpt:**
```
Here are the upcoming events:

1. [**The Identity Overflow**](https://www.annakitney.com/event/the-identity-overflow/) - Jan 09 - Jan 11, 2026 (Zoom)
2. [**SoulAlign® Manifestation Mastery**](https://www.annakitney.com/event/soulalign-manifestation-mastery/) - Jan 20 - Apr 07, 2026 (Zoom)
3. [**The ...
```

### Enrollment Intent

*Test enrollment question for programs*

**Turn 1:** PASS

- **User:** "How do I enroll in SoulAlign Coach?"
- **Expected Intent:** `knowledge, event`
- **Actual Intent:** `knowledge`
- **Response Time:** 2680ms
- **Keywords Found:** enroll, SoulAlign Coach

**Response Excerpt:**
```
Wonderful! SoulAlign Coach is part of our SoulAlign programs designed to help you create a thriving coaching business. The first step to enroll is to book a complimentary [Clarity Call](https://www.annakitney.com/clarity-call/). This allows us to understand your goals and see how this program can su...
```

### Bare 'yes' Without Context

*Test that bare 'yes' without event context doesn't misfire*

**Turn 1:** PASS

- **User:** "Hello"
- **Expected Intent:** `greeting`
- **Actual Intent:** `greeting`
- **Response Time:** 389ms

**Response Excerpt:**
```
Hello! I'm Anna's wellness assistant. I'm here to help you learn about our transformational programs and upcoming events. What would you like to explore today?
```

**Turn 2:** PASS

- **User:** "yes"
- **Expected Intent:** `other, greeting, followup_confirm`
- **Actual Intent:** `followup_confirm`
- **Response Time:** 1317ms

**Response Excerpt:**
```
Great! What would you like to know more about? Our programs, upcoming events, or something else on your mind?

---

*Feel free to explore more when you're ready:*
[Work With Me](https://www.annakitney.com/work-with-me/) | [All Programs](https://www.annakitney.com/all-the-things/)
```

### Add to Calendar Request

*Test calendar add functionality*

**Turn 1:** PASS

- **User:** "Can I add The Identity Switch to my calendar?"
- **Expected Intent:** `event`
- **Actual Intent:** `event`
- **Response Time:** 1760ms
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
- **Response Time:** 1483ms
- **Keywords Found:** SoulAlign
- **Keywords Missing:** September

**Response Excerpt:**
```
Here are the upcoming events:

1. [**SoulAlign® Heal**](https://www.annakitney.com/event/soulalign-heal/) - Jun 03 - Sep 30, 2026 (Zoom)

2. [**SoulAlign® Business 2026**](https://www.annakitney.com/event/soulalign-business/) - Sep 08 - Oct 27, 2026 (Zoom)

Would you like more details about any of t...
```
