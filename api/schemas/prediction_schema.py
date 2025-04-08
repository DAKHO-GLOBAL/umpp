# prediction_schema.py
# prediction_schema.py
# api/schemas/prediction_schema.py
from marshmallow import Schema, fields, validate, validates, ValidationError

class PredictionRequestSchema(Schema):
    """Schéma pour la validation des requêtes de prédiction"""
    course_id = fields.Int(required=True)
    prediction_type = fields.Str(validate=validate.OneOf(['standard', 'top3', 'top7', 'realtime']), default='standard')


class CommentRequestSchema(Schema):
    """Schéma pour la validation des requêtes de commentaires"""
    prediction_id = fields.Int(required=True)
    detailed = fields.Bool(default=False)


class OddsFilterSchema(Schema):
    """Schéma pour le filtrage des cotes dans les prédictions"""
    min_odds = fields.Float(validate=validate.Range(min=1.0), required=False)
    max_odds = fields.Float(validate=validate.Range(min=1.0), required=False)
    
    @validates('max_odds')
    def validate_max_odds(self, value):
        """Validation personnalisée pour les cotes maximales"""
        if 'min_odds' in self.data and value < self.data['min_odds']:
            raise ValidationError('Max odds must be greater than or equal to min odds')


class PredictionFilterSchema(Schema):
    """Schéma pour le filtrage des prédictions"""
    min_probability = fields.Float(validate=validate.Range(min=0.0, max=1.0), required=False)
    max_rank = fields.Int(validate=validate.Range(min=1), required=False)
    odds_filter = fields.Nested(OddsFilterSchema, required=False)


class BettingRequestSchema(Schema):
    """Schéma pour la validation des requêtes de suggestions de paris"""
    prediction_id = fields.Int(required=