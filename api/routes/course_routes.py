# course_routes.py
# api/routes/course_routes.py
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.course_service import CourseService
from middleware.rate_limiter import limiter
from utils.decorators import subscription_required

course_bp = Blueprint('course', __name__)
course_service = CourseService()

@course_bp.route('/upcoming', methods=['GET'])
@jwt_required()
def get_upcoming_courses():
    """Récupère la liste des courses à venir"""
    try:
        # Paramètres de filtrage et pagination
        days = request.args.get('days', default=1, type=int)
        page = request.args.get('page', default=1, type=int)
        per_page = request.args.get('per_page', default=20, type=int)
        
        # Limiter pour éviter les abus
        if days > 7:
            days = 7
        
        # Récupérer les courses
        courses = course_service.get_upcoming_courses(days, page, per_page)
        
        return jsonify({
            "success": True,
            "count": courses['count'],
            "page": page,
            "per_page": per_page,
            "total_pages": courses['total_pages'],
            "data": courses['data']
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Error retrieving upcoming courses: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred"}), 500


@course_bp.route('/<int:course_id>', methods=['GET'])
@jwt_required()
def get_course_details(course_id):
    """Récupère les détails d'une course spécifique"""
    try:
        # Récupérer les détails de la course
        course = course_service.get_course_by_id(course_id)
        
        if not course:
            return jsonify({"success": False, "message": "Course not found"}), 404
        
        return jsonify({
            "success": True,
            "data": course
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Error retrieving course details: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred"}), 500


@course_bp.route('/<int:course_id>/participants', methods=['GET'])
@jwt_required()
def get_course_participants(course_id):
    """Récupère la liste des participants à une course"""
    try:
        # Récupérer les participants
        participants = course_service.get_course_participants(course_id)
        
        return jsonify({
            "success": True,
            "course_id": course_id,
            "count": len(participants),
            "data": participants
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Error retrieving course participants: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred"}), 500


@course_bp.route('/<int:course_id>/odds', methods=['GET'])
@jwt_required()
def get_course_odds(course_id):
    """Récupère les cotes des participants à une course"""
    try:
        # Récupérer les cotes
        odds = course_service.get_course_odds(course_id)
        
        return jsonify({
            "success": True,
            "course_id": course_id,
            "timestamp": odds['timestamp'],
            "data": odds['data']
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Error retrieving course odds: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred"}), 500


@course_bp.route('/<int:course_id>/odds/history', methods=['GET'])
@jwt_required()
@subscription_required(['standard', 'premium'])
def get_course_odds_history(course_id):
    """Récupère l'historique des cotes pour une course"""
    try:
        # Récupérer l'historique des cotes
        history = course_service.get_course_odds_history(course_id)
        
        return jsonify({
            "success": True,
            "course_id": course_id,
            "count": len(history),
            "data": history
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Error retrieving odds history: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred"}), 500


@course_bp.route('/<int:course_id>/results', methods=['GET'])
@jwt_required()
def get_course_results(course_id):
    """Récupère les résultats d'une course terminée"""
    try:
        # Récupérer les résultats
        results = course_service.get_course_results(course_id)
        
        if not results:
            return jsonify({"success": False, "message": "Results not available for this course"}), 404
        
        return jsonify({
            "success": True,
            "course_id": course_id,
            "data": results
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Error retrieving course results: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred"}), 500


@course_bp.route('/<int:course_id>/photos', methods=['GET'])
@jwt_required()
@subscription_required(['standard', 'premium'])
def get_course_photos(course_id):
    """Récupère les photos d'arrivée d'une course"""
    try:
        # Récupérer les photos
        photos = course_service.get_course_photos(course_id)
        
        if not photos:
            return jsonify({"success": False, "message": "Photos not available for this course"}), 404
        
        return jsonify({
            "success": True,
            "course_id": course_id,
            "count": len(photos),
            "data": photos
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Error retrieving course photos: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred"}), 500


@course_bp.route('/<int:course_id>/comments', methods=['GET'])
@jwt_required()
def get_course_comments(course_id):
    """Récupère les commentaires officiels d'une course"""
    try:
        # Récupérer les commentaires
        comments = course_service.get_course_comments(course_id)
        
        if not comments:
            return jsonify({"success": False, "message": "Comments not available for this course"}), 404
        
        return jsonify({
            "success": True,
            "course_id": course_id,
            "data": comments
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Error retrieving course comments: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred"}), 500


@course_bp.route('/search', methods=['GET'])
@jwt_required()
@limiter.limit("100/day")
def search_courses():
    """Recherche de courses selon divers critères"""
    try:
        # Paramètres de recherche
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        hippodrome = request.args.get('hippodrome')
        course_type = request.args.get('type')
        cheval_id = request.args.get('cheval_id', type=int)
        jockey_id = request.args.get('jockey_id', type=int)
        
        # Pagination
        page = request.args.get('page', default=1, type=int)
        per_page = request.args.get('per_page', default=20, type=int)
        
        # Effectuer la recherche
        search_results = course_service.search_courses(
            date_from=date_from,
            date_to=date_to,
            hippodrome=hippodrome,
            course_type=course_type,
            cheval_id=cheval_id,
            jockey_id=jockey_id,
            page=page,
            per_page=per_page
        )
        
        return jsonify({
            "success": True,
            "count": search_results['count'],
            "page": page,
            "per_page": per_page,
            "total_pages": search_results['total_pages'],
            "data": search_results['data']
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Error searching courses: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred"}), 500