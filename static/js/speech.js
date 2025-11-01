/**
 * ========================================
 * WEB SPEECH API - RECONNAISSANCE VOCALE (SAFE WEBVIEW)
 * ========================================
 */

const SpeechManager = {
  recognition: null,
  isRecording: false,
  onTranscriptCallback: null,
  micBlocked: false,

  init(onTranscript) {
    if (typeof UI === "undefined" || typeof CONFIG === "undefined") {
      console.error("❌ UI ou CONFIG non chargé.");
      return false;
    }

    // Détection WebView (iOS / Android)
    const userAgent = navigator.userAgent || "";
    const isWebView =
      /\bwv\b/.test(userAgent) || // Android WebView
      /WebView/.test(userAgent) || // iOS WebView
      /(iPhone|iPod|iPad).*AppleWebKit(?!.*Safari)/i.test(userAgent);

    if (isWebView) {
      console.warn(
        "⚠️ WebView détectée : désactivation de la reconnaissance vocale."
      );
      UI.updateStatus(
        "Micro désactivé (utilisez la version mobile native)",
        "error"
      );
      UI.micButton.disabled = true;
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

    if (CONFIG.DEBUG) console.log("✅ Web Speech API initialisée");
    return true;
  },

  toggle() {
    if (!this.recognition || this.micBlocked) return;

    if (this.isRecording) {
      this.stop();
    } else {
      this.start();
    }
  },

  start() {
    if (this.micBlocked) return;
    try {
      this.recognition.start();
    } catch (e) {
      console.warn("⚠️ Reconnaissance déjà en cours ou bloquée", e);
    }
  },

  stop() {
    if (this.recognition) this.recognition.stop();
  },

  _onStart() {
    this.isRecording = true;
    UI.micButton.classList.add("recording");
    UI.micButton.textContent = "🔴 Arrêté...";
    UI.updateStatus("🎤 Parlez maintenant...", "warning");
  },

  _onResult(event) {
    const transcript = event.results[0][0].transcript;
    if (this.onTranscriptCallback) this.onTranscriptCallback(transcript);
  },

  _onError(event) {
    console.error("❌ Erreur Speech API:", event.error);
    let errorMsg = "Erreur vocale";

    switch (event.error) {
      case "no-speech":
        errorMsg = "Aucune parole détectée.";
        break;
      case "audio-capture":
        errorMsg = "Microphone inaccessible.";
        this.micBlocked = true;
        break;
      case "not-allowed":
        errorMsg = "Permission micro refusée.";
        this.micBlocked = true;
        break;
      case "network":
        errorMsg = "Erreur réseau.";
        break;
    }

    UI.updateStatus(`❌ ${errorMsg}`, "error");
    this._resetUI();
  },

  _onEnd() {
    if (CONFIG.DEBUG) console.log("⏹️ Enregistrement terminé");
    this._resetUI();
  },

  _resetUI() {
    this.isRecording = false;
    UI.micButton.classList.remove("recording");
    UI.micButton.textContent = "🎤 Parler";
  },
};

if (typeof window !== "undefined") {
  window.SpeechManager = SpeechManager;
}
