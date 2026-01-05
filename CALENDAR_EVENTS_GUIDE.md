# Calendar Events Integration Guide

## Overview

The chatbot now pulls event information directly from Anna's Google Calendar, stored in a PostgreSQL database for reliability and speed. Events sync automatically every 30 minutes and in real-time when changes are made.

## How It Works

1. Anna's team creates/updates events in Google Calendar
2. The system automatically syncs events to the database
3. The chatbot reads from the database when users ask about events
4. Full event descriptions are now available for the chatbot to share

## Adding URLs to Calendar Events

To include clickable links in chatbot responses (checkout pages, event pages, program info), add a special section to the Google Calendar event description.

### URL Format

Add this block at the END of your event description:

```
---URLS---
EVENT_PAGE: https://www.annakitney.com/event/your-event-name/
CHECKOUT: https://www.annakitneyportal.com/checkout/your-product
CHECKOUT_6MONTH: https://www.annakitneyportal.com/checkout/your-product-6-month
CHECKOUT_12MONTH: https://www.annakitneyportal.com/checkout/your-product-12-month
PROGRAM_PAGE: https://www.annakitney.com/your-program-page/
---END_URLS---
```

### Field Descriptions

| Field | Description | Required |
|-------|-------------|----------|
| EVENT_PAGE | Link to the event landing page on annakitney.com | Recommended |
| CHECKOUT | Direct checkout link (pay-in-full) | For paid events |
| CHECKOUT_6MONTH | 6-month payment plan checkout | Optional |
| CHECKOUT_12MONTH | 12-month payment plan checkout | Optional |
| PROGRAM_PAGE | General program info page | Optional |

### Example

Here's what a complete event description might look like:

```
3-Day Identity Overflow Challenge

Join Anna for an immersive experience to rewire your financial thermostat and dissolve subconscious limitations.

What you'll learn:
- Day 1: Command reality, don't chase it
- Day 2: The identity collapse - become her now
- Day 3: Lock in the overflow as your new default

Includes VIP bonuses and daily giveaways!

---URLS---
EVENT_PAGE: https://www.annakitney.com/event/the-identity-overflow/
CHECKOUT: https://www.annakitneyportal.com/checkout/identity-overflow
---END_URLS---
```

### Important Notes

1. **Use exact format**: The `---URLS---` and `---END_URLS---` markers must be exactly as shown
2. **One URL per line**: Each URL type goes on its own line
3. **No extra spaces**: Don't add extra spaces around the colon
4. **Portal URLs need www**: Always use `https://www.annakitneyportal.com/` (with www)
5. **URLs are optional**: If you don't have a checkout link yet, just skip that line

## Calendar Sync Status

- **Sync Frequency**: Every 30 minutes + real-time via webhooks
- **Calendar ID**: cms370prol01ksuq304erj1gmdug1v4m@import.calendar.google.com
- **Manual Sync**: Available via admin endpoint if needed

## Troubleshooting

### Event not showing in chatbot?
- Wait 30 minutes for the next sync, or trigger manual sync
- Ensure the event is in the future (past events are marked inactive)
- Check that the event is on the correct calendar

### URLs not being picked up?
- Verify the `---URLS---` and `---END_URLS---` markers are correct
- Check for typos in URL field names (EVENT_PAGE, CHECKOUT, etc.)
- Make sure URLs are complete (include https://)

### Multi-week programs
- Use the start date of the FIRST session
- Use the end date of the LAST session
- Include the full schedule in the description

## Technical Endpoints

For developers:

- `GET /api/events/db` - All active events from database
- `GET /api/events/db/by-title/:title` - Specific event by title
- `POST /api/calendar/sync` - Trigger manual sync
- `POST /api/calendar/webhook` - Google Calendar webhook

## Questions?

Contact the development team if you need help with:
- Adding new URL types
- Troubleshooting sync issues
- Custom event formats
