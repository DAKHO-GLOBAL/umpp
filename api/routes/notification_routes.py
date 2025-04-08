# notification_routes.py
# api/routes/notification_routes.py
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from api.services.notification_service import NotificationService
from api.services.user_service import UserService
from api.middleware.rate_limiter import limiter
from api.utils.decorators import subscription_required
from api.app import db

notification_bp = Blueprint('notification', __name__)
notification_service = NotificationService()
user_service = UserService()

@notification_bp.route('/', methods=['GET'])
@jwt_required()
def get_notifications():
    """Récupère les notifications de l'utilisateur"""
    try:
        user_id = get_jwt_identity()
        
        # Paramètres de pagination et filtrage
        page = request.args.get('page', default=1, type=int)
        per_page = request.args.get('per_page', default=20, type=int)
        unread_only = request.args.get('unread_only', default='false').lower() == 'true'
        
        # Récupérer les notifications
        notifications = notification_service.get_user_notifications(
            user_id, page, per_page, unread_only
        )
        
        return jsonify({
            "success": True,
            "count": notifications['count'],
            "page": page,
            "per_page": per_page,
            "total_pages": notifications['total_pages'],
            "data": notifications['data']
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Error retrieving notifications: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred"}), 500


@notification_bp.route('/unread-count', methods=['GET'])
@jwt_required()
def get_unread_count():
    """Récupère le nombre de notifications non lues"""
    try:
        user_id = get_jwt_identity()
        
        # Récupérer le nombre de notifications non lues
        count = notification_service.get_unread_count(user_id)
        
        return jsonify({
            "success": True,
            "unread_count": count
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Error getting unread count: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred"}), 500


@notification_bp.route('/<int:notification_id>/read', methods=['POST'])
@jwt_required()
def mark_read(notification_id):
    """Marque une notification comme lue"""
    try:
        user_id = get_jwt_identity()
        
        # Marquer la notification comme lue
        success = notification_service.mark_notification_as_read(notification_id, user_id)
        
        if not success:
            return jsonify({
                "success": False,
                "message": "Notification not found or does not belong to this user"
            }), 404
        
        return jsonify({
            "success": True,
            "message": "Notification marked as read"
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Error marking notification as read: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred"}), 500


@notification_bp.route('/mark-all-read', methods=['POST'])
@jwt_required()
def mark_all_read():
    """Marque toutes les notifications de l'utilisateur comme lues"""
    try:
        user_id = get_jwt_identity()
        
        # Marquer toutes les notifications comme lues
        success = notification_service.mark_all_as_read(user_id)
        
        return jsonify({
            "success": success,
            "message": "All notifications marked as read" if success else "Failed to mark notifications as read"
        }), 200 if success else 500
    
    except Exception as e:
        current_app.logger.error(f"Error marking all notifications as read: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred"}), 500


@notification_bp.route('/<int:notification_id>', methods=['DELETE'])
@jwt_required()
def delete_notification(notification_id):
    """Supprime une notification"""
    try:
        user_id = get_jwt_identity()
        
        # Supprimer la notification
        success = notification_service.delete_notification(notification_id, user_id)
        
        if not success:
            return jsonify({
                "success": False,
                "message": "Notification not found or does not belong to this user"
            }), 404
        
        return jsonify({
            "success": True,
            "message": "Notification deleted successfully"
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Error deleting notification: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred"}), 500


@notification_bp.route('/settings', methods=['GET'])
@jwt_required()
def get_notification_settings():
    """Récupère les paramètres de notification de l'utilisateur"""
    try:
        user_id = get_jwt_identity()
        
        # Récupérer les paramètres depuis la base de données
        query = """
        SELECT email_notifications, push_notifications, 
               notify_predictions, notify_odds_changes, notify_upcoming_races,
               min_minutes_before_race
        FROM notification_settings
        WHERE user_id = :user_id
        """
        
        result = db.session.execute(query, {"user_id": user_id}).fetchone()
        
        if not result:
            # Paramètres par défaut si non trouvés
            settings = {
                "email_notifications": True,
                "push_notifications": True,
                "notify_predictions": True,
                "notify_odds_changes": True,
                "notify_upcoming_races": True,
                "min_minutes_before_race": 60
            }
        else:
            settings = {
                "email_notifications": result.email_notifications,
                "push_notifications": result.push_notifications,
                "notify_predictions": result.notify_predictions,
                "notify_odds_changes": result.notify_odds_changes,
                "notify_upcoming_races": result.notify_upcoming_races,
                "min_minutes_before_race": result.min_minutes_before_race
            }
            return jsonify({
            "success": True,
            "settings": settings
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Error retrieving notification settings: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred"}), 500


@notification_bp.route('/settings', methods=['PUT'])
@jwt_required()
def update_notification_settings():
    """Met à jour les paramètres de notification de l'utilisateur"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({"success": False, "message": "No data provided"}), 400
        
        # Valider les données
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
        
        # Construire la requête SQL dynamiquement
        update_values = []
        params = {"user_id": user_id}
        
        for key, value in data.items():
            update_values.append(f"{key} = :{key}")
            params[key] = value
        
        # Si aucune donnée valide n'est fournie, retourner une erreur
        if not update_values:
            return jsonify({
                "success": False,
                "message": "No valid settings provided"
            }), 400
        
        # Construire et exécuter la requête
        query = f"""
        INSERT INTO notification_settings (user_id, {', '.join(data.keys())})
        VALUES (:user_id, {', '.join([':'+k for k in data.keys()])})
        ON CONFLICT (user_id) 
        DO UPDATE SET {', '.join(update_values)}
        """
        
        db.session.execute(query, params)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Notification settings updated successfully"
        }), 200
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating notification settings: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred"}), 500


@notification_bp.route('/test', methods=['POST'])
@jwt_required()
@subscription_required(['premium'])
def send_test_notification():
    """Envoie une notification de test à l'utilisateur"""
    try:
        user_id = get_jwt_identity()
        
        # Données de la requête
        data = request.get_json()
        notification_type = data.get('type', 'test')
        
        # Créer une notification de test différente selon le type demandé
        if notification_type == 'odds_change':
            # Notification de changement de cotes
            changed_horses = [
                {
                    "id_cheval": 123,
                    "cheval_nom": "Cheval de test",
                    "cote_avant": 5.2,
                    "cote_apres": 3.8,
                    "variation": -1.4
                }
            ]
            
            notification_id = notification_service.create_odds_change_notification(
                user_id=user_id,
                course_id=1,  # ID factice
                changed_horses=changed_horses
            )
            
        elif notification_type == 'upcoming_course':
            # Notification de course à venir
            notification_id = notification_service.create_upcoming_course_notification(
                user_id=user_id,
                course_id=1,  # ID factice
                time_before_start=30  # 30 minutes avant le départ
            )
            
        elif notification_type == 'prediction':
            # Notification de prédiction
            interesting_picks = [
                {
                    "id_cheval": 123,
                    "cheval_nom": "Cheval de test",
                    "cote": 5.2,
                    "probabilite": 0.85
                }
            ]
            
            notification_id = notification_service.create_course_prediction_notification(
                user_id=user_id,
                course_id=1,  # ID factice
                prediction_type='top3',
                interesting_picks=interesting_picks
            )
            
        else:
            # Notification de test générique
            notification_id = notification_service.create_notification(
                user_id=user_id,
                notification_type='test',
                title='Notification de test',
                message='Ceci est une notification de test pour vérifier que le système fonctionne correctement.',
                data={'test': True, 'timestamp': datetime.now().isoformat()},
                send_email=data.get('send_email', False),
                send_push=data.get('send_push', False)
            )
        
        if not notification_id:
            return jsonify({
                "success": False,
                "message": "Failed to create test notification"
            }), 500
        
        return jsonify({
            "success": True,
            "message": "Test notification sent successfully",
            "notification_id": notification_id
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Error sending test notification: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred"}), 500


@notification_bp.route('/register-device', methods=['POST'])
@jwt_required()
def register_device():
    """Enregistre un appareil pour les notifications push"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or 'device_token' not in data:
            return jsonify({
                "success": False,
                "message": "Device token is required"
            }), 400
        
        # Récupérer les données de l'appareil
        device_token = data.get('device_token')
        device_type = data.get('device_type', 'unknown')  # android, ios, web, etc.
        device_name = data.get('device_name', 'Unknown device')
        
        # Insérer ou mettre à jour l'appareil dans la base de données
        query = """
        INSERT INTO user_devices (user_id, device_token, device_type, device_name, notification_enabled, last_used_at)
        VALUES (:user_id, :device_token, :device_type, :device_name, :notification_enabled, :last_used_at)
        ON CONFLICT (device_token) 
        DO UPDATE SET 
            user_id = :user_id,
            device_type = :device_type,
            device_name = :device_name,
            notification_enabled = :notification_enabled,
            last_used_at = :last_used_at
        """
        
        db.session.execute(query, {
            "user_id": user_id,
            "device_token": device_token,
            "device_type": device_type,
            "device_name": device_name,
            "notification_enabled": True,
            "last_used_at": datetime.now()
        })
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Device registered successfully for push notifications"
        }), 200
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error registering device: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred"}), 500