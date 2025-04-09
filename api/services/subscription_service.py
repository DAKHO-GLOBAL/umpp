# subscription_service.py
# subscription_service.py
# api/services/subscription_service.py
import logging
from datetime import datetime, timedelta
from flask import current_app
from sqlalchemy import func, and_, or_, text

from api import db
from models.user import User
from models.subscription import UserSubscription, SubscriptionPlan, PaymentTransaction, PromotionCode
from utils.email_sender import send_email

class SubscriptionService:
    """Service pour gérer les abonnements des utilisateurs"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def get_subscription_plans(self, include_inactive=False):
        """
        Récupère tous les plans d'abonnement disponibles.
        
        Args:
            include_inactive (bool): Inclure les plans inactifs
            
        Returns:
            list: Liste des plans d'abonnement
        """
        try:
            query = SubscriptionPlan.query
            
            if not include_inactive:
                query = query.filter_by(is_active=True)
            
            plans = query.order_by(SubscriptionPlan.price_monthly).all()
            
            return [plan.to_dict() for plan in plans]
            
        except Exception as e:
            self.logger.error(f"Error retrieving subscription plans: {str(e)}")
            return []
    
    def get_plan_by_name(self, plan_name):
        """
        Récupère un plan d'abonnement par son nom.
        
        Args:
            plan_name (str): Nom du plan
            
        Returns:
            dict or None: Plan d'abonnement ou None si non trouvé
        """
        try:
            plan = SubscriptionPlan.query.filter_by(name=plan_name, is_active=True).first()
            
            if not plan:
                return None
            
            return plan.to_dict()
            
        except Exception as e:
            self.logger.error(f"Error retrieving subscription plan {plan_name}: {str(e)}")
            return None
    
    def get_user_subscription(self, user_id):
        """
        Récupère l'abonnement actif d'un utilisateur.
        
        Args:
            user_id (int): ID de l'utilisateur
            
        Returns:
            dict or None: Abonnement de l'utilisateur ou None si non trouvé
        """
        try:
            # Récupérer l'abonnement actif le plus récent
            subscription = UserSubscription.query.filter(
                UserSubscription.user_id == user_id,
                UserSubscription.status == 'active',
                or_(
                    UserSubscription.end_date.is_(None),
                    UserSubscription.end_date >= datetime.utcnow()
                )
            ).order_by(UserSubscription.created_at.desc()).first()
            
            if not subscription:
                return None
            
            return subscription.to_dict()
            
        except Exception as e:
            self.logger.error(f"Error retrieving user subscription for user {user_id}: {str(e)}")
            return None
    
    def get_subscription_history(self, user_id):
        """
        Récupère l'historique des abonnements d'un utilisateur.
        
        Args:
            user_id (int): ID de l'utilisateur
            
        Returns:
            list: Liste des abonnements de l'utilisateur
        """
        try:
            subscriptions = UserSubscription.query.filter_by(
                user_id=user_id
            ).order_by(UserSubscription.created_at.desc()).all()
            
            return [subscription.to_dict() for subscription in subscriptions]
            
        except Exception as e:
            self.logger.error(f"Error retrieving subscription history for user {user_id}: {str(e)}")
            return []
    
    def create_subscription(self, user_id, plan_name, duration_months=1, payment_method=None, 
                           promotion_code=None, payment_reference=None):
        """
        Crée un nouvel abonnement pour un utilisateur.
        
        Args:
            user_id (int): ID de l'utilisateur
            plan_name (str): Nom du plan d'abonnement
            duration_months (int): Durée de l'abonnement en mois
            payment_method (str): Méthode de paiement utilisée
            promotion_code (str): Code promotionnel utilisé
            payment_reference (str): Référence du paiement
            
        Returns:
            dict or None: Nouvel abonnement ou None en cas d'erreur
        """
        try:
            # Récupérer l'utilisateur
            user = User.query.get(user_id)
            
            if not user:
                self.logger.error(f"User {user_id} not found")
                return None
            
            # Récupérer le plan d'abonnement
            plan = SubscriptionPlan.query.filter_by(name=plan_name, is_active=True).first()
            
            if not plan:
                self.logger.error(f"Subscription plan {plan_name} not found or inactive")
                return None
            
            # Calculer le prix selon la durée
            if duration_months >= 12 and plan.price_yearly:
                price = plan.price_yearly
            elif duration_months >= 3 and plan.price_quarterly:
                price = plan.price_quarterly
            else:
                price = plan.price_monthly * duration_months
            
            # Appliquer le code promo si fourni
            discount_applied = 0
            promo_code_used = None
            
            if promotion_code:
                promo = PromotionCode.query.filter_by(code=promotion_code, is_active=True).first()
                
                if promo and promo.is_valid() and (promo.applies_to_plan is None or promo.applies_to_plan == plan_name):
                    if promo.discount_type == 'percentage':
                        discount_applied = price * (promo.discount_value / 100)
                    else:  # fixed
                        discount_applied = promo.discount_value
                    
                    # Ne pas dépasser le prix total
                    discount_applied = min(discount_applied, price)
                    price -= discount_applied
                    
                    # Incrémenter le compteur d'utilisation
                    promo.used_count += 1
                    promo_code_used = promo.code
            
            # Définir les dates de début et de fin
            start_date = datetime.utcnow()
            end_date = start_date + timedelta(days=30 * duration_months)
            
            # Vérifier si l'utilisateur a déjà un abonnement actif
            current_subscription = UserSubscription.query.filter(
                UserSubscription.user_id == user_id,
                UserSubscription.status == 'active',
                or_(
                    UserSubscription.end_date.is_(None),
                    UserSubscription.end_date >= datetime.utcnow()
                )
            ).order_by(UserSubscription.created_at.desc()).first()
            
            # Si un abonnement actif existe, le prolonger
            if current_subscription and current_subscription.end_date and current_subscription.end_date > start_date:
                end_date = current_subscription.end_date + timedelta(days=30 * duration_months)
                
                # Mettre à jour le statut de l'ancien abonnement
                if current_subscription.plan != plan_name:
                    current_subscription.status = 'cancelled'
                    db.session.flush()
            
            # Créer le nouvel abonnement
            subscription = UserSubscription(
                user_id=user_id,
                plan=plan_name,
                start_date=start_date,
                end_date=end_date,
                price=price,
                payment_method=payment_method,
                payment_reference=payment_reference,
                status='active',
                auto_renew=False
            )
            
            db.session.add(subscription)
            
            # Créer la transaction de paiement si nécessaire
            if payment_method and price > 0:
                transaction = PaymentTransaction(
                    user_id=user_id,
                    subscription_id=subscription.id,
                    amount=price,
                    currency='EUR',
                    payment_method=payment_method,
                    transaction_reference=payment_reference,
                    status='completed',
                    payment_date=datetime.utcnow(),
                    details={
                        'plan': plan_name,
                        'duration_months': duration_months,
                        'original_price': plan.price_monthly * duration_months,
                        'discount_applied': discount_applied,
                        'promotion_code': promo_code_used
                    }
                )
                
                db.session.add(transaction)
            
            # Mettre à jour les informations d'abonnement de l'utilisateur
            user.subscription_level = plan_name
            user.subscription_start = start_date
            user.subscription_expiry = end_date
            
            db.session.commit()
            
            # Envoyer un email de confirmation
            self._send_subscription_confirmation_email(user, subscription)
            
            return subscription.to_dict()
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error creating subscription for user {user_id}: {str(e)}")
            return None
    
    def cancel_subscription(self, user_id, immediate=False):
        """
        Annule l'abonnement d'un utilisateur.
        
        Args:
            user_id (int): ID de l'utilisateur
            immediate (bool): Annulation immédiate ou à la fin de la période
            
        Returns:
            bool: True si l'annulation a réussi, False sinon
        """
        try:
            # Récupérer l'abonnement actif
            subscription = UserSubscription.query.filter(
                UserSubscription.user_id == user_id,
                UserSubscription.status == 'active'
            ).order_by(UserSubscription.created_at.desc()).first()
            
            if not subscription:
                self.logger.warning(f"No active subscription found for user {user_id}")
                return False
            
            # Récupérer l'utilisateur
            user = User.query.get(user_id)
            
            if not user:
                self.logger.error(f"User {user_id} not found")
                return False
            
            # Annuler l'abonnement
            subscription.status = 'cancelled'
            subscription.cancelled_at = datetime.utcnow()
            
            if immediate:
                # Passer immédiatement au niveau gratuit
                user.subscription_level = 'free'
                
                # Mettre à jour la date d'expiration
                subscription.end_date = datetime.utcnow()
                user.subscription_expiry = datetime.utcnow()
            
            db.session.commit()
            
            # Envoyer un email de confirmation d'annulation
            self._send_subscription_cancellation_email(user, subscription, immediate)
            
            return True
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error cancelling subscription for user {user_id}: {str(e)}")
            return False
    
    def extend_subscription(self, user_id, duration_months=1):
        """
        Prolonge l'abonnement d'un utilisateur.
        
        Args:
            user_id (int): ID de l'utilisateur
            duration_months (int): Durée de prolongation en mois
            
        Returns:
            dict or None: Abonnement mis à jour ou None en cas d'erreur
        """
        try:
            # Récupérer l'utilisateur
            user = User.query.get(user_id)
            
            if not user:
                self.logger.error(f"User {user_id} not found")
                return None
            
            # Récupérer l'abonnement actif
            subscription = UserSubscription.query.filter(
                UserSubscription.user_id == user_id,
                UserSubscription.status == 'active'
            ).order_by(UserSubscription.created_at.desc()).first()
            
            if not subscription:
                self.logger.warning(f"No active subscription found for user {user_id}")
                return None
            
            # Calculer la nouvelle date d'expiration
            if subscription.end_date and subscription.end_date > datetime.utcnow():
                new_end_date = subscription.end_date + timedelta(days=30 * duration_months)
            else:
                new_end_date = datetime.utcnow() + timedelta(days=30 * duration_months)
            
            # Mettre à jour l'abonnement
            subscription.end_date = new_end_date
            user.subscription_expiry = new_end_date
            
            db.session.commit()
            
            # Envoyer un email de confirmation
            self._send_subscription_extension_email(user, subscription, duration_months)
            
            return subscription.to_dict()
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error extending subscription for user {user_id}: {str(e)}")
            return None
    
    def change_subscription_plan(self, user_id, new_plan_name, payment_method=None, promotion_code=None, payment_reference=None):
        """
        Change le plan d'abonnement d'un utilisateur.
        
        Args:
            user_id (int): ID de l'utilisateur
            new_plan_name (str): Nom du nouveau plan
            payment_method (str): Méthode de paiement utilisée
            promotion_code (str): Code promotionnel utilisé
            payment_reference (str): Référence du paiement
            
        Returns:
            dict or None: Nouvel abonnement ou None en cas d'erreur
        """
        try:
            # Récupérer l'utilisateur
            user = User.query.get(user_id)
            
            if not user:
                self.logger.error(f"User {user_id} not found")
                return None
            
            # Récupérer le nouveau plan
            new_plan = SubscriptionPlan.query.filter_by(name=new_plan_name, is_active=True).first()
            
            if not new_plan:
                self.logger.error(f"Subscription plan {new_plan_name} not found or inactive")
                return None
            
            # Récupérer l'abonnement actif
            current_subscription = UserSubscription.query.filter(
                UserSubscription.user_id == user_id,
                UserSubscription.status == 'active'
            ).order_by(UserSubscription.created_at.desc()).first()
            
            # Calculer le temps restant sur l'abonnement actuel
            remaining_days = 0
            if current_subscription and current_subscription.end_date and current_subscription.end_date > datetime.utcnow():
                remaining_days = (current_subscription.end_date - datetime.utcnow()).days
            
            # Calculer la durée du nouvel abonnement (au moins 1 mois)
            duration_months = max(1, remaining_days // 30)
            
            # Calculer le prix selon la durée
            if duration_months >= 12 and new_plan.price_yearly:
                price = new_plan.price_yearly
            elif duration_months >= 3 and new_plan.price_quarterly:
                price = new_plan.price_quarterly
            else:
                price = new_plan.price_monthly * duration_months
            
            # Appliquer le code promo si fourni
            discount_applied = 0
            promo_code_used = None
            
            if promotion_code:
                promo = PromotionCode.query.filter_by(code=promotion_code, is_active=True).first()
                
                if promo and promo.is_valid() and (promo.applies_to_plan is None or promo.applies_to_plan == new_plan_name):
                    if promo.discount_type == 'percentage':
                        discount_applied = price * (promo.discount_value / 100)
                    else:  # fixed
                        discount_applied = promo.discount_value
                    
                    # Ne pas dépasser le prix total
                    discount_applied = min(discount_applied, price)
                    price -= discount_applied
                    
                    # Incrémenter le compteur d'utilisation
                    promo.used_count += 1
                    promo_code_used = promo.code
            
            # Annuler l'abonnement actuel
            if current_subscription:
                current_subscription.status = 'cancelled'
                current_subscription.cancelled_at = datetime.utcnow()
            
            # Créer le nouvel abonnement
            start_date = datetime.utcnow()
            end_date = start_date + timedelta(days=30 * duration_months)
            
            subscription = UserSubscription(
                user_id=user_id,
                plan=new_plan_name,
                start_date=start_date,
                end_date=end_date,
                price=price,
                payment_method=payment_method,
                payment_reference=payment_reference,
                status='active',
                auto_renew=False
            )
            
            db.session.add(subscription)
            
            # Créer la transaction de paiement si nécessaire
            if payment_method and price > 0:
                transaction = PaymentTransaction(
                    user_id=user_id,
                    subscription_id=subscription.id,
                    amount=price,
                    currency='EUR',
                    payment_method=payment_method,
                    transaction_reference=payment_reference,
                    status='completed',
                    payment_date=datetime.utcnow(),
                    details={
                        'plan': new_plan_name,
                        'duration_months': duration_months,
                        'original_price': new_plan.price_monthly * duration_months,
                        'discount_applied': discount_applied,
                        'promotion_code': promo_code_used,
                        'previous_plan': user.subscription_level,
                        'remaining_days': remaining_days
                    }
                )
                
                db.session.add(transaction)
            
            # Mettre à jour les informations d'abonnement de l'utilisateur
            user.subscription_level = new_plan_name
            user.subscription_start = start_date
            user.subscription_expiry = end_date
            
            db.session.commit()
            
            # Envoyer un email de confirmation
            self._send_subscription_change_email(user, subscription, current_subscription)
            
            return subscription.to_dict()
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error changing subscription plan for user {user_id}: {str(e)}")
            return None
    
    def validate_promotion_code(self, code, plan_name=None):
        """
        Valide un code promotionnel.
        
        Args:
            code (str): Code promotionnel
            plan_name (str): Nom du plan d'abonnement (optionnel)
            
        Returns:
            dict or None: Informations sur le code promo ou None si invalide
        """
        try:
            promo = PromotionCode.query.filter_by(code=code, is_active=True).first()
            
            if not promo:
                return None
            
            # Vérifier si le code est valide
            if not promo.is_valid():
                return None
            
            # Vérifier si le code s'applique au plan spécifié
            if plan_name and promo.applies_to_plan and promo.applies_to_plan != plan_name:
                return None
            
            return {
                'code': promo.code,
                'description': promo.description,
                'discount_type': promo.discount_type,
                'discount_value': promo.discount_value,
                'valid_until': promo.valid_until.isoformat() if promo.valid_until else None,
                'applies_to_plan': promo.applies_to_plan
            }
            
        except Exception as e:
            self.logger.error(f"Error validating promotion code {code}: {str(e)}")
            return None
    
    def get_payment_transactions(self, user_id):
        """
        Récupère les transactions de paiement d'un utilisateur.
        
        Args:
            user_id (int): ID de l'utilisateur
            
        Returns:
            list: Liste des transactions de paiement
        """
        try:
            transactions = PaymentTransaction.query.filter_by(
                user_id=user_id
            ).order_by(PaymentTransaction.created_at.desc()).all()
            
            return [transaction.to_dict() for transaction in transactions]
            
        except Exception as e:
            self.logger.error(f"Error retrieving payment transactions for user {user_id}: {str(e)}")
            return []
    
    def _send_subscription_confirmation_email(self, user, subscription):
        """
        Envoie un email de confirmation d'abonnement.
        
        Args:
            user (User): Utilisateur
            subscription (UserSubscription): Abonnement
            
        Returns:
            bool: True si l'email a été envoyé, False sinon
        """
        try:
            # Récupérer le plan d'abonnement
            plan = SubscriptionPlan.query.filter_by(name=subscription.plan).first()
            
            subject = f"Confirmation de votre abonnement {subscription.plan}"
            
            data = {
                'user_name': user.get_full_name(),
                'subscription_plan': subscription.plan.capitalize(),
                'subscription_price': subscription.price,
                'start_date': subscription.start_date.strftime('%d/%m/%Y'),
                'end_date': subscription.end_date.strftime('%d/%m/%Y') if subscription.end_date else 'Illimitée',
                'plan_features': plan.features if plan else [],
                'app_name': current_app.config.get('APP_NAME', 'PMU Prediction'),
                'support_email': current_app.config.get('SUPPORT_EMAIL', 'support@example.com')
            }
            
            return send_email(
                recipient=user.email,
                subject=subject,
                body="",
                template_name='subscription_confirmation',
                data=data,
                html=True
            )
            
        except Exception as e:
            self.logger.error(f"Error sending subscription confirmation email: {str(e)}")
            return False
    
    def _send_subscription_cancellation_email(self, user, subscription, immediate):
        """
        Envoie un email de confirmation d'annulation d'abonnement.
        
        Args:
            user (User): Utilisateur
            subscription (UserSubscription): Abonnement
            immediate (bool): Annulation immédiate ou à la fin de la période
            
        Returns:
            bool: True si l'email a été envoyé, False sinon
        """
        try:
            subject = f"Confirmation d'annulation de votre abonnement {subscription.plan}"
            
            end_date = datetime.utcnow() if immediate else subscription.end_date
            
            data = {
                'user_name': user.get_full_name(),
                'subscription_plan': subscription.plan.capitalize(),
                'end_date': end_date.strftime('%d/%m/%Y') if end_date else 'Illimitée',
                'immediate': immediate,
                'app_name': current_app.config.get('APP_NAME', 'PMU Prediction'),
                'support_email': current_app.config.get('SUPPORT_EMAIL', 'support@example.com')
            }
            
            return send_email(
                recipient=user.email,
                subject=subject,
                body="",
                template_name='subscription_cancellation',
                data=data,
                html=True
            )
            
        except Exception as e:
            self.logger.error(f"Error sending subscription cancellation email: {str(e)}")
            return False
    
    def _send_subscription_extension_email(self, user, subscription, duration_months):
        """
        Envoie un email de confirmation de prolongation d'abonnement.
        
        Args:
            user (User): Utilisateur
            subscription (UserSubscription): Abonnement
            duration_months (int): Durée de prolongation en mois
            
        Returns:
            bool: True si l'email a été envoyé, False sinon
        """
        try:
            subject = f"Prolongation de votre abonnement {subscription.plan}"
            
            data = {
                'user_name': user.get_full_name(),
                'subscription_plan': subscription.plan.capitalize(),
                'duration_months': duration_months,
                'end_date': subscription.end_date.strftime('%d/%m/%Y') if subscription.end_date else 'Illimitée',
                'app_name': current_app.config.get('APP_NAME', 'PMU Prediction'),
                'support_email': current_app.config.get('SUPPORT_EMAIL', 'support@example.com')
            }
            
            return send_email(
                recipient=user.email,
                subject=subject,
                body="",
                template_name='subscription_extension',
                data=data,
                html=True
            )
            
        except Exception as e:
            self.logger.error(f"Error sending subscription extension email: {str(e)}")
            return False
    
    def _send_subscription_change_email(self, user, new_subscription, old_subscription):
        """
        Envoie un email de confirmation de changement de plan d'abonnement.
        
        Args:
            user (User): Utilisateur
            new_subscription (UserSubscription): Nouvel abonnement
            old_subscription (UserSubscription): Ancien abonnement
            
        Returns:
            bool: True si l'email a été envoyé, False sinon
        """
        try:
            subject = f"Changement de votre abonnement vers {new_subscription.plan}"
            
            # Récupérer le nouveau plan d'abonnement
            new_plan = SubscriptionPlan.query.filter_by(name=new_subscription.plan).first()
            
            data = {
                'user_name': user.get_full_name(),
                'old_plan': old_subscription.plan.capitalize() if old_subscription else 'Gratuit',
                'new_plan': new_subscription.plan.capitalize(),
                'subscription_price': new_subscription.price,
                'start_date': new_subscription.start_date.strftime('%d/%m/%Y'),
                'end_date': new_subscription.end_date.strftime('%d/%m/%Y') if new_subscription.end_date else 'Illimitée',
                'plan_features': new_plan.features if new_plan else [],
                'app_name': current_app.config.get('APP_NAME', 'PMU Prediction'),
                'support_email': current_app.config.get('SUPPORT_EMAIL', 'support@example.com')
            }
            
            return send_email(
                recipient=user.email,
                subject=subject,
                body="",
                template_name='subscription_change',
                data=data,
                html=True
            )
            
        except Exception as e:
            self.logger.error(f"Error sending subscription change email: {str(e)}")
            return False