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
    prediction_id = fields.Int(required=True)
    bet_type = fields.Str(validate=validate.OneOf([
        'simple_gagnant', 'simple_place', 'couple_ordre', 'couple_desordre',
        'tierce_ordre', 'tierce_desordre', 'quarte_ordre', 'quarte_desordre',
        'quinte_ordre', 'quinte_desordre', 'top7'
    ]), required=True)
    stake = fields.Float(validate=validate.Range(min=1.0), required=False)


class PredictionCompareSchema(Schema):
    """Schéma pour la validation des requêtes de comparaison de prédictions"""
    course_id = fields.Int(required=True)
    prediction_ids = fields.List(fields.Int(), validate=validate.Length(min=2), required=True)


class PredictionExportSchema(Schema):
    """Schéma pour la validation des requêtes d'exportation de prédictions"""
    prediction_id = fields.Int(required=True)
    format = fields.Str(validate=validate.OneOf(['csv', 'json', 'pdf']), required=True)
    include_comments = fields.Bool(default=True)
    include_odds = fields.Bool(default=True)
    include_statistics = fields.Bool(default=False)


class PredictionAnalysisRequestSchema(Schema):
    """Schéma pour la validation des requêtes d'analyse de prédictions"""
    prediction_id = fields.Int(required=True)
    analysis_type = fields.Str(validate=validate.OneOf([
        'basic', 'detailed', 'statistical', 'comparison', 'historical'
    ]), required=True)
    include_factors = fields.Bool(default=False)
    compare_with_bookmakers = fields.Bool(default=False)


class EvaluationRequestSchema(Schema):
    """Schéma pour la validation des requêtes d'évaluation de prédictions"""
    prediction_id = fields.Int(required=True)
    actual_results = fields.List(fields.Int(), required=False)  # Optionnel si les résultats sont déjà en base


class EvaluationFilterSchema(Schema):
    """Schéma pour le filtrage des évaluations"""
    from_date = fields.Date(required=False)
    to_date = fields.Date(required=False)
    min_accuracy = fields.Float(validate=validate.Range(min=0.0, max=1.0), required=False)
    bet_type = fields.Str(validate=validate.OneOf([
        'simple_gagnant', 'simple_place', 'couple_ordre', 'couple_desordre',
        'tierce_ordre', 'tierce_desordre', 'quarte_ordre', 'quarte_desordre',
        'quinte_ordre', 'quinte_desordre', 'top7'
    ]), required=False)


class DailyPredictionRequestSchema(Schema):
    """Schéma pour la validation des requêtes de prédictions journalières"""
    date = fields.Date(required=False)
    prediction_types = fields.List(
        fields.Str(validate=validate.OneOf(['standard', 'top3', 'top7', 'realtime'])),
        required=False
    )
    tracks = fields.List(fields.Str(), required=False)
    limit = fields.Int(validate=validate.Range(min=1, max=50), required=False)