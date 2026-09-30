import React, { useState } from 'react';
import { Send, Mic, Sparkles } from 'lucide-react';

export default function InputBar({
  onSendMessage,
  disabled,
  isListening,
  onToggleListen,
}) {
  const [text, setText] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    const trimmed = text.trim();
    if (!trimmed || disabled) return;
    onSendMessage(trimmed, false);
    setText('');
  };

  return (
    <div className="w-full max-w-4xl mx-auto px-4 pb-4">
      <form
        onSubmit={handleSubmit}
        className="relative flex items-center glass-panel-glow rounded-2xl border border-indigo-500/30 p-1.5 focus-within:border-cyan-400/70 transition-all shadow-xl"
      >
        {/* Mic shortcut icon */}
        <button
          type="button"
          onClick={onToggleListen}
          className={`p-2.5 rounded-xl transition-all cursor-pointer ${
            isListening
              ? 'bg-rose-500/20 text-rose-400 animate-pulse'
              : 'text-slate-400 hover:text-cyan-400 hover:bg-slate-800/60'
          }`}
          title={isListening ? 'Stop listening' : 'Start microphone'}
        >
          <Mic className="w-5 h-5" />
        </button>

        {/* Text Input */}
        <input
          type="text"
          value={text}
          onChange={(e) => setText(e.target.value)}
          disabled={disabled}
          placeholder="Ask anything about exams, timetable, classrooms, notices..."
          className="flex-1 bg-transparent border-none px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-0 disabled:opacity-50"
        />

        {/* Send Button */}
        <button
          type="submit"
          disabled={!text.trim() || disabled}
          className="p-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-cyan-500 hover:from-indigo-500 hover:to-cyan-400 text-white font-medium disabled:opacity-30 disabled:cursor-not-allowed transition-all transform active:scale-95 shadow-md shadow-indigo-600/20 cursor-pointer"
          title="Send Question"
        >
          <Send className="w-4 h-4" />
        </button>
      </form>
    </div>
  );
}
