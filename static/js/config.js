/**
 * ========================================
 * CONFIGURATION GLOBALE
 * ========================================
 */

const CONFIG = {
  // API
  API_URL: "/api/v2/chat",

  // Session
  SESSION_STORAGE_KEY: "psycho_session_id",
  SESSION_PREFIX: "user",

  // Speech
  SPEECH_LANG: "fr-FR",
  SPEECH_CONTINUOUS: false,
  SPEECH_INTERIM_RESULTS: false,
  SPEECH_MAX_ALTERNATIVES: 1,

  // UI
  TYPING_ANIMATION_DELAY: 500,
  WELCOME_MESSAGE_DELAY: 500,

  // Messages
  MESSAGES: {
    WELCOME:
      "Bonjour ! Je suis votre assistant psychologique. Comment vous sentez-vous aujourd'hui ?",
    NETWORK_ERROR:
      "❌ Impossible de joindre le serveur. Vérifiez votre connexion.",
    EMPTY_TEXT_WARNING: "⚠️ Texte vide ignoré",
  },

  // Debugging
  DEBUG: true,
};

// Export sécurisé
if (typeof window !== "undefined") {
  window.CONFIG = CONFIG;
}
