"""
Agents spécialisés pour architecture agentique Zenflow
Chaque agent a sa responsabilité et collabore avec les autres
"""

from .analysis_agent import AnalysisAgent
from .booking_agent import BookingAgent
from .recommendation_agent import RecommendationAgent
from .emergency_agent import EmergencyAgent
from .conversation_agent import ConversationAgent
from .calendar_agent import CalendarAgent

__all__ = [
    'AnalysisAgent',
    'BookingAgent',
    'RecommendationAgent',
    'EmergencyAgent',
    'ConversationAgent',
    'CalendarAgent'
]
