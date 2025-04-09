# user.py

# user.py
# api/models/user.py
from datetime import datetime, timedelta
import jwt
import uuid
import os
import json
from flask import current_app
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Text, ForeignKey, text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from werkzeug.security import generate_password_hash, check_password_hash

from extensions import db
from models.notification import NotificationSetting, Notification, UserDevice
from models.subscription import UserSubscription
#from models.api_key import ApiKey
from models.token import ResetToken  # Importez-le ici si vous y faites référence

class User(db.Model):
    """Modèle utilisateur pour l'application de prédiction PMU"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    username = Column(String(80), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(50), nullable=True)
    last_name = Column(String(50), nullable=True)
    profile_picture = Column(String(255), nullable=True)
    bio = Column(Text, nullable=True)
    
    # Statut du compte
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    verification_token = Column(String(100), nullable=True)
    
    # Données d'abonnement
    subscription_level = Column(String(20), default='free')  # free, standard, premium
    subscription_start = Column(DateTime, nullable=True)
    subscription_expiry = Column(DateTime, nullable=True)
    
    # Données de paiement et facturation
    billing_address = Column(Text, nullable=True)
    payment_info = Column(Text, nullable=True)  # Stockage crypté des infos de paiement
    
    # Statistiques et préférences
    login_count = Column(Integer, default=0)
    last_login = Column(DateTime, nullable=True)
    prediction_count = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)
    preferences = Column(Text, nullable=True)  # JSON avec les préférences utilisateur
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relations
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    notification_settings = relationship("NotificationSetting", back_populates="user", uselist=False, cascade="all, delete-orphan")
    devices = relationship("UserDevice", back_populates="user", cascade="all, delete-orphan")
    subscriptions = relationship("UserSubscription", back_populates="user", cascade="all, delete-orphan")
    api_keys = relationship("ApiKey", back_populates="user", cascade="all, delete-orphan")
    
    def __init__(self, email, username, password, first_name=None, last_name=None):
        """
        Initialisation d'un nouvel utilisateur.
        
        Args:
            email (str): Email de l'utilisateur
            username (str): Nom d'utilisateur unique
            password (str): Mot de passe (sera haché)
            first_name (str, optional): Prénom
            last_name (str, optional): Nom de famille
        """
        self.email = email.lower()
        self.username = username
        self.set_password(password)
        self.first_name = first_name
        self.last_name = last_name
        self.verification_token = str(uuid.uuid4())
        
        # Créer automatiquement les paramètres de notification par défaut
        self.notification_settings = NotificationSetting(
            user_id=self.id,
            email_notifications=True,
            push_notifications=True,
            notify_predictions=True,
            notify_odds_changes=True,
            notify_upcoming_races=True,
            min_minutes_before_race=60
        )
    
    def set_password(self, password):
        """
        Définit le mot de passe haché pour l'utilisateur.
        
        Args:
            password (str): Mot de passe en clair
        """
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """
        Vérifie si le mot de passe fourni correspond au mot de passe haché.
        
        Args:
            password (str): Mot de passe en clair à vérifier
            
        Returns:
            bool: True si le mot de passe correspond, False sinon
        """
        return check_password_hash(self.password_hash, password)
    
    def generate_auth_token(self, expiration=86400):
        """
        Génère un token JWT pour l'authentification.
        
        Args:
            expiration (int, optional): Durée de validité du token en secondes (défaut: 24h)
            
        Returns:
            str: Token JWT encodé
        """
        payload = {
            'exp': datetime.utcnow() + timedelta(seconds=expiration),
            'iat': datetime.utcnow(),
            'sub': self.id,
            'role': 'admin' if self.is_admin else 'user',
            'level': self.subscription_level
        }
        
        return jwt.encode(
            payload,
            current_app.config.get('JWT_SECRET_KEY'),
            algorithm='HS256'
        )
    
    def generate_password_reset_token(self, expiration=3600):
        """
        Génère un token pour la réinitialisation du mot de passe.
        
        Args:
            expiration (int, optional): Durée de validité du token en secondes (défaut: 1h)
            
        Returns:
            str: Token de réinitialisation
        """
        token = str(uuid.uuid4())
        # Stocker temporairement le token en base de données ou dans un cache Redis
        from extensions import db
        from models.token import ResetToken
        
        # Supprimer les anciens tokens
        ResetToken.query.filter_by(user_id=self.id).delete()
        
        # Créer un nouveau token
        reset_token = ResetToken(
            user_id=self.id,
            token=token,
            expires_at=datetime.utcnow() + timedelta(seconds=expiration)
        )
        
        db.session.add(reset_token)
        db.session.commit()
        
        return token
    
    def get_full_name(self):
        """
        Renvoie le nom complet de l'utilisateur.
        
        Returns:
            str: Nom complet de l'utilisateur
        """
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        else:
            return self.username
    
    def update_login_stats(self):
        """Met à jour les statistiques de connexion de l'utilisateur."""
        self.login_count += 1
        self.last_login = datetime.utcnow()
        db.session.commit()
    
    def is_subscription_active(self):
        """
        Vérifie si l'abonnement de l'utilisateur est actif.
        
        Returns:
            bool: True si l'abonnement est actif, False sinon
        """
        if self.subscription_level == 'free':
            return True
        
        if not self.subscription_expiry:
            return False
        
        return datetime.utcnow() < self.subscription_expiry
    
    def upgrade_subscription(self, plan_name, duration_months=1):
        """
        Met à niveau l'abonnement de l'utilisateur.
        
        Args:
            plan_name (str): Nom du plan (standard, premium)
            duration_months (int): Durée de l'abonnement en mois
            
        Returns:
            bool: True si la mise à niveau a réussi, False sinon
        """
        try:
            # Vérifier que le plan est valide
            if plan_name not in ['standard', 'premium']:
                return False
            
            # Définir les dates d'abonnement
            now = datetime.utcnow()
            
            # Si l'abonnement est toujours actif, prolonger la durée
            if self.subscription_expiry and self.subscription_expiry > now:
                expiry = self.subscription_expiry + timedelta(days=30 * duration_months)
            else:
                # Sinon, commencer un nouvel abonnement
                self.subscription_start = now
                expiry = now + timedelta(days=30 * duration_months)
            
            self.subscription_level = plan_name
            self.subscription_expiry = expiry
            
            # Créer un enregistrement d'abonnement
            subscription = UserSubscription(
                user_id=self.id,
                plan=plan_name,
                start_date=self.subscription_start,
                end_date=self.subscription_expiry,
                price=self._get_plan_price(plan_name, duration_months),
                status='active'
            )
            
            db.session.add(subscription)
            db.session.commit()
            
            return True
        
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error upgrading subscription: {str(e)}")
            return False
    
    def _get_plan_price(self, plan_name, duration_months):
        """
        Récupère le prix d'un plan en fonction de sa durée.
        
        Args:
            plan_name (str): Nom du plan
            duration_months (int): Durée en mois
            
        Returns:
            float: Prix du plan
        """
        # Tarifs mensuels
        prices = {
            'standard': 9.99,
            'premium': 19.99
        }
        
        # Remises pour abonnements plus longs
        discounts = {
            3: 0.1,  # 10% de remise pour 3 mois
            6: 0.15,  # 15% de remise pour 6 mois
            12: 0.25  # 25% de remise pour 12 mois
        }
        
        base_price = prices.get(plan_name, 0) * duration_months
        
        # Appliquer la remise si applicable
        if duration_months in discounts:
            discount = discounts[duration_months]
            return round(base_price * (1 - discount), 2)
        
        return base_price
    
    def cancel_subscription(self):
        """
        Annule l'abonnement de l'utilisateur.
        
        Returns:
            bool: True si l'annulation a réussi, False sinon
        """
        try:
            # Récupérer l'abonnement actif
            subscription = UserSubscription.query.filter_by(
                user_id=self.id,
                status='active'
            ).order_by(UserSubscription.created_at.desc()).first()
            
            if subscription:
                subscription.status = 'cancelled'
                subscription.cancelled_at = datetime.utcnow()
                
                # L'utilisateur garde son abonnement jusqu'à la fin de la période payée
                db.session.commit()
                return True
            
            return False
        
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error cancelling subscription: {str(e)}")
            return False
    
    def get_preferences(self):
        """
        Récupère les préférences utilisateur.
        
        Returns:
            dict: Préférences utilisateur
        """
        if not self.preferences:
            return {}
        
        try:
            return json.loads(self.preferences)
        except:
            return {}
    
    def update_preferences(self, preferences):
        """
        Met à jour les préférences utilisateur.
        
        Args:
            preferences (dict): Nouvelles préférences
            
        Returns:
            bool: True si la mise à jour a réussi, False sinon
        """
        try:
            # Récupérer les préférences actuelles
            current_prefs = self.get_preferences()
            
            # Mettre à jour avec les nouvelles préférences
            current_prefs.update(preferences)
            
            # Sauvegarder les préférences
            self.preferences = json.dumps(current_prefs)
            db.session.commit()
            
            return True
        
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating preferences: {str(e)}")
            return False
    
    def to_dict(self, with_stats=False):
        """
        Convertit l'utilisateur en dictionnaire.
        
        Args:
            with_stats (bool): Inclure les statistiques détaillées
            
        Returns:
            dict: Données utilisateur
        """
        data = {
            'id': self.id,
            'email': self.email,
            'username': self.username,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'profile_picture': self.profile_picture,
            'bio': self.bio,
            'is_active': self.is_active,
            'is_admin': self.is_admin,
            'is_verified': self.is_verified,
            'subscription': {
                'level': self.subscription_level,
                'active': self.is_subscription_active(),
                'expiry': self.subscription_expiry.isoformat() if self.subscription_expiry else None
            },
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
        
        if with_stats:
            # Ajouter des statistiques détaillées
            from extensions import db
            from sqlalchemy import func, and_
            
            # Récupérer des statistiques sur les prédictions
            stats_query = text("""
            SELECT 
                COUNT(*) as total_predictions,
                COUNT(DISTINCT course_id) as unique_courses,
                MAX(created_at) as last_prediction
            FROM prediction_usage
            WHERE user_id = :user_id
            """)
            
            stats = db.session.execute(stats_query, {"user_id": self.id}).fetchone()
            
            data['stats'] = {
                'prediction_count': stats.total_predictions if stats else 0,
                'unique_courses': stats.unique_courses if stats else 0,
                'last_prediction': stats.last_prediction.isoformat() if stats and stats.last_prediction else None,
                'login_count': self.login_count,
                'success_rate': self.success_rate
            }
            
            # Ajouter les paramètres de notification
            if hasattr(self, 'notification_settings') and self.notification_settings:
                data['notification_settings'] = {
                    'email_notifications': self.notification_settings.email_notifications,
                    'push_notifications': self.notification_settings.push_notifications,
                    'notify_predictions': self.notification_settings.notify_predictions,
                    'notify_odds_changes': self.notification_settings.notify_odds_changes,
                    'notify_upcoming_races': self.notification_settings.notify_upcoming_races,
                    'min_minutes_before_race': self.notification_settings.min_minutes_before_race
                }
            
            # Ajouter les préférences utilisateur
            data['preferences'] = self.get_preferences()
        
        return data
    
    # def __repr__(self):
    #     """Représentation textuelle de l'utilisateur."""
    #     return f"<User {self.id}: {self.username}>"

    # """Modèle pour les tokens de réinitialisation de mot de passe"""
    # __tablename__ = 'reset_tokens'
    
    # id = Column(Integer, primary_key=True)
    # user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    # token = Column(String(100), nullable=False, unique=True)
    # created_at = Column(DateTime, default=func.now())
    # expires_at = Column(DateTime, nullable=False)
    # used = Column(Boolean, default=False)
    
    @staticmethod
    def verify_token(token):
        """
        Vérifie si un token de réinitialisation est valide.
        
        Args:
            token (str): Token à vérifier
            
        Returns:
            User or None: L'utilisateur associé au token ou None si invalide
        """
        reset_token = ResetToken.query.filter_by(
            token=token,
            used=False
        ).first()
        
        if not reset_token or reset_token.expires_at < datetime.utcnow():
            return None
        
        return User.query.get(reset_token.user_id)
    
    @staticmethod
    def use_token(token):
        """
        Marque un token comme utilisé.
        
        Args:
            token (str): Token à marquer
            
        Returns:
            bool: True si le token a été marqué comme utilisé, False sinon
        """
        try:
            reset_token = ResetToken.query.filter_by(token=token).first()
            
            if reset_token:
                reset_token.used = True
                db.session.commit()
                return True
            
            return False
        
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error using token: {str(e)}")
            return False