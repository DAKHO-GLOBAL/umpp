# decorators.py
# decorators.py
# api/utils/decorators.py
from datetime import datetime
import logging
from functools import wraps
from flask import request, jsonify, current_app
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

logger = logging.getLogger(__name__)

def subscription_required(subscription_levels):
    """
    Décorateur qui vérifie si l'utilisateur possède un abonnement dans les niveaux requis.
    
    Args:
        subscription_levels (list): Liste des niveaux d'abonnement autorisés
        
    Returns:
        function: Le décorateur configuré
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            # Vérifier le JWT
            verify_jwt_in_request()
            
            # Récupérer l'ID utilisateur
            user_id = get_jwt_identity()
            
            # Importer User pour éviter les imports circulaires
            from models.user import User
            
            # Récupérer l'utilisateur depuis la base de données
            user = User.query.get(user_id)
            
            if not user:
                return jsonify({
                    "success": False,
                    "message": "User not found"
                }), 404
            
            # Vérifier si l'abonnement de l'utilisateur est dans la liste des niveaux autorisés
            if user.subscription_level not in subscription_levels:
                return jsonify({
                    "success": False,
                    "message": "This feature requires a higher subscription level",
                    "required_levels": subscription_levels,
                    "current_level": user.subscription_level
                }), 403
            
            # Vérifier si l'abonnement est actif et non expiré
            if not user.is_subscription_active():
                return jsonify({
                    "success": False,
                    "message": "Your subscription has expired",
                    "subscription_level": user.subscription_level,
                    "expiration_date": user.subscription_expiry.isoformat() if user.subscription_expiry else None
                }), 403
            
            # Si tout est bon, poursuivre avec la fonction originale
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def admin_required(fn):
    """
    Décorateur qui vérifie si l'utilisateur est administrateur.
    
    Returns:
        function: Le décorateur configuré
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        # Vérifier le JWT
        verify_jwt_in_request()
        
        # Récupérer l'ID utilisateur
        user_id = get_jwt_identity()
        
        # Importer User pour éviter les imports circulaires
        from models.user import User
        
        # Récupérer l'utilisateur depuis la base de données
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
        
        # Si tout est bon, poursuivre avec la fonction originale
        return fn(*args, **kwargs)
    return wrapper


def api_key_required(fn):
    """
    Décorateur qui vérifie si une clé API valide est fournie dans les en-têtes.
    
    Returns:
        function: Le décorateur configuré
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        # Récupérer la clé API depuis les en-têtes
        api_key = request.headers.get('X-API-Key')
        
        if not api_key:
            return jsonify({
                "success": False,
                "message": "API key is required"
            }), 401
        
        # Vérifier la validité de la clé API
        from models.api_key import ApiKey
        
        api_key_obj = ApiKey.query.filter_by(key=api_key, is_active=True).first()
        
        if not api_key_obj:
            return jsonify({
                "success": False,
                "message": "Invalid API key"
            }), 403
        
        # Vérifier si la clé API a expiré
        if api_key_obj.is_expired():
            return jsonify({
                "success": False,
                "message": "API key has expired"
            }), 403
        
        # Mettre à jour la dernière utilisation de la clé API
        api_key_obj.update_last_used()
        
        # Si tout est bon, poursuivre avec la fonction originale
        return fn(*args, **kwargs)
    return wrapper


def rate_limited(requests_per_minute=60):
    """
    Décorateur de limitation de taux basique basé sur l'adresse IP.
    Utilise le cache de l'application pour stocker les compteurs de requêtes.
    
    Args:
        requests_per_minute (int): Nombre maximum de requêtes autorisées par minute
        
    Returns:
        function: Le décorateur configuré
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            # Récupérer l'adresse IP du client
            client_ip = request.remote_addr
            
            # Clé de cache pour cette route et cette IP
            cache_key = f"rate_limit:{request.endpoint}:{client_ip}"
            
            # Récupérer les données de limite de taux du cache
            rate_data = current_app.cache.get(cache_key) or {"count": 0, "reset_time": datetime.now().timestamp() + 60}
            
            # Vérifier si la période de limite a été réinitialisée
            current_time = datetime.now().timestamp()
            if current_time > rate_data["reset_time"]:
                rate_data = {"count": 0, "reset_time": current_time + 60}
            
            # Vérifier si la limite de taux a été dépassée
            if rate_data["count"] >= requests_per_minute:
                return jsonify({
                    "success": False,
                    "message": "Rate limit exceeded",
                    "retry_after": int(rate_data["reset_time"] - current_time)
                }), 429
            
            # Incrémenter le compteur de requêtes
            rate_data["count"] += 1
            
            # Mettre à jour les données dans le cache
            current_app.cache.set(cache_key, rate_data, timeout=int(rate_data["reset_time"] - current_time) + 1)
            
            # Si tout est bon, poursuivre avec la fonction originale
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def log_api_call(fn):
    """
    Décorateur qui journalise chaque appel 
    
    Returns:
        function: Le décorateur configuré
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        # Récupérer l'ID utilisateur si disponible
        user_id = None
        try:
            verify_jwt_in_request(optional=True)
            user_id = get_jwt_identity()
        except:
            pass
        
        # Journaliser l'appel API
        logger.info(f"API Call: {request.method} {request.path} | User: {user_id or 'Anonymous'} | IP: {request.remote_addr}")
        
        # Si tout est bon, poursuivre avec la fonction originale
        return fn(*args, **kwargs)
    return wrapper