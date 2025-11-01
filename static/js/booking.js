/**
 * ========================================
 * Gestion de la réservation
 * ========================================
 */
class BookingManager {
  constructor() {
    this.container = document.getElementById("booking-container");
    this.currentSlots = []; // Stocker les créneaux
  }

  // Affiche les créneaux reçus de /text-intent
  displaySlots(slots) {
    // Stocker les créneaux pour y accéder lors du clic
    this.currentSlots = slots;

    // Efface le contenu précédent
    this.container.innerHTML = "";

    // Crée la carte de réservation
    const card = document.createElement("div");
    card.className = "booking-card";
    card.innerHTML = `
            <h3>📅 Créneaux disponibles</h3>
            <div class="slots-grid"></div>
        `;

    const slotsGrid = card.querySelector(".slots-grid");

    // Ajoute chaque créneau
    slots.forEach((slot, index) => {
      const slotElement = this.createSlotElement(slot, index);
      slotsGrid.appendChild(slotElement);
    });

    this.container.appendChild(card);
    this.container.style.display = "none";

    console.log(" [BOOKING] Créneaux affichés avec succès");
  }

  //  Crée l'élément HTML pour un créneau
  createSlotElement(slot, index) {
    const slotDiv = document.createElement("div");
    slotDiv.className = "slot-item";

    const modeIcon = slot.mode === "téléconsultation" ? "💻" : "🏥";

    slotDiv.innerHTML = `
            <div class="slot-info">
                <div class="slot-date">📅 ${this.formatDate(slot.date)}</div>
                <div class="slot-time">🕐 ${slot.time}</div>
                <div class="slot-provider">👤 ${slot.provider_name}</div>
                <div class="slot-mode">${modeIcon} ${slot.mode}</div>
                ${
                  slot.address
                    ? `<div class="slot-address">📍 ${slot.address}</div>`
                    : ""
                }
            </div>
            <button class="slot-book-btn" data-slot-index="${index}">
                ✅ Réserver
            </button>
        `;

    // Ajouter l'événement de clic
    const bookBtn = slotDiv.querySelector(".slot-book-btn");
    bookBtn.addEventListener("click", () => this.bookSlot(index));

    return slotDiv;
  }

  // Réserve un créneau
  async bookSlot(slotIndex) {
    const slot = this.currentSlots[slotIndex];

    if (!slot) {
      console.error("❌ [BOOKING] Créneau introuvable");
      return;
    }

    // Désactiver tous les boutons
    const buttons = this.container.querySelectorAll(".slot-book-btn");
    buttons.forEach((btn) => {
      btn.disabled = true;
      btn.textContent = "⏳ Réservation...";
    });

    try {
      // Récupérer correctement le session_id
      const sessionId =
        window.SessionManager &&
        typeof window.SessionManager.getSessionId === "function"
          ? window.SessionManager.getSessionId()
          : "demo-session";

      console.log(`📋 [BOOKING] Session ID: ${sessionId}`);

      // Envoyer au backend
      const response = await fetch(`/api/orientation/feedback`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          session_id: sessionId,
          intent: "accepter_booking",
          slot_index: slotIndex,
          slot_data: {
            date: slot.date,
            time: slot.time,
            specialty: slot.specialty || "Consultation",
            doctor: slot.provider_name,
            mode: slot.mode,
            address: slot.address || "À confirmer",
          },
        }),
      });

      const data = await response.json();

      if (data.success) {
        // Masquer les créneaux
        this.hide();

        // Afficher la confirmation
        this.displayConfirmation(slot);
      } else {
        throw new Error(data.error || "Erreur réservation");
      }
    } catch (error) {
      console.error("❌ [BOOKING] Erreur:", error);

      // Afficher message d'erreur
      if (window.UI && window.UI.displayMessage) {
        window.UI.displayMessage(
          "system",
          "❌ Erreur lors de la réservation. Veuillez réessayer."
        );
      }

      // Réactiver les boutons
      buttons.forEach((btn) => {
        btn.disabled = false;
        btn.textContent = "✅ Réserver";
      });
    }
  }

  //  Affiche le message de confirmation
  displayConfirmation(slot) {
    const confirmationHtml = `
            <div class="booking-confirmation">

                <div class="confirmation-header">
                    <span class="confirmation-icon">✅</span>
                    <h3>Créneau réservé !</h3>
                </div>

                <div class="confirmation-details">
                    <p><strong>📅 Date :</strong> ${this.formatDate(
                      slot.date
                    )}</p>
                    <p><strong>🕐 Heure :</strong> ${slot.time}</p>
                    <p><strong>👨‍⚕️ Praticien :</strong> ${slot.provider_name}</p>
                    <p><strong>🏥 Mode :</strong> ${
                      slot.mode === "téléconsultation"
                        ? "💻 Téléconsultation"
                        : "🏥 Cabinet"
                    }</p>
                    ${
                      slot.address
                        ? `<p><strong>📍 Adresse :</strong> ${slot.address}</p>`
                        : ""
                    }
                </div>

                <div class="calendar-status">
                  <div class="calendar-icon">📅</div>
                  <p class="calendar-message">
                    Créneau bien ajouté à  Google Calendar!
                  </p>
                </div>

                <div class="confirmation-actions">
                  <button onclick="window.location.reload()" class="btn-close-confirmation">
                    Terminer
                  </button>
                </div>
            </div>
        `;

    // Afficher dans le container
    this.container.innerHTML = confirmationHtml;
    this.container.style.display = "block";

    // Ou afficher dans le chat si UI existe
    if (window.UI && window.UI.displayMessage) {
      window.UI.displayMessage("system", confirmationHtml);
    }

    console.log("🎉 [BOOKING] Confirmation affichée");
    // Mettre à jour le statut calendrier après 1 seconde
    setTimeout(() => {
      this.updateCalendarStatus(true); // Vous pouvez passer le vrai statut depuis la réponse API
    }, 1000);
  }

  updateCalendarStatus(success) {
    const calendarStatus = document.querySelector(".calendar-status");
    if (!calendarStatus) return;

    if (success) {
      calendarStatus.innerHTML = `
      <div class="calendar-icon">✅</div>
      <p class="calendar-message success">
        Événement ajouté à votre Google Calendar avec succès !
      </p>
    `;
    } else {
      calendarStatus.innerHTML = `
      <div class="calendar-icon">⚠️</div>
      <p class="calendar-message warning">
        L'événement n'a pas pu être synchronisé automatiquement.
        Veuillez l'ajouter manuellement à votre calendrier.
      </p>
    `;
    }
  }

  // Formate la date (2024-03-12 → 12 mars 2024)
  formatDate(dateStr) {
    const date = new Date(dateStr);
    const options = { day: "numeric", month: "long", year: "numeric" };
    return date.toLocaleDateString("fr-FR", options);
  }

  // Cache les créneaux
  hide() {
    if (this.container) {
      this.container.style.display = "none";
      console.log("🧹 [BOOKING] Créneaux masqués");
    }
  }
}

// Export sécurisé pour utilisation dans main.js
if (typeof window !== "undefined") {
  window.BookingManager = BookingManager;
}
