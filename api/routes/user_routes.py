# user_routes.py
# user_routes.py
# api/routes/user_routes.py
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from api.services.user_service import UserService
from api.schemas.user_schema import UserProfileSchema, UserPasswordChangeSchema, UserPreferencesSchema
from api.middleware.rate_limiter import limiter
from api.utils.decorators import admin_required

user_bp = Blueprint('user', __name__)
user_service = UserService()

# Schémas pour la validation des données
profile_schema = UserProfileSchema()
password_schema = UserPasswordChangeSchema()
preferences_schema = UserPreferencesSchema()

@user_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Récupération du profil de l'utilisateur actuel"""
    try:
        user_id = get_jwt_identity()
        user = user_service.get_user_by_id(user_id)
        
        if not user:
            return jsonify({"success": False, "message": "User not found"}), 404
        
        return jsonify({
            "success": True,
            "data": user.to_dict()
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Error retrieving user profile: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred"}), 500


@user_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Mise à jour du profil de l'utilisateur actuel"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validation des données
        errors = profile_schema.validate(data)
        if errors:
            return jsonify({"success": False, "errors": errors}), 400
        
        # Mise à jour du profil
        updated_user = user_service.update_user_profile(user_id, data)
        
        if not updated_user:
            return jsonify({"success": False, "message": "Failed to update profile"}), 400
        
        return jsonify({
            "success": True,
            "message": "Profile updated successfully",
            "data": updated_user.to_dict()
        }), 200
    
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error updating user profile: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred"}), 500


@user_bp.route('/password', methods=['PUT'])
@jwt_required()
def change_password():
    """Changement du mot de passe de l'utilisateur actuel"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validation des données
        errors = password_schema.validate(data)
        if errors:
            return jsonify({"success": False, "errors": errors}), 400
        
        # Changement du mot de passe
        success = user_service.change_user_password(
            user_id=user_id,
            current_password=data['current_password'],
            new_password=data['new_password']
        )
        
        if not success:
            return jsonify({
                "success": False,
                "message": "Failed to change password. Please verify your current password."
            }), 400
        
        return jsonify({
            "success": True,
            "message": "Password changed successfully"
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Error changing password: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred"}), 500


@user_bp.route('/preferences', methods=['GET'])
@jwt_required()
def get_preferences():
    """Récupération des préférences de l'utilisateur actuel"""
    try:
        user_id = get_jwt_identity()
        user = user_service.get_user_by_id(user_id)
        
        if not user:
            return jsonify({"success": False, "message": "User not found"}), 404
        
        return jsonify({
            "success": True,
            "data": user.get_preferences()
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Error retrieving user preferences: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred"}), 500


@user_bp.route('/preferences', methods=['PUT'])
@jwt_required()
def update_preferences():
    """Mise à jour des préférences de l'utilisateur actuel"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validation des données
        errors = preferences_schema.validate(data)
        if errors:
            return jsonify({"success": False, "errors": errors}), 400
        
        # Mise à jour des préférences
        success = user_service.update_user_preferences(user_id, data)
        
        if not success:
            return jsonify({"success": False, "message": "Failed to update preferences"}), 400
        
        # Récupération des préférences mises à jour
        user = user_service.get_user_by_id(user_id)
        
        return jsonify({
            "success": True,
            "message": "Preferences updated successfully",
            "data": user.get_preferences()
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Error updating user preferences: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred"}), 500


@user_bp.route('/notification-settings', methods=['GET'])
@jwt_required()
def get_notification_settings():
    """Récupération des paramètres de notification de l'utilisateur actuel"""
    try:
        user_id = get_jwt_identity()
        settings = user_service.get_notification_settings(user_id)
        
        return jsonify({
            "success": True,
            "data": settings
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Error retrieving notification settings: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred"}), 500


@user_bp.route('/notification-settings', methods=['PUT'])
@jwt_required()
def update_notification_settings():
    """Mise à jour des paramètres de notification de l'utilisateur actuel"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validation des données
        valid_keys = [
            'email_notifications', 'push_notifications', 
            'notify_predictions', 'notify_odds_changes', 'notify_upcoming_races',
            'min_minutes_before_race'
        ]
        
        # Vérifier que toutes les clés sont valides
        for key in data.keys():
            if key not in valid_keys:
                return jsonify({
                    "success": False, 
                    "message": f"Invalid setting key: {key}"
                }), 400
        
        # Mise à jour des paramètres
        success = user_service.update_notification_settings(user_id, data)
        
        if not success:
            return jsonify({
                "success": False,
                "message": "Failed to update notification settings"
            }), 400
        
        # Récupération des paramètres mis à jour
        settings = user_service.get_notification_settings(user_id)
        
        return jsonify({
            "success": True,
            "message": "Notification settings updated successfully",
            "data": settings
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Error updating notification settings: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred"}), 500


@user_bp.route('/statistics', methods=['GET'])
@jwt_required()
def get_statistics():
    """Récupération des statistiques d'utilisation de l'utilisateur actuel"""
    try:
        user_id = get_jwt_identity()
        statistics = user_service.get_user_statistics(user_id)
        
        return jsonify({
            "success": True,
            "data": statistics
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Error retrieving user statistics: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred"}), 500


@user_bp.route('/subscription', methods=['GET'])
@jwt_required()
def get_subscription():
    """Récupération des informations d'abonnement de l'utilisateur actuel"""
    try:
        user_id = get_jwt_identity()
        user = user_service.get_user_by_id(user_id)
        
        if not user:
            return jsonify({"success": False, "message": "User not found"}), 404
        
        # Récupérer les infos d'abonnement
        subscription_info = {
            'level': user.subscription_level,
            'active': user.is_subscription_active(),
            'start_date': user.subscription_start.isoformat() if user.subscription_start else None,
            'expiry_date': user.subscription_expiry.isoformat() if user.subscription_expiry else None,
            'days_remaining': 0
        }
        
        # Calculer les jours restants
        if subscription_info['active'] and user.subscription_expiry:
            from datetime import datetime
            days_remaining = (user.subscription_expiry - datetime.utcnow()).days
            subscription_info['days_remaining'] = max(0, days_remaining)
        
        # Récupérer les limites associées à l'abonnement
        subscription_limits = current_app.config['SUBSCRIPTION_LEVELS'].get(
            user.subscription_level, {'predictions_per_day': 5, 'simulations_per_day': 2}
        )
        
        subscription_info['limits'] = subscription_limits
        
        return jsonify({
            "success": True,
            "data": subscription_info
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Error retrieving subscription info: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred"}), 500


@user_bp.route('/deactivate', methods=['POST'])
@jwt_required()
def deactivate_account():
    """Désactivation du compte de l'utilisateur actuel"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Vérification du mot de passe
        password = data.get('password')
        if not password:
            return jsonify({
                "success": False,
                "message": "Password is required to deactivate account"
            }), 400
        
        # Récupérer l'utilisateur et vérifier le mot de passe
        user = user_service.get_user_by_id(user_id)
        if not user or not user.check_password(password):
            return jsonify({
                "success": False,
                "message": "Invalid password"
            }), 401
        
        # Désactiver le compte
        success = user_service.deactivate_user(user_id)
        
        if not success:
            return jsonify({
                "success": False,
                "message": "Failed to deactivate account"
            }), 400
        
        return jsonify({
            "success": True,
            "message": "Account deactivated successfully"
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Error deactivating account: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred"}), 500


@user_bp.route('/verify-email', methods=['POST'])
@jwt_required()
def resend_verification():
    """Renvoie l'email de vérification à l'utilisateur actuel"""
    try:
        user_id = get_jwt_identity()
        user = user_service.get_user_by_id(user_id)
        
        if not user:
            return jsonify({"success": False, "message": "User not found"}), 404
        
        if user.is_verified:
            return jsonify({
                "success": True,
                "message": "Email already verified"
            }), 200
        
        # Renvoyer l'email de vérification
        success = user_service.resend_verification_email(user_id)
        
        if not success:
            return jsonify({
                "success": False,
                "message": "Failed to send verification email"
            }), 400
        
        return jsonify({
            "success": True,
            "message": "Verification email sent successfully"
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Error sending verification email: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred"}), 500


# Admin routes for user management
@user_bp.route('/admin/users', methods=['GET'])
@jwt_required()
@admin_required
@limiter.limit("100/hour")
def list_users():
    """Liste tous les utilisateurs (admin seulement)"""
    try:
        # Paramètres de pagination et filtrage
        page = request.args.get('page', default=1, type=int)
        per_page = request.args.get('per_page', default=20, type=int)
        search = request.args.get('search', default='')
        status = request.args.get('status', default='all')  # all, active, inactive
        
        # Requête SQL pour récupérer les utilisateurs
        query = """
        SELECT 
            u.id, u.email, u.username, u.first_name, u.last_name, 
            u.is_active, u.is_admin, u.is_verified, 
            u.subscription_level, u.subscription_expiry,
            u.created_at, u.last_login
        FROM users u
        WHERE 1=1
        """
        
        params = {}
        
        # Ajouter le filtre de recherche
        if search:
            query += " AND (u.email LIKE :search OR u.username LIKE :search OR u.first_name LIKE :search OR u.last_name LIKE :search)"
            params['search'] = f"%{search}%"
        
        # Ajouter le filtre de statut
        if status == 'active':
            query += " AND u.is_active = TRUE"
        elif status == 'inactive':
            query += " AND u.is_active = FALSE"
        
        # Ajouter l'ordre et la pagination
        query += " ORDER BY u.created_at DESC LIMIT :limit OFFSET :offset"
        params['limit'] = per_page
        params['offset'] = (page - 1) * per_page
        
        # Exécuter la requête
        from api import db
        from sqlalchemy import text
        
        result = db.session.execute(text(query), params)
        
        # Convertir le résultat en liste de dictionnaires
        users = []
        for row in result:
            user = {
                "id": row.id,
                "email": row.email,
                "username": row.username,
                "first_name": row.first_name,
                "last_name": row.last_name,
                "is_active": row.is_active,
                "is_admin": row.is_admin,
                "is_verified": row.is_verified,
                "subscription_level": row.subscription_level,
                "subscription_expiry": row.subscription_expiry.isoformat() if row.subscription_expiry else None,
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "last_login": row.last_login.isoformat() if row.last_login else None
            }
            users.append(user)
        
        # Compter le nombre total d'utilisateurs pour la pagination
        count_query = """
        SELECT COUNT(*) AS count FROM users u WHERE 1=1
        """
        
        if search:
            count_query += " AND (u.email LIKE :search OR u.username LIKE :search OR u.first_name LIKE :search OR u.last_name LIKE :search)"
        
        if status == 'active':
            count_query += " AND u.is_active = TRUE"
        elif status == 'inactive':
            count_query += " AND u.is_active = FALSE"
        
        count_result = db.session.execute(text(count_query), params).fetchone()
        total_count = count_result.count if count_result else 0
        
        # Calculer le nombre total de pages
        total_pages = (total_count + per_page - 1) // per_page
        
        return jsonify({
            "success": True,
            "count": total_count,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
            "data": users
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Error listing users: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred"}), 500


@user_bp.route('/admin/users/<int:user_id>', methods=['GET'])
@jwt_required()
@admin_required
def get_user(user_id):
    """Récupère les détails d'un utilisateur spécifique (admin seulement)"""
    try:
        user = user_service.get_user_by_id(user_id)
        
        if not user:
            return jsonify({"success": False, "message": "User not found"}), 404
        
        # Récupérer les statistiques de l'utilisateur
        statistics = user_service.get_user_statistics(user_id)
        
        # Récupérer les paramètres de notification
        notification_settings = user_service.get_notification_settings(user_id)
        
        user_data = user.to_dict(with_stats=True)
        user_data['statistics'] = statistics
        user_data['notification_settings'] = notification_settings
        
        return jsonify({
            "success": True,
            "data": user_data
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Error retrieving user details: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred"}), 500


@user_bp.route('/admin/users/<int:user_id>', methods=['PUT'])
@jwt_required()
@admin_required
def update_user(user_id):
    """Met à jour les détails d'un utilisateur (admin seulement)"""
    try:
        data = request.get_json()
        
        # Validation des données
        from api.schemas.user_schema import AdminUserUpdateSchema
        admin_schema = AdminUserUpdateSchema()
        
        errors = admin_schema.validate(data)
        if errors:
            return jsonify({"success": False, "errors": errors}), 400
        
        user = user_service.get_user_by_id(user_id)
        
        if not user:
            return jsonify({"success": False, "message": "User not found"}), 404
        
        # Mettre à jour les champs de l'utilisateur
        if 'email' in data:
            user.email = data['email'].lower()
        
        if 'username' in data:
            user.username = data['username']
        
        if 'first_name' in data:
            user.first_name = data['first_name']
        
        if 'last_name' in data:
            user.last_name = data['last_name']
        
        if 'is_active' in data:
            user.is_active = data['is_active']
        
        if 'is_admin' in data:
            user.is_admin = data['is_admin']
        
        if 'is_verified' in data:
            user.is_verified = data['is_verified']
        
        if 'subscription_level' in data:
            user.subscription_level = data['subscription_level']
        
        if 'subscription_expiry' in data:
            user.subscription_expiry = data['subscription_expiry']
        
        # Sauvegarder les modifications
        from api import db
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "User updated successfully",
            "data": user.to_dict()
        }), 200
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating user: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred"}), 500


@user_bp.route('/admin/users/<int:user_id>/reset-password', methods=['POST'])
@jwt_required()
@admin_required
def admin_reset_password(user_id):
    """Réinitialise le mot de passe d'un utilisateur (admin seulement)"""
    try:
        data = request.get_json()
        
        if not data or 'new_password' not in data:
            return jsonify({
                "success": False,
                "message": "New password is required"
            }), 400
        
        user = user_service.get_user_by_id(user_id)
        
        if not user:
            return jsonify({"success": False, "message": "User not found"}), 404
        
        # Réinitialiser le mot de passe
        user.set_password(data['new_password'])
        
        # Sauvegarder les modifications
        from api import db
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Password reset successfully"
        }), 200
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error resetting password: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred"}), 500


@user_bp.route('/admin/users/<int:user_id>/deactivate', methods=['POST'])
@jwt_required()
@admin_required
def admin_deactivate_user(user_id):
    """Désactive un compte utilisateur (admin seulement)"""
    try:
        success = user_service.deactivate_user(user_id)
        
        if not success:
            return jsonify({
                "success": False,
                "message": "Failed to deactivate user"
            }), 400
        
        return jsonify({
            "success": True,
            "message": "User deactivated successfully"
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Error deactivating user: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred"}), 500


@user_bp.route('/admin/users/<int:user_id>/activate', methods=['POST'])
@jwt_required()
@admin_required
def admin_activate_user(user_id):
    """Réactive un compte utilisateur (admin seulement)"""
    try:
        success = user_service.reactivate_user(user_id)
        
        if not success:
            return jsonify({
                "success": False,
                "message": "Failed to activate user"
            }), 400
        
        return jsonify({
            "success": True,
            "message": "User activated successfully"
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Error activating user: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred"}), 500


@user_bp.route('/admin/users/<int:user_id>/subscription', methods=['POST'])
@jwt_required()
@admin_required
def admin_update_subscription(user_id):
    """Met à jour l'abonnement d'un utilisateur (admin seulement)"""
    try:
        data = request.get_json()
        
        if not data or 'plan' not in data:
            return jsonify({
                "success": False,
                "message": "Subscription plan is required"
            }), 400
        
        plan_name = data['plan']
        duration_months = data.get('duration_months', 1)
        
        if plan_name not in ['free', 'standard', 'premium']:
            return jsonify({
                "success": False,
                "message": "Invalid subscription plan"
            }), 400
        
        success = user_service.upgrade_subscription(user_id, plan_name, duration_months)
        
        if not success:
            return jsonify({
                "success": False,
                "message": "Failed to update subscription"
            }), 400
        
        return jsonify({
            "success": True,
            "message": f"Subscription updated to {plan_name} for {duration_months} month(s)"
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Error updating subscription: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred"}), 500


@user_bp.route('/admin/users/stats', methods=['GET'])
@jwt_required()
@admin_required
def admin_get_user_stats():
    """Récupère des statistiques globales sur les utilisateurs (admin seulement)"""
    try:
        # Requête SQL pour les statistiques globales
        from api import db
        from sqlalchemy import text
        
        stats_query = """
        SELECT 
            COUNT(*) AS total_users,
            SUM(CASE WHEN is_active = TRUE THEN 1 ELSE 0 END) AS active_users,
            SUM(CASE WHEN is_verified = TRUE THEN 1 ELSE 0 END) AS verified_users,
            SUM(CASE WHEN subscription_level = 'free' THEN 1 ELSE 0 END) AS free_users,
            SUM(CASE WHEN subscription_level = 'standard' THEN 1 ELSE 0 END) AS standard_users,
            SUM(CASE WHEN subscription_level = 'premium' THEN 1 ELSE 0 END) AS premium_users,
            COUNT(DISTINCT DATE(created_at)) AS registration_days,
            COUNT(*) / COUNT(DISTINCT DATE(created_at)) AS avg_registrations_per_day
        FROM users
        """
        
        result = db.session.execute(text(stats_query)).fetchone()
        
        # Requête pour les inscriptions par jour (30 derniers jours)
        registrations_query = """
        SELECT 
            DATE(created_at) AS date,
            COUNT(*) AS count
        FROM users
        WHERE created_at >= NOW() - INTERVAL '30 days'
        GROUP BY DATE(created_at)
        ORDER BY date DESC
        """
        
        registrations_result = db.session.execute(text(registrations_query))
        registrations = [
            {"date": row.date.isoformat(), "count": row.count}
            for row in registrations_result
        ]
        
        # Requête pour les statistiques d'abonnement
        subscription_query = """
        SELECT 
            subscription_level,
            COUNT(*) AS count,
            COUNT(*) * 100.0 / (SELECT COUNT(*) FROM users) AS percentage
        FROM users
        GROUP BY subscription_level
        """
        
        subscription_result = db.session.execute(text(subscription_query))
        subscriptions = [
            {"level": row.subscription_level, "count": row.count, "percentage": row.percentage}
            for row in subscription_result
        ]
        
        # Construire la réponse
        stats = {
            "users": {
                "total": result.total_users,
                "active": result.active_users,
                "verified": result.verified_users,
                "activation_rate": result.active_users / result.total_users if result.total_users > 0 else 0,
                "verification_rate": result.verified_users / result.total_users if result.total_users > 0 else 0
            },
            "subscriptions": {
                "free": result.free_users,
                "standard": result.standard_users,
                "premium": result.premium_users,
                "detailed": subscriptions
            },
            "registrations": {
                "total_days": result.registration_days,
                "avg_per_day": result.avg_registrations_per_day,
                "last_30_days": registrations
            }
        }
        
        return jsonify({
            "success": True,
            "data": stats
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Error retrieving user statistics: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred"}), 500