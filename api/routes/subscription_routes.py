# subscription_routes.py
# subscription_routes.py
# api/routes/subscription_routes.py
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from api.services.subscription_service import SubscriptionService
from api.services.user_service import UserService
from api.middleware.rate_limiter import limiter
from api.utils.decorators import subscription_required

subscription_bp = Blueprint('subscription', __name__)
subscription_service = SubscriptionService()
user_service = UserService()

@subscription_bp.route('/plans', methods=['GET'])
def get_plans():
    """Récupère la liste des plans d'abonnement disponibles"""
    try:
        plans = subscription_service.get_subscription_plans()
        
        return jsonify({
            "success": True,
            "count": len(plans),
            "data": plans
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Error retrieving subscription plans: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred"}), 500


@subscription_bp.route('/current', methods=['GET'])
@jwt_required()
def get_current_subscription():
    """Récupère les détails de l'abonnement actuel de l'utilisateur"""
    try:
        user_id = get_jwt_identity()
        user = user_service.get_user_by_id(user_id)
        
        if not user:
            return jsonify({"success": False, "message": "User not found"}), 404
        
        # Récupérer l'abonnement actif
        subscription = subscription_service.get_user_subscription(user_id)
        
        # Récupérer les limites associées à l'abonnement
        subscription_level = user.subscription_level
        subscription_limits = current_app.config['SUBSCRIPTION_LEVELS'].get(
            subscription_level, {'predictions_per_day': 5, 'simulations_per_day': 2}
        )
        
        # Construire la réponse
        subscription_info = {
            'level': user.subscription_level,
            'active': user.is_subscription_active(),
            'start_date': user.subscription_start.isoformat() if user.subscription_start else None,
            'expiry_date': user.subscription_expiry.isoformat() if user.subscription_expiry else None,
            'limits': subscription_limits
        }
        
        # Ajouter les détails complets si disponibles
        if subscription:
            subscription_info['details'] = subscription
        
        # Calculer les jours restants
        if subscription_info['active'] and user.subscription_expiry:
            from datetime import datetime
            days_remaining = (user.subscription_expiry - datetime.utcnow()).days
            subscription_info['days_remaining'] = max(0, days_remaining)
        
        return jsonify({
            "success": True,
            "data": subscription_info
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Error retrieving current subscription: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred"}), 500


@subscription_bp.route('/history', methods=['GET'])
@jwt_required()
def get_subscription_history():
    """Récupère l'historique des abonnements de l'utilisateur"""
    try:
        user_id = get_jwt_identity()
        
        # Récupérer l'historique des abonnements
        history = subscription_service.get_subscription_history(user_id)
        
        return jsonify({
            "success": True,
            "count": len(history),
            "data": history
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Error retrieving subscription history: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred"}), 500


@subscription_bp.route('/subscribe', methods=['POST'])
@jwt_required()
def subscribe():
    """Souscrit à un nouvel abonnement ou met à niveau l'abonnement existant"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validation des données
        if 'plan' not in data:
            return jsonify({"success": False, "message": "Plan name is required"}), 400
        
        plan_name = data['plan']
        duration_months = data.get('duration_months', 1)
        payment_method = data.get('payment_method')
        promotion_code = data.get('promotion_code')
        payment_reference = data.get('payment_reference')
        
        # Vérifier que le plan existe
        plan = subscription_service.get_plan_by_name(plan_name)
        if not plan:
            return jsonify({"success": False, "message": f"Plan {plan_name} not found"}), 404
        
        # Vérifier le code promo si fourni
        promo_validated = None
        if promotion_code:
            promo_validated = subscription_service.validate_promotion_code(promotion_code, plan_name)
            if not promo_validated:
                return jsonify({"success": False, "message": "Invalid or expired promotion code"}), 400
        
        # Créer l'abonnement
        subscription = subscription_service.create_subscription(
            user_id=user_id,
            plan_name=plan_name,
            duration_months=duration_months,
            payment_method=payment_method,
            promotion_code=promotion_code if promo_validated else None,
            payment_reference=payment_reference
        )
        
        if not subscription:
            return jsonify({"success": False, "message": "Failed to create subscription"}), 500
        
        return jsonify({
            "success": True,
            "message": f"Successfully subscribed to {plan_name} plan",
            "data": subscription
        }), 201
    
    except Exception as e:
        current_app.logger.error(f"Error creating subscription: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred"}), 500


@subscription_bp.route('/cancel', methods=['POST'])
@jwt_required()
def cancel_subscription():
    """Annule l'abonnement actuel de l'utilisateur"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Option pour annulation immédiate
        immediate = data.get('immediate', False)
        
        # Annuler l'abonnement
        success = subscription_service.cancel_subscription(user_id, immediate)
        
        if not success:
            return jsonify({"success": False, "message": "Failed to cancel subscription"}), 400
        
        return jsonify({
            "success": True,
            "message": f"Subscription cancelled {'immediately' if immediate else 'at the end of the current period'}"
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Error cancelling subscription: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred"}), 500


@subscription_bp.route('/extend', methods=['POST'])
@jwt_required()
def extend_subscription():
    """Prolonge l'abonnement actuel de l'utilisateur"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validation des données
        if 'duration_months' not in data:
            return jsonify({"success": False, "message": "Duration in months is required"}), 400
        
        duration_months = data.get('duration_months', 1)
        payment_method = data.get('payment_method')
        payment_reference = data.get('payment_reference')
        
        # Récupérer l'abonnement actuel pour vérifier qu'il en a un
        current_subscription = subscription_service.get_user_subscription(user_id)
        
        if not current_subscription:
            return jsonify({
                "success": False, 
                "message": "No active subscription found to extend. Please subscribe first."
            }), 400
        
        # Prolonger l'abonnement
        extended_subscription = subscription_service.extend_subscription(user_id, duration_months)
        
        if not extended_subscription:
            return jsonify({"success": False, "message": "Failed to extend subscription"}), 500
        
        return jsonify({
            "success": True,
            "message": f"Subscription extended by {duration_months} month(s)",
            "data": extended_subscription
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Error extending subscription: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred"}), 500


@subscription_bp.route('/change', methods=['POST'])
@jwt_required()
def change_subscription():
    """Change le plan d'abonnement de l'utilisateur"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validation des données
        if 'plan' not in data:
            return jsonify({"success": False, "message": "New plan name is required"}), 400
        
        new_plan_name = data['plan']
        payment_method = data.get('payment_method')
        promotion_code = data.get('promotion_code')
        payment_reference = data.get('payment_reference')
        
        # Vérifier que le plan existe
        plan = subscription_service.get_plan_by_name(new_plan_name)
        if not plan:
            return jsonify({"success": False, "message": f"Plan {new_plan_name} not found"}), 404
        
        # Vérifier le code promo si fourni
        if promotion_code:
            promo_valid = subscription_service.validate_promotion_code(promotion_code, new_plan_name)
            if not promo_valid:
                return jsonify({"success": False, "message": "Invalid or expired promotion code"}), 400
        
        # Changer l'abonnement
        subscription = subscription_service.change_subscription_plan(
            user_id=user_id,
            new_plan_name=new_plan_name,
            payment_method=payment_method,
            promotion_code=promotion_code,
            payment_reference=payment_reference
        )
        
        if not subscription:
            return jsonify({"success": False, "message": "Failed to change subscription"}), 500
        
        return jsonify({
            "success": True,
            "message": f"Subscription changed to {new_plan_name}",
            "data": subscription
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Error changing subscription: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred"}), 500


@subscription_bp.route('/check-promo', methods=['POST'])
@jwt_required()
def check_promo_code():
    """Vérifie la validité d'un code promotionnel"""
    try:
        data = request.get_json()
        
        # Validation des données
        if 'code' not in data:
            return jsonify({"success": False, "message": "Promotion code is required"}), 400
        
        code = data['code']
        plan_name = data.get('plan')
        
        # Vérifier le code promo
        promo = subscription_service.validate_promotion_code(code, plan_name)
        
        if not promo:
            return jsonify({"success": False, "message": "Invalid or expired promotion code"}), 400
        
        return jsonify({
            "success": True,
            "message": "Promotion code is valid",
            "data": promo
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Error checking promotion code: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred"}), 500


@subscription_bp.route('/transactions', methods=['GET'])
@jwt_required()
def get_transactions():
    """Récupère l'historique des transactions de paiement de l'utilisateur"""
    try:
        user_id = get_jwt_identity()
        
        # Récupérer les transactions
        transactions = subscription_service.get_payment_transactions(user_id)
        
        return jsonify({
            "success": True,
            "count": len(transactions),
            "data": transactions
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Error retrieving payment transactions: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred"}), 500


@subscription_bp.route('/verify-payment', methods=['POST'])
@jwt_required()
def verify_payment():
    """Vérifie un paiement et active l'abonnement si valide"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validation des données
        if 'payment_reference' not in data or 'payment_method' not in data or 'plan' not in data:
            return jsonify({
                "success": False, 
                "message": "Payment reference, payment method and plan are required"
            }), 400
        
        payment_reference = data['payment_reference']
        payment_method = data['payment_method']
        plan_name = data['plan']
        duration_months = data.get('duration_months', 1)
        promotion_code = data.get('promotion_code')
        
        # TODO: Implémenter la vérification de paiement avec le service de paiement
        # Cette partie dépend du service de paiement utilisé (Stripe, PayPal, etc.)
        # Pour l'instant, on considère que le paiement est validé
        
        # Créer l'abonnement
        subscription = subscription_service.create_subscription(
            user_id=user_id,
            plan_name=plan_name,
            duration_months=duration_months,
            payment_method=payment_method,
            promotion_code=promotion_code,
            payment_reference=payment_reference
        )
        
        if not subscription:
            return jsonify({"success": False, "message": "Failed to create subscription"}), 500
        
        return jsonify({
            "success": True,
            "message": "Payment verified and subscription activated",
            "data": subscription
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Error verifying payment: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred"}), 500


@subscription_bp.route('/usage', methods=['GET'])
@jwt_required()
def get_usage():
    """Récupère les statistiques d'utilisation de l'abonnement"""
    try:
        user_id = get_jwt_identity()
        
        # Récupérer l'utilisation des prédictions
        from api.services.prediction_service import PredictionService
        prediction_service = PredictionService()
        predictions_today = prediction_service.get_predictions_count_today(user_id)
        
        # Récupérer l'utilisation des simulations
        from api.services.simulation_service import SimulationService
        simulation_service = SimulationService()
        simulations_today = simulation_service.get_simulations_count_today(user_id)
        
        # Récupérer les limites de l'abonnement
        user = user_service.get_user_by_id(user_id)
        
        subscription_level = user.subscription_level
        subscription_limits = current_app.config['SUBSCRIPTION_LEVELS'].get(
            subscription_level, {'predictions_per_day': 5, 'simulations_per_day': 2}
        )
        
        predictions_limit = subscription_limits.get('predictions_per_day', 5)
        simulations_limit = subscription_limits.get('simulations_per_day', 2)
        
        return jsonify({
            "success": True,
            "data": {
                "predictions": {
                    "used_today": predictions_today,
                    "limit": predictions_limit,
                    "remaining": "Unlimited" if predictions_limit == -1 else (predictions_limit - predictions_today)
                },
                "simulations": {
                    "used_today": simulations_today,
                    "limit": simulations_limit,
                    "remaining": "Unlimited" if simulations_limit == -1 else (simulations_limit - simulations_today)
                },
                "subscription_level": subscription_level,
                "features": subscription_limits.get('features', [])
            }
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Error retrieving subscription usage: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred"}), 500