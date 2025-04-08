# test_auth.py
# test_auth.py
import json
import pytest
from flask import url_for

def test_register(client):
    """Test de l'inscription utilisateur"""
    response = client.post(
        '/api/auth/register',
        json={
            'email': 'new_user@example.com',
            'username': 'newuser',
            'password': 'SecurePass123',
            'confirm_password': 'SecurePass123',
            'first_name': 'New',
            'last_name': 'User'
        }
    )
    
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['success'] is True
    assert 'access_token' in data
    assert 'user' in data
    assert data['user']['email'] == 'new_user@example.com'

def test_login(client, test_user):
    """Test de la connexion utilisateur"""
    response = client.post(
        '/api/auth/login',
        json={
            'email': 'test@example.com',
            'password': 'password123'
        }
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    assert 'access_token' in data
    assert 'refresh_token' in data
    assert data['user']['email'] == 'test@example.com'

def test_login_invalid_credentials(client):
    """Test de la connexion avec des identifiants invalides"""
    response = client.post(
        '/api/auth/login',
        json={
            'email': 'test@example.com',
            'password': 'wrongpassword'
        }
    )
    
    assert response.status_code == 401
    data = json.loads(response.data)
    assert data['success'] is False

def test_refresh_token(client, auth_headers):
    """Test du rafraîchissement du token"""
    response = client.post(
        '/api/auth/refresh',
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    assert 'access_token' in data

def test_password_reset_request(client):
    """Test de la demande de réinitialisation de mot de passe"""
    response = client.post(
        '/api/auth/forgot-password',
        json={
            'email': 'test@example.com'
        }
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True