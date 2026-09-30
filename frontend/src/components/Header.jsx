import React from 'react';
import { Volume2, VolumeX, Sparkles, Database, PlayCircle, RefreshCw, Cpu, Radio, Terminal, Info } from 'lucide-react';

export default function Header({
  isMuted,
  onToggleMute,
  onClearChat,
  onOpenCampusHub,
  onOpenDemoScenarios,
  onOpenDocManager,
  onOpenDevDashboard,
  onOpenAbout,
  listeningStatus,
  isSpeaking,
  systemStatus
}) {
  return (
    <header className="w-full glass-panel border-b border-indigo-500/20 px-4 sm:px-8 py-3.5 sticky top-0 z-30 flex flex-wrap items-center justify-between gap-4">
      {/* Brand & Campus Identity */}
      <div className="flex items-center gap-3">
        <div className="relative flex items-center justify-center w-11 h-11 rounded-xl bg-gradient-to-tr from-indigo-600 via-purple-600 to-cyan-400 p-[1.5px] shadow-lg shadow-indigo-500/25">
          <div className="w-full h-full bg-[#0a0b12] rounded-[10px] flex items-center justify-center">
            <Radio className="w-6 h-6 text-cyan-400 animate-pulse" />
          </div>
          <span className="absolute -bottom-1 -right-1 flex h-3 w-3">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
          </span>
        </div>

        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold bg-gradient-to-r from-white via-indigo-100 to-cyan-300 bg-clip-text text-transparent tracking-tight">
              VocaGuide
            </h1>
            <span className="px-2 py-0.5 text-[10px] font-semibold tracking-wider uppercase rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
              AI Voice Assistant
            </span>
          </div>
          <p className="text-xs text-slate-400 font-medium">
            Nexus Institute of Technology <span className="text-slate-600">•</span> Fall 2026
          </p>
        </div>
      </div>

      {/* Dynamic Status Badges */}
      <div className="hidden md:flex items-center gap-2 text-xs">
        {/* Engine mode */}
        <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900/80 border border-slate-700/60 text-slate-300">
          <Cpu className="w-3.5 h-3.5 text-cyan-400" />
          <span className="text-slate-400">Engine:</span>
          <span className="font-semibold text-cyan-300">
            {systemStatus?.ai_engine?.is_demo_mode ? 'Grounded Engine' : 'Live Cloud LLM'}
          </span>
        </div>

        {/* Live Audio State */}
        {listeningStatus === 'listening' ? (
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-rose-500/20 border border-rose-500/40 text-rose-300 animate-pulse">
            <span className="w-2 h-2 rounded-full bg-rose-500 animate-ping"></span>
            <span className="font-semibold">Microphone Listening...</span>
          </div>
        ) : isSpeaking ? (
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-cyan-500/20 border border-cyan-500/40 text-cyan-300 animate-pulse">
            <Volume2 className="w-3.5 h-3.5 text-cyan-400 animate-bounce" />
            <span className="font-semibold">Speaking aloud...</span>
          </div>
        ) : (
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
            <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
            <span className="font-medium">Voice Ready</span>
          </div>
        )}
      </div>

      {/* Quick Action Controls */}
      <div className="flex items-center gap-2">
        {/* Document Vault (Supabase RAG) */}
        <button
          onClick={onOpenDocManager}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-cyan-950/40 hover:bg-cyan-900/50 border border-cyan-500/40 text-cyan-300 text-xs font-semibold transition-all cursor-pointer"
          title="Upload & Manage College Documents (PDF/TXT) in Supabase"
        >
          <Database className="w-3.5 h-3.5 text-cyan-400" />
          <span className="hidden sm:inline">Docs Vault</span>
        </button>

        {/* Hackathon Demo Presets */}
        <button
          onClick={onOpenDemoScenarios}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-gradient-to-r from-purple-600/30 to-indigo-600/30 hover:from-purple-600/50 hover:to-indigo-600/50 border border-purple-500/40 text-purple-200 text-xs font-semibold transition-all shadow-sm cursor-pointer"
          title="Judge Demo Scenarios (1-click presentation tests)"
        >
          <Sparkles className="w-3.5 h-3.5 text-purple-300" />
          <span className="hidden sm:inline">Demo Scenarios</span>
        </button>

        {/* Knowledge Explorer */}
        <button
          onClick={onOpenCampusHub}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700/80 border border-slate-700 text-slate-200 text-xs font-medium transition-all cursor-pointer"
          title="View Campus Knowledge Base (Exams, Notices, Timetable)"
        >
          <Database className="w-3.5 h-3.5 text-indigo-400" />
          <span className="hidden sm:inline">Campus Data</span>
        </button>

        {/* Developer Dashboard (Features 4 & 8) */}
        <button
          onClick={onOpenDevDashboard}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-cyan-950/50 hover:bg-cyan-900/60 border border-cyan-500/40 text-cyan-300 text-xs font-semibold transition-all cursor-pointer"
          title="Open Developer & Evaluator Dashboard (Intents, Latency, Telemetry)"
        >
          <Terminal className="w-3.5 h-3.5 text-cyan-400" />
          <span className="hidden md:inline">Dev Console</span>
        </button>

        {/* About & Architecture Modal (Section 5) */}
        <button
          onClick={onOpenAbout}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700/80 border border-slate-700 text-slate-300 text-xs font-medium transition-all cursor-pointer"
          title="Learn About VocaGuide, Problem, Solution & Architecture Flow"
        >
          <Info className="w-3.5 h-3.5 text-indigo-400" />
          <span className="hidden lg:inline">About</span>
        </button>


        {/* Audio Mute/Unmute */}
        <button
          onClick={onToggleMute}
          className={`p-2 rounded-lg border transition-all cursor-pointer ${
            isMuted
              ? 'bg-rose-500/10 border-rose-500/30 text-rose-400 hover:bg-rose-500/20'
              : 'bg-slate-800/80 border-slate-700 text-slate-300 hover:text-white hover:bg-slate-700'
          }`}
          title={isMuted ? 'Voice Responses Muted (Click to Unmute)' : 'Voice Responses Active (Click to Mute)'}
        >
          {isMuted ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
        </button>

        {/* Clear Conversation */}
        <button
          onClick={onClearChat}
          className="p-2 rounded-lg bg-slate-800/80 border border-slate-700 text-slate-300 hover:text-amber-400 hover:border-amber-500/40 hover:bg-amber-500/10 transition-all cursor-pointer"
          title="Clear Conversation History"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>
    </header>
  );
}
