import React from 'react';
import { Target, Zap, CheckCircle2, Layers, Compass, HelpCircle } from 'lucide-react';

const INTENT_BADGES = {
  exam_schedule: { label: 'Exam Schedule', color: 'bg-indigo-500/20 text-indigo-300 border-indigo-500/40' },
  classroom_location: { label: 'Classroom & Directions', color: 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40' },
  timetable: { label: 'Class Timetable', color: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40' },
  faculty_info: { label: 'Faculty & Office Hours', color: 'bg-blue-500/20 text-blue-300 border-blue-500/40' },
  notices_announcements: { label: 'Notices & Bulletins', color: 'bg-amber-500/20 text-amber-300 border-amber-500/40' },
  assignment_deadline: { label: 'Assignment Deadlines', color: 'bg-pink-500/20 text-pink-300 border-pink-500/40' },
  campus_events: { label: 'Events & Hackathons', color: 'bg-purple-500/20 text-purple-300 border-purple-500/40' },
  library_info: { label: 'Library Information', color: 'bg-teal-500/20 text-teal-300 border-teal-500/40' },
  campus_facilities: { label: 'Campus Facilities', color: 'bg-orange-500/20 text-orange-300 border-orange-500/40' },
  greeting_or_help: { label: 'Greeting & Assistance', color: 'bg-slate-500/20 text-slate-300 border-slate-500/40' },
  general_campus: { label: 'Campus Q&A', color: 'bg-violet-500/20 text-violet-300 border-violet-500/40' },
};

export default function IntentHUD({ currentIntent, confidence, entities, turnCount, isClarifying }) {
  const badge = INTENT_BADGES[currentIntent] || {
    label: currentIntent || 'Awaiting Speech',
    color: 'bg-slate-800 text-slate-400 border-slate-700'
  };

  return (
    <div className="w-full glass-panel-glow rounded-xl p-3.5 border border-indigo-500/20 text-xs">
      <div className="flex flex-wrap items-center justify-between gap-3">
        {/* Left: Active Intent */}
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-indigo-500/20 text-indigo-400">
            <Target className="w-4 h-4" />
          </div>
          <div>
            <div className="text-[10px] text-slate-400 uppercase font-semibold tracking-wider">
              Detected Intent
            </div>
            <div className="flex items-center gap-2 mt-0.5">
              <span className={`px-2.5 py-0.5 rounded-full font-semibold border ${badge.color}`}>
                {badge.label}
              </span>
              {isClarifying && (
                <span className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-amber-500/20 border border-amber-500/40 text-amber-300 font-medium">
                  <HelpCircle className="w-3 h-3" />
                  Clarification Required
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Center: Extracted Entities */}
        {entities && Object.keys(entities).length > 0 && (
          <div className="hidden sm:flex items-center gap-2 border-l border-slate-800 pl-3">
            <Layers className="w-3.5 h-3.5 text-cyan-400" />
            <span className="text-[10px] text-slate-400 uppercase font-semibold">Extracted:</span>
            <div className="flex flex-wrap gap-1.5">
              {Object.entries(entities).map(([key, val]) => (
                <span
                  key={key}
                  className="px-2 py-0.5 rounded bg-cyan-950/40 border border-cyan-500/30 text-cyan-300 font-mono text-[11px]"
                >
                  <strong className="text-slate-400">{key}:</strong> {String(val)}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Right: Confidence Score & Turn */}
        <div className="flex items-center gap-4">
          {confidence > 0 && (
            <div className="flex items-center gap-1.5">
              <Zap className="w-3.5 h-3.5 text-emerald-400" />
              <span className="text-slate-400">Confidence:</span>
              <span className="font-semibold text-emerald-300">
                {(confidence * 100).toFixed(0)}%
              </span>
            </div>
          )}

          <div className="flex items-center gap-1.5 text-slate-400">
            <Compass className="w-3.5 h-3.5 text-purple-400" />
            <span>Turn:</span>
            <span className="font-mono text-slate-200">#{turnCount}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
