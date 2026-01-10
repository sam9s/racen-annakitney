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
-   **Branding**: The bot is named "Anna," uses `annakitney.com` and `annakitneyportal.com` (for checkout/courses). Primary color is Gold (#D4AF37), background is Cream (#F5F1E8), matching the Anna Kitney brand aesthetic for seamless iframe embedding.
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

### Admin Dashboard (Planned)
Comprehensive dashboard for monitoring and managing the chatbot system. See `docs/dashboard-design.md` for full design specification including:
- Chat sessions and transcripts viewer
- Analytics overview
- Event/calendar management with inline URL editing
- Database viewer and editor
- Safety and security logs
- System health monitoring
- Sync controls

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

8. **Single Source of Truth for CTAs** (Jan 2026):
   - Canonical CTA constants defined in `events_service.py`: `STAGE1_CTA`, `STAGE2_CTA_TEMPLATE`, `STAGE2_CTA_NO_URL`
   - Router uses `_cta_to_regex()` function to derive detection patterns PROGRAMMATICALLY from CTAs
   - Any CTA wording change automatically updates stage detection - no manual pattern updates needed
   - Shared helpers: `_find_event_for_stage1()`, `_format_event_date_range()` for consistent event lookup

9. **Stricter Program Filtering**:
   - Requires confidence thresholds for all matches (`CONFIDENT_MATCH_THRESHOLD`, `FUZZY_MATCH_THRESHOLD`)
   - Falls back to `_build_disambiguation_response()` when multiple matches have close scores
   - Prevents low-confidence matches from surfacing wrong events

10. **Calendar Sync URL Preservation** (Jan 2026):
    - Fixed `server/calendar-sync-service.ts` to preserve manually set URLs during sync
    - Sync now checks for existing database URLs before overwriting
    - Priority: Calendar description URLs > Existing DB URLs > Default null
    - Manual database edits now persist through scheduled syncs

11. **Public Events API & Lovable Integration** (Jan 2026):
    - Added `/api/public/events` endpoint with CORS support for external landing pages
    - Added postMessage listener in `Home.tsx` for search-to-chat integration
    - Created `docs/lovable-prompt-final.md` with complete landing page prompt
    - Chatbot can be embedded via iframe on external pages
    - Search queries from Lovable landing page auto-send to chatbot

12. **Chatbot Theme Update for Iframe Embedding** (Jan 2026):
    - Updated `client/src/index.css` with cream/gold color scheme matching annakitney.com
    - Light mode: Cream background (#F5F1E8), Gold primary (#D4AF37), dark gray text
    - Dark mode: Warm dark brown with gold accents for consistency
    - Custom scrollbar styling with gold/cream colors
    - Seamless visual integration when embedded in Lovable landing page

13. **Removed JoveHeal-Specific LIVE_SESSION_REFERRAL Guardrail** (Jan 2026):
    - Disabled `check_for_live_session_topics` guardrail in `safety_guardrails.py`
    - This was a JoveHeal-specific guardrail (energy healing, chakra work) - NOT relevant to Anna
    - Anna's specific session redirects TBD - we don't know her preferences yet
    - Only universal common-sense guardrails remain:
      1. Crisis content (suicide, self-harm)
      2. Abuse/violence
      3. Extreme distress
      4. No psychiatric/psychological advice
      5. No medical advice

14. **Month Query Handling Fixes** (Jan 2026):
    - Fixed date parsing: Added `(?!\d)` negative lookahead in `_extract_date_from_query()` to prevent "April 2026" from being parsed as "April 20, 2026"
    - Month filter now checked BEFORE event keyword check in `_get_event_context_internal()` so queries like "What about in May?" correctly trigger month filtering instead of falling back to conversation history

15. **Event Follow-up Routing Fixes** (Jan 2026):
    - Fixed `_find_event_from_history` to prioritize PRIMARY event by position (earliest mention = main topic)
    - Added `_extract_event_from_message` to extract event name from bot responses for FOLLOWUP_CONFIRM handling
    - Added `get_event_details_by_name` for direct event lookup by name
    - Fixed key mismatch in `_build_event_summary_response` to support both `start` and `startDate` keys
    - Now correctly shows Dubai event when user confirms "yes" after asking about Dubai (not The Identity Switch)

16. **Fallback Mechanism for Unknown Topics** (Jan 2026):
    - **Problem**: Bot was extrapolating answers from loosely related info (e.g., "lifetime access to replays" → "pre-recorded sessions")
    - **Solution**: Strengthened LLM guidelines with NO EXTRAPOLATION rule
    - Key changes in `chatbot_engine.py` IMPORTANT GUIDELINES section:
      1. STRICT KNOWLEDGE BOUNDS - only answer if EXPLICITLY covered
      2. NO EXTRAPOLATION - don't infer from related but not matching info
      3. WHEN TO DECLINE - redirect to contact page for unknown topics
    - Updated `safety_guardrails.py` DON'T section and added HANDLING UNKNOWN TOPICS section
    - Bot now gracefully redirects: "I don't have specific information about that. Would you like me to help you connect with our team?"

## Important Technical Notes
- **Markdown Parsing Order**: Bold-wrapped links `**[text](url)**` must be matched FIRST, then plain links, then bold text.
- **Two Websites**: annakitney.com (marketing) and annakitneyportal.com (checkout, requires www. prefix)
- **VERBATIM Delimiters**: Used in chatbot_engine.py to prevent LLM from paraphrasing event data
- **Month Query Processing Order**: Month filter extraction MUST be checked before event keyword checks to handle follow-up queries like "What about in May?" that don't contain "event" keyword