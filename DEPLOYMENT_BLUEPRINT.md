# Anna Kitney Wellness Chatbot - Deployment Blueprint

## Overview
This document outlines our phased approach to deploying the complete AI wellness assistant for annakitney.com.

---

## Phase 1: Site Navigation Topology (Week 1-2)

### Step 1: Crawl
- Audit all pages on annakitney.com using site crawling tools
- Document every program, service, and offering page
- Identify all checkout URLs and payment portals (annakitneyportal.com)

### Step 2: Map
- Create a structured navigation manifest (JSON/YAML)
- For each program, document:
  - Program name and URL
  - Enrollment type: Direct Checkout vs. Clarity Call Required
  - Payment options with exact prices and checkout URLs
  - Related programs (upsells, complementary offerings)

### Step 3: Visualize
- Create visual flowcharts showing user journeys
- Map decision points: "Learn More" → Page Navigation, "Enroll" → Payment Options
- Identify common pathways and edge cases

### Step 4: Validate with Anna
- Review the navigation map together
- Confirm all pricing, URLs, and enrollment paths
- Identify priority programs for initial deployment

---

## Phase 2: Chatbot Workflow Design (Week 2-3)

### Conversation Flows
- Welcome & Discovery: Understand visitor's needs
- Program Matching: Recommend based on goals
- Information Delivery: Provide details with navigation options
- Enrollment Guidance: Present correct payment options
- Navigation Handoff: Seamless transition to checkout/booking

### Safety & Accuracy
- All program information sourced from validated manifest
- Crisis detection with professional referrals
- No medical/therapeutic claims beyond scope

---

## Phase 3: Implementation (Week 3-4)

### Technical Components
1. Knowledge Base: ChromaDB with indexed website content
2. Enrollment Manifest: Single source of truth for all programs
3. RAG Engine: GPT-4 powered responses with context
4. Frontend: Web UI + Embeddable Widget

### Quality Assurance
- Test suite covering all program inquiries
- Enrollment flow validation
- Navigation accuracy verification

---

## Phase 4: Deployment & Optimization (Week 4+)

### Launch
- Widget integration on annakitney.com
- Monitoring and analytics setup
- User feedback collection

### Ongoing
- Regular content updates as programs change
- Conversation analytics to improve responses
- A/B testing for engagement optimization

---

## Current POC Status

**Demonstrated Capabilities:**
- RAG-based responses from website content
- Program enrollment guidance with payment options
- Direct navigation to checkout pages
- Embedded widget for external sites

**Flagship Programs Configured:**
- SoulAlign Manifestation Mastery (3 payment tiers)
- Elite Private Advisory (Clarity Call required)
- SoulAlign Heal (2 payment tiers)

---

## Next Steps After Approval

1. Complete site audit and navigation manifest
2. Configure all programs with accurate enrollment data
3. Implement additional "wow factor" features
4. Full testing and quality assurance
5. Production deployment

---

*This blueprint serves as our roadmap. Once approved, we'll expand this into a detailed implementation plan.*
