# New Client Chatbot Replication Guide

## Overview

This document provides comprehensive instructions for replicating the JoveHeal conversational AI chatbot for a new client. The new Replit agent working on this project MUST read this entire document before making any changes.

**Original Project:** JoveHeal Wellness Chatbot (Jovee/RACEN)
**New Client:** Anna Kitney (https://www.annakitney.com/)
**Goal:** Create a POC (Proof of Concept) RAG-based conversational chatbot for Anna's wellness/coaching business

---

## CRITICAL: READ THIS FIRST

### The Golden Rules

1. **FRESH DATABASE** - You MUST use a completely new PostgreSQL database. NEVER connect to JoveHeal's database.
2. **FRESH KNOWLEDGE BASE** - Delete the entire `chroma_db/` folder and rebuild from Anna's content only.
3. **NO SHARED SESSIONS** - Use a unique session ID prefix for this client (e.g., `anna_` instead of `jovee_` or `widget_`).
4. **REMOVE BEFORE ADDING** - Remove all JoveHeal-specific code/content BEFORE adding Anna's content.
5. **TEST IN ISOLATION** - Never test against JoveHeal's endpoints or databases.

### Past Mistakes to NEVER Repeat

When we replicated JoveHeal for other clients (GREST, Nature Mania), we encountered these issues:

| Mistake | Consequence | Prevention |
|---------|-------------|------------|
| Shared database | Client data mixed together, wrong responses | Create fresh PostgreSQL database immediately |
| Reused ChromaDB | Old client's content in new client's responses | Delete `chroma_db/` folder completely before ingestion |
| Forgot to update prompts | Bot introduced itself as "Jovee" for wrong client | Search and replace ALL brand mentions in ALL files |
| Kept old session prefix | Analytics mixed between clients | Update session ID prefix in widget.js and backend |
| Left old integrations | Twilio/VAPI tried to connect to old accounts | Remove all integration code not needed |

---

## Architecture Overview

### What This Chatbot Does

The chatbot is a RAG (Retrieval Augmented Generation) system that:
1. Ingests website content and documents into a vector database (ChromaDB)
2. When users ask questions, it retrieves relevant content from the knowledge base
3. Uses OpenAI GPT to generate contextual responses based on retrieved content
4. Provides safety guardrails for sensitive topics

### Core Components to KEEP

| File | Purpose | Modifications Needed |
|------|---------|---------------------|
| `chatbot_engine.py` | Main RAG logic, system prompts | Update system prompts with Anna's branding |
| `safety_guardrails.py` | Safety filters, response formatting | Update program links, crisis resources |
| `webhook_server.py` | Flask API backend | Simplify - remove unused endpoints |
| `public/widget.js` | Embeddable chat widget | Update branding, colors, allowed domains |
| `ingest_website.py` | Website content ingestion | Update target URLs |
| `ingest_documents.py` | PDF/document ingestion | No changes needed |
| `src/app/page.tsx` | Main frontend page | Update branding |
| `src/app/api/chat/stream/route.ts` | Chat API route | Minimal changes |
| `src/components/ChatMessage.tsx` | Message rendering | Update styling if needed |

### Components to REMOVE (Do NOT Import or Delete After Import)

| File/Folder | Reason |
|-------------|--------|
| `somera_engine.py` | SOMERA coaching assistant - not needed |
| `readiness_scoring.py` | SOMERA-specific scoring |
| `somera_admin.py` | SOMERA admin dashboard |
| `src/app/somera/` | Entire SOMERA frontend |
| `docs/SOMERA_*.md` | SOMERA documentation |
| `vapi_*.py` files | VAPI voice integration |
| `twilio_*.py` files | WhatsApp integration |
| `instagram_*.py` files | Instagram integration |
| `transcripts/` | JoveHeal's transcription files |
| `knowledge_base/` | JoveHeal's documents (replace with Anna's) |
| `chroma_db/` | JoveHeal's vector database (must rebuild) |
| `.env` or secrets | JoveHeal's API keys (use new ones) |

### Database Tables

The PostgreSQL database has these tables. You need a FRESH database:

| Table | Purpose | Action |
|-------|---------|--------|
| `conversations` | Chat history | Fresh table - do not migrate |
| `users` | User accounts | Fresh table if using auth |
| `feedback` | User feedback | Fresh table |
| `analytics` | Usage analytics | Fresh table |

---

## Step-by-Step Implementation Guide

### Phase 1: Initial Setup (Do This First)

#### Step 1.1: Create Fresh PostgreSQL Database
```
1. In Replit, go to the Database tab
2. Create a new PostgreSQL database
3. Note the new DATABASE_URL
4. NEVER use environment variables from JoveHeal
```

#### Step 1.2: Delete JoveHeal's Knowledge Base
```bash
# Delete the entire ChromaDB folder
rm -rf chroma_db/

# Delete JoveHeal's documents
rm -rf knowledge_base/*
```

#### Step 1.3: Remove Unnecessary Files
Delete these files/folders:
- `somera_engine.py`
- `readiness_scoring.py`
- `somera_admin.py`
- `src/app/somera/` (entire folder)
- `docs/SOMERA_*.md`
- Any `vapi_*.py` files
- Any `twilio_*.py` files
- Any `instagram_*.py` files
- `transcripts/` folder contents

#### Step 1.4: Set Up New Environment Variables
Required secrets (request from client or create new):
- `OPENAI_API_KEY` - New OpenAI API key for Anna's account
- `DATABASE_URL` - Auto-generated by Replit PostgreSQL
- `PGHOST`, `PGUSER`, `PGPASSWORD`, `PGDATABASE` - Auto-generated

Optional (remove if not using):
- `VAPI_*` keys - Remove entirely
- `TWILIO_*` keys - Remove entirely
- `DEEPGRAM_*` keys - Remove entirely
- `ELEVENLABS_*` keys - Remove entirely

---

### Phase 2: Branding Updates

#### Step 2.1: Update System Prompts in `chatbot_engine.py`

Find the system prompt section and replace ALL JoveHeal references:

**Search for and replace:**
- "Jovee" → "[Anna's Bot Name]"
- "RACEN" → "[Anna's Bot Name]"
- "JoveHeal" → "Anna Kitney" or her business name
- "Shweta" → "Anna" (or remove if not applicable)
- All JoveHeal program names → Anna's program names
- JoveHeal URLs → Anna's URLs

**Example system prompt structure for Anna:**
```python
SYSTEM_PROMPT = """You are [Bot Name], a friendly and knowledgeable assistant for Anna Kitney's wellness practice.

Your role is to:
- Answer questions about Anna's programs and services
- Provide helpful information from the knowledge base
- Guide visitors to appropriate resources on the website

About Anna Kitney:
[Add brief description of Anna's business, philosophy, approach]

Programs/Services offered:
[List Anna's actual programs from her website]

Important guidelines:
- Always be warm, supportive, and professional
- Do not provide medical or psychological advice
- For specific inquiries, direct users to contact Anna directly
- When mentioning programs, provide accurate information from the knowledge base
"""
```

#### Step 2.2: Update `public/widget.js`

**Update these sections:**

1. **Bot name and description** (around line 498-501):
```javascript
<h3>[Anna's Bot Name]</h3>
<p>Your [Anna Kitney] Guide</p>
```

2. **Welcome message** (around line 510-513):
```javascript
<h4>Hi, I'm [Bot Name]</h4>
<p>[Welcome message for Anna's visitors]</p>
```

3. **Powered by text** (around line 525-527):
```javascript
Powered by <a href="https://www.annakitney.com" target="_blank">Anna Kitney</a>
```

4. **Allowed navigation domains** (around line 678-682):
```javascript
var ALLOWED_NAVIGATION_DOMAINS = [
  'annakitney.com',
  'www.annakitney.com'
  // Add any other domains Anna uses
];
```

5. **Session ID prefix** (around line 543):
```javascript
return 'anna_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
```

6. **Colors** (optional - update primary color):
```javascript
primaryColor: '#[Anna's brand color]',
```

#### Step 2.3: Update `safety_guardrails.py`

1. **Update program links dictionary** - Replace all JoveHeal URLs with Anna's URLs
2. **Update crisis resources** - Keep general crisis resources, update any specific ones
3. **Update any hardcoded brand mentions**

#### Step 2.4: Update Frontend Files

**`src/app/page.tsx`:**
- Update page title
- Update any hardcoded branding
- Update meta tags

**`src/app/layout.tsx`:**
- Update site title
- Update meta description
- Update favicon if provided

---

### Phase 3: Knowledge Base Setup

#### Step 3.1: Ingest Anna's Website Content

1. Update `ingest_website.py` with Anna's URLs:
```python
URLS_TO_INGEST = [
    "https://www.annakitney.com/",
    "https://www.annakitney.com/about",
    "https://www.annakitney.com/services",
    "https://www.annakitney.com/programs",
    # Add all relevant pages
]
```

2. Run the ingestion:
```bash
python ingest_website.py
```

#### Step 3.2: Ingest Any Documents (if provided)

1. Place Anna's PDFs/documents in `knowledge_base/` folder
2. Run document ingestion:
```bash
python ingest_documents.py
```

#### Step 3.3: Verify Knowledge Base

Test with sample questions about Anna's business to ensure:
- Responses reference Anna's programs correctly
- No JoveHeal content appears
- Links point to Anna's website

---

### Phase 4: Testing Checklist

Before considering the chatbot ready, verify ALL of these:

#### Branding Checks
- [ ] Bot introduces itself with Anna's bot name (not Jovee)
- [ ] No "JoveHeal" or "Shweta" mentions appear in responses
- [ ] All links point to annakitney.com domains
- [ ] Widget displays Anna's branding
- [ ] Colors match Anna's brand (if specified)

#### Functionality Checks
- [ ] Chat responses are relevant to Anna's business
- [ ] Knowledge base returns Anna's content only
- [ ] Safety guardrails work correctly
- [ ] Widget opens and closes properly
- [ ] Messages send and receive correctly
- [ ] Streaming responses work
- [ ] Mobile responsive design works

#### Data Isolation Checks
- [ ] Database is fresh (no JoveHeal conversations)
- [ ] ChromaDB only contains Anna's content
- [ ] Session IDs use new prefix
- [ ] No cross-contamination with other clients

---

## Common Issues and Solutions

### Issue: Bot still mentions "Jovee" or "JoveHeal"
**Solution:** 
1. Search entire codebase: `grep -r "Jovee" .` and `grep -r "JoveHeal" .`
2. Check system prompts in `chatbot_engine.py`
3. Check welcome messages in `widget.js`
4. Clear browser cache and test again

### Issue: Wrong content in responses
**Solution:**
1. Delete `chroma_db/` folder completely
2. Re-run ingestion with only Anna's content
3. Verify no old documents in `knowledge_base/`

### Issue: Database errors
**Solution:**
1. Verify new PostgreSQL database is created
2. Check DATABASE_URL environment variable
3. Run database migrations if needed
4. Never connect to JoveHeal's database

### Issue: Widget not loading on external site
**Solution:**
1. Check CORS settings in webhook_server.py
2. Add Anna's domain to allowed origins
3. Verify widget.js is accessible from Anna's domain

---

## Files Reference: What Each File Does

### Backend Files

| File | Description |
|------|-------------|
| `chatbot_engine.py` | Core RAG logic, system prompts, generates responses |
| `safety_guardrails.py` | Filters responses for safety, formats output |
| `webhook_server.py` | Flask API server, handles chat requests |
| `ingest_website.py` | Scrapes and ingests website content |
| `ingest_documents.py` | Ingests PDF/text documents |
| `database.py` | Database connection and ORM models |

### Frontend Files

| File | Description |
|------|-------------|
| `src/app/page.tsx` | Main chat page |
| `src/app/api/chat/stream/route.ts` | API route for streaming chat |
| `src/components/ChatMessage.tsx` | Renders chat messages |
| `public/widget.js` | Embeddable widget (SEPARATE from React app) |

### Configuration Files

| File | Description |
|------|-------------|
| `.replit` | Replit configuration |
| `package.json` | Node.js dependencies |
| `requirements.txt` | Python dependencies |
| `next.config.js` | Next.js configuration |

---

## IMPORTANT: Widget vs Main App Architecture

**This is critical to understand:**

The system has TWO separate rendering paths:

1. **Main App** (`src/components/ChatMessage.tsx`)
   - Used when users visit the Next.js app directly
   - React component with full rendering capabilities
   
2. **Widget** (`public/widget.js`)
   - Used when embedded on external websites (like Anna's Kajabi site)
   - Standalone JavaScript, does NOT use React
   - Has its own `createSafeContent()` function for rendering
   - Must be updated SEPARATELY from ChatMessage.tsx

**If you make formatting changes:**
- Changes to `ChatMessage.tsx` only affect the main app
- Changes to `widget.js` only affect the embedded widget
- You must update BOTH if you want consistent formatting everywhere

---

## Final Checklist Before Handoff

- [ ] All JoveHeal branding removed
- [ ] Anna's branding applied everywhere
- [ ] Fresh database created and connected
- [ ] Fresh ChromaDB with Anna's content only
- [ ] All unnecessary integrations removed
- [ ] Widget tested on external domain
- [ ] Mobile responsiveness verified
- [ ] Safety guardrails tested
- [ ] No console errors in browser
- [ ] No errors in server logs

---

## Contact and Support

If you encounter issues not covered in this guide:
1. Check the original JoveHeal codebase for reference (but don't copy JoveHeal-specific content)
2. Review the existing documentation in `docs/` folder
3. Test thoroughly before deploying

---

*Document created: January 2026*
*Original project: JoveHeal Wellness Chatbot*
*Purpose: Guide for replicating chatbot for new clients*
