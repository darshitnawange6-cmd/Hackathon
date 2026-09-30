import React from 'react';
import { Mic, MicOff, Square, Loader2, Sparkles } from 'lucide-react';

export default function MicrophoneButton({
  isListening,
  isLoading,
  isSpeaking,
  onToggleListen,
  onStopSpeech,
  interimTranscript
}) {
  const getButtonState = () => {
    if (isLoading) return 'loading';
    if (isListening) return 'listening';
    if (isSpeaking) return 'speaking';
    return 'idle';
  };

  const state = getButtonState();

  return (
    <div className="flex flex-col items-center justify-center my-3 relative">
      {/* Outer Glow Ring Layers */}
      <div className="relative flex items-center justify-center">
        {state === 'listening' && (
          <>
            <span className="absolute w-28 h-28 rounded-full bg-rose-500/20 animate-ping"></span>
            <span className="absolute w-36 h-36 rounded-full border border-rose-500/40 animate-pulse"></span>
            <span className="absolute w-44 h-44 rounded-full border border-purple-500/20"></span>
          </>
        )}

        {state === 'speaking' && (
          <>
            <span className="absolute w-28 h-28 rounded-full bg-cyan-500/20 animate-ping"></span>
            <span className="absolute w-36 h-36 rounded-full border border-cyan-500/30 animate-pulse"></span>
          </>
        )}

        {state === 'idle' && (
          <div className="absolute w-28 h-28 rounded-full bg-gradient-to-r from-indigo-500/10 via-cyan-500/10 to-purple-500/10 blur-xl"></div>
        )}

        {/* Central Hero Button */}
        <button
          onClick={state === 'speaking' ? onStopSpeech : onToggleListen}
          disabled={isLoading}
          aria-label={state === 'listening' ? 'Stop listening' : 'Start speaking'}
          className={`relative z-10 flex items-center justify-center w-20 h-20 sm:w-22 sm:h-22 rounded-full transition-all duration-300 transform active:scale-95 cursor-pointer shadow-2xl ${
            state === 'listening'
              ? 'bg-gradient-to-tr from-rose-600 via-pink-600 to-rose-500 text-white shadow-rose-600/50 scale-105'
              : state === 'speaking'
              ? 'bg-gradient-to-tr from-cyan-600 via-indigo-600 to-purple-600 text-white shadow-cyan-600/50 hover:opacity-90'
              : state === 'loading'
              ? 'bg-slate-800 text-cyan-400 border border-cyan-500/40 cursor-wait'
              : 'bg-gradient-to-tr from-indigo-600 via-purple-600 to-cyan-500 text-white shadow-indigo-600/40 hover:scale-105 hover:shadow-cyan-500/40'
          }`}
        >
          {state === 'loading' ? (
            <Loader2 className="w-9 h-9 animate-spin text-cyan-400" />
          ) : state === 'listening' ? (
            <Mic className="w-9 h-9 animate-pulse" />
          ) : state === 'speaking' ? (
            <Square className="w-8 h-8 fill-white" />
          ) : (
            <Mic className="w-9 h-9" />
          )}
        </button>
      </div>

      {/* Dynamic Status Text & Live Transcript Feed */}
      <div className="mt-4 text-center max-w-lg px-4">
        {state === 'listening' ? (
          <div>
            <div className="flex items-center justify-center gap-2 text-rose-400 font-semibold text-sm animate-pulse">
              <span className="w-2 h-2 rounded-full bg-rose-500"></span>
              Listening... Speak your campus question now
            </div>
            {interimTranscript && (
              <p className="mt-2 text-sm text-cyan-200 italic bg-cyan-950/40 border border-cyan-500/30 px-3 py-1.5 rounded-lg animate-fade-in shadow-inner">
                "{interimTranscript}"
              </p>
            )}
          </div>
        ) : state === 'loading' ? (
          <div className="flex items-center justify-center gap-2 text-cyan-400 font-medium text-sm">
            <Sparkles className="w-4 h-4 animate-spin text-cyan-400" />
            VocaGuide AI is analyzing intent & retrieving records...
          </div>
        ) : state === 'speaking' ? (
          <div className="flex items-center justify-center gap-2 text-cyan-300 font-medium text-sm">
            <span>Speaking aloud... Click button or square icon to stop audio</span>
          </div>
        ) : (
          <div className="flex flex-col items-center">
            <span className="text-sm font-semibold text-slate-200">
              Tap the microphone and speak naturally
            </span>
            <span className="text-xs text-slate-400 mt-0.5">
              or type your question in the text box below
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
