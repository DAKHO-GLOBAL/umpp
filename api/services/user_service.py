# user_service.py
# user_service.py
# api/services/user_service.py
import logging
import json
from datetime import datetime, timedelta
from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func, and_, text

from extensions import db
from models.user import User, ResetToken
from models.token import VerificationToken
from models.notification import NotificationSetting
from utils.email_sender import send_welcome_email, send_reset_password_email

class UserService:
    """Service pour gérer les opérations liées aux utilisateurs"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def create_user(self, email, username, password, first_name=None, last_name=None, send_verification=True):
        """
        Crée un nouvel utilisateur.
        
        Args:
            email (str): Email de l'utilisateur
            username (str): Nom d'utilisateur
            password (str): Mot de passe
            first_name (str, optional): Prénom
            last_name (str, optional): Nom de famille
            send_verification (bool, optional): Envoyer un email de vérification
            
        Returns:
            User or None: L'utilisateur créé ou None en cas d'erreur
        """
        try:
            # Vérifier si l'email existe déjà
            if User.query.filter_by(email=email.lower()).first():
                raise ValueError("Email already exists")
            
            # Vérifier si le nom d'utilisateur existe déjà
            if User.query.filter_by(username=username).first():
                raise ValueError("Username already exists")
            
            # Créer l'utilisateur
            user = User(
                email=email.lower(),
                username=username,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            
            # Créer les paramètres de notification par défaut
            notification_settings = NotificationSetting(
                user_id=user.id,
                email_notifications=True,
                push_notifications=True,
                notify_predictions=True,
                notify_odds_changes=True,
                notify_upcoming_races=True,
                min_minutes_before_race=60
            )
            
            db.session.add(user)
            db.session.flush()  # Pour obtenir l'ID sans faire de commit
            
            # Attribuer les paramètres de notification à l'utilisateur
            notification_settings.user_id = user.id
            db.session.add(notification_settings)
            
            db.session.commit()
            
            # Envoyer un email de bienvenue
            try:
                send_welcome_email(user.email, user.get_full_name())
            except Exception as e:
                self.logger.error(f"Failed to send welcome email: {str(e)}")
            
            # Envoyer un email de vérification si demandé
            if send_verification:
                self._send_verification_email(user)
            
            return user
            
        except ValueError as e:
            # Renvoyer l'erreur de validation
            raise
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error creating user: {str(e)}")
            return None
    
    def get_user_by_id(self, user_id):
        """
        Récupère un utilisateur par son ID.
        
        Args:
            user_id (int): ID de l'utilisateur
            
        Returns:
            User or None: L'utilisateur ou None si non trouvé
        """
        return User.query.get(user_id)
    
    def get_user_by_email(self, email):
        """
        Récupère un utilisateur par son email.
        
        Args:
            email (str): Email de l'utilisateur
            
        Returns:
            User or None: L'utilisateur ou None si non trouvé
        """
        return User.query.filter_by(email=email.lower()).first()
    
    def get_user_by_username(self, username):
        """
        Récupère un utilisateur par son nom d'utilisateur.
        
        Args:
            username (str): Nom d'utilisateur
            
        Returns:
            User or None: L'utilisateur ou None si non trouvé
        """
        return User.query.filter_by(username=username).first()
    
    def authenticate_user(self, email, password):
        """
        Authentifie un utilisateur avec son email et son mot de passe.
        
        Args:
            email (str): Email de l'utilisateur
            password (str): Mot de passe
            
        Returns:
            User or None: L'utilisateur si authentifié, None sinon
        """
        user = self.get_user_by_email(email)
        
        if not user:
            return None
        
        if not user.is_active:
            return None
        
        if user.check_password(password):
            # Mettre à jour les statistiques de connexion
            user.update_login_stats()
            return user
        
        return None
    
    def update_user_profile(self, user_id, profile_data):
        """
        Met à jour le profil d'un utilisateur.
        
        Args:
            user_id (int): ID de l'utilisateur
            profile_data (dict): Données de profil à mettre à jour
            
        Returns:
            User or None: L'utilisateur mis à jour ou None en cas d'erreur
        """
        try:
            user = self.get_user_by_id(user_id)
            
            if not user:
                return None
            
            # Mettre à jour les champs du profil
            if 'first_name' in profile_data:
                user.first_name = profile_data['first_name']
            
            if 'last_name' in profile_data:
                user.last_name = profile_data['last_name']
            
            if 'bio' in profile_data:
                user.bio = profile_data['bio']
            
            if 'username' in profile_data:
                # Vérifier si le nom d'utilisateur est disponible
                existing_user = self.get_user_by_username(profile_data['username'])
                if existing_user and existing_user.id != user_id:
                    raise ValueError("Username already exists")
                
                user.username = profile_data['username']
            
            db.session.commit()
            return user
            
        except ValueError as e:
            # Renvoyer l'erreur de validation
            raise
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error updating user profile: {str(e)}")
            return None
    
    def change_user_password(self, user_id, current_password, new_password):
        """
        Change le mot de passe d'un utilisateur.
        
        Args:
            user_id (int): ID de l'utilisateur
            current_password (str): Mot de passe actuel
            new_password (str): Nouveau mot de passe
            
        Returns:
            bool: True si le changement a réussi, False sinon
        """
        try:
            user = self.get_user_by_id(user_id)
            
            if not user:
                return False
            
            # Vérifier le mot de passe actuel
            if not user.check_password(current_password):
                return False
            
            # Mettre à jour le mot de passe
            user.set_password(new_password)
            db.session.commit()
            
            return True
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error changing user password: {str(e)}")
            return False
    
    def reset_password(self, token, new_password):
        """
        Réinitialise le mot de passe d'un utilisateur avec un token.
        
        Args:
            token (str): Token de réinitialisation
            new_password (str): Nouveau mot de passe
            
        Returns:
            bool: True si la réinitialisation a réussi, False sinon
        """
        try:
            # Vérifier le token
            reset_token = ResetToken.query.filter_by(
                token=token,
                used=False
            ).first()
            
            if not reset_token or reset_token.expires_at < datetime.utcnow():
                return False
            
            # Récupérer l'utilisateur
            user = self.get_user_by_id(reset_token.user_id)
            
            if not user:
                return False
            
            # Mettre à jour le mot de passe
            user.set_password(new_password)
            
            # Marquer le token comme utilisé
            reset_token.used = True
            
            db.session.commit()
            
            return True
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error resetting password: {str(e)}")
            return False
    
    def request_password_reset(self, email):
        """
        Envoie un email de réinitialisation de mot de passe.
        
        Args:
            email (str): Email de l'utilisateur
            
        Returns:
            bool: True si l'email a été envoyé, False sinon
        """
        try:
            user = self.get_user_by_email(email)
            
            if not user:
                # Ne pas révéler que l'email n'existe pas pour des raisons de sécurité
                return True
            
            # Générer un token de réinitialisation
            token = ResetToken.generate_for_user(user.id)
            
            # Envoyer l'email de réinitialisation
            success = send_reset_password_email(user.email, token)
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error requesting password reset: {str(e)}")
            return False
    
    def verify_email(self, token):
        """
        Vérifie l'email d'un utilisateur avec un token.
        
        Args:
            token (str): Token de vérification
            
        Returns:
            User or None: L'utilisateur vérifié ou None en cas d'erreur
        """
        try:
            return VerificationToken.verify_token(token)
            
        except Exception as e:
            self.logger.error(f"Error verifying email: {str(e)}")
            return None
    
    def resend_verification_email(self, user_id):
        """
        Renvoie l'email de vérification à un utilisateur.
        
        Args:
            user_id (int): ID de l'utilisateur
            
        Returns:
            bool: True si l'email a été envoyé, False sinon
        """
        try:
            user = self.get_user_by_id(user_id)
            
            if not user:
                return False
            
            if user.is_verified:
                return True
            
            return self._send_verification_email(user)
            
        except Exception as e:
            self.logger.error(f"Error resending verification email: {str(e)}")
            return False
    
    def _send_verification_email(self, user):
        """
        Envoie un email de vérification à un utilisateur.
        
        Args:
            user (User): Utilisateur
            
        Returns:
            bool: True si l'email a été envoyé, False sinon
        """
        try:
            # Générer un token de vérification
            token = VerificationToken.generate_for_user(user.id)
            
            # Construire l'URL de vérification
            frontend_url = current_app.config.get('FRONTEND_URL', 'http://localhost:3000')
            verification_url = f"{frontend_url}/verify-email?token={token}"
            
            # Préparer les données pour le template
            data = {
                'user_name': user.get_full_name(),
                'verification_url': verification_url,
                'expiration_days': 7,
                'app_name': current_app.config.get('APP_NAME', 'PMU Prediction API'),
                'support_email': current_app.config.get('SUPPORT_EMAIL', 'support@example.com')
            }
            
            # Envoyer l'email
            from utils.email_sender import send_email
            success = send_email(
                recipient=user.email,
                subject=f"Verify your {data['app_name']} account",
                body="",  # Le contenu sera fourni par le template
                template_name='email_verification',
                data=data,
                html=True
            )
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error sending verification email: {str(e)}")
            return False
    
    def update_user_preferences(self, user_id, preferences):
        """
        Met à jour les préférences d'un utilisateur.
        
        Args:
            user_id (int): ID de l'utilisateur
            preferences (dict): Préférences à mettre à jour
            
        Returns:
            bool: True si la mise à jour a réussi, False sinon
        """
        try:
            user = self.get_user_by_id(user_id)
            
            if not user:
                return False
            
            # Récupérer les préférences actuelles
            current_prefs = user.get_preferences()
            
            # Mettre à jour avec les nouvelles préférences
            current_prefs.update(preferences)
            
            # Sauvegarder les préférences
            user.preferences = json.dumps(current_prefs)
            db.session.commit()
            
            return True
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error updating user preferences: {str(e)}")
            return False
    
    def update_notification_settings(self, user_id, settings):
        """
        Met à jour les paramètres de notification d'un utilisateur.
        
        Args:
            user_id (int): ID de l'utilisateur
            settings (dict): Paramètres de notification à mettre à jour
            
        Returns:
            bool: True si la mise à jour a réussi, False sinon
        """
        try:
            # Récupérer les paramètres de notification
            notification_settings = NotificationSetting.query.filter_by(user_id=user_id).first()
            
            if not notification_settings:
                # Créer les paramètres s'ils n'existent pas
                notification_settings = NotificationSetting(user_id=user_id)
                db.session.add(notification_settings)
            
            # Mettre à jour les paramètres
            for key, value in settings.items():
                if hasattr(notification_settings, key):
                    setattr(notification_settings, key, value)
            
            db.session.commit()
            
            return True
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error updating notification settings: {str(e)}")
            return False
    
    def get_notification_settings(self, user_id):
        """
        Récupère les paramètres de notification d'un utilisateur.
        
        Args:
            user_id (int): ID de l'utilisateur
            
        Returns:
            dict: Paramètres de notification
        """
        try:
            # Récupérer les paramètres de notification
            notification_settings = NotificationSetting.query.filter_by(user_id=user_id).first()
            
            if not notification_settings:
                return {
                    'email_notifications': True,
                    'push_notifications': True,
                    'notify_predictions': True,
                    'notify_odds_changes': True,
                    'notify_upcoming_races': True,
                    'min_minutes_before_race': 60
                }
            
            return {
                'email_notifications': notification_settings.email_notifications,
                'push_notifications': notification_settings.push_notifications,
                'notify_predictions': notification_settings.notify_predictions,
                'notify_odds_changes': notification_settings.notify_odds_changes,
                'notify_upcoming_races': notification_settings.notify_upcoming_races,
                'min_minutes_before_race': notification_settings.min_minutes_before_race
            }
            
        except Exception as e:
            self.logger.error(f"Error getting notification settings: {str(e)}")
            return {}
    
    def deactivate_user(self, user_id):
        """
        Désactive un compte utilisateur.
        
        Args:
            user_id (int): ID de l'utilisateur
            
        Returns:
            bool: True si la désactivation a réussi, False sinon
        """
        try:
            user = self.get_user_by_id(user_id)
            
            if not user:
                return False
            
            user.is_active = False
            db.session.commit()
            
            return True
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error deactivating user: {str(e)}")
            return False
    
    def reactivate_user(self, user_id):
        """
        Réactive un compte utilisateur.
        
        Args:
            user_id (int): ID de l'utilisateur
            
        Returns:
            bool: True si la réactivation a réussi, False sinon
        """
        try:
            user = self.get_user_by_id(user_id)
            
            if not user:
                return False
            
            user.is_active = True
            db.session.commit()
            
            return True
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error reactivating user: {str(e)}")
            return False
    
    def get_user_statistics(self, user_id):
        """
        Récupère les statistiques d'utilisation d'un utilisateur.
        
        Args:
            user_id (int): ID de l'utilisateur
            
        Returns:
            dict: Statistiques d'utilisation
        """
        try:
            # Récupérer des statistiques sur les prédictions
            prediction_query = text("""
            SELECT 
                COUNT(*) as total_predictions,
                COUNT(DISTINCT course_id) as unique_courses,
                MAX(created_at) as last_prediction
            FROM prediction_usage
            WHERE user_id = :user_id
            """)
            
            prediction_stats = db.session.execute(prediction_query, {"user_id": user_id}).fetchone()
            
            # Récupérer des statistiques sur les simulations
            simulation_query = text("""
            SELECT 
                COUNT(*) as total_simulations,
                COUNT(DISTINCT course_id) as unique_courses_sim,
                MAX(used_at) as last_simulation
            FROM simulation_usage
            WHERE user_id = :user_id
            """)
            
            simulation_stats = db.session.execute(simulation_query, {"user_id": user_id}).fetchone()
            
            # Récupérer l'utilisateur pour les statistiques de connexion
            user = self.get_user_by_id(user_id)
            
            statistics = {
                'predictions': {
                    'total': prediction_stats.total_predictions if prediction_stats else 0,
                    'unique_courses': prediction_stats.unique_courses if prediction_stats else 0,
                    'last_prediction': prediction_stats.last_prediction.isoformat() if prediction_stats and prediction_stats.last_prediction else None
                },
                'simulations': {
                    'total': simulation_stats.total_simulations if simulation_stats else 0,
                    'unique_courses': simulation_stats.unique_courses_sim if simulation_stats else 0,
                    'last_simulation': simulation_stats.last_simulation.isoformat() if simulation_stats and simulation_stats.last_simulation else None
                },
                'account': {
                    'login_count': user.login_count if user else 0,
                    'last_login': user.last_login.isoformat() if user and user.last_login else None,
                    'account_age_days': (datetime.utcnow() - user.created_at).days if user else 0,
                    'subscription_level': user.subscription_level if user else 'free',
                    'is_subscription_active': user.is_subscription_active() if user else False
                }
            }
            
            return statistics
            
        except Exception as e:
            self.logger.error(f"Error getting user statistics: {str(e)}")
            return {
                'predictions': {'total': 0, 'unique_courses': 0},
                'simulations': {'total': 0, 'unique_courses': 0},
                'account': {'login_count': 0}
            }
    
    def upgrade_subscription(self, user_id, plan_name, duration_months=1):
        """
        Met à niveau l'abonnement d'un utilisateur.
        
        Args:
            user_id (int): ID de l'utilisateur
            plan_name (str): Nom du plan d'abonnement
            duration_months (int): Durée en mois
            
        Returns:
            bool: True si la mise à niveau a réussi, False sinon
        """
        try:
            user = self.get_user_by_id(user_id)
            
            if not user:
                return False
            
            return user.upgrade_subscription(plan_name, duration_months)
            
        except Exception as e:
            self.logger.error(f"Error upgrading subscription: {str(e)}")
            return False
    
    def cancel_subscription(self, user_id):
        """
        Annule l'abonnement d'un utilisateur.
        
        Args:
            user_id (int): ID de l'utilisateur
            
        Returns:
            bool: True si l'annulation a réussi, False sinon
        """
        try:
            user = self.get_user_by_id(user_id)
            
            if not user:
                return False
            
            return user.cancel_subscription()
            
        except Exception as e:
            self.logger.error(f"Error cancelling subscription: {str(e)}")
            return False