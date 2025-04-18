# prediction_routes.py
# api/routes/prediction_routes.py
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.prediction_service import PredictionService
from services.user_service import UserService
from schemas.prediction_schema import PredictionRequestSchema
from middleware.rate_limiter import limiter
from utils.decorators import subscription_required

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
    
    except Exception as e:
        current_app.logger.error(f"Error retrieving prediction history: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred"}), 500


@prediction_bp.route('/<int:prediction_id>', methods=['GET'])
@jwt_required()
def get_prediction(prediction_id):
    """Récupère les détails d'une prédiction spécifique"""
    try:
        user_id = get_jwt_identity()
        
        # Récupérer la prédiction
        prediction = prediction_service.get_prediction_by_id(prediction_id, user_id)
        
        if not prediction:
            return jsonify({"success": False, "message": "Prediction not found"}), 404
        
        return jsonify({
            "success": True,
            "data": prediction
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Error retrieving prediction: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred"}), 500


@prediction_bp.route('/compare/<int:course_id>', methods=['GET'])
@jwt_required()
@subscription_required(['premium'])
def compare_predictions(course_id):
    """Compare les prédictions historiques pour une course"""
    try:
        # Récupérer toutes les prédictions pour cette course
        predictions = prediction_service.get_course_prediction_history(course_id)
        
        if not predictions or len(predictions) < 2:
            return jsonify({
                "success": False, 
                "message": "Not enough predictions available for comparison"
            }), 404
        
        # Comparer les prédictions
        comparison = prediction_service.compare_predictions(predictions)
        
        return jsonify({
            "success": True,
            "course_id": course_id,
            "data": comparison
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Error comparing predictions: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred"}), 500


@prediction_bp.route('/stats', methods=['GET'])
@jwt_required()
@subscription_required(['standard', 'premium'])
def prediction_stats():
    """Statistiques globales sur les prédictions de l'utilisateur"""
    try:
        user_id = get_jwt_identity()
        days = request.args.get('days', default=30, type=int)
        
        # Récupérer les statistiques
        stats = prediction_service.get_user_prediction_stats(user_id, days)
        
        return jsonify({
            "success": True,
            "days": days,
            "stats": stats
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Error retrieving prediction stats: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred"}), 500


@prediction_bp.route('/evaluate/<int:prediction_id>', methods=['GET'])
@jwt_required()
def evaluate_prediction(prediction_id):
    """Évalue une prédiction en la comparant aux résultats réels"""
    try:
        user_id = get_jwt_identity()
        
        # Récupérer et évaluer la prédiction
        evaluation = prediction_service.evaluate_prediction(prediction_id, user_id)
        
        if not evaluation:
            return jsonify({
                "success": False, 
                "message": "Prediction not found or results not available"
            }), 404
        
        return jsonify({
            "success": True,
            "prediction_id": prediction_id,
            "evaluation": evaluation
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Error evaluating prediction: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred"}), 500


@prediction_bp.route('/evaluate/recent', methods=['GET'])
@jwt_required()
@subscription_required(['standard', 'premium'])
def evaluate_recent_predictions():
    """Évalue les prédictions récentes de l'utilisateur pour voir leur précision"""
    try:
        user_id = get_jwt_identity()
        days = request.args.get('days', default=7, type=int)
        
        # Limiter pour éviter les abus
        if days > 30:
            days = 30
        
        # Récupérer et évaluer les prédictions récentes
        evaluations = prediction_service.evaluate_recent_predictions(user_id, days)
        
        return jsonify({
            "success": True,
            "days": days,
            "count": len(evaluations),
            "data": evaluations
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Error evaluating recent predictions: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred"}), 500


@prediction_bp.route('/odds/change/<int:course_id>', methods=['GET'])
@jwt_required()
@subscription_required(['premium'])
def get_odds_change_impact(course_id):
    """Analyse l'impact des changements de cotes sur les prédictions"""
    try:
        # Récupérer l'historique des cotes
        odds_history = prediction_service.get_course_odds_history(course_id)
        
        # Analyser l'impact des changements
        impact_analysis = prediction_service.analyze_odds_change_impact(course_id, odds_history)
        
        return jsonify({
            "success": True,
            "course_id": course_id,
            "data": impact_analysis
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Error analyzing odds impact: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred"}), 500


@prediction_bp.route('/daily-summary', methods=['GET'])
@jwt_required()
@subscription_required(['premium'])
def get_daily_summary():
    """Récupère un résumé des meilleures prédictions du jour"""
    try:
        # Paramètres optionnels
        date_str = request.args.get('date', default=None)
        
        # Récupérer le résumé
        summary = prediction_service.get_daily_prediction_summary(date_str)
        
        return jsonify({
            "success": True,
            "date": date_str if date_str else datetime.now().strftime('%Y-%m-%d'),
            "data": summary
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Error generating daily summary: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred"}), 500