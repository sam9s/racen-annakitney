'use client';

import { useState, KeyboardEvent } from 'react';

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled: boolean;
}

export function ChatInput({ onSend, disabled }: ChatInputProps) {
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
            placeholder="Ask about Anna Kitney..."
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
