import { useState, useRef, useEffect, ReactNode } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { ThemeToggle } from "@/components/theme-toggle";
import { Send, RotateCcw, Loader2, MessageCircle } from "lucide-react";
import logoImage from "@assets/AK_logo_black_compressed_1767495757104.png";

function extractNavigationUrl(content: string): { url: string | null; cleanContent: string } {
  const navRegex = /\[NAVIGATE:(https?:\/\/[^\]]+)\]\s*/i;
  const match = content.match(navRegex);
  const cleanContent = content.replace(navRegex, '').trim();
  
  if (match) {
    return { url: match[1], cleanContent };
  }
  return { url: null, cleanContent };
}

function parseInlineContent(text: string, lineIndex: number, startCount: number): { nodes: ReactNode[], count: number } {
  const nodes: ReactNode[] = [];
  const linkRegex = /\[([^\]]+)\]\(([^)]+)\)/g;
  let lastIndex = 0;
  let match;
  let matchCount = startCount;
  
  while ((match = linkRegex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      nodes.push(text.substring(lastIndex, match.index));
    }
    
    const linkText = match[1];
    const linkUrl = match[2];
    nodes.push(
      <a
        key={`link-${lineIndex}-${matchCount}`}
        href={linkUrl}
        target="_blank"
        rel="noopener noreferrer"
        className="text-primary hover:text-primary/80 underline"
        data-testid={`link-program-${matchCount}`}
      >
        {linkText}
      </a>
    );
    
    lastIndex = linkRegex.lastIndex;
    matchCount++;
  }
  
  if (lastIndex < text.length) {
    nodes.push(text.substring(lastIndex));
  }
  
  return { nodes, count: matchCount };
}

function renderMessageContent(text: string): ReactNode[] {
  const parts: ReactNode[] = [];
  const lines = text.split('\n');
  
  lines.forEach((line, lineIndex) => {
    // Handle horizontal dividers
    if (line.trim() === '---' || line.trim() === '***') {
      parts.push(
        <hr 
          key={`hr-${lineIndex}`} 
          className="my-3 border-t border-border/50" 
        />
      );
      return;
    }
    
    // Handle special {{SUBTITLE:...}} marker for event date/description lines
    const subtitleMatch = line.match(/^\{\{SUBTITLE:(.+)\}\}$/);
    if (subtitleMatch) {
      parts.push(
        <div 
          key={`subtitle-${lineIndex}`}
          className="text-base font-medium my-2"
          style={{ color: 'hsl(var(--wellness-teal))' }}
        >
          {subtitleMatch[1]}
        </div>
      );
      return;
    }
    
    if (lineIndex > 0) {
      parts.push(<br key={`br-${lineIndex}`} />);
    }
    
    if (line.trim() === '') {
      return;
    }
    
    // CRITICAL: Use a single combined regex to parse in correct order
    // This ensures markdown links are fully matched before URLs inside them can be matched separately
    // Order: [text](url) -> **bold** -> *italic* -> raw https URLs
    const combinedRegex = /\[([^\]]+)\]\(([^)]+)\)|(\*\*)([^*]+)\*\*|(?:^|[^*])(\*)([^*]+)\*(?:[^*]|$)|(https?:\/\/[^\s<>")\]]+)/g;
    let lastIndex = 0;
    let match;
    let matchCount = 0;
    
    const lineNodes: ReactNode[] = [];
    
    while ((match = combinedRegex.exec(line)) !== null) {
      // Add text before this match
      if (match.index > lastIndex) {
        lineNodes.push(line.substring(lastIndex, match.index));
      }
      
      if (match[1] !== undefined && match[2] !== undefined) {
        // Markdown link: [text](url)
        let linkText = match[1];
        const linkUrl = match[2];
        
        // Check if link text has bold markers **text**
        const boldInLink = linkText.match(/^\*\*(.+)\*\*$/);
        const linkContent = boldInLink ? <strong>{boldInLink[1]}</strong> : linkText;
        
        lineNodes.push(
          <a
            key={`link-${lineIndex}-${matchCount}`}
            href={linkUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="text-primary hover:text-primary/80 underline"
            data-testid={`link-program-${matchCount}`}
          >
            {linkContent}
          </a>
        );
        matchCount++;
        lastIndex = match.index + match[0].length;
      } else if (match[3] !== undefined && match[4] !== undefined) {
        // Bold text: **text**
        lineNodes.push(<strong key={`bold-${lineIndex}-${matchCount}`}>{match[4]}</strong>);
        matchCount++;
        lastIndex = match.index + match[0].length;
      } else if (match[5] !== undefined && match[6] !== undefined) {
        // Italic text: *text* (with boundary handling)
        // Add any leading non-* char back
        const fullMatch = match[0];
        const italicStart = fullMatch.indexOf('*');
        const italicEnd = fullMatch.lastIndexOf('*');
        if (italicStart > 0) {
          lineNodes.push(fullMatch.substring(0, italicStart));
        }
        lineNodes.push(<em key={`italic-${lineIndex}-${matchCount}`} className="text-muted-foreground">{match[6]}</em>);
        if (italicEnd < fullMatch.length - 1) {
          lineNodes.push(fullMatch.substring(italicEnd + 1));
        }
        matchCount++;
        lastIndex = match.index + match[0].length;
      } else if (match[7] !== undefined) {
        // Raw URL
        lineNodes.push(
          <a
            key={`url-${lineIndex}-${matchCount}`}
            href={match[7]}
            target="_blank"
            rel="noopener noreferrer"
            className="text-primary hover:text-primary/80 underline break-all"
            data-testid={`link-url-${matchCount}`}
          >
            {match[7]}
          </a>
        );
        matchCount++;
        lastIndex = match.index + match[0].length;
      }
    }
    
    // Add remaining text after last match
    if (lastIndex < line.length) {
      lineNodes.push(line.substring(lastIndex));
    }
    
    parts.push(...lineNodes);
  });
  
  return parts;
}

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: string[];
  timestamp: Date;
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId] = useState(() => `anna_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 120) + "px";
    }
  }, [input]);

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: `msg_${Date.now()}`,
      role: "user",
      content: input.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      const conversationHistory = [
        ...messages.map((m) => ({
          role: m.role,
          content: m.content,
        })),
        { role: userMessage.role, content: userMessage.content },
      ];

      const response = await fetch("/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: userMessage.content,
          session_id: sessionId,
          conversation_history: conversationHistory,
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to get response");
      }

      const data = await response.json();
      
      const rawResponse = data.response || "I apologize, but I encountered an issue. Please try again.";
      const { url: navigationUrl, cleanContent } = extractNavigationUrl(rawResponse);

      const assistantMessage: Message = {
        id: `msg_${Date.now()}_assistant`,
        role: "assistant",
        content: cleanContent,
        sources: data.sources || [],
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
      
      if (navigationUrl) {
        setTimeout(() => {
          window.open(navigationUrl, '_blank');
        }, 1500);
      }
    } catch (error) {
      console.error("Error sending message:", error);
      const errorMessage: Message = {
        id: `msg_${Date.now()}_error`,
        role: "assistant",
        content: "I apologize, but I encountered a connection issue. Please try again.",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const resetConversation = () => {
    setMessages([]);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="flex flex-col h-screen bg-background" data-testid="page-home">
      <header className="flex items-center justify-between gap-2 px-4 py-3 border-b bg-card">
        <div className="flex items-center gap-2">
          <img src={logoImage} alt="Anna Kitney" className="h-8" data-testid="img-logo" />
          <h1 className="text-lg font-semibold" data-testid="text-header-title">Anna Kitney Wellness</h1>
        </div>
        <div className="flex items-center gap-1">
          <ThemeToggle />
          <Button
            variant="ghost"
            size="icon"
            onClick={resetConversation}
            data-testid="button-reset-chat"
          >
            <RotateCcw className="w-4 h-4" />
          </Button>
        </div>
      </header>

      <div className="flex-1 overflow-y-auto p-4">
        <div className="max-w-2xl mx-auto space-y-4">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center min-h-[50vh] text-center px-4">
              <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mb-4">
                <MessageCircle className="w-8 h-8 text-primary" />
              </div>
              <h2 className="text-xl font-light text-muted-foreground mb-2" data-testid="text-welcome-title">
                Hi, I'm Anna
              </h2>
              <p className="text-sm text-muted-foreground mb-6" data-testid="text-welcome-subtitle">
                Your friendly wellness guide at Anna Kitney
              </p>
              <div className="text-left text-sm text-muted-foreground space-y-1">
                <p className="font-medium mb-2">I can help you explore:</p>
                <p>Wellness coaching programs</p>
                <p>Business and spiritual leadership</p>
                <p>SoulAlign courses and offerings</p>
                <p>How to get started with coaching</p>
              </div>
              <p className="text-sm mt-6 text-muted-foreground/60" data-testid="text-prompt">
                What brings you here today?
              </p>
            </div>
          )}

          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
              data-testid={`message-${message.role}-${message.id}`}
            >
              <Card
                className={`max-w-[80%] p-3 ${
                  message.role === "user"
                    ? "bg-accent"
                    : "bg-muted"
                }`}
              >
                <div 
                  className="text-sm whitespace-pre-wrap leading-relaxed text-justify"
                  style={{ fontFamily: 'var(--font-serif)' }}
                >
                  {message.role === "assistant" 
                    ? renderMessageContent(message.content)
                    : message.content}
                </div>
                {message.sources && message.sources.length > 0 && (
                  <div className="mt-2 pt-2 border-t border-border/50">
                    <p className="text-xs text-muted-foreground">Sources:</p>
                    <ul className="text-xs mt-1 space-y-0.5">
                      {message.sources.slice(0, 3).map((source, idx) => (
                        <li key={idx} className="truncate">
                          <a
                            href={source}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-primary/80 hover:text-primary hover:underline"
                            data-testid={`link-source-${idx}`}
                          >
                            {source}
                          </a>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </Card>
            </div>
          ))}

          {isLoading && (
            <div className="flex justify-start" data-testid="indicator-loading">
              <Card className="bg-muted p-3">
                <div className="flex items-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span className="text-sm text-muted-foreground">Anna is typing...</span>
                </div>
              </Card>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      <div className="p-4 border-t bg-card">
        <div className="max-w-2xl mx-auto flex gap-2">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask me about wellness coaching..."
            className="flex-1 resize-none rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 min-h-[40px] max-h-[120px]"
            disabled={isLoading}
            rows={1}
            data-testid="input-message"
          />
          <Button
            onClick={sendMessage}
            disabled={isLoading || !input.trim()}
            size="icon"
            data-testid="button-send"
          >
            <Send className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}
