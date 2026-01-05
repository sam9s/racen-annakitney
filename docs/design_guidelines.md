# Design Guidelines: Anna Kitney Wellness Chatbot

## Design Approach

**Approach**: Hybrid - Modern chat interface standards with warm wellness aesthetics

**References**: Intercom's conversational UI + wellness brand warmth similar to Headspace's approachable design

**Key Principles**:
- Clean, uncluttered chat interface that feels inviting
- Warm, supportive visual language appropriate for wellness coaching
- Seamless integration as widget on Anna's existing site
- Professional yet approachable tone

---

## Typography

**Font System** (Google Fonts):
- **Primary**: Inter (400, 500, 600) - clean, readable for chat interface
- **Accent**: Spectral (400, 500) - warm, elegant for welcome messages and headings

**Type Scale**:
- Chat messages: text-sm (14px)
- Bot name/headers: text-base (16px) - font-medium
- Welcome heading: text-xl (20px) - Spectral
- Timestamp/metadata: text-xs (12px) - text-gray-500

---

## Layout System

**Spacing Primitives**: Tailwind units of 2, 3, 4, 6, 8, 12

**Widget Dimensions**:
- Desktop: Fixed width 380px, max-height 600px
- Mobile: Full screen takeover (w-full h-full)
- Chat bubble trigger: 60px × 60px (rounded-full)

**Message Container**:
- Max-width for messages: 280px (prevents overly wide text blocks)
- Padding within messages: p-3
- Gap between messages: space-y-3
- Input area padding: p-4

**Widget Structure**:
```
┌─────────────────────────┐
│ Header (h-16, p-4)      │ ← Bot name, minimize button
├─────────────────────────┤
│                         │
│  Messages Area          │ ← Scrollable, flex-1
│  (p-4, space-y-3)      │
│                         │
├─────────────────────────┤
│ Input Area (p-4)        │ ← Text input + send button
└─────────────────────────┘
```

---

## Component Library

### Chat Messages
- **User messages**: Align right, rounded-2xl rounded-tr-sm, max-w-[280px]
- **Bot messages**: Align left, rounded-2xl rounded-tl-sm, max-w-[280px]
- **Avatar**: 32px circle for bot, hidden for user (cleaner look)
- **Timestamp**: Below message, text-xs, subtle gray

### Widget Header
- **Height**: h-16
- **Content**: Bot name (left), minimize/close icons (right)
- **Shadow**: Drop shadow for depth separation

### Input Field
- **Border**: 1px solid, rounded-full
- **Height**: h-12
- **Padding**: px-4
- **Send button**: Integrated within input (right side), icon only, rounded-full

### Welcome Screen (First Interaction)
- **Avatar/Icon**: 56px circle centered
- **Heading**: text-xl, Spectral font, centered
- **Description**: text-sm, centered, max-w-xs
- **Suggested prompts**: 2-3 pill buttons, rounded-full, text-sm, stacked vertically with space-y-2

### Chat Bubble Trigger
- **Size**: 60px × 60px
- **Position**: Fixed bottom-6 right-6
- **Shadow**: Large drop shadow for prominence
- **Badge**: Notification dot (8px circle) for new messages

---

## Specific Implementations

### Message Rendering
- **Links**: Underline on hover, maintain readability
- **Lists**: Proper ul/ol with pl-4, space-y-1
- **Emphasis**: Bold for important terms, italic for gentle emphasis
- **Line height**: leading-relaxed (1.625) for comfortable reading

### Loading States
- **Typing indicator**: Three animated dots (8px each), space-x-1, subtle bounce animation
- **Message sending**: Slight opacity on user message until confirmed

### Scrolling Behavior
- **Auto-scroll**: To bottom on new messages
- **Scroll indicator**: Subtle shadow at top when scrolled up
- **Smooth scroll**: scroll-smooth class

---

## Images

**Hero/Welcome Image**:
- **Location**: Welcome screen background (optional, subtle)
- **Treatment**: Low opacity overlay (20-30%), soft blur
- **Subject**: Abstract wellness imagery - calming nature, soft gradients, or minimal geometric patterns
- **Fallback**: Solid color gradient if no image provided

**Avatar/Bot Icon**:
- **Location**: Bot messages, welcome screen
- **Style**: Simple icon or illustrated avatar representing wellness/support
- **Size**: 32px in messages, 56px on welcome screen
- **Treatment**: Contained in circle, soft shadow

---

## Widget-Specific Considerations

**Embedded Mode**:
- Z-index: 9999 for widget overlay
- Backdrop: Semi-transparent overlay (bg-black/20) when widget open on mobile
- Entry animation: Scale and fade in (150ms ease-out)
- Exit animation: Scale and fade out (100ms ease-in)

**Standalone App**:
- Center container: max-w-2xl mx-auto
- Full height: min-h-screen
- Remove floating behavior, use page-based layout

---

## Accessibility

- **Focus states**: 2px ring-offset-2 on interactive elements
- **Color contrast**: WCAG AA minimum (4.5:1 for text)
- **Keyboard navigation**: Full keyboard support for all interactions
- **ARIA labels**: Proper labels for icon buttons, screen reader announcements for new messages
- **Skip links**: Option to skip to input field

---

**Visual Character**: Professional wellness aesthetic - warm, clean, trustworthy, and inviting without being overly casual or clinical.