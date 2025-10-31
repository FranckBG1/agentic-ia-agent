"""
Orchestrateur ADK - Coordination intelligente des agents spécialisés
Architecture agentique pour projet Zenflow

L'orchestrateur reçoit les messages utilisateur et coordonne les agents :
- EmergencyAgent : Détection urgence (priorité absolue)
- CollectionAgent : Collecte progressive des paramètres psychologiques
- AnalysisAgent : Analyse psychologique (sévérité, urgence, mal-être)
- ConversationAgent : Réponses empathiques
- BookingAgent : Décision et génération créneaux
- RecommendationAgent : Recommandations personnalisées
- CalendarAgent : Analyse et optimisation agenda Google Calendar
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import google.generativeai as genai
import os
from enum import Enum, auto

from agents.collection_agent import CollectionAgent
from agents.analysis_agent import AnalysisAgent
from agents.booking_agent import BookingAgent
from agents.recommendation_agent import RecommendationAgent
from agents.emergency_agent import EmergencyAgent
from agents.conversation_agent import ConversationAgent
from agents.calendar_agent import CalendarAgent

logger = logging.getLogger(__name__)


class ConversationState(Enum):
    """États possibles de la conversation pour la machine à états de l'orchestrateur."""
    ROUTING = auto()
    HANDLING_EMERGENCY = auto()
    COLLECTING_PARAMS = auto()
    WAITING_USER_CONFIRMATION = auto()  # NOUVEAU: Attendre confirmation utilisateur
    ANALYZING_AND_RESPONDING = auto()
    FINAL_RESPONSE_READY = auto()


class ZenflowOrchestrator:
    """
    Orchestrateur principal - Coordonne tous les agents spécialisés via une machine à états.
    
    Implémente les principes de l'ADK (Agent Development Kit) pour une architecture robuste.
    """
    
    def __init__(self, gemini_model=None, agenda_endpoint=None):
        """
        Initialise l'orchestrateur et tous les agents.
        
        Args:
            gemini_model: Modèle Gemini pour extraction et génération
            agenda_endpoint: URL unique de l'API Google Calendar (GET/POST avec params)
        """
        self.model = gemini_model
        
        logger.info("🚀 Initialisation des agents spécialisés pour l'architecture ADK...")
        
        self.collection_agent = CollectionAgent(gemini_model)
        self.analysis_agent = AnalysisAgent()
        self.booking_agent = BookingAgent(gemini_model)
        self.recommendation_agent = RecommendationAgent(gemini_model)
        self.conversation_agent = ConversationAgent(gemini_model)
        self.calendar_agent = CalendarAgent(agenda_endpoint)  # Un seul endpoint
        
        self.emergency_agent = EmergencyAgent(
            booking_agent=self.booking_agent,
            recommendation_agent=self.recommendation_agent
        )
        
        self.sessions: Dict[str, Dict] = {}
        
        logger.info("✅ ZenflowOrchestrator initialisé avec 7 agents et une machine à états ADK.")
    
    def process_message(self, session_id: str, user_message: str) -> Dict[str, Any]:
        """
        Point d'entrée principal - Traite un message utilisateur via la machine à états ADK.
        
        Le workflow est une boucle qui transitionne entre les états jusqu'à ce qu'une
        réponse finale soit prête (état FINAL_RESPONSE_READY).
        """
        logger.info(f"📨 Orchestrateur ADK: Message reçu (session={session_id})")
        
        session_data = self._get_or_create_session(session_id, user_message)
        
        # ✅ Appliquer next_state si défini (pour continuer après urgence)
        if 'next_state' in session_data:
            session_data['state'] = session_data.pop('next_state')
            logger.info(f"🔄 Restauration état: {session_data['state'].name}")
        
        # Boucle de la machine à états ADK
        while session_data['state'] != ConversationState.FINAL_RESPONSE_READY:
            current_state = session_data['state']
            logger.info(f"🔄 État actuel: {current_state.name}")
            
            if current_state == ConversationState.ROUTING:
                self._handle_routing(session_data, user_message)
            
            elif current_state == ConversationState.HANDLING_EMERGENCY:
                self._handle_emergency(session_data, user_message)
            
            elif current_state == ConversationState.COLLECTING_PARAMS:
                self._handle_collecting_params(session_data, user_message)
            
            elif current_state == ConversationState.WAITING_USER_CONFIRMATION:
                self._handle_waiting_confirmation(session_data, user_message)
                
            elif current_state == ConversationState.ANALYZING_AND_RESPONDING:
                self._handle_analysis_and_response(session_data, user_message)

        logger.info("✅ Orchestration ADK terminée. Réponse finale prête.")
        return session_data.get('final_response', {
            "success": False, "response": "Une erreur est survenue."
        })

    # ═════════════════════════════════════════════════════════
    # GESTIONNAIRES D'ÉTATS (STATE HANDLERS)
    # ═════════════════════════════════════════════════════════

    def _handle_routing(self, session_data: Dict, user_message: str):
        """État ROUTING: Décide du prochain état en fonction du message."""
        # Agent d'urgence a la priorité absolue
        emergency_data = self.emergency_agent.detect_emergency(user_message)
        if emergency_data['is_emergency']:
            session_data['emergency_data'] = emergency_data
            session_data['state'] = ConversationState.HANDLING_EMERGENCY
            return

        # Si paramètres complets ET confirmation reçue → analyse
        if session_data.get('params_complete', False) and session_data.get('user_confirmed', False):
            session_data['state'] = ConversationState.ANALYZING_AND_RESPONDING
        # Si paramètres complets MAIS pas de confirmation → attendre
        elif session_data.get('params_complete', False) and not session_data.get('user_confirmed', False):
            session_data['state'] = ConversationState.WAITING_USER_CONFIRMATION
        # Sinon, continuer la collecte
        else:
            session_data['state'] = ConversationState.COLLECTING_PARAMS

    def _handle_emergency(self, session_data: Dict, user_message: str):
        """État HANDLING_EMERGENCY: Gère le protocole d'urgence PUIS continue la collecte."""
        logger.error(f"🚨 URGENCE DÉTECTÉE - Activation du protocole puis collecte des paramètres")
        
        crisis_result = self.emergency_agent.handle_crisis(user_message)
        
        # Réponse empathique générée par Gemini au lieu d'un template froid
        empathetic_prompt = f"""Tu es un conseiller en santé mentale bienveillant et empathique. 
L'utilisateur vient d'exprimer des pensées suicidaires : "{user_message}"

Réponds de manière CHALEUREUSE et HUMAINE :
1. Exprime ta profonde inquiétude pour lui/elle
2. Demande "Pourquoi vouloir en finir ? Qu'est-ce qui te fait tant souffrir ?"
3. Rappelle le 3114 disponible 24h/24 MAIS sans être froid ou robotique
4. Montre que tu veux VRAIMENT comprendre sa souffrance

Ton message doit être court (3-4 phrases), sincère, et donner envie de continuer à parler.
NE METS PAS de formatage markdown ou de liste à puces. Parle naturellement comme un ami inquiet."""

        try:
            gemini_response = self.gemini_model.generate_content(
                empathetic_prompt,
                generation_config={'temperature': 0.9}  # Plus créatif et humain
            )
            emergency_message = gemini_response.text.strip()
        except Exception as e:
            logger.error(f"❌ Erreur génération message empathique: {e}")
            # Fallback empathique
            emergency_message = "Je m'inquiète vraiment pour toi... Pourquoi vouloir en finir ? Qu'est-ce qui te fait tant souffrir ? Le 3114 est là pour t'écouter 24h/24, mais moi aussi je suis là. Raconte-moi ce qui se passe."
        
        final_response_text = emergency_message
        
        # Marquer comme urgence
        session_data['is_emergency'] = True
        session_data['emergency_data'] = crisis_result['emergency_data']
        session_data['protocol'] = crisis_result['protocol']
        
        #  Extraire les paramètres du message d'urgence ET générer la question suivante
        collection_result = self.collection_agent.collect_parameters(user_message, session_data.get('collected_params', {}))
        session_data['collected_params'] = collection_result['collected_params']
        
        #  Réponse immédiate = Message empathique + première question de collecte
        if not collection_result['is_complete']:
            final_response_text += f"\n\n{collection_result['next_question']}"
            
            #  Prochaine requête doit continuer la collecte
            session_data['next_state'] = ConversationState.COLLECTING_PARAMS
        else:
            # Paramètres déjà complets (rare) → passer à la confirmation
            session_data['next_state'] = ConversationState.WAITING_USER_CONFIRMATION
        
        session_data['final_response'] = {
            "success": True,
            "response": final_response_text,
            "is_emergency": True,
            "emergency_data": crisis_result['emergency_data'],
            "protocol": crisis_result['protocol'],
            "session_id": session_data['session_id'],
            "params_complete": collection_result['is_complete'],
            "collected_params": collection_result['collected_params'],
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "agents_used": ["EmergencyAgent", "CollectionAgent"],
                "emergency_level": crisis_result['emergency_data']['level']
            }
        }
        
        #  Sortir de la boucle pour envoyer la réponse
        session_data['state'] = ConversationState.FINAL_RESPONSE_READY

    def _handle_collecting_params(self, session_data: Dict, user_message: str):
        """État COLLECTING_PARAMS: L'AnalysisAgent collecte les informations."""
        current_params = session_data.get('collected_params', {})
        
        collection_result = self.collection_agent.collect_parameters(user_message, current_params)
        
        session_data['collected_params'] = collection_result['collected_params']
        session_data['params_complete'] = collection_result['is_complete']
        
        if collection_result['is_complete']:
            #  Paramètres complets → Demander confirmation utilisateur
            logger.info("✅ Tous les paramètres collectés. Demande de confirmation utilisateur.")
            
            confirmation_message = "Je vous ai bien écouté. Souhaitez-vous ajouter quelque chose d'autre ou préférez-vous que je vous propose des solutions maintenant ?"
            
            session_data['final_response'] = {
                "success": True,
                "response": confirmation_message,
                "is_emergency": session_data.get('is_emergency', False),
                "needs_booking": False,
                "slots": [],
                "recommendations": [],
                "session_id": session_data['session_id'],
                "params_complete": True,
                "awaiting_confirmation": True,  # FLAG important
                "collected_params": collection_result['collected_params'],
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "agents_used": ["AnalysisAgent", "ConversationAgent"]
                }
            }
            #  Sauvegarder le prochain état et sortir
            session_data['next_state'] = ConversationState.WAITING_USER_CONFIRMATION
            session_data['state'] = ConversationState.FINAL_RESPONSE_READY
        else:
            # Paramètres incomplets, on pose la question suivante
            next_question = collection_result['next_question']
            conversation_result = self.conversation_agent.process_conversation_turn(
                user_message,
                collection_result['collected_params'],
                next_question,
                context_type="collection"
            )
            
            logger.info(f"📝 Paramètres: {collection_result['completion_rate']*100:.0f}% complets")
            
            session_data['final_response'] = {
                "success": True,
                "response": conversation_result['response'],
                "is_emergency": False,
                "needs_booking": False,
                "slots": [],
                "recommendations": [],
                "session_id": session_data['session_id'],
                "params_complete": False,
                "completion_rate": collection_result['completion_rate'],
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "agents_used": ["AnalysisAgent", "ConversationAgent"],
                    "collected_params": collection_result['collected_params']
                }
            }
            session_data['state'] = ConversationState.FINAL_RESPONSE_READY

    def _handle_waiting_confirmation(self, session_data: Dict, user_message: str):
        """État WAITING_USER_CONFIRMATION: Attend que l'utilisateur confirme ou ajoute des infos."""
        user_message_lower = user_message.lower().strip()
        
        logger.info(f"💬 Confirmation reçue: '{user_message}'")
        
        #  LOGIQUE SIMPLE : "non" seul ou variations = veut les solutions
        if user_message_lower in ['non', 'n', 'no', 'nope', 'rien', 'rien à ajouter', "c'est tout", 'ça suffit']:
            logger.info("✅ Utilisateur refuse d'ajouter → Passage à l'analyse")
            session_data['user_confirmed'] = True
            session_data['state'] = ConversationState.ANALYZING_AND_RESPONDING
            return
        
        # Si user dit explicitement "oui" ou veut ajouter quelque chose
        if user_message_lower in ['oui', 'o', 'yes', 'ouais', 'ok'] or len(user_message) > 10:
            logger.info("💬 Utilisateur veut ajouter des informations")
            
            empathetic_response = "Je vous écoute. N'hésitez pas à me dire tout ce qui vous pèse."
            
            session_data['final_response'] = {
                "success": True,
                "response": empathetic_response,
                "is_emergency": session_data.get('is_emergency', False),
                "needs_booking": False,
                "slots": [],
                "recommendations": [],
                "session_id": session_data['session_id'],
                "params_complete": True,
                "awaiting_more_info": True,
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "agents_used": ["ConversationAgent"]
                }
            }
            # Réouvrir la collecte
            session_data['user_confirmed'] = False
            session_data['params_complete'] = False
            session_data['state'] = ConversationState.FINAL_RESPONSE_READY
            return
        
        # Par défaut : passer à l'analyse
        logger.info("✅ Message ambigu → Passage à l'analyse par défaut")
        session_data['user_confirmed'] = True
        session_data['state'] = ConversationState.ANALYZING_AND_RESPONDING

    def _handle_analysis_and_response(self, session_data: Dict, user_message: str):
        """État ANALYZING_AND_RESPONDING: Orchestration complète des agents."""
        logger.info("✅ Paramètres complets - Déclenchement de l'analyse multi-agents")
        
        collected_params = session_data['collected_params']
        
        # 1. AnalysisAgent: Analyse psychologique
        analysis_result = self.analysis_agent.analyze_psychological_state(collected_params, user_message)
        
        # 2. CalendarAgent: Analyse de l'agenda
        calendar_result = self._run_calendar_agent(analysis_result)
        proposed_agenda_changes = calendar_result.get('proposed_changes', [])
        
        # 3. BookingAgent: Décision de prise de RDV
        booking_result = self._run_booking_agent(analysis_result, collected_params)
        
        # 4. RecommendationAgent: Génération de recommandations
        recommendations_result = self._run_recommendation_agent(analysis_result, collected_params)
        
        # Enrichir les recommandations avec les suggestions d'agenda
        if proposed_agenda_changes:
            recommendations_result['recommendations'].insert(0, {
                "type": "agenda",
                "titre": "Optimisation de votre planning",
                "message": calendar_result.get('calendar_message', ''),
                "proposed_changes": proposed_agenda_changes
            })

        # 5. ConversationAgent: Message de transition
        transition_message = self.conversation_agent.generate_transition_message("recommendations")
        final_response_text = f"{transition_message}"
        if booking_result['needs_booking']:
            final_response_text += f"\n\n{booking_result['reason']}"

        logger.info(f"✅ Orchestration complète: analyse={analysis_result['severity_level']}, "
                   f"booking={booking_result['needs_booking']}, "
                   f"reco={recommendations_result['count']}")

        session_data['final_response'] = {
            "success": True,
            "response": final_response_text,
            "is_emergency": False,
            "needs_booking": booking_result['needs_booking'],
            "slots": booking_result['slots'],
            "recommendations": recommendations_result['recommendations'],
            "analysis": analysis_result,
            "calendar_analysis": calendar_result,
            "session_id": session_data['session_id'],
            "params_complete": True,
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "agents_used": ["AnalysisAgent", "CalendarAgent", "BookingAgent", "RecommendationAgent", "ConversationAgent"],
                "severity": analysis_result['severity_level']
            }
        }
        session_data['state'] = ConversationState.FINAL_RESPONSE_READY

    # ═════════════════════════════════════════════════════════
    # EXÉCUTEURS D'AGENTS (AGENT RUNNERS)
    # ═════════════════════════════════════════════════════════

    def _run_calendar_agent(self, analysis_result: Dict) -> Dict:
        """Exécute le CalendarAgent si configuré."""
        if not self.calendar_agent.agenda_endpoint:
            return {}
        
        logger.info("📅 CalendarAgent: Analyse de l'agenda en cours...")
        
        # ⚠️ TEST : Forcer la date au 30 octobre 2025
        today = "2025-10-30"  # Date de test
        logger.warning(f"⚠️ TEST MODE: Analyse forcée pour {today}")
        
        calendar_result = self.calendar_agent.process_calendar_analysis(today, analysis_result)
        logger.info(f"📅 CalendarAgent: {len(calendar_result.get('proposed_changes', []))} propositions.")
        return calendar_result

    def _run_booking_agent(self, analysis_result: Dict, collected_params: Dict) -> Dict:
        """Exécute le BookingAgent."""
        booking_context = {
            'severity_level': analysis_result['severity_level'],
            'urgency_score': analysis_result['urgency_score'],
            'duration': collected_params.get('duration', ''),
            'symptomes': collected_params.get('symptomes', ''),
        }
        return self.booking_agent.process_booking_decision(booking_context)

    def _run_recommendation_agent(self, analysis_result: Dict, collected_params: Dict) -> Dict:
        """Exécute le RecommendationAgent."""
        recommendation_context = {
            'analysis': analysis_result,
            'collected_params': collected_params
        }
        return self.recommendation_agent.process_recommendation_request(recommendation_context)
    
    def _clarify_user_intention_with_gemini(self, user_message: str) -> str:
        """
        Utilise Gemini pour clarifier l'intention de l'utilisateur.
        
        Returns:
            - "add_more" : L'utilisateur veut ajouter des informations
            - "get_solutions" : L'utilisateur veut les solutions
            - "unclear" : Intention ambiguë
        """
        if not self.model:
            logger.warning("❌ Modèle Gemini non disponible pour clarification")
            return "get_solutions"  # Par défaut
        
        prompt = f"""Tu es un assistant d'analyse d'intention dans une conversation de soutien psychologique.

L'utilisateur a répondu: "{user_message}"

Contexte: L'assistant vient de demander "Souhaitez-vous ajouter quelque chose d'autre ou préférez-vous que je vous propose des solutions maintenant ?"

Analyse l'intention de l'utilisateur et réponds UNIQUEMENT par l'un de ces mots:
- "add_more" si l'utilisateur veut continuer à parler ou ajouter des informations
- "get_solutions" si l'utilisateur veut recevoir les solutions/recommandations
- "unclear" si l'intention n'est pas claire

EXEMPLES:
- "J'ai rien à ajouter" → "get_solutions"
- "Rien d'autre" → "get_solutions"
- "Non c'est tout" → "get_solutions"
- "Oui j'aimerais parler de..." → "add_more"
- "Encore une chose..." → "add_more"
- "Ok" → "unclear"

Réponds UNIQUEMENT avec le mot-clé, sans explication."""

        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.0,  # Précision maximale
                    max_output_tokens=10
                )
            )
            
            intention = response.text.strip().lower()
            
            if intention in ["add_more", "get_solutions", "unclear"]:
                logger.info(f"🤖 Intention Gemini: {intention}")
                return intention
            else:
                logger.warning(f"⚠️ Intention Gemini invalide: {intention}")
                return "get_solutions"
            
        except Exception as e:
            logger.error(f"❌ Erreur clarification intention: {e}")
            return "get_solutions"

    # ═════════════════════════════════════════════════════════
    # GESTION DE SESSION
    # ═════════════════════════════════════════════════════════
    
    def _get_or_create_session(self, session_id: str, user_message: str) -> Dict[str, Any]:
        """Récupère ou crée une session et initialise son état."""
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                'session_id': session_id,
                'state': ConversationState.ROUTING, # État initial
                'collected_params': {},
                'params_complete': False,
                'is_emergency': False,
                'created_at': datetime.now().isoformat(),
                'history': []
            }
        
        session = self.sessions[session_id]
        
        # ⚠️ CORRECTION : Préserver l'état d'urgence
        # Si en urgence → continuer la collecte au message suivant
        # Sinon → ROUTING pour détecter une éventuelle urgence
        if session.get('is_emergency', False):
            # Session en urgence → continuer la collecte
            logger.warning(f"⚠️ Session {session_id} en mode urgence - Continue collecte paramètres")
            session['state'] = ConversationState.COLLECTING_PARAMS
        else:
            # Session normale → ROUTING pour décision
            session['state'] = ConversationState.ROUTING
        
        session['history'].append({"role": "user", "message": user_message, "timestamp": datetime.now().isoformat()})
        return session
    
    def reset_session(self, session_id: str):
        """Réinitialise une session."""
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"♻️ Session {session_id} réinitialisée")
    
    def get_session_info(self, session_id: str) -> Optional[Dict]:
        """Retourne les informations d'une session."""
        return self.sessions.get(session_id)
    
    def get_stats(self) -> Dict[str, Any]:
        """Retourne des statistiques sur l'orchestrateur."""
        return {
            "total_sessions": len(self.sessions),
            "agents_count": 6, # Nous avons bien 6 agents
            "agents": [
                "AnalysisAgent",
                "BookingAgent",
                "RecommendationAgent",
                "EmergencyAgent",
                "ConversationAgent",
                "CalendarAgent"
            ],
            "architecture": "ADK State Machine"
        }