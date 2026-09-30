import React, { useEffect, useRef } from 'react';

const STATE_CONFIG = {
  listening: {
    label: 'LISTENING',
    badge: 'bg-rose-500/20 text-rose-300 border-rose-500/40 shadow-rose-500/20',
    dot: 'bg-rose-500 animate-ping'
  },
  thinking: {
    label: 'THINKING',
    badge: 'bg-indigo-500/20 text-indigo-300 border-indigo-500/40 shadow-indigo-500/20',
    dot: 'bg-indigo-400 animate-pulse'
  },
  speaking: {
    label: 'SPEAKING',
    badge: 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40 shadow-cyan-500/20',
    dot: 'bg-cyan-400 animate-bounce'
  },
  error: {
    label: 'ERROR',
    badge: 'bg-amber-500/20 text-amber-300 border-amber-500/40 shadow-amber-500/20',
    dot: 'bg-amber-500 animate-ping'
  },
  idle: {
    label: 'IDLE',
    badge: 'bg-slate-800/60 text-slate-400 border-slate-700/60',
    dot: 'bg-emerald-400'
  }
};

export default function VoiceVisualizer({ state = 'idle', height = 65 }) {
  const canvasRef = useRef(null);
  const normalizedState = (state || 'idle').toLowerCase();
  const config = STATE_CONFIG[normalizedState] || STATE_CONFIG.idle;

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let animationId;
    let step = 0;

    const render = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      const width = canvas.width;
      const h = canvas.height;
      const centerY = h / 2;

      step += 0.05;

      if (normalizedState === 'listening') {
        // High-energy dynamic multi-sine wave in vibrant magenta & cyan
        for (let wave = 0; wave < 3; wave++) {
          ctx.beginPath();
          ctx.lineWidth = 2.5;
          const gradient = ctx.createLinearGradient(0, 0, width, 0);
          gradient.addColorStop(0, '#06b6d4');
          gradient.addColorStop(0.5, '#ec4899');
          gradient.addColorStop(1, '#8b5cf6');
          ctx.strokeStyle = gradient;

          const amplitude = 18 + wave * 6;
          const frequency = 0.02 + wave * 0.01;
          const phase = step * (2 + wave);

          for (let x = 0; x < width; x++) {
            const envelope = Math.sin((x / width) * Math.PI);
            const y = centerY + Math.sin(x * frequency + phase) * amplitude * envelope;
            if (x === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
          }
          ctx.stroke();
        }
      } else if (normalizedState === 'speaking') {
        // Equalizer voice bars with harmonic motion
        const barCount = 36;
        const barWidth = 4;
        const gap = (width - barCount * barWidth) / (barCount + 1);

        for (let i = 0; i < barCount; i++) {
          const x = gap + i * (barWidth + gap);
          const barHeight =
            12 + Math.abs(Math.sin(step * 1.5 + i * 0.35)) * (h * 0.65) * Math.sin(((i + 1) / barCount) * Math.PI);

          const grad = ctx.createLinearGradient(0, centerY - barHeight / 2, 0, centerY + barHeight / 2);
          grad.addColorStop(0, '#06b6d4');
          grad.addColorStop(1, '#6366f1');

          ctx.fillStyle = grad;
          ctx.beginPath();
          ctx.roundRect(x, centerY - barHeight / 2, barWidth, barHeight, 3);
          ctx.fill();
        }
      } else if (normalizedState === 'thinking') {
        // Subtle rhythmic pulsing orbital line
        ctx.beginPath();
        ctx.lineWidth = 2;
        ctx.strokeStyle = '#6366f1';
        for (let x = 0; x < width; x++) {
          const envelope = Math.sin((x / width) * Math.PI);
          const y = centerY + Math.sin(x * 0.03 + step * 2.5) * 8 * envelope;
          if (x === 0) ctx.moveTo(x, y);
          else ctx.lineTo(x, y);
        }
        ctx.stroke();
      } else if (normalizedState === 'error') {
        // Agitated jagged pulse wave
        ctx.beginPath();
        ctx.lineWidth = 2;
        ctx.strokeStyle = '#f43f5e';
        for (let x = 0; x < width; x++) {
          const envelope = Math.sin((x / width) * Math.PI);
          const jitter = (Math.sin(x * 0.1 + step * 5) > 0 ? 1 : -1) * 6;
          const y = centerY + jitter * envelope;
          if (x === 0) ctx.moveTo(x, y);
          else ctx.lineTo(x, y);
        }
        ctx.stroke();
      } else {
        // Ambient calm idle wave
        ctx.beginPath();
        ctx.lineWidth = 1.5;
        const grad = ctx.createLinearGradient(0, 0, width, 0);
        grad.addColorStop(0, 'rgba(6, 182, 212, 0.2)');
        grad.addColorStop(0.5, 'rgba(99, 102, 241, 0.4)');
        grad.addColorStop(1, 'rgba(139, 92, 246, 0.2)');
        ctx.strokeStyle = grad;

        for (let x = 0; x < width; x++) {
          const envelope = Math.sin((x / width) * Math.PI);
          const y = centerY + Math.sin(x * 0.015 + step * 0.8) * 5 * envelope;
          if (x === 0) ctx.moveTo(x, y);
          else ctx.lineTo(x, y);
        }
        ctx.stroke();
      }

      animationId = requestAnimationFrame(render);
    };

    render();

    return () => {
      cancelAnimationFrame(animationId);
    };
  }, [normalizedState]);

  return (
    <div className="w-full flex flex-col items-center justify-center relative overflow-hidden my-1">
      {/* 5-State Explicit Visual Pill (Feature 2) */}
      <div className={`mb-1 px-2.5 py-0.5 rounded-full border text-[10px] font-mono font-bold tracking-widest flex items-center gap-1.5 transition-all shadow-sm ${config.badge}`}>
        <span className={`w-1.5 h-1.5 rounded-full ${config.dot}`}></span>
        <span>{config.label}</span>
      </div>

      <canvas
        ref={canvasRef}
        width={480}
        height={height}
        className="w-full max-w-[480px] h-[65px] pointer-events-none"
      />
    </div>
  );
}
