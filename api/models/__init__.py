# __init__.py
# __init__.py
# api/models/__init__.py
import logging

logger = logging.getLogger(__name__)

# Importer tous les modèles pour s'assurer qu'ils sont correctement enregistrés auprès de SQLAlchemy
from api.models.user import User, ResetToken
from api.models.token import VerificationToken, RefreshToken
from api.models.course import Course, Participation, Cheval, Jockey, CoteHistorique, CommentaireCourse
from api.models.prediction import Prediction, PredictionUsage, ModelVersion, PredictionEvaluation
from api.models.simulation import Simulation, SimulationUsage, SimulationComparison, SimulationAnimation, PredefinedScenario
from api.models.subscription import UserSubscription, SubscriptionPlan, PaymentTransaction, PromotionCode
from api.models.notification import Notification, NotificationSetting, UserDevice
from api.models.api_key import ApiKey

def create_tables(db):
    """Crée toutes les tables dans la base de données"""
    logger.info("Creating all database tables")
    db.create_all()
    logger.info("All database tables created successfully")

def drop_tables(db):
    """Supprime toutes les tables de la base de données"""
    logger.warning("Dropping all database tables")
    db.drop_all()
    logger.warning("All database tables dropped")

# Liste des modèles pour référence
__all__ = [
    'User', 'ResetToken', 'VerificationToken', 'RefreshToken',
    'Course', 'Participation', 'Cheval', 'Jockey', 'CoteHistorique', 'CommentaireCourse',
    'Prediction', 'PredictionUsage', 'ModelVersion', 'PredictionEvaluation',
    'Simulation', 'SimulationUsage', 'SimulationComparison', 'SimulationAnimation', 'PredefinedScenario',
    'UserSubscription', 'SubscriptionPlan', 'PaymentTransaction', 'PromotionCode',
    'Notification', 'NotificationSetting', 'UserDevice',
    'ApiKey'
]