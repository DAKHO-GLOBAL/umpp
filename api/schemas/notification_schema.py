# notification_schema.py
# api/schemas/notification_schema.py
from marshmallow import Schema, fields, validate, ValidationError

class NotificationSchema(Schema):
    """Schéma pour la validation des notifications"""
    id = fields.Int(dump_only=True)
    notification_type = fields.Str(required=True, validate=validate.OneOf([
        'prediction', 'odds_change', 'upcoming_course', 'system', 'test'
    ]))
    title = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    message = fields.Str(required=True, validate=validate.Length(min=1, max=1000))
    data = fields.Dict(allow_none=True)
    read = fields.Bool(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class NotificationSettingsSchema(Schema):
    """Schéma pour la validation des paramètres de notification"""
    email_notifications = fields.Bool(required=True)
    push_notifications = fields.Bool(required=True)
    notify_predictions = fields.Bool(required=True)
    notify_odds_changes = fields.Bool(required=True)
    notify_upcoming_races = fields.Bool(required=True)
    min_minutes_before_race = fields.Int(required=True, validate=validate.Range(min=0, max=1440))


class DeviceRegistrationSchema(Schema):
    """Schéma pour la validation de l'enregistrement d'un appareil"""
    device_token = fields.Str(required=True, validate=validate.Length(min=16, max=512))
    device_type = fields.Str(required=True, validate=validate.OneOf(['android', 'ios', 'web', 'desktop', 'unknown']))
    device_name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    notification_enabled = fields.Bool(default=True)