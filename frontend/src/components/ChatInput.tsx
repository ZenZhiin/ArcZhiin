import { useState, useRef, useEffect, KeyboardEvent } from 'react';

interface ChatInputProps {
  onSendMessage: (msg: string) => void;
  onClearContext: () => void;
  isThinking: boolean;
}

export const ChatInput = ({ onSendMessage, onClearContext, isThinking }: ChatInputProps) => {
  const [input, setInput] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    textareaRef.current?.focus();
  }, []);

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (input.trim() && !isThinking) {
        onSendMessage(input.trim());
        setInput('');
      }
    }
  };

  return (
    <div className="p-4 bg-[var(--color-arc-bg)] border-t border-[var(--color-arc-border)] flex gap-3 items-end">
      <button 
        onClick={onClearContext}
        className="mb-1 p-2 h-10 rounded text-[var(--color-arc-muted)] hover:text-[var(--color-arc-error)] hover:bg-[rgba(239,68,68,0.1)] transition-colors text-xs font-mono uppercase tracking-wider whitespace-nowrap"
        title="Clear Context"
      >
        Clear
      </button>
      
      <div className="flex-1 relative group">
        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isThinking}
          placeholder="Type a message..."
          className="w-full bg-[var(--color-arc-surface)] border border-[var(--color-arc-border)] rounded-lg py-3 px-4 text-sm text-[var(--color-arc-text)] focus:outline-none focus:border-[var(--color-arc-cyan)] focus:shadow-[0_0_10px_rgba(0,212,255,0.2)] transition-all resize-none min-h-[44px] max-h-[200px] placeholder:text-[var(--color-arc-muted)]"
          rows={1}
        />
      </div>

      <button
        onClick={() => {
          if (input.trim() && !isThinking) {
            onSendMessage(input.trim());
            setInput('');
          }
        }}
        disabled={isThinking || !input.trim()}
        className="mb-1 h-10 px-6 rounded bg-[var(--color-arc-cyan)] text-black font-semibold text-sm uppercase tracking-wider hover:bg-[var(--color-arc-sky)] disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-[0_0_15px_rgba(0,212,255,0.4)] disabled:shadow-none"
      >
        Send
      </button>
    </div>
  );
};
