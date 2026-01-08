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