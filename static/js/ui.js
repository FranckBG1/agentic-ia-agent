/**
 * ========================================
 * GESTION DE L'INTERFACE UTILISATEUR
 * ========================================
 */

const UI = {
  // Éléments DOM (initialisés dans init())
  chatWindow: null,
  textInput: null,
  sendButton: null,
  micButton: null,
  statusDiv: null,
  sessionIdDisplay: null,

  /**
   * Initialise les références DOM
   */
  init() {
    this.chatWindow = document.getElementById("chat-window");
    this.textInput = document.getElementById("text-input");
    this.sendButton = document.getElementById("send-button");
    this.micButton = document.getElementById("mic-button");
    this.statusDiv = document.getElementById("status");
    this.sessionIdDisplay = document.getElementById("session-id");
  },

  /**
   * Affiche un message dans le chat
   */
  displayMessage(role, text) {
    const msgDiv = document.createElement("div");
    msgDiv.className = `message ${role}`;
    msgDiv.innerHTML = text; // Utiliser innerHTML pour interpréter les balises <b>, <br>, <a> etc.
    this.chatWindow.appendChild(msgDiv);
    this.scrollToBottom();
  },

  /**
   * Affiche un message d'urgence de manière proéminente en haut de la page
   * BANNER UNIQUEMENT = Avis de transmission + numéros d'urgence
   * Le message du bot sera affiché normalement dans le chat
   */
  displayEmergencyMessage(message, emergencyDetails = {}) {
    const emergencyBanner = document.getElementById("emergency-banner");

    if (!emergencyBanner) {
      console.error("Emergency banner element not found");
      return;
    }

    // Banner simple et compact : juste l'essentiel
    let emergencyHTML = `
      <div class="emergency-content">
        <button class="close-emergency" onclick="uiManager.hideEmergencyBanner()">×</button>
        <div class="emergency-header">
          <span class="emergency-icon">🚨</span>
          <strong>AIDE DISPONIBLE</strong>
          <span class="emergency-transmission">📋 Conversation transmise au 3114</span>
        </div>
        <div class="emergency-contacts-compact">
          <strong>3114</strong> (24h/24) • <strong>SOS Amitié</strong> 09 72 39 40 50 • <strong>SAMU</strong> 15 • <strong>Urgences</strong> 112
        </div>
      </div>
    `;

    emergencyBanner.innerHTML = emergencyHTML;
    emergencyBanner.style.display = "block";

    // Scroll en haut pour voir le message
    window.scrollTo({ top: 0, behavior: "smooth" });
  },

  /**
   * Cache le banner d'urgence
   */
  hideEmergencyBanner() {
    const emergencyBanner = document.getElementById("emergency-banner");
    if (emergencyBanner) {
      emergencyBanner.style.display = "none";
    }
  },

  /**
   * Affiche l'indicateur de saisie (typing...)
   */
  showTypingIndicator() {
    // Supprimer l'ancien indicateur s'il existe
    this.hideTypingIndicator();

    const typingDiv = document.createElement("div");
    typingDiv.id = "typing-indicator";
    typingDiv.className = "message bot typing";
    typingDiv.innerHTML = `
      <div class="typing-dots">
        <span></span>
        <span></span>
        <span></span>
      </div>
    `;
    this.chatWindow.appendChild(typingDiv);
    this.scrollToBottom();
  },

  /**
   * Masque l'indicateur de saisie
   */
  hideTypingIndicator() {
    const typingDiv = document.getElementById("typing-indicator");
    if (typingDiv) {
      typingDiv.remove();
    }
  },

  /**
   * Met à jour le statut
   */
  updateStatus(message, type = "") {
    this.statusDiv.textContent = message;
    this.statusDiv.className = type ? `status-${type}` : "";
  },

  /**
   * Active/désactive les contrôles
   */
  setControlsEnabled(enabled) {
    this.sendButton.disabled = !enabled;
    this.micButton.disabled = !enabled;
    this.textInput.disabled = !enabled;
  },

  /**
   * Affiche le session ID
   */
  displaySessionId(sessionId) {
    this.sessionIdDisplay.textContent = sessionId;
  },

  /**
   * Vide le champ de texte
   */
  clearTextInput() {
    this.textInput.value = "";
  },

  /**
   * Récupère le texte saisi
   */
  getTextInput() {
    return this.textInput.value.trim();
  },

  /**
   * Scroll automatique vers le bas
   */
  scrollToBottom() {
    this.chatWindow.scrollTop = this.chatWindow.scrollHeight;
  },

  /**
   * Message de bienvenue
   */
  showWelcomeMessage() {
    setTimeout(() => {
      this.displayMessage("bot", CONFIG.MESSAGES.WELCOME);
    }, CONFIG.WELCOME_MESSAGE_DELAY);
  },
};

// Export global
if (typeof window !== "undefined") {
  window.UI = UI;
}
