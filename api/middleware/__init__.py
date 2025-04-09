# __init__.py
# __init__.py
# api/middleware/__init__.py
import logging

logger = logging.getLogger(__name__)

def register_middlewares(app):
    """
    Enregistre tous les middlewares pour l'application Flask
    
    Args:
        app: L'application Flask
    """
    # Middleware de gestion des erreurs
    from middleware.error_handler import register_error_handlers
    register_error_handlers(app)
    
    # Middleware de limitation de débit
    from middleware.rate_limiter import configure_rate_limiter
    configure_rate_limiter(app)
    
    # Middleware d'authentification
    from middleware.auth_middleware import register_auth_middleware
    register_auth_middleware(app)
    
    logger.info("All middlewares registered successfully")