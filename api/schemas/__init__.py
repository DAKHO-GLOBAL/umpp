# __init__.py
# __init__.py
# api/schemas/__init__.py
import logging

logger = logging.getLogger(__name__)

# Importer tous les schémas pour faciliter l'accès
from api.schemas.user_schema import (
    UserLoginSchema, UserRegisterSchema, UserProfileSchema, 
    UserPasswordChangeSchema, PasswordResetRequestSchema, PasswordResetSchema,
    EmailVerificationSchema, UserPreferencesSchema, AdminUserUpdateSchema
)

from api.schemas.prediction_schema import (
    PredictionRequestSchema, CommentRequestSchema, OddsFilterSchema,
    PredictionFilterSchema, BettingRequestSchema, PredictionCompareSchema,
    PredictionExportSchema, PredictionAnalysisRequestSchema,
    EvaluationRequestSchema, EvaluationFilterSchema, DailyPredictionRequestSchema
)

from api.schemas.simulation_schema import (
    SimulationRequestSchema, HorseModificationSchema, WeatherConditionSchema,
    TrackConditionSchema, AdvancedSimulationRequestSchema,
    SimulationComparisonRequestSchema, SimulationAnimationRequestSchema,
    SimulationExportRequestSchema
)

from api.schemas.notification_schema import (
    NotificationSchema, NotificationSettingsSchema, DeviceRegistrationSchema
)

# Liste des schémas importés pour référence
__all__ = [
    'UserLoginSchema', 'UserRegisterSchema', 'UserProfileSchema', 
    'UserPasswordChangeSchema', 'PasswordResetRequestSchema', 'PasswordResetSchema',
    'EmailVerificationSchema', 'UserPreferencesSchema', 'AdminUserUpdateSchema',
    
    'PredictionRequestSchema', 'CommentRequestSchema', 'OddsFilterSchema',
    'PredictionFilterSchema', 'BettingRequestSchema', 'PredictionCompareSchema',
    'PredictionExportSchema', 'PredictionAnalysisRequestSchema',
    'EvaluationRequestSchema', 'EvaluationFilterSchema', 'DailyPredictionRequestSchema',
    
    'SimulationRequestSchema', 'HorseModificationSchema', 'WeatherConditionSchema',
    'TrackConditionSchema', 'AdvancedSimulationRequestSchema',
    'SimulationComparisonRequestSchema', 'SimulationAnimationRequestSchema',
    'SimulationExportRequestSchema',
    
    'NotificationSchema', 'NotificationSettingsSchema', 'DeviceRegistrationSchema'
]