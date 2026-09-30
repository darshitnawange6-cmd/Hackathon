// Web Speech API Text-to-Speech Abstraction with Chrome Resilience

class TTSService {
  constructor() {
    this.synth = typeof window !== 'undefined' ? window.speechSynthesis : null;
    this.voices = [];
    this.isMuted = false;
    this.currentUtterance = null;
    this.selectedVoice = null;
    this.rate = 1.0;
    this.pitch = 1.0;

    if (this.synth) {
      this.loadVoices();
      if (typeof window !== 'undefined' && window.speechSynthesis) {
        window.speechSynthesis.onvoiceschanged = () => this.loadVoices();
      }
    }
  }

  loadVoices() {
    if (!this.synth) return;
    try {
      this.voices = this.synth.getVoices() || [];
      if (this.voices.length > 0) {
        const preferred = this.voices.find(
          (v) =>
            (v.name.includes('Google') ||
              v.name.includes('Natural') ||
              v.name.includes('Samantha') ||
              v.name.includes('David') ||
              v.name.includes('Zira') ||
              v.name.includes('Jenny')) &&
            v.lang.startsWith('en')
        );
        this.selectedVoice = preferred || this.voices.find((v) => v.lang.startsWith('en')) || this.voices[0];
      }
    } catch (e) {
      console.warn('Voice loading error:', e);
    }
  }

  isSupported() {
    return Boolean(this.synth);
  }

  setMuted(muted) {
    this.isMuted = Boolean(muted);
    if (this.isMuted) {
      this.stop();
    }
  }

  cleanTextForSpeech(text) {
    if (!text) return '';
    return text
      .replace(/###\s+/g, '')
      .replace(/##\s+/g, '')
      .replace(/#\s+/g, '')
      .replace(/\*\*(.*?)\*\*/g, '$1')
      .replace(/\*(.*?)\*/g, '$1')
      .replace(/\[(.*?)\]\(.*?\)/g, '$1')
      .replace(/`{1,3}.*?`{1,3}/g, '')
      .replace(/[-*]\s+/g, '')
      .replace(/\n+/g, ' ')
      .trim();
  }

  speak(text, { onStart, onEnd, onError, rate = 1.0, pitch = 1.0 } = {}) {
    if (!this.synth || this.isMuted || !text) {
      if (onEnd) onEnd();
      return;
    }

    // Always stop and resume audio context to prevent Chrome stall
    this.stop();

    if (this.synth.paused) {
      try {
        this.synth.resume();
      } catch (e) {
        // ignore
      }
    }

    const cleaned = this.cleanTextForSpeech(text);
    if (!cleaned) {
      if (onEnd) onEnd();
      return;
    }

    if (!this.selectedVoice || this.voices.length === 0) {
      this.loadVoices();
    }

    // Small timeout ensures Chrome processes the previous cancel()
    setTimeout(() => {
      try {
        const utterance = new SpeechSynthesisUtterance(cleaned);
        if (this.selectedVoice) {
          utterance.voice = this.selectedVoice;
        }
        utterance.rate = rate || this.rate;
        utterance.pitch = pitch || this.pitch;

        utterance.onstart = () => {
          this.currentUtterance = utterance;
          if (onStart) onStart();
        };

        utterance.onend = () => {
          this.currentUtterance = null;
          if (onEnd) onEnd();
        };

        utterance.onerror = (e) => {
          // 'interrupted' is normal when a user clicks stop or new utterance starts
          if (e.error !== 'interrupted' && e.error !== 'canceled') {
            console.warn('SpeechSynthesis error:', e.error || e);
            if (onError) onError(e);
          }
          this.currentUtterance = null;
          if (onEnd) onEnd();
        };

        this.synth.speak(utterance);
      } catch (err) {
        console.warn('SpeechSynthesis speak exception:', err);
        if (onEnd) onEnd();
      }
    }, 40);
  }

  stop() {
    if (this.synth) {
      try {
        this.synth.cancel();
      } catch (e) {
        console.warn('Cancel error:', e);
      }
    }
    this.currentUtterance = null;
  }

  pause() {
    if (this.synth && this.synth.speaking && !this.synth.paused) {
      this.synth.pause();
    }
  }

  resume() {
    if (this.synth && this.synth.paused) {
      this.synth.resume();
    }
  }

  isSpeaking() {
    return Boolean(this.synth && this.synth.speaking);
  }
}

export const ttsService = new TTSService();
