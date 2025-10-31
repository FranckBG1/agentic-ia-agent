import logging
import re
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import google.generativeai as genai

logger = logging.getLogger(__name__)


class BookingAgent:
    """
    Agent spécialisé dans la décision et génération de créneaux de consultation.
    
    Responsabilités:
    - Décider si des créneaux doivent être proposés (5 critères + PRIORITÉ 0 urgence)
    - Générer les créneaux via Gemini
    - Gérer l'ajout au Google Calendar
    """
    
    def __init__(self, gemini_model=None):
        self.model = gemini_model
        logger.info("✅ BookingAgent initialisé")
    
    def should_propose_slots(self, context: Dict[str, Any]) -> bool:
        """
        Détermine si on doit proposer des créneaux
        
        Args:
            context: Contexte contenant:
                - severity_level: Niveau de sévérité (Élevé, Modéré, Faible)
                - urgency_score: Score d'urgence (0-10)
                - duration: Durée des symptômes
                - symptomes: Symptômes rapportés
                - is_emergency: Si True, cas d'urgence (suicide, violence)
        
        Returns:
            bool: True si on doit proposer des créneaux
        """
        severity_level = context.get('severity_level', 'Faible')
        urgency_score = context.get('urgency_score', 0)
        duration = context.get('duration', '')
        symptomes = context.get('symptomes', '')
        is_emergency = context.get('is_emergency', False)
        
        # ═════════════════════════════════════════════════════════
        # PRIORITÉ 0: URGENCE (suicide, violence) → TOUJOURS proposer
        # ═════════════════════════════════════════════════════════
        if is_emergency:
            logger.info(f"🚨 Booking proposé: URGENCE DÉTECTÉE")
            return True
        
        # ═════════════════════════════════════════════════════════
        # Cas 1: Sévérité élevée → TOUJOURS proposer
        # ═════════════════════════════════════════════════════════
        if severity_level in ['Élevé', 'Elevé']:
            logger.info(f"📅 Booking proposé: sévérité élevée")
            return True
        
        # ═════════════════════════════════════════════════════════
        # Cas 2: Score d'urgence élevé (≥ 7) → TOUJOURS proposer
        # ═════════════════════════════════════════════════════════
        if urgency_score >= 7:
            logger.info(f"📅 Booking proposé: urgence élevée ({urgency_score}/10)")
            return True
        
        # ═════════════════════════════════════════════════════════
        # Cas 3: Durée longue (mois/ans) → proposer
        # ═════════════════════════════════════════════════════════
        duration_lower = duration.lower() if duration else ""
        if any(word in duration_lower for word in ['mois', 'ans', 'années', 'année']):
            logger.info(f"📅 Booking proposé: durée longue ({duration})")
            return True
        
        # ═════════════════════════════════════════════════════════
        # Cas 4: Plus de 2 semaines → proposer
        # ═════════════════════════════════════════════════════════
        match = re.search(r'(\d+)\s*semaines?', duration_lower)
        if match and int(match.group(1)) > 2:
            logger.info(f"📅 Booking proposé: durée > 2 semaines")
            return True
        
        # ═════════════════════════════════════════════════════════
        # Cas 5: Sévérité modérée → proposer
        # ═════════════════════════════════════════════════════════
        if severity_level == 'Modéré':
            logger.info(f"📅 Booking proposé: sévérité modérée")
            return True
        
        # ═════════════════════════════════════════════════════════
        # Sinon, ne pas proposer
        # ═════════════════════════════════════════════════════════
        logger.info(f"📅 Booking NON proposé: sévérité faible et courte durée")
        return False
    
    def generate_slots(self, specialty: str = "psychologue", city: str = "Paris") -> List[Dict]:
        """
        Génère 3 créneaux de consultation via Gemini
        TA LOGIQUE EXACTE depuis app.py (generate_fake_slots_with_gemini)
        
        Args:
            specialty: Spécialité du praticien
            city: Ville de consultation
            
        Returns:
            Liste de 3 créneaux avec date, heure, praticien, lien, mode
        """
        if not self.model:
            logger.warning("❌ Modèle Gemini non disponible pour génération créneaux")
            return self._fallback_slots()
        
        try:
            prompt = f"""Tu es un assistant de prise de rendez-vous.
Génère 3 faux créneaux de rendez-vous pour un(e) {specialty} à {city}.
Les créneaux doivent être dans les 7 prochains jours à compter du 30 Octobre 2025.
Les noms des praticiens doivent être français et fictifs.

Format JSON à retourner (tableau de 3 objets) :
[
  {{
    "date": "YYYY-MM-DD",
    "time": "HH:MM",
    "provider_name": "Dr. Nom Prénom",
    "booking_link": "https://www.doctolib.fr/booking/fake-{specialty}-{city}",
    "mode": "présentiel" ou "téléconsultation"
  }}
]

Réponds UNIQUEMENT avec le tableau JSON, sans texte ni balises markdown."""

            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(temperature=0.8)
            )

            response_text = response.text.strip()

            # Parser JSON
            try:
                # Chercher pattern JSON
                import json
                json_match = re.search(r'\[\s*\{.*?\}\s*\]', response_text, re.DOTALL)
                if json_match:
                    json_text = json_match.group(0)
                else:
                    # Essayer de nettoyer les balises markdown
                    json_text = re.sub(r'```json\s*|\s*```', '', response_text).strip()

                slots = json.loads(json_text)

                if not isinstance(slots, list):
                    raise ValueError("La réponse n'est pas une liste")

                logger.info(f"✅ {len(slots)} créneaux générés par Gemini")
                return slots

            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"❌ Erreur parsing JSON: {e}")
                logger.error(f"Réponse brute: {response_text}")
                return self._fallback_slots()

        except Exception as e:
            logger.error(f"❌ Erreur génération créneaux: {e}", exc_info=True)
            return self._fallback_slots()
    
    def _fallback_slots(self) -> List[Dict]:
        """Créneaux par défaut en cas d'erreur Gemini"""
        return [
            {
                "date": (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d"),
                "time": "10:00",
                "provider_name": "Dr. Martin Dubois",
                "booking_link": "https://www.doctolib.fr/booking/demo",
                "mode": "présentiel"
            },
            {
                "date": (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d"),
                "time": "14:30",
                "provider_name": "Dr. Sophie Laurent",
                "booking_link": "https://www.doctolib.fr/booking/demo",
                "mode": "téléconsultation"
            },
            {
                "date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
                "time": "16:00",
                "provider_name": "Dr. Claire Bernard",
                "booking_link": "https://www.doctolib.fr/booking/demo",
                "mode": "présentiel"
            }
        ]
    
    def process_booking_decision(self, analysis_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Traite la décision complète de booking
        
        Args:
            analysis_context: Résultats de l'analyse (severity, urgency, duration, is_emergency)
        
        Returns:
            Dict contenant:
                - needs_booking: bool
                - slots: List[Dict] si needs_booking=True
                - reason: str (raison de la décision)
        """
        needs_booking = self.should_propose_slots(analysis_context)
        
        result = {
            "needs_booking": needs_booking,
            "slots": [],
            "reason": ""
        }
        
        if needs_booking:
            # Générer les créneaux
            result["slots"] = self.generate_slots()
            result["reason"] = self._get_booking_reason(analysis_context)
            logger.info(f"✅ BookingAgent: {len(result['slots'])} créneaux générés")
        else:
            result["reason"] = "Situation ne nécessite pas de consultation immédiate"
            logger.info(f"✅ BookingAgent: Pas de créneaux nécessaires")
        
        return result
    
    def _get_booking_reason(self, context: Dict) -> str:
        """Génère un message expliquant pourquoi on propose des créneaux"""
        if context.get('is_emergency'):
            return "En raison de l'urgence de votre situation, je vous propose des créneaux de consultation immédiate."
        
        severity = context.get('severity_level', '')
        urgency = context.get('urgency_score', 0)
        
        if severity in ['Élevé', 'Elevé']:
            return "Votre situation nécessite un accompagnement professionnel. Voici des créneaux disponibles."
        
        if urgency >= 7:
            return "Compte tenu du niveau d'urgence de votre situation, je vous recommande de consulter rapidement."
        
        return "Je vous propose des créneaux de consultation pour un suivi adapté à votre situation."
