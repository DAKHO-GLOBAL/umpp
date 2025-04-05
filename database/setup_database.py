from datetime import datetime
from sqlalchemy import Boolean, Float, create_engine, Column, Integer, String, ForeignKey, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# Dans setup_database.py
class CoteEvolution(Base):
    __tablename__ = 'pmu_cote_evolution'
    
    id = Column(Integer, primary_key=True)
    participant_id = Column(Integer, ForeignKey('pmu_participants.id'))
    timestamp = Column(DateTime, default=datetime.utcnow)
    valeur_cote = Column(Float)
    variation = Column(Float, nullable=True)  # Variation par rapport à la dernière cote


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
    nature = Column(String)
    audience = Column(String)
    statut = Column(String)
    disciplinesMere = Column(JSON)
    specialites = Column(JSON)
    derniereReunion = Column(String)
    reportPlusFpaMax = Column(Integer)
    hippodrome_code = Column(String, ForeignKey('pmu_hippodromes.code'))
    pays_code = Column(String, ForeignKey('pmu_pays.code'))
    nebulositeCode = Column(String)
    nebulositeLibelleCourt = Column(String)
    nebulositeLibelleLong = Column(String)
    temperature = Column(Integer)
    forceVent = Column(Integer)
    directionVent = Column(String)

class Hippodrome(Base):
    __tablename__ = 'pmu_hippodromes'

    code = Column(String, primary_key=True)
    libelleCourt = Column(String)
    libelleLong = Column(String)

class Pays(Base):
    __tablename__ = 'pmu_pays'

    code = Column(String, primary_key=True)
    libelle = Column(String)

class Course(Base):
    __tablename__ = 'pmu_courses'

    id = Column(Integer, primary_key=True)
    numReunion = Column(Integer)
    numOrdre = Column(Integer)
    libelle = Column(String)
    heureDepart = Column(DateTime)
    timezoneOffset = Column(Integer)
    distance = Column(Integer)
    distanceUnit = Column(String)
    corde = Column(String)
    nombreDeclaresPartants = Column(Integer)
    discipline = Column(String)
    specialite = Column(String)
    hippodrome_code = Column(String, ForeignKey('pmu_hippodromes.code'))
    ordreArrivee= Column(JSON)


# Dans database/setup_database.py - Ajout à votre code existant

class Participant(Base):
    __tablename__ = 'pmu_participants'

    id = Column(Integer, primary_key=True)
    id_course = Column(Integer, ForeignKey('pmu_courses.id'))  # Utilisez la même convention de nommage
    numPmu = Column(Integer)
    nom = Column(String)
    age = Column(Integer)
    sexe = Column(String)
    race = Column(String)
    statut = Column(String)
    driver = Column(String)
    entraineur = Column(String)
    proprietaire = Column(String)
    musique = Column(String)
    incident = Column(String)
    ordreArrivee = Column(Integer)
    tempsObtenu = Column(Integer)
    reductionKilometrique = Column(Integer)
    
    # Structure pour stocker les cotes
    dernierRapportDirect = Column(JSON)  # Stockez le JSON complet
    dernierRapportReference = Column(JSON)

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

# Configurer la connexion à la base de données
engine = create_engine('mysql+pymysql://username:password@localhost/pmu_ai')

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
