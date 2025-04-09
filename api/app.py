# api/app.py
from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_cors import CORS
from extensions import db, ma, jwt, limiter

def create_app(config_object=None):
    """Crée et configure l'application Flask"""
    app = Flask(__name__)
    
    # Configurer l'application
    if config_object:
        app.config.from_object(config_object)
    else:
        # Configuration par défaut
        from config import get_config
        app.config.from_object(get_config())
    
    # Support pour les proxys
    app.wsgi_app = ProxyFix(app.wsgi_app)
    
    # Initialiser les extensions
    db.init_app(app)
    ma.init_app(app)
    jwt.init_app(app)
    limiter.init_app(app)
    CORS(app)
    
    with app.app_context():
        # Configurer le logger
        from utils.logger import setup_logger
        setup_logger(app)
        
        # Gestionnaire d'erreurs global
        from middleware.error_handler import register_error_handlers
        register_error_handlers(app)
        
        # Enregistrer les blueprints
        from routes import register_routes
        register_routes(app)
    
    return app