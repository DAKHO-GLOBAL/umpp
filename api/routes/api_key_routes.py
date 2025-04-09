# api_key_routes.py
# api/routes/api_key_routes.py
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models.api_key import ApiKey
from utils.decorators import admin_required, subscription_required
from middleware.rate_limiter import limiter
from sqlalchemy import desc

api_key_bp = Blueprint('api_key', __name__)

@api_key_bp.route('/', methods=['GET'])
@jwt_required()
def get_api_keys():
    """Récupère les clés API de l'utilisateur"""
    try:
        user_id = get_jwt_identity()
        
        # Récupérer les clés API de l'utilisateur
        keys = ApiKey.query.filter_by(user_id=user_id).order_by(desc(ApiKey.created_at)).all()
        
        api_keys = []
        for key in keys:
            # Masquer la clé complète pour des raisons de sécurité
            masked_key = key.key[:8] + '...' + key.key[-4:]
            
            api_keys.append({
                "id": key.id,
                "key": masked_key,
                "name": key.name,
                "description": key.description,
                "is_active": key.is_active,
                "expiry_date": key.expiry_date.isoformat() if key.expiry_date else None,
                "created_at": key.created_at.isoformat(),
                "last_used_at": key.last_used_at.isoformat() if key.last_used_at else None,
                "usage_count": key.usage_count
            })
        
        return jsonify({
            "success": True,
            "count": len(api_keys),
            "data": api_keys
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Error retrieving API keys: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred"}), 500


@api_key_bp.route('/', methods=['POST'])
@jwt_required()
@subscription_required(['standard', 'premium'])
@limiter.limit("5/day")
def create_api_key():
    """Crée une nouvelle clé API pour l'utilisateur"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({"success": False, "message": "No data provided"}), 400
        
        # Validation des données
        name = data.get('name')
        if not name:
            return jsonify({"success": False, "message": "Name is required"}), 400
        
        description = data.get('description')
        expiry_days = data.get('expiry_days')
        
        # Vérifier le nombre maximum de clés API par utilisateur
        keys_count = ApiKey.query.filter_by(user_id=user_id).count()
        max_keys = current_app.config.get('MAX_API_KEYS_PER_USER', 5)
        
        if keys_count >= max_keys:
            return jsonify({
                "success": False,
                "message": f"Maximum number of API keys ({max_keys}) reached"
            }), 403
        
        # Créer la nouvelle clé API
        api_key = ApiKey.generate_for_user(
            user_id=user_id,
            name=name,
            description=description,
            expiry_days=expiry_days
        )
        
        # Retourner la clé complète une seule fois lors de la création
        return jsonify({
            "success": True,
            "message": "API key created successfully",
            "data": {
                "id": api_key.id,
                "key": api_key.key,  # Clé complète (seulement à la création)
                "name": api_key.name,
                "description": api_key.description,
                "expiry_date": api_key.expiry_date.isoformat() if api_key.expiry_date else None,
                "created_at": api_key.created_at.isoformat()
            }
        }), 201
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating API key: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred"}), 500


@api_key_bp.route('/<int:key_id>', methods=['PUT'])
@jwt_required()
def update_api_key(key_id):
    """Met à jour une clé API existante"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({"success": False, "message": "No data provided"}), 400
        
        # Récupérer la clé API
        api_key = ApiKey.query.filter_by(id=key_id, user_id=user_id).first()
        
        if not api_key:
            return jsonify({
                "success": False,
                "message": "API key not found or does not belong to this user"
            }), 404
        
        # Mettre à jour les champs modifiables
        if 'name' in data:
            api_key.name = data['name']
        
        if 'description' in data:
            api_key.description = data['description']
        
        if 'is_active' in data:
            api_key.is_active = data['is_active']
        
        if 'expiry_days' in data and data['expiry_days']:
            # Prolonger l'expiration
            api_key.extend_expiry(data['expiry_days'])
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "API key updated successfully",
            "data": {
                "id": api_key.id,
                "name": api_key.name,
                "description": api_key.description,
                "is_active": api_key.is_active,
                "expiry_date": api_key.expiry_date.isoformat() if api_key.expiry_date else None,
                "last_used_at": api_key.last_used_at.isoformat() if api_key.last_used_at else None
            }
        }), 200
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating API key: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred"}), 500


@api_key_bp.route('/<int:key_id>', methods=['DELETE'])
@jwt_required()
def delete_api_key(key_id):
    """Supprime une clé API"""
    try:
        user_id = get_jwt_identity()
        
        # Récupérer la clé API
        api_key = ApiKey.query.filter_by(id=key_id, user_id=user_id).first()
        
        if not api_key:
            return jsonify({
                "success": False,
                "message": "API key not found or does not belong to this user"
            }), 404
        
        # Supprimer la clé API
        db.session.delete(api_key)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "API key deleted successfully"
        }), 200
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting API key: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred"}), 500


@api_key_bp.route('/<int:key_id>/activate', methods=['POST'])
@jwt_required()
def activate_api_key(key_id):
    """Active une clé API"""
    try:
        user_id = get_jwt_identity()
        
        # Récupérer la clé API
        api_key = ApiKey.query.filter_by(id=key_id, user_id=user_id).first()
        
        if not api_key:
            return jsonify({
                "success": False,
                "message": "API key not found or does not belong to this user"
            }), 404
        
        # Activer la clé API
        api_key.reactivate()
        
        return jsonify({
            "success": True,
            "message": "API key activated successfully"
        }), 200
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error activating API key: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred"}), 500


@api_key_bp.route('/<int:key_id>/deactivate', methods=['POST'])
@jwt_required()
def deactivate_api_key(key_id):
    """Désactive une clé API"""
    try:
        user_id = get_jwt_identity()
        
        # Récupérer la clé API
        api_key = ApiKey.query.filter_by(id=key_id, user_id=user_id).first()
        
        if not api_key:
            return jsonify({
                "success": False,
                "message": "API key not found or does not belong to this user"
            }), 404
        
        # Désactiver la clé API
        api_key.deactivate()
        
        return jsonify({
            "success": True,
            "message": "API key deactivated successfully"
        }), 200
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deactivating API key: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred"}), 500


@api_key_bp.route('/verify', methods=['POST'])
def verify_api_key():
    """Vérifie la validité d'une clé API (pour les tests)"""
    try:
        data = request.get_json()
        
        if not data or 'key' not in data:
            return jsonify({"success": False, "message": "API key is required"}), 400
        
        api_key = data.get('key')
        
        # Récupérer la clé API
        key_obj = ApiKey.query.filter_by(key=api_key, is_active=True).first()
        
        if not key_obj:
            return jsonify({
                "success": False,
                "message": "Invalid API key"
            }), 403
        
        # Vérifier si la clé API a expiré
        if key_obj.is_expired():
            return jsonify({
                "success": False,
                "message": "API key has expired"
            }), 403
        
        # Mettre à jour la dernière utilisation
        key_obj.update_last_used()
        
        return jsonify({
            "success": True,
            "message": "API key is valid",
            "data": {
                "user_id": key_obj.user_id,
                "name": key_obj.name,
                "expiry_date": key_obj.expiry_date.isoformat() if key_obj.expiry_date else None
            }
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Error verifying API key: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred"}), 500