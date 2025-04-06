from datetime import datetime
from sqlalchemy import Boolean, Float, create_engine, Column, Integer, String, ForeignKey, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

# Configuration de la base de données
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "pmu_ia",
    "port": "3306",
}
engine = create_engine(f"mysql+mysqlconnector://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}")

# Tables avec préfixe pmu_
class PmuHippodrome(Base):
    __tablename__ = 'pmu_hippodromes'

    code = Column(String(10), primary_key=True)
    libelleCourt = Column(String(100))
    libelleLong = Column(String(200))

class PmuPays(Base):
    __tablename__ = 'pmu_pays'

    code = Column(String(3), primary_key=True)
    libelle = Column(String(100))

class PmuReunion(Base):
    __tablename__ = 'pmu_reunions'

    id = Column(Integer, primary_key=True)
    cached = Column(Integer)
    timezoneOffset = Column(Integer)
    dateReunion = Column(DateTime)
    numOfficiel = Column(Integer)
    numOfficielReunionPrecedente = Column(Integer)
    numOfficielReunionSuivante = Column(Integer)
    numExterne = Column(Integer)
    nature = Column(String(50))
    audience = Column(String(50))
    statut = Column(String(50))
    disciplinesMere = Column(JSON)
    specialites = Column(JSON)
    derniereReunion = Column(String(10))
    reportPlusFpaMax = Column(Integer)
    hippodrome_code = Column(String(10), ForeignKey('pmu_hippodromes.code'))
    pays_code = Column(String(3), ForeignKey('pmu_pays.code'))
    nebulositeCode = Column(String(20))
    nebulositeLibelleCourt = Column(String(50))
    nebulositeLibelleLong = Column(String(200))
    temperature = Column(Integer)
    forceVent = Column(Integer)
    directionVent = Column(String(10))

class PmuCourse(Base):
    __tablename__ = 'pmu_courses'

    id = Column(Integer, primary_key=True)
    numReunion = Column(Integer)
    numOrdre = Column(Integer)
    libelle = Column(String(200))
    heureDepart = Column(DateTime)
    timezoneOffset = Column(Integer)
    distance = Column(Integer)
    distanceUnit = Column(String(20))
    corde = Column(String(50))
    nombreDeclaresPartants = Column(Integer)
    discipline = Column(String(50))
    specialite = Column(String(50))
    hippodrome_code = Column(String(10), ForeignKey('pmu_hippodromes.code'))
    ordreArrivee = Column(JSON)
    
    # Relation avec participants
    participants = relationship("PmuParticipant", back_populates="course")

class PmuParticipant(Base):
    __tablename__ = 'pmu_participants'

    id = Column(Integer, primary_key=True)
    id_course = Column(Integer, ForeignKey('pmu_courses.id'))
    numPmu = Column(Integer)
    nom = Column(String(100))
    age = Column(Integer)
    sexe = Column(String(20))
    race = Column(String(50))
    statut = Column(String(50))
    driver = Column(String(100))
    entraineur = Column(String(100))
    proprietaire = Column(String(100))
    musique = Column(String(255))
    incident = Column(String(100))
    ordreArrivee = Column(Integer)
    tempsObtenu = Column(Integer)
    reductionKilometrique = Column(Integer)
    dernierRapportDirect = Column(JSON)
    dernierRapportReference = Column(JSON)
    
    # Relations
    course = relationship("PmuCourse", back_populates="participants")
    cotes_evolution = relationship("PmuCoteEvolution", back_populates="participant")

class PmuCoteEvolution(Base):
    __tablename__ = 'pmu_cote_evolution'
    
    id = Column(Integer, primary_key=True)
    id_participant = Column(Integer, ForeignKey('pmu_participants.id'))
    horodatage = Column(DateTime, default=datetime.utcnow)
    cote = Column(Float)
    variation = Column(Float, nullable=True)
    
    # Relation
    participant = relationship("PmuParticipant", back_populates="cotes_evolution")

# Tables sans préfixe
class Cheval(Base):
    __tablename__ = 'chevaux'
    
    id = Column(Integer, primary_key=True)
    nom = Column(String(100), nullable=False)
    age = Column(Integer)
    sexe = Column(String(10))
    proprietaire = Column(String(100))
    nomPere = Column(String(100))
    nomMere = Column(String(100))
    
    # Relation
    participations = relationship("Participation", back_populates="cheval")

class Jockey(Base):
    __tablename__ = 'jockeys'
    
    id = Column(Integer, primary_key=True)
    nom = Column(String(100), nullable=False)
    pays = Column(String(50))
    
    # Relation
    participations = relationship("Participation", back_populates="jockey")

class Course(Base):
    __tablename__ = 'courses'
    
    id = Column(Integer, primary_key=True)
    date_heure = Column(DateTime, nullable=False)
    lieu = Column(String(100))
    type_course = Column(String(50))
    distance = Column(Integer)
    terrain = Column(String(50))
    num_course = Column(Integer)
    
    # Relation
    participations = relationship("Participation", back_populates="course")
    predictions = relationship("Prediction", back_populates="course")
    simulations = relationship("Simulation", back_populates="course")

class Participation(Base):
    __tablename__ = 'participations'
    
    id = Column(Integer, primary_key=True)
    id_course = Column(Integer, ForeignKey('courses.id'))
    id_cheval = Column(Integer, ForeignKey('chevaux.id'))
    id_jockey = Column(Integer, ForeignKey('jockeys.id'))
    position = Column(Integer)
    poids = Column(Float)
    est_forfait = Column(Boolean, default=False)
    cote_initiale = Column(Float)
    cote_actuelle = Column(Float)
    statut = Column(String(50))
    
    # Relations
    course = relationship("Course", back_populates="participations")
    cheval = relationship("Cheval", back_populates="participations")
    jockey = relationship("Jockey", back_populates="participations")
    cotes_historique = relationship("CoteHistorique", back_populates="participation")

class CoteHistorique(Base):
    __tablename__ = 'cote_historique'
    
    id = Column(Integer, primary_key=True)
    id_participation = Column(Integer, ForeignKey('participations.id'))
    horodatage = Column(DateTime)
    cote = Column(Float)
    
    # Relation
    participation = relationship("Participation", back_populates="cotes_historique")

class Prediction(Base):
    __tablename__ = 'predictions'
    
    id = Column(Integer, primary_key=True)
    id_course = Column(Integer, ForeignKey('courses.id'))
    horodatage = Column(DateTime)
    prediction = Column(JSON)
    note_confiance = Column(Float)
    
    # Relation
    course = relationship("Course", back_populates="predictions")

class Utilisateur(Base):
    __tablename__ = 'utilisateurs'
    
    id = Column(Integer, primary_key=True)
    nom_utilisateur = Column(String(50))
    email = Column(String(100), unique=True)
    mot_de_passe = Column(String(255))
    abonnement_actif = Column(Boolean, default=False)
    date_expiration = Column(DateTime)
    
    # Relation
    simulations = relationship("Simulation", back_populates="utilisateur")

class Simulation(Base):
    __tablename__ = 'simulations'
    
    id = Column(Integer, primary_key=True)
    utilisateur_id = Column(Integer, ForeignKey('utilisateurs.id'))
    date_simulation = Column(DateTime)
    id_course = Column(Integer, ForeignKey('courses.id'))
    chevaux_selectionnes = Column(JSON)
    resultat_simule = Column(JSON)
    
    # Relations
    utilisateur = relationship("Utilisateur", back_populates="simulations")
    course = relationship("Course", back_populates="simulations")

class ModelVersion(Base):
    __tablename__ = 'model_versions'
    
    id = Column(Integer, primary_key=True)
    model_type = Column(String(50), nullable=False)
    hyperparameters = Column(JSON)
    training_date = Column(DateTime, nullable=False)
    training_duration = Column(Integer)
    accuracy = Column(Float)
    precision_score = Column(Float)
    recall_score = Column(Float)
    f1_score = Column(Float)
    log_loss = Column(Float)
    file_path = Column(String(255), nullable=False)
    training_data_range = Column(String(100))
    feature_count = Column(Integer)
    sample_count = Column(Integer)
    validation_method = Column(String(50))
    notes = Column(String(255))
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Pour la compatibilité avec le code existant, créez des alias
Hippodrome = PmuHippodrome
Pays = PmuPays
Reunion = PmuReunion
Participant = PmuParticipant
CoteEvolution = PmuCoteEvolution

# Fonction pour créer toutes les tables
def create_tables():
    Base.metadata.create_all(engine)

# Fonction pour supprimer toutes les tables
def drop_tables():
    Base.metadata.drop_all(engine)