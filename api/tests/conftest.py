# conftest.py
# conftest.py
import os
import pytest
from datetime import datetime, timedelta
import jwt
from flask import current_app

from api import create_app, db
from config import TestingConfig
from models.user import User
from models.course import Course, Participation, Cheval, Jockey

@pytest.fixture(scope='module')
def app():
    """Crée une instance de l'application Flask pour les tests"""
    app = create_app(TestingConfig)
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture(scope='module')
def client(app):
    """Retourne un client de test pour l'application"""
    return app.test_client()

@pytest.fixture(scope='module')
def db_instance(app):
    """Retourne une instance de la base de données"""
    with app.app_context():
        yield db

@pytest.fixture
def auth_headers(app):
    """Génère des en-têtes d'authentification JWT pour les tests"""
    with app.app_context():
        # Créer un token de test
        access_token = jwt.encode(
            {
                'sub': 1,  # ID utilisateur fictif
                'exp': datetime.utcnow() + timedelta(hours=1),
                'role': 'user',
                'level': 'standard'
            },
            current_app.config['JWT_SECRET_KEY'],
            algorithm='HS256'
        )
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        return headers

@pytest.fixture
def admin_auth_headers(app):
    """Génère des en-têtes d'authentification JWT pour les tests admin"""
    with app.app_context():
        # Créer un token de test admin
        access_token = jwt.encode(
            {
                'sub': 2,  # ID utilisateur admin fictif
                'exp': datetime.utcnow() + timedelta(hours=1),
                'role': 'admin',
                'level': 'premium'
            },
            current_app.config['JWT_SECRET_KEY'],
            algorithm='HS256'
        )
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        return headers

@pytest.fixture
def test_user(app, db_instance):
    """Crée un utilisateur de test dans la base de données"""
    with app.app_context():
        user = User(
            email='test@example.com',
            username='testuser',
            first_name='Test',
            last_name='User',
            subscription_level='standard',
            is_active=True,
            is_verified=True
        )
        user.set_password('password123')
        db_instance.session.add(user)
        db_instance.session.commit()
        
        yield user
        
        # Nettoyer après le test
        db_instance.session.delete(user)
        db_instance.session.commit()

@pytest.fixture
def test_course(app, db_instance):
    """Crée une course de test dans la base de données"""
    with app.app_context():
        # Créer une course
        course = Course(
            date_heure=datetime.now() + timedelta(days=1),
            lieu='Hippodrome Test',
            type_course='Plat',
            distance=2400,
            terrain='Bon',
            num_course=1,
            libelle='Course de test'
        )
        db_instance.session.add(course)
        db_instance.session.flush()
        
        # Créer quelques chevaux
        chevaux = []
        for i in range(1, 6):
            cheval = Cheval(
                nom=f'Cheval Test {i}',
                age=5,
                sexe='M' if i % 2 == 0 else 'F'
            )
            db_instance.session.add(cheval)
            chevaux.append(cheval)
        
        # Créer un jockey
        jockey = Jockey(
            nom='Jockey Test',
            pays='France'
        )
        db_instance.session.add(jockey)
        db_instance.session.flush()
        
        # Créer des participations
        for i, cheval in enumerate(chevaux, start=1):
            participation = Participation(
                id_course=course.id,
                id_cheval=cheval.id,
                id_jockey=jockey.id,
                numPmu=i,
                cote_initiale=5.0 + i * 0.5,
                cote_actuelle=4.5 + i * 0.5
            )
            db_instance.session.add(participation)
        
        db_instance.session.commit()
        
        yield course
        
        # Nettoyer après le test
        db_instance.session.execute(f"DELETE FROM participations WHERE id_course = {course.id}")
        db_instance.session.delete(course)
        for cheval in chevaux:
            db_instance.session.delete(cheval)
        db_instance.session.delete(jockey)
        db_instance.session.commit()