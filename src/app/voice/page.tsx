'use client';

import { useState, useEffect, useCallback } from 'react';
import Vapi from '@vapi-ai/web';

type CallStatus = 'idle' | 'connecting' | 'connected' | 'disconnecting';

export default function VoiceDemo() {
  const [vapi, setVapi] = useState<Vapi | null>(null);
  const [callStatus, setCallStatus] = useState<CallStatus>('idle');
  const [volumeLevel, setVolumeLevel] = useState(0);
  const [transcript, setTranscript] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isAssistantSpeaking, setIsAssistantSpeaking] = useState(false);
  const [liveTranscript, setLiveTranscript] = useState<string>('');
  const [waitingForResponse, setWaitingForResponse] = useState(false);
  const [hasReceivedFirstResponse, setHasReceivedFirstResponse] = useState(false);

  useEffect(() => {
    const publicKey = process.env.NEXT_PUBLIC_VAPI_PUBLIC_KEY || '135fdcab-d4e9-4729-ac09-a905d8793170';
    
    if (!publicKey) {
      setError('VAPI Public Key not configured. Please add NEXT_PUBLIC_VAPI_PUBLIC_KEY to environment variables.');
      return;
    }

    const vapiInstance = new Vapi(publicKey);

    vapiInstance.on('call-start', () => {
      setCallStatus('connected');
      setError(null);
      setWaitingForResponse(true);
    });

    vapiInstance.on('call-end', () => {
      setCallStatus('idle');
      setIsSpeaking(false);
      setIsAssistantSpeaking(false);
      setVolumeLevel(0);
      setLiveTranscript('');
      setWaitingForResponse(false);
      setHasReceivedFirstResponse(false);
    });

    vapiInstance.on('speech-start', () => {
      setIsSpeaking(true);
    });

    vapiInstance.on('speech-end', () => {
      setIsSpeaking(false);
    });

    vapiInstance.on('volume-level', (level: number) => {
      setVolumeLevel(level);
    });

    vapiInstance.on('message', (message: { type: string; transcript?: string; transcriptType?: string; role?: string }) => {
      if (message.type === 'transcript' && message.transcript) {
        const role = message.role === 'user' ? 'You' : 'SOMERA';
        
        if (message.transcriptType === 'final') {
          setTranscript(prev => [...prev, `${role}: ${message.transcript}`]);
          setLiveTranscript('');
          if (message.role === 'assistant') {
            setHasReceivedFirstResponse(true);
            setWaitingForResponse(false);
          } else if (message.role === 'user') {
            setWaitingForResponse(true);
          }
        } else {
          setLiveTranscript(`${role}: ${message.transcript}`);
        }
      }
      
      if (message.type === 'speech-update') {
        const speechMsg = message as { type: string; status?: string; role?: string };
        if (speechMsg.role === 'assistant') {
          const isStarted = speechMsg.status === 'started';
          setIsAssistantSpeaking(isStarted);
        }
        if (speechMsg.role === 'user') {
          if (speechMsg.status === 'ended') {
            setWaitingForResponse(true);
          } else if (speechMsg.status === 'started') {
            setWaitingForResponse(false);
          }
        }
      }
    });

    vapiInstance.on('error', (err: Error) => {
      console.error('VAPI Error:', err);
      const errorMsg = err?.message || '';
      
      // Empty error messages or common termination phrases are normal call endings
      const isNormalTermination = 
        !errorMsg ||
        errorMsg.toLowerCase().includes('ended') ||
        errorMsg.toLowerCase().includes('closed') ||
        errorMsg.toLowerCase().includes('disconnected') ||
        errorMsg.toLowerCase().includes('timeout') ||
        errorMsg.toLowerCase().includes('max duration') ||
        errorMsg.toLowerCase().includes('user') ||
        errorMsg.toLowerCase().includes('hangup') ||
        errorMsg.toLowerCase().includes('bye');
      
      if (!isNormalTermination) {
        setError(errorMsg);
      }
      setCallStatus('idle');
    });

    setVapi(vapiInstance);

    return () => {
      vapiInstance.stop();
    };
  }, []);

  const startCall = useCallback(async () => {
    if (!vapi) return;
    
    const assistantId = process.env.NEXT_PUBLIC_VAPI_ASSISTANT_ID || 'c09f6a3b-35d5-4e23-bd67-36299a4f44dd';
    
    if (!assistantId) {
      setError('VAPI Assistant ID not configured. Please add NEXT_PUBLIC_VAPI_ASSISTANT_ID to environment variables.');
      return;
    }

    setCallStatus('connecting');
    setTranscript([]);
    setError(null);

    try {
      await vapi.start(assistantId);
    } catch (err) {
      console.error('Failed to start call:', err);
      setError(err instanceof Error ? err.message : 'Failed to start call');
      setCallStatus('idle');
    }
  }, [vapi]);

  const endCall = useCallback(() => {
    if (!vapi) return;
    setCallStatus('disconnecting');
    vapi.stop();
  }, [vapi]);

  const toggleCall = useCallback(() => {
    if (callStatus === 'idle') {
      startCall();
    } else if (callStatus === 'connected') {
      endCall();
    }
  }, [callStatus, startCall, endCall]);

  const getButtonText = () => {
    switch (callStatus) {
      case 'connecting': return 'Connecting...';
      case 'connected': return 'End Call';
      case 'disconnecting': return 'Ending...';
      default: return 'Talk to SOMERA';
    }
  };

  const getButtonColor = () => {
    switch (callStatus) {
      case 'connecting':
      case 'disconnecting':
        return 'bg-yellow-500 hover:bg-yellow-600';
      case 'connected':
        return 'bg-red-500 hover:bg-red-600';
      default:
        return 'bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-900 via-purple-900/20 to-gray-900 flex flex-col items-center justify-center p-6">
      <div className="max-w-md w-full">
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold bg-gradient-to-r from-purple-400 via-pink-400 to-purple-400 bg-clip-text text-transparent mb-4">
            SOMERA
          </h1>
          <p className="text-gray-400 text-lg">
            Your Empathetic Coaching Companion
          </p>
          <p className="text-gray-500 text-sm mt-2">
            Voice Experience Demo
          </p>
        </div>

        <div className="relative flex flex-col items-center">
          <div className="relative mb-8">
            {callStatus === 'connecting' && (
              <>
                <div className="absolute inset-0 rounded-full bg-gradient-to-r from-purple-500/40 to-pink-500/40 animate-ping" style={{ animationDuration: '1.5s' }} />
                <div className="absolute inset-0 rounded-full bg-gradient-to-r from-purple-500/20 to-pink-500/20 animate-pulse" />
                <div 
                  className="absolute inset-0 rounded-full border-4 border-transparent border-t-purple-400 border-r-pink-400 animate-spin"
                  style={{ animationDuration: '1s' }}
                />
              </>
            )}

            <div 
              className={`absolute inset-0 rounded-full transition-all duration-300 ${
                callStatus === 'connected' 
                  ? 'bg-purple-500/30 animate-pulse' 
                  : ''
              }`}
              style={{
                transform: callStatus === 'connected' ? `scale(${1 + volumeLevel * 0.5})` : 'scale(1)',
                opacity: callStatus === 'connected' ? 0.6 : 0
              }}
            />
            
            {callStatus === 'connected' && (
              <>
                <div 
                  className="absolute inset-0 rounded-full bg-purple-400/20"
                  style={{
                    transform: `scale(${1.2 + volumeLevel * 0.3})`,
                    transition: 'transform 0.1s ease-out'
                  }}
                />
                <div 
                  className="absolute inset-0 rounded-full bg-pink-400/10"
                  style={{
                    transform: `scale(${1.4 + volumeLevel * 0.2})`,
                    transition: 'transform 0.15s ease-out'
                  }}
                />
              </>
            )}

            <button
              onClick={toggleCall}
              disabled={callStatus === 'connecting' || callStatus === 'disconnecting'}
              className={`relative w-40 h-40 rounded-full ${getButtonColor()} text-white font-semibold text-lg shadow-2xl transition-all duration-300 transform hover:scale-105 disabled:opacity-70 disabled:cursor-not-allowed disabled:transform-none flex items-center justify-center`}
            >
              <div className="flex flex-col items-center">
                {callStatus === 'idle' && (
                  <svg className="w-12 h-12 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                  </svg>
                )}
                {callStatus === 'connected' && (
                  <svg className="w-12 h-12 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                )}
                {(callStatus === 'connecting' || callStatus === 'disconnecting') && (
                  <div className="w-12 h-12 mb-2 border-4 border-white/30 border-t-white rounded-full animate-spin" />
                )}
                <span className="text-sm">{getButtonText()}</span>
              </div>
            </button>
          </div>

          {callStatus === 'connecting' && (
            <div className="text-center mb-6">
              <div className="flex items-center justify-center gap-2 text-purple-400 mb-2">
                <div className="flex gap-1">
                  <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                  <div className="w-2 h-2 bg-pink-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                  <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
              </div>
              <p className="text-purple-300 text-sm">Connecting to SOMERA...</p>
              <p className="text-gray-500 text-xs mt-1">Please allow microphone access</p>
            </div>
          )}

          {callStatus === 'connected' && (
            <div className="text-center mb-6 animate-fade-in">
              <div className="flex items-center justify-center gap-2 text-green-400 mb-2">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                <span className="text-sm font-medium">Connected</span>
              </div>
              {isAssistantSpeaking && (
                <p className="text-purple-300 text-sm">SOMERA is speaking...</p>
              )}
              {isSpeaking && !isAssistantSpeaking && (
                <p className="text-pink-300 text-sm">Listening to you...</p>
              )}
              {waitingForResponse && !isAssistantSpeaking && !isSpeaking && hasReceivedFirstResponse && (
                <div className="flex flex-col items-center">
                  <div className="flex gap-1 mb-1">
                    <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                    <div className="w-2 h-2 bg-pink-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                    <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                  </div>
                  <p className="text-yellow-300 text-sm">Preparing response...</p>
                </div>
              )}
              {!hasReceivedFirstResponse && !isAssistantSpeaking && (
                <div className="flex flex-col items-center p-4 bg-purple-500/10 border border-purple-500/30 rounded-xl">
                  <div className="flex gap-1.5 mb-2">
                    <div className="w-3 h-3 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                    <div className="w-3 h-3 bg-pink-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                    <div className="w-3 h-3 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                  </div>
                  <p className="text-yellow-300 text-sm font-medium">Initializing SOMERA...</p>
                  <p className="text-gray-400 text-xs mt-1">Please wait, first response loading</p>
                </div>
              )}
              {!isSpeaking && !isAssistantSpeaking && !waitingForResponse && hasReceivedFirstResponse && (
                <p className="text-gray-400 text-sm">Listening...</p>
              )}
            </div>
          )}

          {liveTranscript && callStatus === 'connected' && (
            <div className="w-full mb-4 p-3 bg-purple-900/30 rounded-lg border border-purple-500/30 animate-pulse">
              <p className={`text-sm italic ${liveTranscript.startsWith('You:') ? 'text-pink-300' : 'text-purple-300'}`}>
                {liveTranscript}...
              </p>
            </div>
          )}

          {transcript.length > 0 && (
            <div className="w-full mt-4 p-4 bg-gray-800/50 rounded-xl border border-gray-700/50 max-h-48 overflow-y-auto">
              <h3 className="text-xs text-gray-500 uppercase tracking-wider mb-2">Transcript</h3>
              <div className="space-y-2">
                {transcript.map((line, index) => (
                  <p 
                    key={index} 
                    className={`text-sm ${line.startsWith('You:') ? 'text-pink-300' : 'text-purple-300'}`}
                  >
                    {line}
                  </p>
                ))}
              </div>
            </div>
          )}

          {error && (
            <div className="w-full mt-4 p-4 bg-red-900/30 border border-red-700/50 rounded-xl">
              <p className="text-red-400 text-sm">{error}</p>
            </div>
          )}
        </div>

        <div className="mt-12 text-center">
          <p className="text-gray-600 text-xs">
            Powered by JoveHeal Wellness
          </p>
        </div>
      </div>
    </div>
  );
}
