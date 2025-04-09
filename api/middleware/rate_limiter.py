# rate_limiter.py
# rate_limiter.py
# api/middleware/rate_limiter.py
import logging
from flask import request, jsonify, current_app
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

logger = logging.getLogger(__name__)

# Initialisé dans api/__init__.py
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

def get_api_key_or_ip():
    """
    Fonction de clé personnalisée qui utilise la clé API si présente,
    sinon utilise l'adresse IP.
    
    Returns:
        str: Clé API ou adresse IP
    """
    api_key = request.headers.get('X-API-Key')
    if api_key:
        return f"api_key:{api_key}"
    else:
        return get_remote_address()

def get_user_id():
    """
    Fonction de clé personnalisée qui utilise l'ID utilisateur si présent,
    sinon utilise l'adresse IP.
    
    Returns:
        str: ID utilisateur ou adresse IP
    """
    # Vérifier si le token JWT est valide et récupérer l'ID utilisateur
    try:
        from flask_jwt_extended import get_jwt_identity
        user_id = get_jwt_identity()
        if user_id:
            return f"user:{user_id}"
    except:
        pass
    
    return get_remote_address()

def configure_rate_limiter(app):
    """
    Configure le limiteur de taux pour l'application.
    
    Args:
        app: L'application Flask
    """
    # Initialiser le limiteur avec l'application Flask
    limiter.init_app(app)
    
    # Configurer le gestionnaire d'erreur
    @limiter.request_filter
    def exempt_api_keys():
        """
        Exempte les clés API premium de la limitation.
        
        Returns:
            bool: True si la clé est exemptée, False sinon
        """
        # Exemption de limitation pour les API keys premium
        api_key = request.headers.get('X-API-Key')
        if api_key:
            try:
                from models.api_key import ApiKey
                key = ApiKey.query.filter_by(key=api_key, is_active=True).first()
                
                # Vérifier si la clé appartient à un utilisateur premium
                if key and hasattr(key, 'user') and key.user:
                    is_premium = key.user.subscription_level == 'premium'
                    is_admin = getattr(key.user, 'is_admin', False)
                    return is_premium or is_admin
            except:
                logger.exception("Error checking API key for rate limiting exemption")
        
        return False
    
    # Exemption pour les adresses IP de la liste blanche
    @limiter.request_filter
    def exempt_whitelist():
        """
        Exempte les adresses IP de la liste blanche de la limitation.
        
        Returns:
            bool: True si l'IP est exemptée, False sinon
        """
        whitelist = current_app.config.get('RATE_LIMIT_WHITELIST', [])
        return request.remote_addr in whitelist
    
    # Journalisation des dépassements de limite
    @app.after_request
    def log_rate_limit_info(response):
        """
        Journalise les informations sur les limites de taux.
        
        Args:
            response: La réponse Flask
            
        Returns:
            Response: La réponse inchangée
        """
        # Journaliser les en-têtes de limitation de taux
        limit_headers = {
            'X-RateLimit-Limit': response.headers.get('X-RateLimit-Limit'),
            'X-RateLimit-Remaining': response.headers.get('X-RateLimit-Remaining'),
            'X-RateLimit-Reset': response.headers.get('X-RateLimit-Reset'),
            'Retry-After': response.headers.get('Retry-After')
        }
        
        # Si le code est 429, c'est un dépassement de limite
        if response.status_code == 429:
            logger.warning(
                f"Rate limit exceeded for {get_remote_address()} "
                f"on {request.path} - Headers: {limit_headers}"
            )
        
        return response
    
    logger.info("Rate limiter configured successfully")