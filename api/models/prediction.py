# prediction.py
# prediction.py
# api/models/prediction.py
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from extensions import db

class Prediction(db.Model):
    """Modèle pour les prédictions de courses"""
    __tablename__ = 'predictions'
    
    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey('courses.id'), nullable=False)
    prediction_type = Column(String(20), nullable=False)  # standard, top3, top7, realtime
    prediction_data = Column(JSON, nullable=False)
    confidence_score = Column(Float, nullable=True)
    model_version_id = Column(Integer, ForeignKey('model_versions.id'), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relations
    course = relationship("Course", back_populates="predictions")
    model_version = relationship("ModelVersion")
    
    def __repr__(self):
        return f"<Prediction {self.id}: Course {self.course_id}, Type {self.prediction_type}>"
    
    def to_dict(self):
        """Convertit l'objet en dictionnaire"""
        return {
            'id': self.id,
            'course_id': self.course_id,
            'prediction_type': self.prediction_type,
            'prediction_data': self.prediction_data,
            'confidence_score': self.confidence_score,
            'model_version_id': self.model_version_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class PredictionUsage(db.Model):
    """Modèle pour suivre l'utilisation des prédictions par les utilisateurs"""
    __tablename__ = 'prediction_usage'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    course_id = Column(Integer, ForeignKey('courses.id'), nullable=False)
    prediction_type = Column(String(20), nullable=False)  # standard, top3, top7, realtime
    used_at = Column(DateTime, default=func.now())
    
    # Relations
    user = relationship("User")
    course = relationship("Course")
    
    def __repr__(self):
        return f"<PredictionUsage {self.id}: User {self.user_id}, Course {self.course_id}>"


class ModelVersion(db.Model):
    """Modèle pour les versions des modèles de prédiction"""
    __tablename__ = 'model_versions'
    
    id = Column(Integer, primary_key=True)
    model_type = Column(String(50), nullable=False)
    model_category = Column(String(20), default='standard')  # standard, simulation
    hyperparameters = Column(JSON, nullable=True)
    training_date = Column(DateTime, nullable=False)
    training_duration = Column(Integer, nullable=True)  # durée en secondes
    accuracy = Column(Float, nullable=True)
    precision_score = Column(Float, nullable=True)
    recall_score = Column(Float, nullable=True)
    f1_score = Column(Float, nullable=True)
    log_loss = Column(Float, nullable=True)
    file_path = Column(String(255), nullable=False)
    training_data_range = Column(String(100), nullable=True)
    feature_count = Column(Integer, nullable=True)
    sample_count = Column(Integer, nullable=True)
    validation_method = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<ModelVersion {self.id}: {self.model_type}, Active: {self.is_active}>"
    
    def to_dict(self):
        """Convertit l'objet en dictionnaire"""
        return {
            'id': self.id,
            'model_type': self.model_type,
            'model_category': self.model_category,
            'hyperparameters': self.hyperparameters,
            'training_date': self.training_date.isoformat() if self.training_date else None,
            'accuracy': self.accuracy,
            'precision_score': self.precision_score,
            'recall_score': self.recall_score,
            'f1_score': self.f1_score,
            'file_path': self.file_path,
            'feature_count': self.feature_count,
            'sample_count': self.sample_count,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class PredictionEvaluation(db.Model):
    """Modèle pour l'évaluation des prédictions par rapport aux résultats réels"""
    __tablename__ = 'prediction_evaluations'
    
    id = Column(Integer, primary_key=True)
    prediction_id = Column(Integer, ForeignKey('predictions.id'), nullable=False)
    accuracy_score = Column(Float, nullable=False)  # pourcentage de prédictions correctes
    precision_simple = Column(Float, nullable=True)  # précision pour les paris simple
    precision_couple = Column(Float, nullable=True)  # précision pour les paris couplé
    precision_tierce = Column(Float, nullable=True)  # précision pour les paris tiercé
    precision_quarte = Column(Float, nullable=True)  # précision pour les paris quarté
    precision_quinte = Column(Float, nullable=True)  # précision pour les paris quinté
    evaluation_notes = Column(Text, nullable=True)
    evaluated_at = Column(DateTime, default=func.now())
    
    # Relation
    prediction = relationship("Prediction")
    
    def __repr__(self):
        return f"<PredictionEvaluation {self.id}: Prediction {self.prediction_id}, Accuracy {self.accuracy_score}>"
    
    def to_dict(self):
        """Convertit l'objet en dictionnaire"""
        return {
            'id': self.id,
            'prediction_id': self.prediction_id,
            'accuracy_score': self.accuracy_score,
            'precision_simple': self.precision_simple,
            'precision_couple': self.precision_couple,
            'precision_tierce': self.precision_tierce,
            'precision_quarte': self.precision_quarte,
            'precision_quinte': self.precision_quinte,
            'evaluation_notes': self.evaluation_notes,
            'evaluated_at': self.evaluated_at.isoformat() if self.evaluated_at else None
        }