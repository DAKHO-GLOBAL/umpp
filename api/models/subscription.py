# subscription.py
# subscription.py
# api/models/subscription.py
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from extensions import db

class UserSubscription(db.Model):
    """Modèle pour les abonnements des utilisateurs"""
    __tablename__ = 'user_subscriptions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    plan = Column(String(20), nullable=False)  # free, standard, premium
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=True)
    price = Column(Float, nullable=True)
    payment_method = Column(String(50), nullable=True)
    payment_reference = Column(String(100), nullable=True)
    status = Column(String(20), default='active')  # active, cancelled, expired
    auto_renew = Column(Boolean, default=False)
    cancelled_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relations
    user = relationship("User", back_populates="subscriptions")
    
    def __repr__(self):
        return f"<UserSubscription {self.id}: User {self.user_id}, Plan {self.plan}, Status {self.status}>"
    
    def is_active(self):
        """Vérifie si l'abonnement est actif"""
        return self.status == 'active' and (self.end_date is None or self.end_date > datetime.utcnow())
    
    def to_dict(self):
        """Convertit l'objet en dictionnaire"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'plan': self.plan,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'price': self.price,
            'payment_method': self.payment_method,
            'status': self.status,
            'auto_renew': self.auto_renew,
            'is_active': self.is_active(),
            'cancelled_at': self.cancelled_at.isoformat() if self.cancelled_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class SubscriptionPlan(db.Model):
    """Modèle pour les plans d'abonnement disponibles"""
    __tablename__ = 'subscription_plans'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)  # free, standard, premium
    display_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    price_monthly = Column(Float, nullable=False)
    price_quarterly = Column(Float, nullable=True)
    price_yearly = Column(Float, nullable=True)
    features = Column(JSON, nullable=False)  # liste des fonctionnalités incluses
    limits = Column(JSON, nullable=False)  # limites (prédictions par jour, etc.)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<SubscriptionPlan {self.id}: {self.name}, Price {self.price_monthly}>"
    
    def to_dict(self):
        """Convertit l'objet en dictionnaire"""
        return {
            'id': self.id,
            'name': self.name,
            'display_name': self.display_name,
            'description': self.description,
            'price_monthly': self.price_monthly,
            'price_quarterly': self.price_quarterly,
            'price_yearly': self.price_yearly,
            'features': self.features,
            'limits': self.limits,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class PaymentTransaction(db.Model):
    """Modèle pour les transactions de paiement"""
    __tablename__ = 'payment_transactions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    subscription_id = Column(Integer, ForeignKey('user_subscriptions.id'), nullable=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default='EUR')
    payment_method = Column(String(50), nullable=False)
    transaction_reference = Column(String(100), nullable=True)
    status = Column(String(20), default='pending')  # pending, completed, failed, refunded
    payment_date = Column(DateTime, nullable=True)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relations
    user = relationship("User")
    subscription = relationship("UserSubscription")
    
    def __repr__(self):
        return f"<PaymentTransaction {self.id}: User {self.user_id}, Amount {self.amount}, Status {self.status}>"
    
    def to_dict(self):
        """Convertit l'objet en dictionnaire"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'subscription_id': self.subscription_id,
            'amount': self.amount,
            'currency': self.currency,
            'payment_method': self.payment_method,
            'transaction_reference': self.transaction_reference,
            'status': self.status,
            'payment_date': self.payment_date.isoformat() if self.payment_date else None,
            'details': self.details,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class PromotionCode(db.Model):
    """Modèle pour les codes promotionnels"""
    __tablename__ = 'promotion_codes'
    
    id = Column(Integer, primary_key=True)
    code = Column(String(20), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    discount_type = Column(String(10), nullable=False)  # percentage, fixed
    discount_value = Column(Float, nullable=False)
    valid_from = Column(DateTime, nullable=False)
    valid_until = Column(DateTime, nullable=True)
    max_uses = Column(Integer, nullable=True)
    used_count = Column(Integer, default=0)
    applies_to_plan = Column(String(20), nullable=True)  # applicable à un plan spécifique
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<PromotionCode {self.id}: {self.code}, Discount {self.discount_type} {self.discount_value}>"
    
    def is_valid(self):
        """Vérifie si le code promo est valide"""
        now = datetime.utcnow()
        is_time_valid = self.valid_from <= now and (self.valid_until is None or self.valid_until >= now)
        is_usage_valid = self.max_uses is None or self.used_count < self.max_uses
        return self.is_active and is_time_valid and is_usage_valid
    
    def to_dict(self):
        """Convertit l'objet en dictionnaire"""
        return {
            'id': self.id,
            'code': self.code,
            'description': self.description,
            'discount_type': self.discount_type,
            'discount_value': self.discount_value,
            'valid_from': self.valid_from.isoformat() if self.valid_from else None,
            'valid_until': self.valid_until.isoformat() if self.valid_until else None,
            'max_uses': self.max_uses,
            'used_count': self.used_count,
            'applies_to_plan': self.applies_to_plan,
            'is_active': self.is_active,
            'is_valid': self.is_valid(),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }