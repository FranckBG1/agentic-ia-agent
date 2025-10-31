import logging
from typing import Dict, Any, List, Optional
import google.generativeai as genai

logger = logging.getLogger(__name__)


class ConversationAgent:
    """
    Agent spécialisé dans la génération de réponses empathiques et naturelles.
    
    Responsabilités:
    - Générer validations empathiques via Gemini
    - Maintenir contexte conversationnel
    - Ajouter questions de façon fluide
    - Fallback si erreur Gemini
    """
    
    def __init__(self, gemini_model=None):
        self.model = gemini_model
        self.fallback_responses = self._load_fallback_responses()
        logger.info("✅ ConversationAgent initialisé")
    
    def _load_fallback_responses(self) -> Dict[str, List[str]]:
        """
        TES RÉPONSES DE SECOURS EXACTES depuis adk_agent.py
        Utilisées si Gemini échoue
        """
        return {
            "tristesse": [
                "Je suis vraiment désolé que vous traversiez cela. Votre courage de parler est déjà une grande force.",
                "Je comprends que ces moments sont difficiles. Vous n'êtes pas seul(e) dans cette épreuve.",
                "Je vous entends. La tristesse peut être vraiment pesante, et il est important d'en parler."
            ],
            "anxiété": [
                "L'anxiété peut être vraiment épuisante. Merci de partager cela avec moi.",
                "Je comprends que vous vous sentiez anxieux(se). C'est courageux de votre part d'en parler.",
                "Je suis là pour vous écouter. L'anxiété est difficile à vivre au quotidien."
            ],
            "stress": [
                "Je comprends que le stress puisse être accablant. Vous faites de votre mieux.",
                "Le stress peut vraiment peser sur nous. Je suis là pour vous accompagner.",
                "Je vous entends. Il est normal de se sentir dépassé(e) parfois."
            ],
            "colère": [
                "La colère est une émotion légitime. Merci de la partager avec moi.",
                "Je comprends votre frustration. C'est important d'exprimer ce que vous ressentez.",
                "Je vous entends. La colère peut être un signal que quelque chose doit changer."
            ],
            "peur": [
                "La peur est une émotion naturelle. Je suis là pour vous soutenir.",
                "Je comprends que vous ayez peur. C'est courageux de le reconnaître.",
                "Je vous entends. La peur peut être paralysante, mais vous n'êtes pas seul(e)."
            ],
            "solitude": [
                "La solitude peut être vraiment difficile. Je suis là pour vous écouter.",
                "Je comprends que vous vous sentiez seul(e). Merci de me faire confiance.",
                "Je vous entends. La solitude est une épreuve, mais vous n'êtes pas seul(e) en ce moment."
            ],
            "dépression": [
                "Je suis vraiment touché(e) que vous partagiez cela avec moi. Votre courage est immense.",
                "La dépression est une maladie sérieuse. Je suis là pour vous accompagner.",
                "Je vous entends. Vous faites preuve d'une grande force en cherchant de l'aide."
            ],
            "fatigue": [
                "L'épuisement peut être vraiment difficile. Votre corps et votre esprit méritent du repos.",
                "Je comprends que vous soyez fatigué(e). C'est important d'écouter ces signaux.",
                "Je vous entends. La fatigue peut affecter tous les aspects de notre vie."
            ],
            "confusion": [
                "Je comprends que vous vous sentiez perdu(e). Je suis là pour vous aider à y voir plus clair.",
                "La confusion est normale quand on traverse des moments difficiles.",
                "Je vous entends. Prenons le temps ensemble de démêler tout cela."
            ],
            "default": [
                "Je suis là pour vous écouter. Merci de partager cela avec moi.",
                "Je vous entends. Vos émotions sont légitimes et importantes.",
                "Je comprends que ce soit difficile. Je suis là pour vous accompagner."
            ]
        }
    
    def generate_empathetic_response(
        self,
        user_message: str,
        collected_params: Dict[str, Any],
        next_question: str = None
    ) -> str:
        """
        Génère réponse empathique via Gemini
        
        Args:
            user_message: Message utilisateur
            collected_params: Paramètres déjà collectés
            next_question: Question à poser ensuite (optionnel)
        
        Returns:
            str: Réponse empathique + question
        """
        if not self.model:
            logger.warning("❌ Modèle Gemini non disponible, utilisation fallback")
            return self._generate_fallback_response(collected_params, next_question)
        
        # ═════════════════════════════════════════════════════════
        # Construire contexte des paramètres collectés
        # ═════════════════════════════════════════════════════════
        context_parts = []
        
        emotion = collected_params.get('emotion', '')
        causes = collected_params.get('causes', '')
        duration = collected_params.get('duration', '')
        symptomes = collected_params.get('symptomes', '')
        intensite = collected_params.get('intensite', '')
        
        if emotion:
            context_parts.append(f"- Émotion ressentie: {emotion}")
        if causes:
            context_parts.append(f"- Causes identifiées: {causes}")
        if duration:
            context_parts.append(f"- Durée: {duration}")
        if symptomes:
            context_parts.append(f"- Symptômes: {symptomes}")
        if intensite:
            context_parts.append(f"- Intensité: {intensite}")
        
        context_text = "\n".join(context_parts) if context_parts else "Aucun paramètre collecté pour le moment"
        
        # ═════════════════════════════════════════════════════════
        # Prompt Gemini - UNIQUEMENT validation (pas de question)
        # ═════════════════════════════════════════════════════════
        prompt = f"""Tu es Zenflow, un assistant psychologique bienveillant et empathique spécialisé en santé mentale.

**CONTEXTE DE LA CONVERSATION:**
L'utilisateur vient de dire : "{user_message}"

**INFORMATIONS DÉJÀ COLLECTÉES:**
{context_text}

**TA MISSION:**
Génère UNIQUEMENT une phrase de validation empathique (1-2 phrases maximum) qui :
1. **VALIDE** l'émotion/situation de l'utilisateur avec chaleur
2. **NE RÉPÈTE PAS** textuellement ce que l'utilisateur vient de dire
3. **NE POSE PAS DE QUESTION** - juste une validation

**RÈGLES IMPORTANTES:**
- Sois chaleureux(se) et authentique
- Utilise "Je comprends", "Je vous entends", "Je suis là pour vous"
- NE répète PAS mot pour mot ce que l'utilisateur dit
- Reste très concis : 1-2 phrases MAXIMUM
- NE termine PAS par une question

**EXEMPLES DE BONNES RÉPONSES (validation UNIQUEMENT):**
- "Je suis là pour vous écouter. Ces moments sont vraiment difficiles."
- "Je vous entends. Il est clair que vous traversez une période éprouvante."
- "Je comprends que ce n'est pas facile. Votre courage de parler est important."

**GÉNÈRE UNIQUEMENT LA VALIDATION (1-2 phrases, PAS de question):**"""

        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,  # Créativité modérée
                    max_output_tokens=150
                )
            )
            
            if response and response.text:
                generated_response = response.text.strip()
                
                # Sécurité : réponse trop courte
                if len(generated_response) < 20:
                    logger.warning("⚠️ Réponse Gemini trop courte, fallback")
                    return self._generate_fallback_response(collected_params, next_question)
                
                logger.info(f"✅ Réponse empathique Gemini ({len(generated_response)} chars)")
                
                # Gemini génère VALIDATION uniquement, code ajoute question
                if next_question:
                    return f"{generated_response} {next_question}"
                return generated_response
            else:
                logger.warning("⚠️ Pas de réponse Gemini, fallback")
                return self._generate_fallback_response(collected_params, next_question)
                
        except Exception as e:
            logger.error(f"❌ Erreur génération empathique: {e}")
            return self._generate_fallback_response(collected_params, next_question)
    
    def _generate_fallback_response(self, collected_params: Dict, next_question: str = None) -> str:
        """
        TA LOGIQUE EXACTE depuis adk_agent.py (_fallback_empathetic_response)
        Génère réponse de secours si Gemini échoue
        """
        emotion = collected_params.get('emotion', '').lower()
        
        # Sélectionner réponse appropriée selon émotion
        if 'triste' in emotion or 'tristesse' in emotion:
            responses = self.fallback_responses['tristesse']
        elif 'anxie' in emotion or 'angoisse' in emotion:
            responses = self.fallback_responses['anxiété']
        elif 'stress' in emotion:
            responses = self.fallback_responses['stress']
        elif 'colère' in emotion:
            responses = self.fallback_responses['colère']
        elif 'peur' in emotion:
            responses = self.fallback_responses['peur']
        elif 'seul' in emotion or 'solitude' in emotion:
            responses = self.fallback_responses['solitude']
        elif 'dépression' in emotion or 'déprimé' in emotion:
            responses = self.fallback_responses['dépression']
        elif 'fatigue' in emotion or 'épuisé' in emotion:
            responses = self.fallback_responses['fatigue']
        else:
            responses = self.fallback_responses['default']
        
        # Choisir une réponse (simple rotation)
        import random
        validation = random.choice(responses)
        
        # Ajouter question si fournie
        if next_question:
            return f"{validation} {next_question}"
        return validation
    
    def generate_transition_message(self, context: str = "analyse") -> str:
        """
        Génère message de transition naturel
        
        Args:
            context: Type de transition (analyse, recommendations, booking)
        """
        transitions = {
            "analyse": "Très bien, je prends un moment pour analyser votre situation...",
            "recommendations": "Voici des ressources qui pourraient vous aider...",
            "booking": "Je vous propose des créneaux de consultation disponibles...",
            "emergency": "Je comprends l'urgence de votre situation. Voici des contacts immédiats..."
        }
        return transitions.get(context, "Un instant...")
    
    def should_user_continue(self, user_message: str) -> bool:
        """
        Détermine si l'utilisateur veut ajouter quelque chose
        TA LOGIQUE depuis adk_agent.py (_user_wants_to_continue)
        """
        text_lower = user_message.lower().strip()
        
        # Indicateurs que l'utilisateur veut continuer
        continue_keywords = [
            'oui', 'oui,', 'oui.', 'ouais', 'ok', 'okay', 'd\'accord',
            'encore', 'ajouter', 'aussi', 'également', 'en plus',
            'je veux', 'j\'aimerais', 'je voudrais', 'attends'
        ]
        
        # Indicateurs que l'utilisateur est prêt pour l'analyse
        ready_keywords = [
            'non', 'non,', 'non.', 'ça va', 'c\'est bon', 'pas besoin',
            'prêt', 'prête', 'allons-y', 'allez', 'go', 'c\'est tout',
            'fini', 'termine', 'analyse'
        ]
        
        # Vérifier si message indique continuation
        for keyword in continue_keywords:
            if keyword in text_lower:
                return True
        
        # Vérifier si message indique qu'il est prêt
        for keyword in ready_keywords:
            if keyword in text_lower:
                return False
        
        # Par défaut : si le message est court (< 10 mots), considérer comme "non"
        # Si long, considérer comme continuation
        word_count = len(text_lower.split())
        return word_count > 10
    
    def process_conversation_turn(
        self,
        user_message: str,
        collected_params: Dict,
        next_question: str = None,
        context_type: str = "collection"
    ) -> Dict[str, Any]:
        """
        Pipeline complet pour un tour de conversation
        
        Returns:
            Dict avec:
                - response: str (réponse complète)
                - validation: str (partie validation seule)
                - question: str (partie question seule)
                - wants_to_continue: bool
        """
        # Générer réponse empathique
        full_response = self.generate_empathetic_response(
            user_message,
            collected_params,
            next_question
        )
        
        # Détecter si utilisateur veut continuer
        wants_to_continue = self.should_user_continue(user_message)
        
        # Séparer validation et question
        validation = full_response
        question = next_question or ""
        if next_question and next_question in full_response:
            parts = full_response.rsplit(next_question, 1)
            validation = parts[0].strip()
        
        return {
            "response": full_response,
            "validation": validation,
            "question": question,
            "wants_to_continue": wants_to_continue
        }
