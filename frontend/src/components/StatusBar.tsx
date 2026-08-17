import { useMemo } from 'react';
import type { ChatMessageData } from '../hooks/useWebSocket';

interface StatusBarProps {
  isConnected: boolean;
  sessionId: string | null;
  messages: ChatMessageData[];
}

export const StatusBar = ({ isConnected, sessionId, messages }: StatusBarProps) => {
  const { totalInputTokens, totalOutputTokens, lastModel, lastTier } = useMemo(() => {
    let input = 0;
    let output = 0;
    let model = 'Awaiting...';
    let tier = '-';

    messages.forEach(m => {
      if (m.tokens) {
        input += m.tokens.input;
        output += m.tokens.output;
      }
      if (m.model) model = m.model;
      if (m.tier) tier = m.tier;
    });

    return { totalInputTokens: input, totalOutputTokens: output, lastModel: model, lastTier: tier };
  }, [messages]);

  return (
    <div className="fixed top-0 left-0 right-0 h-14 bg-[var(--color-arc-surface)] border-b border-[var(--color-arc-border)] flex items-center justify-between px-6 z-50">
      <div className="flex items-center gap-3">
        <div className={`w-2.5 h-2.5 rounded-full ${isConnected ? 'bg-[var(--color-arc-success)] animate-pulse shadow-[0_0_8px_var(--color-arc-success)]' : 'bg-[var(--color-arc-error)]'}`} />
        <span className="font-bold text-lg tracking-wider text-[var(--color-arc-cyan)] drop-shadow-[0_0_4px_rgba(0,212,255,0.3)]">ArcZhiin</span>
      </div>
      
      <div className="hidden sm:flex flex-col items-center">
        <span className="text-xs text-[var(--color-arc-muted)] uppercase tracking-widest">Active Core</span>
        <div className="flex items-center gap-2">
          <span className="text-sm font-mono text-[var(--color-arc-sky)]">{lastModel}</span>
          <span className="text-[10px] bg-[var(--color-arc-border)] px-1.5 py-0.5 rounded text-[var(--color-arc-text)]">{lastTier}</span>
        </div>
      </div>

      <div className="hidden md:flex items-center gap-6 text-xs font-mono text-[var(--color-arc-muted)]">
        <div className="flex flex-col text-right">
          <span>Session</span>
          <span className="text-[var(--color-arc-text)]">{sessionId ? sessionId.slice(0,8) : 'DISCONNECTED'}</span>
        </div>
        <div className="flex flex-col text-right">
          <span>Usage</span>
          <span className="text-[var(--color-arc-cyan)]">{totalInputTokens} In / {totalOutputTokens} Out</span>
        </div>
      </div>
    </div>
  );
};
