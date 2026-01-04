# Program Link Redirection Feature - Implementation Guide

This document explains how the JoveHeal chatbot implements clickable program links that redirect users to program pages.

## Overview

When the chatbot mentions a program (e.g., "Balance Mastery"), it automatically:
1. Converts the program name to a clickable markdown link
2. The frontend renders this as a clickable link
3. Clicking opens the program page in a new tab (or navigates in embedded mode)

## Architecture

The feature has two parts:
1. **Backend**: Injects markdown links into the response
2. **Frontend**: Renders markdown links as clickable elements

---

## Backend Implementation

### 1. Define Program URL Mapping

Create a dictionary mapping program names to their URLs:

```python
# In your guardrails/engine file
PROGRAM_URLS = {
    "Program Name 1": "https://yoursite.com/program-1/",
    "Program Name 2": "https://yoursite.com/program-2/",
    # Add all programs here
}
```

### 2. Create the Link Injection Function

This function post-processes the LLM response to convert program mentions into markdown links:

```python
import re

def inject_program_links(response: str) -> str:
    """
    Post-process LLM response to add clickable links to program mentions.
    
    Converts mentions like "Balance Mastery" to "[Balance Mastery](https://site.com/balance-mastery/)"
    Case-insensitive matching, only converts if not already a markdown link.
    """
    result = response
    
    for program_name, url in PROGRAM_URLS.items():
        # Skip generic pages (Services, About, etc.)
        if program_name in ["Services", "About", "Contact"]:
            continue
        
        # Pattern: Match program name that's NOT already in a markdown link
        # (?<!\[) = not preceded by [
        # (?!\]|\() = not followed by ] or (
        pattern = rf'(?<!\[)({re.escape(program_name)})(?!\]|\()'
        
        match = re.search(pattern, result, re.IGNORECASE)
        if match:
            matched_text = match.group(1)
            markdown_link = f"[{program_name}]({url})"
            result = result[:match.start()] + markdown_link + result[match.end():]
    
    return result
```

### 3. Call the Function After LLM Response

In your main chat response function, apply link injection after getting the LLM response:

```python
def generate_response(user_message, conversation_history):
    # ... get LLM response ...
    response = get_llm_response(...)
    
    # Post-process: inject program links
    response = inject_program_links(response)
    
    return response
```

---

## Frontend Implementation

### React/Next.js (ChatMessage.tsx)

The frontend needs to:
1. Parse markdown links in the response
2. Render them as clickable `<a>` tags

```tsx
// Function to handle navigation (works in embedded mode too)
function navigateToUrl(url: string, isEmbedded: boolean) {
  if (isEmbedded) {
    try {
      // In iframe, navigate parent window
      window.parent.location.href = url;
    } catch {
      // Fallback if cross-origin blocked
      window.open(url, '_blank');
    }
  } else {
    // Normal mode: open in new tab
    window.open(url, '_blank');
  }
}

// In your message rendering component
function renderMessageWithLinks(text: string) {
  // Regex to match markdown links: [text](url)
  const linkPattern = /\[([^\]]+)\]\(([^)]+)\)/g;
  
  const parts = [];
  let lastIndex = 0;
  let match;
  
  while ((match = linkPattern.exec(text)) !== null) {
    // Add text before the link
    if (match.index > lastIndex) {
      parts.push(text.slice(lastIndex, match.index));
    }
    
    // Add the clickable link
    const linkText = match[1];
    const url = match[2];
    parts.push(
      <a
        key={match.index}
        href={url}
        target="_blank"
        rel="noopener noreferrer"
        className="text-blue-500 hover:text-blue-400 underline"
      >
        {linkText}
      </a>
    );
    
    lastIndex = match.index + match[0].length;
  }
  
  // Add remaining text
  if (lastIndex < text.length) {
    parts.push(text.slice(lastIndex));
  }
  
  return parts;
}
```

### Widget.js (Standalone JavaScript)

For embeddable widgets without React:

```javascript
function createSafeContent(text) {
  // Convert markdown links to HTML
  const linkPattern = /\[([^\]]+)\]\((https?:\/\/[^)]+)\)/g;
  
  let result = text.replace(linkPattern, function(match, linkText, url) {
    return `<a href="${url}" target="_blank" rel="noopener noreferrer" 
            style="color: #60a5fa; text-decoration: underline;">${linkText}</a>`;
  });
  
  return result;
}

// Use when rendering messages
messageElement.innerHTML = createSafeContent(message.content);
```

---

## Optional: Contextual Links at Response End

For adding relevant program links even when the chatbot doesn't explicitly mention them:

```python
# Define topic-to-program mapping
TOPIC_TO_PROGRAMS = {
    "stress": ["Balance Mastery", "Inner Reset"],
    "relationship": ["Relationship Healing", "Elevate 360"],
    "career": ["Career Healing", "Beyond the Hustle"],
    "money": ["Money and Abundance"],
    # Add more topic keywords
}

def append_contextual_links(query: str, response: str) -> str:
    """
    Append relevant program links at the end of response based on topic keywords.
    Only if response doesn't already have URLs.
    """
    # Check if response already has links
    if re.search(r'\[[^\]]+\]\([^)]+\)', response):
        return response
    
    # Find relevant programs based on query keywords
    query_lower = query.lower()
    programs = []
    
    for keyword, program_list in TOPIC_TO_PROGRAMS.items():
        if keyword in query_lower:
            for program in program_list:
                if program not in programs and len(programs) < 3:
                    programs.append(program)
    
    if not programs:
        return response
    
    # Build links
    links = []
    for program in programs:
        if program in PROGRAM_URLS:
            url = PROGRAM_URLS[program]
            links.append(f"[{program}]({url})")
    
    # Append to response
    closing = "\n\n---\n\n*You might find these helpful:*\n" + " | ".join(links)
    return response + closing
```

---

## Key Files in JoveHeal Implementation

| File | Purpose |
|------|---------|
| `safety_guardrails.py` | Contains `inject_program_links()`, `append_contextual_links()`, URL mappings |
| `chatbot_engine.py` | Calls link injection after LLM response |
| `src/components/ChatMessage.tsx` | React component that renders markdown links as clickable |
| `public/widget.js` | Standalone widget with its own link rendering |

---

## Testing

1. Ask the chatbot about a specific program: "Tell me about Balance Mastery"
2. The response should contain `[Balance Mastery](https://...)` 
3. The link should be clickable and open the program page
4. In embedded widget mode, clicking should navigate the parent window

---

## Notes

- The regex `(?<!\[)` prevents double-linking already linked text
- Case-insensitive matching handles "balance mastery" → "Balance Mastery"
- The frontend must handle both embedded (iframe) and standalone modes differently
