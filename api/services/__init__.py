# __init__.py
# __init__.py
# api/services/__init__.py
import logging

logger = logging.getLogger(__name__)

# Importer tous les services pour faciliter l'accès
from services.auth_service import AuthService
from services.user_service import UserService
from services.course_service import CourseService
from services.prediction_service import PredictionService
from services.simulation_service import SimulationService
from services.notification_service import NotificationService
from services.subscription_service import SubscriptionService

# Liste des services importés pour référence
__all__ = [
    'AuthService',
    'UserService',
    'CourseService',
    'PredictionService',
    'SimulationService',
    'NotificationService',
    'SubscriptionService'
]