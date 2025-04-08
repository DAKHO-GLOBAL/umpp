# error_handler.py
# api/middleware/error_handler.py
import logging
from flask import jsonify, current_app
from werkzeug.exceptions import HTTPException
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from marshmallow.exceptions import ValidationError
from jwt.exceptions import PyJWTError

logger = logging.getLogger(__name__)

def register_error_handlers(app):
    """Enregistre tous les gestionnaires d'erreurs pour l'application Flask"""
    
    @app.errorhandler(400)
    def bad_request_error(error):
        """Gestionnaire pour les erreurs 400 Bad Request"""
        logger.warning(f"Bad Request Error: {error}")
        return jsonify({
            "success": False,
            "message": "Bad request",
            "details": str(error)
        }), 400
    
    @app.errorhandler(401)
    def unauthorized_error(error):
        """Gestionnaire pour les erreurs 401 Unauthorized"""
        logger.warning(f"Unauthorized Error: {error}")
        return jsonify({
            "success": False,
            "message": "Authentication required",
            "details": str(error)
        }), 401
    
    @app.errorhandler(403)
    def forbidden_error(error):
        """Gestionnaire pour les erreurs 403 Forbidden"""
        logger.warning(f"Forbidden Error: {error}")
        return jsonify({
            "success": False,
            "message": "Access forbidden",
            "details": str(error)
        }), 403
    
    @app.errorhandler(404)
    def not_found_error(error):
        """Gestionnaire pour les erreurs 404 Not Found"""
        logger.warning(f"Not Found Error: {error}")
        return jsonify({
            "success": False,
            "message": "Resource not found",
            "details": str(error)
        }), 404
    
    @app.errorhandler(405)
    def method_not_allowed_error(error):
        """Gestionnaire pour les erreurs 405 Method Not Allowed"""
        logger.warning(f"Method Not Allowed Error: {error}")
        return jsonify({
            "success": False,
            "message": "Method not allowed",
            "details": str(error)
        }), 405
    
    @app.errorhandler(429)
    def too_many_requests_error(error):
        """Gestionnaire pour les erreurs 429 Too Many Requests"""
        logger.warning(f"Rate Limit Exceeded: {error}")
        return jsonify({
            "success": False,
            "message": "Rate limit exceeded",
            "details": str(error)
        }), 429
    
    @app.errorhandler(500)
    def internal_server_error(error):
        """Gestionnaire pour les erreurs 500 Internal Server Error"""
        logger.error(f"Internal Server Error: {error}")
        return jsonify({
            "success": False,
            "message": "Internal server error",
            "details": str(error) if current_app.config['DEBUG'] else "An unexpected error occurred"
        }), 500
    
    @app.errorhandler(ValidationError)
    def validation_error(error):
        """Gestionnaire pour les erreurs de validation Marshmallow"""
        logger.warning(f"Validation Error: {error}")
        return jsonify({
            "success": False,
            "message": "Validation error",
            "errors": error.messages
        }), 400
    
    @app.errorhandler(PyJWTError)
    def jwt_error(error):
        """Gestionnaire pour les erreurs JWT"""
        logger.warning(f"JWT Error: {error}")
        return jsonify({
            "success": False,
            "message": "JWT token error",
            "details": str(error)
        }), 401
    
    @app.errorhandler(IntegrityError)
    def integrity_error(error):
        """Gestionnaire pour les erreurs d'intégrité de la base de données"""
        logger.error(f"Database Integrity Error: {error}")
        return jsonify({
            "success": False,
            "message": "Database integrity error",
            "details": "A database constraint was violated" if not current_app.config['DEBUG'] else str(error)
        }), 400
    
    @app.errorhandler(SQLAlchemyError)
    def sqlalchemy_error(error):
        """Gestionnaire pour les erreurs SQLAlchemy générales"""
        logger.error(f"Database Error: {error}")
        return jsonify({
            "success": False,
            "message": "Database error",
            "details": "A database error occurred" if not current_app.config['DEBUG'] else str(error)
        }), 500
    
    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        """Gestionnaire pour toutes les autres exceptions HTTP"""
        logger.warning(f"HTTP Exception: {error}")
        return jsonify({
            "success": False,
            "message": error.name,
            "details": error.description
        }), error.code
    
    @app.errorhandler(Exception)
    def handle_generic_exception(error):
        """Gestionnaire pour toutes les autres exceptions non gérées"""
        logger.error(f"Unhandled Exception: {error}", exc_info=True)
        return jsonify({
            "success": False,
            "message": "An unexpected error occurred",
            "details": str(error) if current_app.config['DEBUG'] else "Please try again later"
        }), 500
    
    logger.info("Error handlers registered successfully")