import logging
from datetime import datetime, timedelta

from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from database.setup_database import (
    Cheval, CoteHistorique, Jockey, Participation, 
    Prediction, engine, Hippodrome, Pays, Reunion, Course,
    PmuCourse, PmuParticipant, PmuCoteEvolution as CoteEvolution
)


def save_pays(pays_data):
    Session = sessionmaker(bind=engine)
    session = Session()
    existing_pays = session.query(Pays).filter_by(code=pays_data.get('code')).first()
    if not existing_pays:
        pays_obj = Pays(**pays_data)
        session.add(pays_obj)
        logging.info("Saving pays data")
    session.commit()

def save_hippodrome(hippodrome_data):
    Session = sessionmaker(bind=engine)
    session = Session()
    existing_hippodrome = session.query(Hippodrome).filter_by(code=hippodrome_data.get('code')).first()
    if not existing_hippodrome:
        hippodrome_obj = Hippodrome(**hippodrome_data)
        session.add(hippodrome_obj)
        logging.info("Saving hippodrome data")
    session.commit()

def save_reunions(reunion_data):
    Session = sessionmaker(bind=engine)
    session = Session()
    existing_reunion = (session.query(Reunion)
                        .filter_by(
        dateReunion=reunion_data.get('dateReunion'),
        numOfficiel=reunion_data.get('numOfficiel')
    ).first())
    if not existing_reunion:
        reunion_data.pop('hippodrome', None)
        reunion_data.pop('pays', None)
        reunion_data.pop('courses', None)
        reunion_obj = Reunion(**reunion_data, hippodrome_code=reunion_data.get('hippodrome', {}).get('code'), pays_code=reunion_data.get('pays', {}).get('code'))
        session.add(reunion_obj)
        logging.info("Saving reunion data")
    session.commit()

def save_courses(courses_data):
    Session = sessionmaker(bind=engine)
    session = Session()

    for course_data in courses_data:
        course_data['heureDepart'] = datetime.utcfromtimestamp(course_data['heureDepart'] / 1000.0)
        existing_course = (session.query(Course).filter_by(
            heureDepart=course_data.get('heureDepart'),
            numReunion=course_data.get('numReunion'),
            numOrdre=course_data.get('numOrdre')
        ).first())
        if not existing_course:
            hipodrome_code = course_data.get('hippodrome', {}).get('codeHippodrome')
            # Définissez une liste des noms d'attributs valides de la classe Course
            valid_attributes = [attr.name for attr in Course.__table__.columns]

            # Créez un nouveau dictionnaire avec seulement les attributs valides
            filtered_course_data = {key: value for key, value in course_data.items() if key in valid_attributes}

            course_obj = Course(**filtered_course_data, hippodrome_code=hipodrome_code)
            session.add(course_obj)
            logging.info("Saving Course data")
            session.commit()


def save_course(course_data):
    """Sauvegarde une course et retourne son ID"""
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Vérifier si la course existe déjà
        existing_course = session.query(Course).filter_by(
            heureDepart=course_data['heureDepart'],
            num_course=course_data['num_course'],
            lieu=course_data['lieu']
        ).first()
        
        if existing_course:
            logging.info(f"Course already exists: {course_data['libelle']} at {course_data['date_heure']}")
            return existing_course.id
        
        # Créer une nouvelle course
        new_course = Course(**course_data)
        session.add(new_course)
        session.commit()
        
        logging.info(f"Saved course: {course_data['libelle']} with ID {new_course.id}")
        return new_course.id
    
    except SQLAlchemyError as e:
        session.rollback()
        logging.error(f"Error saving course: {str(e)}")
        return None
    
    finally:
        session.close()


# Dans database/database.py - Ajout à votre code existant

def save_participants_data(participants_data, course_id):

    """Sauvegarde les données des participants dans la base de données"""
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Récupérer l'ID de la course en utilisant les détails fournis
    date_str, reunion_str, course_str = course_id.split('R')[0], course_id.split('R')[1].split('C')[0], course_id.split('C')[1]
    
    reunion_date = datetime.strptime(date_str, "%d%m%Y")
    reunion_num = int(reunion_str)
    course_num = int(course_str)
    
    # Rechercher la course avec la même convention que vos autres requêtes
    course = session.query(Course).filter_by(
        numReunion=reunion_num,
        numOrdre=course_num
    ).first()
    
    if not course:
        logging.error(f"Course {course_id} non trouvée dans la base de données")
        session.close()
        return
    
    participants = participants_data.get('participants', [])
    
    for participant_data in participants:
        # Vérifier si le participant existe déjà
        existing_participant = session.query(Participant).filter_by(
            id_course=course.id,
            numPmu=participant_data.get('numPmu')
        ).first()
        
        if not existing_participant:
            # Créer un dictionnaire avec les champs que nous voulons sauvegarder
            participant_dict = {
                'id_course': course.id,
                'numPmu': participant_data.get('numPmu'),
                'nom': participant_data.get('nom'),
                'age': participant_data.get('age'),
                'sexe': participant_data.get('sexe'),
                'race': participant_data.get('race'),
                'statut': participant_data.get('statut'),
                'driver': participant_data.get('driver'),
                'entraineur': participant_data.get('entraineur'),
                'proprietaire': participant_data.get('proprietaire'),
                'musique': participant_data.get('musique'),
                'incident': participant_data.get('incident'),
                'ordreArrivee': participant_data.get('ordreArrivee'),
                'tempsObtenu': participant_data.get('tempsObtenu'),
                'reductionKilometrique': participant_data.get('reductionKilometrique'),
                'dernierRapportDirect': participant_data.get('dernierRapportDirect'),
                'dernierRapportReference': participant_data.get('dernierRapportReference')
            }
            
            # Créer et sauvegarder le participant
            participant = Participant(**participant_dict)
            session.add(participant)
            logging.info(f"Sauvegarde du participant {participant_data.get('nom')} pour la course {course_id}")
            
            # Si le participant a un rapport direct (cote), l'enregistrer aussi dans la table d'évolution
            if participant_data.get('dernierRapportDirect') and 'rapport' in participant_data.get('dernierRapportDirect'):
                cote_value = participant_data['dernierRapportDirect']['rapport']
                
                # Sauvegarder la cote initiale dans l'historique des cotes
                # Nous devons d'abord commit pour obtenir l'ID du participant
                session.commit()
                
                cote_record = CoteEvolution(
                    id_participant=participant.id,
                    cote=cote_value,
                    variation=0.0  # Pas de variation pour la première entrée
                )
                session.add(cote_record)
    
    session.commit()
    session.close()


def save_participation(cheval_data, jockey_data, participation_data):
    """Sauvegarde les données de participation (cheval, jockey, participation)"""
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Vérifier/sauvegarder le cheval
        cheval = session.query(Cheval).filter_by(nom=cheval_data['nom']).first()
        if not cheval:
            cheval = Cheval(**cheval_data)
            session.add(cheval)
            session.flush()  # Pour obtenir l'ID
        
        # Vérifier/sauvegarder le jockey
        jockey = session.query(Jockey).filter_by(nom=jockey_data['nom']).first()
        if not jockey:
            jockey = Jockey(**jockey_data)
            session.add(jockey)
            session.flush()  # Pour obtenir l'ID
        
        # Compléter les données de participation
        participation_data['id_cheval'] = cheval.id
        participation_data['id_jockey'] = jockey.id
        
        # Vérifier si la participation existe déjà
        existing_participation = session.query(Participation).filter_by(
            id_course=participation_data['id_course'],
            id_cheval=participation_data['id_cheval'],
            id_jockey=participation_data['id_jockey']
        ).first()
        
        if existing_participation:
            # Mettre à jour les données existantes
            for key, value in participation_data.items():
                setattr(existing_participation, key, value)
            
            participation_id = existing_participation.id
            logging.info(f"Updated participation for {cheval.nom} in course {participation_data['id_course']}")
        else:
            # Créer une nouvelle participation
            new_participation = Participation(**participation_data)
            session.add(new_participation)
            session.flush()
            participation_id = new_participation.id
            logging.info(f"Saved participation for {cheval.nom} in course {participation_data['id_course']}")
        
        # Enregistrer la cote initiale dans l'historique si disponible
        if 'cote_initiale' in participation_data and participation_data['cote_initiale']:
            cote_historique = CoteHistorique(
                id_participation=participation_id,
                horodatage=datetime.now(),
                cote=participation_data['cote_initiale']
            )
            session.add(cote_historique)
        
        session.commit()
    
    except SQLAlchemyError as e:
        session.rollback()
        logging.error(f"Error saving participation: {str(e)}")
    
    finally:
        session.close()

def update_odds(date_str, reunion_number, course_number, participants_data):
    """Met à jour les cotes et sauvegarde l'historique"""
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Trouver la course
        course_date = datetime.strptime(date_str, "%d%m%Y")
        course = session.query(Course).filter(
            Course.date_heure >= course_date,
            Course.date_heure < course_date + timedelta(days=1),
            Course.num_course == course_number
        ).first()
        
        if not course:
            logging.error(f"Course not found for {date_str}R{reunion_number}C{course_number}")
            return
        
        for p_data in participants_data:
            # Trouver le cheval
            cheval = session.query(Cheval).filter_by(nom=p_data.get('nom')).first()
            
            if not cheval:
                logging.warning(f"Cheval not found: {p_data.get('nom')}")
                continue
            
            # Trouver la participation
            participation = session.query(Participation).filter_by(
                id_course=course.id,
                id_cheval=cheval.id
            ).first()
            
            if not participation:
                logging.warning(f"Participation not found for {cheval.nom} in course {course.id}")
                continue
            
            # Mettre à jour la cote actuelle
            if 'dernierRapportDirect' in p_data and 'rapport' in p_data['dernierRapportDirect']:
                cote_value = p_data['dernierRapportDirect']['rapport']
                
                # Ne mettre à jour que si la cote a changé
                if participation.cote_actuelle != cote_value:
                    participation.cote_actuelle = cote_value
                    
                    # Enregistrer dans l'historique
                    cote_historique = CoteHistorique(
                        id_participation=participation.id,
                        horodatage=datetime.now(),
                        cote=cote_value
                    )
                    session.add(cote_historique)
                    
                    logging.info(f"Updated odds for {cheval.nom}: {cote_value}")
        
        session.commit()
    
    except SQLAlchemyError as e:
        session.rollback()
        logging.error(f"Error updating odds: {str(e)}")
    
    finally:
        session.close()



def save_prediction(course_id, predictions_data, confidence):
    """Sauvegarde les prédictions pour une course"""
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Créer une nouvelle prédiction
        prediction = Prediction(
            id_course=course_id,
            horodatage=datetime.now(),
            prediction=predictions_data,
            note_confiance=confidence
        )
        
        session.add(prediction)
        session.commit()
        
        logging.info(f"Saved prediction for course {course_id}")
        return prediction.id
    
    except SQLAlchemyError as e:
        session.rollback()
        logging.error(f"Error saving prediction: {str(e)}")
        return None
    
    finally:
        session.close()

def save_pmu_course(course_data):
    """Sauvegarde une course PMU et retourne son ID"""
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Vérifier si la course existe déjà
        existing_course = session.query(PmuCourse).filter_by(
            heureDepart=course_data['heureDepart'],
            numReunion=course_data['numReunion'],
            numOrdre=course_data['numOrdre']
        ).first()
        
        if existing_course:
            logging.info(f"Course already exists: {course_data['libelle']} at {course_data['heureDepart']}")
            return existing_course.id
        
        # Créer une nouvelle course
        new_course = PmuCourse(**course_data)
        session.add(new_course)
        session.commit()
        
        logging.info(f"Saved course: {course_data['libelle']} with ID {new_course.id}")
        return new_course.id
    
    except SQLAlchemyError as e:
        session.rollback()
        logging.error(f"Error saving course: {str(e)}")
        return None
    
    finally:
        session.close()