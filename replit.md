# Anna Kitney Wellness Chatbot

## Overview
This project is a RAG-based wellness chatbot for Anna Kitney's coaching business (annakitney.com). The bot, named "Anna," guides visitors through wellness coaching programs and services. Its purpose is to provide information, manage event inquiries, and facilitate engagement with Anna Kitney's offerings, ultimately enhancing user experience and supporting business growth.

## User Preferences
I prefer iterative development with clear communication on significant changes. Please ask before making major architectural modifications or introducing new external dependencies. I value concise explanations and well-documented code. When presenting options or summaries, please use clear, numbered lists.

## System Architecture
The chatbot employs a hybrid architecture:
-   **Frontend**: React with Express server (Vite) for the web UI, and an embeddable `widget.js` for external site integration.
-   **Backend**: Python Flask API handles chat processing and integrations.
-   **RAG Engine**: Utilizes OpenAI GPT-4o-mini with ChromaDB for vector storage, managed by `chatbot_engine.py` and `knowledge_base.py`.
-   **Intent Routing**: An "intent-first" system (`intent_router.py`) classifies queries into types like EVENT, KNOWLEDGE, HYBRID, CLARIFICATION, GREETING, FOLLOWUP_SELECT, FOLLOWUP_CONFIRM, or OTHER to direct them to appropriate handlers and data sources, preventing RAG pollution for event queries. Follow-up detection is a single decision point within the router.
-   **Database**: PostgreSQL stores conversation history and synchronized Google Calendar events, handled by `events_service.py` and `server/calendar-sync-service.ts`.
-   **Calendar Integration**: Google Calendar is the source of truth for events, synced to PostgreSQL via webhooks and scheduled backups for real-time and robust event data. Event descriptions can include specific URLs for event pages and checkout options.
-   **Safety Features**: Includes crisis content detection, medical/mental health filtering, no personal information collection, and rate limiting.
-   **Branding**: The bot is named "Anna," uses `annakitney.com` and `annakitneyportal.com` (for checkout/courses), with a primary color of `#03a9f4`.
-   **Content Ingestion**: A `web_scraper.py` and `ingest_anna_website.py` script are used to populate the knowledge base from `annakitney.com`.
-   **UI/UX**: The UI displays event details with Lora serif font, justified text, teal subtitles, horizontal rule dividers, and italic text support. Markdown links are rendered correctly with a specific parsing order to handle `**[text](url)**` formats.

## External Dependencies
-   **OpenAI API**: For large language model capabilities (GPT-4o-mini) and embeddings.
-   **ChromaDB**: Vector database for RAG knowledge storage.
-   **PostgreSQL**: Relational database for conversation history and synchronized calendar events.
-   **Google Calendar API**: For event management and real-time synchronization.
-   **Vite**: Frontend tooling for React development.
-   **Express**: Backend server for the React frontend.
-   **Flask**: Python web framework for the API backend.

## Pending Items / Future Work

### Google Calendar Webhook (Real-time Sync) - NOT YET CONFIGURED
The webhook endpoint exists (`POST /api/calendar/webhook`) but requires Google Cloud Console configuration:
1. Create a Google Cloud Project with Calendar API enabled
2. Set up push notifications (webhooks) in Google Calendar API
3. Configure the webhook URL to point to your deployed app's `/api/calendar/webhook` endpoint
4. Webhooks require HTTPS (will work once app is published/deployed)

**Current workaround**: 30-minute scheduled sync runs automatically, plus full sync on app startup.

### Other Future Enhancements
- In-chat booking with email confirmations
- Payment processing integration
- Multi-language support

## Recent Changes (Jan 2026)

1. **Greeting Fix**: Restored the curated greeting from `get_greeting_message()` in chatbot_engine.py. **CRITICAL: Never replace this with LLM calls** - the curated greeting is brand-approved and intentional. The LLM produces generic responses; the curated message is warm and structured.

2. **Dynamic Location Queries**: Made location-based event queries fully dynamic (no hardcoded cities). Queries like "Is there an event in [any city]?" now search all events by title and location fields.

3. **GUI Test Runner**: Added `/test-runner` page for end-to-end testing of chatbot functionality. Runs 30 test scenarios covering events, dates, enrollment, programs, safety.

4. **Intent Classification Improvements**: Expanded TIME_PATTERNS for month-based queries ("events in March"), generic event queries, and location queries.

5. **Single Decision Point Follow-up Architecture**: FOLLOWUP_SELECT and FOLLOWUP_CONFIRM intent types in IntentRouter for handling numbered list selections.

6. **Calendar PostgreSQL Sync**: Events sync from Google Calendar to PostgreSQL with full descriptions and URL parsing.

7. **Progressive Event Detail Flow**: Three-stage event information delivery:
   - **Stage 1 (Summary)**: User asks about an event → Deterministic summary with "Would you like more details about this event?" CTA
   - **Stage 2 (Details)**: User confirms → VERBATIM event details from database with "[event page](url)" link
   - **Stage 3 (Navigate)**: User confirms again → `[NAVIGATE:url]` emitted for navigation
   - Uses `EventFollowupStage` enum (NONE, LISTING_SHOWN, SUMMARY_SHOWN, DETAILS_SHOWN)
   - New intent types: EVENT_DETAIL_REQUEST, EVENT_NAVIGATE
   - Stage-1 bypasses LLM to guarantee exact CTA for reliable stage detection

## Important Technical Notes
- **Markdown Parsing Order**: Bold-wrapped links `**[text](url)**` must be matched FIRST, then plain links, then bold text.
- **Two Websites**: annakitney.com (marketing) and annakitneyportal.com (checkout, requires www. prefix)
- **VERBATIM Delimiters**: Used in chatbot_engine.py to prevent LLM from paraphrasing event data