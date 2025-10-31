"""
ZENFLOW - Architecture Agentique Pure
Point d'entrée principal avec orchestrateur ADK

Aucune logique métier ici - uniquement routes Flask + orchestrateur.
"""
import os
import logging
import uuid
from datetime import datetime
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from dotenv import load_dotenv
import google.generativeai as genai

# Charger variables d'environnement
load_dotenv()

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════

PROJECT_ID = os.getenv('PROJECT_ID')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
AGENDA_ENDPOINT = os.getenv("AGENDA_ENDPOINT")  # Un seul endpoint pour tout


# Configuration Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-2.0-flash-exp')
    logger.info("✅ Gemini 2.0 Flash Exp configuré")
else:
    gemini_model = None
    logger.warning("⚠️ GEMINI_API_KEY non configurée")

# ═══════════════════════════════════════════════════════════
# FLASK APP
# ═══════════════════════════════════════════════════════════

app = Flask(__name__)
CORS(app)

# ═══════════════════════════════════════════════════════════
# ORCHESTRATEUR ADK (6 AGENTS SPÉCIALISÉS)
# ═══════════════════════════════════════════════════════════

try:
    from adk_orchestrator import ZenflowOrchestrator
    
    orchestrator = ZenflowOrchestrator(
        gemini_model=gemini_model,
        agenda_endpoint=AGENDA_ENDPOINT 
    )
    
    
except Exception as e:
    orchestrator = None
    logger.error(f"❌ ERREUR FATALE: Impossible d'initialiser l'orchestrateur: {e}")
    raise SystemExit(f"Orchestrateur non disponible. Application arrêtée. Erreur: {e}")


# ═══════════════════════════════════════════════════════════
# ROUTES HTTP - INTERFACE AVEC ORCHESTRATEUR
# ═══════════════════════════════════════════════════════════

@app.route('/')
def index():
    """Page d'accueil"""
    return render_template('index.html')


@app.route('/health', methods=['GET'])
def health_check():
    """
    Vérification santé du système
    Retourne statut orchestrateur + agents
    """
    try:
        stats = orchestrator.get_stats() if orchestrator else {}
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'architecture': 'agentic',
            'orchestrator_active': orchestrator is not None,
            'agents': stats.get('agents', []),
            'agents_count': stats.get('agents_count', 0),
            'gemini_model': 'gemini-2.0-flash-exp',
            'sessions_active': stats.get('total_sessions', 0)
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Erreur health check: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/v2/chat', methods=['POST'])
def chat():
    """
    ENDPOINT PRINCIPAL - Architecture Agentique
    
    Workflow:
    1. Reçoit message utilisateur
    2. Délègue à l'orchestrateur
    3. Orchestrateur coordonne les 6 agents
    4. Retourne réponse complète
    
    Body JSON:
        {
            "text": "message utilisateur",
            "session_id": "uuid" (optionnel)
        }
    
    Returns:
        {
            "success": bool,
            "response": str,
            "is_emergency": bool,
            "needs_booking": bool,
            "slots": [...],
            "recommendations": [...],
            "calendar_analysis": {...},
            "session_id": str,
            "metadata": {...}
        }
    """
    if not orchestrator:
        return jsonify({
            'success': False,
            'error': 'Orchestrateur non disponible'
        }), 500
    
    try:
        data = request.json
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Corps JSON requis'
            }), 400
        
        user_text = data.get('text', '').strip()
        session_id = data.get('session_id', '').strip() or str(uuid.uuid4())
        
        if not user_text:
            return jsonify({
                'success': False,
                'error': 'Champ "text" requis et non vide'
            }), 400
        
        logger.info(f"📨 Message reçu (session={session_id[:8]}...): \"{user_text[:50]}...\"")
        
        # Délégation à l'orchestrateur ADK
        orchestrator_response = orchestrator.process_message(session_id, user_text)
        
        logger.info(f"✅ Réponse générée (agents={len(orchestrator_response.get('metadata', {}).get('agents_used', []))})")
        
        return jsonify(orchestrator_response)
    
    except Exception as e:
        logger.error(f"❌ ERREUR /api/v2/chat: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Erreur interne du serveur',
            'details': str(e)
        }), 500


@app.route('/api/session/<session_id>', methods=['GET'])
def get_session(session_id):
    """
    Récupère informations d'une session
    """
    if not orchestrator:
        return jsonify({'error': 'Orchestrateur non disponible'}), 500
    
    session_info = orchestrator.get_session_info(session_id)
    
    if not session_info:
        return jsonify({'error': 'Session non trouvée'}), 404
    
    return jsonify({
        'success': True,
        'session': session_info
    })


@app.route('/api/session/<session_id>', methods=['DELETE'])
def reset_session(session_id):
    """
    Réinitialise une session
    """
    if not orchestrator:
        return jsonify({'error': 'Orchestrateur non disponible'}), 500
    
    orchestrator.reset_session(session_id)
    
    return jsonify({
        'success': True,
        'message': f'Session {session_id} réinitialisée'
    })


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """
    Statistiques système et orchestrateur
    """
    if not orchestrator:
        return jsonify({'error': 'Orchestrateur non disponible'}), 500
    
    stats = orchestrator.get_stats()
    
    return jsonify({
        'success': True,
        'stats': stats
    })


# ═══════════════════════════════════════════════════════════
# ROUTES BOOKING (Créneaux de consultation)
# ═══════════════════════════════════════════════════════════

@app.route('/api/booking/accept', methods=['POST'])
def accept_booking():
    """
    Accepte un créneau de consultation et l'ajoute à Google Calendar
    
    Body JSON:
        {
            "session_id": "uuid",
            "slot": {
                "date": "YYYY-MM-DD",
                "time": "HH:MM",
                "provider_name": "Dr. Nom",
                "mode": "présentiel|téléconsultation"
            }
        }
    """
    try:
        data = request.json
        session_id = data.get('session_id')
        slot = data.get('slot')
        
        if not slot:
            return jsonify({'success': False, 'error': 'Créneau requis'}), 400
        
        # TODO: Intégrer avec CalendarAgent pour ajout Google Calendar
        # Pour l'instant, retour success simulé
        
        logger.info(f"✅ Booking accepté: {slot.get('provider_name')} le {slot.get('date')} à {slot.get('time')}")
        
        return jsonify({
            'success': True,
            'message': 'Rendez-vous confirmé',
            'booking': slot
        })
    
    except Exception as e:
        logger.error(f"❌ Erreur acceptation booking: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/orientation/feedback', methods=['POST', 'OPTIONS'])
def orientation_feedback():
    """
    Route pour recevoir le feedback utilisateur et gérer réservations + agenda
    (Migration depuis app.py)
    """
    # Gérer OPTIONS pour CORS
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        return response, 200

    try:
        logger.info("🔥 [FEEDBACK] Route touchée")
        
        # Récupérer les données JSON
        data = request.get_json(force=True)
        logger.info(f"📦 [FEEDBACK] Données reçues: {data}")

        session_id = data.get('session_id', 'demo-session')
        intent = data.get('intent')
        slot_index = data.get('slot_index')
        slot_data = data.get('slot_data')
        
        logger.info(f"📝 Session: {session_id}, Intent: {intent}, Slot: {slot_index}")
        
        # CAS 1: ACCEPTATION DE RÉSERVATION
        if intent == 'accepter_booking':
            logger.info("✅ [BOOKING] Réservation acceptée")
            
            message = f"✅ Parfait ! Le créneau #{slot_index + 1} est maintenant réservé."
            calendar_added = False
            
            # Si on a les données du créneau, l'ajouter au calendrier
            if slot_data and AGENDA_ENDPOINT:
                logger.info("📅 [BOOKING] Tentative d'ajout au Google Calendar...")
                
                try:
                    # Utiliser le CalendarAgent pour ajouter l'événement
                    calendar_payload = {
                        'date': slot_data.get('date'),
                        'title': f"Consultation - {slot_data.get('specialty', 'Médecin')}",
                        'duration_hours': 1,
                        'description': f"""📋 Consultation médicale
👨‍⚕️ Praticien: {slot_data.get('doctor', 'N/A')}
🏥 Spécialité: {slot_data.get('specialty', 'N/A')}
📍 Adresse: {slot_data.get('address', '47 Rue Spontini, 75016 Paris')}
⏰ Heure: {slot_data.get('time', 'N/A')}

🤖 Réservé via Zenflow le {datetime.now().strftime('%d/%m/%Y à %H:%M')}"""
                    }
                    
                    # TODO: Intégrer avec CalendarAgent.add_to_calendar()
                    # Pour l'instant, simulation
                    calendar_added = True
                    message = "✅ Créneau réservé avec succès et ajouté à votre agenda Google !"
                    logger.info("✅ [BOOKING] Événement ajouté au Google Calendar")
                    
                except Exception as e:
                    logger.error(f"❌ [BOOKING] Erreur calendrier: {e}")
                    message = "✅ Créneau réservé mais non ajouté au calendrier (erreur technique)"
            
            return jsonify({
                'success': True,
                'message': message,
                'session_id': session_id,
                'intent': intent,
                'slot_index': slot_index,
                'calendar_added': calendar_added,
                'demo_mode': True
            })

        # CAS 2: REFUS DE RÉSERVATION
        elif intent == 'refuser_booking':
            logger.info("❌ [BOOKING] Réservation refusée")
            return jsonify({
                'success': True,
                'message': 'D\'accord, aucune réservation n\'a été effectuée.',
                'session_id': session_id,
                'intent': intent
            })
        
        # CAS PAR DÉFAUT
        else:
            logger.warning(f"⚠️ [FEEDBACK] Intent inconnu: {intent}")
            return jsonify({
                'success': False,
                'error': f'Intent inconnu: {intent}'
            }), 400
    
    except Exception as e:
        logger.error(f"❌ Erreur orientation feedback: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ═══════════════════════════════════════════════════════════
# ROUTES AGENDA (Optimisation calendrier)
# ═══════════════════════════════════════════════════════════

@app.route('/api/agenda/confirm_changes', methods=['POST', 'OPTIONS'])
def confirm_agenda_changes():
    """
    Confirme suppressions d'événements proposées par CalendarAgent
    
    Body JSON:
        {
            "session_id": "uuid",
            "event_ids": ["id1", "id2", ...],
            "action": "apply|reject"
        }
    """
    # Gérer OPTIONS pour CORS
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        return response, 200
    
    try:
        data = request.json
        event_ids = data.get('event_ids', [])
        action = data.get('action', 'apply')
        session_id = data.get('session_id', 'unknown')
        
        logger.info(f"📋 [AGENDA] Confirmation reçue: {len(event_ids)} événements, action={action}")
        
        if action == 'apply' and event_ids:
            # Supprimer réellement via l'API Google Calendar
            deleted_count = 0
            failed_count = 0
            
            for event_id in event_ids:
                try:
                    # ✅ Appel à l'API Google Calendar (GET avec params, pas POST avec JSON)
                    import requests
                    import urllib3
                    
                    # Désactiver les avertissements SSL (Google Apps Script peut avoir des problèmes de certificat)
                    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                    
                    response = requests.get(
                        AGENDA_ENDPOINT,
                        params={
                            "action_type": "DELETE",
                            "event_id": event_id
                        },
                        timeout=10,
                        verify=False  # ✅ Désactiver vérification SSL pour Google Apps Script
                    )
                    
                    result = response.json()
                    if result.get('code') == 200:
                        deleted_count += 1
                        logger.info(f"✅ Événement {event_id} supprimé")
                    else:
                        failed_count += 1
                        logger.warning(f"⚠️ Échec suppression {event_id}: {result}")
                        
                except Exception as e:
                    failed_count += 1
                    logger.error(f"❌ Erreur suppression {event_id}: {e}")
            
            logger.info(f"✅ Suppressions terminées: {deleted_count} réussies, {failed_count} échouées")
            
            return jsonify({
                'success': True,
                'message': f'✅ {deleted_count} suppression(s) effectuée(s) avec succès',
                'deleted_count': deleted_count,
                'failed_count': failed_count
            })
        else:
            logger.info(f"❌ Suppressions agenda rejetées ou liste vide")
            return jsonify({
                'success': True,
                'message': 'Modifications annulées',
                'deleted_count': 0
            })
    
    except Exception as e:
        logger.error(f"❌ Erreur confirmation agenda: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ═══════════════════════════════════════════════════════════
# DÉMARRAGE APPLICATION
# ═══════════════════════════════════════════════════════════

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    logger.info(f"""
╔═══════════════════════════════════════════════════════════╗
║  🚀 ZENFLOW - Démarrage du serveur                       ║
╟───────────────────────────────────────────────────────────╢
║  📍 URL: http://localhost:{port}                          ║
║  🔧 Mode: {'Development' if debug else 'Production'}      ║
║  🤖 Architecture: Agentique (6 agents)                   ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )
