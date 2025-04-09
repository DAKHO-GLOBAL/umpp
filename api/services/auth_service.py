# auth_service.py
# auth_service.py
# api/services/auth_service.py
import logging
from datetime import datetime, timedelta
from flask import current_app
import jwt
import requests
import json

from app import db
from models.user import User
from models.token import ResetToken, RefreshToken
from utils.email_sender import send_reset_password_email
from services.user_service import UserService

class AuthService:
    """Service pour gérer l'authentification des utilisateurs"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.user_service = UserService()
    
    def register_user(self, email, password, first_name=None, last_name=None):
        """
        Inscrit un nouvel utilisateur.
        
        Args:
            email (str): Email de l'utilisateur
            password (str): Mot de passe
            first_name (str, optional): Prénom
            last_name (str, optional): Nom de famille
            
        Returns:
            User or None: L'utilisateur créé ou None en cas d'erreur
        """
        try:
            # Vérifier si l'email existe déjà
            existing_user = User.query.filter_by(email=email.lower()).first()
            if existing_user:
                raise ValueError("Email already exists")
            
            # Créer l'utilisateur
            user = self.user_service.create_user(
                email=email,
                username=self._generate_username(email, first_name, last_name),
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            
            return user
            
        except ValueError as e:
            # Renvoyer l'erreur de validation
            raise
        except Exception as e:
            self.logger.error(f"Error registering user: {str(e)}")
            return None
    
    def authenticate_user(self, email, password):
        """
        Authentifie un utilisateur avec son email et son mot de passe.
        
        Args:
            email (str): Email de l'utilisateur
            password (str): Mot de passe
            
        Returns:
            User or None: L'utilisateur si authentifié, None sinon
        """
        return self.user_service.authenticate_user(email, password)
    
    def authenticate_with_firebase(self, firebase_token):
        """
        Authentifie un utilisateur avec un token Firebase.
        
        Args:
            firebase_token (str): Token Firebase
            
        Returns:
            User or None: L'utilisateur si authentifié, None sinon
        """
        try:
            # Vérifier le token Firebase
            from utils.firebase_client import verify_firebase_token
            decoded_token = verify_firebase_token(firebase_token)
            
            if not decoded_token:
                raise ValueError("Invalid Firebase token")
            
            # Récupérer l'email de l'utilisateur
            email = decoded_token.get('email')
            if not email:
                raise ValueError("Email not found in Firebase token")
            
            # Rechercher l'utilisateur dans la base de données
            user = self.user_service.get_user_by_email(email)
            
            # Si l'utilisateur n'existe pas, le créer avec les données Firebase
            if not user:
                name_parts = decoded_token.get('name', '').split(' ', 1)
                first_name = name_parts[0] if name_parts else ''
                last_name = name_parts[1] if len(name_parts) > 1 else ''
                
                # Créer l'utilisateur avec un mot de passe aléatoire
                import uuid
                random_password = str(uuid.uuid4())
                
                user = self.user_service.create_user(
                    email=email,
                    username=self._generate_username(email, first_name, last_name),
                    password=random_password,
                    first_name=first_name,
                    last_name=last_name,
                    send_verification=False  # Pas besoin de vérification pour Firebase
                )
                
                # Marquer l'utilisateur comme vérifié
                user.is_verified = True
                db.session.commit()
            
            # Mettre à jour les statistiques de connexion
            user.update_login_stats()
            
            return user
            
        except ValueError as e:
            # Renvoyer l'erreur de validation
            raise
        except Exception as e:
            self.logger.error(f"Error authenticating with Firebase: {str(e)}")
            return None
    
    def generate_tokens(self, user_id):
        """
        Génère des tokens JWT pour un utilisateur.
        
        Args:
            user_id (int): ID de l'utilisateur
            
        Returns:
            dict: Tokens JWT générés
        """
        try:
            user = self.user_service.get_user_by_id(user_id)
            
            if not user:
                return None
            
            # Générer le token d'accès
            access_token_expires = current_app.config.get('JWT_ACCESS_TOKEN_EXPIRES', 3600)
            access_token_payload = {
                'sub': user_id,
                'iat': datetime.utcnow(),
                'exp': datetime.utcnow() + timedelta(seconds=access_token_expires),
                'role': 'admin' if user.is_admin else 'user',
                'level': user.subscription_level
            }
            
            access_token = jwt.encode(
                access_token_payload,
                current_app.config.get('JWT_SECRET_KEY'),
                algorithm='HS256'
            )
            
            # Générer le token de rafraîchissement
            refresh_token_expires = current_app.config.get('JWT_REFRESH_TOKEN_EXPIRES', 2592000)  # 30 jours par défaut
            refresh_token_payload = {
                'sub': user_id,
                'iat': datetime.utcnow(),
                'exp': datetime.utcnow() + timedelta(seconds=refresh_token_expires),
                'type': 'refresh'
            }
            
            refresh_token = jwt.encode(
                refresh_token_payload,
                current_app.config.get('JWT_SECRET_KEY'),
                algorithm='HS256'
            )
            
            # Sauvegarder le token de rafraîchissement
            expires_at = datetime.utcnow() + timedelta(seconds=refresh_token_expires)
            db_refresh_token = RefreshToken(
                user_id=user_id,
                token=refresh_token,
                expires_at=expires_at
            )
            
            db.session.add(db_refresh_token)
            db.session.commit()
            
            return {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'expires': access_token_expires
            }
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error generating tokens: {str(e)}")
            return None
    
    def refresh_access_token(self, refresh_token):
        """
        Rafraîchit le token d'accès avec un token de rafraîchissement.
        
        Args:
            refresh_token (str): Token de rafraîchissement
            
        Returns:
            dict or None: Nouveau token d'accès ou None en cas d'erreur
        """
        try:
            # Vérifier le token de rafraîchissement
            token_obj = RefreshToken.get_by_token(refresh_token)
            
            if not token_obj or not token_obj.is_valid():
                return None
            
            # Récupérer l'utilisateur
            user = self.user_service.get_user_by_id(token_obj.user_id)
            
            if not user or not user.is_active:
                return None
            
            # Générer un nouveau token d'accès
            access_token_expires = current_app.config.get('JWT_ACCESS_TOKEN_EXPIRES', 3600)
            access_token_payload = {
                'sub': user.id,
                'iat': datetime.utcnow(),
                'exp': datetime.utcnow() + timedelta(seconds=access_token_expires),
                'role': 'admin' if user.is_admin else 'user',
                'level': user.subscription_level
            }
            
            access_token = jwt.encode(
                access_token_payload,
                current_app.config.get('JWT_SECRET_KEY'),
                algorithm='HS256'
            )
            
            return {
                'access_token': access_token,
                'expires': access_token_expires
            }
            
        except Exception as e:
            self.logger.error(f"Error refreshing access token: {str(e)}")
            return None
    
    def revoke_token(self, refresh_token):
        """
        Révoque un token de rafraîchissement.
        
        Args:
            refresh_token (str): Token de rafraîchissement
            
        Returns:
            bool: True si le token a été révoqué, False sinon
        """
        try:
            # Récupérer et révoquer le token
            token_obj = RefreshToken.get_by_token(refresh_token)
            
            if not token_obj:
                return False
            
            return token_obj.revoke()
            
        except Exception as e:
            self.logger.error(f"Error revoking token: {str(e)}")
            return False
    
    def revoke_all_tokens(self, user_id):
        """
        Révoque tous les tokens de rafraîchissement d'un utilisateur.
        
        Args:
            user_id (int): ID de l'utilisateur
            
        Returns:
            int: Nombre de tokens révoqués
        """
        try:
            return RefreshToken.revoke_all_for_user(user_id)
            
        except Exception as e:
            self.logger.error(f"Error revoking all tokens: {str(e)}")
            return 0
    
    def send_password_reset_email(self, email):
        """
        Envoie un email de réinitialisation de mot de passe.
        
        Args:
            email (str): Email de l'utilisateur
            
        Returns:
            bool: True si l'email a été envoyé, False sinon
        """
        try:
            return self.user_service.request_password_reset(email)
            
        except Exception as e:
            self.logger.error(f"Error sending password reset email: {str(e)}")
            return False
    
    def reset_password(self, token, new_password):
        """
        Réinitialise le mot de passe d'un utilisateur.
        
        Args:
            token (str): Token de réinitialisation
            new_password (str): Nouveau mot de passe
            
        Returns:
            bool: True si la réinitialisation a réussi, False sinon
        """
        try:
            return self.user_service.reset_password(token, new_password)
            
        except Exception as e:
            self.logger.error(f"Error resetting password: {str(e)}")
            return False
    
    def verify_email(self, token):
        """
        Vérifie l'email d'un utilisateur.
        
        Args:
            token (str): Token de vérification
            
        Returns:
            User or None: L'utilisateur vérifié ou None en cas d'erreur
        """
        try:
            return self.user_service.verify_email(token)
            
        except Exception as e:
            self.logger.error(f"Error verifying email: {str(e)}")
            return None
    
    def _generate_username(self, email, first_name=None, last_name=None):
        """
        Génère un nom d'utilisateur unique.
        
        Args:
            email (str): Email de l'utilisateur
            first_name (str, optional): Prénom
            last_name (str, optional): Nom de famille
            
        Returns:
            str: Nom d'utilisateur unique
        """
        if first_name and last_name:
            base_username = f"{first_name.lower()}.{last_name.lower()}"
        elif first_name:
            base_username = first_name.lower()
        else:
            # Utiliser la partie avant @ de l'email
            base_username = email.split('@')[0].lower()
        
        # Nettoyer le nom d'utilisateur (lettres, chiffres et underscore seulement)
        import re
        base_username = re.sub(r'[^a-z0-9_]', '_', base_username)
        
        # Vérifier si le nom d'utilisateur existe déjà
        username = base_username
        counter = 1
        
        while User.query.filter_by(username=username).first():
            username = f"{base_username}{counter}"
            counter += 1
        
        return username