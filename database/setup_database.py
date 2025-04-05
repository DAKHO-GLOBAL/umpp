from datetime import datetime
from sqlalchemy import Boolean, Float, create_engine, Column, Integer, String, ForeignKey, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# Dans setup_database.py
# class CoteEvolution(Base):
#     __tablename__ = 'pmu_cote_evolution'
    
#     id = Column(Integer, primary_key=True)
#     participant_id = Column(Integer, ForeignKey('pmu_participants.id'))
#     timestamp = Column(DateTime, default=datetime.utcnow)
#     valeur_cote = Column(Float)
#     variation = Column(Float, nullable=True)  # Variation par rapport à la dernière cote


class Cheval(Base):
    __tablename__ = 'chevaux'
    
    id = Column(Integer, primary_key=True)
    nom = Column(String(100))
    age = Column(Integer)
    sexe = Column(String(10))
    proprietaire = Column(String(100))
    nomPere = Column(String(100))
    nomMere = Column(String(100))




class Jockey(Base):
    __tablename__ = 'jockeys'
    
    id = Column(Integer, primary_key=True)
    nom = Column(String(100))
    pays = Column(String(50))


class Reunion(Base):
    __tablename__ = 'pmu_reunions'

    id = Column(Integer, primary_key=True)
    cached = Column(Integer)
    timezoneOffset = Column(Integer)
    dateReunion = Column(DateTime)
    numOfficiel = Column(Integer)
    numOfficielReunionPrecedente = Column(Integer)
    numOfficielReunionSuivante = Column(Integer)
    numExterne = Column(Integer)
    nature = Column(String(50))  # Ajout de taille
    audience = Column(String(50))  # Ajout de taille
    statut = Column(String(50))  # Ajout de taille
    disciplinesMere = Column(JSON)
    specialites = Column(JSON)
    derniereReunion = Column(String(10))  # Ajout de taille
    reportPlusFpaMax = Column(Integer)
    hippodrome_code = Column(String(10), ForeignKey('pmu_hippodromes.code'))
    pays_code = Column(String(3), ForeignKey('pmu_pays.code'))
    nebulositeCode = Column(String(20))  # Ajout de taille
    nebulositeLibelleCourt = Column(String(50))  # Ajout de taille
    nebulositeLibelleLong = Column(String(200))  # Ajout de taille
    temperature = Column(Integer)
    forceVent = Column(Integer)
    directionVent = Column(String(10))  # Ajout de taille
# class Hippodrome(Base):
#     __tablename__ = 'pmu_hippodromes'

#     code = Column(String, primary_key=True)
#     libelleCourt = Column(String)
#     libelleLong = Column(String)

# class Pays(Base):
#     __tablename__ = 'pmu_pays'

#     code = Column(String, primary_key=True)
#     libelle = Column(String)

class Course(Base):
    __tablename__ = 'pmu_courses'

    id = Column(Integer, primary_key=True)
    numReunion = Column(Integer)
    numOrdre = Column(Integer)
    libelle = Column(String(200))  # Ajout de taille
    heureDepart = Column(DateTime)
    timezoneOffset = Column(Integer)
    distance = Column(Integer)
    distanceUnit = Column(String(20))  # Ajout de taille
    corde = Column(String(50))  # Ajout de taille
    nombreDeclaresPartants = Column(Integer)
    discipline = Column(String(50))  # Ajout de taille
    specialite = Column(String(50))  # Ajout de taille
    hippodrome_code = Column(String(10), ForeignKey('pmu_hippodromes.code'))
    ordreArrivee = Column(JSON)


# Dans database/setup_database.py - Ajout à votre code existant

class Participant(Base):
    __tablename__ = 'pmu_participants'

    id = Column(Integer, primary_key=True)
    id_course = Column(Integer, ForeignKey('pmu_courses.id'))
    numPmu = Column(Integer)
    nom = Column(String(100))  # Ajout de taille
    age = Column(Integer)
    sexe = Column(String(20))  # Ajout de taille
    race = Column(String(50))  # Ajout de taille
    statut = Column(String(50))  # Ajout de taille
    driver = Column(String(100))  # Ajout de taille
    entraineur = Column(String(100))  # Ajout de taille
    proprietaire = Column(String(100))  # Ajout de taille
    musique = Column(String(255))  # Ajout de taille
    incident = Column(String(100))  # Ajout de taille
    ordreArrivee = Column(Integer)
    tempsObtenu = Column(Integer)
    reductionKilometrique = Column(Integer)
    
    dernierRapportDirect = Column(JSON)
    dernierRapportReference = Column(JSON)
    
    # # Structure pour stocker les cotes
    # dernierRapportDirect = Column(JSON)  # Stockez le JSON complet
    # dernierRapportReference = Column(JSON)

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


class CoteEvolution(Base):
    __tablename__ = 'pmu_cote_evolution'
    
    id = Column(Integer, primary_key=True)
    id_participant = Column(Integer, ForeignKey('pmu_participants.id'))  # Même convention
    horodatage = Column(DateTime, default=datetime.utcnow)  # Utilisez "horodatage" comme dans vos autres tables
    cote = Column(Float)
    variation = Column(Float, nullable=True)  # Variation par rapport à la dernière cote

class CoteHistorique(Base):
    __tablename__ = 'cote_historique'
    
    id = Column(Integer, primary_key=True)
    id_participation = Column(Integer, ForeignKey('participations.id'))
    horodatage = Column(DateTime)
    cote = Column(Float)


class Prediction(Base):
    __tablename__ = 'predictions'
    
    id = Column(Integer, primary_key=True)
    id_course = Column(Integer, ForeignKey('courses.id'))
    horodatage = Column(DateTime)
    prediction = Column(JSON)
    note_confiance = Column(Float)


    class Utilisateur(Base):

        __tablename__ = 'utilisateurs'
        
        id = Column(Integer, primary_key=True)
        nom_utilisateur = Column(String(50))
        email = Column(String(100))
        mot_de_passe = Column(String(255))
        abonnement_actif = Column(Boolean, default=False)
        date_expiration = Column(DateTime)

class Simulation(Base):
    __tablename__ = 'simulations'
    
    id = Column(Integer, primary_key=True)
    utilisateur_id = Column(Integer, ForeignKey('utilisateurs.id'))
    date_simulation = Column(DateTime)
    id_course = Column(Integer, ForeignKey('courses.id'))
    chevaux_selectionnes = Column(JSON)
    resultat_simule = Column(JSON)

class Hippodrome(Base):
    __tablename__ = 'pmu_hippodromes'

    code = Column(String(10), primary_key=True)  # Spécifier la longueur (10)
    libelleCourt = Column(String(100))  # Spécifier la longueur (100)
    libelleLong = Column(String(200))  # Spécifier la longueur (200)

class Pays(Base):
    __tablename__ = 'pmu_pays'

    code = Column(String(3), primary_key=True)  # Spécifier la longueur (3)
    libelle = Column(String(100))  # Spécifier la longueur (100)


db_config = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "pmu_ia",
    "port": "3306",
}
# Configurer la connexion à la base de données
#engine = create_engine('mysql+pymysql://username:password@localhost/pmu_ai')
engine = create_engine(f"mysql+mysqlconnector://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}")

    # incidents = Column(String)

    # Add other fields as needed

    # Define a relationship with the Pari model
    # paris = relationship('Pari', back_populates='pmu_courses')

# class Pari(Base):
#     __tablename__ = 'pmu_paris'
#
#     id = Column(Integer, primary_key=True)
#     numReunion = Column(Integer, ForeignKey('courses.numReunion'))
#     numExterneReunion = Column(Integer, ForeignKey('courses.numExterneReunion'))
#     codePari = Column(String)
#     # Add other fields as needed
#
#     # Define a relationship with the Course model
#     course = relationship('Course', back_populates='pmu_paris')

# class Cheval(Base):
#     __tablename__ = 'pmu_cheval'
#
#     code = Column(String, primary_key=True)
#     libelle = Column(String)

# Configurer la connexion à la base de données SQLite (utilisez un fichier local)
#engine = create_engine('sqlite:///database/db/pmu_data.db')
Base.metadata.create_all(engine)
