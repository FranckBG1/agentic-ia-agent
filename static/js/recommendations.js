// Composants interactifs pour les recommandations
let interval;
const audioContext = new (window.AudioContext || window.webkitAudioContext)();

// Créer des sons personnalisés pour chaque phase
function createBreathSound(frequency, type = "sine") {
  const oscillator = audioContext.createOscillator();
  const gainNode = audioContext.createGain();

  oscillator.type = type;
  oscillator.frequency.setValueAtTime(frequency, audioContext.currentTime);

  gainNode.gain.setValueAtTime(0, audioContext.currentTime);

  oscillator.connect(gainNode);
  gainNode.connect(audioContext.destination);

  return { oscillator, gainNode };
}

// Paramètres de respiration par défaut
let defaultSteps = [
  {
    text: "Inspirez pendant 4s",
    scale: 1.3,
    frequency: 196,
    gainStart: 0.2,
    gainEnd: 0,
    duration: 4,
  },
  {
    text: "Retenez 4s",
    scale: 1.3,
    frequency: 294.66,
    gainStart: 0.1,
    gainEnd: 0,
    duration: 4,
  },
  {
    text: "Expirez 4s",
    scale: 1,
    frequency: 164.81,
    gainStart: 0.2,
    gainEnd: 0,
    duration: 4,
  },
  {
    text: "Pause 4s",
    scale: 1,
    frequency: 246.94,
    gainStart: 0.1,
    gainEnd: 0,
    duration: 4,
  },
];

let steps = defaultSteps.map((step) => ({
  ...step,
  // sound now accepts a duration so the gain ramp matches the step duration
  sound: (duration = step.duration || 4) => {
    const sound = createBreathSound(step.frequency);
    const now = audioContext.currentTime;
    // ramp up quickly then down over the step duration
    sound.gainNode.gain.cancelScheduledValues(now);
    sound.gainNode.gain.setValueAtTime(0, now);
    sound.gainNode.gain.linearRampToValueAtTime(
      step.gainStart,
      now + Math.min(0.5, duration * 0.25)
    );
    sound.gainNode.gain.linearRampToValueAtTime(step.gainEnd, now + duration);
    return sound;
  },
}));

// Classes pour gérer les différents composants interactifs
class BreathingExercise {
  constructor(container, steps) {
    this.container = container;
    this.box = container.querySelector(".breathing-box");
    this.instruction = container.querySelector(".breath-instruction");
    this.startBtn = container.querySelector(".start-btn");
    this.stopBtn = container.querySelector(".stop-btn");
    this.steps = steps;
    this.index = 0;
    this.stepTimeout = null;
    this.countdownInterval = null;
    this.currentSound = null;

    this.startBtn.addEventListener("click", () => this.start());
    this.stopBtn.addEventListener("click", () => this.stop());
  }

  start() {
    document.querySelectorAll(".breathing-container").forEach((container) => {
      if (container !== this.container) {
        const exercise = container.exercise;
        if (exercise) exercise.stop();
      }
    });
    // Stop previous run if any
    this.stop();
    this.index = 0;

    const playStep = () => {
      const step = this.steps[this.index];
      const duration = step.duration || 4;
      console.log(
        `[Breathing] Step ${this.index + 1}/${this.steps.length}: ${step.text}`
      );

      // Update instruction with countdown placeholder
      let remaining = Math.ceil(duration);
      this.instruction.innerHTML = `${step.text} <span class="breath-countdown">(${remaining}s)</span>`;

      // Smooth transform
      this.box.style.transition = `transform ${duration}s ease-in-out`;
      // Apply scale
      requestAnimationFrame(() => {
        this.box.style.transform = `scale(${step.scale})`;
      });

      // Stop previous sound
      if (this.currentSound) {
        try {
          this.currentSound.oscillator.stop();
        } catch (e) {
          // ignore if already stopped
        }
        this.currentSound = null;
      }

      // Start new sound and schedule stop
      this.currentSound = step.sound(duration);
      try {
        this.currentSound.oscillator.start();
      } catch (e) {
        // oscillator may have been started already if reused; ignore
      }

      // Countdown update
      this.countdownInterval = setInterval(() => {
        remaining--;
        const span = this.instruction.querySelector(".breath-countdown");
        if (span) span.textContent = `(${Math.max(0, remaining)}s)`;
      }, 1000);

      // Schedule end of this step
      this.stepTimeout = setTimeout(() => {
        // stop sound gracefully
        if (this.currentSound) {
          try {
            this.currentSound.oscillator.stop();
          } catch (e) {}
          this.currentSound = null;
        }

        // move to next
        clearInterval(this.countdownInterval);
        this.countdownInterval = null;
        this.index = (this.index + 1) % this.steps.length;
        playStep();
      }, duration * 1000);
    };

    // start first step
    playStep();
  }

  stop() {
    // Clear all timers and intervals
    if (this.stepTimeout) {
      clearTimeout(this.stepTimeout);
      this.stepTimeout = null;
    }

    if (this.countdownInterval) {
      clearInterval(this.countdownInterval);
      this.countdownInterval = null;
    }

    // Stop sound
    if (this.currentSound) {
      try {
        this.currentSound.oscillator.stop();
      } catch (e) {
        // ignore if already stopped
      }
      this.currentSound = null;
    }

    // Reset box to initial state
    this.box.style.transform = "scale(1)";
    this.box.style.transition = "";

    // Reset instruction
    this.instruction.textContent = "Cliquez sur Démarrer pour commencer";

    // Reset index
    this.index = 0;

    console.log("[Breathing] Exercise stopped");
  }

  loadEntries() {
    this.entriesList.innerHTML = this.entries
      .map(
        (entry) => `<li>
        <div>${entry.text}</div>
        <small>${entry.date}</small>
      </li>`
      )
      .join("");
  }
}

class PomodoroTimer {
  constructor(container) {
    this.container = container;
    this.display = container.querySelector(".timer-display");
    this.progressBar = container.querySelector(".progress-bar");
    this.startBtn = container.querySelector(".start-timer-btn");
    this.pauseBtn = container.querySelector(".pause-timer-btn");
    this.resetBtn = container.querySelector(".reset-timer-btn");

    this.totalTime = 25 * 60;
    this.timeLeft = this.totalTime;
    this.isRunning = false;

    this.startBtn.addEventListener("click", () => this.start());
    this.pauseBtn.addEventListener("click", () => this.pause());
    this.resetBtn.addEventListener("click", () => this.reset());
  }

  start() {
    if (!this.isRunning) {
      this.isRunning = true;
      this.startBtn.disabled = true;
      this.pauseBtn.disabled = false;
      this.timer = setInterval(() => this.tick(), 1000);
    }
  }

  pause() {
    this.isRunning = false;
    this.startBtn.disabled = false;
    this.pauseBtn.disabled = true;
    clearInterval(this.timer);
  }

  reset() {
    this.pause();
    this.timeLeft = this.totalTime;
    this.updateDisplay();
    this.progressBar.style.width = "0%";
  }

  tick() {
    if (this.timeLeft > 0) {
      this.timeLeft--;
      this.updateDisplay();
      const progress =
        ((this.totalTime - this.timeLeft) / this.totalTime) * 100;
      this.progressBar.style.width = `${progress}%`;
    } else {
      this.pause();
      alert("Temps écoulé ! Prenez une pause.");
    }
  }

  updateDisplay() {
    const minutes = Math.floor(this.timeLeft / 60);
    const seconds = this.timeLeft % 60;
    this.display.textContent = `${minutes.toString().padStart(2, "0")}:${seconds
      .toString()
      .padStart(2, "0")}`;
  }
}

class YogaExercise {
  constructor(container) {
    this.container = container;
    this.timeDisplay = container.querySelector(".time-display");
    this.timerCircle = container.querySelector(".timer-circle");
    this.startBtn = container.querySelector(".start-yoga-btn");
    this.stopBtn = container.querySelector(".stop-yoga-btn");
    this.duration = 180;
    this.timeLeft = this.duration;
    this.interval = null;

    this.startBtn.addEventListener("click", () => this.start());
    this.stopBtn.addEventListener("click", () => this.stop());
  }

  start() {
    if (!this.interval) {
      this.timerCircle.classList.add("active");
      this.interval = setInterval(() => {
        this.timeLeft--;
        this.updateDisplay();
        if (this.timeLeft <= 0) {
          this.stop();
          alert("Excellent ! Vous avez terminé la pose de yoga.");
        }
      }, 1000);
    }
  }

  stop() {
    if (this.interval) {
      clearInterval(this.interval);
      this.interval = null;
      this.timerCircle.classList.remove("active");
    }
    this.timeLeft = this.duration;
    this.updateDisplay();
  }

  updateDisplay() {
    const minutes = Math.floor(this.timeLeft / 60);
    const seconds = this.timeLeft % 60;
    this.timeDisplay.textContent = `${minutes
      .toString()
      .padStart(2, "0")}:${seconds.toString().padStart(2, "0")}`;
  }
}

// Classe VideoPlayer (doit être définie avant usage)
class VideoPlayer {
  constructor(container) {
    this.container = container;
    this.preview = container.querySelector(".video-preview");
    this.videoContainer = container.querySelector(".video-container");
    this.iframe = this.videoContainer.querySelector("iframe");
    this.videoUrl = this.preview.dataset.video;
    this.preview.addEventListener("click", () => this.play());
  }
  play() {
    this.iframe.src = this.videoUrl;
    this.preview.classList.add("hidden");
    this.videoContainer.classList.remove("hidden");
  }
}

// Classe GratitudeJournal pour gérer le journal de gratitude
class GratitudeJournal {
  constructor(container) {
    this.container = container;
    this.textarea = container.querySelector(".gratitude-entry");
    this.saveBtn = container.querySelector(".save-entry-btn");
    this.entriesList = container.querySelector(".entries-list");

    // Charger les entrées sauvegardées
    this.loadEntries();

    // Événement de sauvegarde
    if (this.saveBtn) {
      this.saveBtn.addEventListener("click", () => this.saveEntry());
    }
  }

  saveEntry() {
    const entry = this.textarea.value.trim();
    if (!entry) {
      alert("Veuillez écrire quelque chose avant de sauvegarder.");
      return;
    }

    // Récupérer les entrées existantes
    let entries = JSON.parse(localStorage.getItem("gratitudeEntries") || "[]");

    // Ajouter la nouvelle entrée avec la date
    entries.unshift({
      text: entry,
      date: new Date().toLocaleDateString("fr-FR"),
    });

    // Limiter à 10 entrées
    if (entries.length > 10) {
      entries = entries.slice(0, 10);
    }

    // Sauvegarder
    localStorage.setItem("gratitudeEntries", JSON.stringify(entries));

    // Réinitialiser le champ
    this.textarea.value = "";

    // Recharger l'affichage
    this.loadEntries();

    // Feedback visuel
    this.saveBtn.textContent = "✅ Sauvegardé !";
    setTimeout(() => {
      this.saveBtn.textContent = "💝 Sauvegarder";
    }, 2000);
  }

  loadEntries() {
    const entries = JSON.parse(
      localStorage.getItem("gratitudeEntries") || "[]"
    );

    if (entries.length === 0) {
      this.entriesList.innerHTML = "<li>Aucune entrée pour le moment</li>";
      return;
    }

    this.entriesList.innerHTML = entries
      .map((entry) => `<li><strong>${entry.date}</strong> : ${entry.text}</li>`)
      .join("");
  }
}

// Initialisation des composants
function initializeRecommendationComponents() {
  // Initialiser les exercices de respiration (toujours avec les étapes enrichies)
  document.querySelectorAll(".breathing-container").forEach((container) => {
    container.exercise = new BreathingExercise(container, steps);
  });

  // Initialiser les lecteurs vidéo
  document.querySelectorAll(".media-player").forEach((container) => {
    new VideoPlayer(container);
  });

  // Initialiser les journaux de gratitude
  document.querySelectorAll(".gratitude-journal").forEach((container) => {
    new GratitudeJournal(container);
  });

  // Initialiser les minuteurs Pomodoro
  document.querySelectorAll(".pomodoro-timer").forEach((container) => {
    new PomodoroTimer(container);
  });

  // Initialiser les exercices de yoga
  document.querySelectorAll(".yoga-container").forEach((container) => {
    new YogaExercise(container);
  });

  // Gestionnaires pour les boutons de bascule des instructions
  document.querySelectorAll(".toggle-instructions-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const instructions = btn.nextElementSibling;
      instructions.classList.toggle("hidden");
      btn.textContent = instructions.classList.contains("hidden")
        ? "📖 Voir les conseils"
        : "📖 Masquer les conseils";
    });
  });
}

// Function to render recommendations
function renderRecommendations(recommendations) {
  const container = document.querySelector(".recommendations-grid");
  if (!container) return;

  container.innerHTML = recommendations
    .map((reco) => {
      if (typeof reco === "string") {
        return `
        <div class="recommendation-card simple">
          <div class="tip-content">
            <div class="tip-icon">💡</div>
            <p>${reco}</p>
          </div>
        </div>`;
      }

      // Handle different types of recommendations
      switch (reco.type) {
        case "respiration":
          return createBreathingCard(reco);
        case "yoga":
          return createYogaCard(reco);
        case "meditation":
        case "relaxation":
        case "sommeil":
        case "energie":
        case "focus":
          return createMediaCard(reco);
        case "gratitude":
          return createGratitudeCard(reco);
        case "productivite":
          return createPomodoroCard(reco);
        case "agenda":
          return createAgendaCard(reco);
        default:
          return createSimpleCard(reco);
      }
    })
    .join("");

  // Initialize interactive components
  initializeRecommendationComponents();
}

// Helper functions to create different card types
function createBreathingCard(reco) {
  return `
    <div class="recommendation-card breathing" data-breathing-steps='${JSON.stringify(
      reco.breathingSteps || []
    )}'>
      <h3>${reco.titre || "Exercice de respiration"}</h3>
      <p>${reco.message || ""}</p>
      <div class="breathing-container">
        <div class="breathing-box"></div>
        <p class="breath-instruction">Cliquez sur Démarrer pour commencer</p>
        <div class="controls">
          <button class="start-btn">▶️ Démarrer</button>
          <button class="stop-btn">⏹️ Stop</button>
        </div>
      </div>
    </div>`;
}

function createYogaCard(reco) {
  return `
    <div class="recommendation-card yoga">
      <h3>${reco.titre || "Yoga"}</h3>
      <p>${reco.message || ""}</p>
      <div class="yoga-container">
        <div class="yoga-video">
          <iframe src="${
            reco.video_url || ""
          }" frameborder="0" allowfullscreen></iframe>
        </div>
        <div class="meditation-timer">
          <div class="timer-circle">
            <span class="time-display">03:00</span>
          </div>
          <div class="controls">
            <button class="start-yoga-btn">▶️ Commencer</button>
            <button class="stop-yoga-btn">⏹️ Arrêter</button>
          </div>
        </div>
      </div>
    </div>`;
}

function createMediaCard(reco) {
  return `
    <div class="recommendation-card media">
      <h3>${reco.titre || ""}</h3>
      <p>${reco.message || ""}</p>
      ${
        reco.lien
          ? `
        <div class="media-player">
          <div class="video-preview" data-video="${reco.lien.replace(
            "watch?v=",
            "embed/"
          )}">
            <div class="play-overlay">
              <button class="play-btn">▶️ Lancer la vidéo</button>
            </div>
          </div>
          <div class="video-container hidden">
            <iframe src="about:blank" allowfullscreen></iframe>
          </div>
        </div>
      `
          : ""
      }
    </div>`;
}

function createGratitudeCard(reco) {
  return `
    <div class="recommendation-card gratitude">
      <h3>${reco.titre || "Journal de gratitude"}</h3>
      <p>${reco.message || ""}</p>
      <div class="gratitude-journal">
        <div class="journal-entries">
          <textarea class="gratitude-entry" placeholder="Notez ici quelque chose de positif..."></textarea>
          <div class="entry-list"></div>
        </div>
        <button class="save-entry-btn">💝 Sauvegarder</button>
        <div class="saved-entries">
          <h4>Vos moments de gratitude :</h4>
          <ul class="entries-list"></ul>
        </div>
      </div>
    </div>`;
}

function createPomodoroCard(reco) {
  return `
    <div class="recommendation-card productivity">
      <h3>${reco.titre || "Timer Pomodoro"}</h3>
      <p>${reco.message || ""}</p>
      <div class="pomodoro-timer">
        <div class="timer-display">25:00</div>
        <div class="timer-controls">
          <button class="start-timer-btn">▶️ Démarrer</button>
          <button class="pause-timer-btn" disabled>⏸️ Pause</button>
          <button class="reset-timer-btn">🔄 Réinitialiser</button>
        </div>
        <div class="timer-progress">
          <div class="progress-bar"></div>
        </div>
      </div>
    </div>`;
}

function createSimpleCard(reco) {
  return `
    <div class="recommendation-card simple">
      <div class="tip-content">
        <div class="tip-icon">💡</div>
        <p>${reco.message || ""}</p>
      </div>
    </div>`;
}

function createAgendaCard(reco) {
  const proposedChanges = reco.proposed_changes || [];

  const eventsHTML = proposedChanges
    .map(
      (change, index) => `
    <div class="agenda-event-item">
      <input type="checkbox" 
             id="event-${index}" 
             class="event-checkbox" 
             data-event-id="${change.event_id}"
             checked>
      <label for="event-${index}">
        <div class="event-details">
          <strong>${change.event_title}</strong>
          <span class="event-time">${change.event_start} • ${change.duration}h</span>
          <span class="event-reason">${change.reason}</span>
        </div>
      </label>
    </div>
  `
    )
    .join("");

  return `
    <div class="recommendation-card agenda" data-awaiting-confirmation="${
      reco.awaiting_confirmation
    }">
      <h3>🗓️ ${reco.titre || "Alléger votre agenda"}</h3>
      <p class="agenda-message">${reco.message}</p>
      
      <div class="agenda-events-list">
        ${eventsHTML}
      </div>
      
      <div class="agenda-actions">
        <button class="btn-confirm-agenda" onclick="confirmAgendaChanges()">
          ✅ Confirmer les suppressions
        </button>
        <button class="btn-cancel-agenda" onclick="cancelAgendaChanges()">
          ❌ Annuler
        </button>
      </div>
      
      <div class="agenda-result" style="display: none;"></div>
    </div>`;
}

// Fonctions globales pour gérer les actions agenda
window.confirmAgendaChanges = function () {
  const checkedBoxes = document.querySelectorAll(".event-checkbox:checked");
  const eventIds = Array.from(checkedBoxes).map((cb) => cb.dataset.eventId);

  if (eventIds.length === 0) {
    alert("Aucun événement sélectionné");
    return;
  }

  // Appeler directement l'API
  if (window.API && typeof window.API.confirmAgendaChanges === "function") {
    // ✅ DÉSACTIVER immédiatement le bouton pour éviter les doubles clics
    const agendaCard = document.querySelector(".recommendation-card.agenda");
    const validateBtn = agendaCard?.querySelector(
      'button[onclick="validateAgendaChanges()"]'
    );
    if (validateBtn) {
      validateBtn.disabled = true;
      validateBtn.textContent = "⏳ Suppression en cours...";
    }

    window.API.confirmAgendaChanges(eventIds, "apply")
      .then((result) => {
        if (agendaCard) {
          const resultDiv = agendaCard.querySelector(".agenda-result");

          if (result && result.success) {
            const summary = result.data || {};
            const successCount = summary.deleted_count || 0;
            const failedCount = summary.failed_count || 0;

            // Message adapté au résultat
            if (successCount > 0) {
              resultDiv.innerHTML = `<p class="success-message">✅ ${successCount} suppression(s) effectuée(s) avec succès</p>`;
            } else if (failedCount > 0) {
              resultDiv.innerHTML = `<p class="warning-message">⚠️ Événements déjà supprimés ou introuvables</p>`;
            } else {
              resultDiv.innerHTML = `<p class="info-message">ℹ️ Aucune modification effectuée</p>`;
            }

            resultDiv.style.display = "block";

            // ✅ CACHER TOUTE LA CARTE après 2 secondes
            setTimeout(() => {
              if (agendaCard) {
                agendaCard.style.display = "none";
              }
            }, 2000);
          } else {
            resultDiv.innerHTML = `<p class="error-message">❌ Erreur: ${
              result?.error || "Erreur inconnue"
            }</p>`;
            resultDiv.style.display = "block";
          }

          // Cacher la liste et les boutons immédiatement
          const eventsList = agendaCard.querySelector(".agenda-events-list");
          if (eventsList) eventsList.style.display = "none";

          const actionsDiv = agendaCard.querySelector(".agenda-actions");
          if (actionsDiv) actionsDiv.style.display = "none";
        }
      })
      .catch((error) => {
        console.error("❌ Erreur confirmAgendaChanges:", error);

        if (agendaCard) {
          const resultDiv = agendaCard.querySelector(".agenda-result");
          resultDiv.innerHTML = `<p class="error-message">❌ Erreur: ${error.message}</p>`;
          resultDiv.style.display = "block";

          // Cacher aussi en cas d'erreur
          const eventsList = agendaCard.querySelector(".agenda-events-list");
          if (eventsList) eventsList.style.display = "none";

          const actionsDiv = agendaCard.querySelector(".agenda-actions");
          if (actionsDiv) actionsDiv.style.display = "none";
        }
      });
  } else {
    console.error("API.confirmAgendaChanges non disponible");
    alert("Fonction non disponible");
  }
};

window.cancelAgendaChanges = function () {
  const agendaCard = document.querySelector(".recommendation-card.agenda");
  if (agendaCard) {
    agendaCard.querySelector(".agenda-result").innerHTML =
      '<p class="info-message">✅ Aucune modification n\'a été effectuée.</p>';
    agendaCard.querySelector(".agenda-result").style.display = "block";
    agendaCard.querySelector(".agenda-actions").style.display = "none";
  }
};

// Export functions for use in main.js
window.RecommendationsManager = {
  renderRecommendations,
  initializeRecommendationComponents,
};
