# 🧘 Zenflow - Backend Architecture Multi-Agents

Système de chatbot santé mentale avec architecture agentique pour orientation, booking, et gestion d'urgences.

## 📋 Table des matières

- [Architecture](#architecture)
- [Agents Spécialisés](#agents-spécialisés)
- [Machine à États](#machine-à-états)
- [API Endpoints](#api-endpoints)
- [Intégration Frontend](#intégration-frontend)
- [Installation](#installation)
- [Configuration](#configuration)

---

## 🏗️ Architecture

### **Principe : Multi-Agent System avec Orchestrateur Central**

```
┌─────────────────────────────────────────────────────────────┐
│                   ZENFLOW ORCHESTRATOR                      │
│              (adk_orchestrator.py)                          │
│   ┌─────────────────────────────────────────────────────┐  │
│   │        State Machine (6 états)                      │  │
│   │  ROUTING → EMERGENCY → COLLECTING → CONFIRMATION    │  │
│   │           → ANALYZING → FINAL_RESPONSE              │  │
│   └─────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ Emergency    │    │ Collection   │    │ Analysis     │
│ Agent        │    │ Agent        │    │ Agent        │
└──────────────┘    └──────────────┘    └──────────────┘
        ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ Booking      │    │ Calendar     │    │ Recommend.   │
│ Agent        │    │ Agent        │    │ Agent        │
└──────────────┘    └──────────────┘    └──────────────┘
                            │
                    ┌───────┴───────┐
                    ▼               ▼
            ┌──────────────┐ ┌──────────────┐
            │ Conversation │ │ Google       │
            │ Agent        │ │ Calendar API │
            └──────────────┘ └──────────────┘
```

---

## 🤖 Agents Spécialisés

### **1. EmergencyAgent** (`agents/emergency_agent.py`)

**Responsabilité :** Détection et protocole d'urgence (suicide, violence)

**Fonctionnalités :**

- Détection mots-clés critiques (suicide, automutilation)
- Activation protocole 3114 (bannière + numéros urgence)
- Coordination avec BookingAgent pour créneaux IMMÉDIATS
- **Important :** La conversation continue normalement après détection

**Workflow :**

```python
detect_emergency(text) → {is_emergency, level, type, urgency_score}
handle_crisis() → Affiche bannière 3114 + Continue collecte paramètres
```

---

### **2. CollectionAgent** (`agents/collection_agent.py`)

**Responsabilité :** Collecte des 5 paramètres psychologiques

**Paramètres collectés :**

1. **emotion** : État émotionnel (anxiété, stress, tristesse, etc.)
2. **causes** : Origines (travail, relations, santé, etc.)
3. **duration** : Durée des symptômes (jours, semaines, mois)
4. **symptomes** : Manifestations (insomnie, fatigue, perte appétit, etc.)
5. **intensite** : Échelle 1-10 ou qualificatif (léger, modéré, intense)

**Fonctionnalités :**

- Extraction automatique via Gemini (température 0.1)
- Génération questions dynamiques contextuelles (température 0.7)
- Validation complétude (5/5 paramètres requis)

**API :**

```python
collect_parameters(message, current_params) → {
    is_complete: bool,
    collected_params: dict,
    next_question: str,
    completion_rate: float
}
```

---

### **3. AnalysisAgent** (`agents/analysis_agent.py`)

**Responsabilité :** Analyse psychologique (après collecte complète)

**Calculs :**

- **severity_level** : Élevé / Modéré / Faible
- **urgency_score** : 0-10 (détermine besoin RDV)
- **taux_mal_etre** : 0-1 (basé sur sentiment + intensité + durée)

**Critères détection urgence :**

- Émotions critiques : suicide, dépression sévère, violence
- Intensité ≥ 8/10
- Durée longue (> 2 mois)

---

### **4. CalendarAgent** (`agents/calendar_agent.py`)

**Responsabilité :** Analyse charge agenda Google Calendar

**Fonctionnalités :**

- Consultation agenda via Google Apps Script
- Détection surcharge (> 8h/jour)
- Proposition suppressions événements (si mal-être > 50%)
- Ajout pauses bien-être (si charge faible + bien-être élevé)

**Workflow :**

```python
analyze_calendar_load(date, taux_mal_etre, severity) → {
    charge_totale_heures: float,
    charge_excessive: bool,
    proposed_changes: [DELETE events],
    calendar_message: str,
    awaiting_confirmation: bool
}
```

**API Google Calendar :**

- **Endpoint unique** : `AGENDA_ENDPOINT` (Google Apps Script)
- **Actions** : `CONSULT`, `ADD`, `DELETE`
- **Format requête** : GET avec params `action_type`, `date`, `event_id`

---

### **5. BookingAgent** (`agents/booking_agent.py`)

**Responsabilité :** Décision et génération créneaux consultation

**Critères proposition RDV :**

- Sévérité = Élevée OU Urgence ≥ 7/10
- Durée longue (> 2 semaines)
- Sévérité modérée
- Urgence détectée (booking IMMÉDIAT)

**Spécialités proposées :**

- **Psychologue** : Sévérité élevée, stress, anxiété
- **Psychiatre** : Dépression, troubles graves
- **Thérapeute** : Sévérité modérée

**Génération créneaux :**

- 3 créneaux fictifs via Gemini
- Données : date (J+2 à J+7), heure, praticien, mode (présentiel/téléconsultation)

---

### **6. RecommendationAgent** (`agents/recommendation_agent.py`)

**Responsabilité :** Génération recommandations personnalisées

**Types de recommandations :**

- **Respiration** : Exercices guidés avec sons (respiration carrée)
- **Méditation** : Vidéos YouTube pleine conscience
- **Yoga** : Séances douces embeddées
- **Journal gratitude** : Instructions étapes
- **Musique relaxante** : Playlists apaisantes
- **Agenda** : Propositions suppressions événements (intégré)

**Priorisation :**

1. Toujours inclure exercice respiration
2. Activité interactive (méditation/yoga/journal)
3. Recommandations spécifiques symptômes
4. Calendrier (si `proposed_changes` présent)

---

### **7. ConversationAgent** (`agents/conversation_agent.py`)

**Responsabilité :** Gestion fluidité conversationnelle

**Fonctionnalités :**

- Messages de transition contextuels
- Reformulation questions collecte avec empathie
- Génération réponses naturelles (pas de templates froids)

---

## 🔄 Machine à États

### **États du ConversationState**

```python
class ConversationState(Enum):
    ROUTING = auto()                    # État initial - Détection urgence
    HANDLING_EMERGENCY = auto()         # Protocole urgence + continue collecte
    COLLECTING_PARAMS = auto()          # Collecte 5 paramètres
    WAITING_USER_CONFIRMATION = auto()  # "Ajouter quelque chose ou solutions ?"
    ANALYZING_AND_RESPONDING = auto()   # Analyse + Booking + Agenda + Reco
    FINAL_RESPONSE_READY = auto()       # Réponse prête à envoyer
```

### **Flux Conversationnel**

#### **Cas Normal (sans urgence)**

```
User: "Je suis stressé"
  → ROUTING → COLLECTING_PARAMS

Bot: "Qu'est-ce qui cause ce stress ?"
User: "Mon travail"
  → COLLECTING_PARAMS (2/5 paramètres)

Bot: "Depuis combien de temps ?"
User: "2 mois"
  → COLLECTING_PARAMS (3/5 paramètres)

... (continue jusqu'à 5/5)

Bot: "Ajouter quelque chose ou solutions maintenant ?"
  → WAITING_USER_CONFIRMATION

User: "non"
  → ANALYZING_AND_RESPONDING

Bot: [Analyse] → [Créneaux] → [Recommandations] → [Agenda]
  → FINAL_RESPONSE_READY
```

#### **Cas Urgence (suicide)**

```
User: "Je veux me suicider"
  → ROUTING → HANDLING_EMERGENCY

Bot: [Bannière 3114 affichée en haut]
     "Je m'inquiète pour toi... Pourquoi vouloir en finir ?"
  → next_state = COLLECTING_PARAMS

User: "Parce que je suis stressé au travail"
  → COLLECTING_PARAMS (2/5 paramètres)
  [Bannière 3114 reste affichée]

... (flux identique au cas normal)

Bot: [Analyse] → [Créneaux URGENTS] → [Recommandations] → [Agenda]
  [Bannière 3114 toujours visible]
```

**Différences cas urgence :**

- ✅ Bannière 3114 affichée et reste visible toute la conversation
- ✅ Message empathique généré par Gemini (température 0.9)
- ✅ Flag `is_emergency: true` dans toutes les réponses
- ❌ **Pas de différence dans le workflow** (même collecte, analyse, créneaux)

---

## 🌐 API Endpoints

### **POST /api/v2/chat**

**Endpoint principal** - Traite tous les messages utilisateur

**Request :**

```json
{
  "text": "Je me sens stressé",
  "session_id": "uuid-v4-optionnel"
}
```

**Response (collecte en cours) :**

```json
{
  "success": true,
  "response": "Qu'est-ce qui cause ce stress ?",
  "session_id": "abc123",
  "is_emergency": false,
  "params_complete": false,
  "completion_rate": 0.4,
  "collected_params": {
    "emotion": "stress",
    "causes": "travail"
  }
}
```

**Response (analyse complète) :**

```json
{
  "success": true,
  "response": "Voici des solutions personnalisées...",
  "session_id": "abc123",
  "is_emergency": false,
  "needs_booking": true,
  "slots": [
    {
      "date": "2025-11-05",
      "time": "10:00",
      "provider_name": "Dr. Sophie Martin",
      "specialty": "Psychologue",
      "mode": "téléconsultation",
      "booking_link": "https://doctolib.fr/..."
    }
  ],
  "recommendations": [
    {
      "type": "respiration",
      "titre": "Exercice Respiration Carrée",
      "breathingSteps": [...]
    },
    {
      "type": "agenda",
      "titre": "Alléger votre agenda",
      "proposed_changes": [
        {
          "action": "DELETE",
          "event_id": "xxx",
          "event_title": "Réunion",
          "duration": 2,
          "reason": "Alléger la charge"
        }
      ],
      "awaiting_confirmation": true
    }
  ],
  "analysis": {
    "severity_level": "Modéré",
    "urgency_score": 6,
    "taux_mal_etre": 0.65
  }
}
```

**Response (urgence détectée) :**

```json
{
  "success": true,
  "response": "Je m'inquiète vraiment pour toi...",
  "session_id": "abc123",
  "is_emergency": true,
  "emergency_data": {
    "level": "CRITIQUE",
    "type": "self_harm",
    "keywords_found": ["suicide"]
  },
  "protocol": {
    "hotline": "3114",
    "hotline_name": "Prévention Suicide",
    "banner": {
      "visible": true,
      "title": "🆘 Numéro d'urgence : 3114",
      "subtitle": "Disponible 24h/24"
    }
  }
}
```

---

### **POST /api/orientation/feedback**

**Confirmation/refus réservation créneau**

**Request :**

```json
{
  "session_id": "abc123",
  "intent": "accepter_booking",
  "slot_index": 1,
  "slot_data": {
    "date": "2025-11-05",
    "time": "10:00",
    "doctor": "Dr. Martin",
    "specialty": "Psychologue"
  }
}
```

**Response :**

```json
{
  "success": true,
  "message": "✅ Créneau réservé et ajouté à votre agenda",
  "calendar_added": true
}
```

---

### **POST /api/agenda/confirm_changes**

**Confirmation suppressions événements agenda**

**Request :**

```json
{
  "session_id": "abc123",
  "event_ids": ["event-1", "event-2"],
  "action": "apply"
}
```

**Response :**

```json
{
  "success": true,
  "message": "✅ 2 suppression(s) effectuée(s) avec succès",
  "deleted_count": 2,
  "failed_count": 0
}
```

---

## 🖥️ Intégration Frontend

### **Fichiers Frontend Actuels**

Le dossier `/static` contient un frontend de démo complet :

```
static/
├── css/
│   ├── style.css         # Styles principaux chatbot
│   └── slots.css         # Styles créneaux booking
├── js/
│   ├── main.js          # Orchestrateur frontend principal
│   ├── api.js           # Client API (fetch wrapper)
│   ├── ui.js            # Gestion UI (messages, bannières)
│   ├── booking.js       # Gestion créneaux consultation
│   ├── recommendations.js # Affichage recommandations interactives
│   ├── session.js       # Gestion sessions utilisateur
│   ├── speech.js        # Reconnaissance vocale (optionnel)
│   └── config.js        # Configuration endpoints
templates/
└── index.html           # Page démo chatbot
```

### **Intégration avec Votre Frontend**

#### **Option 1 : Réutiliser les modules JS existants**

Les fichiers JS sont modulaires et peuvent être intégrés dans votre appli :

```javascript
// 1. Importez les modules
import { API } from "./static/js/api.js";
import { UI } from "./static/js/ui.js";
import { RecommendationsManager } from "./static/js/recommendations.js";

// 2. Configurez l'endpoint
API.baseURL = "https://votre-backend.com";

// 3. Envoyez un message
const response = await API.sendMessage("Je suis stressé", sessionId);

// 4. Affichez la réponse
UI.displayMessage("bot", response.response);

// 5. Gérez les urgences
if (response.is_emergency) {
  UI.displayEmergencyMessage("", response.emergency_data);
}

// 6. Affichez les recommandations
if (response.recommendations) {
  RecommendationsManager.renderRecommendations(
    response.recommendations,
    document.getElementById("recommendations-container")
  );
}
```

#### **Option 2 : Intégration API pure**

Si vous avez déjà votre propre frontend, utilisez directement l'API :

```javascript
// Envoyer un message
const response = await fetch("https://backend.com/api/v2/chat", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    text: userMessage,
    session_id: sessionId,
  }),
});

const data = await response.json();

// Gérer la réponse
if (data.is_emergency) {
  // Afficher bannière urgence (3114)
  showEmergencyBanner(data.protocol);
}

// Afficher message bot
displayBotMessage(data.response);

// Si créneaux disponibles
if (data.needs_booking && data.slots.length > 0) {
  displayBookingSlots(data.slots);
}

// Si recommandations
if (data.recommendations) {
  displayRecommendations(data.recommendations);
}
```

### **Composants Frontend Clés à Implémenter**

#### **1. Bannière Urgence (critique)**

```html
<div id="emergency-banner" style="display: none;">
  <div class="emergency-content">
    <strong>🚨 AIDE DISPONIBLE</strong>
    <div class="emergency-contacts">
      <strong>3114</strong> (24h/24) • <strong>SOS Amitié</strong> 09 72 39 40
      50
    </div>
    <button onclick="closeBanner()">×</button>
  </div>
</div>
```

**Important :**

- Doit rester visible pendant toute la conversation
- Position fixe en haut de la page
- Fond rouge/orange pour visibilité

#### **2. Créneaux Booking**

```javascript
// Affichage des créneaux
slots.forEach((slot, index) => {
  const slotHTML = `
    <div class="slot-card" data-index="${index}">
      <h4>${slot.provider_name}</h4>
      <p>${slot.specialty} - ${slot.mode}</p>
      <p>📅 ${slot.date} à ${slot.time}</p>
      <button onclick="bookSlot(${index}, slot)">Réserver</button>
    </div>
  `;
});

// Confirmation réservation
async function bookSlot(index, slotData) {
  const response = await fetch("/api/orientation/feedback", {
    method: "POST",
    body: JSON.stringify({
      session_id: sessionId,
      intent: "accepter_booking",
      slot_index: index,
      slot_data: slotData,
    }),
  });
}
```

#### **3. Recommandations Interactives**

**Respiration :**

```javascript
// Exercice respiration avec sons
const breathingSteps = recommendation.breathingSteps;
breathingSteps.forEach((step) => {
  // Afficher texte + jouer fréquence audio
  playTone(step.frequency, step.duration);
});
```

**Agenda (suppressions) :**

```javascript
// Afficher événements proposés à supprimer
proposed_changes.forEach((change) => {
  const eventHTML = `
    <div class="agenda-event">
      <input type="checkbox" 
             class="event-checkbox" 
             data-event-id="${change.event_id}">
      <label>
        ${change.event_title} 
        (${change.duration}h) - ${change.reason}
      </label>
    </div>
  `;
});

// Confirmation suppressions
async function confirmDeletions() {
  const selectedIds = getCheckedEventIds();
  const response = await fetch("/api/agenda/confirm_changes", {
    method: "POST",
    body: JSON.stringify({
      event_ids: selectedIds,
      action: "apply",
    }),
  });
}
```

---

## 🚀 Installation

### **Prérequis**

- Python 3.9+
- Clé API Google Gemini
- Google Apps Script déployé (pour Google Calendar)

### **Installation**

```bash
# 1. Cloner le repo
cd back

# 2. Créer environnement virtuel
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 3. Installer dépendances
pip install -r requirements.txt

# 4. Configurer .env
cp .env.example .env
# Éditer .env avec vos clés API
```

### **Configuration `.env`**

```env
# Gemini API
PROJECT_ID=your-project-id
GEMINI_API_KEY=your-gemini-api-key

# Google Calendar (Google Apps Script)
AGENDA_ENDPOINT=https://script.google.com/macros/s/YOUR_SCRIPT_ID/exec
```

### **Démarrage**

```bash
python main.py
```

Le serveur démarre sur `http://localhost:5000`

---

## ⚙️ Configuration

### **Variables d'environnement**

| Variable          | Description            | Exemple                         |
| ----------------- | ---------------------- | ------------------------------- |
| `PROJECT_ID`      | ID projet Google Cloud | `zenflow-project`               |
| `GEMINI_API_KEY`  | Clé API Gemini 2.0     | `AIzaSy...`                     |
| `AGENDA_ENDPOINT` | URL Google Apps Script | `https://script.google.com/...` |

### **Paramètres Agents (modifiables dans le code)**

**CollectionAgent :**

```python
# agents/collection_agent.py
REQUIRED_PARAMS = ['emotion', 'causes', 'duration', 'symptomes', 'intensite']
GEMINI_TEMPERATURE_EXTRACTION = 0.1  # Extraction précise
GEMINI_TEMPERATURE_QUESTIONS = 0.7   # Questions créatives
```

**AnalysisAgent :**

```python
# agents/analysis_agent.py
SEVERITY_THRESHOLDS = {
    'high': 70,    # Taux mal-être ≥ 70% → Élevé
    'moderate': 40 # 40-70% → Modéré, < 40% → Faible
}
```

**CalendarAgent :**

```python
# agents/calendar_agent.py
SEUIL_HEURES_JOURNALIER = 8  # Surcharge si > 8h/jour
TARGET_HOURS = 6.0           # Objectif après allègement
```

**BookingAgent :**

```python
# agents/booking_agent.py
URGENCY_THRESHOLD = 7        # Booking si urgence ≥ 7/10
DURATION_THRESHOLD_WEEKS = 2 # Booking si durée > 2 semaines
```

---

## 📊 Monitoring & Logs

### **Logs Console**

Le système utilise `logging` Python avec niveaux :

- **ERROR** : Urgences critiques, erreurs API
- **WARNING** : Surcharges agenda, échecs non-bloquants
- **INFO** : Flux normal, états machine, paramètres collectés

**Exemple logs :**

```
2025-10-31 10:15:50,989 - agents.emergency_agent - ERROR - 🚨 URGENCE CRITIQUE: 'suicide' détecté
2025-10-31 10:15:51,006 - agents.booking_agent - INFO - 🆘 Booking proposé: URGENCE DÉTECTÉE
2025-10-31 10:15:51,045 - adk_orchestrator - INFO - ✅ Orchestration ADK terminée
```

### **Métriques importantes à surveiller**

- **Taux détection urgence** : `emergency_agent.detect_emergency()`
- **Taux complétion paramètres** : `collection_agent.completion_rate`
- **Temps réponse Gemini** : Extraction + Questions (quota API)
- **Erreurs API Google Calendar** : Échecs `CONSULT`/`DELETE`

---

## 🔒 Sécurité & Confidentialité

### **Données utilisateur**

**Stockées en session (backend) :**

- Paramètres psychologiques (5 paramètres)
- État conversation (machine à états)
- Flag urgence

**NON stockées en base de données** (système stateless actuel)

### **Recommandations pour production**

1. **HTTPS obligatoire** pour toutes les communications
2. **Chiffrement sessions** (actuellement en mémoire serveur)
3. **Tokenisation** : Remplacer `session_id` simple par JWT
4. **Rate limiting** : Limiter requêtes par IP/utilisateur
5. **Logs anonymisés** : Pas de PII (infos perso) dans les logs
6. **Conformité RGPD** : Ajouter consentement + droit oubli

---

## 🧪 Tests

### **Tests Manuels (Frontend Démo)**

1. **Cas normal** : "Je suis stressé" → Collecte → Analyse → Créneaux
2. **Cas urgence** : "Je veux me suicider" → Bannière 3114 + Collecte continue
3. **Cas refus RDV** : Refuser créneau proposé
4. **Cas agenda surchargé** : Tester suppressions événements (date 2025-10-30)

### **Tests Automatisés (à implémenter)**

```python
# tests/test_emergency_agent.py
def test_detect_suicide_keyword():
    agent = EmergencyAgent()
    result = agent.detect_emergency("je veux me suicider")
    assert result['is_emergency'] == True
    assert result['level'] == 'CRITIQUE'

# tests/test_collection_agent.py
def test_completion_rate():
    agent = CollectionAgent(gemini_model)
    result = agent.collect_parameters("stress travail 2 mois", {})
    assert result['completion_rate'] > 0.4
```

---

## 📚 Ressources

### **Documentation externe**

- **Google Gemini API** : https://ai.google.dev/docs
- **Google Apps Script** : https://developers.google.com/apps-script
- **Flask CORS** : https://flask-cors.readthedocs.io/

### **Numéros d'urgence (France)**

- **3114** : Prévention suicide (24h/24)
- **SOS Amitié** : 09 72 39 40 50
- **SAMU** : 15
- **Urgences** : 112

---

## 🤝 Support & Contact

Pour toute question technique sur l'intégration :

- Consultez la section [Intégration Frontend](#intégration-frontend)
- Vérifiez les [API Endpoints](#api-endpoints)
- Testez avec le frontend démo (`/templates/index.html`)

---

## 📝 Changelog

### v2.0.0 - Architecture Multi-Agents (Novembre 2025)

- ✅ Refonte complète architecture agentique
- ✅ Machine à états 6 états
- ✅ Séparation responsabilités agents
- ✅ Questions dynamiques Gemini
- ✅ Gestion urgence avec conversation continue
- ✅ Intégration Google Calendar (suppressions événements)
- ✅ Recommandations interactives (respiration, méditation, agenda)

---

**🧘 Zenflow - Votre compagnon bien-être digital**
