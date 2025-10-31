/**
 * ========================================
 * WEB SPEECH API - RECONNAISSANCE VOCALE
 * ========================================
 */

const SpeechManager = {
  recognition: null,
  isRecording: false,
  onTranscriptCallback: null,

  /**
   * Initialise la reconnaissance vocale
   */
  init(onTranscript) {
    // Dépendances
    if (typeof UI === "undefined" || typeof CONFIG === "undefined") {
      console.error(
        "❌ UI ou CONFIG non chargé. Assurez-vous que ui.js et config.js sont inclus avant speech.js."
      );
      return false;
    }

    if (
      !("webkitSpeechRecognition" in window) &&
      !("SpeechRecognition" in window)
    ) {
      console.error("❌ Web Speech API non supportée");
      UI.updateStatus(
        "⚠️ Reconnaissance vocale non disponible (utilisez Chrome/Edge)",
        "error"
      );
      UI.micButton.disabled = true;
      return false;
    }

    this.onTranscriptCallback = onTranscript;

    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;
    this.recognition = new SpeechRecognition();

    this.recognition.lang = CONFIG.SPEECH_LANG;
    this.recognition.continuous = CONFIG.SPEECH_CONTINUOUS;
    this.recognition.interimResults = CONFIG.SPEECH_INTERIM_RESULTS;
    this.recognition.maxAlternatives = CONFIG.SPEECH_MAX_ALTERNATIVES;

    this.recognition.onstart = () => this._onStart();
    this.recognition.onresult = (event) => this._onResult(event);
    this.recognition.onerror = (event) => this._onError(event);
    this.recognition.onend = () => this._onEnd();

    if (CONFIG.DEBUG) {
      console.log("✅ Web Speech API initialisée");
    }

    return true;
  },

  /**
   * Démarre/arrête l'enregistrement
   */
  toggle() {
    if (!this.recognition) {
      console.error("❌ Speech recognition non initialisée");
      return;
    }

    if (this.isRecording) {
      this.stop();
    } else {
      this.start();
    }
  },

  /**
   * Démarre l'enregistrement
   */
  start() {
    try {
      this.recognition.start();
    } catch (e) {
      console.warn("⚠️ Reconnaissance déjà en cours");
    }
  },

  /**
   * Arrête l'enregistrement
   */
  stop() {
    this.recognition.stop();
  },

  // --- Événements internes ---

  _onStart() {
    if (CONFIG.DEBUG) {
      console.log("🎤 Enregistrement démarré");
    }

    this.isRecording = true;
    UI.micButton.classList.add("recording");
    UI.micButton.textContent = "🔴 Arrété...";
    UI.updateStatus("🎤 Parlez maintenant...", "warning");
  },

  _onResult(event) {
    const transcript = event.results[0][0].transcript;
    const confidence = event.results[0][0].confidence;

    // Callback vers main.js
    if (this.onTranscriptCallback) {
      this.onTranscriptCallback(transcript);
    }
  },

  _onError(event) {
    console.error("❌ Erreur Speech API:", event.error);

    let errorMsg = "Erreur vocale";
    switch (event.error) {
      case "no-speech":
        errorMsg = "Aucune parole détectée. Réessayez.";
        break;
      case "audio-capture":
        errorMsg = "Microphone inaccessible";
        break;
      case "not-allowed":
        errorMsg = "Permission microphone refusée";
        break;
      case "network":
        errorMsg = "Erreur réseau";
        break;
    }

    UI.updateStatus(`❌ ${errorMsg}`, "error");
    this._resetUI();
  },

  _onEnd() {
    if (CONFIG.DEBUG) {
      console.log("⏹️ Enregistrement terminé");
    }
    this._resetUI();
  },

  _resetUI() {
    this.isRecording = false;
    UI.micButton.classList.remove("recording");
    UI.micButton.textContent = "🎤 Parler";
  },
};

// Export global
if (typeof window !== "undefined") {
  window.SpeechManager = SpeechManager;
}
