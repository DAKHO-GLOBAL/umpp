# simulation_routes.py
# api/routes/simulation_routes.py
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from api.services.simulation_service import SimulationService
from api.services.user_service import UserService
from api.schemas.simulation_schema import SimulationRequestSchema
from api.middleware.rate_limiter import limiter
from api.utils.decorators import subscription_required

simulation_bp = Blueprint('simulation', __name__)
simulation_service = SimulationService()
user_service = UserService()

# Schémas pour la validation des données
simulation_request_schema = SimulationRequestSchema()

@simulation_bp.route('/basic/<int:course_id>', methods=['POST'])
@jwt_required()
@limiter.limit("50/day")
def basic_simulation(course_id):
    """Simulation de base pour une course avec des chevaux sélectionnés"""
    data = request.get_json()
    
    # Validation des données
    errors = simulation_request_schema.validate(data)
    if errors:
        return jsonify({"success": False, "errors": errors}), 400
    
    try:
        # Vérifier si l'utilisateur a encore des simulations disponibles
        user_id = get_jwt_identity()
        user = user_service.get_user_by_id(user_id)
        
        # Vérifier le niveau d'abonnement et le quota
        subscription_level = user.subscription_level
        quota = current_app.config['SUBSCRIPTION_LEVELS'][subscription_level]['simulations_per_day']
        
        if quota != -1:  # -1 signifie illimité
            # Vérifier le quota utilisé
            used_today = simulation_service.get_simulations_count_today(user_id)
            if used_today >= quota:
                return jsonify({
                    "success": False,
                    "message": f"You have reached your daily limit of {quota} simulations. Upgrade your subscription for more."
                }), 403
        
        # Effectuer la simulation
        selected_horses = data.get('selected_horses', [])
        simulation_params = data.get('simulation_params', {})
        
        simulation = simulation_service.simulate_course(
            course_id, 
            selected_horses=selected_horses, 
            simulation_params=simulation_params,
            simulation_type='basic'
        )
        
        # Enregistrer l'utilisation
        simulation_service.log_simulation_usage(user_id, course_id, 'basic', selected_horses)
        
        return jsonify({
            "success": True,
            "course_id": course_id,
            "simulation_type": "basic",
            "timestamp": simulation['timestamp'],
            "selected_horses": selected_horses,
            "data": simulation['data'],
            "animation_data": simulation.get('animation_data')
        }), 200
    
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error in basic simulation: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred during simulation"}), 500


@simulation_bp.route('/advanced/<int:course_id>', methods=['POST'])
@jwt_required()
@subscription_required(['premium'])
@limiter.limit("100/day")
def advanced_simulation(course_id):
    """Simulation avancée permettant la modification de paramètres des chevaux"""
    data = request.get_json()
    
    # Validation des données
    errors = simulation_request_schema.validate(data)
    if errors:
        return jsonify({"success": False, "errors": errors}), 400
    
    try:
        # Effectuer la simulation avancée
        selected_horses = data.get('selected_horses', [])
        simulation_params = data.get('simulation_params', {})
        
        # Paramètres spécifiques avancés
        horse_modifications = data.get('horse_modifications', {})
        weather_conditions = data.get('weather_conditions', None)
        track_conditions = data.get('track_conditions', None)
        
        simulation = simulation_service.simulate_course(
            course_id, 
            selected_horses=selected_horses, 
            simulation_params=simulation_params,
            horse_modifications=horse_modifications,
            weather_conditions=weather_conditions,
            track_conditions=track_conditions,
            simulation_type='advanced'
        )
        
        # Enregistrer l'utilisation
        user_id = get_jwt_identity()
        simulation_service.log_simulation_usage(user_id, course_id, 'advanced', selected_horses)
        
        # Générer une analyse des modifications
        impact_analysis = simulation_service.analyze_parameter_impact(
            course_id, 
            selected_horses, 
            horse_modifications,
            simulation['data']
        )
        
        return jsonify({
            "success": True,
            "course_id": course_id,
            "simulation_type": "advanced",
            "timestamp": simulation['timestamp'],
            "selected_horses": selected_horses,
            "modifications": horse_modifications,
            "weather": weather_conditions,
            "track": track_conditions,
            "data": simulation['data'],
            "impact_analysis": impact_analysis,
            "animation_data": simulation.get('animation_data')
        }), 200
    
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error in advanced simulation: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred during advanced simulation"}), 500


@simulation_bp.route('/compare/<int:course_id>', methods=['POST'])
@jwt_required()
@subscription_required(['premium'])
def compare_simulations(course_id):
    """Compare plusieurs scénarios de simulation"""
    data = request.get_json()
    
    if not data or 'scenarios' not in data or not isinstance(data['scenarios'], list):
        return jsonify({"success": False, "message": "Scenarios list is required"}), 400
    
    try:
        # Limiter le nombre de scénarios pour éviter les abus
        scenarios = data['scenarios'][:5]  # Maximum 5 scénarios à comparer
        
        # Effectuer les simulations et les comparer
        comparison = simulation_service.compare_multiple_scenarios(course_id, scenarios)
        
        # Enregistrer l'utilisation (compte comme une seule simulation avancée)
        user_id = get_jwt_identity()
        simulation_service.log_simulation_usage(user_id, course_id, 'comparison', [])
        
        return jsonify({
            "success": True,
            "course_id": course_id,
            "simulation_type": "comparison",
            "timestamp": comparison['timestamp'],
            "scenarios_count": len(scenarios),
            "data": comparison['data'],
            "comparative_analysis": comparison['analysis']
        }), 200
    
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error in simulation comparison: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred during simulation comparison"}), 500


@simulation_bp.route('/animation/<int:simulation_id>', methods=['GET'])
@jwt_required()
def get_simulation_animation(simulation_id):
    """Récupère les données pour l'animation d'une simulation"""
    try:
        # Récupérer les données d'animation
        animation_data = simulation_service.get_simulation_animation(simulation_id)
        
        if not animation_data:
            return jsonify({"success": False, "message": "Animation data not found"}), 404
        
        return jsonify({
            "success": True,
            "simulation_id": simulation_id,
            "animation_data": animation_data
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Error retrieving animation data: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred"}), 500


@simulation_bp.route('/history', methods=['GET'])
@jwt_required()
def simulation_history():
    """Historique des simulations de l'utilisateur"""
    try:
        user_id = get_jwt_identity()
        
        # Paramètres de pagination
        page = request.args.get('page', default=1, type=int)
        per_page = request.args.get('per_page', default=10, type=int)
        
        # Récupérer l'historique des simulations
        history = simulation_service.get_user_simulation_history(user_id, page, per_page)
        
        return jsonify({
            "success": True,
            "count": history['count'],
            "page": page,
            "per_page": per_page,
            "total_pages": history['total_pages'],
            "data": history['data']
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Error retrieving simulation history: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred"}), 500


@simulation_bp.route('/<int:simulation_id>', methods=['GET'])
@jwt_required()
def get_simulation(simulation_id):
    """Récupère les détails d'une simulation spécifique"""
    try:
        user_id = get_jwt_identity()
        
        # Récupérer la simulation
        simulation = simulation_service.get_simulation_by_id(simulation_id, user_id)
        
        if not simulation:
            return jsonify({"success": False, "message": "Simulation not found"}), 404
        
        return jsonify({
            "success": True,
            "data": simulation
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Error retrieving simulation: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred"}), 500