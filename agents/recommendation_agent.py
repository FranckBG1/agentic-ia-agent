import logging
import json
from typing import Dict, Any, List, Optional
import google.generativeai as genai

logger = logging.getLogger(__name__)


class RecommendationAgent:
    """
    Agent spécialisé dans la génération de recommandations personnalisées.
    
    Responsabilités:
    - Générer recommandations basées sur analyse
    - Sélectionner ressources pertinentes (vidéos, exercices)
    - Proposer modifications agenda Google Calendar
    - Personnaliser selon profil utilisateur
    """
    
    def __init__(self, gemini_model=None):
        self.model = gemini_model
        # Charger TES ressources existantes (préservées)
        self.resource_database = self._load_resource_database()
        logger.info("✅ RecommendationAgent initialisé")
    
    def _load_resource_database(self) -> Dict:
        """
        Base de données des contenus (vidéos, exercices, etc.)
        """
        return {
            "anxiety_stress": [
                {
                    "type": "respiration",
                    "titre": "Exercice de Respiration Carrée",
                    "message": "Un exercice de respiration guidé par le son pour vous aider à retrouver le calme.",
                    "breathingSteps": [
                        {"text": "Inspirez lentement", "scale": 1.3, "frequency": 196.00, "gainStart": 0.2, "gainEnd": 0.05},
                        {"text": "Retenez l'air", "scale": 1.3, "frequency": 246.94, "gainStart": 0.15, "gainEnd": 0.05},
                        {"text": "Expirez doucement", "scale": 1, "frequency": 164.81, "gainStart": 0.2, "gainEnd": 0.05},
                        {"text": "Gardez les poumons vides", "scale": 1, "frequency": 130.81, "gainStart": 0.15, "gainEnd": 0.05}
                    ]
                },
                {
                    "type": "meditation",
                    "titre": "Méditation de pleine conscience",
                    "message": "Une séance guidée de mindfulness pour apaiser l'esprit",
                    "lien": "https://www.youtube.com/embed/xZeFiXMuYM0"
                },
                {
                    "type": "relaxation",
                    "titre": "Musique relaxante anti-stress",
                    "message": "Une playlist apaisante pour vous aider à gérer le stress",
                    "lien": "https://www.youtube.com/embed/lFcSrYw-ARY"
                }
            ],
            "insomnia": [
                {
                    "type": "productivite",
                    "titre": "Routine du sommeil",
                    "message": "Établissez une routine relaxante avant le coucher",
                    "instructions": [
                        "Couchez-vous et levez-vous à heures fixes",
                        "Évitez les écrans 1h avant le coucher",
                        "Créez une atmosphère calme et sombre",
                        "Faites des exercices de relaxation"
                    ]
                },
                {
                    "type": "meditation",
                    "titre": "Méditation pour le sommeil",
                    "message": "Une séance de relaxation pour faciliter l'endormissement",
                    "lien": "https://www.youtube.com/watch?v=aEqlQvczMJQ"
                },
                {
                    "type": "respiration",
                    "titre": "Respiration pour dormir",
                    "message": "Une technique de respiration apaisante pour favoriser l'endormissement",
                    "breathingSteps": [
                        {"text": "Inspirez doucement", "scale": 1.2, "frequency": 174.61, "gainStart": 0.15, "gainEnd": 0},
                        {"text": "Retenez brièvement", "scale": 1.2, "frequency": 164.81, "gainStart": 0.08, "gainEnd": 0},
                        {"text": "Longue expiration", "scale": 1, "frequency": 146.83, "gainStart": 0.15, "gainEnd": 0},
                        {"text": "Pause relaxante", "scale": 1, "frequency": 130.81, "gainStart": 0.05, "gainEnd": 0}
                    ]
                },
                {
                    "type": "audio",
                    "titre": "Sons pour dormir (Pluie & Nature)",
                    "lien": "https://www.youtube.com/watch?v=q76bMs-NwRk",
                    "message": "Des bruits blancs apaisants pour favoriser l'endormissement."
                }
            ],
            "fatigue": [
                {
                    "type": "motivation",
                    "titre": "3 petites actions pour recharger son énergie",
                    "message": "Relancez votre énergie avec des gestes simples et efficaces.",
                    "conseils": [
                        "Faites une courte marche de 5 à 10 minutes à l'extérieur.",
                        "Étirez-vous pendant 2 minutes pour réveiller votre corps.",
                        "Écoutez une chanson qui vous donne de l'énergie."
                    ]
                },
                {
                    "type": "energie",
                    "titre": "Musique énergisante (Workout Motivation)",
                    "lien": "https://www.youtube.com/watch?v=2RHTiXvELNg",
                    "message": "Une playlist dynamique pour booster votre motivation."
                }
            ],
            "concentration": [
                {
                    "type": "focus",
                    "titre": "Musique pour la concentration (Lofi Beats)",
                    "lien": "https://www.youtube.com/watch?v=jfKfPfyJRdk",
                    "message": "Une ambiance sonore calme pour vous aider à retrouver votre concentration."
                },
                {
                    "type": "productivite",
                    "titre": "Sons binauraux pour concentration profonde",
                    "lien": "https://www.youtube.com/watch?v=WPni755-Krg",
                    "message": "Des fréquences audio scientifiquement conçues pour améliorer la concentration."
                }
            ],
            "tristesse": [
                {
                    "type": "gratitude",
                    "titre": "Journal de gratitude",
                    "message": "Notez 3 choses positives de votre journée",
                    "instructions": [
                        "Prenez un moment calme pour réfléchir",
                        "Identifiez 3 petites victoires ou moments agréables",
                        "Écrivez-les dans un carnet dédié",
                        "Relisez vos notes régulièrement"
                    ]
                },
                {
                    "type": "meditation",
                    "titre": "Méditation de compassion",
                    "message": "Une séance pour cultiver la bienveillance envers soi-même",
                    "lien": "https://www.youtube.com/watch?v=sz7cpV7ERsM"
                },
                {
                    "type": "yoga",
                    "titre": "Yoga doux pour l'humeur",
                    "message": "Des postures douces pour libérer les tensions émotionnelles",
                    "video_url": "https://www.youtube.com/embed/v7AYKMP6rOE",
                    "duration": "15:00"
                }
            ],
            "depression": [
                {
                    "type": "productivite",
                    "titre": "Micro-actions quotidiennes",
                    "message": "Commencez par de toutes petites victoires",
                    "instructions": [
                        "Fixez-vous UN seul petit objectif par jour",
                        "Célébrez chaque petite réussite",
                        "Soyez patient et bienveillant avec vous-même",
                        "Notez vos progrès même minimes"
                    ]
                },
                {
                    "type": "gratitude",
                    "titre": "Auto-compassion",
                    "message": "Pratiquez la bienveillance envers vous-même",
                    "instructions": [
                        "Parlez-vous comme à un ami cher",
                        "Acceptez vos émotions sans jugement",
                        "Reconnaissez votre courage dans cette épreuve"
                    ]
                }
            ]
        }
    
    def generate_recommendations(self, analysis_context: Dict, proposed_agenda_changes: List = None) -> List[Dict]:
        """
        Génère recommandations personnalisées basées sur l'analyse
        
        Args:
            analysis_context: Résultats analyse (severity, symptomes, duration, etc.)
            proposed_agenda_changes: Modifications agenda proposées
        
        Returns:
            List[Dict] de recommandations enrichies
        """
        recommendations = []
        
        severity = analysis_context.get('severity_level', 'Modéré')
        symptomes = analysis_context.get('symptomes', '')
        emotion = analysis_context.get('emotion', '')
        
        # ═════════════════════════════════════════════════════════
        # 1. Sélectionner ressources pertinentes depuis BASE
        # ═════════════════════════════════════════════════════════
        recommendations.extend(self._select_from_database(symptomes, emotion, severity))
        
        # ═════════════════════════════════════════════════════════
        # 2. Ajouter recommandations agenda si proposées
        # ═════════════════════════════════════════════════════════
        if proposed_agenda_changes and len(proposed_agenda_changes) > 0:
            recommendations.append({
                "type": "agenda",
                "titre": "Optimisation de votre planning",
                "message": f"J'ai analysé votre agenda et identifié {len(proposed_agenda_changes)} opportunités pour libérer du temps et réduire votre charge.",
                "proposed_changes": proposed_agenda_changes,
                "instructions": [
                    "Consultez les propositions ci-dessous",
                    "Sélectionnez celles qui vous conviennent",
                    "Validez pour libérer du temps et réduire votre charge"
                ]
            })
            logger.info(f"✅ Recommandation agenda ajoutée avec {len(proposed_agenda_changes)} propositions")
        
        # ═════════════════════════════════════════════════════════
        # 3. Enrichir avec Gemini (personnalisation contextuelle)
        # ═════════════════════════════════════════════════════════
        if self.model and len(recommendations) > 0:
            recommendations = self._enrich_with_gemini(recommendations, analysis_context)
        
        logger.info(f"✅ {len(recommendations)} recommandations générées")
        return recommendations
    
    def _select_from_database(self, symptomes: str, emotion: str, severity: str) -> List[Dict]:
        """Sélectionne ressources pertinentes depuis la base"""
        selected = []
        symptomes_lower = symptomes.lower()
        emotion_lower = emotion.lower()
        
        # Mapping symptômes → catégories
        if any(word in symptomes_lower for word in ['anxiété', 'anxieux', 'stress', 'angoisse']):
            selected.extend(self.resource_database.get('anxiety_stress', []))
        
        if any(word in symptomes_lower for word in ['insomnie', 'sommeil', 'dors']):
            selected.extend(self.resource_database.get('insomnia', []))
        
        if any(word in symptomes_lower for word in ['fatigue', 'épuisé', 'énergie']):
            selected.extend(self.resource_database.get('fatigue', []))
        
        if any(word in symptomes_lower for word in ['concentration', 'focus', 'distrait']):
            selected.extend(self.resource_database.get('concentration', []))
        
        # Mapping émotions → catégories
        if any(word in emotion_lower for word in ['triste', 'tristesse', 'mélancolie']):
            selected.extend(self.resource_database.get('tristesse', []))
        
        if any(word in emotion_lower for word in ['dépression', 'déprimé', 'désespoir']):
            selected.extend(self.resource_database.get('depression', []))
        
        # Si rien trouvé, ajouter ressources génériques
        if not selected:
            selected.append({
                "type": "gratitude",
                "titre": "Journal de gratitude",
                "message": "Prenez un moment pour identifier les petits bonheurs du quotidien",
                "instructions": [
                    "Notez 3 choses positives de votre journée",
                    "Décrivez vos émotions",
                    "Célébrez vos petites victoires"
                ]
            })
        
        return selected[:5]  # Limiter à 5 max
    
    def _enrich_with_gemini(self, recommendations: List[Dict], context: Dict) -> List[Dict]:
        """Enrichit recommandations avec contexte personnalisé Gemini"""
        # Pour l'instant retourner tel quel
        # Tu peux ajouter personnalisation Gemini ici plus tard
        return recommendations
    
    def get_crisis_resources(self) -> List[Dict]:
        """
        Ressources spécifiques pour situations d'urgence
        Appelé par EmergencyAgent en cas de crise
        """
        return [
            {
                "type": "urgence",
                "titre": "🆘 Numéro d'urgence : 3114",
                "message": "Le 3114 est le numéro national de prévention du suicide, disponible 24h/24 et 7j/7. Gratuit et confidentiel.",
                "hotline": "3114",
                "instructions": [
                    "Appelez immédiatement le 3114",
                    "Parlez à un professionnel formé",
                    "Vous n'êtes pas seul(e)"
                ]
            },
            {
                "type": "respiration",
                "titre": "Respiration d'urgence",
                "message": "Un exercice rapide pour retrouver le calme",
                "breathingSteps": [
                    {"text": "Inspirez 4 secondes", "scale": 1.3, "frequency": 196.00, "gainStart": 0.2, "gainEnd": 0.05},
                    {"text": "Retenez 4 secondes", "scale": 1.3, "frequency": 246.94, "gainStart": 0.15, "gainEnd": 0.05},
                    {"text": "Expirez 4 secondes", "scale": 1, "frequency": 164.81, "gainStart": 0.2, "gainEnd": 0.05},
                    {"text": "Pause 4 secondes", "scale": 1, "frequency": 130.81, "gainStart": 0.15, "gainEnd": 0.05}
                ]
            },
            {
                "type": "contact",
                "titre": "Contacter un proche",
                "message": "Identifiez immédiatement une personne de confiance à qui parler",
                "instructions": [
                    "Appelez ou envoyez un message à un proche",
                    "Exprimez que vous avez besoin d'aide",
                    "Ne restez pas seul(e) en ce moment"
                ]
            }
        ]
    
    def process_recommendation_request(self, context: Dict) -> Dict[str, Any]:
        """
        Pipeline complet de génération recommandations
        
        Args:
            context: Peut être soit:
                - {'analysis': Dict, 'collected_params': Dict} (depuis orchestrateur)
                - analysis_result direct
        
        Returns:
            Dict avec:
                - recommendations: List[Dict]
                - count: int
                - categories: List[str]
        """
        # Support des deux formats pour compatibilité
        if 'analysis' in context:
            # Format orchestrateur: {'analysis': {...}, 'collected_params': {...}}
            analysis_context = context['analysis']
            collected_params = context.get('collected_params', {})
        else:
            # Format direct: analysis_result
            analysis_context = context
            collected_params = context.get('analyzed_params', {})
        
        # Fusionner contextes
        full_context = {**analysis_context, **collected_params}
        
        # Générer recommandations
        recommendations = self.generate_recommendations(full_context)
        
        # Extraire catégories
        categories = list(set(r.get('type', 'autre') for r in recommendations))
        
        logger.info(f"✅ {len(recommendations)} recommandations générées (catégories: {categories})")
        
        return {
            "recommendations": recommendations,
            "count": len(recommendations),
            "categories": categories
        }
