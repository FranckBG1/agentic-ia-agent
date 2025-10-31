"""
Fichier de base pour l'architecture agentique ADK - Agent de base

Ce fichier définit la classe `Agent` abstraite dont tous les agents spécialisés
de Zenflow hériteront.

Cette approche garantit une structure standardisée et modulaire, alignée avec
les principes du Google Agent Development Kit (ADK).
"""
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict

logger = logging.getLogger(__name__)

class Agent(ABC):
    """
    Classe de base abstraite pour tous les agents spécialisés.
    
    Chaque agent doit hériter de cette classe et implémenter la méthode `execute`.
    """
    
    def __init__(self, model: Any, name: str, instruction: str, description: str):
        """
        Initialise un agent.
        
        Args:
            model: Le grand modèle de langage (LLM) que l'agent utilisera comme "cerveau".
                   Ex: une instance de `google.generativeai.GenerativeModel`.
            name (str): Un nom unique pour l'agent (ex: "analysis_agent").
            instruction (str): Le prompt système ou l'instruction principale qui définit
                               le comportement et l'objectif de l'agent.
            description (str): Une courte description du rôle de l'agent.
        """
        if not all([model, name, instruction, description]):
            raise ValueError("Tous les paramètres (model, name, instruction, description) sont requis.")
            
        self.model = model
        self.name = name
        self.instruction = instruction
        self.description = description
        
        logger.info(f"🤖 Agent '{self.name}' initialisé. Description: {self.description}")

    @abstractmethod
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Le point d'entrée principal pour faire travailler l'agent.
        
        Cette méthode doit être implémentée par chaque agent spécialisé. Elle prend
        un dictionnaire de contexte en entrée et doit retourner un dictionnaire
        contenant les résultats de son travail.
        
        Args:
            context (Dict[str, Any]): Un dictionnaire contenant toutes les données
                                      nécessaires à l'agent pour sa tâche (ex: message
                                      utilisateur, état de la session, etc.).
        
        Returns:
            Dict[str, Any]: Un dictionnaire avec les résultats de l'agent.
        """
        pass

    def __repr__(self) -> str:
        return f"Agent(name='{self.name}', description='{self.description}')"

