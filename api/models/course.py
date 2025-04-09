# course.py
# course.py
# api/models/course.py
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from extensions import db

class Course(db.Model):
    """Modèle pour les courses de chevaux"""
    __tablename__ = 'courses'
    
    id = Column(Integer, primary_key=True)
    date_heure = Column(DateTime, nullable=False)
    lieu = Column(String(100), nullable=True)
    type_course = Column(String(50), nullable=True)
    distance = Column(Integer, nullable=True)
    terrain = Column(String(50), nullable=True)
    num_course = Column(Integer, nullable=True)
    libelle = Column(String(200), nullable=True)
    corde = Column(String(50), nullable=True)
    discipline = Column(String(50), nullable=True)
    specialite = Column(String(50), nullable=True)
    ordreArrivee = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relation avec la table PMU
    pmu_course_id = Column(Integer, ForeignKey('pmu_courses.id'), nullable=True)
    
    # Relations
    participations = relationship("Participation", back_populates="course", cascade="all, delete-orphan")
    predictions = relationship("Prediction", back_populates="course", cascade="all, delete-orphan")
    simulations = relationship("Simulation", back_populates="course", cascade="all, delete-orphan")
    commentaires = relationship("CommentaireCourse", back_populates="course", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Course {self.id}: {self.lieu} {self.date_heure}>"
    
    def to_dict(self):
        """Convertit l'objet en dictionnaire"""
        return {
            'id': self.id,
            'date_heure': self.date_heure.isoformat() if self.date_heure else None,
            'lieu': self.lieu,
            'type_course': self.type_course,
            'distance': self.distance,
            'terrain': self.terrain,
            'num_course': self.num_course,
            'libelle': self.libelle,
            'corde': self.corde,
            'discipline': self.discipline,
            'specialite': self.specialite,
            'ordreArrivee': self.ordreArrivee,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Participation(db.Model):
    """Modèle pour les participations des chevaux aux courses"""
    __tablename__ = 'participations'
    
    id = Column(Integer, primary_key=True)
    id_course = Column(Integer, ForeignKey('courses.id'), nullable=False)
    id_cheval = Column(Integer, ForeignKey('chevaux.id'), nullable=False)
    id_jockey = Column(Integer, ForeignKey('jockeys.id'), nullable=True)
    position = Column(Integer, nullable=True)
    poids = Column(Float, nullable=True)
    est_forfait = Column(Boolean, default=False)
    cote_initiale = Column(Float, nullable=True)
    cote_actuelle = Column(Float, nullable=True)
    statut = Column(String(50), nullable=True)
    numPmu = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relations
    course = relationship("Course", back_populates="participations")
    cheval = relationship("Cheval", back_populates="participations")
    jockey = relationship("Jockey", back_populates="participations")
    cotes_historique = relationship("CoteHistorique", back_populates="participation", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Participation {self.id}: Course {self.id_course}, Cheval {self.id_cheval}>"
    
    def to_dict(self):
        """Convertit l'objet en dictionnaire"""
        return {
            'id': self.id,
            'id_course': self.id_course,
            'id_cheval': self.id_cheval,
            'id_jockey': self.id_jockey,
            'position': self.position,
            'poids': self.poids,
            'est_forfait': self.est_forfait,
            'cote_initiale': self.cote_initiale,
            'cote_actuelle': self.cote_actuelle,
            'statut': self.statut,
            'numPmu': self.numPmu,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Cheval(db.Model):
    """Modèle pour les chevaux"""
    __tablename__ = 'chevaux'
    
    id = Column(Integer, primary_key=True)
    nom = Column(String(100), nullable=False)
    age = Column(Integer, nullable=True)
    sexe = Column(String(10), nullable=True)
    proprietaire = Column(String(100), nullable=True)
    nomPere = Column(String(100), nullable=True)
    nomMere = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relations
    participations = relationship("Participation", back_populates="cheval")
    participants_pmu = relationship("PmuParticipant", back_populates="cheval")
    
    def __repr__(self):
        return f"<Cheval {self.id}: {self.nom}>"
    
    def to_dict(self):
        """Convertit l'objet en dictionnaire"""
        return {
            'id': self.id,
            'nom': self.nom,
            'age': self.age,
            'sexe': self.sexe,
            'proprietaire': self.proprietaire,
            'nomPere': self.nomPere,
            'nomMere': self.nomMere,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Jockey(db.Model):
    """Modèle pour les jockeys"""
    __tablename__ = 'jockeys'
    
    id = Column(Integer, primary_key=True)
    nom = Column(String(100), nullable=False)
    pays = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relations
    participations = relationship("Participation", back_populates="jockey")
    participants_pmu = relationship("PmuParticipant", back_populates="jockey_ref")
    
    def __repr__(self):
        return f"<Jockey {self.id}: {self.nom}>"
    
    def to_dict(self):
        """Convertit l'objet en dictionnaire"""
        return {
            'id': self.id,
            'nom': self.nom,
            'pays': self.pays,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class CoteHistorique(db.Model):
    """Modèle pour l'historique des cotes"""
    __tablename__ = 'cote_historique'
    
    id = Column(Integer, primary_key=True)
    id_participation = Column(Integer, ForeignKey('participations.id'), nullable=False)
    horodatage = Column(DateTime, default=func.now())
    cote = Column(Float, nullable=False)
    
    # Relation
    participation = relationship("Participation", back_populates="cotes_historique")
    
    def __repr__(self):
        return f"<CoteHistorique {self.id}: Participation {self.id_participation}, Cote {self.cote}>"
    
    def to_dict(self):
        """Convertit l'objet en dictionnaire"""
        return {
            'id': self.id,
            'id_participation': self.id_participation,
            'horodatage': self.horodatage.isoformat() if self.horodatage else None,
            'cote': self.cote
        }


class CommentaireCourse(db.Model):
    """Modèle pour les commentaires de course"""
    __tablename__ = 'commentaires_course'
    
    id = Column(Integer, primary_key=True)
    id_course = Column(Integer, ForeignKey('courses.id'), nullable=False)
    texte = Column(Text, nullable=False)
    source = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=func.now())
    
    # Relation
    course = relationship("Course", back_populates="commentaires")