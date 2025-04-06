from datetime import datetime
from sqlalchemy import Boolean, Date, Float, Text, create_engine, Column, Integer, String, ForeignKey, DateTime, JSON
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

# Tables essentielles pour le scraping PMU

class Utilisateur(Base):
    """Classe représentant un utilisateur du système"""
    __tablename__ = 'utilisateurs'
    
    id = Column(Integer, primary_key=True)
    nom_utilisateur = Column(String(50), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    mot_de_passe = Column(String(255), nullable=False)
    abonnement_actif = Column(Boolean, default=False)
    date_expiration = Column(Date)
    date_creation = Column(DateTime, default=datetime.utcnow)
    derniere_connexion = Column(DateTime)
    role = Column(String(20), default='utilisateur')
    
    # Relation avec la table simulations
    simulations = relationship("Simulation", back_populates="utilisateur")
    
    def __repr__(self):
        return f"<Utilisateur(id={self.id}, nom_utilisateur={self.nom_utilisateur}, email={self.email})>"


class Simulation(Base):
    """Classe représentant une simulation personnalisée"""
    __tablename__ = 'simulations'
    
    id = Column(Integer, primary_key=True)
    utilisateur_id = Column(Integer, ForeignKey('utilisateurs.id'))
    date_simulation = Column(DateTime, default=datetime.utcnow)
    id_course = Column(Integer, ForeignKey('courses.id'))
    chevaux_selectionnes = Column(JSON)
    resultat_simule = Column(JSON)
    parametres_simulation = Column(JSON)
    
    # Relations
    utilisateur = relationship("Utilisateur", back_populates="simulations")
    course = relationship("Course")
    
    def __repr__(self):
        return f"<Simulation(id={self.id}, utilisateur_id={self.utilisateur_id}, id_course={self.id_course})>"

class Hippodrome(Base):
    __tablename__ = 'pmu_hippodromes'

    code = Column(String(10), primary_key=True)
    libelleCourt = Column(String(100))
    libelleLong = Column(String(200))
    
    # Relations
    reunions = relationship("Reunion", back_populates="hippodrome")
    courses = relationship("PmuCourse", back_populates="hippodrome")

class Pays(Base):
    __tablename__ = 'pmu_pays'

    code = Column(String(3), primary_key=True)
    libelle = Column(String(100))
    
    # Relations
    reunions = relationship("Reunion", back_populates="pays")

class Reunion(Base):
    __tablename__ = 'pmu_reunions'

    id = Column(Integer, primary_key=True)
    cached = Column(Integer, nullable=True)
    timezoneOffset = Column(Integer, nullable=True)
    dateReunion = Column(DateTime)
    numOfficiel = Column(Integer)
    numOfficielReunionPrecedente = Column(Integer, nullable=True)
    numOfficielReunionSuivante = Column(Integer, nullable=True)
    numExterne = Column(Integer, nullable=True)
    nature = Column(String(50), nullable=True)
    audience = Column(String(50), nullable=True)
    statut = Column(String(50), nullable=True)
    disciplinesMere = Column(JSON, nullable=True)
    specialites = Column(JSON, nullable=True)
    derniereReunion = Column(String(10), nullable=True)
    reportPlusFpaMax = Column(Integer, nullable=True)
    hippodrome_code = Column(String(10), ForeignKey('pmu_hippodromes.code'), nullable=True)
    pays_code = Column(String(3), ForeignKey('pmu_pays.code'), nullable=True)
    nebulositeCode = Column(String(20), nullable=True)
    nebulositeLibelleCourt = Column(String(50), nullable=True)
    nebulositeLibelleLong = Column(String(200), nullable=True)
    temperature = Column(Integer, nullable=True)
    forceVent = Column(Integer, nullable=True)
    directionVent = Column(String(10), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    hippodrome = relationship("Hippodrome", back_populates="reunions")
    pays = relationship("Pays", back_populates="reunions")
    courses = relationship("PmuCourse", back_populates="reunion")

class PmuCourse(Base):
    __tablename__ = 'pmu_courses'

    id = Column(Integer, primary_key=True)
    numReunion = Column(Integer)
    numExterneReunion = Column(Integer, nullable=True)
    numOrdre = Column(Integer)
    numExterne = Column(Integer, nullable=True)
    libelle = Column(String(200))
    libelleCourt = Column(String(200), nullable=True)
    heureDepart = Column(DateTime)
    timezoneOffset = Column(Integer, nullable=True)
    distance = Column(Integer)
    distanceUnit = Column(String(20), nullable=True)
    corde = Column(String(50), nullable=True)
    nombreDeclaresPartants = Column(Integer, nullable=True)
    discipline = Column(String(50), nullable=True)
    specialite = Column(String(50))
    hippodrome_code = Column(String(10), ForeignKey('pmu_hippodromes.code'), nullable=True)
    ordreArrivee = Column(JSON, nullable=True)
    statut = Column(String(50), nullable=True)
    categorieStatut = Column(String(50), nullable=True)
    dureeCourse = Column(Integer, nullable=True)
    reunion_id = Column(Integer, ForeignKey('pmu_reunions.id'), nullable=True)
    categorieParticularite = Column(String(100), nullable=True)
    conditionSexe = Column(String(50), nullable=True)
    montantPrix = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    hippodrome = relationship("Hippodrome", back_populates="courses")
    reunion = relationship("Reunion", back_populates="courses")
    participants = relationship("Participant", back_populates="course")
    incidents = relationship("Incident", back_populates="course")
    commentaires = relationship("CommentaireCourse", back_populates="course")
    photos = relationship("PhotoArrivee", back_populates="course")

class Participant(Base):
    __tablename__ = 'pmu_participants'

    id = Column(Integer, primary_key=True)
    id_course = Column(Integer, ForeignKey('pmu_courses.id'))
    numPmu = Column(Integer)
    nom = Column(String(100))
    age = Column(Integer, nullable=True)
    sexe = Column(String(20), nullable=True)
    race = Column(String(50), nullable=True)
    statut = Column(String(50), nullable=True)
    driver = Column(String(100), nullable=True)  # Jockey pour les courses attelées
    jockey = Column(String(100), nullable=True)  # Pour les courses montées
    entraineur = Column(String(100), nullable=True)
    proprietaire = Column(String(100), nullable=True)
    musique = Column(String(255), nullable=True)
    incident = Column(String(100), nullable=True)
    ordreArrivee = Column(Integer, nullable=True)
    tempsObtenu = Column(Integer, nullable=True)
    reductionKilometrique = Column(Integer, nullable=True)
    dernierRapportDirect = Column(JSON, nullable=True)
    dernierRapportReference = Column(JSON, nullable=True)
    handicapPoids = Column(Float, nullable=True)
    nomPere = Column(String(100), nullable=True)
    nomMere = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    course = relationship("PmuCourse", back_populates="participants")
    cotes_evolution = relationship("CoteEvolution", back_populates="participant")
    
    # Pour le lien avec les tables de modèle IA
    cheval_id = Column(Integer, ForeignKey('chevaux.id'), nullable=True)
    jockey_id = Column(Integer, ForeignKey('jockeys.id'), nullable=True)
    
    cheval = relationship("Cheval", back_populates="participants_pmu")
    jockey_ref = relationship("Jockey", back_populates="participants_pmu")

class CoteEvolution(Base):
    __tablename__ = 'pmu_cote_evolution'
    
    id = Column(Integer, primary_key=True)
    id_participant = Column(Integer, ForeignKey('pmu_participants.id'))
    horodatage = Column(DateTime, default=datetime.utcnow)
    cote = Column(Float)
    variation = Column(Float, nullable=True)
    
    # Relation
    participant = relationship("Participant", back_populates="cotes_evolution")

class Cheval(Base):
    __tablename__ = 'chevaux'
    
    id = Column(Integer, primary_key=True)
    nom = Column(String(100), nullable=False)
    age = Column(Integer, nullable=True)
    sexe = Column(String(10), nullable=True)
    proprietaire = Column(String(100), nullable=True)
    nomPere = Column(String(100), nullable=True)
    nomMere = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    participations = relationship("Participation", back_populates="cheval")
    participants_pmu = relationship("Participant", back_populates="cheval")

class Jockey(Base):
    __tablename__ = 'jockeys'
    
    id = Column(Integer, primary_key=True)
    nom = Column(String(100), nullable=False)
    pays = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    participations = relationship("Participation", back_populates="jockey")
    participants_pmu = relationship("Participant", back_populates="jockey_ref")

class Course(Base):
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
    ordreArrivee = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relation avec la table PMU
    pmu_course_id = Column(Integer, ForeignKey('pmu_courses.id'), nullable=True)
    
    # Relations
    participations = relationship("Participation", back_populates="course")
    predictions = relationship("Prediction", back_populates="course")

class Participation(Base):
    __tablename__ = 'participations'
    
    id = Column(Integer, primary_key=True)
    id_course = Column(Integer, ForeignKey('courses.id'))
    id_cheval = Column(Integer, ForeignKey('chevaux.id'))
    id_jockey = Column(Integer, ForeignKey('jockeys.id'), nullable=True)
    position = Column(Integer, nullable=True)
    poids = Column(Float, nullable=True)
    est_forfait = Column(Boolean, default=False)
    cote_initiale = Column(Float, nullable=True)
    cote_actuelle = Column(Float, nullable=True)
    statut = Column(String(50), nullable=True)
    numPmu = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    course = relationship("Course", back_populates="participations")
    cheval = relationship("Cheval", back_populates="participations")
    jockey = relationship("Jockey", back_populates="participations")
    cotes_historique = relationship("CoteHistorique", back_populates="participation")

class CoteHistorique(Base):
    __tablename__ = 'cote_historique'
    
    id = Column(Integer, primary_key=True)
    id_participation = Column(Integer, ForeignKey('participations.id'))
    horodatage = Column(DateTime, default=datetime.utcnow)
    cote = Column(Float)
    
    # Relation
    participation = relationship("Participation", back_populates="cotes_historique")

class Prediction(Base):
    __tablename__ = 'predictions'
    
    id = Column(Integer, primary_key=True)
    id_course = Column(Integer, ForeignKey('courses.id'))
    horodatage = Column(DateTime, default=datetime.utcnow)
    prediction = Column(JSON)
    note_confiance = Column(Float, nullable=True)
    model_version_id = Column(Integer, ForeignKey('model_versions.id'), nullable=True)
    
    # Relations
    course = relationship("Course", back_populates="predictions")
    model_version = relationship("ModelVersion", back_populates="predictions")

class ModelVersion(Base):
    """Classe représentant une version de modèle"""
    __tablename__ = 'model_versions'
    
    id = Column(Integer, primary_key=True)
    model_type = Column(String(50), nullable=False)
    model_category = Column(String(20), default='standard')  # 'standard' ou 'simulation'
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
    notes = Column(Text)
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<ModelVersion(id={self.id}, model_type={self.model_type}, model_category={self.model_category}, is_active={self.is_active})>"


class Incident(Base):
    __tablename__ = 'incidents'
    
    id = Column(Integer, primary_key=True)
    id_course = Column(Integer, ForeignKey('pmu_courses.id'))
    type_incident = Column(String(100))
    numero_participants = Column(JSON, nullable=True)
    
    # Relation
    course = relationship("PmuCourse", back_populates="incidents")

class CommentaireCourse(Base):
    __tablename__ = 'commentaires_course'
    
    id = Column(Integer, primary_key=True)
    id_course = Column(Integer, ForeignKey('pmu_courses.id'))
    texte = Column(Text)
    source = Column(String(50), nullable=True)
    
    # Relation
    course = relationship("PmuCourse", back_populates="commentaires")

class PhotoArrivee(Base):
    __tablename__ = 'photos_arrivee'
    
    id = Column(Integer, primary_key=True)
    id_course = Column(Integer, ForeignKey('pmu_courses.id'))
    url = Column(String(255))
    height = Column(Integer, nullable=True)
    width = Column(Integer, nullable=True)
    is_original = Column(Boolean, default=False)
    
    # Relation
    course = relationship("PmuCourse", back_populates="photos")

# Fonction pour créer toutes les tables
def create_tables():
    Base.metadata.create_all(engine)

# Fonction pour supprimer toutes les tables
def drop_tables():
    Base.metadata.drop_all(engine)

if __name__ == "__main__":
    # Créer toutes les tables
    create_tables()
    print("Base de données initialisée avec succès!")

#python -c "from database.setup_database import Base, engine; Base.metadata.drop_all(engine); Base.metadata.create_all(engine)"