/**
 * ════════════════════════════════════════════════════════
 *  MAIN.JS - Orchestrateur principal
 * ════════════════════════════════════════════════════════
 */

(function () {
  "use strict";

  // Variables globales
  let SESSION_ID = null;

  /**
   * Initialisation de l'application
   */
  function init() {
    // Vérifier les dépendances
    const requiredModules = ["UI", "API", "SessionManager", "BookingManager"];
    const missing = requiredModules.filter((mod) => !window[mod]);

    if (missing.length > 0) {
      console.error("❌ Modules manquants:", missing);
      alert("Erreur : Modules JavaScript manquants. Rechargez la page.");
      return;
    }

    // Initialiser l'UI
    UI.init();

    // Récupérer/créer session
    SESSION_ID = SessionManager.getOrCreateSessionId();
    UI.displaySessionId(SESSION_ID);

    // Initialiser Speech API
    const speechSupported = SpeechManager.init(handleTranscript);

    if (speechSupported) {
      UI.updateStatus(" Prêt (micro activé)", "success");
    } else {
      UI.updateStatus(" Prêt (micro non supporté)", "warning");
    }

    // Event listeners
    setupEventListeners();

    //  Initialiser BookingManager globalement
    window.bookingManagerInstance = new window.BookingManager();

    // Initialiser AgendaManager globalement (pour propositions de suppression)
    if (window.AgendaManager) {
      window.agendaManagerInstance = new window.AgendaManager();
    }

    // Message de bienvenue
    UI.showWelcomeMessage();
  }

  /**
   * Configuration des event listeners
   */
  function setupEventListeners() {
    // Bouton Envoyer
    UI.sendButton.addEventListener("click", handleSendMessage);

    // Touche Entrée
    UI.textInput.addEventListener("keypress", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleSendMessage();
      }
    });

    // Bouton Microphone
    if (UI.micButton) {
      UI.micButton.addEventListener("click", () => {
        SpeechManager.toggle();
      });
    }

    // Bouton Reset
    const resetBtn = document.getElementById("reset-button");
    if (resetBtn) {
      resetBtn.addEventListener("click", () => {
        SessionManager.reset();
      });
    }

    // Bouton Terminer (pour mode urgence)
    const endBtn = document.getElementById("end-conversation-button");
    if (endBtn) {
      endBtn.addEventListener("click", () => {
        endConversation();
      });
    }

    // finalize-button removed (no automatic finalization button)
  }

  /**
   * Termine la conversation et confirme l'envoi au 114
   */
  async function endConversation() {
    if (window.EMERGENCY_MODE) {
      // Désactiver les contrôles
      UI.setControlsEnabled(false);

      // Afficher un message de confirmation
      UI.displayMessage(
        "system",
        "📤 Transmission de la conversation au service d'aide spécialisé (114)..."
      );

      // Simuler un délai d'envoi
      await new Promise((resolve) => setTimeout(resolve, 2000));

      // Confirmer l'envoi dans le bandeau
      confirmHelpServiceSent();

      // Message de confirmation dans le chat
      UI.displayMessage(
        "system",
        "✅ Votre conversation a été transmise avec succès au 114. Un professionnel pourra vous contacter si nécessaire."
      );

      // Cacher le bouton "Terminer"
      const endBtn = document.getElementById("end-conversation-button");
      if (endBtn) {
        endBtn.style.display = "none";
      }
    } else {
      // Mode normal : simplement reset
      SessionManager.reset();
    }
  }

  /**
   * Gestion envoi message
   */
  async function handleSendMessage() {
    const text = UI.getTextInput();

    if (!text) {
      return;
    }

    await sendTextToBackend(text, {});
  }

  /**
   * Gestion transcription vocale
   */
  async function handleTranscript(transcript) {
    await sendTextToBackend(transcript, {});
  }

  /**
   * Envoi message au backend
   */
  async function sendTextToBackend(text, options = {}) {
    // 1. Afficher message utilisateur
    UI.displayMessage("user", text);
    UI.clearTextInput();

    // 2. Désactiver contrôles
    UI.setControlsEnabled(false);
    UI.showTypingIndicator();
    UI.updateStatus("⏳ Envoi en cours...", "warning");

    try {
      // 3. Appel API via API.sendMessage()
      const result = await API.sendMessage(text, SESSION_ID, options);

      // 4. Masquer indicateur
      UI.hideTypingIndicator();

      // 5. Vérifier succès
      if (!result || !result.success) {
        const errorMsg = result?.error || CONFIG.MESSAGES.NETWORK_ERROR;
        UI.displayMessage("bot", `❌ ${errorMsg}`);
        UI.updateStatus("❌ Erreur de réponse", "error");
        UI.setControlsEnabled(true);
        return;
      }

      const data = result.data;
      console.log(" [MAIN] Réponse reçue:", {
        success: result.success,
        data: data,
        is_emergency: data.is_emergency,
        has_analysis: !!data.analysis,
        awaiting_confirmation: data.analysis?.awaiting_confirmation,
        has_proposals: data.analysis?.proposed_changes?.length > 0,
      });

      // 6. GESTION URGENCE - PRIORITÉ ABSOLUE
      if (data.is_emergency === true) {
        console.log("🚨 [MAIN] URGENCE DÉTECTÉE !");

        // Afficher le banner d'urgence en haut de la page
        UI.displayEmergencyMessage(
          "**N'hésitez pas à appeler immédiatement :**",
          data.emergency_details || {}
        );

        // Marquer la session en mode urgence
        window.EMERGENCY_MODE = true;
        window.EMERGENCY_LEVEL = data.emergency_details?.level || "CRITICAL";

        // ✅ Continuer le traitement normal (afficher message bot, etc.)
        // La bannière reste affichée en haut pendant toute la conversation
      }

      // 7. FLUX NORMAL (continue même en cas d'urgence)

      if (data.response) {
        UI.displayMessage("bot", data.response);
      }

      // Afficher les recommandations si présentes (avec message d'introduction et délai)
      // ✅ CORRECTION : Lire depuis data.recommendations (pas data.analysis_results.recommendations)
      if (data.recommendations && data.recommendations.length > 0) {
        // 1. Afficher d'abord un message d'introduction
        setTimeout(() => {
          const introMessage =
            "✨ Sur la base de ce que vous m'avez partagé, j'ai préparé des recommandations personnalisées pour vous aider. Prenez le temps de les explorer ci-dessous :";
          UI.displayMessage("bot", introMessage);

          // 2. Attendre que l'utilisateur lise le message avant d'afficher les cartes
          setTimeout(() => {
            const recommendationsContainer = document.getElementById(
              "recommendations-container"
            );
            if (recommendationsContainer) {
              // Transformer les recommandations textuelles en composants interactifs
              const formattedRecommendations = data.recommendations.map(
                (reco) => {
                  // Si c'est déjà un objet structuré, le retourner tel quel
                  if (typeof reco === "object") return reco;

                  // Analyser le texte pour déterminer le type approprié
                  if (
                    reco.toLowerCase().includes("respiration") ||
                    reco.toLowerCase().includes("respiratoire")
                  ) {
                    return {
                      type: "respiration",
                      titre: "Exercice de respiration",
                      message: reco,
                      breathingSteps: [
                        // Étapes de respiration par défaut
                        { phase: "Inspirez", duration: 4 },
                        { phase: "Retenez", duration: 7 },
                        { phase: "Expirez", duration: 8 },
                      ],
                    };
                  }
                  if (
                    reco.toLowerCase().includes("méditation") ||
                    reco.toLowerCase().includes("meditation")
                  ) {
                    return {
                      type: "meditation",
                      titre: "Méditation guidée",
                      message: reco,
                      video_url: "https://www.youtube.com/embed/xZeFiXMuYM0", // Vidéo de méditation par défaut
                    };
                  }
                  if (reco.toLowerCase().includes("yoga")) {
                    return {
                      type: "yoga",
                      titre: "Exercice de yoga",
                      message: reco,
                      video_url: "https://www.youtube.com/embed/v7AYKMP6rOE", // Vidéo de yoga par défaut
                    };
                  }
                  if (reco.toLowerCase().includes("gratitude")) {
                    return {
                      type: "gratitude",
                      titre: "Journal de gratitude",
                      message: reco,
                    };
                  }
                  if (
                    reco.toLowerCase().includes("productivité") ||
                    reco.toLowerCase().includes("concentration") ||
                    reco.toLowerCase().includes("focus")
                  ) {
                    return {
                      type: "productivite",
                      titre: "Timer Pomodoro",
                      message: reco,
                    };
                  }
                  // Par défaut, créer une carte simple
                  return {
                    type: "simple",
                    message: reco,
                  };
                }
              );

              recommendationsContainer.style.display = "block";
              window.RecommendationsManager.renderRecommendations(
                formattedRecommendations
              );
            }
          }, 1500); // Attendre 1.5s avant d'afficher les cartes
        }, 800); // Attendre 800ms avant le message d'introduction
      }

      if (window.EMERGENCY_MODE) {
        UI.updateStatus(`🚨 MODE URGENCE - Aide disponible ci-dessus`, "error");
      } else {
        const intentInfo = data.intent || "conversation";
        const confidence = data.confidence
          ? `(${(data.confidence * 100).toFixed(0)}%)`
          : "";
        UI.updateStatus(` ${intentInfo} ${confidence}`, "success");
      }

      // 8. SI ORIENTATION NÉCESSAIRE
      console.log("   → needs_booking:", data.needs_booking);
      console.log("   → analysis_results:", !!data.analysis_results);

      // Note: Les propositions calendrier sont maintenant affichées dans les recommandations
      // via le type "agenda" dans recommendations.js

      // 8b. Orientation (réservation)
      if (data.needs_booking && data.slots && data.slots.length > 0) {
        console.log("✅ [MAIN] Créneaux de réservation détectés → Affichage");

        // Attendre 1.5 seconde pour laisser lire la réponse
        setTimeout(() => {
          handleOrientation(data);
        }, 1500);
      } else {
        console.log("ℹ️ [MAIN] Pas de créneaux de réservation");
      }
    } catch (error) {
      console.error("❌ Erreur sendTextToBackend:", error);
      UI.hideTypingIndicator();
      UI.displayMessage("bot", "❌ Une erreur inattendue s'est produite.");
      UI.updateStatus("❌ Erreur", "error");
    }

    // 9. Réactiver contrôles
    UI.setControlsEnabled(true);
  }

  // ═══════════════════════════════════════════════════════════
  // FONCTIONS OBSOLÈTES SUPPRIMÉES
  // displayEmergencyMessage() → Maintenant dans UI.displayEmergencyMessage()
  // displayEmergencyContacts() → Intégré dans UI.displayEmergencyMessage()
  // playEmergencySound() → Optionnel, retiré pour simplifier
  // ═══════════════════════════════════════════════════════════

  function showEmergencyBanner() {
    // Vérifier si bandeau existe déjà
    const existing = document.getElementById("emergency-banner");
    if (existing) {
      console.log("⚠️ [BANNER] Bandeau existe déjà, annulation");
      return;
    }

    const banner = document.createElement("div");
    banner.id = "emergency-banner";
    banner.className = "emergency-banner";
    banner.innerHTML = `
            <span style="font-size: 24px;">🚨</span>
            <span>A contacter en cas d'urgence :  09 72 39 40 50 </span>
            <a href="tel:0972394050" class="emergency-banner-button">
                📞 Appeler maintenant
            </a>
        `;

    // Insérer au début du body
    document.body.insertBefore(banner, document.body.firstChild);
    document.body.classList.add("emergency-mode");
  }

  /**
   * Affiche un bandeau persistant indiquant que la conversation sera transmise au service d'aide
   */
  function showHelpServiceBanner() {
    // Vérifier si bandeau existe déjà
    const existing = document.getElementById("help-service-banner");
    if (existing) {
      console.log("⚠️ [BANNER] Bandeau service d'aide existe déjà, annulation");
      return;
    }

    const banner = document.createElement("div");
    banner.id = "help-service-banner";
    banner.className = "help-service-banner";
    banner.innerHTML = `
            <span style="font-size: 20px;">📨</span>
            <span>Cette conversation sera transmise au 114 (service d'aide spécialisé) à la fin de la discussion</span>
        `;

    // Insérer après le bandeau d'urgence si présent, sinon au début du body
    const emergencyBanner = document.getElementById("emergency-banner");
    if (emergencyBanner && emergencyBanner.nextSibling) {
      document.body.insertBefore(banner, emergencyBanner.nextSibling);
    } else if (emergencyBanner) {
      emergencyBanner.parentNode.insertBefore(
        banner,
        emergencyBanner.nextSibling
      );
    } else {
      document.body.insertBefore(banner, document.body.firstChild);
    }
  }

  /**
   * Met à jour le bandeau pour confirmer l'envoi au 114
   */
  function confirmHelpServiceSent() {
    const banner = document.getElementById("help-service-banner");
    if (banner) {
      banner.classList.add("sent");
      banner.innerHTML = `
            <span style="font-size: 20px;">✅</span>
            <span>Conversation transmise avec succès au 114 (service d'aide spécialisé)</span>
        `;
    }
  }

  // Exposer la fonction globalement pour pouvoir l'appeler depuis l'extérieur
  window.confirmHelpServiceSent = confirmHelpServiceSent;

  /**
   * Affiche le bouton "Terminer la conversation" en mode urgence
   */
  function showEndConversationButton() {
    // Vérifier si le bouton existe déjà
    const existing = document.getElementById("end-conversation-button");
    if (existing) {
      existing.style.display = "block";
      return;
    }

    // Créer le bouton
    const endBtn = document.createElement("button");
    endBtn.id = "end-conversation-button";
    endBtn.className = "end-conversation-button";
    endBtn.textContent = "📤 Terminer et envoyer au 114";

    // Ajouter l'event listener
    endBtn.addEventListener("click", () => {
      endConversation();
    });

    // Insérer dans la session-header
    const sessionHeader = document.querySelector(".session-header");
    if (sessionHeader) {
      sessionHeader.appendChild(endBtn);
    }
  }

  /**
   *  Formate le texte avec Markdown simple
   */
  function formatMessageWithMarkdown(text) {
    if (!text) return "";

    return (
      text
        // Gras
        .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
        // Italique
        .replace(/\*(.*?)\*/g, "<em>$1</em>")
        // Listes à puces
        .replace(/^- (.+)$/gm, "<li>$1</li>")
        // Sauts de ligne
        .replace(/\n/g, "<br>")
        // Entourer les listes
        .replace(/(<li>.*<\/li>)/s, "<ul>$1</ul>")
    );
  }

  /**
   * Gestion de l'orientation (réservation rendez-vous)
   */
  function handleOrientation(data) {
    console.log("🔍 [MAIN] handleOrientation appelé");
    console.log("   → needs_booking:", data.needs_booking);
    console.log("   → slots:", data.slots?.length);

    if (data.needs_booking && data.slots && data.slots.length > 0) {
      console.log(`✅ [MAIN] Affichage de ${data.slots.length} créneaux`);
      window.bookingManagerInstance.displaySlots(data.slots);
    } else {
      console.log("ℹ️ [MAIN] Aucun créneau à afficher");
      window.bookingManagerInstance.hide();
    }
  }

  // Démarrage au chargement du DOM
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
