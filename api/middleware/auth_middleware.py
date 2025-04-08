# auth_middleware.py
# auth_middleware.py
# api/middleware/auth_middleware.py
import logging
from functools import wraps
from flask import request, jsonify, current_app
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity

logger = logging.getLogger(__name__)

def authenticate_api_key():
    """
    Vérifie la validité d'une clé API.
    
    Returns:
        tuple: (success, user_id, message)
        - success: bool indiquant si la clé est valide
        - user_id: ID de l'utilisateur ou None
        - message: Message d'erreur ou None
    """
    api_key = request.headers.get('X-API-Key')
    if not api_key:
        return False, None, "API key is required"
    
    # Vérifier la validité de la clé
    try:
        from api.models.api_key import ApiKey
        key = ApiKey.query.filter_by(key=api_key, is_active=True).first()
        
        if not key:
            return False, None, "Invalid API key"
        
        # Vérifier si la clé a expiré
        if key.is_expired():
            return False, None, "API key has expired"
        
        # Mettre à jour la dernière utilisation
        key.update_last_used()
        
        return True, key.user_id, None
    except Exception as e:
        logger.error(f"Error authenticating API key: {str(e)}")
        return False, None, "Error authenticating API key"

def api_key_required(fn):
    """
    Décorateur qui requiert une clé API valide.
    
    Args:
        fn: La fonction à décorer
    
    Returns:
        function: La fonction décorée
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        success, user_id, message = authenticate_api_key()
        
        if not success:
            return jsonify({
                "success": False,
                "message": message
            }), 401
        
        # Stocker l'ID utilisateur pour le gestionnaire
        request.user_id = user_id
        
        return fn(*args, **kwargs)
    return wrapper

def jwt_or_api_key_required(fn):
    """
    Décorateur qui requiert soit un JWT valide, soit une clé API valide.
    
    Args:
        fn: La fonction à décorer
    
    Returns:
        function: La fonction décorée
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        # Essayer d'abord la clé API
        api_key = request.headers.get('X-API-Key')
        if api_key:
            success, user_id, message = authenticate_api_key()
            if success:
                # Stocker l'ID utilisateur pour le gestionnaire
                request.user_id = user_id
                return fn(*args, **kwargs)
        
        # Si la clé API n'est pas valide, essayer le JWT
        try:
            verify_jwt_in_request()
            # Stocker l'ID utilisateur pour le gestionnaire
            request.user_id = get_jwt_identity()
            return fn(*args, **kwargs)
        except Exception as e:
            return jsonify({
                "success": False,
                "message": "Authentication required. Please provide a valid API key or JWT token."
            }), 401
    return wrapper

def admin_required(fn):
    """
    Décorateur qui vérifie si l'utilisateur est administrateur.
    
    Args:
        fn: La fonction à décorer
    
    Returns:
        function: La fonction décorée
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        # Vérifier le JWT
        try:
            verify_jwt_in_request()
            user_id = get_jwt_identity()
            
            # Récupérer l'utilisateur depuis la base de données
            from api.models.user import User
            user = User.query.get(user_id)
            
            if not user:
                return jsonify({
                    "success": False,
                    "message": "User not found"
                }), 404
            
            # Vérifier si l'utilisateur est administrateur
            if not user.is_admin:
                return jsonify({
                    "success": False,
                    "message": "Admin access required"
                }), 403
            
            return fn(*args, **kwargs)
        except Exception as e:
            return jsonify({
                "success": False,
                "message": "Authentication required"
            }), 401
    return wrapper

def subscription_required(subscription_levels):
    """
    Décorateur qui vérifie si l'utilisateur a un abonnement suffisant.
    
    Args:
        subscription_levels (list): Liste des niveaux d'abonnement autorisés
    
    Returns:
        function: Le décorateur
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            # Vérifier le JWT
            try:
                verify_jwt_in_request()
                user_id = get_jwt_identity()
                
                # Récupérer l'utilisateur depuis la base de données
                from api.models.user import User
                user = User.query.get(user_id)
                
                if not user:
                    return jsonify({
                        "success": False,
                        "message": "User not found"
                    }), 404
                
                # Vérifier le niveau d'abonnement
                if user.subscription_level not in subscription_levels:
                    return jsonify({
                        "success": False,
                        "message": "This feature requires a higher subscription level",
                        "required_levels": subscription_levels,
                        "current_level": user.subscription_level
                    }), 403
                
                # Vérifier si l'abonnement est actif
                if not user.is_subscription_active():
                    return jsonify({
                        "success": False,
                        "message": "Your subscription has expired",
                        "subscription_level": user.subscription_level,
                        "expiration_date": user.subscription_expiry.isoformat() if user.subscription_expiry else None
                    }), 403
                
                return fn(*args, **kwargs)
            except Exception as e:
                return jsonify({
                    "success": False,
                    "message": "Authentication required"
                }), 401
        return wrapper
    return decorator

def register_auth_middleware(app):
    """
    Enregistre les middleware d'authentification pour l'application.
    
    Args:
        app: L'application Flask
    """
    # Middleware global - vérifier si l'API est en maintenance
    @app.before_request
    def check_maintenance_mode():
        """Vérifie si l'API est en mode maintenance"""
        if current_app.config.get('MAINTENANCE_MODE', False):
            # Toujours autoriser les administrateurs
            try:
                # Vérifier si c'est une clé API d'administrateur
                api_key = request.headers.get('X-API-Key')
                if api_key:
                    from api.models.api_key import ApiKey
                    key = ApiKey.query.filter_by(key=api_key, is_active=True).first()
                    if key and key.user and key.user.is_admin:
                        return None  # Autoriser
                
                # Vérifier si c'est un token JWT d'administrateur
                verify_jwt_in_request(optional=True)
                user_id = get_jwt_identity()
                if user_id:
                    from api.models.user import User
                    user = User.query.get(user_id)
                    if user and user.is_admin:
                        return None  # Autoriser
            except:
                pass
            
            # Refuser l'accès pour les autres
            return jsonify({
                "success": False,
                "message": "API is currently in maintenance mode. Please try again later."
            }), 503
    
    logger.info("Auth middleware registered successfully")