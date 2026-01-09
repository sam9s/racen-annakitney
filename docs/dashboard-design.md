# Anna Kitney Wellness Chatbot - Admin Dashboard Design

## Overview
A comprehensive dashboard for administrators to monitor, manage, and control all aspects of the Anna Kitney wellness chatbot system.

---

## Dashboard Tabs & Features

### 1. Analytics Overview
- **Chat Volume**: Daily/weekly/monthly chat session counts
- **Peak Hours**: Heatmap showing busiest chat times
- **Response Time**: Average bot response latency
- **User Satisfaction**: Thumbs up/down feedback metrics (if implemented)
- **Conversion Tracking**: Users who clicked enrollment/event links

### 2. Chat Sessions & Transcripts
- **Session List**: Sortable table of all chat sessions
  - Session ID, Start Time, Duration, Message Count
  - Intent breakdown (EVENT, KNOWLEDGE, GREETING, etc.)
  - User location/timezone (if available)
- **Transcript Viewer**: 
  - Full conversation history for any session
  - Message timestamps
  - Intent classification for each message
  - Highlight safety triggers or escalations
- **Search & Filter**:
  - Search by keywords in messages
  - Filter by date range, intent type, event mentioned
  - Export to CSV/PDF

### 3. Events & Calendar Management
- **Event List**: View all synced calendar events
  - Title, Dates, Location, Status (Active/Inactive)
  - Event Page URL, Checkout URLs
  - Last sync timestamp
- **Edit Event URLs**: 
  - Inline editing for event_page_url, checkout_url, checkout_url_6month, checkout_url_12month, program_page_url
  - Changes persist through calendar syncs
- **Sync Controls**:
  - "Sync Now" button to trigger manual sync
  - Last sync timestamp display
  - Sync status indicator (success/error)
  - Enable/disable scheduled sync toggle
  - Sync interval configuration (currently 30 min)

### 4. Database Viewer
- **Tables Overview**: List of all database tables
- **Table Browser**: 
  - View records in paginated table format
  - Sort by any column
  - Filter/search within table
- **Record Editor**:
  - Add new records
  - Edit existing records (with validation)
  - Delete records (with confirmation)
- **Tables to include**:
  - calendar_events
  - conversations (chat history)
  - users (if applicable)

### 5. Knowledge Base Management
- **Document List**: All documents in ChromaDB
- **Ingest Status**: Last ingestion date, document count
- **Re-ingest Controls**: 
  - Trigger website scrape
  - Upload new documents
  - View ingestion logs

### 6. Safety & Security
- **Crisis Detection Log**: 
  - Messages that triggered crisis response
  - Timestamp, session ID, message content
  - Action taken (resources provided, etc.)
- **Blocked Content Log**:
  - Messages filtered for medical/mental health advice
  - PII detection events
- **Rate Limiting Stats**:
  - Requests per user/session
  - Rate limit violations
- **Security Alerts**:
  - Unusual activity patterns
  - Failed authentication attempts (if applicable)

### 7. Intent Classification Monitor
- **Intent Distribution**: Pie/bar chart of intent types
- **Classification Confidence**: Average confidence scores
- **Misclassification Review**:
  - Flag sessions for manual review
  - Correct intent labels for training
- **Pattern Performance**:
  - Which regex patterns are matching
  - Time-based queries accuracy

### 8. System Health
- **Service Status**:
  - Flask API health
  - Express server health
  - ChromaDB connection
  - PostgreSQL connection
  - Google Calendar API status
- **Logs Viewer**:
  - Real-time log stream
  - Filter by log level (INFO, WARN, ERROR)
  - Search logs
- **Performance Metrics**:
  - Memory usage
  - CPU usage
  - API response times

### 9. Settings & Configuration
- **Bot Personality**:
  - Greeting message preview/edit
  - Response tone settings
- **Calendar Sync Settings**:
  - Sync interval
  - Webhook configuration status
  - Calendar ID
- **Safety Settings**:
  - Crisis keywords list
  - Blocked topics list
  - Rate limit thresholds
- **Branding**:
  - Primary color
  - Bot name
  - Website URLs

---

## Technical Implementation Plan

### Phase 1: Core Infrastructure
1. Create `/admin` route with authentication
2. Set up dashboard layout with sidebar navigation
3. Implement session-based admin authentication

### Phase 2: Data Visualization
1. Analytics overview with charts (recharts library)
2. Chat session list with pagination
3. Transcript viewer component

### Phase 3: Event Management
1. Event list with inline editing
2. Sync controls and status display
3. URL validation before save

### Phase 4: Database Admin
1. Generic table browser component
2. Record CRUD operations
3. Validation and confirmation dialogs

### Phase 5: Security & Monitoring
1. Safety logs viewer
2. Real-time log streaming
3. System health indicators

---

## API Endpoints Needed

```
GET  /api/admin/stats               - Dashboard overview stats
GET  /api/admin/sessions            - List chat sessions
GET  /api/admin/sessions/:id        - Get session transcript
GET  /api/admin/events              - List events with URLs
PUT  /api/admin/events/:id          - Update event URLs
POST /api/admin/sync/trigger        - Manual calendar sync
GET  /api/admin/sync/status         - Sync status
GET  /api/admin/tables              - List database tables
GET  /api/admin/tables/:name        - Get table records
PUT  /api/admin/tables/:name/:id    - Update record
POST /api/admin/tables/:name        - Create record
DELETE /api/admin/tables/:name/:id  - Delete record
GET  /api/admin/safety/logs         - Safety trigger logs
GET  /api/admin/health              - System health check
GET  /api/admin/logs                - Application logs
```

---

## Access Control

- Dashboard accessible at `/admin` or `/dashboard`
- Protected by admin authentication (consider Replit Auth or custom)
- Role-based access if multiple admins needed
- Audit log for admin actions

---

## UI/UX Considerations

- Dark/light mode support
- Responsive design for tablet/desktop
- Keyboard shortcuts for power users
- Export functionality for reports
- Real-time updates where applicable (WebSocket)

---

## Priority Order for Implementation

1. **High Priority**:
   - Event URL management (immediate need)
   - Sync controls
   - Chat transcript viewer

2. **Medium Priority**:
   - Analytics overview
   - Safety logs
   - Database viewer

3. **Lower Priority**:
   - System health monitoring
   - Knowledge base management
   - Advanced settings

---

## Notes

- Existing sync interval: 30 minutes
- Sync preserves manually set URLs (fixed Jan 2026)
- Calendar events stored in PostgreSQL `calendar_events` table
- Chat history stored in PostgreSQL via `events_service.py`

---

*Last Updated: January 2026*
*Status: Planning Phase - To be implemented after initial deployment*
