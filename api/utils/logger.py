# logger.py
# logger.py
# api/utils/logger.py
import os
import logging
import datetime
from logging.handlers import RotatingFileHandler, SMTPHandler
from flask import request, has_request_context

class RequestFormatter(logging.Formatter):
    """Format de journalisation qui inclut des informations sur la requête"""
    
    def format(self, record):
        """Ajoute des informations sur la requête au format du journal"""
        if has_request_context():
            record.url = request.url
            record.remote_addr = request.remote_addr
            record.method = request.method
            
            # Ajouter l'utilisateur si authentifié
            try:
                from flask_jwt_extended import get_jwt_identity
                user_id = get_jwt_identity()
                if user_id:
                    record.user_id = user_id
                else:
                    record.user_id = 'anonymous'
            except:
                record.user_id = 'unknown'
        else:
            record.url = None
            record.remote_addr = None
            record.method = None
            record.user_id = None
        
        return super().format(record)

def setup_logger(app):
    """
    Configure le logger pour l'application.
    
    Args:
        app: L'application Flask
    """
    # Configurer le niveau de journalisation
    log_level = app.config.get('LOG_LEVEL', 'INFO')
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        numeric_level = logging.INFO
    
    # Créer le dossier logs s'il n'existe pas
    log_dir = app.config.get('LOG_DIR', 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Nom du fichier journal
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    log_file = os.path.join(log_dir, f'{today}_app.log')
    app.config['LOG_FILE'] = log_file
    
    # Format des messages de journal
    if app.debug:
        formatter = RequestFormatter(
            '[%(asctime)s] %(remote_addr)s - %(user_id)s - %(levelname)s in %(module)s: %(message)s'
        )
    else:
        formatter = RequestFormatter(
            '[%(asctime)s] %(remote_addr)s - User:%(user_id)s - %(levelname)s: %(message)s'
        )
    
    # Handler pour les fichiers (avec rotation)
    file_handler = RotatingFileHandler(log_file, maxBytes=10485760, backupCount=10)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(numeric_level)
    
    # Handler pour la console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(numeric_level)
    
    # Handler pour les emails (erreurs critiques seulement)
    if not app.debug and app.config.get('MAIL_SERVER'):
        mail_handler = SMTPHandler(
            mailhost=(app.config.get('MAIL_SERVER'), app.config.get('MAIL_PORT')),
            fromaddr=app.config.get('MAIL_DEFAULT_SENDER'),
            toaddrs=app.config.get('ADMINS', ['admin@example.com']),
            subject='PMU Prediction Application Error',
            credentials=(app.config.get('MAIL_USERNAME'), app.config.get('MAIL_PASSWORD')),
            secure=app.config.get('MAIL_USE_TLS')
        )
        mail_handler.setLevel(logging.ERROR)
        mail_handler.setFormatter(formatter)
        app.logger.addHandler(mail_handler)
    
    # Supprimer les handlers existants
    del app.logger.handlers[:]
    
    # Ajouter les handlers configurés
    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)
    
    # Définir le niveau du logger de l'app
    app.logger.setLevel(numeric_level)
    
    # Configurer également le logger racine
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Supprimer les handlers existants du logger racine
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Ajouter nos handlers au logger racine
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Configurer le logger SQLAlchemy
    if app.config.get('SQLALCHEMY_ECHO', False):
        logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
    else:
        logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    
    app.logger.info(f"Logger configured with level {log_level}")
    
    return app.logger

def get_logger(name):
    """
    Récupère un logger configuré pour un module spécifique.
    
    Args:
        name (str): Nom du module
        
    Returns:
        Logger: Logger configuré
    """
    return logging.getLogger(name)