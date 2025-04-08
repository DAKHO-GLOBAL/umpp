# prediction_routes.py
# api/routes/prediction_routes.py
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from api.services.prediction_service import PredictionService
from api.services.user_service import UserService
from api.schemas.prediction_schema import PredictionRequestSchema
from api.middleware.rate_limiter import limiter
from api.utils.decorators import subscription_required

prediction_bp = Blueprint('prediction', __name__)
prediction_service = PredictionService()
user_service = UserService()

# Schémas pour la validation des données
prediction_request_schema = PredictionRequestSchema()

@prediction_bp.route('/upcoming', methods=['GET'])
@jwt_required()
def upcoming_races():
    """Récupère les courses à venir"""
    try:
        # Paramètres optionnels
        days_ahead = request.args.get('days', default=1, type=int)
        
        # Limite pour éviter les abus
        if days_ahead > 7:
            days_ahead = 7
        
        # Récupérer les courses à venir
        upcoming = prediction_service.get_upcoming_races(days_ahead)
        
        return jsonify({
            "success": True,
            "count": len(upcoming),
            "data": upcoming
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Error fetching upcoming races: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred"}), 500


@prediction_bp.route('/standard/<int:course_id>', methods=['GET'])
@jwt_required()
@limiter.limit("100/day")
def standard_prediction(course_id):
    """Prédiction standard pour une course (top 3)"""
    try:
        # Vérifier si l'utilisateur a encore des prédictions disponibles
        user_id = get_jwt_identity()
        user = user_service.get_user_by_id(user_id)
        
        # Vérifier le niveau d'abonnement et le quota
        subscription_level = user.subscription_level
        quota = current_app.config['SUBSCRIPTION_LEVELS'][subscription_level]['predictions_per_day']
        
        if quota != -1:  # -1 signifie illimité
            # Vérifier le quota utilisé
            used_today = prediction_service.get_predictions_count_today(user_id)
            if used_today >= quota:
                return jsonify({
                    "success": False,
                    "message": f"You have reached your daily limit of {quota} predictions. Upgrade your subscription for more."
                }), 403
        
        # Effectuer la prédiction
        prediction = prediction_service.predict_course(course_id, prediction_type='standard')
        
        # Enregistrer l'utilisation
        prediction_service.log_prediction_usage(user_id, course_id, 'standard')
        
        return jsonify({
            "success": True,
            "course_id": course_id,
            "prediction_type": "standard",
            "timestamp": prediction['timestamp'],
            "data": prediction['data']
        }), 200
    
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error making standard prediction: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred"}), 500


@prediction_bp.route('/top3/<int:course_id>', methods=['GET'])
@jwt_required()
@subscription_required(['standard', 'premium'])
@limiter.limit("150/day")
def top3_prediction(course_id):
    """Prédiction des 3 premiers de la course avec probabilités détaillées"""
    try:
        # Effectuer la prédiction
        prediction = prediction_service.predict_course(course_id, prediction_type='top3')
        
        # Enregistrer l'utilisation
        user_id = get_jwt_identity()
        prediction_service.log_prediction_usage(user_id, course_id, 'top3')
        
        # Ajouter les commentaires automatisés
        comments = prediction_service.generate_prediction_comments(prediction['data'])
        
        return jsonify({
            "success": True,
            "course_id": course_id,
            "prediction_type": "top3",
            "timestamp": prediction['timestamp'],
            "data": prediction['data'],
            "comments": comments
        }), 200
    
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error making top3 prediction: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred"}), 500


@prediction_bp.route('/top7/<int:course_id>', methods=['GET'])
@jwt_required()
@subscription_required(['premium'])
@limiter.limit("200/day")
def top7_prediction(course_id):
    """Prédiction complète du top 7 (premium)"""
    try:
        # Effectuer la prédiction
        prediction = prediction_service.predict_course(course_id, prediction_type='top7')
        
        # Enregistrer l'utilisation
        user_id = get_jwt_identity()
        prediction_service.log_prediction_usage(user_id, course_id, 'top7')
        
        # Ajouter les commentaires automatisés et suggestions de paris
        comments = prediction_service.generate_prediction_comments(prediction['data'], detailed=True)
        betting_suggestions = prediction_service.generate_betting_suggestions(prediction['data'])
        
        return jsonify({
            "success": True,
            "course_id": course_id,
            "prediction_type": "top7",
            "timestamp": prediction['timestamp'],
            "data": prediction['data'],
            "comments": comments,
            "betting_suggestions": betting_suggestions
        }), 200
    
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error making top7 prediction: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred"}), 500


@prediction_bp.route('/realtime/<int:course_id>', methods=['GET'])
@jwt_required()
@subscription_required(['premium'])
def realtime_prediction(course_id):
    """Prédictions en temps réel avec les dernières cotes"""
    try:
        # Récupérer les dernières cotes
        latest_odds = prediction_service.get_latest_odds(course_id)
        
        # Faire la prédiction avec les dernières données
        prediction = prediction_service.predict_course_realtime(course_id, latest_odds)
        
        # Comparer avec les prédictions précédentes pour détecter les changements
        changes = prediction_service.detect_prediction_changes(course_id, prediction['data'])
        
        return jsonify({
            "success": True,
            "course_id": course_id,
            "prediction_type": "realtime",
            "timestamp": prediction['timestamp'],
            "data": prediction['data'],
            "changes": changes
        }), 200
    
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error making realtime prediction: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred"}), 500


@prediction_bp.route('/history', methods=['GET'])
@jwt_required()
def prediction_history():
    """Historique des prédictions de l'utilisateur"""
    try:
        user_id = get_jwt_identity()
        
        # Paramètres de pagination
        page = request.args.get('page', default=1, type=int)
        per_page = request.args.get('per_page', default=10, type=int)
        
        # Récupérer l'historique des prédictions
        history = prediction_service.get_user_prediction_history(user_id, page, per_page)
        
        return jsonify({
            "success": True,
            "count": history['count'],
            "page": page,
            "per_page": per_page,
            "total_pages": history['total_pages'],
            "data": history['data']
        }), 200