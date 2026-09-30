import React from 'react';
import { Calendar, GraduationCap, Bell, BookOpen, Sparkles, Clock, CheckCircle } from 'lucide-react';

export default function QuickActions({ onSelectAction, disabled }) {
  const actions = [
    { label: "🎯 Demo: Physics Exam", query: "When is my Physics exam?", icon: Sparkles, color: "text-amber-300 border-amber-400/50 hover:border-amber-300 bg-amber-950/40 ring-1 ring-amber-400/30 font-semibold" },
    { label: "Today's timetable", query: "What is my timetable for today?", icon: Calendar, color: "text-cyan-400 border-cyan-500/30 hover:border-cyan-400 bg-cyan-950/20" },
    { label: "Upcoming exams", query: "When are my upcoming exams?", icon: GraduationCap, color: "text-indigo-400 border-indigo-500/30 hover:border-indigo-400 bg-indigo-950/20" },
    { label: "College notices", query: "What are the latest college notices?", icon: Bell, color: "text-amber-400 border-amber-500/30 hover:border-amber-400 bg-amber-950/20" },
    { label: "Library information", query: "Tell me about the central library hours and rules", icon: BookOpen, color: "text-emerald-400 border-emerald-500/30 hover:border-emerald-400 bg-emerald-950/20" },
    { label: "Upcoming events", query: "What events and hackathons are coming up?", icon: Sparkles, color: "text-purple-400 border-purple-500/30 hover:border-purple-400 bg-purple-950/20" },
    { label: "Assignments due", query: "When are my upcoming assignment deadlines?", icon: Clock, color: "text-pink-400 border-pink-500/30 hover:border-pink-400 bg-pink-950/20" },
  ];

  return (
    <div className="w-full flex items-center justify-center py-2 px-2">
      <div className="flex flex-wrap items-center justify-center gap-2 max-w-4xl">
        <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mr-1">
          Quick Actions:
        </span>
        {actions.map((act, index) => {
          const Icon = act.icon;
          return (
            <button
              key={index}
              disabled={disabled}
              onClick={() => onSelectAction(act.query)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium border transition-all duration-200 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer ${act.color}`}
            >
              <Icon className="w-3.5 h-3.5" />
              <span>{act.label}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
