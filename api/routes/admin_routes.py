# admin_routes.py
# admin_routes.py
# api/routes/admin_routes.py
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required
from utils.decorators import admin_required
from middleware.rate_limiter import limiter
from sqlalchemy import text
from extensions import db
from services.user_service import UserService
from services.prediction_service import PredictionService
from services.simulation_service import SimulationService
from services.notification_service import NotificationService

admin_bp = Blueprint('admin', __name__)
user_service = UserService()
prediction_service = PredictionService()
simulation_service = SimulationService()
notification_service = NotificationService()

@admin_bp.route('/dashboard', methods=['GET'])
@jwt_required()
@admin_required
def admin_dashboard():
    """Récupère les données pour le tableau de bord d'administration"""
    try:
        # Statistiques utilisateurs
        user_query = text("""
        SELECT
            COUNT(*) AS total_users,
            SUM(CASE WHEN is_active = TRUE THEN 1 ELSE 0 END) AS active_users,
            SUM(CASE WHEN is_verified = TRUE THEN 1 ELSE 0 END) AS verified_users,
            SUM(CASE WHEN subscription_level = 'free' THEN 1 ELSE 0 END) AS free_users,
            SUM(CASE WHEN subscription_level = 'standard' THEN 1 ELSE 0 END) AS standard_users,
            SUM(CASE WHEN subscription_level = 'premium' THEN 1 ELSE 0 END) AS premium_users,
            COUNT(DISTINCT DATE(created_at)) AS registration_days
        FROM users
        """)
        
        user_stats = db.session.execute(user_query).fetchone()
        
        # Statistiques prédictions
        prediction_query = text("""
        SELECT
            COUNT(*) AS total_predictions,
            COUNT(DISTINCT course_id) AS unique_courses,
            MAX(created_at) AS last_prediction
        FROM predictions
        """)
        
        prediction_stats = db.session.execute(prediction_query).fetchone()
        
        # Statistiques simulations
        simulation_query = text("""
        SELECT
            COUNT(*) AS total_simulations,
            COUNT(DISTINCT course_id) AS unique_courses,
            MAX(created_at) AS last_simulation
        FROM simulations
        """)
        
        simulation_stats = db.session.execute(simulation_query).fetchone()
        
        # Statistiques courses
        course_query = text("""
        SELECT
            COUNT(*) AS total_courses,
            SUM(CASE WHEN date_heure > NOW() THEN 1 ELSE 0 END) AS upcoming_courses,
            SUM(CASE WHEN date_heure <= NOW() THEN 1 ELSE 0 END) AS past_courses
        FROM courses
        """)
        
        course_stats = db.session.execute(course_query).fetchone()
        
        return jsonify({
            "success": True,
            "data": {
                "users": {
                    "total": user_stats.total_users,
                    "active": user_stats.active_users,
                    "verified": user_stats.verified_users,
                    "free": user_stats.free_users,
                    "standard": user_stats.standard_users,
                    "premium": user_stats.premium_users
                },
                "predictions": {
                    "total": prediction_stats.total_predictions,
                    "unique_courses": prediction_stats.unique_courses,
                    "last_prediction": prediction_stats.last_prediction.isoformat() if prediction_stats.last_prediction else None
                },
                "simulations": {
                    "total": simulation_stats.total_simulations,
                    "unique_courses": simulation_stats.unique_courses,
                    "last_simulation": simulation_stats.last_simulation.isoformat() if simulation_stats.last_simulation else None
                },
                "courses": {
                    "total": course_stats.total_courses,
                    "upcoming": course_stats.upcoming_courses,
                    "past": course_stats.past_courses
                }
            }
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Error retrieving admin dashboard: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred"}), 500


@admin_bp.route('/users', methods=['GET'])
@jwt_required()
@admin_required
@limiter.limit("100/hour")
def admin_list_users():
    """Liste tous les utilisateurs avec options de filtrage et pagination"""
    try:
        # Paramètres de pagination et filtrage
        page = request.args.get('page', default=1, type=int)
        per_page = request.args.get('per_page', default=20, type=int)
        search = request.args.get('search', default='')
        subscription = request.args.get('subscription', default='all')
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
        
        # Ajouter le filtre d'abonnement
        if subscription != 'all':
            query += " AND u.subscription_level = :subscription"
            params['subscription'] = subscription
        
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
        
        if subscription != 'all':
            count_query += " AND u.subscription_level = :subscription"
        
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


@admin_bp.route('/users/<int:user_id>', methods=['GET'])
@jwt_required()
@admin_required
def admin_get_user(user_id):
    """Récupère les détails d'un utilisateur spécifique"""
    try:
        user = user_service.get_user_by_id(user_id)
        
        if not user:
            return jsonify({"success": False, "message": "User not found"}), 404
        
        # Récupérer les statistiques détaillées
        statistics = user_service.get_user_statistics(user_id)
        
        # Récupérer l'historique des abonnements
        subscription_query = text("""
        SELECT 
            s.id, s.plan, s.start_date, s.end_date, s.price, s.status, 
            s.payment_method, s.created_at
        FROM user_subscriptions s
        WHERE s.user_id = :user_id
        ORDER BY s.created_at DESC
        """)
        
        subscription_result = db.session.execute(subscription_query, {"user_id": user_id})
        
        subscriptions = []
        for row in subscription_result:
            subscription = {
                "id": row.id,
                "plan": row.plan,
                "start_date": row.start_date.isoformat() if row.start_date else None,
                "end_date": row.end_date.isoformat() if row.end_date else None,
                "price": row.price,
                "status": row.status,
                "payment_method": row.payment_method,
                "created_at": row.created_at.isoformat() if row.created_at else None
            }
            subscriptions.append(subscription)
        
        # Construire la réponse complète
        user_data = user.to_dict(with_stats=True)
        user_data['statistics'] = statistics
        user_data['subscription_history'] = subscriptions
        
        return jsonify({
            "success": True,
            "data": user_data
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Error retrieving user details: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred"}), 500


@admin_bp.route('/users/<int:user_id>', methods=['PUT'])
@jwt_required()
@admin_required
def admin_update_user(user_id):
    """Met à jour les informations d'un utilisateur"""
    try:
        data = request.get_json()
        user = user_service.get_user_by_id(user_id)
        
        if not user:
            return jsonify({"success": False, "message": "User not found"}), 404
        
        # Champs modifiables
        modifiable_fields = [
            'email', 'username', 'first_name', 'last_name', 
            'is_active', 'is_admin', 'is_verified', 'subscription_level'
        ]
        
        # Mettre à jour les champs
        updated = False
        for field in modifiable_fields:
            if field in data:
                setattr(user, field, data[field])
                updated = True
        
        # Mettre à jour l'abonnement si spécifié
        if 'subscription_expiry' in data:
            try:
                from datetime import datetime
                expiry_date = datetime.fromisoformat(data['subscription_expiry'])
                user.subscription_expiry = expiry_date
                updated = True
            except (ValueError, TypeError):
                return jsonify({"success": False, "message": "Invalid date format for subscription_expiry"}), 400
        
        # Mettre à jour le mot de passe si spécifié
        if 'new_password' in data and data['new_password']:
            user.set_password(data['new_password'])
            updated = True
        
        if updated:
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


@admin_bp.route('/models', methods=['GET'])
@jwt_required()
@admin_required
def list_models():
    """Liste tous les modèles de prédiction"""
    try:
        query = text("""
        SELECT 
            m.id, m.model_type, m.model_category, m.training_date, 
            m.accuracy, m.f1_score, m.is_active, m.file_path
        FROM model_versions m
        ORDER BY m.training_date DESC
        """)
        
        result = db.session.execute(query)
        
        models = []
        for row in result:
            model = {
                "id": row.id,
                "model_type": row.model_type,
                "model_category": row.model_category,
                "training_date": row.training_date.isoformat() if row.training_date else None,
                "accuracy": row.accuracy,
                "f1_score": row.f1_score,
                "is_active": row.is_active,
                "file_path": row.file_path
            }
            models.append(model)
        
        return jsonify({
            "success": True,
            "count": len(models),
            "data": models
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Error listing models: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred"}), 500


@admin_bp.route('/models/<int:model_id>/activate', methods=['POST'])
@jwt_required()
@admin_required
def activate_model(model_id):
    """Active un modèle spécifique comme modèle principal"""
    try:
        # Récupérer le modèle
        model_query = text("""
        SELECT m.id, m.model_category
        FROM model_versions m
        WHERE m.id = :model_id
        """)
        
        model = db.session.execute(model_query, {"model_id": model_id}).fetchone()
        
        if not model:
            return jsonify({"success": False, "message": "Model not found"}), 404
        
        # Désactiver tous les modèles de cette catégorie
        deactivate_query = text("""
        UPDATE model_versions
        SET is_active = FALSE
        WHERE model_category = :category
        """)
        
        db.session.execute(deactivate_query, {"category": model.model_category})
        
        # Activer le modèle sélectionné
        activate_query = text("""
        UPDATE model_versions
        SET is_active = TRUE
        WHERE id = :model_id
        """)
        
        db.session.execute(activate_query, {"model_id": model_id})
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": f"Model {model_id} activated successfully"
        }), 200
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error activating model: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred"}), 500


@admin_bp.route('/maintenance/toggle', methods=['POST'])
@jwt_required()
@admin_required
def toggle_maintenance_mode():
    """Active ou désactive le mode maintenance de l'API"""
    try:
        data = request.get_json()
        
        if 'maintenance_mode' not in data:
            return jsonify({"success": False, "message": "maintenance_mode parameter is required"}), 400
        
        maintenance_mode = data['maintenance_mode']
        
        # Mettre à jour le paramètre de configuration
        current_app.config['MAINTENANCE_MODE'] = maintenance_mode
        
        # Enregistrer dans la base de données pour persistance
        query = text("""
        INSERT INTO app_settings (setting_key, setting_value, updated_at)
        VALUES ('maintenance_mode', :value, NOW())
        ON CONFLICT (setting_key) 
        DO UPDATE SET setting_value = :value, updated_at = NOW()
        """)
        
        db.session.execute(query, {"value": str(maintenance_mode).lower()})
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": f"Maintenance mode {'activated' if maintenance_mode else 'deactivated'} successfully",
            "maintenance_mode": maintenance_mode
        }), 200
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error toggling maintenance mode: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred"}), 500


@admin_bp.route('/tasks/trigger', methods=['POST'])
@jwt_required()
@admin_required
def trigger_task():
    """Déclenche manuellement une tâche planifiée"""
    try:
        data = request.get_json()
        
        if 'task_name' not in data:
            return jsonify({"success": False, "message": "task_name parameter is required"}), 400
        
        task_name = data['task_name']
        task_params = data.get('params', {})
        
        # Importer le gestionnaire de tâches
        from tasks import task_manager
        
        # Déclencher la tâche
        task_id = task_manager.run_task(task_name, task_params)
        
        if not task_id:
            return jsonify({"success": False, "message": f"Task {task_name} not found or could not be started"}), 400
        
        return jsonify({
            "success": True,
            "message": f"Task {task_name} triggered successfully",
            "task_id": task_id
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Error triggering task: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred"}), 500


@admin_bp.route('/logs', methods=['GET'])
@jwt_required()
@admin_required
def get_logs():
    """Récupère les logs de l'application"""
    try:
        # Paramètres de filtrage
        log_level = request.args.get('level', default='INFO')
        limit = request.args.get('limit', default=100, type=int)
        
        # Limiter le nombre de lignes pour éviter les abus
        if limit > 1000:
            limit = 1000
        
        # Lire les logs depuis le fichier
        log_file = current_app.config.get('LOG_FILE', 'app.log')
        
        try:
            with open(log_file, 'r') as f:
                lines = f.readlines()
                
                # Filtrer par niveau de log
                if log_level != 'ALL':
                    lines = [line for line in lines if f" {log_level} " in line]
                
                # Limiter le nombre de lignes
                lines = lines[-limit:]
                
                return jsonify({
                    "success": True,
                    "count": len(lines),
                    "logs": lines
                }), 200
        except FileNotFoundError:
            return jsonify({
                "success": False,
                "message": f"Log file not found at {log_file}"
            }), 404
    
    except Exception as e:
        current_app.logger.error(f"Error retrieving logs: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred"}), 500


@admin_bp.route('/statistics', methods=['GET'])
@jwt_required()
@admin_required
def get_statistics():
    """Récupère des statistiques globales sur l'utilisation de l'application"""
    try:
        # Statistiques prédictions par jour
        predictions_query = text("""
        SELECT 
            DATE(created_at) AS date,
            COUNT(*) AS count
        FROM prediction_usage
        GROUP BY DATE(created_at)
        ORDER BY date DESC
        LIMIT 30
        """)
        
        predictions_result = db.session.execute(predictions_query)
        
        predictions_by_day = []
        for row in predictions_result:
            predictions_by_day.append({
                "date": row.date.isoformat(),
                "count": row.count
            })
        
        # Statistiques simulations par jour
        simulations_query = text("""
        SELECT 
            DATE(used_at) AS date,
            COUNT(*) AS count
        FROM simulation_usage
        GROUP BY DATE(used_at)
        ORDER BY date DESC
        LIMIT 30
        """)
        
        simulations_result = db.session.execute(simulations_query)
        
        simulations_by_day = []
        for row in simulations_result:
            simulations_by_day.append({
                "date": row.date.isoformat(),
                "count": row.count
            })
        
        # Statistiques inscriptions par jour
        registrations_query = text("""
        SELECT 
            DATE(created_at) AS date,
            COUNT(*) AS count
        FROM users
        GROUP BY DATE(created_at)
        ORDER BY date DESC
        LIMIT 30
        """)
        
        registrations_result = db.session.execute(registrations_query)
        
        registrations_by_day = []
        for row in registrations_result:
            registrations_by_day.append({
                "date": row.date.isoformat(),
                "count": row.count
            })
        
        # Statistiques de conversion
        conversion_query = text("""
        WITH user_counts AS (
            SELECT 
                COUNT(*) AS total_users,
                SUM(CASE WHEN subscription_level = 'free' THEN 1 ELSE 0 END) AS free_users,
                SUM(CASE WHEN subscription_level != 'free' THEN 1 ELSE 0 END) AS paid_users
            FROM users
            WHERE is_active = TRUE
        )
        SELECT 
            total_users,
            free_users,
            paid_users,
            CASE WHEN total_users > 0 THEN paid_users * 100.0 / total_users ELSE 0 END AS conversion_rate
        FROM user_counts
        """)
        
        conversion_result = db.session.execute(conversion_query).fetchone()
        
        conversion = {
            "total_users": conversion_result.total_users,
            "free_users": conversion_result.free_users,
            "paid_users": conversion_result.paid_users,
            "conversion_rate": conversion_result.conversion_rate
        }
        
        return jsonify({
            "success": True,
            "data": {
                "predictions_by_day": predictions_by_day,
                "simulations_by_day": simulations_by_day,
                "registrations_by_day": registrations_by_day,
                "conversion": conversion
            }
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Error retrieving statistics: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred"}), 500


@admin_bp.route('/notifications/send', methods=['POST'])
@jwt_required()
@admin_required
def send_admin_notification():
    """Envoie une notification à un utilisateur ou à tous les utilisateurs"""
    try:
        data = request.get_json()
        
        # Validation des données
        if 'title' not in data or 'message' not in data:
            return jsonify({"success": False, "message": "Title and message are required"}), 400
        
        title = data['title']
        message = data['message']
        notification_type = data.get('notification_type', 'system')
        additional_data = data.get('data', {})
        
        # Vérifier si c'est pour un utilisateur spécifique ou tous
        user_id = data.get('user_id')
        send_to_all = data.get('send_to_all', False)
        
        # Filtrage par niveau d'abonnement
        subscription_level = data.get('subscription_level')
        
        # Options d'envoi
        send_email = data.get('send_email', False)
        send_push = data.get('send_push', False)
        
        if user_id:
            # Envoyer à un utilisateur spécifique
            notification_id = notification_service.create_notification(
                user_id=user_id,
                notification_type=notification_type,
                title=title,
                message=message,
                data=additional_data,
                send_email=send_email,
                send_push=send_push
            )
            
            return jsonify({
                "success": True,
                "message": "Notification sent successfully",
                "notification_id": notification_id
            }), 200
            
        elif send_to_all:
            # Envoyer à tous les utilisateurs (ou filtrés par abonnement)
            query = "SELECT id FROM users WHERE is_active = TRUE"
            params = {}
            
            if subscription_level:
                query += " AND subscription_level = :subscription_level"
                params["subscription_level"] = subscription_level
            
            result = db.session.execute(text(query), params)
            
            count = 0
            for row in result:
                notification_service.create_notification(
                    user_id=row.id,
                    notification_type=notification_type,
                    title=title,
                    message=message,
                    data=additional_data,
                    send_email=send_email,
                    send_push=send_push
                )
                count += 1
            
            return jsonify({
                "success": True,
                "message": f"Notification sent to {count} users",
                "count": count
            }), 200
        else:
            return jsonify({"success": False, "message": "Either user_id or send_to_all must be specified"}), 400
    
    except Exception as e:
        current_app.logger.error(f"Error sending admin notification: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred"}), 500