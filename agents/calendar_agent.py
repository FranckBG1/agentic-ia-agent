import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import requests

logger = logging.getLogger(__name__)


class CalendarAgent:
    """
    Agent spécialisé dans l'analyse et l'optimisation de l'agenda.
    
    Responsabilités:
    - Analyser la charge de l'agenda Google Calendar
    - Détecter surcharge (> 8h/jour)
    - Proposer suppressions d'événements pour alléger
    - Ajouter pauses bien-être si charge faible
    - Coordonner avec AnalysisAgent pour décisions contextuelles
    """
    
    SEUIL_HEURES_JOURNALIER = 8  # Seuil de surcharge
    
    def __init__(self, agenda_endpoint: str = None):
        """
        Args:
            agenda_endpoint: URL unique de l'API Google Calendar
                - GET avec param date → Consulter
                - POST avec action=add → Ajouter
                - POST avec action=delete → Supprimer
        """
        self.agenda_endpoint = agenda_endpoint
        logger.info("✅ CalendarAgent initialisé")
    
    def consulter_agenda(self, date: str) -> tuple[str, List[Dict], float]:
        """
        Consulte l'agenda Google Calendar pour une date
        
        Args:
            date: Date au format YYYY-MM-DD
        
        Returns:
            tuple: (diagnostic_str, details_evenements, total_duration_heures)
        """
        if not self.agenda_endpoint:
            logger.warning("❌ Endpoint agenda non configuré")
            return "Endpoint non configuré", [], 0.0
        
        try:
            import urllib3
            # Désactiver les avertissements SSL
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            
            response = requests.get(
                self.agenda_endpoint, 
                params={"action_type": "CONSULT", "date": date}, 
                timeout=10,
                verify=False  # Désactiver vérification SSL
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get('code') != 200:
                error_msg = data.get('details', {}).get('message', 'Erreur inconnue')
                logger.error(f"❌ Erreur API agenda (code {data.get('code')}): {error_msg}")
                return error_msg, [], 0.0
            
            details = data.get('details', {})
            events = details.get('events', [])
            
            # Somme des durées de tous les événements
            total_duration_h = sum(e.get("duration_hours", 0) for e in events)
            
            diagnostic = f"Agenda du {date}: {len(events)} événement(s), {total_duration_h}h totales"
            
            logger.info(f"✅ Agenda consulté: {len(events)} événements, {total_duration_h}h")
            
            return diagnostic, events, total_duration_h
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Erreur consultation agenda: {e}")
            return f"Erreur réseau: {e}", [], 0.0
    
    def analyze_calendar_load(
        self,
        date: str,
        taux_mal_etre: float,
        severity_level: str
    ) -> Dict[str, Any]:
        """
        TA LOGIQUE EXACTE depuis app.py (analyze_psychological_state - partie calendrier)
        Analyse charge agenda et propose actions
        
        Args:
            date: Date à analyser (YYYY-MM-DD)
            taux_mal_etre: Taux de mal-être (0-100)
            severity_level: Sévérité (Élevé, Modéré, Faible)
        
        Returns:
            Dict contenant:
                - charge_totale_heures: float
                - nombre_evenements: int
                - charge_excessive: bool
                - proposed_changes: List[Dict] (suppressions proposées)
                - actions_effectuees: List[Dict] (pauses ajoutées)
                - calendar_message: str
                - awaiting_confirmation: bool
        """
        logger.info(f"📅 CalendarAgent: Analyse agenda pour {date}")
        
        # ═════════════════════════════════════════════════════════
        # 1. Consulter l'agenda
        # ═════════════════════════════════════════════════════════
        diagnostic, details_evenements, total_duration_h = self.consulter_agenda(date)
        
        logger.info(f"📅 Agenda {date}: {len(details_evenements)} événements, {total_duration_h}h totales")
        logger.info(f"📊 Taux mal-être: {taux_mal_etre}%, Sévérité: {severity_level}")
        
        if not details_evenements:
            logger.warning("⚠️ Agenda vide ou non accessible - Aucune analyse possible")
            return {
                "charge_totale_heures": 0,
                "nombre_evenements": 0,
                "charge_excessive": False,
                "proposed_changes": [],
                "actions_effectuees": [],
                "calendar_message": "",
                "awaiting_confirmation": False
            }
        
        # ═════════════════════════════════════════════════════════
        # 2. Déterminer si charge excessive
        # ═════════════════════════════════════════════════════════
        charge_excessive = total_duration_h > self.SEUIL_HEURES_JOURNALIER
        
        if charge_excessive:
            logger.warning(f"⚠️ SURCHARGE DÉTECTÉE: {total_duration_h}h > {self.SEUIL_HEURES_JOURNALIER}h")
        else:
            logger.info(f"✅ Charge normale: {total_duration_h}h ≤ {self.SEUIL_HEURES_JOURNALIER}h")
        
        # ═════════════════════════════════════════════════════════
        # 3. DÉCISION ET ACTIONS
        # ═════════════════════════════════════════════════════════
        
        # CAS 1: SURCHARGE + MAL-ÊTRE ÉLEVÉ (> 50%)
        if charge_excessive and taux_mal_etre > 50:
            logger.warning(f"🚨 CAS 1: SURCHARGE ({total_duration_h}h) + MAL-ÊTRE ÉLEVÉ ({taux_mal_etre}%)")
            return self._handle_overload_case(
                date,
                total_duration_h,
                taux_mal_etre,
                details_evenements
            )
        
        # CAS 2: CHARGE FAIBLE + BIEN-ÊTRE ÉLEVÉ (< 30%)
        elif not charge_excessive and taux_mal_etre < 30:
            return self._handle_wellbeing_case(
                date,
                total_duration_h,
                taux_mal_etre,
                details_evenements
            )
        
        # CAS 3: SITUATION NORMALE
        else:
            logger.info(f"🟡 Situation normale: charge={total_duration_h}h, mal-être={taux_mal_etre}%")
            return {
                "charge_totale_heures": total_duration_h,
                "nombre_evenements": len(details_evenements),
                "charge_excessive": charge_excessive,
                "proposed_changes": [],
                "actions_effectuees": [],
                "calendar_message": "",
                "awaiting_confirmation": False
            }
    
    def _handle_overload_case(
        self,
        date: str,
        total_duration_h: float,
        taux_mal_etre: float,
        details_evenements: List[Dict]
    ) -> Dict[str, Any]:
        """
        TA LOGIQUE EXACTE: CAS SURCHARGE + MAL-ÊTRE ÉLEVÉ
        Propose suppressions d'événements
        """
        logger.warning(f"🚨 CAS CRITIQUE: Surcharge ({total_duration_h}h) + Mal-être ({taux_mal_etre}%)")
        logger.warning(f"📋 Nombre événements reçus: {len(details_evenements)}")
        
        # Calculer heures à libérer
        hours_to_free = total_duration_h - self.SEUIL_HEURES_JOURNALIER
        logger.info(f"🎯 Objectif: libérer {hours_to_free}h")
        
        # Trier événements (moins prioritaires + longs d'abord)
        sortable_events = sorted(
            details_evenements,
            key=lambda e: (
                e.get('priority', 5),           # Priorité basse d'abord
                -e.get('duration_hours', 1)     # Plus longs d'abord
            )
        )
        
        logger.info(f"🔄 Événements triés: {[e.get('title') for e in sortable_events[:3]]}")
        
        # Proposer suppressions (SANS les exécuter)
        proposed_changes = []
        freed_hours = 0
        
        for event in sortable_events:
            if freed_hours >= hours_to_free:
                break
            
            event_id = event.get("id")
            event_title = event.get('title', 'Sans titre')
            event_duration = event.get('duration_hours', 1)
            event_start = event.get('start', 'N/A')
            
            if not event_id:
                continue
            
            # AJOUTER À PROPOSITIONS (pas de suppression automatique)
            proposed_changes.append({
                'action': 'DELETE',
                'event_id': event_id,
                'event_title': event_title,
                'event_start': event_start,
                'duration': event_duration,
                'reason': f"Alléger la charge (actuellement {total_duration_h}h)"
            })
            freed_hours += event_duration
            
            logger.info(f"🗑️ Proposition: '{event_title}' ({event_duration}h)")
        
        # Message utilisateur
        if proposed_changes:
            calendar_message = (
                f"Je comprends que votre journée est chargée ({total_duration_h}h). "
                f"Pour vous aider à retrouver un meilleur équilibre, j'ai identifié "
                f"{len(proposed_changes)} événement(s) qui pourraient être reportés ou annulés."
            )
            logger.warning(f"✅ {len(proposed_changes)} propositions créées")
            logger.warning(f"📦 Propositions: {[p['event_title'] for p in proposed_changes]}")
        else:
            calendar_message = "⚠️ Impossible d'identifier des événements à supprimer automatiquement."
            logger.warning("❌ Aucune proposition possible")
        
        result = {
            "charge_totale_heures": total_duration_h,
            "nombre_evenements": len(details_evenements),
            "charge_excessive": True,
            "proposed_changes": proposed_changes,
            "actions_effectuees": [],
            "calendar_message": calendar_message,
            "awaiting_confirmation": len(proposed_changes) > 0
        }
        
        logger.warning(f"🔥 RETOUR _handle_overload_case: {len(result.get('proposed_changes', []))} propositions")
        return result
    
    def _handle_wellbeing_case(
        self,
        date: str,
        total_duration_h: float,
        taux_mal_etre: float,
        details_evenements: List[Dict]
    ) -> Dict[str, Any]:
        """
        TA LOGIQUE EXACTE: CAS CHARGE FAIBLE + BIEN-ÊTRE ÉLEVÉ
        Ajoute pause bien-être
        """
        logger.info(f"🟢 CAS STABLE: Charge faible ({total_duration_h}h) + Bien-être ({taux_mal_etre}%)")
        
        # Payload pour ajouter pause
        payload_add = {
            "date": date,
            "title": "Pause Bien-être Recommandée",
            "duration_hours": 1,
            "description": f"Ajouté automatiquement : charge légère ({total_duration_h}h), mal-être faible ({taux_mal_etre}%)."
        }
        
        actions_effectuees = []
        calendar_message = ""
        
        try:
            add_result = self.executer_action_agenda("ADD", payload_add)
            
            if add_result.get('success'):
                calendar_message = "🌿 J'ai ajouté une pause bien-être à votre agenda pour favoriser votre équilibre."
                actions_effectuees.append({
                    'action': 'ADD',
                    'event_title': payload_add['title'],
                    'duration': 1,
                    'reason': f"Charge faible ({total_duration_h}h) + Bien-être élevé ({taux_mal_etre}%)"
                })
                logger.info("✅ Pause bien-être ajoutée")
            else:
                calendar_message = f"⚠️ Impossible d'ajouter la pause : {add_result.get('message', 'Erreur')}"
                logger.warning(f"❌ Échec ajout: {add_result.get('message')}")
        
        except Exception as e:
            logger.error(f"❌ Erreur ajout pause: {e}")
            calendar_message = f"❌ Erreur lors de l'ajout de la pause : {e}"
        
        return {
            "charge_totale_heures": total_duration_h,
            "nombre_evenements": len(details_evenements),
            "charge_excessive": False,
            "proposed_changes": [],
            "actions_effectuees": actions_effectuees,
            "calendar_message": calendar_message,
            "awaiting_confirmation": False
        }
    
    def executer_action_agenda(self, action: str, payload: Dict) -> Dict[str, Any]:
        """
        Exécute action sur agenda (ADD, DELETE, MOVE) via l'endpoint unique.
        
        Args:
            action: Type d'action (ADD, DELETE, MOVE)
            payload: Données de l'action
        
        Returns:
            Dict avec success: bool, message: str
        """
        if not self.agenda_endpoint:
            logger.warning("❌ Endpoint agenda non configuré")
            return {"success": False, "message": "Endpoint non configuré"}
        
        try:
            if action == "ADD":
                # POST avec action=add
                response = requests.post(
                    self.agenda_endpoint,
                    json={**payload, "action": "add"},
                    headers={"Content-Type": "application/json"},
                    timeout=10
                )
            elif action == "DELETE":
                # POST avec action=delete
                response = requests.post(
                    self.agenda_endpoint,
                    json={**payload, "action": "delete"},
                    headers={"Content-Type": "application/json"},
                    timeout=10
                )
            else:
                logger.warning(f"⚠️ Action '{action}' non implémentée")
                return {"success": False, "message": f"Action '{action}' non supportée"}
            
            response.raise_for_status()
            result = response.json()
            
            if result.get('success'):
                logger.info(f"✅ Action {action} exécutée: {payload.get('title', 'N/A')}")
            else:
                logger.warning(f"❌ Échec action {action}: {result.get('message')}")
            
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Erreur action {action}: {e}")
            return {"success": False, "message": str(e)}
    
    def process_calendar_analysis(
        self,
        date: str,
        analysis_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Pipeline complet d'analyse calendrier
        
        Args:
            date: Date à analyser
            analysis_context: Contexte depuis AnalysisAgent (taux_mal_etre, severity, etc.)
        
        Returns:
            Résultat complet analyse calendrier
        """
        taux_mal_etre = analysis_context.get('taux_mal_etre', 0) * 100  # Convertir 0-1 → 0-100
        severity_level = analysis_context.get('severity_level', 'Modéré')
        
        return self.analyze_calendar_load(date, taux_mal_etre, severity_level)
