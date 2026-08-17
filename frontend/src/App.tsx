import { useEffect, useRef } from 'react';
import { useWebSocket } from './hooks/useWebSocket';
import { StatusBar } from './components/StatusBar';
import { VoiceOrb } from './components/VoiceOrb';
import { ChatMessage } from './components/ChatMessage';
import { ChatInput } from './components/ChatInput';

const App = () => {
  const { messages, isConnected, isThinking, sessionId, sendMessage, clearContext } = useWebSocket();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isThinking]);

  return (
    <div className="flex flex-col h-screen w-screen bg-[var(--color-arc-bg)] text-[var(--color-arc-text)] font-sans overflow-hidden">
      <StatusBar isConnected={isConnected} sessionId={sessionId} messages={messages} />
      
      <div className="flex flex-col md:flex-row flex-1 mt-14 overflow-hidden">
        {/* Left Panel: Voice Orb */}
        <div className="hidden md:flex md:w-[40%] h-full relative z-10 bg-[var(--color-arc-bg)]">
          <VoiceOrb isConnected={isConnected} />
        </div>
        
        {/* Right Panel: Chat Interface */}
        <div className="flex flex-col w-full md:w-[60%] h-full relative z-20 shadow-[-10px_0_30px_rgba(0,0,0,0.5)]">
          <div className="flex-1 overflow-y-auto p-6 scroll-smooth">
            {messages.map(msg => (
              <ChatMessage key={msg.id} message={msg} />
            ))}
            
            {isThinking && (
              <div className="flex justify-start my-4 animate-fade-in">
                <div className="bg-[#181824] rounded-xl rounded-bl-none p-4 border-l-2 border-l-[var(--color-arc-cyan)] shadow-[-4px_0_15px_rgba(0,212,255,0.05)]">
                  <div className="flex gap-1.5 items-center h-5">
                    <div className="w-2 h-2 rounded-full bg-[var(--color-arc-cyan)] animate-bounce" style={{ animationDelay: '0ms' }} />
                    <div className="w-2 h-2 rounded-full bg-[var(--color-arc-cyan)] animate-bounce" style={{ animationDelay: '150ms' }} />
                    <div className="w-2 h-2 rounded-full bg-[var(--color-arc-cyan)] animate-bounce" style={{ animationDelay: '300ms' }} />
                  </div>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>
          
          <ChatInput 
            onSendMessage={sendMessage} 
            onClearContext={clearContext}
            isThinking={isThinking}
          />
        </div>
      </div>
    </div>
  );
};

export default App;
