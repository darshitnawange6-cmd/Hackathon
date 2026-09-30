import React from 'react';
import { 
  X, Sparkles, CheckCircle2, Cpu, Database, Volume2, ShieldCheck, 
  Layers, Zap, Terminal, ArrowRight, BookOpen, Clock, AlertTriangle 
} from 'lucide-react';

export default function AboutModal({ isOpen, onClose }) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-black/85 backdrop-blur-md animate-fade-in">
      <div className="relative w-full max-w-4xl h-[92vh] max-h-[850px] flex flex-col rounded-2xl bg-[#090b14] border border-indigo-500/40 shadow-2xl shadow-indigo-500/20 overflow-hidden text-slate-200">
        
        {/* Header */}
        <div className="px-6 py-4 bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 border-b border-indigo-500/30 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-cyan-500 p-0.5 shadow-lg shadow-indigo-500/30 flex items-center justify-center">
              <div className="w-full h-full bg-[#0a0b12] rounded-[10px] flex items-center justify-center">
                <Sparkles className="w-5 h-5 text-cyan-400 animate-pulse" />
              </div>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-bold text-white tracking-tight">About VocaGuide</h2>
                <span className="px-2 py-0.5 text-[10px] font-mono uppercase bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 rounded-full font-bold">
                  College AI Assistant
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Voice-First Conversational Intelligence for College Campuses
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition-all cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Scrollable Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6 text-xs sm:text-sm">
          
          {/* 1. Problem & Solution Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Problem */}
            <div className="p-4 rounded-xl bg-rose-950/20 border border-rose-500/30 space-y-2">
              <div className="flex items-center gap-2 text-rose-400 font-bold text-sm">
                <AlertTriangle className="w-4 h-4" />
                <span>The Problem on College Campuses</span>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed">
                Students navigate fragmented academic portals, buried PDFs, outdated pinboards, and disconnected bulletin circulars. Simple questions like <em>"Where is my exam?"</em>, <em>"Are calculators allowed?"</em>, or <em>"What classes do I have tomorrow?"</em> require digging through 20-page handbooks and multiple logins.
              </p>
            </div>

            {/* Solution */}
            <div className="p-4 rounded-xl bg-emerald-950/20 border border-emerald-500/30 space-y-2">
              <div className="flex items-center gap-2 text-emerald-400 font-bold text-sm">
                <CheckCircle2 className="w-4 h-4" />
                <span>The VocaGuide Solution</span>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed">
                VocaGuide is a voice-first, AI-powered campus assistant that operates through natural conversational speech. It answers questions instantly, resolves pronoun follow-ups (<em>"it"</em>, <em>"that"</em>), grounds every response with source document citations, and executes automated study actions (reminders, timetable views) with zero latency.
              </p>
            </div>
          </div>

          {/* 2. Visual Architecture Diagram */}
          <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-cyan-300 uppercase tracking-wider flex items-center gap-1.5">
                <Layers className="w-4 h-4" />
                System Architecture & Interaction Flow
              </span>
              <span className="text-[10px] font-mono text-slate-400">End-to-End Pipeline</span>
            </div>

            {/* Architecture Flow Diagram */}
            <div className="p-4 rounded-xl bg-[#07080e] border border-slate-800/80 overflow-x-auto">
              <div className="flex items-center justify-between min-w-[620px] gap-2 text-center text-xs">
                {/* Step 1 */}
                <div className="flex-1 p-2.5 rounded-xl bg-slate-900 border border-indigo-500/30">
                  <div className="p-1 rounded bg-indigo-500/20 text-indigo-400 w-fit mx-auto mb-1">
                    <Volume2 className="w-4 h-4" />
                  </div>
                  <div className="font-bold text-white text-[11px]">1. Voice / Speech</div>
                  <div className="text-[10px] text-slate-400 mt-0.5">Web Speech STT (Interim + Final)</div>
                </div>

                <ArrowRight className="w-4 h-4 text-slate-600 shrink-0" />

                {/* Step 2 */}
                <div className="flex-1 p-2.5 rounded-xl bg-slate-900 border border-cyan-500/30">
                  <div className="p-1 rounded bg-cyan-500/20 text-cyan-400 w-fit mx-auto mb-1">
                    <Cpu className="w-4 h-4" />
                  </div>
                  <div className="font-bold text-white text-[11px]">2. Context & Intent</div>
                  <div className="text-[10px] text-slate-400 mt-0.5">Pronoun & Multi-turn Memory</div>
                </div>

                <ArrowRight className="w-4 h-4 text-slate-600 shrink-0" />

                {/* Step 3 */}
                <div className="flex-1 p-2.5 rounded-xl bg-slate-900 border border-purple-500/30">
                  <div className="p-1 rounded bg-purple-500/20 text-purple-400 w-fit mx-auto mb-1">
                    <Database className="w-4 h-4" />
                  </div>
                  <div className="font-bold text-white text-[11px]">3. Hybrid RAG</div>
                  <div className="text-[10px] text-slate-400 mt-0.5">Supabase Vector + SQLite Core</div>
                </div>

                <ArrowRight className="w-4 h-4 text-slate-600 shrink-0" />

                {/* Step 4 */}
                <div className="flex-1 p-2.5 rounded-xl bg-slate-900 border border-emerald-500/30">
                  <div className="p-1 rounded bg-emerald-500/20 text-emerald-400 w-fit mx-auto mb-1">
                    <Zap className="w-4 h-4" />
                  </div>
                  <div className="font-bold text-white text-[11px]">4. Grounded Synthesis</div>
                  <div className="text-[10px] text-slate-400 mt-0.5">SSE Stream + Source Citations</div>
                </div>

                <ArrowRight className="w-4 h-4 text-slate-600 shrink-0" />

                {/* Step 5 */}
                <div className="flex-1 p-2.5 rounded-xl bg-slate-900 border border-pink-500/30">
                  <div className="p-1 rounded bg-pink-500/20 text-pink-400 w-fit mx-auto mb-1">
                    <Volume2 className="w-4 h-4" />
                  </div>
                  <div className="font-bold text-white text-[11px]">5. Voice Out</div>
                  <div className="text-[10px] text-slate-400 mt-0.5">TTS Aloud + Barge-In Interruption</div>
                </div>
              </div>
            </div>
          </div>

          {/* 3. Key Features Grid */}
          <div className="space-y-3">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block">
              Core Capabilities & Innovations
            </span>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
              {[
                {
                  title: 'Natural Pronoun Resolution',
                  desc: 'Understands "Where is it?", "What do I need to bring?", and "Remind me tomorrow" using conversational state.',
                  icon: Layers,
                  color: 'text-cyan-400'
                },
                {
                  title: 'Instant Voice Interruption',
                  desc: 'Barge-in technology: speaking stops immediately when the user starts speaking, transitioning to listening with zero delay.',
                  icon: Zap,
                  color: 'text-rose-400'
                },
                {
                  title: 'Real-Time SSE Streaming',
                  desc: 'FastAPI Server-Sent Events progressive token streaming gives typewriter UI responses in real time.',
                  icon: Terminal,
                  color: 'text-indigo-400'
                },
                {
                  title: 'Source Transparency',
                  desc: 'Every answer is grounded with document name, category, term date, and section citations without exposing prompts.',
                  icon: BookOpen,
                  color: 'text-emerald-400'
                },
                {
                  title: 'Student Study Action Tools',
                  desc: 'Built-in action tools execute personal reminder creation, timetable viewing, and notice alerts automatically.',
                  icon: Clock,
                  color: 'text-amber-400'
                },
                {
                  title: 'Zero-Key Offline Resilience',
                  desc: '3-tier fallback chain guarantees 100% presentation uptime locally even if external cloud APIs or Wi-Fi are disconnected.',
                  icon: ShieldCheck,
                  color: 'text-purple-400'
                }
              ].map((feat, i) => {
                const Icon = feat.icon;
                return (
                  <div key={i} className="p-3.5 rounded-xl bg-slate-900/50 border border-slate-800 space-y-1.5">
                    <div className="flex items-center gap-2 font-bold text-white text-xs">
                      <Icon className={`w-4 h-4 ${feat.color}`} />
                      <span>{feat.title}</span>
                    </div>
                    <p className="text-[11px] text-slate-400 leading-normal">{feat.desc}</p>
                  </div>
                );
              })}
            </div>
          </div>

          {/* 4. Technology Stack */}
          <div className="p-4 rounded-xl bg-slate-900/40 border border-slate-800 space-y-2">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block">
              Technology Stack
            </span>
            <div className="flex flex-wrap gap-2 text-xs">
              <span className="px-2.5 py-1 rounded-lg bg-slate-800 text-cyan-300 border border-cyan-500/30 font-mono">
                FastAPI (Python 3.14)
              </span>
              <span className="px-2.5 py-1 rounded-lg bg-slate-800 text-indigo-300 border border-indigo-500/30 font-mono">
                React 18 + Vite
              </span>
              <span className="px-2.5 py-1 rounded-lg bg-slate-800 text-emerald-300 border border-emerald-500/30 font-mono">
                Supabase (PostgreSQL + Vectors)
              </span>
              <span className="px-2.5 py-1 rounded-lg bg-slate-800 text-purple-300 border border-purple-500/30 font-mono">
                Web Speech API (STT / TTS)
              </span>
              <span className="px-2.5 py-1 rounded-lg bg-slate-800 text-pink-300 border border-pink-500/30 font-mono">
                SQLite 3 Local Fallback
              </span>
              <span className="px-2.5 py-1 rounded-lg bg-slate-800 text-amber-300 border border-amber-500/30 font-mono">
                Tailwind CSS
              </span>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-3 bg-slate-950 border-t border-slate-800 flex items-center justify-between text-xs text-slate-500">
          <span>Nexus Institute of Technology • Hackathon Presentation Edition</span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold transition-all cursor-pointer"
          >
            Start Exploring
          </button>
        </div>
      </div>
    </div>
  );
}
