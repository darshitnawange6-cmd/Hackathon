import React, { useState, useEffect, useRef } from 'react';
import Header from './components/Header';
import VoiceVisualizer from './components/VoiceVisualizer';
import MicrophoneButton from './components/MicrophoneButton';
import QuickActions from './components/QuickActions';
import IntentHUD from './components/IntentHUD';
import ChatWindow from './components/ChatWindow';
import InputBar from './components/InputBar';
import CampusHubModal from './components/CampusHubModal';
import DemoScenarioRunner from './components/DemoScenarioRunner';
import DocumentManagerModal from './components/DocumentManagerModal';
import DeveloperDashboard from './components/DeveloperDashboard';
import AboutModal from './components/AboutModal';
import { speechService } from './services/speechService';
import { ttsService } from './services/ttsService';
import { apiService } from './services/apiService';

export default function App() {
  const [messages, setMessages] = useState([]);
  const [isListening, setIsListening] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [interimTranscript, setInterimTranscript] = useState('');
  const [currentSpokenMessageId, setCurrentSpokenMessageId] = useState(null);
  const [systemStatus, setSystemStatus] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);

  // Intent telemetry HUD state
  const [currentIntent, setCurrentIntent] = useState('Awaiting Input');
  const [standardIntent, setStandardIntent] = useState('UNKNOWN');
  const [confidence, setConfidence] = useState(0);
  const [entities, setEntities] = useState({});
  const [turnCount, setTurnCount] = useState(0);
  const [isClarifying, setIsClarifying] = useState(false);

  // Performance latency metrics (Feature 8)
  const [latencyMetrics, setLatencyMetrics] = useState({});
  const [speechLatency, setSpeechLatency] = useState(null);
  const speechStartTimeRef = useRef(null);

  // Sources and Action logs
  const [sourceDetails, setSourceDetails] = useState([]);
  const [sources, setSources] = useState([]);
  const [actionLogs, setActionLogs] = useState([]);
  const [sessionContext, setSessionContext] = useState({});

  // Modals
  const [isCampusHubOpen, setIsCampusHubOpen] = useState(false);
  const [isDemoScenariosOpen, setIsDemoScenariosOpen] = useState(false);
  const [isDocManagerOpen, setIsDocManagerOpen] = useState(false);
  const [isDevDashboardOpen, setIsDevDashboardOpen] = useState(false);
  const [isAboutOpen, setIsAboutOpen] = useState(false);

  const sessionIdRef = useRef('student-' + Math.random().toString(36).substring(2, 9));

  // Load system health & attach keyboard shortcuts on mount
  useEffect(() => {
    apiService
      .getHealth()
      .then((data) => setSystemStatus(data))
      .catch((err) => console.warn('Backend health check error:', err));

    const handleKeyDown = (e) => {
      // Toggle Developer Dashboard with Ctrl+D or F2
      if ((e.ctrlKey && e.key.toLowerCase() === 'd') || e.key === 'F2') {
        e.preventDefault();
        setIsDevDashboardOpen((prev) => !prev);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const refreshSessionContext = async () => {
    try {
      const data = await apiService.getSession(sessionIdRef.current);
      if (data?.context) {
        setSessionContext(data.context);
      }
    } catch (e) {
      console.warn('Failed to refresh session context:', e);
    }
  };

  // Voice recognition toggle with instant voice interruption (Feature 2)
  const handleToggleListen = () => {
    if (isListening) {
      speechService.stopListening();
      setIsListening(false);
      return;
    }

    // Voice Interruption: immediately cancel any active AI speech
    ttsService.stop();
    setIsSpeaking(false);
    setCurrentSpokenMessageId(null);
    setErrorMessage(null);

    speechStartTimeRef.current = Date.now();

    const started = speechService.startListening({
      onStart: () => {
        setIsListening(true);
        setInterimTranscript('');
      },
      onInterim: (text) => {
        // Voice Interruption / Barge-In: if AI speaks, stop instantly
        if (ttsService.isSpeaking()) {
          ttsService.stop();
          setIsSpeaking(false);
          setCurrentSpokenMessageId(null);
        }
        setInterimTranscript(text);
      },
      onResult: (finalText) => {
        setIsListening(false);
        setInterimTranscript('');
        if (speechStartTimeRef.current) {
          setSpeechLatency(Date.now() - speechStartTimeRef.current);
        }
        if (finalText) {
          handleSendMessage(finalText, true);
        }
      },
      onError: (msg) => {
        setIsListening(false);
        setInterimTranscript('');
        setErrorMessage(msg);
        setTimeout(() => setErrorMessage(null), 5000);
      },
      onEnd: () => {
        setIsListening(false);
      },
    });

    if (!started && !speechService.isSupported()) {
      setErrorMessage(
        'Browser speech recognition is not supported in this environment. You can type or use the Quick Action buttons!'
      );
      setTimeout(() => setErrorMessage(null), 6000);
    }
  };

  // Text or voice question submission with progressive SSE streaming (Feature 3)
  const handleSendMessage = async (text, isVoice = false) => {
    if (!text || isLoading) return;

    // Stop active listening & active speech immediately
    speechService.stopListening();
    setIsListening(false);
    ttsService.stop();
    setIsSpeaking(false);
    setCurrentSpokenMessageId(null);

    const userMsgId = 'msg-' + Date.now();
    const newTurn = turnCount + 1;
    setTurnCount(newTurn);

    const userMessage = {
      id: userMsgId,
      role: 'user',
      content: text,
      isVoice,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);
    setErrorMessage(null);

    const aiMsgId = 'msg-' + (Date.now() + 1);
    let accumulatedText = '';

    // Create assistant message placeholder for streaming
    const initialAiMessage = {
      id: aiMsgId,
      role: 'assistant',
      content: '',
      isStreaming: true,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      intent: 'thinking',
      confidence: 0,
      followUps: [],
      sources: [],
      sourceDetails: [],
    };
    setMessages((prev) => [...prev, initialAiMessage]);

    try {
      // Stream response using SSE endpoint (Feature 3)
      await apiService.sendMessageStream(text, sessionIdRef.current, isVoice, {
        onMetadata: (meta) => {
          if (meta.detected_intent) setCurrentIntent(meta.detected_intent);
          if (meta.standard_intent) setStandardIntent(meta.standard_intent);
          if (meta.sources) setSources(meta.sources);
          if (meta.source_details) setSourceDetails(meta.source_details);

          setMessages((prev) =>
            prev.map((m) =>
              m.id === aiMsgId
                ? {
                    ...m,
                    intent: meta.detected_intent,
                    standardIntent: meta.standard_intent,
                    sources: meta.sources || [],
                    sourceDetails: meta.source_details || [],
                    primarySource: meta.primary_source,
                    actionExecuted: meta.action_executed,
                  }
                : m
            )
          );
        },
        onDelta: (delta) => {
          accumulatedText += delta;
          setMessages((prev) =>
            prev.map((m) =>
              m.id === aiMsgId ? { ...m, content: accumulatedText } : m
            )
          );
        },
        onDone: (done) => {
          setIsLoading(false);
          const fullContent = done.full_text || accumulatedText;
          setMessages((prev) =>
            prev.map((m) =>
              m.id === aiMsgId
                ? {
                    ...m,
                    content: fullContent,
                    isStreaming: false,
                    spokenText: done.spoken_text,
                    followUps: done.follow_up_suggestions || [],
                    actionResult: done.action_result,
                  }
                : m
            )
          );

          if (done.metrics) {
            setLatencyMetrics(done.metrics);
          }

          if (done.action_result) {
            setActionLogs((prev) => [
              { time: new Date().toLocaleTimeString(), action: done.action_result.action || 'Executed Action', result: done.action_result },
              ...prev.slice(0, 9),
            ]);
          }

          setIsClarifying(Boolean(done.clarification_needed));
          refreshSessionContext();

          // Natural Speech Synthesis aloud
          if (!isMuted && done.spoken_text) {
            setCurrentSpokenMessageId(aiMsgId);
            setIsSpeaking(true);
            ttsService.speak(done.spoken_text, {
              onStart: () => setIsSpeaking(true),
              onEnd: () => {
                setIsSpeaking(false);
                setCurrentSpokenMessageId(null);
              },
              onError: () => {
                setIsSpeaking(false);
                setCurrentSpokenMessageId(null);
              },
            });
          }
        },
        onError: (err) => {
          console.warn('Stream error occurred:', err);
          setErrorMessage('Streaming update error: ' + err);
        },
      });
    } catch (err) {
      console.warn('Stream failed, falling back to standard chat endpoint:', err);
      try {
        const response = await apiService.sendMessage(text, sessionIdRef.current, isVoice);
        setMessages((prev) =>
          prev.map((m) =>
            m.id === aiMsgId
              ? {
                  ...m,
                  content: response.response_text,
                  isStreaming: false,
                  spokenText: response.spoken_text,
                  intent: response.detected_intent,
                  standardIntent: response.standard_intent,
                  confidence: response.confidence,
                  entities: response.entities,
                  followUps: response.follow_up_suggestions,
                  sources: response.sources || [],
                  sourceDetails: response.source_details || [],
                  primarySource: response.primary_source,
                  actionExecuted: response.action_executed,
                  actionResult: response.action_result,
                }
              : m
          )
        );

        setCurrentIntent(response.detected_intent);
        if (response.standard_intent) setStandardIntent(response.standard_intent);
        setConfidence(response.confidence);
        setEntities(response.entities || {});
        setIsClarifying(Boolean(response.clarification_needed));
        if (response.metrics) setLatencyMetrics(response.metrics);
        if (response.source_details) setSourceDetails(response.source_details);
        refreshSessionContext();

        if (!isMuted && response.spoken_text) {
          setCurrentSpokenMessageId(aiMsgId);
          setIsSpeaking(true);
          ttsService.speak(response.spoken_text, {
            onStart: () => setIsSpeaking(true),
            onEnd: () => {
              setIsSpeaking(false);
              setCurrentSpokenMessageId(null);
            },
            onError: () => {
              setIsSpeaking(false);
              setCurrentSpokenMessageId(null);
            },
          });
        }
      } catch (fallbackErr) {
        console.error('All chat calls failed:', fallbackErr);
        setMessages((prev) =>
          prev.map((m) =>
            m.id === aiMsgId
              ? {
                  ...m,
                  content:
                    '⚠️ I encountered an issue connecting to the campus assistant service. Please check that the backend is running.',
                  isStreaming: false,
                  followUps: ['When is my physics exam?', 'College notices'],
                }
              : m
          )
        );
      }
    } finally {
      setIsLoading(false);
    }
  };

  // Replay message audio
  const handleReplayAudio = (msg) => {
    if (!msg.spokenText) return;
    ttsService.stop();
    setCurrentSpokenMessageId(msg.id);
    setIsSpeaking(true);
    ttsService.speak(msg.spokenText, {
      onStart: () => setIsSpeaking(true),
      onEnd: () => {
        setIsSpeaking(false);
        setCurrentSpokenMessageId(null);
      },
      onError: () => {
        setIsSpeaking(false);
        setCurrentSpokenMessageId(null);
      },
    });
  };

  const handleStopAudio = () => {
    ttsService.stop();
    setIsSpeaking(false);
    setCurrentSpokenMessageId(null);
  };

  const handleToggleMute = () => {
    const nextMuted = !isMuted;
    setIsMuted(nextMuted);
    ttsService.setMuted(nextMuted);
    if (nextMuted) {
      handleStopAudio();
    }
  };

  const handleClearChat = async () => {
    try {
      await apiService.clearSession(sessionIdRef.current);
    } catch (e) {
      console.warn('Clear session error:', e);
    }
    setMessages([]);
    setTurnCount(0);
    setCurrentIntent('Awaiting Input');
    setStandardIntent('UNKNOWN');
    setConfidence(0);
    setEntities({});
    setIsClarifying(false);
    setSessionContext({});
    handleStopAudio();
  };

  // 5 Explicit Visual States (Feature 2): LISTENING, THINKING, SPEAKING, IDLE, ERROR
  const visualizerState = errorMessage
    ? 'error'
    : isListening
    ? 'listening'
    : isLoading
    ? 'thinking'
    : isSpeaking
    ? 'speaking'
    : 'idle';

  return (
    <div className="min-h-screen bg-[#08090e] text-slate-100 flex flex-col justify-between selection:bg-indigo-500 selection:text-white">
      {/* Background cyber ambient gradients */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden z-0">
        <div className="absolute top-[-10%] left-[20%] w-[500px] h-[500px] rounded-full bg-indigo-600/10 blur-[130px] animate-float-orb"></div>
        <div className="absolute bottom-[-10%] right-[15%] w-[600px] h-[600px] rounded-full bg-cyan-600/10 blur-[150px] animate-float-orb delay-1000"></div>
        <div className="absolute top-[40%] right-[30%] w-[350px] h-[350px] rounded-full bg-purple-600/10 blur-[120px]"></div>
      </div>

      {/* Main Top Header */}
      <Header
        isMuted={isMuted}
        onToggleMute={handleToggleMute}
        onClearChat={handleClearChat}
        onOpenCampusHub={() => setIsCampusHubOpen(true)}
        onOpenDemoScenarios={() => setIsDemoScenariosOpen(true)}
        onOpenDocManager={() => setIsDocManagerOpen(true)}
        onOpenDevDashboard={() => setIsDevDashboardOpen(true)}
        onOpenAbout={() => setIsAboutOpen(true)}
        listeningStatus={isListening ? 'listening' : 'idle'}
        isSpeaking={isSpeaking}
        systemStatus={systemStatus}
      />

      {/* Error alert toast */}
      {errorMessage && (
        <div className="w-full max-w-xl mx-auto px-4 mt-3 z-30 animate-fade-in">
          <div className="p-3 rounded-xl bg-rose-500/20 border border-rose-500/40 text-rose-200 text-xs flex items-center justify-between shadow-lg">
            <span>{errorMessage}</span>
            <button onClick={() => setErrorMessage(null)} className="ml-2 font-bold hover:text-white">✕</button>
          </div>
        </div>
      )}

      {/* Central Content Area */}
      <main className="relative z-10 flex-1 flex flex-col justify-between max-w-5xl w-full mx-auto px-2 sm:px-4 py-2">
        {/* Hero Voice Zone */}
        <section className="flex flex-col items-center justify-center pt-2 pb-1">
          <VoiceVisualizer state={visualizerState} height={60} />
          <MicrophoneButton
            isListening={isListening}
            isLoading={isLoading}
            isSpeaking={isSpeaking}
            onToggleListen={handleToggleListen}
            onStopSpeech={handleStopAudio}
            interimTranscript={interimTranscript}
          />
          <QuickActions onSelectAction={(q) => handleSendMessage(q, false)} disabled={isLoading} />
        </section>

        {/* Live Intent HUD Telemetry (clean student-facing view) */}
        <div className="px-2 my-2">
          <IntentHUD
            currentIntent={currentIntent}
            confidence={confidence}
            entities={entities}
            turnCount={turnCount}
            isClarifying={isClarifying}
          />
        </div>

        {/* Chat Stream Window */}
        <ChatWindow
          messages={messages}
          isLoading={isLoading}
          currentSpokenMessageId={currentSpokenMessageId}
          isSpeaking={isSpeaking}
          onReplayAudio={handleReplayAudio}
          onStopAudio={handleStopAudio}
          onSelectSuggestion={(sug) => handleSendMessage(sug, false)}
        />

        {/* Text Input Footer Bar */}
        <InputBar
          onSendMessage={(txt) => handleSendMessage(txt, false)}
          disabled={isLoading}
          isListening={isListening}
          onToggleListen={handleToggleListen}
        />
      </main>

      {/* Developer & Evaluator Dashboard (Features 4, 5, 6, 8) */}
      <DeveloperDashboard
        isOpen={isDevDashboardOpen}
        onClose={() => setIsDevDashboardOpen(false)}
        standardIntent={standardIntent}
        rawIntent={currentIntent}
        confidence={confidence}
        metrics={latencyMetrics}
        speechLatency={speechLatency}
        context={sessionContext}
        actionLogs={actionLogs}
        sources={sources}
        sourceDetails={sourceDetails}
        systemStatus={systemStatus}
        onRefreshContext={refreshSessionContext}
      />

      {/* Campus Knowledge Base Explorer Modal */}
      <CampusHubModal
        isOpen={isCampusHubOpen}
        onClose={() => setIsCampusHubOpen(false)}
        onAskAbout={(q) => handleSendMessage(q, false)}
      />

      {/* Hackathon Judge Demo Scenarios Runner */}
      <DemoScenarioRunner
        isOpen={isDemoScenariosOpen}
        onClose={() => setIsDemoScenariosOpen(false)}
        onExecuteScenarioQuery={(q, voiceFlag) => handleSendMessage(q, voiceFlag)}
      />

      {/* Supabase Document & Knowledge Vault Modal */}
      <DocumentManagerModal
        isOpen={isDocManagerOpen}
        onClose={() => setIsDocManagerOpen(false)}
      />

      {/* About & System Architecture Presentation Modal */}
      <AboutModal
        isOpen={isAboutOpen}
        onClose={() => setIsAboutOpen(false)}
      />
    </div>
  );
}
