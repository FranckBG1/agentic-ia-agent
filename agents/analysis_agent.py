import logging
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class AnalysisAgent:
    """
    Agent spécialisé dans l'ANALYSE psychologique.
    Travaille avec des paramètres DÉJÀ COLLECTÉS par le CollectionAgent.
    
    Responsabilités:
    - Analyser sentiment et état psychologique
    - Évaluer sévérité (Élevé, Modéré, Faible)
    - Calculer urgence (0-10)
    - Calculer taux de mal-être (0-1)
    """
    
    def __init__(self):
        logger.info("✅ AnalysisAgent initialisé")
    
    def analyze_psychological_state(self, collected_params: Dict, user_text: str = "") -> Dict[str, Any]:
        """
        Analyse psychologique complète
        
        Args:
            collected_params: Paramètres collectés
            user_text: Texte utilisateur optionnel
        
        Returns:
            Dict contenant:
                - severity_level: str (Élevé, Modéré, Faible)
                - urgency_score: int (0-10)
                - taux_mal_etre: float
                - sentiment_score: float
                - needs_orientation: bool
                - recommendations: List[str]
        """
        emotion = collected_params.get('emotion', '')
        causes = collected_params.get('causes', '')
        duration = collected_params.get('duration', '')
        symptomes = collected_params.get('symptomes', '')
        intensite = collected_params.get('intensite', '5')
        
        # Convertir intensité en nombre
        try:
            intensite_num = int(str(intensite).split('/')[0]) if intensite else 5
        except:
            intensite_num = 5
        
        # ═════════════════════════════════════════════════════════
        # Calcul sévérité (basé sur intensité et durée)
        # ═════════════════════════════════════════════════════════
        severity_level = "Faible"
        urgency_score = intensite_num  # Base: intensité
        
        # Émotions graves
        critical_emotions = ['suicide', 'suicidaire', 'dépression', 'désespoir', 'mort']
        if any(word in emotion.lower() for word in critical_emotions):
            severity_level = "Élevé"
            urgency_score = 10
        
        # Durée longue augmente sévérité
        duration_lower = duration.lower()
        if any(word in duration_lower for word in ['mois', 'ans', 'année', 'longtemps']):
            if severity_level != "Élevé":
                severity_level = "Modéré"
            urgency_score = min(10, urgency_score + 2)
        
        # Intensité élevée
        if intensite_num >= 8:
            severity_level = "Élevé"
            urgency_score = max(urgency_score, 9)
        elif intensite_num >= 6:
            if severity_level != "Élevé":
                severity_level = "Modéré"
            urgency_score = max(urgency_score, 7)
        
        # ═════════════════════════════════════════════════════════
        # Taux de mal-être (0-1)
        # ═════════════════════════════════════════════════════════
        taux_mal_etre = intensite_num / 10.0
        
        # ═════════════════════════════════════════════════════════
        # Analyse sentiment (si texte fourni)
        # ═════════════════════════════════════════════════════════
        sentiment_score = 0.0
        if user_text:
            sentiment_score = self._analyze_sentiment_simple(user_text)
        
        # ═════════════════════════════════════════════════════════
        # Orientation professionnelle nécessaire ?
        # ═════════════════════════════════════════════════════════
        needs_orientation = (
            severity_level in ["Élevé", "Modéré"] or
            urgency_score >= 7 or
            any(word in duration_lower for word in ['mois', 'ans'])
        )
        
        # ═════════════════════════════════════════════════════════
        # Recommandations de base
        # ═════════════════════════════════════════════════════════
        recommendations = []
        if severity_level == "Élevé":
            recommendations.append("Consultation psychologique recommandée")
        if 'insomnie' in symptomes.lower() or 'sommeil' in symptomes.lower():
            recommendations.append("Améliorer l'hygiène du sommeil")
        if urgency_score >= 7:
            recommendations.append("Suivi professionnel conseillé")
        
        logger.info(f"✅ Analyse: Sévérité={severity_level}, Urgence={urgency_score}/10")
        
        return {
            "severity_level": severity_level,
            "urgency_score": urgency_score,
            "taux_mal_etre": taux_mal_etre,
            "sentiment_score": sentiment_score,
            "needs_orientation": needs_orientation,
            "recommendations": recommendations,
            "analyzed_params": collected_params
        }
    
    def _analyze_sentiment_simple(self, text: str) -> float:
        """
        Analyse sentiment simple basée sur mots-clés
        Retourne score -1.0 (négatif) à 1.0 (positif)
        """
        text_lower = text.lower()
        
        negative_words = [
            'triste', 'mal', 'déprimé', 'anxieux', 'stressé', 
            'peur', 'colère', 'désespoir', 'seul', 'vide'
        ]
        positive_words = [
            'bien', 'heureux', 'content', 'motivé', 'calme', 
            'espoir', 'mieux', 'confiant'
        ]
        
        neg_count = sum(1 for word in negative_words if word in text_lower)
        pos_count = sum(1 for word in positive_words if word in text_lower)
        
        total = neg_count + pos_count
        if total == 0:
            return 0.0
        
        # Score normalisé
        score = (pos_count - neg_count) / total
        return max(-1.0, min(1.0, score))
