# notification.py
# api/models/notification.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from extensions import db
from datetime import datetime

class Notification(db.Model):
    """Modèle pour les notifications utilisateur"""
    __tablename__ = 'notifications'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    notification_type = Column(String(50), nullable=False)  # prediction, odds_change, upcoming_course, system, etc.
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    data = Column(JSON, nullable=True)  # Données JSON supplémentaires spécifiques au type
    read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relations
    user = relationship("User", back_populates="notifications")
    
    def __repr__(self):
        return f"<Notification {self.id} | Type: {self.notification_type} | User: {self.user_id}>"


class NotificationSetting(db.Model):
    """Modèle pour les paramètres de notification utilisateur"""
    __tablename__ = 'notification_settings'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True)
    email_notifications = Column(Boolean, default=True)
    push_notifications = Column(Boolean, default=True)
    notify_predictions = Column(Boolean, default=True)
    notify_odds_changes = Column(Boolean, default=True)
    notify_upcoming_races = Column(Boolean, default=True)
    min_minutes_before_race = Column(Integer, default=60)  # Minimum minutes avant une course pour notifier
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relations
    user = relationship("User", back_populates="notification_settings")
    
    def __repr__(self):
        return f"<NotificationSetting {self.id} | User: {self.user_id}>"


class UserDevice(db.Model):
    """Modèle pour les appareils des utilisateurs pour les notifications push"""
    __tablename__ = 'user_devices'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    device_token = Column(String(512), nullable=False, unique=True)
    device_type = Column(String(50), nullable=False)  # android, ios, web, desktop, etc.
    device_name = Column(String(100), nullable=False)
    notification_enabled = Column(Boolean, default=True)
    last_used_at = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())
    
    # Relations
    user = relationship("User", back_populates="devices")
    
    def __repr__(self):
        return f"<UserDevice {self.id} | User: {self.user_id} | Type: {self.device_type}>"