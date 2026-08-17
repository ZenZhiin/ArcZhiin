import type { ChatMessageData } from '../hooks/useWebSocket';

interface ChatMessageProps {
  message: ChatMessageData;
}

export const ChatMessage = ({ message }: ChatMessageProps) => {
  const isUser = message.type === 'user';
  
  if (message.type === 'welcome') {
    return (
      <div className="flex justify-center my-6 animate-fade-in">
        <span className="text-xs text-[var(--color-arc-sky)] border border-[var(--color-arc-border)] bg-[var(--color-arc-surface)] px-4 py-2 rounded-full tracking-wider uppercase shadow-[0_0_15px_rgba(14,165,233,0.1)]">
          {message.content}
        </span>
      </div>
    );
  }

  if (message.type === 'error') {
    return (
      <div className="flex justify-center my-4 animate-fade-in">
        <span className="text-xs text-[var(--color-arc-error)] bg-[rgba(239,68,68,0.1)] px-4 py-2 rounded-md">
          {message.content}
        </span>
      </div>
    );
  }

  return (
    <div className={`flex w-full my-4 animate-fade-in ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`max-w-[80%] p-4 rounded-xl relative ${
        isUser 
          ? 'bg-[var(--color-arc-surface)] rounded-br-none border border-[var(--color-arc-border)]' 
          : 'bg-[#181824] rounded-bl-none border-l-2 border-l-[var(--color-arc-cyan)] shadow-[-4px_0_15px_rgba(0,212,255,0.05)]'
      }`}>
        <p className="text-sm whitespace-pre-wrap leading-relaxed">
          {message.content}
        </p>
        
        {!isUser && message.model && (
          <div className="flex gap-2 mt-3 pt-2 border-t border-[var(--color-arc-border)] text-[10px] text-[var(--color-arc-muted)] font-mono">
            <span className="text-[var(--color-arc-sky)]">{message.model}</span>
            <span>•</span>
            <span>{message.tokens?.input} I / {message.tokens?.output} O</span>
          </div>
        )}
      </div>
    </div>
  );
};
