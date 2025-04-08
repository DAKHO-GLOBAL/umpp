# __init__.py
# __init__.py
# api/services/__init__.py
import logging

logger = logging.getLogger(__name__)

# Importer tous les services pour faciliter l'accès
from api.services.auth_service import AuthService
from api.services.user_service import UserService
from api.services.course_service import CourseService
from api.services.prediction_service import PredictionService
from api.services.simulation_service import SimulationService
from api.services.notification_service import NotificationService
from api.services.subscription_service import SubscriptionService

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