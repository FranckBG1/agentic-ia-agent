/**
 * ========================================
 * GESTION DE SESSION PERSISTANTE (compatible WebView)
 * ========================================
 */

const SessionManager = {
  /**
   * Récupère ou crée un session_id unique
   */
  getOrCreateSessionId() {
    if (typeof CONFIG === "undefined") {
      console.error(
        "❌ CONFIG n'est pas chargé. Assurez-vous que config.js est inclus avant session.js."
      );
      return `error-config-missing-${Date.now()}`;
    }

    let sessionId = localStorage.getItem(CONFIG.SESSION_STORAGE_KEY);

    if (!sessionId) {
      const timestamp = Date.now();
      const random = Math.random().toString(36).substring(2, 11);
      sessionId = `${CONFIG.SESSION_PREFIX}-${timestamp}-${random}`;

      localStorage.setItem(CONFIG.SESSION_STORAGE_KEY, sessionId);

      if (CONFIG.DEBUG) {
        console.log("✅ Nouvelle session créée:", sessionId);
      }
    } else {
      if (CONFIG.DEBUG) {
        console.log("♻️ Session existante réutilisée:", sessionId);
      }
    }

    return sessionId;
  },

  /**
   * Réinitialise la session (nouvelle conversation)
   * — Version mobile-friendly : pas de popup confirm()
   */
  reset() {
    try {
      // Supprimer directement la session
      localStorage.removeItem(CONFIG.SESSION_STORAGE_KEY);

      if (CONFIG.DEBUG) {
        console.log("🧹 Session réinitialisée (sans confirmation)");
      }

      // Recharge la page immédiatement
      window.location.reload();
    } catch (err) {
      console.error("❌ Erreur lors du reset de session :", err);
    }
  },

  /**
   * Retourne l'ID de session actuel
   */
  getCurrentSessionId() {
    return localStorage.getItem(CONFIG.SESSION_STORAGE_KEY);
  },
};

// Export global
if (typeof window !== "undefined") {
  window.SessionManager = SessionManager;
}
