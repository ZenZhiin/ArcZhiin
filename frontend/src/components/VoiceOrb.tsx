import type { VoiceStatus } from '../hooks/useVoice';

interface VoiceOrbProps {
  isConnected: boolean;
  status: VoiceStatus;
  lastTranscription: string;
  lastResponse: string;
  onTapStart: () => void;
  onTapStop: () => void;
}

const STATUS_LABELS: Record<VoiceStatus, string> = {
  idle: 'Tap to Speak',
  recording: 'Listening...',
  transcribing: 'Transcribing...',
  thinking: 'Thinking...',
  speaking: 'Speaking...',
  error: 'Error — Try Again',
};

export const VoiceOrb = ({
  isConnected,
  status,
  lastTranscription,
  lastResponse,
  onTapStart,
  onTapStop,
}: VoiceOrbProps) => {
  const isRecording = status === 'recording';
  const isProcessing = status === 'transcribing' || status === 'thinking';
  const isSpeaking = status === 'speaking';
  const isActive = isRecording || isProcessing || isSpeaking;

  const handleClick = () => {
    if (!isConnected) return;

    if (isRecording) {
      onTapStop();
    } else if (status === 'idle') {
      onTapStart();
    }
  };

  // Dynamic colors based on state
  const coreColor = isRecording
    ? 'from-red-500 to-red-600 shadow-[0_0_60px_rgba(239,68,68,0.6)]'
    : isProcessing
      ? 'from-amber-400 to-orange-500 shadow-[0_0_40px_rgba(251,191,36,0.5)]'
      : isSpeaking
        ? 'from-[var(--color-arc-cyan)] to-emerald-400 shadow-[0_0_50px_rgba(0,212,255,0.6)]'
        : isConnected
          ? 'from-[var(--color-arc-cyan)] to-[var(--color-arc-sky)] shadow-[0_0_40px_rgba(0,212,255,0.5)]'
          : '';

  const pingColor = isRecording
    ? 'bg-red-500'
    : isProcessing
      ? 'bg-amber-400'
      : isSpeaking
        ? 'bg-emerald-400'
        : 'bg-[var(--color-arc-cyan)]';

  return (
    <div className="flex flex-col items-center justify-center h-full w-full bg-[var(--color-arc-bg)] border-r border-[var(--color-arc-border)]">
      {/* Orb Container */}
      <button
        onClick={handleClick}
        disabled={!isConnected || isProcessing || isSpeaking}
        className="relative flex items-center justify-center w-64 h-64 cursor-pointer disabled:cursor-not-allowed focus:outline-none group"
        aria-label={STATUS_LABELS[status]}
      >
        {/* Outer Ring */}
        <div className={`absolute w-full h-full rounded-full border border-[var(--color-arc-border)] ${isActive ? 'animate-[spin_4s_linear_infinite]' : isConnected ? 'animate-[spin_10s_linear_infinite]' : ''}`}>
          <div className={`absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 w-2 h-2 rounded-full ${isConnected ? `${pingColor} shadow-[0_0_8px_currentColor]` : 'bg-[var(--color-arc-muted)]'}`} />
          <div className={`absolute bottom-0 left-1/2 -translate-x-1/2 translate-y-1/2 w-2 h-2 rounded-full ${isConnected ? `${pingColor} shadow-[0_0_8px_currentColor]` : 'bg-[var(--color-arc-muted)]'}`} />
        </div>

        {/* Middle Ring */}
        <div className={`absolute w-48 h-48 rounded-full border-2 border-dashed transition-all duration-500 ${
          isRecording
            ? 'border-red-500 animate-[spin_3s_linear_infinite_reverse] opacity-80'
            : isActive
              ? 'border-amber-400 animate-[spin_8s_linear_infinite_reverse] opacity-60'
              : isConnected
                ? 'border-[var(--color-arc-sky)] animate-[spin_15s_linear_infinite_reverse] opacity-50'
                : 'border-[var(--color-arc-muted)] opacity-20'
        }`} />

        {/* Inner Core */}
        <div className={`w-32 h-32 rounded-full flex items-center justify-center transition-all duration-300 ${
          isConnected
            ? `bg-gradient-to-br ${coreColor} ${isRecording ? 'scale-110' : ''} ${isActive ? 'animate-pulse' : ''}`
            : 'bg-[var(--color-arc-surface)] border border-[var(--color-arc-border)]'
        } group-hover:scale-105`}>
          <div className={`w-24 h-24 rounded-full bg-[var(--color-arc-bg)] flex items-center justify-center ${isConnected ? 'opacity-90' : ''}`}>
            {isRecording ? (
              /* Mic icon when recording */
              <div className="flex flex-col items-center gap-1">
                <div className="w-4 h-6 rounded-full border-2 border-red-400" />
                <div className="w-8 h-0.5 bg-red-400 rounded" />
              </div>
            ) : (
              <div className={`w-12 h-12 rounded-full transition-all duration-300 ${
                isConnected
                  ? `${pingColor} blur-md ${isActive ? 'animate-ping' : 'animate-pulse'}`
                  : 'bg-[var(--color-arc-muted)] opacity-20'
              }`} />
            )}
          </div>
        </div>
      </button>

      {/* Status Text */}
      <div className="mt-10 text-center font-mono max-w-xs px-4">
        <p className={`text-sm tracking-[0.2em] uppercase transition-colors duration-300 ${
          isRecording ? 'text-red-400' :
          isProcessing ? 'text-amber-400' :
          isSpeaking ? 'text-emerald-400' :
          isConnected ? 'text-[var(--color-arc-cyan)]' :
          'text-[var(--color-arc-muted)]'
        }`}>
          {isConnected ? STATUS_LABELS[status] : 'System Offline'}
        </p>

        {/* Show transcription or response */}
        {lastTranscription && (status === 'thinking' || status === 'speaking') && (
          <p className="text-xs text-[var(--color-arc-muted)] mt-3 italic animate-fade-in">
            "{lastTranscription}"
          </p>
        )}
        {lastResponse && status === 'speaking' && (
          <p className="text-xs text-[var(--color-arc-text)] mt-2 leading-relaxed animate-fade-in line-clamp-3">
            {lastResponse}
          </p>
        )}
      </div>
    </div>
  );
};
