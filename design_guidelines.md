# Admin Dashboard Design Guidelines - Anna Kitney Wellness Chatbot

## Design Approach
**Hybrid System**: Linear/Notion-inspired admin aesthetic with Anna Kitney's luxe wellness brand personality. Clean, data-focused layouts elevated with sophisticated brand touches.

## Typography System
**Primary Font**: Inter or DM Sans (Google Fonts) - exceptional readability for data
**Accent Font**: Cormorant Garamond or Playfair Display - elegant serif for headers

**Hierarchy**:
- Page Headers: Accent serif, 32px, medium weight
- Section Titles: Sans-serif, 20px, semibold
- Data Labels: Sans-serif, 14px, medium
- Body Text: Sans-serif, 15px, regular
- Table Headers: Sans-serif, 13px, uppercase, semibold, letter-spacing
- Metrics/Numbers: Sans-serif, tabular-nums

## Layout System
**Spacing Primitives**: Tailwind units of 2, 4, 6, 8 (p-2, gap-4, mb-6, py-8)

**Container Structure**:
- Fixed sidebar: 280px width
- Main content: max-w-7xl with px-8 padding
- Card containers: p-6 to p-8
- Tight data sections: p-4

## Component Architecture

### Sidebar Navigation
Left-aligned, full-height, cream background with subtle gold accents
- Logo zone at top with brand icon
- Navigation groups with dividers
- Active state: gold border-left indicator (4px)
- Icons: Heroicons (outline style)
- Bottom section: user profile card

### Dashboard Grid Layout
3-column metric cards at top (grid-cols-3), then 2-column split for main content (grid-cols-2 lg:grid-cols-3)
- Metric Cards: Large numbers (36px), descriptive labels below, subtle gold accent borders
- Session Analytics: Line/area charts with cream/gold gradient fills
- Recent Activity Feed: Timeline-style list with gold connection lines

### Data Tables (Session Lists)
Clean table design with sophisticated styling:
- Header row: cream background, gold bottom border (2px)
- Alternating row backgrounds (white/cream-50)
- Hover state: subtle gold glow
- Row height: py-4 for breathing room
- Right-aligned action buttons (icon-only)
- Pagination: gold accent for active page
- Search/filter bar above table with subtle gold focus rings

### Conversation Transcript Viewer
Two-pane modal/drawer design:
- Left pane (320px): Session metadata card with user info, timestamp, session stats
- Right pane: Chat transcript with message bubbles
  - User messages: white background, align-right
  - Bot messages: cream background, align-left
  - Timestamps: subtle, 12px, between message groups
  - Smooth scroll with gold scrollbar track

### Cards & Containers
All data containers use soft shadows (shadow-sm to shadow-md), rounded-xl borders
- White backgrounds for content cards
- Cream backgrounds for sidebar/secondary areas
- Gold accent borders (1px) for focused/important cards
- Generous padding (p-6 to p-8)

### Form Elements & Inputs
Refined input styling:
- Border: 1.5px, transitions to gold on focus
- Height: h-11 for text inputs
- Rounded: rounded-lg
- Background: white with cream on disabled
- Labels: 14px, medium weight, mb-2

### Buttons
Primary: Gold background, white text, rounded-lg, px-6 py-3
Secondary: White background, gold border, gold text
Tertiary: Ghost style with gold hover state
Icon buttons: 40x40px, rounded-full, subtle gold hover background

## Visual Enhancements

**Micro-interactions**: Subtle scale transforms on card hover (scale-[1.01]), smooth color transitions (transition-all duration-200)

**Dividers**: Use cream-colored hairline dividers (1px) between sections, gold dividers (2px) for major breaks

**Badges/Tags**: Rounded-full pills for status indicators (Active/Inactive), conversation sentiment tags, cream background with gold text

**Empty States**: Centered illustrations with gentle gold accent color, encouraging copy, "Add New" CTAs

**Loading States**: Skeleton screens with cream shimmer effect for tables/lists

## Images
No hero images required. Include:
- **Brand Logo**: Elegant lockup in sidebar header (SVG preferred)
- **User Avatars**: Circular, 40px in tables, 80px in profile cards
- **Empty State Illustrations**: Minimalist line art in gold tones for "No sessions yet," "No messages"
- **Chart Placeholder**: If no data, show gold-tinted sample visualization

## Data Visualization
Charts use cream/gold gradient palette:
- Line charts: Gold stroke with cream fill gradient
- Bar charts: Gold bars with cream backgrounds
- Pie/donut: Monochromatic gold shades
- Use Recharts or Chart.js libraries

This dashboard balances professional admin functionality with Anna Kitney's refined wellness brand, creating a cohesive experience from chatbot to backend management.