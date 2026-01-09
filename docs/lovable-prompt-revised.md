# The Ana Collective - Revised Lovable Prompt

## Changes Made from Original

1. **Chat window is now an EMBED PLACEHOLDER** - Lovable creates the container, but the actual chat is embedded via iframe from our deployed Replit app
2. **Calendar widget fetches from API** - Instead of direct Google Calendar integration, it fetches from our `/api/public/events` endpoint
3. **Search bar removed from hero** - Moved functionality to chatbot (ask the bot instead)
4. **Clarified static vs dynamic content** - Services/testimonials are hardcoded; calendar/chat are dynamic

---

## REVISED PROMPT FOR LOVABLE

```
You are creating a premium, luxury landing page for "The Ana Collective" - 
an information portal for Anna Kitney, a spiritual advisor and legacy mentor 
to visionary female founders.

PROJECT OVERVIEW:
- Single landing page (not a multi-page website)
- Two-column layout: Content (40% left) + Chat Embed (60% right)
- Chat window is an IFRAME EMBED from external URL (not built by Lovable)
- Target audience: Visionary, purpose-driven women entrepreneurs
- Brand: Luxury, spiritual, strategic, elegant

DESIGN AESTHETIC: (take reference from https://www.annakitney.com/)
- Color palette: Gold (#D4AF37), Cream (#F5F1E8), White (#FFFFFF), Dark Gray (#2C2C2C)
- Typography: Elegant serif fonts for headings, clean sans-serif for body
- Style: Premium, luxury, sophisticated, spiritual
- Tone: Empowering, transformational, exclusive but welcoming
- No clutter: Clean, spacious, breathing room between sections

HEADER (Fixed at Top):
- Left: Anna Kitney logo (golden wings, 40px height)
- Right: Social media icons (Facebook, Instagram, LinkedIn, Pinterest, YouTube)
- Background: White/cream with subtle shadow
- Height: 60-70px
- Logo clickable (returns to top)
- Social icons link to Anna's profiles:
  - Facebook: https://www.facebook.com/anna.kitney
  - Instagram: https://www.instagram.com/annakitney/
  - LinkedIn: https://www.linkedin.com/in/annakitney/
  - Pinterest: https://www.pinterest.com/annakitney/
  - YouTube: https://www.youtube.com/@annakitney

HERO SECTION:
- Full width, centered content
- Background: Subtle gradient (cream to white)
- Content (top to bottom):
  1. Anna Kitney logo (centered, 60px height)
  2. Main heading: "The Ana Collective" (large, elegant serif, gold color, 48px)
  3. Subheading: "Your Portal to Purpose-Driven Prosperity" (elegant serif, 24px, dark gray)
  4. CTA: "Start a Conversation" button (gold background, white text, scrolls to chat section)
- Height: 300-350px
- NO search bar in hero

MAIN LAYOUT (Two Columns):

LEFT COLUMN (40%) - CONTENT SECTIONS (Scrollable):

SECTION 1 - FEATURED SERVICES (350px):
- Heading: "Our Offerings"
- Display as card grid (2 columns, 2 rows)
- 4 service cards (STATIC CONTENT - hardcoded):

Card 1: Elite Private Coaching
- Description: "Personalized 1:1 mentorship for high-achieving founders ready to create their legacy."
- Link: "Learn More" → https://www.annakitney.com/coaching/

Card 2: VIP Immersion Days
- Description: "Intensive strategy sessions designed to accelerate your transformation."
- Link: "Learn More" → https://www.annakitney.com/vip-days/

Card 3: SoulAlign Business
- Description: "Build a soul-aligned empire with strategic spiritual guidance."
- Link: "Learn More" → https://www.annakitney.com/soulalign-business/

Card 4: The ASCEND Collective
- Description: "Join an exclusive community of visionary female founders."
- Link: "Learn More" → https://www.annakitney.com/ascend/

- Card design: Cream background, gold border on hover, rounded corners (8px)

SECTION 2 - UPCOMING EVENTS (350px):
- Heading: "Upcoming Events"
- Display as simple list (NOT a calendar widget)
- PLACEHOLDER: This section will be populated dynamically from API
- For now, create a placeholder with sample events:

Event 1:
- Date: "Jan 17, 2026"
- Title: "The Identity Overflow"
- Location: "Dubai, UAE"
- Button: "Learn More" (gold outline button)

Event 2:
- Date: "Jan 23 - Apr 17, 2026"
- Title: "SoulAlign Manifestation Mastery"
- Location: "Online"
- Button: "Learn More" (gold outline button)

Event 3:
- Date: "Mar 14, 2026"
- Title: "Success Redefined: The Meditation"
- Location: "Dubai, UAE"
- Button: "Learn More" (gold outline button)

- Include comment in code: "// TODO: Replace with API fetch from /api/public/events"
- Design: Clean list with gold date badges, clear hierarchy

SECTION 3 - ABOUT ANNA (300px):
- Heading: "Meet Anna Kitney"
- Layout: Professional photo (left, 40%) + Bio text (right, 60%)
- Photo placeholder: Use a professional headshot placeholder
- Bio text (HARDCODED):
  "Anna Kitney is a spiritual advisor and legacy mentor to visionary female founders. 
   With over two decades of experience in transformational leadership, she guides 
   purpose-driven entrepreneurs to build soul-aligned empires that create lasting impact.
   
   Her unique approach combines spiritual wisdom with strategic business acumen, 
   helping her clients achieve what she calls 'God-level success' - prosperity that 
   honors both their purpose and their profit."
- CTA: "Read Full Story" → https://www.annakitney.com/about/

SECTION 4 - TESTIMONIALS (300px):
- Heading: "What Our Community Says"
- 3 testimonial cards in horizontal row
- HARDCODED content:

Testimonial 1:
- Quote: "Working with Anna transformed not just my business, but my entire perspective on success."
- Name: "Sarah M."
- Role: "Founder & CEO"

Testimonial 2:
- Quote: "The soulALIGN methodology helped me build a 7-figure business that feels authentic to who I am."
- Name: "Jessica L."
- Role: "Serial Entrepreneur"

Testimonial 3:
- Quote: "Anna's guidance helped me step into my power as a leader and legacy builder."
- Name: "Michelle K."
- Role: "Business Coach"

- Card design: Cream background, gold left border (4px), italic quotes

SECTION 5 - BLOG LINK (150px):
- Heading: "Latest Insights"
- Description: "Discover insights on spiritual leadership, feminine entrepreneurship, and legacy building."
- CTA Button: "Visit Blog" → https://www.annakitney.com/blog/
- Simple, elegant design

---

RIGHT COLUMN (60%) - CHAT EMBED:

CRITICAL: This is NOT a chat component built by Lovable.
This is an IFRAME that embeds an external chat application.

Structure:
- Container div with id="chat-container"
- Full height of viewport (minus header/footer)
- Contains single iframe element

Iframe configuration:
- src: "https://REPLIT_APP_URL_HERE" (placeholder - will be replaced after deployment)
- width: 100%
- height: 100%
- border: none
- border-radius: 12px
- background: #F5F1E8

Container styling:
- Background: Cream (#F5F1E8)
- Padding: 20px
- Position: sticky (stays in viewport on desktop)
- Top: 80px (below header)
- Height: calc(100vh - 160px)

Include comment in code:
// INTEGRATION NOTE: Replace iframe src with deployed Replit app URL
// Example: src="https://anna-kitney-chatbot.replit.app"
// The iframe will display the full chatbot interface

---

FOOTER:
- Full width, centered content
- Background: Dark gray (#2C2C2C)
- Content:
  - Links: Privacy Policy | Terms & Conditions | Contact
  - Social icons (same as header)
  - Copyright: "© 2025 Anna Kitney International L.L.C-FZ. Dubai, UAE."
- Text color: Light gray (#CCCCCC)
- Height: 100px

---

RESPONSIVE DESIGN:

Desktop (> 1024px):
- Two-column layout (40/60)
- Chat iframe sticky on right

Tablet (768px - 1024px):
- Stack columns vertically
- Content first, then chat
- Chat height: 500px

Mobile (< 768px):
- Full width single column
- Content sections stack
- Chat section at bottom with "Chat with Anna" button that expands to full screen

---

IMPORTANT IMPLEMENTATION NOTES:

1. The chat is an IFRAME EMBED - do NOT build chat components
2. Events section is a PLACEHOLDER - will be replaced with API data
3. All "Learn More" links should open in new tab (target="_blank")
4. Use CSS custom properties for colors (easy to update)
5. Include data-testid attributes on interactive elements
6. Ensure all images have alt text
7. Use semantic HTML (header, main, section, footer)

---

DELIVERABLE:
- Single React page with TypeScript
- Two-column layout with iframe chat placeholder
- All content sections with hardcoded data
- Ready for backend integration
- Clean, production-ready code
- Premium, luxury aesthetic
```

---

## WHAT REPLIT WILL PROVIDE

After Lovable generates the page, I (Replit) will:

1. **Deploy the chatbot** → Get public URL (e.g., https://anna-kitney-chatbot.replit.app)
2. **Update iframe src** → Replace placeholder with actual URL
3. **Create /api/public/events endpoint** → For dynamic event listing
4. **Provide event fetching code** → JavaScript to populate events section

---

## INTEGRATION CODE (For Later)

### Events Section - Dynamic Loading

```javascript
// Add this to the Events section component
useEffect(() => {
  fetch('https://anna-kitney-chatbot.replit.app/api/public/events')
    .then(res => res.json())
    .then(data => setEvents(data.events))
    .catch(err => console.error('Failed to load events:', err));
}, []);
```

### Chat Iframe - Already Configured

The iframe src will be:
```
https://anna-kitney-chatbot.replit.app
```

This displays the full chat interface, handling all:
- Message sending/receiving
- Session management
- Markdown rendering
- Navigation commands
- Safety features

---

## NEXT STEPS

1. **Give revised prompt to Lovable** → Generate landing page
2. **Review output** → Adjust styling if needed
3. **Deploy Replit chatbot** → Get public URL
4. **Update iframe src** → Connect chat
5. **Create public events API** → For dynamic events
6. **Test end-to-end** → Verify everything works
7. **Go live** → Launch The Ana Collective
