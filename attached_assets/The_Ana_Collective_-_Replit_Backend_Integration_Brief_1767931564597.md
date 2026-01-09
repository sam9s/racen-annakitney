# The Ana Collective - Replit Backend Integration Brief

**This document explains the frontend landing page being built and what backend integration is needed from Replit.**

---

## PROJECT OVERVIEW

We are building **The Ana Collective** - a premium landing page for Ana Kitney that combines:
1. An information portal (left side)
2. A conversational chatbot (right side)

The **frontend landing page** is being built in Lovable (AI-powered UI builder).
The **backend chatbot** (already built by Replit) needs to be integrated into the landing page.

---

## LANDING PAGE STRUCTURE

### **Single Page Layout (Two Columns)**

```
┌─────────────────────────────────────────────────────────────┐
│                        HEADER                               │
│  Logo (Left) | Social Icons (Right)                         │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                     HERO SECTION                             │
│  Title + Subheading + Search Bar                            │
└─────────────────────────────────────────────────────────────┘

┌──────────────────────────┬──────────────────────────────────┐
│                          │                                  │
│   LEFT (40%)             │   RIGHT (60%)                    │
│   CONTENT                │   CHAT WINDOW                    │
│   (Scrollable)           │   (Scrollable)                   │
│                          │                                  │
│  - Featured Services     │   Chat Header                    │
│  - Tiny Calendar         │   Messages Area                  │
│  - About Ana             │   Input Field                    │
│  - Testimonials          │                                  │
│  - Blog Link             │                                  │
│                          │                                  │
└──────────────────────────┴──────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                       FOOTER                                │
│  Links | Social | Copyright                                │
└─────────────────────────────────────────────────────────────┘
```

---

## FRONTEND COMPONENTS (Lovable will build these)

### **Header**
- Ana Kitney logo (left)
- Social media icons (right)
- Fixed at top

### **Hero Section**
- Logo, heading, subheading
- Search bar
- CTA button

### **Left Column (40%) - Content**
1. **Featured Services Carousel** - Shows 3-4 featured services
2. **Tiny Calendar + Events** - Google Calendar widget + event list
3. **About Ana** - Bio section with photo
4. **Testimonials** - Client testimonial cards
5. **Blog Link** - Link to Ana's blog

### **Right Column (60%) - Chat Window**
- **Chat Header** - "The Ana Collective Assistant"
- **Messages Area** - Scrollable chat messages (bot and user)
- **Input Field** - Text input + Send button
- **Both independently scrollable**

### **Footer**
- Links, social icons, copyright

---


## SUMMARY

**Frontend (Lovable):**
- Builds beautiful landing page with chat UI
- Connects to Replit backend
- Displays messages in real-time
- Handles user input

**Backend (Replit):**
- Exposes WebSocket/API endpoint
- Processes user messages
- Generates responses
- Maintains conversation context

**Integration:**
- Frontend sends messages to backend
- Backend processes and responds
- Frontend displays responses
- Repeat for each message

**Result:**
- Premium landing page with working chatbot
- Ready for Ana to use
- Professional, luxury experience

---

**This brief explains everything Replit needs to know about the frontend and what backend integration is required.**
