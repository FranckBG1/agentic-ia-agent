class AgendaManager {
  constructor() {
    // Get the existing container from HTML
    this.container = document.getElementById("agenda-container");
    if (!this.container) {
      console.log(
        " AgendaManager: Container non trouvé, utilisation du mode modal uniquement"
      );
    }

    this.currentProposals = [];
  }

  displayProposals(proposals = []) {
    console.log(" [AGENDA] displayProposals appelé avec:", proposals);

    this.currentProposals = proposals || [];
    // If no proposals, nothing to display
    if (!this.currentProposals || this.currentProposals.length === 0) {
      console.log("⚠️ [AGENDA] Pas de propositions à afficher");
      return;
    }

    // Display initial message in chat
    if (!window.UI) {
      console.error("❌ [AGENDA] window.UI non disponible!");
      return;
    }

    if (typeof window.UI.displayMessage !== "function") {
      console.error("❌ [AGENDA] UI.displayMessage n'est pas une fonction!");
      return;
    }

    console.log(" [AGENDA] Affichage message initial dans le chat");
    window.UI.displayMessage(
      "system",
      "Voici les événements que je vous propose de supprimer de votre agenda. Cochez ceux que vous souhaitez conserver."
    );

    // Create overlay
    this._closeOverlay();
    const overlay = document.createElement("div");
    overlay.className = "agenda-overlay";

    const card = document.createElement("div");
    card.className = "agenda-card agenda-modal-card";

    // Build inner HTML
    const listHtml = this.currentProposals
      .map((p) => {
        const title = p.event_title || p.title || "Sans titre";
        const start = p.event_start || p.start || "";
        const duration = p.duration || p.duration_hours || "";
        const reason = p.reason
          ? `<div class=\"proposal-reason\">${p.reason}</div>`
          : "";
        return `
          <div class=\"proposal-item\">
            <label class=\"proposal-label\">
              <input type=\"checkbox\" data-event-id=\"${
                p.event_id
              }\" checked />
              <span class=\"proposal-meta\">${title} ${
          start ? "— " + start : ""
        } ${duration ? "— " + duration + "h" : ""}</span>
            </label>
            ${reason}
          </div>`;
      })
      .join("\n");

    card.innerHTML = `
      <button class="agenda-close" aria-label="Fermer">×</button>
      <h3>📋 Propositions pour alléger votre agenda</h3>
      <div class="proposals-list">${listHtml}</div>
      <div class="agenda-actions">
        <button class="agenda-confirm btn-primary">Confirmer suppressions</button>
        <button class="agenda-cancel btn-secondary">Annuler</button>
      </div>
    `;

    overlay.appendChild(card);
    document.body.appendChild(overlay);
    this.overlay = overlay;

    // events
    const confirmBtn = card.querySelector(".agenda-confirm");
    const cancelBtn = card.querySelector(".agenda-cancel");
    const closeBtn = card.querySelector(".agenda-close");

    confirmBtn.addEventListener("click", () => this._onConfirm());
    cancelBtn.addEventListener("click", () => this._onCancel());
    closeBtn.addEventListener("click", () => this._onCancel());

    // focus management
    card.setAttribute("tabindex", "-1");
    card.focus();
  }

  hide() {
    this._closeOverlay();
    if (this.container) this.container.style.display = "none";
  }

  _closeOverlay() {
    if (this.overlay) {
      try {
        this.overlay.remove();
      } catch (e) {}
      this.overlay = null;
    }
  }

  async _onConfirm() {
    // Collect selected event ids from overlay (modal)
    const root = this.overlay || this.container;
    if (!root) {
      console.error(
        "❌ AgendaManager: Pas de container trouvé pour la confirmation"
      );
      return;
    }

    const boxes = root.querySelectorAll("input[type=checkbox][data-event-id]");
    const eventIds = [];
    boxes.forEach((cb) => {
      if (cb.checked) eventIds.push(cb.getAttribute("data-event-id"));
    });

    if (eventIds.length === 0) {
      if (window.UI && typeof window.UI.displayMessage === "function") {
        window.UI.displayMessage(
          "system",
          "⚠️ Aucun événement sélectionné pour suppression."
        );
      } else {
        alert("Aucun événement sélectionné.");
      }
      return;
    }

    // disable buttons to avoid double-click
    const buttons = root.querySelectorAll("button");
    buttons.forEach((b) => (b.disabled = true));

    // call API wrapper if available
    if (!window.API || typeof window.API.confirmAgendaChanges !== "function") {
      console.error("API.confirmAgendaChanges non disponible");
      alert("Action impossible: API indisponible.");
      buttons.forEach((b) => (b.disabled = false));
      return;
    }

    const result = await window.API.confirmAgendaChanges(eventIds, "apply");

    if (!result || !result.success) {
      console.error("Erreur confirmAgendaChanges:", result);
      const errorMessage =
        "❌ Erreur lors de l'application des changements: " +
        (result?.error || "Erreur inconnue");

      if (window.UI && typeof window.UI.displayMessage === "function") {
        window.UI.displayMessage("system", errorMessage);
      } else {
        alert(errorMessage);
      }
      buttons.forEach((b) => (b.disabled = false));
      // keep overlay open for retry
      return;
    }

    // Show a summary in the chat if UI exists
    const summary = result.data;
    const successCount = summary.applied_count || 0;
    const attempted = summary.attempted_count || eventIds.length;

    const message = `✅ ${successCount}/${attempted} suppression(s) effectuée(s).`;

    if (window.UI && typeof window.UI.displayMessage === "function") {
      window.UI.displayMessage("system", message);
    } else {
      alert(message);
    }
    // hide the modal overlay
    this._closeOverlay();
  }

  async _onCancel() {
    // Optionally notify backend about cancellation
    if (window.API && typeof window.API.confirmAgendaChanges === "function") {
      // We can call with empty list and action cancel
      await window.API.confirmAgendaChanges([], "cancel");
    }

    // hide UI / overlay
    this._closeOverlay();

    if (window.UI && typeof window.UI.displayMessage === "function") {
      window.UI.displayMessage(
        "system",
        "Les propositions d'allègement ont été annulées."
      );
    }
  }
}

if (typeof window !== "undefined") {
  window.AgendaManager = AgendaManager;
}
