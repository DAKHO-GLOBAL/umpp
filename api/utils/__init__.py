# __init__.py
# __init__.py
# api/utils/__init__.py
import logging

logger = logging.getLogger(__name__)

# Importer les modules utilitaires pour faciliter l'accès
from api.utils.decorators import (
    admin_required, subscription_required, rate_limited, log_api_call,
    api_key_required, jwt_or_api_key_required
)

from api.utils.validators import (
    is_valid_email, is_valid_password, is_valid_username, is_valid_date,
    is_valid_uuid, is_valid_phone, is_valid_url, is_valid_subscription_level,
    is_valid_prediction_type, is_valid_simulation_type, is_valid_payment_method,
    sanitize_input, validate_date_range
)

from api.utils.logger import setup_logger, get_logger
from api.utils.email_sender import (
    send_email, send_welcome_email, send_reset_password_email,
    send_prediction_notification_email, send_odds_change_notification_email,
    send_upcoming_race_notification_email
)

from api.utils.firebase_client import (
    initialize_firebase, verify_firebase_token, send_push_notification,
    send_push_notification_to_multiple_devices, send_topic_notification,
    subscribe_to_topic, unsubscribe_from_topic, validate_fcm_token
)

# Liste des fonctions importées pour référence
__all__ = [
    # Decorators
    'admin_required', 'subscription_required', 'rate_limited', 'log_api_call',
    'api_key_required', 'jwt_or_api_key_required',
    
    # Validators
    'is_valid_email', 'is_valid_password', 'is_valid_username', 'is_valid_date',
    'is_valid_uuid', 'is_valid_phone', 'is_valid_url', 'is_valid_subscription_level',
    'is_valid_prediction_type', 'is_valid_simulation_type', 'is_valid_payment_method',
    'sanitize_input', 'validate_date_range',
    
    # Logger
    'setup_logger', 'get_logger',
    
    # Email sender
    'send_email', 'send_welcome_email', 'send_reset_password_email',
    'send_prediction_notification_email', 'send_odds_change_notification_email',
    'send_upcoming_race_notification_email',
    
    # Firebase client
    'initialize_firebase', 'verify_firebase_token', 'send_push_notification',
    'send_push_notification_to_multiple_devices', 'send_topic_notification',
    'subscribe_to_topic', 'unsubscribe_from_topic', 'validate_fcm_token'
]

logger.info("Utils module loaded successfully")