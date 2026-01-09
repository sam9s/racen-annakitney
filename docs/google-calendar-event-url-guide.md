# Google Calendar Event URL Guide

## For Anna Kitney's Team

This guide explains how to add event page URLs to Google Calendar events so the chatbot can correctly navigate users to the right pages.

---

## Why This Matters

The chatbot uses event information from Google Calendar to help visitors. When a user asks about an event and wants to visit the event page, the chatbot needs the correct URL.

**Problem:** Some event page URLs don't match the event name (e.g., "SoulAlign® Manifestation Mastery" has URL `/phoenixrising/`).

**Solution:** Include the event page URL directly in the Google Calendar event description.

---

## How to Add Event URLs

### Step 1: Open the Event in Google Calendar

Go to Google Calendar and click on the event you want to update.

### Step 2: Edit the Description

At the **very end** of the event description, add a URLs section like this:

```
---URLS---
EVENT_PAGE: https://www.annakitney.com/event/your-event-slug/
---END_URLS---
```

### Example

If your event is "SoulAlign® Manifestation Mastery" and the website URL is `https://www.annakitney.com/event/phoenixrising/`, your description should end with:

```
...rest of your event description here...

---URLS---
EVENT_PAGE: https://www.annakitney.com/event/phoenixrising/
---END_URLS---
```

---

## Optional: Add Checkout URLs

If your event has direct checkout/enrollment links, you can add them all in the URLs section:

```
---URLS---
EVENT_PAGE: https://www.annakitney.com/event/phoenixrising/
CHECKOUT: https://www.annakitneyportal.com/checkout/your-checkout-link
CHECKOUT_6MONTH: https://www.annakitneyportal.com/checkout/6-month-plan
CHECKOUT_12MONTH: https://www.annakitneyportal.com/checkout/12-month-plan
PROGRAM_PAGE: https://www.annakitney.com/soulalign-manifestation-mastery/
---END_URLS---
```

---

## URL Format Reference

| URL Type | Format | Example |
|----------|--------|---------|
| Event Page | `EVENT_PAGE: [url]` | `EVENT_PAGE: https://www.annakitney.com/event/phoenixrising/` |
| Checkout | `CHECKOUT: [url]` | `CHECKOUT: https://www.annakitneyportal.com/checkout/abc123` |
| 6-Month Plan | `CHECKOUT_6MONTH: [url]` | `CHECKOUT_6MONTH: https://www.annakitneyportal.com/checkout/6mo` |
| 12-Month Plan | `CHECKOUT_12MONTH: [url]` | `CHECKOUT_12MONTH: https://www.annakitneyportal.com/checkout/12mo` |
| Program Page | `PROGRAM_PAGE: [url]` | `PROGRAM_PAGE: https://www.annakitney.com/program-name/` |

---

## Important Notes

1. **Place URLs at the end** of the description, each on its own line
2. **Use the exact format** shown above (including the colon after "Event Page")
3. **Changes sync automatically** - the chatbot will pick up updates within 30 minutes
4. **Test after updating** - ask the chatbot about your event to verify the correct URL appears

---

## Current Events Checklist

Please verify/update URLs for these events:

- [ ] The Identity Overflow
- [ ] SoulAlign® Manifestation Mastery (uses /phoenixrising/)
- [ ] The Identity Switch (uses /theidentityswitch/)
- [ ] Success Redefined – The Meditation: LIVE IN DUBAI
- [ ] SoulAlign® Coach (uses /soulalign-manifestation-mastery/)
- [ ] SoulAlign® Heal
- [ ] SoulAlign® Business 2026

---

## Questions?

If you have any questions about this process, please reach out to the development team.
