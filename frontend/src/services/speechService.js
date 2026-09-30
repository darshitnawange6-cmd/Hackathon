// Web Speech API Speech-to-Text Abstraction

class SpeechService {
  constructor() {
    this.recognition = null;
    this.isListening = false;
    this.callbacks = {};
    this.init();
  }

  init() {
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      console.warn('Web Speech API is not supported in this browser.');
      return;
    }

    try {
      this.recognition = new SpeechRecognition();
      this.recognition.continuous = false; // We want clear sentence chunks for queries
      this.recognition.interimResults = true;
      this.recognition.lang = 'en-US';
      this.recognition.maxAlternatives = 1;

      this.recognition.onstart = () => {
        this.isListening = true;
        if (this.callbacks.onStart) this.callbacks.onStart();
      };

      this.recognition.onresult = (event) => {
        let interimTranscript = '';
        let finalTranscript = '';

        for (let i = event.resultIndex; i < event.results.length; ++i) {
          const transcript = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            finalTranscript += transcript;
          } else {
            interimTranscript += transcript;
          }
        }

        if (interimTranscript && this.callbacks.onInterim) {
          this.callbacks.onInterim(interimTranscript);
        }

        if (finalTranscript && this.callbacks.onResult) {
          this.callbacks.onResult(finalTranscript.trim());
        }
      };

      this.recognition.onerror = (event) => {
        console.warn('Speech recognition error event:', event.error);
        this.isListening = false;
        let userFriendlyMsg = 'Speech recognition error.';
        if (event.error === 'not-allowed' || event.error === 'service-not-allowed') {
          userFriendlyMsg = 'Microphone access was denied. Please allow microphone permissions in your browser address bar.';
        } else if (event.error === 'no-speech') {
          userFriendlyMsg = 'No speech detected. Please try speaking again.';
        } else if (event.error === 'network') {
          userFriendlyMsg = 'Speech network error. You can still type your question below.';
        }
        if (this.callbacks.onError) this.callbacks.onError(userFriendlyMsg, event.error);
      };

      this.recognition.onend = () => {
        this.isListening = false;
        if (this.callbacks.onEnd) this.callbacks.onEnd();
      };
    } catch (e) {
      console.error('Failed to initialize SpeechRecognition:', e);
    }
  }

  isSupported() {
    return Boolean(window.SpeechRecognition || window.webkitSpeechRecognition);
  }

  startListening({ onStart, onInterim, onResult, onError, onEnd } = {}) {
    if (!this.recognition) {
      if (onError) onError('Speech Recognition is not available on this browser. Try Google Chrome, Edge, or use text input.');
      return false;
    }

    if (this.isListening) {
      this.stopListening();
    }

    this.callbacks = { onStart, onInterim, onResult, onError, onEnd };

    try {
      this.recognition.start();
      return true;
    } catch (err) {
      console.warn('Recognition start exception:', err);
      if (onError) onError('Could not start microphone. Please check permissions.');
      return false;
    }
  }

  stopListening() {
    if (this.recognition && this.isListening) {
      try {
        this.recognition.stop();
      } catch (err) {
        console.warn('Recognition stop error:', err);
      }
    }
    this.isListening = false;
  }

  abortListening() {
    if (this.recognition) {
      try {
        this.recognition.abort();
      } catch (err) {
        console.warn('Recognition abort error:', err);
      }
    }
    this.isListening = false;
  }
}

export const speechService = new SpeechService();
