# user_schema.py
# user_schema.py
# api/schemas/user_schema.py
from marshmallow import Schema, fields, validate, validates, ValidationError
import re

class UserLoginSchema(Schema):
    """Schéma pour la validation des données de connexion"""
    email = fields.Email(required=True, error_messages={
        'required': 'Email is required',
        'invalid': 'Invalid email format'
    })
    password = fields.Str(required=True, validate=validate.Length(min=6), error_messages={
        'required': 'Password is required',
        'validator_failed': 'Password must be at least 6 characters long'
    })
    remember_me = fields.Bool(missing=False)


class UserRegisterSchema(Schema):
    """Schéma pour la validation des données d'inscription"""
    email = fields.Email(required=True, error_messages={
        'required': 'Email is required',
        'invalid': 'Invalid email format'
    })
    username = fields.Str(required=True, validate=validate.Length(min=3, max=30), error_messages={
        'required': 'Username is required',
        'validator_failed': 'Username must be between 3 and 30 characters'
    })
    password = fields.Str(required=True, validate=validate.Length(min=8), error_messages={
        'required': 'Password is required',
        'validator_failed': 'Password must be at least 8 characters long'
    })
    confirm_password = fields.Str(required=True, error_messages={
        'required': 'Password confirmation is required'
    })
    first_name = fields.Str(validate=validate.Length(max=50), allow_none=True)
    last_name = fields.Str(validate=validate.Length(max=50), allow_none=True)
    
    @validates('username')
    def validate_username(self, value):
        """Validation personnalisée pour le nom d'utilisateur"""
        # Vérifier que le nom d'utilisateur ne contient que des caractères alphanumériques et underscore
        if not re.match(r'^[a-zA-Z0-9_]+$', value):
            raise ValidationError('Username can only contain letters, numbers and underscores')
    
    @validates('password')
    def validate_password(self, value):
        """Validation personnalisée pour le mot de passe"""
        # Vérifier que le mot de passe contient au moins une lettre majuscule, une lettre minuscule et un chiffre
        if not re.search(r'[A-Z]', value):
            raise ValidationError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', value):
            raise ValidationError('Password must contain at least one lowercase letter')
        if not re.search(r'[0-9]', value):
            raise ValidationError('Password must contain at least one number')
    
    @validates('confirm_password')
    def validate_confirm_password(self, value):
        """Validation personnalisée pour la confirmation de mot de passe"""
        # Vérifier que les deux mots de passe correspondent
        if 'password' in self.data and value != self.data['password']:
            raise ValidationError('Passwords do not match')


class UserProfileSchema(Schema):
    """Schéma pour la validation des données de profil utilisateur"""
    first_name = fields.Str(validate=validate.Length(max=50), allow_none=True)
    last_name = fields.Str(validate=validate.Length(max=50), allow_none=True)
    bio = fields.Str(validate=validate.Length(max=500), allow_none=True)
    username = fields.Str(validate=validate.Length(min=3, max=30), allow_none=True)
    
    @validates('username')
    def validate_username(self, value):
        """Validation personnalisée pour le nom d'utilisateur"""
        if value is None:
            return
        # Vérifier que le nom d'utilisateur ne contient que des caractères alphanumériques et underscore
        if not re.match(r'^[a-zA-Z0-9_]+$', value):
            raise ValidationError('Username can only contain letters, numbers and underscores')


class UserPasswordChangeSchema(Schema):
    """Schéma pour la validation du changement de mot de passe"""
    current_password = fields.Str(required=True, error_messages={
        'required': 'Current password is required'
    })
    new_password = fields.Str(required=True, validate=validate.Length(min=8), error_messages={
        'required': 'New password is required',
        'validator_failed': 'New password must be at least 8 characters long'
    })
    confirm_password = fields.Str(required=True, error_messages={
        'required': 'Password confirmation is required'
    })
    
    @validates('new_password')
    def validate_new_password(self, value):
        """Validation personnalisée pour le nouveau mot de passe"""
        # Vérifier que le mot de passe contient au moins une lettre majuscule, une lettre minuscule et un chiffre
        if not re.search(r'[A-Z]', value):
            raise ValidationError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', value):
            raise ValidationError('Password must contain at least one lowercase letter')
        if not re.search(r'[0-9]', value):
            raise ValidationError('Password must contain at least one number')
        
        # Vérifier que le nouveau mot de passe est différent de l'ancien
        if 'current_password' in self.data and value == self.data['current_password']:
            raise ValidationError('New password must be different from current password')
    
    @validates('confirm_password')
    def validate_confirm_password(self, value):
        """Validation personnalisée pour la confirmation de mot de passe"""
        # Vérifier que les deux mots de passe correspondent
        if 'new_password' in self.data and value != self.data['new_password']:
            raise ValidationError('Passwords do not match')


class PasswordResetRequestSchema(Schema):
    """Schéma pour la validation de la demande de réinitialisation de mot de passe"""
    email = fields.Email(required=True, error_messages={
        'required': 'Email is required',
        'invalid': 'Invalid email format'
    })


class PasswordResetSchema(Schema):
    """Schéma pour la validation de la réinitialisation de mot de passe"""
    token = fields.Str(required=True, error_messages={
        'required': 'Token is required'
    })
    new_password = fields.Str(required=True, validate=validate.Length(min=8), error_messages={
        'required': 'New password is required',
        'validator_failed': 'New password must be at least 8 characters long'
    })
    confirm_password = fields.Str(required=True, error_messages={
        'required': 'Password confirmation is required'
    })
    
    @validates('new_password')
    def validate_new_password(self, value):
        """Validation personnalisée pour le nouveau mot de passe"""
        # Vérifier que le mot de passe contient au moins une lettre majuscule, une lettre minuscule et un chiffre
        if not re.search(r'[A-Z]', value):
            raise ValidationError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', value):
            raise ValidationError('Password must contain at least one lowercase letter')
        if not re.search(r'[0-9]', value):
            raise ValidationError('Password must contain at least one number')
    
    @validates('confirm_password')
    def validate_confirm_password(self, value):
        """Validation personnalisée pour la confirmation de mot de passe"""
        # Vérifier que les deux mots de passe correspondent
        if 'new_password' in self.data and value != self.data['new_password']:
            raise ValidationError('Passwords do not match')


class EmailVerificationSchema(Schema):
    """Schéma pour la validation de la vérification d'email"""
    token = fields.Str(required=True, error_messages={
        'required': 'Verification token is required'
    })


class UserPreferencesSchema(Schema):
    """Schéma pour la validation des préférences utilisateur"""
    favorite_racetracks = fields.List(fields.Str(), allow_none=True)
    favorite_jockeys = fields.List(fields.Str(), allow_none=True)
    favorite_horses = fields.List(fields.Str(), allow_none=True)
    dark_mode = fields.Bool(allow_none=True)
    language = fields.Str(validate=validate.OneOf(['fr', 'en']), allow_none=True)
    notifications_enabled = fields.Bool(allow_none=True)
    default_prediction_type = fields.Str(validate=validate.OneOf(['standard', 'top3', 'top7']), allow_none=True)


class AdminUserUpdateSchema(Schema):
    """Schéma pour la validation des mises à jour d'utilisateur par un administrateur"""
    email = fields.Email(allow_none=True)
    username = fields.Str(validate=validate.Length(min=3, max=30), allow_none=True)
    first_name = fields.Str(validate=validate.Length(max=50), allow_none=True)
    last_name = fields.Str(validate=validate.Length(max=50), allow_none=True)
    is_active = fields.Bool(allow_none=True)
    is_admin = fields.Bool(allow_none=True)
    is_verified = fields.Bool(allow_none=True)
    subscription_level = fields.Str(validate=validate.OneOf(['free', 'standard', 'premium']), allow_none=True)
    subscription_expiry = fields.DateTime(allow_none=True)
    
    @validates('username')
    def validate_username(self, value):
        """Validation personnalisée pour le nom d'utilisateur"""
        if value is None:
            return
        # Vérifier que le nom d'utilisateur ne contient que des caractères alphanumériques et underscore
        if not re.match(r'^[a-zA-Z0-9_]+$', value):
            raise ValidationError('Username can only contain letters, numbers and underscores')