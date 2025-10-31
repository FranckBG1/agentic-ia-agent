/**
 * ========================================
 * API - Communication avec le backend
 * ========================================
 */

const API = {
  /**
   * Envoie un message texte au backend
   * @param {string} text - Message utilisateur
   * @param {string} sessionId - ID de session
   * @returns {Promise<{success: boolean, data?: any, error?: string}>}
   */
  async sendMessage(text, sessionId, options = {}) {
    // 1. Validation
    if (!text || !text.trim()) {
      console.warn(CONFIG.MESSAGES.EMPTY_TEXT_WARNING);
      return { success: false, error: "Texte vide" };
    }

    if (!sessionId) {
      return { success: false, error: "Session invalide" };
    }

    const userText = text.trim();
    this._log(` [${sessionId}] Envoi: "${userText}"`);

    // 2. Préparation requête
    const payload = {
      session_id: sessionId,
      text: userText,
      timestamp: Date.now(),
      // options can include analyze_calendar: true/false
      ...(options.analyze_calendar ? { analyze_calendar: true } : {}),
    };

    // 3. Configuration timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(
      () => controller.abort(),
      CONFIG.API_TIMEOUT || 30000
    );

    try {
      // 4. Envoi requête
      const response = await fetch(CONFIG.API_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Session-ID": sessionId,
        },
        body: JSON.stringify(payload),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      // 5. Parse réponse
      const data = await response.json();
      this._log(" Réponse:", {
        rawData: data,
        hasAnalysis: !!data.analysis,
        awaitingConfirmation: data.analysis?.awaiting_confirmation,
        proposedChanges: data.analysis?.proposed_changes,
      });

      // 6. Gestion erreurs HTTP
      if (!response.ok) {
        console.error(`❌ Erreur HTTP ${response.status}:`, data);
        return {
          success: false,
          error: data.error || data.message || `Erreur ${response.status}`,
          statusCode: response.status,
        };
      }

      // 7. Validation données
      if (!data || typeof data !== "object") {
        console.error(" Réponse invalide:", data);
        return {
          success: false,
          error: "Format de réponse invalide",
        };
      }

      return {
        success: true,
        data: data,
      };
    } catch (error) {
      clearTimeout(timeoutId);

      // Gestion timeout
      if (error.name === "AbortError") {
        console.error(" Timeout après 30s");
        return {
          success: false,
          error: "Le serveur ne répond pas",
          timeout: true,
        };
      }

      // Gestion erreurs réseau
      console.error(" Erreur réseau:", error);
      return {
        success: false,
        error: error.message || "Erreur de connexion",
        networkError: true,
      };
    }
  },

  /**
   * Démarre le processus d'orientation
   * @param {Object} analysisData - Données d'analyse psychologique
   * @returns {Promise<{success: boolean, data?: any, error?: string}>}
   */
  async startOrientation(analysisData) {
    // Validation BookingManager
    if (!window.BookingManager) {
      console.error(" BookingManager non chargé");
      return {
        success: false,
        error: "Module de réservation indisponible",
      };
    }

    // Validation données
    if (!analysisData || !analysisData.severity_level) {
      console.error(" Données d'analyse invalides");
      return {
        success: false,
        error: "Données manquantes",
      };
    }

    try {
      const result = await window.BookingManager.startBooking(analysisData);

      if (!result || !result.success) {
        console.error(" Échec réservation:", result);
        return {
          success: false,
          error: result?.error || "Erreur réservation",
        };
      }

      this._log(" Orientation réussie:", result);
      return result;
    } catch (error) {
      console.error("❌ Erreur orientation:", error);
      // On relève l'erreur pour que main.js puisse l'attraper et afficher le message de secours.
      throw error;
    }
  },

  /**
   * Vérifie la santé du backend
   * @returns {Promise<{success: boolean}>}
   */
  async healthCheck() {
    try {
      const response = await fetch(`/health`, {
        method: "GET",
        headers: { "Content-Type": "application/json" },
      });

      const data = await response.json();
      return {
        success: response.ok,
        data: data,
      };
    } catch (error) {
      console.error("❌ Health check échoué:", error);
      return {
        success: false,
        error: error.message,
      };
    }
  },

  /**
   * Confirme ou annule des changements d'agenda proposés
   * @param {Array<string>} eventIds
   * @param {string} action - 'apply' ou 'cancel'
   */
  async confirmAgendaChanges(eventIds, action = "apply") {
    if (!Array.isArray(eventIds)) {
      return { success: false, error: "eventIds must be an array" };
    }

    try {
      const response = await fetch(`/api/agenda/confirm_changes`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ event_ids: eventIds, action }),
      });

      const data = await response.json();
      if (!response.ok) {
        return {
          success: false,
          error: data.error || data.message || "Erreur serveur",
        };
      }

      return { success: true, data };
    } catch (error) {
      console.error("❌ confirmAgendaChanges error:", error);
      return { success: false, error: error.message || "Erreur réseau" };
    }
  },

  /**
   * Log conditionnel (debug uniquement)
   * @private
   */
  _log(...args) {
    if (CONFIG.DEBUG && CONFIG.ENV !== "production") {
      console.log(...args);
    }
  },
};

if (typeof window !== "undefined") {
  window.API = API;
}

// Auto-test au chargement
if (CONFIG.DEBUG) {
  API.healthCheck().then((result) => {
    if (result.success) {
      console.log("✅ Backend accessible");
    } else {
      console.warn("⚠️ Backend inaccessible:", result.error);
    }
  });
}
