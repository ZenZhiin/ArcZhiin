interface VoiceOrbProps {
  isConnected: boolean;
}

export const VoiceOrb = ({ isConnected }: VoiceOrbProps) => {
  return (
    <div className="flex flex-col items-center justify-center h-full w-full bg-[var(--color-arc-bg)] border-r border-[var(--color-arc-border)]">
      <div className="relative flex items-center justify-center w-64 h-64">
        {/* Outer Ring */}
        <div className={`absolute w-full h-full rounded-full border border-[var(--color-arc-border)] ${isConnected ? 'animate-[spin_10s_linear_infinite]' : ''}`}>
          <div className={`absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 w-2 h-2 rounded-full ${isConnected ? 'bg-[var(--color-arc-cyan)] shadow-[0_0_8px_var(--color-arc-cyan)]' : 'bg-[var(--color-arc-muted)]'}`} />
          <div className={`absolute bottom-0 left-1/2 -translate-x-1/2 translate-y-1/2 w-2 h-2 rounded-full ${isConnected ? 'bg-[var(--color-arc-sky)] shadow-[0_0_8px_var(--color-arc-sky)]' : 'bg-[var(--color-arc-muted)]'}`} />
        </div>
        
        {/* Middle Ring */}
        <div className={`absolute w-48 h-48 rounded-full border-2 border-dashed ${isConnected ? 'border-[var(--color-arc-sky)] animate-[spin_15s_linear_infinite_reverse] opacity-50' : 'border-[var(--color-arc-muted)] opacity-20'}`} />

        {/* Inner Core */}
        <div className={`w-32 h-32 rounded-full flex items-center justify-center ${
          isConnected 
            ? 'bg-gradient-to-br from-[var(--color-arc-cyan)] to-[var(--color-arc-sky)] shadow-[0_0_40px_rgba(0,212,255,0.5)] animate-pulse' 
            : 'bg-[var(--color-arc-surface)] border border-[var(--color-arc-border)]'
        }`}>
          <div className={`w-24 h-24 rounded-full bg-[var(--color-arc-bg)] flex items-center justify-center ${isConnected ? 'opacity-90' : ''}`}>
             <div className={`w-12 h-12 rounded-full ${isConnected ? 'bg-[var(--color-arc-cyan)] blur-md animate-ping' : 'bg-[var(--color-arc-muted)] opacity-20'}`} />
          </div>
        </div>
      </div>
      
      <div className="mt-12 text-center font-mono">
        <p className={`text-sm tracking-[0.2em] uppercase ${isConnected ? 'text-[var(--color-arc-cyan)]' : 'text-[var(--color-arc-muted)]'}`}>
          {isConnected ? 'System Online' : 'System Offline'}
        </p>
        <p className="text-xs text-[var(--color-arc-muted)] mt-2 opacity-70">
          Voice Interface Standby
        </p>
      </div>
    </div>
  );
};
