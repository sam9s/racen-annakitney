# Anna Kitney Wellness Chatbot

## Overview
This is a RAG-based wellness chatbot for Anna Kitney's wellness coaching business (annakitney.com). The bot is named "Anna" and serves as a friendly guide to help visitors learn about wellness coaching programs and services.

## Architecture
- **Frontend**: Next.js with React components
- **Backend**: Python Flask API for chat processing
- **RAG Engine**: OpenAI GPT-4o-mini with ChromaDB vector storage
- **Database**: PostgreSQL for conversation history
- **Embeddable Widget**: `public/widget.js` for embedding on external sites

## Key Files
- `chatbot_engine.py` - Core RAG logic and response generation
- `safety_guardrails.py` - Safety filters and system prompts
- `webhook_server.py` - Flask API endpoints
- `knowledge_base.py` - ChromaDB vector database management
- `web_scraper.py` - Website content scraping
- `ingest_anna_website.py` - Script to ingest annakitney.com content
- `public/widget.js` - Embeddable chat widget
- `src/app/page.tsx` - Main chat interface
- `src/components/` - React components

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
- Primary color: #03a9f4 (customizable)

## Safety Features
- Crisis content detection with professional referral
- Medical/mental health content filtering
- No personal information collection
- Rate limiting

## Events Integration (Google Calendar)

The chatbot has live integration with Anna's Google Calendar for real-time event information.

### Key Files
- `server/calendar-service.ts` - Google Calendar API integration (Express/TypeScript)
- `events_service.py` - Python service for chatbot event queries

### Features
- **Live Event Data**: Fetches upcoming events from Anna's synced Google Calendar
- **Event Queries**: Users can ask "What events are coming up?" or ask about specific events
- **Navigation**: Bot navigates users to event pages (pattern: `/event/[event-slug]/`)
- **Calendar Booking**: Users can add events to their calendar with "add to my calendar"

### API Endpoints
- `GET /api/events` - List upcoming events
- `GET /api/events/search?q=query` - Search events
- `GET /api/events/by-title/:title` - Get specific event
- `POST /api/events/book` - Add event to calendar
- `GET /api/calendars` - List available calendars

### Calendar ID
Anna Kitney Coaching calendar: `cms370prol01ksuq304erj1gmdug1v4m@import.calendar.google.com`

## Recent Changes
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
