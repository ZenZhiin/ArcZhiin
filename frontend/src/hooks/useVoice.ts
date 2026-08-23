import { useState, useRef, useCallback, useEffect } from 'react';

export type VoiceStatus = 'idle' | 'recording' | 'transcribing' | 'thinking' | 'speaking' | 'error';

export interface VoiceMessageData {
  id: string;
  type: 'transcription' | 'response' | 'error' | 'welcome';
  content: string;
  model?: string;
  tier?: string;
}

export const useVoice = () => {
  const [status, setStatus] = useState<VoiceStatus>('idle');
  const [isConnected, setIsConnected] = useState(false);
  const [lastTranscription, setLastTranscription] = useState('');
  const [lastResponse, setLastResponse] = useState('');

  const ws = useRef<WebSocket | null>(null);
  const mediaRecorder = useRef<MediaRecorder | null>(null);
  const audioChunks = useRef<Blob[]>([]);
  const reconnectAttempts = useRef(0);

  const connect = useCallback(() => {
    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/ws/voice`;
      ws.current = new WebSocket(wsUrl);

      ws.current.onopen = () => {
        setIsConnected(true);
        reconnectAttempts.current = 0;
      };

      ws.current.onmessage = (event) => {
        const data = JSON.parse(event.data);

        switch (data.type) {
          case 'transcription':
            setLastTranscription(data.content);
            setStatus('thinking');
            break;

          case 'status':
            if (data.content === 'transcribing') setStatus('transcribing');
            else if (data.content === 'thinking') setStatus('thinking');
            else if (data.content === 'speaking') setStatus('speaking');
            break;

          case 'response':
            setLastResponse(data.content);
            // We don't set 'speaking' here anymore, we wait for the 'audio' message
            break;

          case 'audio':
            setStatus('speaking');
            playAudio(data.data);
            break;

          case 'error':
            setLastResponse(data.content);
            setStatus('error');
            setTimeout(() => setStatus('idle'), 3000);
            break;

          case 'welcome':
            break;
        }
      };

      ws.current.onclose = () => {
        setIsConnected(false);
        setStatus('idle');
        if (reconnectAttempts.current < 5) {
          const timeout = Math.pow(2, reconnectAttempts.current) * 1000;
          setTimeout(connect, timeout);
          reconnectAttempts.current += 1;
        }
      };

      ws.current.onerror = () => {
        ws.current?.close();
      };
    } catch (error) {
      console.error('Voice WebSocket error:', error);
    }
  }, []);

  useEffect(() => {
    connect();
    return () => {
      ws.current?.close();
      mediaRecorder.current?.stop();
    };
  }, [connect]);

  const startRecording = useCallback(async () => {
    if (status !== 'idle' || !isConnected) return;

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          sampleRate: 16000,
          echoCancellation: true,
          noiseSuppression: true,
        },
      });

      audioChunks.current = [];
      const recorder = new MediaRecorder(stream, { mimeType: 'audio/webm;codecs=opus' });

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunks.current.push(event.data);
        }
      };

      recorder.onstop = () => {
        // Stop all tracks to release the mic
        stream.getTracks().forEach(track => track.stop());

        if (audioChunks.current.length > 0) {
          const audioBlob = new Blob(audioChunks.current, { type: 'audio/webm' });

          // Convert to WAV before sending (backend expects WAV/PCM)
          convertToWav(audioBlob).then(wavBlob => {
            if (ws.current?.readyState === WebSocket.OPEN) {
              ws.current.send(wavBlob);
              setStatus('transcribing');
            }
          });
        }
      };

      mediaRecorder.current = recorder;
      recorder.start();
      setStatus('recording');
    } catch (error) {
      console.error('Microphone access error:', error);
      setStatus('error');
      setTimeout(() => setStatus('idle'), 3000);
    }
  }, [status, isConnected]);

  const stopRecording = useCallback(() => {
    if (mediaRecorder.current?.state === 'recording') {
      mediaRecorder.current.stop();
    }
  }, []);

  const playAudio = useCallback((base64Data: string) => {
    try {
      const binaryString = atob(base64Data);
      const len = binaryString.length;
      const bytes = new Uint8Array(len);
      for (let i = 0; i < len; i++) {
        bytes[i] = binaryString.charCodeAt(i);
      }
      
      const blob = new Blob([bytes], { type: 'audio/wav' });
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      
      audio.onended = () => {
        setStatus('idle');
        URL.revokeObjectURL(url);
      };
      
      audio.onerror = () => {
        console.error('Audio playback error');
        setStatus('idle');
        URL.revokeObjectURL(url);
      };

      audio.play().catch(err => {
        console.error('Audio play blocked or failed:', err);
        setStatus('idle');
      });
    } catch (err) {
      console.error('Failed to decode audio:', err);
      setStatus('idle');
    }
  }, []);

  return {
    status,
    isConnected,
    lastTranscription,
    lastResponse,
    startRecording,
    stopRecording,
  };
};


/**
 * Convert a WebM audio blob to WAV format for the backend.
 * Uses the Web Audio API to decode and re-encode.
 */
const convertToWav = async (webmBlob: Blob): Promise<Blob> => {
  const arrayBuffer = await webmBlob.arrayBuffer();
  const audioContext = new AudioContext({ sampleRate: 16000 });

  try {
    const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
    const channelData = audioBuffer.getChannelData(0); // mono

    // Create WAV file
    const wavBuffer = encodeWav(channelData, 16000);
    return new Blob([wavBuffer], { type: 'audio/wav' });
  } finally {
    await audioContext.close();
  }
};

/**
 * Encode Float32Array PCM data as a WAV file.
 */
const encodeWav = (samples: Float32Array, sampleRate: number): ArrayBuffer => {
  const buffer = new ArrayBuffer(44 + samples.length * 2);
  const view = new DataView(buffer);

  // WAV header
  const writeString = (offset: number, str: string) => {
    for (let i = 0; i < str.length; i++) {
      view.setUint8(offset + i, str.charCodeAt(i));
    }
  };

  writeString(0, 'RIFF');
  view.setUint32(4, 36 + samples.length * 2, true);
  writeString(8, 'WAVE');
  writeString(12, 'fmt ');
  view.setUint32(16, 16, true);           // Subchunk1Size
  view.setUint16(20, 1, true);            // PCM format
  view.setUint16(22, 1, true);            // Mono
  view.setUint32(24, sampleRate, true);    // Sample rate
  view.setUint32(28, sampleRate * 2, true); // Byte rate
  view.setUint16(32, 2, true);            // Block align
  view.setUint16(34, 16, true);           // Bits per sample
  writeString(36, 'data');
  view.setUint32(40, samples.length * 2, true);

  // Convert float samples to 16-bit PCM
  for (let i = 0; i < samples.length; i++) {
    const s = Math.max(-1, Math.min(1, samples[i]));
    view.setInt16(44 + i * 2, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
  }

  return buffer;
};
