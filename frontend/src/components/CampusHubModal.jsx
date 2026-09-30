import React, { useState, useEffect } from 'react';
import { X, GraduationCap, Calendar, Users, Bell, Sparkles, Building, BookOpen, MessageSquare, Loader2 } from 'lucide-react';
import { apiService } from '../services/apiService';

export default function CampusHubModal({ isOpen, onClose, onAskAbout }) {
  const [activeTab, setActiveTab] = useState('exams');
  const [data, setData] = useState({
    exams: [],
    timetable: [],
    faculty: [],
    notices: [],
    events: [],
    facilities: [],
    library: {}
  });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen) {
      loadCategoryData(activeTab);
    }
  }, [isOpen, activeTab]);

  const loadCategoryData = async (tab) => {
    setLoading(true);
    try {
      if (tab === 'exams' && data.exams.length === 0) {
        const res = await apiService.getCampusData('exams');
        setData((prev) => ({ ...prev, exams: res }));
      } else if (tab === 'timetable' && data.timetable.length === 0) {
        const res = await apiService.getCampusData('timetable');
        setData((prev) => ({ ...prev, timetable: res }));
      } else if (tab === 'faculty' && data.faculty.length === 0) {
        const res = await apiService.getCampusData('faculty');
        setData((prev) => ({ ...prev, faculty: res }));
      } else if (tab === 'notices' && data.notices.length === 0) {
        const res = await apiService.getCampusData('notices');
        setData((prev) => ({ ...prev, notices: res }));
      } else if (tab === 'events' && data.events.length === 0) {
        const res = await apiService.getCampusData('events');
        setData((prev) => ({ ...prev, events: res }));
      } else if (tab === 'facilities' && data.facilities.length === 0) {
        const [facRes, libRes] = await Promise.all([
          apiService.getCampusData('facilities'),
          apiService.getCampusData('library')
        ]);
        setData((prev) => ({ ...prev, facilities: facRes, library: libRes }));
      }
    } catch (e) {
      console.error('Failed to load campus data:', e);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  const tabs = [
    { id: 'exams', label: 'Exams Schedule', icon: GraduationCap },
    { id: 'timetable', label: 'Class Timetable', icon: Calendar },
    { id: 'notices', label: 'Notices & Bulletins', icon: Bell },
    { id: 'faculty', label: 'Faculty Directory', icon: Users },
    { id: 'events', label: 'Events & Hackathons', icon: Sparkles },
    { id: 'facilities', label: 'Library & Facilities', icon: Building },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fade-in">
      <div className="relative w-full max-w-4xl max-h-[85vh] flex flex-col bg-[#0d0f1a] border border-indigo-500/30 rounded-2xl shadow-2xl overflow-hidden">
        {/* Modal Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-900/60">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-400">
              <BookOpen className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-white">Campus Knowledge Explorer</h3>
              <p className="text-xs text-slate-400">Verified SQLite database for Nexus Institute of Technology</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition-all cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tab Bar */}
        <div className="flex items-center gap-1 px-6 pt-3 border-b border-slate-800/80 overflow-x-auto">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const active = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-2.5 text-xs font-semibold rounded-t-xl transition-all border-b-2 cursor-pointer whitespace-nowrap ${
                  active
                    ? 'border-cyan-400 text-cyan-300 bg-cyan-950/20'
                    : 'border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>

        {/* Tab Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {loading ? (
            <div className="flex flex-col items-center justify-center py-16 text-slate-400">
              <Loader2 className="w-8 h-8 animate-spin text-cyan-400 mb-2" />
              <span>Loading campus records...</span>
            </div>
          ) : (
            <>
              {/* EXAMS */}
              {activeTab === 'exams' && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {data.exams.map((ex) => (
                    <div
                      key={ex.id}
                      className="p-4 rounded-xl glass-panel border border-slate-800 hover:border-indigo-500/40 transition-all flex flex-col justify-between"
                    >
                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <span className="px-2 py-0.5 text-[10px] font-mono rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                            {ex.code}
                          </span>
                          <span className="text-xs text-slate-400">{ex.duration}</span>
                        </div>
                        <h4 className="text-base font-bold text-white mb-1">{ex.title}</h4>
                        <div className="text-xs text-slate-300 space-y-1 mt-2">
                          <p>📅 <strong className="text-white">Date:</strong> {ex.date}</p>
                          <p>⏰ <strong className="text-white">Time:</strong> {ex.time}</p>
                          <p>📍 <strong className="text-white">Location:</strong> {ex.room} ({ex.block})</p>
                          <p>👨‍🏫 <strong className="text-white">Instructor:</strong> {ex.instructor}</p>
                        </div>
                      </div>
                      <button
                        onClick={() => {
                          onClose();
                          onAskAbout(`When is my ${ex.subject} exam?`);
                        }}
                        className="mt-4 w-full py-1.5 px-3 rounded-lg bg-indigo-600/20 hover:bg-indigo-600/40 border border-indigo-500/30 text-indigo-300 text-xs font-semibold flex items-center justify-center gap-1.5 transition-all cursor-pointer"
                      >
                        <MessageSquare className="w-3.5 h-3.5" />
                        <span>Ask AI about {ex.subject}</span>
                      </button>
                    </div>
                  ))}
                </div>
              )}

              {/* TIMETABLE */}
              {activeTab === 'timetable' && (
                <div className="space-y-4">
                  {['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'].map((day) => {
                    const slots = data.timetable.filter((t) => t.day.toLowerCase() === day.toLowerCase());
                    return (
                      <div key={day} className="p-4 rounded-xl glass-panel border border-slate-800">
                        <div className="flex items-center justify-between mb-3 border-b border-slate-800 pb-2">
                          <h4 className="text-sm font-bold text-cyan-300 uppercase tracking-wider">{day}</h4>
                          <button
                            onClick={() => {
                              onClose();
                              onAskAbout(`What is my timetable for ${day}?`);
                            }}
                            className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center gap-1 cursor-pointer"
                          >
                            <span>Ask for {day}</span>
                          </button>
                        </div>
                        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
                          {slots.map((s, idx) => (
                            <div key={idx} className="p-2.5 rounded-lg bg-slate-900/60 border border-slate-800 text-xs">
                              <span className="text-[10px] text-indigo-400 font-mono">{s.time}</span>
                              <p className="font-semibold text-white mt-0.5">{s.subject}</p>
                              <p className="text-slate-400 mt-0.5">📍 {s.room} • {s.instructor}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}

              {/* NOTICES */}
              {activeTab === 'notices' && (
                <div className="space-y-3">
                  {data.notices.map((n) => (
                    <div key={n.id} className="p-4 rounded-xl glass-panel border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                            n.priority === 'High' ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40' : 'bg-slate-800 text-slate-300'
                          }`}>
                            {n.priority} Priority
                          </span>
                          <span className="text-xs text-slate-500">{n.date}</span>
                          <span className="text-xs text-cyan-400">• {n.category}</span>
                        </div>
                        <h4 className="text-sm font-bold text-white">{n.title}</h4>
                        <p className="text-xs text-slate-300 mt-1 max-w-2xl">{n.details}</p>
                        {n.action && (
                          <p className="text-xs text-indigo-300 mt-1 font-medium">👉 {n.action}</p>
                        )}
                      </div>
                      <button
                        onClick={() => {
                          onClose();
                          onAskAbout("Tell me about latest college notices");
                        }}
                        className="py-1.5 px-3 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs text-cyan-300 border border-slate-700 whitespace-nowrap cursor-pointer"
                      >
                        Ask Assistant
                      </button>
                    </div>
                  ))}
                </div>
              )}

              {/* FACULTY */}
              {activeTab === 'faculty' && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {data.faculty.map((f, idx) => (
                    <div key={idx} className="p-4 rounded-xl glass-panel border border-slate-800 text-xs">
                      <h4 className="text-sm font-bold text-white">{f.name}</h4>
                      <p className="text-indigo-400 mt-0.5">{f.title}</p>
                      <p className="text-slate-400">{f.department}</p>
                      <div className="mt-3 space-y-1 text-slate-300 border-t border-slate-800/80 pt-2">
                        <p>🏢 <strong className="text-white">Office:</strong> {f.office}</p>
                        <p>🕒 <strong className="text-white">Hours:</strong> {f.office_hours}</p>
                        <p>📧 <strong className="text-white">Email:</strong> {f.email}</p>
                      </div>
                      <button
                        onClick={() => {
                          onClose();
                          onAskAbout(`Where is ${f.name}'s office and what are the office hours?`);
                        }}
                        className="mt-3 w-full py-1.5 rounded-lg bg-slate-800/80 hover:bg-indigo-900/40 text-slate-200 border border-slate-700 text-[11px] font-medium cursor-pointer"
                      >
                        Ask about {f.name.split(' ').pop()}
                      </button>
                    </div>
                  ))}
                </div>
              )}

              {/* EVENTS */}
              {activeTab === 'events' && (
                <div className="space-y-3">
                  {data.events.map((ev, idx) => (
                    <div key={idx} className="p-4 rounded-xl glass-panel border border-slate-800">
                      <div className="flex items-center justify-between">
                        <span className="px-2 py-0.5 rounded text-[10px] bg-purple-500/20 text-purple-300 border border-purple-500/40 font-semibold">
                          {ev.category}
                        </span>
                        <span className="text-xs text-slate-400">{ev.date}</span>
                      </div>
                      <h4 className="text-base font-bold text-white mt-1">{ev.title}</h4>
                      <p className="text-xs text-slate-300 mt-1">📍 {ev.venue} • Organized by {ev.organizer}</p>
                      <p className="text-xs text-slate-400 mt-2 italic">✨ {ev.highlights}</p>
                      <button
                        onClick={() => {
                          onClose();
                          onAskAbout(`Tell me about ${ev.title}`);
                        }}
                        className="mt-3 py-1.5 px-3 rounded-lg bg-purple-600/20 hover:bg-purple-600/30 text-purple-300 border border-purple-500/30 text-xs font-semibold cursor-pointer"
                      >
                        Ask AI about this event
                      </button>
                    </div>
                  ))}
                </div>
              )}

              {/* FACILITIES & LIBRARY */}
              {activeTab === 'facilities' && (
                <div className="space-y-4">
                  {/* Library card */}
                  {data.library && data.library.name && (
                    <div className="p-4 rounded-xl glass-panel-glow border border-teal-500/30">
                      <h4 className="text-base font-bold text-teal-300">{data.library.name}</h4>
                      <p className="text-xs text-slate-300 mt-1">⏰ <strong>Regular Hours:</strong> {data.library.regular_timings}</p>
                      <p className="text-xs text-slate-300 mt-0.5">🔥 <strong>Exam Period:</strong> {data.library.exam_period_timings}</p>
                      <p className="text-xs text-slate-300 mt-0.5">📖 <strong>Rules:</strong> {data.library.borrowing_rules}</p>
                      <button
                        onClick={() => {
                          onClose();
                          onAskAbout("Tell me about the central library hours and quiet zones");
                        }}
                        className="mt-3 py-1 px-3 rounded-lg bg-teal-600/20 text-teal-300 border border-teal-500/30 text-xs font-medium cursor-pointer"
                      >
                        Ask about Library
                      </button>
                    </div>
                  )}

                  {/* Other Facilities */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {data.facilities.map((fac, idx) => (
                      <div key={idx} className="p-3 rounded-xl glass-panel border border-slate-800 text-xs">
                        <h5 className="font-bold text-white">{fac.name}</h5>
                        <p className="text-slate-400 mt-0.5">📍 {fac.location}</p>
                        <p className="text-slate-300 mt-0.5">⏰ {fac.timings}</p>
                        <p className="text-slate-400 mt-1 text-[11px]">{fac.services}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
