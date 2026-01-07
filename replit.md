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
- `intent_router.py` - Intent-first query classification (EVENT/KNOWLEDGE/HYBRID/CLARIFICATION)
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

## Intent Router Architecture

The chatbot uses an "intent-first" routing system that classifies user queries BEFORE any database access, eliminating RAG pollution of event queries.

### Key File
- `intent_router.py` - IntentRouter class with pluggable handler system

### Intent Types
| Intent | Description | Data Sources |
|--------|-------------|--------------|
| EVENT | Specific date queries, event registration, booking | SQL only (PostgreSQL) |
| KNOWLEDGE | Program pricing, features, enrollment process | RAG only (ChromaDB) |
| HYBRID | General questions that may need both | SQL + RAG |
| CLARIFICATION | Ambiguous queries (e.g., same name for program and event) | Asks user first |
| GREETING | Hello, hi, etc. | No data query needed |
| FOLLOWUP_SELECT | User selecting from a numbered list (e.g., "1", "the first one") | Uses conversation history |
| FOLLOWUP_CONFIRM | User confirming interest (e.g., "yes", "tell me more") | Uses conversation history |
| OTHER | Fallback for unclassified queries | RAG + general response |

### Follow-up Detection (Single Decision Point)
The IntentRouter is the SINGLE decision point for all follow-up detection. This runs BEFORE other intent checks (after greeting).

**FOLLOWUP_SELECT**: When user types "1", "first", etc. AND the last bot message contains a numbered list:
- Router extracts the selection index (0-based)
- Passes `selection_index` to events_service
- events_service uses `_extract_events_from_history()` to parse the list and return the selected event

**FOLLOWUP_CONFIRM**: When user types "yes", "tell me more", etc.:
- Router checks context from last bot message
- Routes to EVENT or PROGRAM handler based on context

**Date Protection**: Messages containing date patterns (e.g., "June 1st") are NEVER treated as ordinal selections, even if they contain "1st". Date queries always take priority.

### Clarification Pathway
When the same name exists for both a program and an event (e.g., "SoulAlign Heal"), the system asks:
> "Are you asking about: 1. Program details or 2. Event dates?"

### Dynamic Data Loading
- Event titles loaded from PostgreSQL at Flask startup via `refresh_router_data()`
- Program names currently use predefined list (future: DB-driven)
- Called at startup in `webhook_server.py` via `initialize_intent_router()`

### Intent Classification Logic (Priority Order)
1. Greeting check → GREETING
2. Follow-up detection (if no date in message) → FOLLOWUP_SELECT or FOLLOWUP_CONFIRM
3. Date-specific queries → EVENT (high confidence 0.8)
4. Pricing/cost queries → KNOWLEDGE (high confidence 0.85)
5. Event action words (register, book, attend) → EVENT
6. Program match only → KNOWLEDGE
7. Event match only → EVENT
8. Both program AND event match → CLARIFICATION

### Adding New Intent Types (Future Scalability)
1. Add new `IntentType` enum value in `intent_router.py`
2. Add detection logic in `classify()` method
3. Add handler in `chatbot_engine.py` after intent classification block

## Recent Changes
- **Single Decision Point Follow-up Architecture (Jan 2026)**: Implemented FOLLOWUP_SELECT and FOLLOWUP_CONFIRM intent types in IntentRouter. Router is now the SINGLE decision point for all follow-up detection, eliminating competing logic in events_service.py. Key features:
  - Date patterns like "June 1st" are protected from ordinal matching (date queries always take priority)
  - `_extract_events_from_history()` parses numbered lists from previous bot messages
  - Defensive clarification when selection index is out of bounds
  - Removed ordinal detection from events_service `is_followup_response()` to prevent conflicts
- **Intent-First Router Architecture (Jan 2026)**: Implemented IntentRouter that classifies queries BEFORE any database access. Created `intent_router.py` with pluggable handler system supporting EVENT (SQL only), KNOWLEDGE (RAG only), HYBRID (both), and CLARIFICATION (asks user) intents. This eliminates RAG pollution of event queries.
- **Multi-day Event Support (Jan 2026)**: Added comprehensive support for multi-day/recurring events:
  - New `extract_specific_date()` function parses queries like "June 26", "1st of June", "26th July 2026"
  - New `filter_events_by_specific_date()` checks if a date falls within event's start-end range
  - Updated `filter_events_by_month()` to include events whose range overlaps the requested month
  - Updated `format_events_list()` to display date ranges for multi-day events (e.g., "Jun 03 - Sep 30, 2026")
  - Now correctly answers "any event on June 26" when SoulAlign® Heal runs June 3 - Sept 30
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
