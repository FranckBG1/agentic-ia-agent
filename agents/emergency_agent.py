import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class EmergencyAgent:
    """
    Agent spécialisé dans la détection et gestion des situations d'urgence.
    
    Responsabilités:
    - Détecter urgences (suicide, violence, automutilation)
    - Activer protocole 3114
    - Coordonner avec BookingAgent pour créneaux IMMÉDIATS
    - Coordonner avec RecommendationAgent pour ressources d'urgence
    """
    
    def __init__(self, booking_agent=None, recommendation_agent=None):
        self.booking_agent = booking_agent
        self.recommendation_agent = recommendation_agent
        logger.info("✅ EmergencyAgent initialisé")
    
    def detect_emergency(self, text: str) -> Dict[str, Any]:
        """
        Détection rapide d'urgence basée sur mots-clés critiques
        
        Args:
            text: Message utilisateur
        
        Returns:
            Dict contenant:
                - is_emergency: bool
                - level: str (CRITIQUE, NORMAL)
                - keywords_found: List[str]
                - type: str (self_harm, violence, etc.)
                - urgency_score: int (0-10)
        """
        text_lower = text.lower()
        keywords_found = []

        # ═════════════════════════════════════════════════════════
        # Mots-clés CRITIQUES (suicide, automutilation)
        # ═════════════════════════════════════════════════════════
        critical_self_harm = [
            'suicide', 'suicidaire', 'me tuer', 'en finir',
            'je veux mourir', 'plus envie de vivre',
            'mettre fin à mes jours', 'me suicider',
            'overdose', 'surdose', 'avaler des pilules',
            'me jeter', 'sauter', 'pendaison', 'pendre'
        ]

        for keyword in critical_self_harm:
            if keyword in text_lower:
                keywords_found.append(keyword)
                logger.error(f"🚨 URGENCE CRITIQUE: '{keyword}' détecté")
        
        # Si mots-clés critiques détectés → URGENCE
        if keywords_found:
            return {
                'is_emergency': True,
                'level': 'CRITIQUE',
                'keywords_found': keywords_found,
                'type': 'self_harm',
                'urgency_score': 10
            }
        
        # Sinon situation normale
        return {
            'is_emergency': False,
            'level': 'NORMAL',
            'keywords_found': [],
            'type': None,
            'urgency_score': 0
        }
    
    def handle_crisis(self, user_message: str, analysis_context: Dict = None) -> Dict[str, Any]:
        """
        Gestion complète d'une situation de crise
        Coordonne avec les autres agents pour réponse complète
        
        Args:
            user_message: Message utilisateur
            analysis_context: Contexte d'analyse optionnel
        
        Returns:
            Dict contenant:
                - is_emergency: bool
                - emergency_data: Dict (détection)
                - booking: Dict (créneaux IMMÉDIATS)
                - recommendations: List (ressources urgence)
                - protocol: Dict (3114, etc.)
        """
        # 1. Détection urgence
        emergency_data = self.detect_emergency(user_message)
        
        if not emergency_data['is_emergency']:
            return {
                'is_emergency': False,
                'emergency_data': emergency_data
            }
        
        logger.error(f"🚨 EmergencyAgent: CRISE DÉTECTÉE - Type: {emergency_data['type']}")
        
        # 2. Préparer contexte pour autres agents
        crisis_context = {
            'is_emergency': True,
            'severity_level': 'Élevé',
            'urgency_score': 10,
            'duration': 'immédiat',
            'symptomes': emergency_data['keywords_found']
        }
        
        # Si contexte d'analyse fourni, fusionner
        if analysis_context:
            crisis_context.update(analysis_context)
        
        # 3. Coordonner avec BookingAgent → créneaux IMMÉDIATS
        booking_result = {}
        if self.booking_agent:
            booking_result = self.booking_agent.process_booking_decision(crisis_context)
            logger.info(f"✅ EmergencyAgent: Créneaux d'urgence générés")
        
        # 4. Coordonner avec RecommendationAgent → ressources urgence
        recommendations = []
        if self.recommendation_agent:
            recommendations = self.recommendation_agent.get_crisis_resources()
            logger.info(f"✅ EmergencyAgent: Ressources d'urgence ajoutées")
        
        # 5. Protocole 3114
        protocol = self._get_emergency_protocol(emergency_data['type'])
        
        return {
            'is_emergency': True,
            'emergency_data': emergency_data,
            'booking': booking_result,
            'recommendations': recommendations,
            'protocol': protocol,
            'context': crisis_context  # Pour autres agents
        }
    
    def _get_emergency_protocol(self, crisis_type: str) -> Dict[str, Any]:
        """
        Retourne le protocole d'urgence approprié
        
        Args:
            crisis_type: Type de crise (self_harm, violence, etc.)
        
        Returns:
            Dict avec numéros d'urgence, messages, actions
        """
        if crisis_type == 'self_harm':
            return {
                'hotline': '3114',
                'hotline_name': 'Numéro National de Prévention du Suicide',
                'message': "Votre sécurité est notre priorité. Le 3114 est disponible 24h/24 et 7j/7.",
                'actions': [
                    "Appeler le 3114 immédiatement",
                    "Contacter un proche de confiance",
                    "Se rendre aux urgences si danger imminent"
                ],
                'banner': {
                    'visible': True,
                    'title': '🆘 Numéro d\'urgence : 3114',
                    'subtitle': 'Disponible 24h/24 - Appel gratuit et confidentiel'
                }
            }
        
        # Protocole par défaut
        return {
            'hotline': '15',
            'hotline_name': 'SAMU',
            'message': "En cas d'urgence médicale, contactez le 15.",
            'actions': ["Appeler le 15 si danger imminent"],
            'banner': {
                'visible': True,
                'title': '🆘 Urgence : 15',
                'subtitle': 'SAMU - Disponible 24h/24'
            }
        }
    
    def should_trigger_emergency_booking(self, emergency_data: Dict) -> bool:
        """
        Détermine si l'urgence nécessite booking immédiat
        
        Args:
            emergency_data: Données de détection urgence
        
        Returns:
            bool: True si booking immédiat requis
        """
        # Pour toute urgence critique → booking IMMÉDIAT
        if emergency_data.get('is_emergency') and emergency_data.get('level') == 'CRITIQUE':
            return True
        
        return False
