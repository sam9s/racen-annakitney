# The Anna Collective - Lovable Prompt (FINAL VERSION)

**INSTRUCTIONS: Copy EVERYTHING below this line and paste into Lovable.**

---

You are creating a premium, luxury landing page for "The Anna Collective" - an information portal for Anna Kitney, a spiritual advisor and legacy mentor to visionary female founders.

PROJECT OVERVIEW:
- Single landing page (not a multi-page website)
- Two-column layout: Content (40% left) + Chat Embed (60% right)
- Chat window is an IFRAME EMBED from external URL (not built by Lovable)
- Hero search bar sends queries to the chatbot (scroll + auto-send)
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
  2. Main heading: "The Anna Collective" (large, elegant serif, gold color, 48px)
  3. Subheading: "Your Portal to Purpose-Driven Prosperity" (elegant serif, 24px, dark gray)
  4. SMART SEARCH BAR (see behavior below)
  5. "Explore The Collective" button (gold background, white text, scrolls to content)
- Height: 350-400px

SMART SEARCH BAR BEHAVIOR:
- Wide search input (centered, rounded, placeholder: "Ask about programs, events, coaching...")
- Gold "Ask Anna" button on right side of search bar
- When user types and clicks "Ask Anna" or presses Enter:
  1. Page smoothly scrolls down to the chat section (right column)
  2. The search query is automatically inserted into the chat input field
  3. The message is automatically sent to the chatbot
  4. Bot responds with relevant information
- This creates a seamless "search to chat" experience
- Include JavaScript to handle this behavior:

```javascript
// Search bar submit handler
function handleSearchSubmit(query) {
  // 1. Scroll to chat section
  document.getElementById('chat-container').scrollIntoView({ behavior: 'smooth' });
  
  // 2. Post message to iframe to send the query
  const chatIframe = document.getElementById('chat-iframe');
  chatIframe.contentWindow.postMessage({ type: 'sendMessage', message: query }, '*');
}
```

Note: The iframe will listen for this postMessage and auto-send the query.

MAIN LAYOUT (Two Columns):

LEFT COLUMN (40%) - CONTENT SECTIONS (Scrollable):

SECTION 1 - FEATURED SERVICES CAROUSEL (350-400px):
- Heading: "Our Offerings"
- CAROUSEL with 4 featured services (not a grid)
- Auto-rotate every 5 seconds OR manual navigation with arrows
- Previous/Next arrows on left and right sides
- Slide indicator dots at bottom
- Smooth slide transitions (0.3s ease)
- Each slide shows:
  - Service image placeholder (high-quality, professional)
  - Service title (bold, serif, 20px)
  - Brief description (2-3 lines, sans-serif, 14px)
  - "Learn More" link (gold color, hover underline)
- Hover effect: Slight lift, shadow increase

CAROUSEL SLIDES (4 services):

Slide 1: Elite Private Coaching
- Description: "Personalized 1:1 mentorship for high-achieving founders ready to create their legacy."
- Link: "Learn More" → https://www.annakitney.com/elite-private-coaching/

Slide 2: VIP Immersion Days
- Description: "Intensive strategy sessions designed to accelerate your transformation."
- Link: "Learn More" → https://www.annakitney.com/vip-day/

Slide 3: SoulAlign Business
- Description: "Build a soul-aligned empire with strategic spiritual guidance."
- Link: "Learn More" → https://www.annakitney.com/soul-align-business-course/

Slide 4: The ASCEND Collective
- Description: "Join an exclusive community of visionary female founders."
- Link: "Learn More" → https://www.annakitney.com/the-ascend-collective/

- Carousel design: Cream background card, gold border on hover, rounded corners (8px)

SECTION 2 - UPCOMING EVENTS WITH MINI CALENDAR (400-450px):
- Heading: "Upcoming Events"
- TWO-PART LAYOUT:
  
Part A - Mini Calendar Widget (top):
- Compact monthly calendar view
- Current month displayed with month/year header
- Previous/Next month arrows
- Days with events highlighted with gold dots or gold background
- Clickable dates - clicking a date with an event scrolls to that event in the list below
- Elegant, minimal design matching brand colors
- Calendar grid: 7 columns (Sun-Sat), 5-6 rows

Part B - Event List (below calendar):
- List of upcoming events with details
- Each event card shows:
  - Date badge (gold background, white text)
  - Event title (bold, serif)
  - Location (regular, muted text)
  - "Learn More" button (gold outline)
- Maximum 5 events displayed
- Scrollable if more than 5

SAMPLE EVENTS (will be replaced with API data):

Event 1:
- Date: "Jan 17, 2026"
- Title: "The Identity Overflow"
- Location: "Dubai, UAE"
- Button: "Learn More"

Event 2:
- Date: "Jan 23 - Apr 17, 2026"
- Title: "SoulAlign Manifestation Mastery"
- Location: "Online"
- Button: "Learn More"

Event 3:
- Date: "Mar 14, 2026"
- Title: "Success Redefined: The Meditation"
- Location: "Dubai, UAE"
- Button: "Learn More"

- Include comment in code: "// TODO: Fetch events from https://anna--ravensolutions.replit.app/api/public/events"

SECTION 3 - ABOUT ANNA (300px):
- Heading: "Meet Anna Kitney"
- Layout: Professional photo (left, 40%) + Bio text (right, 60%)
- Photo placeholder: Use a professional headshot placeholder
- Bio text:
  "Anna Kitney is a spiritual advisor and legacy mentor to visionary female founders. With over two decades of experience in transformational leadership, she guides purpose-driven entrepreneurs to build soul-aligned empires that create lasting impact.
   
   Her unique approach combines spiritual wisdom with strategic business acumen, helping her clients achieve what she calls 'God-level success' - prosperity that honors both their purpose and their profit."
- CTA: "Read Full Story" → https://www.annakitney.com/about/

SECTION 4 - TESTIMONIALS (300-350px):
- Heading: "What Our Community Says"
- 3 testimonial cards in horizontal row (or stacked on mobile)
- REAL TESTIMONIALS from Anna's clients:

Testimonial 1:
- Quote: "Within 60 seconds, Anna identified a core wound holding me back. Within 30 minutes, it was cleared. Within 24 hours, I had a different view of the world and made decisions differently. Anna is the real deal."
- Name: "Kelly O'Neal"
- Role: "7-Figure Positioning & Profit Strategist"

Testimonial 2:
- Quote: "I sold my first $12,000 package to a private client, launched a group program and made $14,000, and quit my hairdressing job. I'm now working toward my $250,000 revenue goal."
- Name: "Claire Gorman"
- Role: "Entrepreneur"

Testimonial 3:
- Quote: "I hit a $10K month - the fastest goal-reaching I've ever experienced. Anna's strategies gave my business the exact infusion it needed. I'm now attracting soul-aligned clients with phenomenal results."
- Name: "Amelia Critchlow"
- Role: "Business Owner"

- Card design: Cream background, gold left border (4px), italic quotes, rounded corners (8px)
- Include comment: "// TODO: Can be made dynamic via API in future"

SECTION 5 - BLOG LINK (150px):
- Heading: "Latest Insights"
- Description: "Discover insights on spiritual leadership, feminine entrepreneurship, and legacy building."
- CTA Button: "Visit Blog" → https://www.annakitney.com/blog/
- Simple, elegant design

RIGHT COLUMN (60%) - CHAT EMBED:

CRITICAL: This is NOT a chat component built by Lovable.
This is an IFRAME that embeds an external chat application.

Structure:
- Container div with id="chat-container"
- Full height of viewport (minus header/footer)
- Contains single iframe element with id="chat-iframe"

Iframe configuration:
- id: "chat-iframe"
- src: "https://anna--ravensolutions.replit.app"
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

FOOTER:
- Full width, centered content
- Background: Dark gray (#2C2C2C)
- Content:
  - Links: Privacy Policy | Terms & Conditions | Contact
  - Social icons (same as header)
  - Copyright: "© 2025 Anna Kitney International L.L.C-FZ. Dubai, UAE."
- Text color: Light gray (#CCCCCC)
- Height: 100px

RESPONSIVE DESIGN:

Desktop (> 1024px):
- Two-column layout (40/60)
- Chat iframe sticky on right
- Services carousel shows 1 item at a time
- Testimonials in horizontal row

Tablet (768px - 1024px):
- Stack columns vertically
- Content first, then chat
- Chat height: 500px
- Testimonials in horizontal row (smaller cards)

Mobile (< 768px):
- Full width single column
- Content sections stack
- Carousel works with swipe gestures
- Testimonials stack vertically
- Mini calendar becomes more compact
- Chat section at bottom with "Chat with Anna" button that expands to full screen

IMPORTANT IMPLEMENTATION NOTES:

1. The chat is an IFRAME EMBED - do NOT build chat components
2. Events section will be populated from API (placeholder data for now)
3. All "Learn More" links should open in new tab (target="_blank")
4. Use CSS custom properties for colors (easy to update)
5. Include data-testid attributes on interactive elements
6. Ensure all images have alt text
7. Use semantic HTML (header, main, section, footer)
8. Search bar must trigger scroll + postMessage to iframe
9. Carousel should have smooth transitions and auto-rotate
10. Mini calendar should highlight dates with events using gold color

DELIVERABLE:
- Single React page with TypeScript
- Two-column layout with iframe chat placeholder
- Smart search bar that sends queries to chat
- Services carousel with 4 slides
- Mini calendar widget with event list
- Real testimonials from Anna's clients
- All content sections styled per brand guidelines
- Ready for backend integration
- Clean, production-ready code
- Premium, luxury aesthetic
