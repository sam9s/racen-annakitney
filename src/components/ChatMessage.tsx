'use client';

import { useState, useEffect, useRef } from 'react';
import Image from 'next/image';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: string[];
  timestamp: Date;
  feedbackGiven?: 'up' | 'down' | null;
}

interface ChatMessageProps {
  message: Message;
  onFeedback: (messageId: string, feedback: 'up' | 'down', comment?: string) => void;
}

const ALLOWED_NAVIGATION_DOMAINS = [
  'joveheal.com',
  'www.joveheal.com',
  'bit.ly',
];

function isAllowedUrl(url: string): boolean {
  try {
    const parsed = new URL(url);
    return ALLOWED_NAVIGATION_DOMAINS.some(domain => 
      parsed.hostname === domain || parsed.hostname.endsWith('.' + domain)
    );
  } catch {
    return false;
  }
}

function extractNavigationUrl(content: string): { url: string | null; cleanContent: string } {
  const navRegex = /\[NAVIGATE:(https?:\/\/[^\]]+)\]\s*/i;
  const match = content.match(navRegex);
  const cleanContent = content.replace(navRegex, '').trim();
  
  if (match) {
    const url = match[1];
    if (isAllowedUrl(url)) {
      return { url, cleanContent };
    }
    console.warn('Navigation blocked: URL not in allowlist', url);
  }
  
  return { url: null, cleanContent };
}

function performNavigation(url: string): void {
  if (!isAllowedUrl(url)) {
    console.warn('Navigation blocked: URL not in allowlist', url);
    return;
  }
  
  const isEmbedded = typeof window !== 'undefined' && window.parent !== window;
  
  if (isEmbedded) {
    try {
      window.parent.location.href = url;
    } catch {
      window.open(url, '_blank');
    }
  } else {
    window.open(url, '_blank');
  }
}

function renderFormattedText(text: string, keyPrefix: string = ''): React.ReactNode[] {
  const lines = text.split('\n');
  const result: React.ReactNode[] = [];
  
  lines.forEach((line, lineIndex) => {
    if (lineIndex > 0) {
      result.push(<br key={`${keyPrefix}br-${lineIndex}`} />);
    }
    
    const parts: React.ReactNode[] = [];
    const combinedRegex = /(\*\*([^*]+)\*\*)|(\[([^\]]+)\]\(([^)]+)\))|(https?:\/\/[^\s]+)/g;
    let lastIndex = 0;
    let match;
    let matchIndex = 0;

    while ((match = combinedRegex.exec(line)) !== null) {
      if (match.index > lastIndex) {
        parts.push(line.slice(lastIndex, match.index));
      }
      
      if (match[1]) {
        const boldText = match[2];
        parts.push(
          <strong key={`${keyPrefix}bold-${lineIndex}-${matchIndex}`} className="font-semibold">
            {boldText}
          </strong>
        );
      } else if (match[3]) {
        const linkText = match[4];
        const url = match[5];
        parts.push(
          <a
            key={`${keyPrefix}link-${lineIndex}-${matchIndex}`}
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-primary-400 hover:text-primary-300 underline underline-offset-2 transition-colors"
          >
            {linkText}
          </a>
        );
      } else if (match[6]) {
        const url = match[6];
        parts.push(
          <a
            key={`${keyPrefix}url-${lineIndex}-${matchIndex}`}
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-primary-400 hover:text-primary-300 underline underline-offset-2 transition-colors break-all"
          >
            {url}
          </a>
        );
      }
      
      matchIndex++;
      lastIndex = match.index + match[0].length;
    }

    if (lastIndex < line.length) {
      parts.push(line.slice(lastIndex));
    }

    if (parts.length > 0) {
      result.push(...parts);
    } else if (line.length > 0) {
      result.push(line);
    }
  });

  return result.length > 0 ? result : [text];
}

function renderLinks(text: string): React.ReactNode[] {
  return renderFormattedText(text);
}

export function ChatMessage({ message, onFeedback }: ChatMessageProps) {
  const [showFeedbackInput, setShowFeedbackInput] = useState(false);
  const [feedbackComment, setFeedbackComment] = useState('');
  const [pendingFeedback, setPendingFeedback] = useState<'up' | 'down' | null>(null);
  const navigationTriggered = useRef(false);

  const isUser = message.role === 'user';
  
  const { url: navigationUrl, cleanContent } = extractNavigationUrl(message.content);
  
  useEffect(() => {
    if (navigationUrl && !navigationTriggered.current && message.role === 'assistant') {
      navigationTriggered.current = true;
      const timer = setTimeout(() => {
        performNavigation(navigationUrl);
      }, 1500);
      
      return () => clearTimeout(timer);
    }
  }, [navigationUrl, message.role]);

  const handleFeedbackClick = (feedback: 'up' | 'down') => {
    if (message.feedbackGiven) return;
    
    if (feedback === 'down') {
      setPendingFeedback(feedback);
      setShowFeedbackInput(true);
    } else {
      onFeedback(message.id, feedback);
    }
  };

  const submitFeedback = () => {
    if (pendingFeedback) {
      onFeedback(message.id, pendingFeedback, feedbackComment);
      setShowFeedbackInput(false);
      setFeedbackComment('');
      setPendingFeedback(null);
    }
  };

  return (
    <div className={`message-enter flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      {!isUser && (
        <div className="flex-shrink-0 mr-2 mt-1">
          <div className="w-7 h-7 rounded-full overflow-hidden bg-primary-500/20 border border-primary-500/30">
            <Image
              src="/jovee-logo.png"
              alt="Jovee"
              width={28}
              height={28}
              className="w-full h-full object-cover"
            />
          </div>
        </div>
      )}
      
      <div
        className={`max-w-[80%] md:max-w-[70%] rounded-xl px-3 py-2 transition-colors duration-300 ${
          isUser
            ? 'bg-primary-500/20 border border-primary-500/30 text-theme'
            : 'bg-theme-card border border-primary-500/10 text-theme'
        }`}
      >
        <div className="whitespace-pre-wrap text-xs md:text-sm leading-relaxed">
          {renderLinks(cleanContent)}
        </div>
        
        {navigationUrl && (
          <div className="mt-2 flex items-center gap-2 text-xs text-primary-400">
            <svg className="w-4 h-4 animate-pulse" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            <span>Navigating...</span>
          </div>
        )}
        
        {!isUser && (
          <div className="mt-2 pt-2 border-t border-primary-500/10">
            <div className="flex items-center gap-2">
              <span className="text-[10px] text-theme-muted">Was this helpful?</span>
              <button
                onClick={() => handleFeedbackClick('up')}
                disabled={!!message.feedbackGiven}
                className={`p-1 rounded transition-colors ${
                  message.feedbackGiven === 'up'
                    ? 'text-green-500 bg-green-500/10'
                    : 'text-theme-muted hover:text-green-500 hover:bg-green-500/10'
                } disabled:cursor-not-allowed`}
                aria-label="Thumbs up"
              >
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5" />
                </svg>
              </button>
              <button
                onClick={() => handleFeedbackClick('down')}
                disabled={!!message.feedbackGiven}
                className={`p-1 rounded transition-colors ${
                  message.feedbackGiven === 'down'
                    ? 'text-red-500 bg-red-500/10'
                    : 'text-theme-muted hover:text-red-500 hover:bg-red-500/10'
                } disabled:cursor-not-allowed`}
                aria-label="Thumbs down"
              >
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14H5.236a2 2 0 01-1.789-2.894l3.5-7A2 2 0 018.736 3h4.018a2 2 0 01.485.06l3.76.94m-7 10v5a2 2 0 002 2h.096c.5 0 .905-.405.905-.904 0-.715.211-1.413.608-2.008L17 13V4m-7 10h2m5-10h2a2 2 0 012 2v6a2 2 0 01-2 2h-2.5" />
                </svg>
              </button>
            </div>
            
            {showFeedbackInput && (
              <div className="mt-2 space-y-2">
                <textarea
                  value={feedbackComment}
                  onChange={(e) => setFeedbackComment(e.target.value)}
                  placeholder="What could be improved? (optional)"
                  className="w-full px-2 py-1.5 text-xs bg-theme-surface border border-primary-500/20 rounded-lg text-theme placeholder-gray-500 focus:outline-none focus:border-primary-500/50 resize-none transition-colors duration-300"
                  rows={2}
                />
                <div className="flex gap-2">
                  <button
                    onClick={submitFeedback}
                    className="px-2 py-1 text-[10px] bg-primary-500/20 hover:bg-primary-500/30 text-primary-500 rounded transition-colors"
                  >
                    Submit
                  </button>
                  <button
                    onClick={() => {
                      setShowFeedbackInput(false);
                      setFeedbackComment('');
                      setPendingFeedback(null);
                    }}
                    className="px-2 py-1 text-[10px] bg-theme-surface hover:bg-primary-500/10 text-theme-muted rounded transition-colors border border-primary-500/10"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
