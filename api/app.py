# app.py
# api/app.py
#from create_app import create_app
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
from config import get_config

app = create_app(get_config())

@app.route('/health')
def health_check():
    """Route simple pour vérifier que l'API fonctionne"""
    return {'status': 'healthy', 'version': '1.0.0'}, 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)


# api/wsgi.py
from app import app

if __name__ == "__main__":
    app.run()



