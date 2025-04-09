# token.py
# api/models/token.py
from datetime import datetime, timedelta
import uuid
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from api import db

class ResetToken(db.Model):
    """Modèle pour les tokens de réinitialisation de mot de passe"""
    __tablename__ = 'reset_tokens'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    token = Column(String(100), nullable=False, unique=True)
    created_at = Column(DateTime, default=func.now())
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)
    
    # Relation avec l'utilisateur (pas de backref pour éviter les cycles)
    user = relationship("User", foreign_keys=[user_id])
    
    def __init__(self, user_id, token=None, expires_at=None):
        """
        Initialisation d'un nouveau token de réinitialisation.
        
        Args:
            user_id (int): ID de l'utilisateur
            token (str, optional): Token aléatoire (généré si non fourni)
            expires_at (datetime, optional): Date d'expiration (1h par défaut)
        """
        self.user_id = user_id
        self.token = token or str(uuid.uuid4())
        self.expires_at = expires_at or datetime.utcnow() + timedelta(hours=1)
    
    def is_valid(self):
        """
        Vérifie si le token est valide (non utilisé et non expiré).
        
        Returns:
            bool: True si le token est valide, False sinon
        """
        return not self.used and self.expires_at > datetime.utcnow()
    
    def use(self):
        """
        Marque le token comme utilisé.
        
        Returns:
            bool: True si le token a été marqué comme utilisé, False sinon
        """
        if not self.is_valid():
            return False
        
        self.used = True
        db.session.commit()
        return True
    
    @staticmethod
    def verify_token(token_string):
        """
        Vérifie si un token de réinitialisation est valide.
        
        Args:
            token_string (str): Token à vérifier
            
        Returns:
            User or None: L'utilisateur associé au token ou None si invalide
        """
        from models.user import User  # Import here to avoid circular imports
        
        reset_token = ResetToken.query.filter_by(
            token=token_string,
            used=False
        ).first()
        
        if not reset_token or not reset_token.is_valid():
            return None
        
        return User.query.get(reset_token.user_id)
    
    @staticmethod
    def generate_for_user(user_id, expiration_hours=1):
        """
        Génère un nouveau token de réinitialisation pour un utilisateur.
        
        Args:
            user_id (int): ID de l'utilisateur
            expiration_hours (int, optional): Durée de validité en heures
            
        Returns:
            str: Token généré
        """
        # Supprimer les anciens tokens non utilisés pour cet utilisateur
        ResetToken.query.filter_by(
            user_id=user_id,
            used=False
        ).delete()
        
        # Créer un nouveau token
        token = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(hours=expiration_hours)
        
        reset_token = ResetToken(
            user_id=user_id,
            token=token,
            expires_at=expires_at
        )
        
        db.session.add(reset_token)
        db.session.commit()
        
        return token
    
    def __repr__(self):
        """Représentation textuelle du token."""
        valid = "Valid" if self.is_valid() else "Invalid"
        return f"<ResetToken {self.id}: {valid} | User: {self.user_id}>"


class VerificationToken(db.Model):
    """Modèle pour les tokens de vérification d'email"""
    __tablename__ = 'verification_tokens'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    token = Column(String(100), nullable=False, unique=True)
    created_at = Column(DateTime, default=func.now())
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)
    
    # Relation avec l'utilisateur (pas de backref pour éviter les cycles)
    user = relationship("User", foreign_keys=[user_id])
    
    def __init__(self, user_id, token=None, expires_at=None):
        """
        Initialisation d'un nouveau token de vérification.
        
        Args:
            user_id (int): ID de l'utilisateur
            token (str, optional): Token aléatoire (généré si non fourni)
            expires_at (datetime, optional): Date d'expiration (7 jours par défaut)
        """
        self.user_id = user_id
        self.token = token or str(uuid.uuid4())
        self.expires_at = expires_at or datetime.utcnow() + timedelta(days=7)
    
    def is_valid(self):
        """
        Vérifie si le token est valide (non utilisé et non expiré).
        
        Returns:
            bool: True si le token est valide, False sinon
        """
        return not self.used and self.expires_at > datetime.utcnow()
    
    def use(self):
        """
        Marque le token comme utilisé et vérifie l'utilisateur.
        
        Returns:
            bool: True si le token a été marqué comme utilisé, False sinon
        """
        if not self.is_valid():
            return False
        
        try:
            from models.user import User  # Import here to avoid circular imports
            
            user = User.query.get(self.user_id)
            if user:
                user.is_verified = True
                self.used = True
                db.session.commit()
                return True
            return False
        except:
            db.session.rollback()
            return False
    
    @staticmethod
    def verify_token(token_string):
        """
        Vérifie et utilise un token de vérification.
        
        Args:
            token_string (str): Token à vérifier
            
        Returns:
            User or None: L'utilisateur associé au token ou None si invalide
        """
        from models.user import User  # Import here to avoid circular imports
        
        verification_token = VerificationToken.query.filter_by(
            token=token_string,
            used=False
        ).first()
        
        if not verification_token or not verification_token.is_valid():
            return None
        
        # Marquer comme utilisé et vérifier l'utilisateur
        if verification_token.use():
            return User.query.get(verification_token.user_id)
        
        return None
    
    @staticmethod
    def generate_for_user(user_id, expiration_days=7):
        """
        Génère un nouveau token de vérification pour un utilisateur.
        
        Args:
            user_id (int): ID de l'utilisateur
            expiration_days (int, optional): Durée de validité en jours
            
        Returns:
            str: Token généré
        """
        # Supprimer les anciens tokens non utilisés pour cet utilisateur
        VerificationToken.query.filter_by(
            user_id=user_id,
            used=False
        ).delete()
        
        # Créer un nouveau token
        token = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(days=expiration_days)
        
        verification_token = VerificationToken(
            user_id=user_id,
            token=token,
            expires_at=expires_at
        )
        
        db.session.add(verification_token)
        db.session.commit()
        
        return token
    
    def __repr__(self):
        """Représentation textuelle du token."""
        valid = "Valid" if self.is_valid() else "Invalid"
        return f"<VerificationToken {self.id}: {valid} | User: {self.user_id}>"


class RefreshToken(db.Model):
    """Modèle pour les tokens de rafraîchissement JWT"""
    __tablename__ = 'refresh_tokens'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    token = Column(String(255), nullable=False, unique=True)
    expires_at = Column(DateTime, nullable=False)
    revoked = Column(Boolean, default=False)
    issued_at = Column(DateTime, default=func.now())
    device_info = Column(String(255), nullable=True)  # Info sur l'appareil utilisé
    
    # Relation avec l'utilisateur (pas de backref pour éviter les cycles)
    user = relationship("User", foreign_keys=[user_id])
    
    def __init__(self, user_id, token, expires_at, device_info=None):
        """
        Initialisation d'un nouveau token de rafraîchissement.
        
        Args:
            user_id (int): ID de l'utilisateur
            token (str): Token JWT
            expires_at (datetime): Date d'expiration
            device_info (str, optional): Informations sur l'appareil
        """
        self.user_id = user_id
        self.token = token
        self.expires_at = expires_at
        self.device_info = device_info
    
    def is_valid(self):
        """
        Vérifie si le token est valide (non révoqué et non expiré).
        
        Returns:
            bool: True si le token est valide, False sinon
        """
        return not self.revoked and self.expires_at > datetime.utcnow()
    
    def revoke(self):
        """
        Révoque le token.
        
        Returns:
            bool: True si le token a été révoqué, False sinon
        """
        try:
            self.revoked = True
            db.session.commit()
            return True
        except:
            db.session.rollback()
            return False
    
    @staticmethod
    def get_by_token(token_string):
        """
        Récupère un token de rafraîchissement par sa valeur.
        
        Args:
            token_string (str): Token à rechercher
            
        Returns:
            RefreshToken or None: Le token ou None si non trouvé
        """
        return RefreshToken.query.filter_by(token=token_string).first()
    
    @staticmethod
    def revoke_all_for_user(user_id):
        """
        Révoque tous les tokens de rafraîchissement d'un utilisateur.
        
        Args:
            user_id (int): ID de l'utilisateur
            
        Returns:
            int: Nombre de tokens révoqués
        """
        try:
            tokens = RefreshToken.query.filter_by(user_id=user_id, revoked=False).all()
            count = 0
            
            for token in tokens:
                token.revoked = True
                count += 1
            
            db.session.commit()
            return count
        except:
            db.session.rollback()
            return 0
    
    def __repr__(self):
        """Représentation textuelle du token."""
        status = "Valid" if self.is_valid() else "Invalid"
        return f"<RefreshToken {self.id}: {status} | User: {self.user_id}>"