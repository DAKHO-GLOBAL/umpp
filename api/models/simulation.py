# simulation.py
# simulation.py
# api/models/simulation.py
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from extensions import db

class Simulation(db.Model):
    """Modèle pour les simulations de courses"""
    __tablename__ = 'simulations'
    
    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey('courses.id'), nullable=False)
    simulation_type = Column(String(20), nullable=False)  # basic, advanced, comparison
    selected_horses = Column(JSON, nullable=True)
    simulation_params = Column(JSON, nullable=True)
    horse_modifications = Column(JSON, nullable=True)
    weather_conditions = Column(JSON, nullable=True)
    track_conditions = Column(JSON, nullable=True)
    resultat_simule = Column(JSON, nullable=False)
    model_version_id = Column(Integer, ForeignKey('model_versions.id'), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relations
    course = relationship("Course", back_populates="simulations")
    model_version = relationship("ModelVersion")
    
    def __repr__(self):
        return f"<Simulation {self.id}: Course {self.course_id}, Type {self.simulation_type}>"
    
    def to_dict(self):
        """Convertit l'objet en dictionnaire"""
        return {
            'id': self.id,
            'course_id': self.course_id,
            'simulation_type': self.simulation_type,
            'selected_horses': self.selected_horses,
            'simulation_params': self.simulation_params,
            'horse_modifications': self.horse_modifications,
            'weather_conditions': self.weather_conditions,
            'track_conditions': self.track_conditions,
            'resultat_simule': self.resultat_simule,
            'model_version_id': self.model_version_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class SimulationUsage(db.Model):
    """Modèle pour suivre l'utilisation des simulations par les utilisateurs"""
    __tablename__ = 'simulation_usage'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    course_id = Column(Integer, ForeignKey('courses.id'), nullable=False)
    simulation_type = Column(String(20), nullable=False)  # basic, advanced, comparison
    selected_horses = Column(JSON, nullable=True)
    used_at = Column(DateTime, default=func.now())
    
    # Relations
    user = relationship("User")
    course = relationship("Course")
    
    def __repr__(self):
        return f"<SimulationUsage {self.id}: User {self.user_id}, Course {self.course_id}, Type {self.simulation_type}>"


class SimulationComparison(db.Model):
    """Modèle pour les comparaisons de simulations multiples"""
    __tablename__ = 'simulation_comparisons'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    course_id = Column(Integer, ForeignKey('courses.id'), nullable=False)
    scenarios = Column(JSON, nullable=False)  # liste de scénarios à comparer
    comparison_results = Column(JSON, nullable=False)  # résultats de la comparaison
    created_at = Column(DateTime, default=func.now())
    
    # Relations
    user = relationship("User")
    course = relationship("Course")
    
    def __repr__(self):
        return f"<SimulationComparison {self.id}: User {self.user_id}, Course {self.course_id}>"
    
    def to_dict(self):
        """Convertit l'objet en dictionnaire"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'course_id': self.course_id,
            'scenarios': self.scenarios,
            'comparison_results': self.comparison_results,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class SimulationAnimation(db.Model):
    """Modèle pour les animations de simulations"""
    __tablename__ = 'simulation_animations'
    
    id = Column(Integer, primary_key=True)
    simulation_id = Column(Integer, ForeignKey('simulations.id'), nullable=False)
    animation_data = Column(JSON, nullable=False)
    animation_type = Column(String(10), default='2d')  # 2d, 3d, text
    created_at = Column(DateTime, default=func.now())
    
    # Relation
    simulation = relationship("Simulation")
    
    def __repr__(self):
        return f"<SimulationAnimation {self.id}: Simulation {self.simulation_id}, Type {self.animation_type}>"


class PredefinedScenario(db.Model):
    """Modèle pour les scénarios de simulation prédéfinis"""
    __tablename__ = 'predefined_scenarios'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    scenario_type = Column(String(20), nullable=False)  # weather, track, horse_form, jockey
    scenario_data = Column(JSON, nullable=False)
    is_public = Column(Boolean, default=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)  # créateur du scénario (si privé)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relation
    user = relationship("User")
    
    def __repr__(self):
        return f"<PredefinedScenario {self.id}: {self.name}, Type {self.scenario_type}>"
    
    def to_dict(self):
        """Convertit l'objet en dictionnaire"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'scenario_type': self.scenario_type,
            'scenario_data': self.scenario_data,
            'is_public': self.is_public,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }