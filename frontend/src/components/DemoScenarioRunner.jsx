import React, { useState } from 'react';
import { X, Play, Sparkles, CheckCircle2, ChevronRight, HelpCircle, Bell, GraduationCap } from 'lucide-react';
import confetti from 'canvas-confetti';

export default function DemoScenarioRunner({
  isOpen,
  onClose,
  onExecuteScenarioQuery,
}) {
  const [activeScenario, setActiveScenario] = useState('exam_flow');
  const [currentStepIndex, setCurrentStepIndex] = useState(-1);
  const [isRunning, setIsRunning] = useState(false);

  if (!isOpen) return null;

  const scenarios = {
    exam_flow: {
      title: 'Scenario 1: Official 4-Step Hackathon Demo',
      description: 'The complete presentation flow: speech recognition, exam retrieval, pronoun location resolution, exam hall requirements, and contextual reminder creation.',
      badge: 'Official Hackathon Flow (4 Steps)',
      badgeColor: 'bg-indigo-500/20 text-indigo-300 border-indigo-500/40',
      icon: GraduationCap,
      steps: [
        {
          label: 'Step 1: Exam Inquiry',
          query: 'When is my Physics exam?',
          detail: 'Tests speech recognition, intent detection, knowledge retrieval, and grounded text-to-speech response.',
        },
        {
          label: 'Step 2: Pronoun Location Follow-up',
          query: 'Where is it?',
          detail: 'Uses conversational memory to resolve "it" to Physics exam room (Hall B-204) with directions.',
        },
        {
          label: 'Step 3: Exam Requirements Follow-up',
          query: 'What do I need to bring?',
          detail: 'Continues context to retrieve exam equipment rules (Hall Ticket, ID card, approved calculator).',
        },
        {
          label: 'Step 4: Contextual Reminder Creation',
          query: 'Remind me tomorrow.',
          detail: 'Executes create_reminder action with contextual inheritance of "Physics Exam" and confirms the task.',
        },
      ],
    },
    notices_flow: {
      title: 'Scenario 2: College Notices & Hackathon Alert',
      description: 'Demonstrates retrieval of urgent administrative bulletins, 24/7 library exam hours, and HackSphere 2026 hackathon registration.',
      badge: 'Campus Intelligence',
      badgeColor: 'bg-amber-500/20 text-amber-300 border-amber-500/40',
      icon: Bell,
      steps: [
        {
          label: 'Step 1: Check Bulletins',
          query: 'What are the latest college notices?',
          detail: 'Retrieves high-priority campus announcements including midterm circulars and Wi-Fi maintenance.',
        },
        {
          label: 'Step 2: Inquire About Events',
          query: 'Tell me about the upcoming HackSphere 2026 hackathon',
          detail: 'Retrieves event dates, venue (Auditorium 1), prize pool, and registration guidelines.',
        },
      ],
    },
    clarification_flow: {
      title: 'Scenario 3: Ambiguous Request & Clarification',
      description: 'Demonstrates the system asking for clarification when a user gives an underspecified inquiry ("When is my exam?").',
      badge: 'Smart Clarification',
      badgeColor: 'bg-purple-500/20 text-purple-300 border-purple-500/40',
      icon: HelpCircle,
      steps: [
        {
          label: 'Step 1: Ambiguous Question',
          query: 'When is my exam?',
          detail: 'User does not state the subject. AI asks: "Which subject\'s exam are you asking about?"',
        },
        {
          label: 'Step 2: User Clarification Answer',
          query: 'Physics',
          detail: 'System resolves the clarification prompt and gives the full Physics exam schedule.',
        },
      ],
    },
  };

  const current = scenarios[activeScenario];

  const handleRunStep = async (step, index) => {
    setCurrentStepIndex(index);
    setIsRunning(true);
    onClose();
    await onExecuteScenarioQuery(step.query, true);
    setIsRunning(false);
  };

  const handleRunFullSequence = async () => {
    setIsRunning(true);
    onClose();
    for (let i = 0; i < current.steps.length; i++) {
      setCurrentStepIndex(i);
      await onExecuteScenarioQuery(current.steps[i].query, true);
      // Brief pause between questions for realistic conversational flow
      if (i < current.steps.length - 1) {
        await new Promise((resolve) => setTimeout(resolve, 3500));
      }
    }
    setIsRunning(false);
    confetti({
      particleCount: 80,
      spread: 70,
      origin: { y: 0.6 },
    });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fade-in">
      <div className="relative w-full max-w-2xl bg-[#0c0e18] border border-purple-500/40 rounded-2xl shadow-2xl overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-900/60">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-purple-500/20 border border-purple-500/40 text-purple-300">
              <Sparkles className="w-5 h-5 animate-pulse" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">Judge Demo Scenarios</h3>
              <p className="text-xs text-slate-400">1-click test runs for hackathon evaluation</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition-all cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Scenario Selection Tabs */}
        <div className="grid grid-cols-3 gap-2 p-4 border-b border-slate-800/80 bg-slate-950/40">
          {Object.entries(scenarios).map(([key, s]) => {
            const Icon = s.icon;
            const active = activeScenario === key;
            return (
              <button
                key={key}
                onClick={() => {
                  setActiveScenario(key);
                  setCurrentStepIndex(-1);
                }}
                className={`p-3 rounded-xl border text-left transition-all cursor-pointer ${
                  active
                    ? 'bg-purple-950/40 border-purple-500/60 text-white shadow-lg'
                    : 'bg-slate-900/40 border-slate-800 text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                }`}
              >
                <Icon className={`w-4 h-4 mb-1.5 ${active ? 'text-purple-300' : 'text-slate-400'}`} />
                <div className="text-xs font-bold truncate">{s.title.split(':')[0]}</div>
                <div className="text-[10px] text-slate-400 truncate">{s.badge}</div>
              </button>
            );
          })}
        </div>

        {/* Scenario Details & Step List */}
        <div className="p-6 space-y-4 overflow-y-auto max-h-[55vh]">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${current.badgeColor}`}>
                {current.badge}
              </span>
            </div>
            <h4 className="text-lg font-bold text-white">{current.title}</h4>
            <p className="text-xs text-slate-300 mt-1">{current.description}</p>
          </div>

          <div className="space-y-3 mt-4">
            <div className="text-xs font-bold text-slate-400 uppercase tracking-wider">
              Sequence of Voice Interactions:
            </div>
            {current.steps.map((st, idx) => (
              <div
                key={idx}
                className="p-3.5 rounded-xl glass-panel border border-slate-800 hover:border-purple-500/40 flex items-center justify-between gap-3 transition-all"
              >
                <div className="flex items-start gap-3">
                  <div className="w-6 h-6 rounded-full bg-purple-500/20 text-purple-300 flex items-center justify-center text-xs font-bold shrink-0 mt-0.5">
                    {idx + 1}
                  </div>
                  <div>
                    <p className="text-xs font-bold text-white font-mono">"{st.query}"</p>
                    <p className="text-[11px] text-slate-400 mt-0.5">{st.detail}</p>
                  </div>
                </div>
                <button
                  onClick={() => handleRunStep(st, idx)}
                  className="px-3 py-1.5 rounded-lg bg-indigo-600/30 hover:bg-indigo-600/50 text-indigo-300 border border-indigo-500/30 text-xs font-medium flex items-center gap-1 shrink-0 cursor-pointer"
                  title="Run this step"
                >
                  <Play className="w-3 h-3 fill-current" />
                  <span>Test Step</span>
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Footer with Run Entire Scenario Button */}
        <div className="p-4 border-t border-slate-800 bg-slate-900/60 flex items-center justify-between">
          <span className="text-xs text-slate-400">
            Clicking run will speak & transcribe automatically
          </span>
          <button
            onClick={handleRunFullSequence}
            disabled={isRunning}
            className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white text-xs font-bold flex items-center gap-2 shadow-lg shadow-purple-600/30 transition-all transform active:scale-95 cursor-pointer disabled:opacity-50"
          >
            <Play className="w-4 h-4 fill-white" />
            <span>Run Full Scenario ({current.steps.length} Steps)</span>
          </button>
        </div>
      </div>
    </div>
  );
}
