# api/config.py
import os
from dotenv import load_dotenv

# Charger les variables d'environnement depuis .env
load_dotenv()

class Config:
    """Configuration de base pour l'application"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'default-secret-key-for-development'
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'default-jwt-secret-key'
    JWT_ACCESS_TOKEN_EXPIRES = 3600  # 1 heure
    
    # Configuration de la base de données
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'mysql+pymysql://root:@localhost:3306/pmu_ia'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Dossier pour les modèles entraînés
    MODEL_PATH = os.environ.get('MODEL_PATH') or 'model/trained_models'
    
    # Configuration pour Firebase
    FIREBASE_API_KEY = os.environ.get('FIREBASE_API_KEY')
    FIREBASE_AUTH_DOMAIN = os.environ.get('FIREBASE_AUTH_DOMAIN')
    FIREBASE_PROJECT_ID = os.environ.get('FIREBASE_PROJECT_ID')
    
    # Configuration pour les emails
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') or True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    
    # Rate limiting
    RATELIMIT_DEFAULT = "100/hour"
    RATELIMIT_STORAGE_URL = "memory://"
    
    # Niveaux d'abonnement
    SUBSCRIPTION_LEVELS = {
        'free': {
            'predictions_per_day': 5,
            'simulations_per_day': 2,
            'features': ['basic_predictions']
        },
        'standard': {
            'predictions_per_day': 30,
            'simulations_per_day': 15,
            'features': ['basic_predictions', 'top3_predictions', 'basic_simulations']
        },
        'premium': {
            'predictions_per_day': -1,  # Illimité
            'simulations_per_day': -1,  # Illimité
            'features': ['basic_predictions', 'top3_predictions', 'top7_predictions', 
                        'basic_simulations', 'advanced_simulations', 'notifications']
        }
    }


class DevelopmentConfig(Config):
    """Configuration pour le développement"""
    DEBUG = True
    TESTING = False
    
    # Configuration logger
    LOG_LEVEL = 'DEBUG'
    

class TestingConfig(Config):
    """Configuration pour les tests"""
    DEBUG = False
    TESTING = True
    
    # Base de données de test
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
    # Configuration logger
    LOG_LEVEL = 'INFO'


class ProductionConfig(Config):
    """Configuration pour la production"""
    DEBUG = False
    TESTING = False
    
    # Générer une clé secrète forte pour la production
    SECRET_KEY = os.environ.get('SECRET_KEY')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
    
    # Configuration logger
    LOG_LEVEL = 'ERROR'
    
    # Rate limiting plus strict
    RATELIMIT_DEFAULT = "50/hour"


# Configuration selon l'environnement
config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig
}

# Configuration par défaut
def get_config():
    env = os.environ.get('FLASK_ENV', 'development')
    return config_by_name[env]