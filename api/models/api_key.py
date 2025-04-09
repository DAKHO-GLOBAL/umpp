# api_key.py
# api/models/api_key.py
import uuid
from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from api import db
from models.user import User

class ApiKey(db.Model):
    """Modèle pour les clés API utilisées pour l'authentification des services externes"""
    __tablename__ = 'api_keys'
    
    id = Column(Integer, primary_key=True)
    key = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    is_active = Column(Boolean, default=True)
    expiry_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    last_used_at = Column(DateTime, nullable=True)
    usage_count = Column(Integer, default=0)
    
    # Relations
    user = relationship('User', back_populates='api_keys')
    
    def __init__(self, name, user_id, description=None, expiry_days=None):
        """
        Initialise une nouvelle clé 
        
        Args:
            name (str): Nom de la clé API pour identification
            user_id (int): ID de l'utilisateur propriétaire
            description (str, optional): Description de l'utilisation
            expiry_days (int, optional): Nombre de jours avant expiration
        """
        self.key = str(uuid.uuid4()).replace('-', '')
        self.name = name
        self.user_id = user_id
        self.description = description
        
        if expiry_days:
            self.expiry_date = datetime.now() + timedelta(days=expiry_days)
    
    def is_expired(self):
        """
        Vérifie si la clé API a expiré.
        
        Returns:
            bool: True si la clé a expiré, False sinon
        """
        if not self.expiry_date:
            return False
        
        return datetime.now() > self.expiry_date
    
    def update_last_used(self):
        """Met à jour la date de dernière utilisation et incrémente le compteur d'utilisation"""
        self.last_used_at = datetime.now()
        self.usage_count += 1
        db.session.commit()
    
    def deactivate(self):
        """Désactive la clé API"""
        self.is_active = False
        db.session.commit()
    
    def reactivate(self):
        """Réactive la clé API"""
        self.is_active = True
        db.session.commit()
    
    def extend_expiry(self, days):
        """
        Prolonge la date d'expiration de la clé 
        
        Args:
            days (int): Nombre de jours à ajouter
        """
        if self.expiry_date:
            self.expiry_date += timedelta(days=days)
        else:
            self.expiry_date = datetime.now() + timedelta(days=days)
        
        db.session.commit()
    
    @classmethod
    def generate_for_user(cls, user_id, name, description=None, expiry_days=None):
        """
        Génère une nouvelle clé API pour un utilisateur.
        
        Args:
            user_id (int): ID de l'utilisateur
            name (str): Nom de la clé
            description (str, optional): Description de la clé
            expiry_days (int, optional): Nombre de jours avant expiration
            
        Returns:
            ApiKey: L'instance de clé API créée
        """
        api_key = cls(name=name, user_id=user_id, description=description, expiry_days=expiry_days)
        db.session.add(api_key)
        db.session.commit()
        return api_key
    
    def __repr__(self):
        return f"<ApiKey {self.id} | Name: {self.name} | User: {self.user_id}>"