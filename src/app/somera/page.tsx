'use client';

import { useState, useRef, useEffect, KeyboardEvent } from 'react';
import { useTheme } from '@/components/ThemeProvider';
import Image from 'next/image';

function renderMessageWithLinks(content: string): React.ReactNode {
  const parts: React.ReactNode[] = [];
  const combinedRegex = /(\*\*([^*]+)\*\*)|(\[([^\]]+)\]\(([^)]+)\))|(https?:\/\/[^\s]+)/g;
  let lastIndex = 0;
  let match;
  let matchIndex = 0;

  while ((match = combinedRegex.exec(content)) !== null) {
    if (match.index > lastIndex) {
      parts.push(content.slice(lastIndex, match.index));
    }
    
    if (match[1]) {
      // Bold text: **text**
      const boldText = match[2];
      parts.push(
        <strong key={`bold-${matchIndex}`} className="font-semibold">
          {boldText}
        </strong>
      );
    } else if (match[3]) {
      // Markdown link: [text](url)
      const linkText = match[4];
      const url = match[5];
      parts.push(
        <a
          key={`link-${matchIndex}`}
          href={url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-primary-400 hover:text-primary-300 underline underline-offset-2"
        >
          {linkText}
        </a>
      );
    } else if (match[6]) {
      // Raw URL
      const url = match[6];
      parts.push(
        <a
          key={`url-${matchIndex}`}
          href={url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-primary-400 hover:text-primary-300 underline underline-offset-2 break-all"
        >
          {url}
        </a>
      );
    }
    
    matchIndex++;
    lastIndex = match.index + match[0].length;
  }

  if (lastIndex < content.length) {
    parts.push(content.slice(lastIndex));
  }

  return parts.length > 0 ? parts : [content];
}

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: { source: string; topic: string; youtube_url?: string }[];
  timestamp: Date;
}

function SomeraHeader({ onReset }: { onReset: () => void }) {
  const { theme, toggleTheme } = useTheme();

  return (
    <header className="sticky top-0 z-50 backdrop-blur-md bg-theme-surface/90 header-bg border-b border-primary-500/10 transition-colors duration-300">
      <div className="max-w-6xl mx-auto px-2 md:px-4 py-1.5 md:py-2">
        <div className="flex items-center justify-between">
          <div className="w-20 md:w-24 hidden md:block" />
          
          <div className="flex flex-col items-center flex-1">
            <h1 className="text-2xl md:text-3xl font-medium tracking-wider text-white">
              SOMERA
            </h1>
            <p className="hidden md:block text-[10px] md:text-xs tracking-wide text-gray-400 mt-0.5">
              Your Empathetic Coaching Companion
            </p>
          </div>
          
          <div className="flex items-center gap-1 md:gap-2">
            <button
              onClick={toggleTheme}
              className="p-2 md:p-2 rounded-lg btn-theme min-w-[44px] min-h-[44px] flex items-center justify-center"
              aria-label="Toggle theme"
            >
              {theme === 'dark' ? (
                <svg
                  className="w-4 h-4 text-primary-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"
                  />
                </svg>
              ) : (
                <svg
                  className="w-4 h-4 text-primary-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"
                  />
                </svg>
              )}
            </button>
            
            <button
              onClick={onReset}
              className="flex items-center gap-1 md:gap-1.5 px-2 md:px-3 py-2 md:py-1.5 text-xs font-medium rounded-lg btn-theme text-theme min-h-[44px]"
            >
              <svg 
                className="w-4 h-4 md:w-3.5 md:h-3.5" 
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
              >
                <path 
                  strokeLinecap="round" 
                  strokeLinejoin="round" 
                  strokeWidth={2} 
                  d="M12 4v16m8-8H4" 
                />
              </svg>
              <span className="hidden md:inline">New Chat</span>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}

function SomeraMessage({ message }: { message: Message }) {
  const isUser = message.role === 'user';

  return (
    <div className={`message-enter flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      {!isUser && (
        <div className="flex-shrink-0 mr-2 mt-1">
          <div className="w-8 h-8 rounded-full overflow-hidden">
            <Image
              src="/somera-icon.png"
              alt="Somera"
              width={32}
              height={32}
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
          {renderMessageWithLinks(message.content)}
        </div>
        
        {message.sources && message.sources.length > 0 && (
          <div className="mt-2 pt-2 border-t border-primary-500/10 space-y-1">
            <p className="text-[10px] text-theme-muted">Inspired by:</p>
            {message.sources.map((s, i) => (
              <div key={i} className="flex items-center gap-1">
                {s.youtube_url ? (
                  <a
                    href={s.youtube_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-[10px] text-primary-400 hover:text-primary-300 underline underline-offset-2 flex items-center gap-1"
                  >
                    <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M19.615 3.184c-3.604-.246-11.631-.245-15.23 0-3.897.266-4.356 2.62-4.385 8.816.029 6.185.484 8.549 4.385 8.816 3.6.245 11.626.246 15.23 0 3.897-.266 4.356-2.62 4.385-8.816-.029-6.185-.484-8.549-4.385-8.816zm-10.615 12.816v-8l8 3.993-8 4.007z"/>
                    </svg>
                    {s.source}
                  </a>
                ) : (
                  <span className="text-[10px] text-theme-muted">{s.source}</span>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function SomeraInput({ onSend, disabled }: { onSend: (message: string) => void; disabled: boolean }) {
  const [input, setInput] = useState('');

  const handleSubmit = () => {
    if (input.trim() && !disabled) {
      onSend(input);
      setInput('');
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const isButtonEnabled = input.trim().length > 0 && !disabled;

  return (
    <div className="relative">
      <div className="gradient-border rounded-full overflow-hidden">
        <div className="flex items-center bg-theme-surface/90 rounded-full transition-colors duration-300">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={disabled}
            placeholder="Share what's on your mind..."
            className="flex-1 px-3 md:px-5 py-3 md:py-3 text-base md:text-sm bg-transparent text-theme placeholder-gray-500 focus:outline-none disabled:opacity-50"
          />
          <button
            onClick={handleSubmit}
            disabled={!isButtonEnabled}
            className={`mr-1 md:mr-1.5 p-3 md:p-2.5 rounded-full transition-all duration-200 min-w-[44px] min-h-[44px] flex items-center justify-center ${
              isButtonEnabled 
                ? 'bg-primary-500 hover:bg-primary-600 glow cursor-pointer' 
                : 'bg-gray-600 cursor-not-allowed opacity-50'
            }`}
            aria-label="Send message"
          >
            <svg
              className="w-5 h-5 md:w-4 md:h-4 text-white"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M14 5l7 7m0 0l-7 7m7-7H3"
              />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}

function SomeraTypingIndicator() {
  return (
    <div className="flex justify-start message-enter">
      <div className="flex-shrink-0 mr-2 mt-1">
        <div className="w-8 h-8 rounded-full overflow-hidden">
          <Image
            src="/somera-icon.png"
            alt="Somera"
            width={32}
            height={32}
            className="w-full h-full object-cover"
          />
        </div>
      </div>
      <div className="bg-theme-card border border-primary-500/10 rounded-2xl px-5 py-4 transition-colors duration-300">
        <div className="flex items-center gap-1">
          <div className="w-2 h-2 bg-primary-400 rounded-full typing-dot" />
          <div className="w-2 h-2 bg-primary-400 rounded-full typing-dot" />
          <div className="w-2 h-2 bg-primary-400 rounded-full typing-dot" />
        </div>
      </div>
    </div>
  );
}

export default function SomeraPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId] = useState(() => `somera_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const sendMessage = async (content: string) => {
    if (!content.trim() || isLoading) return;

    const userMessage: Message = {
      id: `msg_${Date.now()}`,
      role: 'user',
      content: content.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    const assistantMessageId = `msg_${Date.now()}_assistant`;

    try {
      const response = await fetch('/api/somera/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: content.trim(),
          session_id: sessionId,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        if (response.status === 429) {
          if (errorData.captcha_required) {
            const userAnswer = prompt(errorData.captcha?.question || 'Please verify you are human');
            if (userAnswer) {
              const retryResponse = await fetch('/api/somera/stream', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                  message: content.trim(),
                  session_id: sessionId,
                  captcha_answer: userAnswer,
                }),
              });
              if (retryResponse.ok) {
                setIsLoading(false);
                sendMessage(content);
                return;
              }
            }
          }
          throw new Error(errorData.error || 'Rate limit exceeded. Please wait a moment.');
        }
        throw new Error('Stream request failed');
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('No reader available');
      }

      const decoder = new TextDecoder();
      let streamedContent = '';
      let sources: { source: string; topic: string }[] = [];
      let messageAdded = false;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              
              if (data.type === 'content') {
                streamedContent += data.content;
                
                if (!messageAdded) {
                  setMessages((prev) => [...prev, {
                    id: assistantMessageId,
                    role: 'assistant',
                    content: streamedContent,
                    sources: [],
                    timestamp: new Date(),
                  }]);
                  messageAdded = true;
                  setIsLoading(false);
                } else {
                  setMessages((prev) => 
                    prev.map((msg) => 
                      msg.id === assistantMessageId 
                        ? { ...msg, content: streamedContent }
                        : msg
                    )
                  );
                }
              } else if (data.type === 'correction') {
                const correctedContent = data.corrected_response;
                streamedContent = correctedContent;
                setMessages((prev) => 
                  prev.map((msg) => 
                    msg.id === assistantMessageId 
                      ? { ...msg, content: correctedContent }
                      : msg
                  )
                );
              } else if (data.type === 'done') {
                sources = data.sources || [];
                const finalContent = data.full_response || streamedContent;
                setMessages((prev) => 
                  prev.map((msg) => 
                    msg.id === assistantMessageId 
                      ? { ...msg, content: finalContent, sources }
                      : msg
                  )
                );
              } else if (data.type === 'error') {
                if (!messageAdded) {
                  setMessages((prev) => [...prev, {
                    id: assistantMessageId,
                    role: 'assistant',
                    content: data.error || 'I apologize, but I encountered an issue. Please try again.',
                    timestamp: new Date(),
                  }]);
                }
              }
            } catch {
            }
          }
        }
      }

      if (!messageAdded) {
        setMessages((prev) => [...prev, {
          id: assistantMessageId,
          role: 'assistant',
          content: streamedContent || 'I apologize, but I encountered an issue. Please try again.',
          sources,
          timestamp: new Date(),
        }]);
      }
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage: Message = {
        id: `msg_${Date.now()}_error`,
        role: 'assistant',
        content: 'I apologize, but I encountered a connection issue. Please try again.',
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

  return (
    <main className="flex min-h-screen flex-col bg-theme transition-colors duration-300">
      <SomeraHeader onReset={resetConversation} />
      
      <div className="flex-1 flex flex-col max-w-3xl mx-auto w-full px-2 md:px-4">
        <div className="flex-1 overflow-y-auto py-3 md:py-6 space-y-3 md:space-y-4">
          {messages.length === 0 && (
            <div className="flex-1 flex items-center justify-center min-h-[50vh] md:min-h-[60vh]">
              <div className="text-center max-w-md px-4">
                <p className="text-xl font-light text-theme-muted">
                  Hi, I'm SOMERA
                </p>
                <p className="text-sm mt-2 text-theme-muted opacity-80">
                  Your empathetic coaching companion, inspired by Shweta's wisdom
                </p>
                <div className="mt-6 text-left text-sm text-theme-muted opacity-70 space-y-1">
                  <p className="font-medium opacity-90 mb-2">I'm here to support you with:</p>
                  <p>• Understanding procrastination patterns</p>
                  <p>• Finding inner peace and balance</p>
                  <p>• Navigating life's challenges</p>
                  <p>• Gentle, empathetic guidance</p>
                </div>
                <p className="text-sm mt-6 text-theme-muted opacity-60">
                  What's on your mind today?
                </p>
              </div>
            </div>
          )}
          
          {messages.map((message) => (
            <SomeraMessage key={message.id} message={message} />
          ))}
          
          {isLoading && <SomeraTypingIndicator />}
          
          <div ref={messagesEndRef} />
        </div>
        
        <div className="sticky bottom-0 pb-3 md:pb-6 pt-2 md:pt-4 bg-gradient-to-t from-theme via-theme to-transparent">
          <SomeraInput onSend={sendMessage} disabled={isLoading} />
        </div>
      </div>
    </main>
  );
}
