import { useState, useRef, useEffect, ReactNode } from "react";
import { useLocation } from "wouter";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { ThemeToggle } from "@/components/theme-toggle";
import { Send, RotateCcw, Loader2, MessageCircle } from "lucide-react";
import logoImage from "@assets/AK_gpt_transparent-removebg-preview_1767940932921.png";

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
    
    // CRITICAL: Parse markdown in correct order to handle **[text](url)** pattern
    // The LLM outputs bold-wrapped links like **[Elite Private Advisory](url)**
    // We need to match: 1) bold-wrapped links, 2) plain links, 3) bold, 4) raw URLs
    const boldLinkRegex = /\*\*\[([^\]]+)\]\(([^)]+)\)\*\*/g;
    const linkRegex = /\[([^\]]+)\]\(([^)]+)\)/g;
    const boldRegex = /\*\*([^*]+)\*\*/g;
    const urlRegex = /(https?:\/\/[^\s<>")\]]+)/g;
    
    let lastIndex = 0;
    let matchCount = 0;
    const lineNodes: ReactNode[] = [];
    
    // Build a list of all matches with their positions
    type MatchInfo = { start: number; end: number; type: string; groups: string[] };
    const allMatches: MatchInfo[] = [];
    
    // Find bold-wrapped links FIRST (highest priority)
    let m;
    while ((m = boldLinkRegex.exec(line)) !== null) {
      allMatches.push({ start: m.index, end: m.index + m[0].length, type: 'boldLink', groups: [m[1], m[2]] });
    }
    
    // Find plain links (skip if overlaps with bold link)
    while ((m = linkRegex.exec(line)) !== null) {
      const overlaps = allMatches.some(x => m!.index >= x.start && m!.index < x.end);
      if (!overlaps) {
        allMatches.push({ start: m.index, end: m.index + m[0].length, type: 'link', groups: [m[1], m[2]] });
      }
    }
    
    // Find bold text (skip if overlaps)
    while ((m = boldRegex.exec(line)) !== null) {
      const overlaps = allMatches.some(x => m!.index >= x.start && m!.index < x.end);
      if (!overlaps) {
        allMatches.push({ start: m.index, end: m.index + m[0].length, type: 'bold', groups: [m[1]] });
      }
    }
    
    // Find raw URLs (skip if overlaps)
    while ((m = urlRegex.exec(line)) !== null) {
      const overlaps = allMatches.some(x => m!.index >= x.start && m!.index < x.end);
      if (!overlaps) {
        allMatches.push({ start: m.index, end: m.index + m[0].length, type: 'url', groups: [m[0]] });
      }
    }
    
    // Sort by position
    allMatches.sort((a, b) => a.start - b.start);
    
    // Process matches in order
    for (const match of allMatches) {
      // Add text before this match
      if (match.start > lastIndex) {
        lineNodes.push(line.substring(lastIndex, match.start));
      }
      
      if (match.type === 'boldLink') {
        // **[text](url)** - bold link
        lineNodes.push(
          <a
            key={`link-${lineIndex}-${matchCount}`}
            href={match.groups[1]}
            target="_blank"
            rel="noopener noreferrer"
            className="text-primary hover:text-primary/80 underline font-bold"
            data-testid={`link-program-${matchCount}`}
          >
            {match.groups[0]}
          </a>
        );
        matchCount++;
      } else if (match.type === 'link') {
        // [text](url) - plain link
        let linkText = match.groups[0];
        // Check if link text has bold markers **text**
        const boldInLink = linkText.match(/^\*\*(.+)\*\*$/);
        const linkContent = boldInLink ? <strong>{boldInLink[1]}</strong> : linkText;
        
        lineNodes.push(
          <a
            key={`link-${lineIndex}-${matchCount}`}
            href={match.groups[1]}
            target="_blank"
            rel="noopener noreferrer"
            className="text-primary hover:text-primary/80 underline"
            data-testid={`link-program-${matchCount}`}
          >
            {linkContent}
          </a>
        );
        matchCount++;
      } else if (match.type === 'bold') {
        lineNodes.push(<strong key={`bold-${lineIndex}-${matchCount}`}>{match.groups[0]}</strong>);
        matchCount++;
      } else if (match.type === 'url') {
        lineNodes.push(
          <a
            key={`url-${lineIndex}-${matchCount}`}
            href={match.groups[0]}
            target="_blank"
            rel="noopener noreferrer"
            className="text-primary hover:text-primary/80 underline break-all"
            data-testid={`link-url-${matchCount}`}
          >
            {match.groups[0]}
          </a>
        );
        matchCount++;
      }
      
      lastIndex = match.end;
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
  const [, setLocation] = useLocation();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId] = useState(() => `anna_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const goToTestRunner = () => {
    sessionStorage.setItem("testRunnerAccess", "true");
    setLocation("/test-runner");
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  // Listen for postMessage from parent page (Lovable landing page search bar)
  useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      // Accept messages with sendMessage type from any origin (for iframe embedding)
      if (event.data && event.data.type === 'sendMessage' && event.data.message) {
        const query = event.data.message.trim();
        if (query) {
          setInput(query);
          // Use setTimeout to ensure input state is set before sending
          setTimeout(() => {
            const userMessage: Message = {
              id: `msg_${Date.now()}`,
              role: "user",
              content: query,
              timestamp: new Date(),
            };
            setMessages((prev) => [...prev, userMessage]);
            setIsLoading(true);

            // Send to API
            fetch("/api/chat", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                message: query,
                session_id: sessionId,
                conversation_history: [],
              }),
            })
              .then(res => res.json())
              .then(data => {
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
                  setTimeout(() => window.open(navigationUrl, '_blank'), 1500);
                }
              })
              .catch(() => {
                setMessages((prev) => [...prev, {
                  id: `msg_${Date.now()}_error`,
                  role: "assistant",
                  content: "I apologize, but I encountered a connection issue. Please try again.",
                  timestamp: new Date(),
                }]);
              })
              .finally(() => {
                setIsLoading(false);
                setInput("");
              });
          }, 100);
        }
      }
    };

    window.addEventListener('message', handleMessage);
    return () => window.removeEventListener('message', handleMessage);
  }, [sessionId]);

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
          <img src={logoImage} alt="Anna Kitney" className="h-16" data-testid="img-logo" />
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
        <div className="max-w-2xl mx-auto mt-2 text-center">
          <button
            onClick={goToTestRunner}
            className="text-xs text-muted-foreground/50 hover:text-muted-foreground"
            data-testid="link-test-runner"
          >
            Dev: Test Runner
          </button>
        </div>
      </div>
    </div>
  );
}
