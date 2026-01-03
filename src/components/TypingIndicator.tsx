'use client';

export function TypingIndicator() {
  return (
    <div className="flex justify-start message-enter">
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
