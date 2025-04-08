# simulation_schema.py
# api/schemas/simulation_schema.py
from marshmallow import Schema, fields, validate, validates, ValidationError

class SimulationRequestSchema(Schema):
    """Schéma pour la validation des requêtes de simulation"""
    selected_horses = fields.List(fields.Int(), required=False)
    simulation_params = fields.Dict(required=False)
    horse_modifications = fields.Dict(keys=fields.Int(), values=fields.Dict(), required=False)
    weather_conditions = fields.Dict(required=False)
    track_conditions = fields.Dict(required=False)


class HorseModificationSchema(Schema):
    """Schéma pour la validation des modifications de chevaux"""
    poids = fields.Float(validate=validate.Range(min=0), required=False)
    forme = fields.Int(validate=validate.Range(min=1, max=10), required=False)
    jockey_id = fields.Int(required=False)
    cote_initiale = fields.Float(validate=validate.Range(min=1.0), required=False)


class WeatherConditionSchema(Schema):
    """Schéma pour la validation des conditions météorologiques"""
    weather_type = fields.Str(validate=validate.OneOf([
        'Ensoleillé', 'Peu Nuageux', 'Partiellement Nuageux', 'Nuageux', 
        'Très Nuageux', 'Couvert', 'Brouillard', 'Pluie Légère', 
        'Pluie', 'Forte Pluie', 'Orage'
    ]), required=False)
    temperature = fields.Float(validate=validate.Range(min=-10, max=40), required=False)
    wind_speed = fields.Float(validate=validate.Range(min=0, max=100), required=False)
    wind_direction = fields.Str(validate=validate.OneOf([
        'N', 'NE', 'E', 'SE', 'S', 'SO', 'O', 'NO'
    ]), required=False)


class TrackConditionSchema(Schema):
    """Schéma pour la validation des conditions de piste"""
    terrain = fields.Str(validate=validate.OneOf([
        'Bon', 'Souple', 'Collant', 'Lourd', 'Très Lourd', 'Gelé', 'Sec'
    ]), required=False)
    corde = fields.Str(validate=validate.OneOf([
        'Droite', 'Gauche', 'Sans'
    ]), required=False)
    difficulty = fields.Int(validate=validate.Range(min=1, max=10), required=False)


class AdvancedSimulationRequestSchema(Schema):
    """Schéma pour la validation des requêtes de simulation avancée"""
    selected_horses = fields.List(fields.Int(), required=False)
    horse_modifications = fields.Dict(
        keys=fields.Int(),
        values=fields.Nested(HorseModificationSchema), 
        required=True
    )
    weather_conditions = fields.Nested(WeatherConditionSchema, required=False)
    track_conditions = fields.Nested(TrackConditionSchema, required=False)
    custom_factors = fields.Dict(required=False)


class SimulationComparisonRequestSchema(Schema):
    """Schéma pour la validation des requêtes de comparaison de simulations"""
    scenarios = fields.List(fields.Dict(), validate=validate.Length(min=2, max=5), required=True)


class SimulationAnimationRequestSchema(Schema):
    """Schéma pour la validation des requêtes d'animation de simulation"""
    simulation_id = fields.Int(required=True)
    animation_type = fields.Str(validate=validate.OneOf(['2d', '3d', 'text']), default='2d')
    speed = fields.Float(validate=validate.Range(min=0.5, max=2.0), default=1.0)


class SimulationExportRequestSchema(Schema):
    """Schéma pour la validation des requêtes d'exportation de simulation"""
    simulation_id = fields.Int(required=True)
    format = fields.Str(validate=validate.OneOf(['csv', 'json', 'pdf']), required=True)
    include_details = fields.Bool(default=True)
    include_animation = fields.Bool(default=False)