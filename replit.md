# Anna Kitney Wellness Chatbot

## Overview
This is a RAG-based wellness chatbot for Anna Kitney's wellness coaching business (annakitney.com). The bot is named "Anna" and serves as a friendly guide to help visitors learn about wellness coaching programs and services.

## Architecture
- **Frontend**: React with Express server (Vite)
- **Backend**: Python Flask API for chat processing
- **RAG Engine**: OpenAI GPT-4o-mini with ChromaDB vector storage
- **Database**: PostgreSQL for conversation history and calendar events
- **Embeddable Widget**: `public/widget.js` for embedding on external sites
- **Calendar Sync**: Google Calendar to PostgreSQL with webhooks + scheduled backup

## Key Files
- `chatbot_engine.py` - Core RAG logic and response generation
- `safety_guardrails.py` - Safety filters and system prompts
- `webhook_server.py` - Flask API endpoints
- `knowledge_base.py` - ChromaDB vector database management
- `web_scraper.py` - Website content scraping
- `ingest_anna_website.py` - Script to ingest annakitney.com content
- `public/widget.js` - Embeddable chat widget for external sites
- `client/src/pages/Home.tsx` - React web UI for development/preview
- `events_service.py` - Python service for chatbot event queries
- `server/calendar-service.ts` - Google Calendar API integration
- `server/calendar-sync-service.ts` - Calendar to PostgreSQL sync

## Documentation (in /docs folder)
- `docs/CALENDAR_EVENTS_GUIDE.md` - Guide for Anna's team on adding event URLs
- `docs/DEPLOYMENT_BLUEPRINT.md` - Deployment instructions
- `docs/design_guidelines.md` - Frontend design guidelines

## Environment Variables Required
- `DATABASE_URL` - PostgreSQL connection string
- `AI_INTEGRATIONS_OPENAI_API_KEY` - OpenAI API key
- `AI_INTEGRATIONS_OPENAI_BASE_URL` - OpenAI API base URL
- `SESSION_SECRET` - Session encryption key

## Getting Started

### 1. Ingest Website Content
Run the ingestion script to populate the knowledge base:
```bash
python ingest_anna_website.py
```

### 2. Start the Application
The application runs via the "Start application" workflow which executes:
```bash
npm run dev
```

### 3. Embed the Widget
To embed the chatbot on annakitney.com:
```html
<script src="YOUR_REPL_URL/widget.js"></script>
```

## Branding
- Bot name: "Anna"
- Session prefix: "anna_"
- Website: annakitney.com
- Portal: annakitneyportal.com (checkout/course platform - always use www. prefix)
- Primary color: #03a9f4 (customizable)

## Safety Features
- Crisis content detection with professional referral
- Medical/mental health content filtering
- No personal information collection
- Rate limiting

## Events Integration (Google Calendar + PostgreSQL)

The chatbot has live integration with Anna's Google Calendar, synced to PostgreSQL for reliability and comprehensive event data.

### Architecture
1. **Google Calendar** - Source of truth for events
2. **PostgreSQL `calendar_events` table** - Synced copy with full descriptions and URLs
3. **Sync Service** - Webhooks for real-time + 30-minute scheduled backup
4. **Chatbot** - Reads from PostgreSQL for event queries

### Key Files
- `server/calendar-sync-service.ts` - Sync logic, URL parsing, scheduled sync
- `server/calendar-service.ts` - Google Calendar API integration
- `events_service.py` - Python service for chatbot event queries
- `shared/schema.ts` - Database schema including `calendarEvents` table

### Database Table: calendar_events
| Column | Type | Description |
|--------|------|-------------|
| id | serial | Primary key |
| googleEventId | varchar | Unique Google Calendar event ID |
| title | varchar | Event title |
| startDate | timestamp | Event start (UTC) |
| endDate | timestamp | Event end (UTC) |
| timezone | varchar | Original timezone (e.g., "Asia/Dubai") |
| location | text | Event location |
| description | text | Full event description |
| eventPageUrl | text | Link to event page on annakitney.com |
| checkoutUrl | text | Pay-in-full checkout link |
| checkoutUrl6Month | text | 6-month payment plan link |
| checkoutUrl12Month | text | 12-month payment plan link |
| programPageUrl | text | Program info page link |
| isActive | boolean | False for past events |
| lastSynced | timestamp | Last sync time |

### URL Parsing
Anna's team can add URLs to calendar event descriptions using this format:
```
---URLS---
EVENT_PAGE: https://www.annakitney.com/event/your-event/
CHECKOUT: https://www.annakitneyportal.com/checkout/product
CHECKOUT_6MONTH: https://www.annakitneyportal.com/checkout/product-6
CHECKOUT_12MONTH: https://www.annakitneyportal.com/checkout/product-12
PROGRAM_PAGE: https://www.annakitney.com/program-page/
---END_URLS---
```

### API Endpoints

#### Database Events (Primary - use these)
- `GET /api/events/db` - All active events from PostgreSQL
- `GET /api/events/db?includeInactive=true` - All events including past
- `GET /api/events/db/by-title/:title` - Specific event by title (fuzzy match)

#### Calendar Sync
- `POST /api/calendar/sync` - Trigger manual sync
- `POST /api/calendar/webhook` - Google Calendar webhook endpoint

#### Legacy Direct Calendar (still functional)
- `GET /api/events` - Direct from Google Calendar
- `GET /api/events/search?q=query` - Search events
- `GET /api/events/by-title/:title` - Get specific event
- `POST /api/events/book` - Add event to calendar
- `GET /api/calendars` - List available calendars

### Calendar ID
Anna Kitney Coaching calendar: `cms370prol01ksuq304erj1gmdug1v4m@import.calendar.google.com`

### Sync Behavior
- **Startup**: Full sync on application start
- **Scheduled**: Every 30 minutes
- **Webhooks**: Real-time when Google Calendar changes
- **Past Events**: Automatically marked as `isActive: false`

## Recent Changes
- **Follow-up Detection Safeguard (Jan 2026)**: Fixed `is_event_query()` and follow-up detection to require conversation history with an event before treating "yes" responses as event queries. Prevents misclassifying generic "yes" as event follow-ups when no event context exists. Updated `is_event_query(message, conversation_history)` signature to accept optional history parameter.
- **Event Styling Improvements (Jan 2026)**: Enhanced event description formatting with Lora serif font, text justification, teal-colored event subtitles (date | description lines), horizontal rule dividers, and italic text support. Changes applied to both Home.tsx and widget.js for consistency.
- **Markdown Link Rendering Fix (Jan 2026)**: Fixed both React web UI (Home.tsx) and embeddable widget (widget.js) to render markdown links correctly. Root cause: bold `**text**` was being matched BEFORE markdown links `[text](url)`, breaking `[**text**](url)` syntax. Solution: Match markdown links FIRST, then bold, then raw URLs.
- **Documentation Reorganization**: Moved all MD files to `/docs` folder for clarity
- **Two Rendering Systems**: 
  - `public/widget.js` = Embeddable widget for external sites (annakitney.com)
  - `client/src/pages/Home.tsx` = React web UI for development/Replit Preview
- **Calendar PostgreSQL Sync**: Events now sync from Google Calendar to PostgreSQL with full descriptions
- **URL Parsing**: Anna's team can add checkout/event URLs to calendar descriptions
- Added Google Calendar integration for live event data
- Implemented event booking (add to calendar) functionality
- Updated system prompts with event conversation flow
- Gated enrollment flow for programs (payment options only after explicit intent)
- Clarity Call-only programs: Elite Private Advisory, VIP Day
- Migrated from JoveHeal template to Anna Kitney branding
- Updated all URLs to annakitney.com
- Updated system prompts for Anna's wellness coaching business
- Fresh PostgreSQL database created
- Knowledge base ready for content ingestion

## Important Technical Notes
- **Markdown Parsing Order**: The LLM outputs `**[text](url)**` format (bold WRAPPING the link). The parsing order MUST be:
  1. `**[text](url)**` - Bold-wrapped links (highest priority)
  2. `[text](url)` - Plain markdown links
  3. `**text**` - Bold text
  4. Raw URLs
  This is implemented in both `Home.tsx` (renderMessageContent) and `widget.js` (createSafeContent) using separate regex patterns with overlap detection.
- **Two Websites**: annakitney.com (marketing) and annakitneyportal.com (checkout, requires www. prefix)
- **VERBATIM Delimiters**: Used in chatbot_engine.py to prevent LLM from paraphrasing event data
