# auth_routes.py
# api/routes/auth_routes.py
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import (
    create_access_token, create_refresh_token, 
    jwt_required, get_jwt_identity
)
from services.auth_service import AuthService
from schemas.user_schema import UserLoginSchema, UserRegisterSchema
from middleware.rate_limiter import limiter

auth_bp = Blueprint('auth', __name__)
auth_service = AuthService()

# Schémas pour la validation des données
login_schema = UserLoginSchema()
register_schema = UserRegisterSchema()

@auth_bp.route('/register', methods=['POST'])
@limiter.limit("10/hour")
def register():
    """Inscription d'un nouvel utilisateur"""
    data = request.get_json()
    
    # Validation des données
    errors = register_schema.validate(data)
    if errors:
        return jsonify({"success": False, "errors": errors}), 400
    
    try:
        # Création du nouvel utilisateur
        user = auth_service.register_user(
            email=data['email'],
            password=data['password'],
            first_name=data.get('first_name', ''),
            last_name=data.get('last_name', '')
        )
        
        # Créer les tokens JWT
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)
        
        return jsonify({
            "success": True,
            "message": "User registered successfully",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": {
                "id": user.id,
                "email": user.email,
                "name": f"{user.first_name} {user.last_name}",
                "subscription_level": user.subscription_level
            }
        }), 201
    
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Registration error: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred during registration"}), 500


@auth_bp.route('/login', methods=['POST'])
@limiter.limit("20/hour")
def login():
    """Connexion d'un utilisateur existant"""
    data = request.get_json()
    
    # Validation des données
    errors = login_schema.validate(data)
    if errors:
        return jsonify({"success": False, "errors": errors}), 400
    
    try:
        # Vérification des identifiants
        user = auth_service.authenticate_user(data['email'], data['password'])
        
        if not user:
            return jsonify({"success": False, "message": "Invalid credentials"}), 401
        
        # Créer les tokens JWT
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)
        
        return jsonify({
            "success": True,
            "message": "Login successful",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": {
                "id": user.id,
                "email": user.email,
                "name": f"{user.first_name} {user.last_name}",
                "subscription_level": user.subscription_level
            }
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Login error: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred during login"}), 500


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Rafraîchissement du token d'accès"""
    current_user_id = get_jwt_identity()
    new_access_token = create_access_token(identity=current_user_id)
    
    return jsonify({
        "success": True,
        "access_token": new_access_token
    }), 200


@auth_bp.route('/firebase-auth', methods=['POST'])
@limiter.limit("20/hour")
def firebase_auth():
    """Authentification via Firebase"""
    data = request.get_json()
    
    if not data or 'firebase_token' not in data:
        return jsonify({"success": False, "message": "Firebase token is required"}), 400
    
    try:
        # Vérifier le token Firebase et récupérer l'utilisateur
        user = auth_service.authenticate_with_firebase(data['firebase_token'])
        
        # Créer les tokens JWT
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)
        
        return jsonify({
            "success": True,
            "message": "Firebase authentication successful",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": {
                "id": user.id,
                "email": user.email,
                "name": f"{user.first_name} {user.last_name}",
                "subscription_level": user.subscription_level
            }
        }), 200
    
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Firebase auth error: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred during Firebase authentication"}), 500


@auth_bp.route('/forgot-password', methods=['POST'])
@limiter.limit("5/hour")
def forgot_password():
    """Demande de réinitialisation de mot de passe"""
    data = request.get_json()
    
    if not data or 'email' not in data:
        return jsonify({"success": False, "message": "Email is required"}), 400
    
    try:
        # Envoi du mail de réinitialisation
        auth_service.send_password_reset_email(data['email'])
        
        return jsonify({
            "success": True,
            "message": "Password reset email sent if the account exists"
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Password reset error: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred"}), 500


@auth_bp.route('/reset-password', methods=['POST'])
@limiter.limit("5/hour")
def reset_password():
    """Réinitialisation du mot de passe"""
    data = request.get_json()
    
    if not data or 'token' not in data or 'new_password' not in data:
        return jsonify({"success": False, "message": "Token and new password are required"}), 400
    
    try:
        # Réinitialisation du mot de passe
        auth_service.reset_password(data['token'], data['new_password'])
        
        return jsonify({
            "success": True,
            "message": "Password reset successful"
        }), 200
    
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Password reset error: {str(e)}")
        return jsonify({"success": False, "message": "An error occurred during password reset"}), 500