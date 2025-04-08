# api/__init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_marshmallow import Marshmallow
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.middleware.proxy_fix import ProxyFix

db = SQLAlchemy()
ma = Marshmallow()
jwt = JWTManager()
limiter = Limiter(key_func=get_remote_address)

def create_app(config_object=None):
    """Crée et configure l'application Flask"""
    app = Flask(__name__)
    
    # Configurer l'application
    if config_object:
        app.config.from_object(config_object)
    else:
        # Configuration par défaut
        from api.config import get_config
        app.config.from_object(get_config())
    
    # Support pour les proxys
    app.wsgi_app = ProxyFix(app.wsgi_app)
    
    # Initialiser les extensions
    db.init_app(app)
    ma.init_app(app)
    jwt.init_app(app)
    limiter.init_app(app)
    CORS(app)
    
    # Configurer le logger
    from api.utils.logger import setup_logger
    setup_logger(app)
    
    # Gestionnaire d'erreurs global
    from api.middleware.error_handler import register_error_handlers
    register_error_handlers(app)
    
    # Enregistrer les blueprints
    from api.routes import register_routes
    register_routes(app)
    
    return app