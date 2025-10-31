import logging
import json
import re
from typing import Dict, Any, List
import google.generativeai as genai

logger = logging.getLogger(__name__)


class CollectionAgent:
    """
    Agent spécialisé dans la collecte progressive de paramètres psychologiques.
    
    Responsabilités:
    - Collecter paramètres (emotion, causes, duration, symptomes, intensite)
    - Extraction intelligente via Gemini
    - Génération de questions contextuelles
    - Suivi de progression (completion_rate)
    
    """
    
    REQUIRED_PARAMS = ['emotion', 'causes', 'duration', 'symptomes', 'intensite']
    
    def __init__(self, gemini_model=None):
        """
        Args:
            gemini_model: Modèle Gemini pour extraction intelligente
        """
        self.model = gemini_model
        logger.info("✅ CollectionAgent initialisé")
    
    def collect_parameters(self, user_text: str, current_params: Dict = None) -> Dict[str, Any]:
        """
        Collecte progressive des paramètres psychologiques.
        
        Args:
            user_text: Message utilisateur
            current_params: Paramètres déjà collectés
        
        Returns:
            Dict contenant:
                - is_complete: bool
                - collected_params: Dict
                - missing_params: List[str]
                - next_question: str
                - completion_rate: float
        """
        collected = current_params or {}
        
        # Extraire nouveaux paramètres (100% Gemini)
        new_params = self._extract_params_with_gemini(user_text)
        
        # Mettre à jour avec nouveaux paramètres
        for key, value in new_params.items():
            if value and not collected.get(key):
                collected[key] = value
                logger.info(f"✓ Paramètre collecté: {key} = {value}")
        
        # Vérifier paramètres manquants
        missing = [p for p in self.REQUIRED_PARAMS if not collected.get(p)]
        
        # Taux de complétion
        completion_rate = (len(self.REQUIRED_PARAMS) - len(missing)) / len(self.REQUIRED_PARAMS)
        
        # Si complet
        if not missing:
            logger.info(f"✅ Tous les paramètres collectés: {collected}")
            return {
                "is_complete": True,
                "collected_params": collected,
                "missing_params": [],
                "next_question": None,
                "completion_rate": 1.0
            }
        
        # Générer question pour prochain paramètre
        next_param = missing[0]
        next_question = self._generate_question_for_param(next_param, collected)
        
        logger.info(f"📝 Paramètre manquant: {next_param} ({completion_rate*100:.0f}% complété)")
        
        return {
            "is_complete": False,
            "collected_params": collected,
            "missing_params": missing,
            "next_question": next_question,
            "completion_rate": completion_rate
        }
    
    def _extract_params_with_gemini(self, text: str) -> Dict[str, Any]:
        """
        Extraction 100% Gemini pour intelligence maximale.
        Détecte émotions, causes, durée, symptômes, intensité.
        """
        if not self.model:
            logger.warning("❌ Modèle Gemini non disponible")
            return {}
        
        prompt = f"""Tu es un assistant d'extraction de paramètres psychologiques pour une conversation de soutien.

Analyse cette phrase et extrais UNIQUEMENT les informations pertinentes sur l'état psychologique :
"{text}"

Paramètres à extraire (si présents) :
- emotion : l'émotion principale ressentie (tristesse, anxiété, stress, colère, peur, solitude, dépression, suicide, etc.)
- causes : la cause du mal-être (travail, famille, relation, santé, financier, études, solitude, etc.)
- duration : depuis combien de temps (exemples: "1 mois", "2 semaines", "quelques jours", "longtemps", etc.)
- symptomes : symptômes physiques/mentaux (insomnie, fatigue, maux de tête, concentration, appétit, etc.)
- intensite : niveau d'intensité de 1 à 10 (si mentionné explicitement OU si le texte est UNIQUEMENT un chiffre entre 1 et 10)

RÈGLES CRITIQUES :
- N'extrais QUE les émotions/symptômes RÉELLEMENT ressentis par la personne
- IGNORE les expressions familières, blagues, ou langage figuré ("t'es fou", "c'est dingue", etc.)
- Si le texte est UNIQUEMENT un chiffre entre 1-10 (ex: "9"), extrais-le comme intensite
- Si la phrase est une question ou expression NON-INFORMATIVE, retourne {{}}
- Ne réponds QU'AVEC un objet JSON valide
- Si un paramètre n'est PAS clairement mentionné, mets null
- Utilise des termes simples et clairs

Exemples :
- "je me sens stressée" → {{"emotion": "stress"}}
- "c'est à cause de mon travail" → {{"causes": "travail"}}
- "je veux me suicider" → {{"emotion": "suicide"}}
- "9" → {{"intensite": "9"}}
- "8/10" → {{"intensite": "8"}}
- "t'es fou ou quoi?" → {{}}  (expression, pas une émotion réelle)
- "depuis 3 mois" → {{"duration": "3 mois"}}
- "je dors mal depuis une semaine" → {{"symptomes": "insomnie", "duration": "1 semaine"}}

Réponds UNIQUEMENT avec le JSON, sans texte avant ou après."""

        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,  # Précision maximale
                    max_output_tokens=200
                )
            )
            
            response_text = response.text.strip()
            response_text = re.sub(r'```json\s*|\s*```', '', response_text).strip()
            
            params = json.loads(response_text)
            filtered_params = {k: v for k, v in params.items() if v is not None}
            
            logger.info(f"🤖 Extraction Gemini: {filtered_params}")
            return filtered_params
            
        except Exception as e:
            logger.error(f"❌ Erreur extraction Gemini: {e}")
            return {}
    
    def _generate_question_for_param(self, param_name: str, collected: Dict) -> str:
        """
        Génère question contextuelle pour paramètre manquant.
        Utilise Gemini pour personnalisation dynamique et empathique.
        """
        # Questions par défaut (fallback si Gemini échoue)
        fallback_questions = {
            'emotion': "Comment vous sentez-vous en ce moment ?",
            'causes': "Selon vous, qu'est-ce qui pourrait expliquer cet état ?",
            'duration': "Depuis combien de temps ressentez-vous cela ?",
            'symptomes': "Avez-vous remarqué des symptômes particuliers (sommeil, appétit, concentration) ?",
            'intensite': "Sur une échelle de 1 à 10, à quel point ressentez-vous cet inconfort ?"
        }
        
        # Si Gemini non disponible, utiliser question par défaut
        if not self.model:
            return fallback_questions.get(param_name, "Pouvez-vous m'en dire plus ?")
        
        # Construire contexte pour Gemini
        context_parts = []
        if collected.get('emotion'):
            context_parts.append(f"l'utilisateur ressent {collected['emotion']}")
        if collected.get('causes'):
            context_parts.append(f"à cause de {collected['causes']}")
        if collected.get('duration'):
            context_parts.append(f"depuis {collected['duration']}")
        if collected.get('symptomes'):
            context_parts.append(f"avec symptômes: {collected['symptomes']}")
        if collected.get('intensite'):
            context_parts.append(f"intensité: {collected['intensite']}/10")
        
        context_str = ", ".join(context_parts) if context_parts else "début de conversation"
        
        # Descriptions des paramètres pour Gemini
        param_descriptions = {
            'emotion': "l'émotion principale ressentie (tristesse, stress, anxiété, etc.)",
            'causes': "la cause ou l'origine du mal-être (travail, famille, santé, etc.)",
            'duration': "depuis combien de temps cette situation dure",
            'symptomes': "les symptômes physiques ou mentaux observés (insomnie, fatigue, concentration, etc.)",
            'intensite': "le niveau d'intensité sur une échelle de 1 à 10"
        }
        
        prompt = f"""Tu es un psychologue empathique dans une conversation de soutien.

Contexte actuel: {context_str}

Tu dois poser UNE question pour collecter: {param_descriptions.get(param_name, param_name)}

RÈGLES CRITIQUES:
- Question courte (max 20 mots)
- Ton empathique et bienveillant
- Naturelle et conversationnelle (pas robotique)
- Adaptée au contexte déjà collecté
- Ne répète PAS les informations déjà données
- Utilise "vous" (vouvoiement)

EXEMPLES:
- Si contexte vide + cherche emotion → "Comment vous sentez-vous en ce moment ?"
- Si emotion=stress + cherche causes → "Qu'est-ce qui vous stresse particulièrement ?"
- Si emotion=tristesse, causes=travail + cherche duration → "Depuis quand cette situation au travail vous affecte-t-elle ?"
- Si plusieurs paramètres connus + cherche intensite → "Sur une échelle de 1 à 10, comment évalueriez-vous votre mal-être ?"

Réponds UNIQUEMENT avec la question, sans guillemets ni ponctuation supplémentaire."""

        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,  # Un peu de créativité pour variété
                    max_output_tokens=50
                )
            )
            
            question = response.text.strip().strip('"').strip("'")
            
            # Validation: la question doit se terminer par ?
            if not question.endswith('?'):
                question += ' ?'
            
            logger.info(f"🤖 Question Gemini générée: {question}")
            return question
            
        except Exception as e:
            logger.error(f"❌ Erreur génération question Gemini: {e}")
            # Fallback sur question par défaut
            base_question = fallback_questions.get(param_name, "Pouvez-vous m'en dire plus ?")
            
            # Personnalisation contextuelle simple en fallback
            if param_name == 'duration' and collected.get('emotion'):
                emotion = collected['emotion']
                return f"Depuis combien de temps ressentez-vous {emotion} ?"
            
            return base_question
    
    def get_collection_summary(self, collected_params: Dict) -> str:
        """
        Génère un résumé textuel des paramètres collectés.
        Utile pour afficher à l'utilisateur ce qui a été compris.
        """
        if not collected_params:
            return "Aucun paramètre collecté pour le moment."
        
        summary_parts = []
        
        if collected_params.get('emotion'):
            summary_parts.append(f"Émotion: {collected_params['emotion']}")
        if collected_params.get('causes'):
            summary_parts.append(f"Cause: {collected_params['causes']}")
        if collected_params.get('duration'):
            summary_parts.append(f"Durée: {collected_params['duration']}")
        if collected_params.get('symptomes'):
            summary_parts.append(f"Symptômes: {collected_params['symptomes']}")
        if collected_params.get('intensite'):
            summary_parts.append(f"Intensité: {collected_params['intensite']}/10")
        
        return " | ".join(summary_parts)
