import React, { useEffect, useRef } from 'react';
import { Bot, User, Volume2, VolumeX, Copy, Check, Sparkles, CornerDownRight } from 'lucide-react';

export default function ChatWindow({
  messages,
  isLoading,
  currentSpokenMessageId,
  isSpeaking,
  onReplayAudio,
  onStopAudio,
  onSelectSuggestion,
}) {
  const scrollRef = useRef(null);
  const [copiedId, setCopiedId] = React.useState(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isLoading]);

  const copyToClipboard = (id, text) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  // Helper to format basic markdown to HTML safely
  const formatMarkdown = (text) => {
    if (!text) return '';
    // Format headers
    let html = text
      .replace(/^### (.*$)/gim, '<h3 class="text-base font-bold text-cyan-300 mt-2 mb-1">$1</h3>')
      .replace(/^## (.*$)/gim, '<h2 class="text-lg font-bold text-white mt-2 mb-1">$1</h2>')
      .replace(/^# (.*$)/gim, '<h1 class="text-xl font-bold text-white mt-2 mb-1">$1</h1>')
      .replace(/\*\*(.*?)\*\*/g, '<strong class="text-indigo-200 font-semibold">$1</strong>')
      .replace(/\*(.*?)\*/g, '<em class="text-slate-300 italic">$1</em>')
      .replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_blank" rel="noreferrer" class="text-cyan-400 underline hover:text-cyan-300">$1</a>');

    // Format list items
    const lines = html.split('\n');
    const formattedLines = lines.map((line) => {
      if (line.trim().startsWith('- ')) {
        return `<div class="flex items-start gap-2 my-1"><span class="text-cyan-400 mt-1">•</span><span>${line.trim().substring(2)}</span></div>`;
      }
      return line ? `<div class="my-0.5">${line}</div>` : '<div class="h-2"></div>';
    });

    return formattedLines.join('');
  };

  return (
    <div
      ref={scrollRef}
      className="flex-1 w-full overflow-y-auto px-4 py-4 space-y-4 max-w-4xl mx-auto"
    >
      {/* Empty State Welcome */}
      {messages.length === 0 && (
        <div className="flex flex-col items-center justify-center min-h-[300px] text-center px-4 py-8">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-cyan-500/20 via-indigo-500/20 to-purple-500/20 border border-cyan-500/30 flex items-center justify-center mb-4 shadow-lg shadow-cyan-500/10">
            <Sparkles className="w-8 h-8 text-cyan-400 animate-pulse" />
          </div>
          <h2 className="text-2xl font-bold text-white tracking-tight">
            Speak naturally. Ask anything about your campus.
          </h2>
          <p className="text-slate-400 text-sm max-w-md mt-2">
            Ask about exam schedules, classrooms, daily timetables, professor office hours, or college notices using voice or text.
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-6 w-full max-w-lg">
            {[
              "When is my physics exam?",
              "What classroom is it in?",
              "What is my timetable for today?",
              "Are there any college notices?"
            ].map((starter, idx) => (
              <button
                key={idx}
                onClick={() => onSelectSuggestion(starter)}
                className="px-3 py-2 text-xs rounded-xl bg-slate-900/60 hover:bg-slate-800 border border-slate-800 hover:border-indigo-500/40 text-slate-300 hover:text-white transition-all text-left flex items-center gap-2 cursor-pointer"
              >
                <CornerDownRight className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
                <span className="truncate">{starter}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Message Stream */}
      {messages.map((msg) => {
        const isUser = msg.role === 'user';
        const isPlayingThis = currentSpokenMessageId === msg.id && isSpeaking;

        return (
          <div
            key={msg.id}
            className={`flex items-start gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'} animate-fade-in`}
          >
            {/* Avatar */}
            <div
              className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 border ${
                isUser
                  ? 'bg-gradient-to-tr from-indigo-600 to-purple-600 border-indigo-400/40 text-white shadow-md'
                  : 'bg-gradient-to-tr from-slate-900 to-indigo-950 border-cyan-500/30 text-cyan-400 shadow-md'
              }`}
            >
              {isUser ? <User className="w-5 h-5" /> : <Bot className="w-5 h-5" />}
            </div>

            {/* Bubble Container */}
            <div className={`flex flex-col max-w-[85%] sm:max-w-[75%] ${isUser ? 'items-end' : 'items-start'}`}>
              <div
                className={`relative px-4 py-3 rounded-2xl text-sm leading-relaxed ${
                  isUser
                    ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white shadow-lg shadow-indigo-600/20 rounded-tr-sm'
                    : 'glass-panel-glow border border-slate-700/80 text-slate-200 rounded-tl-sm shadow-xl'
                }`}
              >
                {/* User Message */}
                {isUser ? (
                  <div>
                    <p className="whitespace-pre-wrap">{msg.content}</p>
                    {msg.isVoice && (
                      <span className="inline-flex items-center gap-1 mt-1 text-[10px] text-indigo-200 font-medium">
                        🎤 Voice input
                      </span>
                    )}
                  </div>
                ) : (
                  /* Assistant Message */
                  <div>
                    {msg.actionExecuted && (
                      <div className="mb-2 inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-emerald-500/15 border border-emerald-500/30 text-emerald-300 text-xs font-semibold">
                        <Check className="w-3.5 h-3.5 text-emerald-400" />
                        <span>Tool Action: {msg.actionExecuted}</span>
                      </div>
                    )}

                    <div
                      className="markdown-content space-y-1"
                      dangerouslySetInnerHTML={{ __html: formatMarkdown(msg.content) }}
                    />
                    {msg.isStreaming && (
                      <span className="inline-block w-2 h-4 ml-1 bg-cyan-400 animate-pulse align-middle" />
                    )}

                    {/* Source Transparency Details (Feature 6) */}
                    {msg.sourceDetails && msg.sourceDetails.length > 0 ? (
                      <div className="mt-2.5 pt-2 border-t border-slate-800/80 space-y-1.5">
                        <div className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider flex items-center gap-1">
                          <span>📚 Grounded Sources ({msg.sourceDetails.length}):</span>
                        </div>
                        <div className="flex flex-wrap gap-1.5">
                          {msg.sourceDetails.map((src, sIdx) => (
                            <div
                              key={sIdx}
                              className="px-2.5 py-1 rounded-lg bg-slate-900/90 border border-indigo-500/30 text-[11px] space-y-0.5"
                            >
                              <div className="font-semibold text-cyan-300">{src.document_name}</div>
                              <div className="flex items-center gap-2 text-[10px] text-slate-400">
                                <span className="text-indigo-300 font-mono">[{src.category}]</span>
                                <span>•</span>
                                <span>{src.section}</span>
                                <span>•</span>
                                <span>{src.date}</span>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    ) : msg.sources && msg.sources.length > 0 ? (
                      <div className="mt-2.5 pt-2 border-t border-slate-800/80 flex flex-wrap items-center gap-1.5 text-[11px] text-slate-400">
                        <span className="font-semibold text-slate-500 uppercase tracking-wider flex items-center gap-1">
                          📚 Source:
                        </span>
                        {msg.sources.map((src, sIdx) => (
                          <span
                            key={sIdx}
                            className="px-2 py-0.5 rounded bg-slate-900/90 border border-indigo-500/30 text-cyan-300 font-mono text-[10.5px]"
                          >
                            {src}
                          </span>
                        ))}
                      </div>
                    ) : null}

                    {/* Spoken Text Audio Preview Banner if distinct */}
                    {msg.spokenText && (
                      <div className="mt-3 pt-2.5 border-t border-slate-800 flex items-center justify-between gap-2 text-xs">
                        <div className="flex items-center gap-1.5 text-cyan-300/90 font-medium italic">

                          <Volume2 className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
                          <span className="line-clamp-1">"{msg.spokenText}"</span>
                        </div>

                        {/* Controls */}
                        <div className="flex items-center gap-1 shrink-0">
                          <button
                            onClick={() => (isPlayingThis ? onStopAudio() : onReplayAudio(msg))}
                            className={`p-1.5 rounded-lg border text-xs flex items-center gap-1 transition-all cursor-pointer ${
                              isPlayingThis
                                ? 'bg-cyan-500/20 border-cyan-400 text-cyan-300'
                                : 'bg-slate-800/80 hover:bg-slate-700 border-slate-700 text-slate-300'
                            }`}
                            title={isPlayingThis ? 'Stop Audio' : 'Play / Replay Voice'}
                          >
                            {isPlayingThis ? (
                              <VolumeX className="w-3.5 h-3.5 text-cyan-400" />
                            ) : (
                              <Volume2 className="w-3.5 h-3.5" />
                            )}
                          </button>

                          <button
                            onClick={() => copyToClipboard(msg.id, msg.content)}
                            className="p-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700 border border-slate-700 text-slate-300 transition-all cursor-pointer"
                            title="Copy response"
                          >
                            {copiedId === msg.id ? (
                              <Check className="w-3.5 h-3.5 text-emerald-400" />
                            ) : (
                              <Copy className="w-3.5 h-3.5" />
                            )}
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Timestamp & Metadata Footer */}
              <div className="flex items-center gap-2 mt-1 px-1 text-[11px] text-slate-500">
                <span>{msg.timestamp || 'Just now'}</span>
                {msg.intent && (
                  <>
                    <span>•</span>
                    <span className="text-indigo-400 font-mono text-[10px]">
                      {msg.intent}
                    </span>
                  </>
                )}
              </div>

              {/* Follow-up suggestions */}
              {!isUser && msg.followUps && msg.followUps.length > 0 && (
                <div className="flex flex-wrap gap-1.5 mt-2.5">
                  {msg.followUps.map((suggestion, sIdx) => (
                    <button
                      key={sIdx}
                      onClick={() => onSelectSuggestion(suggestion)}
                      className="px-2.5 py-1 rounded-full text-xs bg-slate-800/90 hover:bg-indigo-950/70 border border-slate-700 hover:border-indigo-500/50 text-indigo-300 transition-all flex items-center gap-1 active:scale-95 cursor-pointer"
                    >
                      <Sparkles className="w-3 h-3 text-cyan-400" />
                      <span>{suggestion}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        );
      })}

      {/* Loading Skeleton */}
      {isLoading && (
        <div className="flex items-start gap-3 animate-fade-in">
          <div className="w-9 h-9 rounded-xl bg-slate-900 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
            <Bot className="w-5 h-5 animate-pulse" />
          </div>
          <div className="glass-panel px-4 py-3 rounded-2xl rounded-tl-sm border border-slate-800 flex items-center gap-2 text-sm text-slate-400">
            <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping"></span>
            <span className="w-2 h-2 rounded-full bg-indigo-400 animate-ping delay-100"></span>
            <span className="w-2 h-2 rounded-full bg-purple-400 animate-ping delay-200"></span>
            <span className="ml-1 text-xs text-slate-400">VocaGuide is composing answer...</span>
          </div>
        </div>
      )}
    </div>
  );
}
