# import json
# import logging
# import requests
# from datetime import datetime, timedelta

# from sqlalchemy import Engine
# from data_traitement.traitement import save_race_data
# from sqlalchemy.orm import sessionmaker

# from database.database import save_participants_data
# from database.setup_database import CoteEvolution, Course, Participant
# # Calcul les dates intermédiaires entre deux dates données
# def get_race_dates(start_date, end_date):
#     current_date = start_date
#     race_dates = []

#     while current_date <= end_date:
#         race_dates.append(current_date.strftime("%d%m%Y"))
#         current_date += timedelta(days=1)

#     return race_dates

# # Apelle l'api pmu afin de récupérer l'ensemble des données des courses, réunions, hippodrome, participants
# # Collecte les données entre deux dates
# def call_api_between_dates(start_date, end_date):
#     current_date = start_date
#     while current_date <= end_date:
#         date_str = current_date.strftime("%d%m%Y")
#         reunion_number = 1
        
#         while True:
#             base_url = "https://online.turfinfo.api.pmu.fr/rest/client/61/programme/{}/{}?specialisation=INTERNET"
#             url = base_url.format(date_str, f"R{reunion_number}")
            
#             headers = {
#                 'accept': 'application/json',
#                 'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
#             }
            
#             logging.debug(f"Attempting to call API for {date_str}, R{reunion_number}")
#             response = requests.get(url, headers=headers)
            
#             if response.status_code == 204:
#                 # Plus de réunion ce jour-là
#                 logging.info(f"No more reunion [{reunion_number}] on {current_date} : 204")
#                 break
#             elif response.status_code == 200:
#                 # Courses disponibles pour cette réunion
#                 data = response.json()
#                 logging.debug(f"Response 200 for reunions [{reunion_number}] on {current_date}")
                
#                 # Sauvegarder les données de courses
#                 courses_data = save_race_data(data)
                
#                 # Pour chaque course, récupérer les participants
#                 for course in data.get('courses', []):
#                     course_number = course.get('numOrdre')
#                     try:
#                         get_participants(date_str, reunion_number, course_number, courses_data)
#                     except Exception as e:
#                         logging.error(f"Error fetching participants for {date_str}R{reunion_number}C{course_number}: {str(e)}")
#             else:
#                 logging.error(f"API request failed: {response.status_code}, Date: {date_str}, Reunion: {reunion_number}")
            
#             reunion_number += 1
        
#         current_date += timedelta(days=1)
# # Récupère les données des participants pour une course
# def get_participants(date_str, reunion_number, course_number, courses_data):
#     """Récupère les participants pour une course spécifique"""
#     url = f"https://online.turfinfo.api.pmu.fr/rest/client/61/programme/{date_str}/R{reunion_number}/C{course_number}/participants?specialisation=INTERNET"
    
#     headers = {
#         'accept': 'application/json',
#         'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
#     }
    
#     logging.debug(f"Fetching participants for {date_str}R{reunion_number}C{course_number}")
#     response = requests.get(url, headers=headers)
    
#     if response.status_code == 200:
#         try:
#             participants_data = response.json()
            
#             # Trouver l'ID de la course correspondante dans courses_data
#             course_id = None
#             for course in courses_data:
#                 if (course.get('numReunion') == reunion_number and 
#                     course.get('numOrdre') == course_number):
#                     course_id = course.get('id')
#                     break
            
#             if not course_id:
#                 logging.error(f"Course ID not found for {date_str}R{reunion_number}C{course_number}")
#                 return
            
#             # Sauvegarder chaque participant
#             for participant_data in participants_data.get('participants', []):
#                 try:
#                     # Filtrer les champs pour correspondre à la table pmu_participants
#                     from database.setup_database import Participant
#                     valid_fields = [column.name for column in Participant.__table__.columns]
                    
#                     filtered_data = {
#                         'id_course': course_id,  # Important: lier à la course
#                     }
                    
#                     # Ajouter les champs valides du participant
#                     for key, value in participant_data.items():
#                         if key in valid_fields:
#                             filtered_data[key] = value
                    
#                     # Traitement spécial pour certains champs JSON
#                     if 'dernierRapportDirect' in participant_data:
#                         filtered_data['dernierRapportDirect'] = json.dumps(participant_data.get('dernierRapportDirect'))
                    
#                     if 'dernierRapportReference' in participant_data:
#                         filtered_data['dernierRapportReference'] = json.dumps(participant_data.get('dernierRapportReference'))
                    
#                     # Créer et sauvegarder le participant
#                     Session = sessionmaker(bind=engine)
#                     session = Session()
                    
#                     # Vérifier si le participant existe déjà
#                     existing_participant = session.query(Participant).filter_by(
#                         id_course=course_id,
#                         numPmu=participant_data.get('numPmu')
#                     ).first()
                    
#                     if existing_participant:
#                         logging.debug(f"Participant already exists: {participant_data.get('nom')} in course {course_id}")
#                     else:
#                         new_participant = Participant(**filtered_data)
#                         session.add(new_participant)
#                         session.commit()
#                         logging.info(f"Saved participant: {participant_data.get('nom')} for course {course_id}")
                    
#                     session.close()
                
#                 except Exception as e:
#                     logging.error(f"Error saving participant {participant_data.get('nom', 'unknown')}: {str(e)}")
            
#             logging.info(f"Saved {len(participants_data.get('participants', []))} participants for course {course_id}")
        
#         except Exception as e:
#             logging.error(f"Error processing participants data for {date_str}R{reunion_number}C{course_number}: {str(e)}")
#     else:
#         logging.error(f"Failed to fetch participants: {response.status_code}, {date_str}R{reunion_number}C{course_number}")


# def scrap_participants(current_date, reunion_number, data):
#     """Récupère les participants pour chaque course d'une réunion"""
#     courses = data.get('courses', [])
    
#     for course in courses:
#         course_number = course.get('numOrdre')
#         course_id = f"{current_date.strftime('%d%m%Y')}R{reunion_number}C{course_number}"
        
#         # Construire l'URL de l'API pour les participants
#         url = f"https://online.turfinfo.api.pmu.fr/rest/client/61/programme/{current_date.strftime('%d%m%Y')}/R{reunion_number}/C{course_number}/participants?specialisation=INTERNET"
        
#         headers = {
#             'accept': 'application/json',
#             'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
#         }
        
#         logging.debug(f"Fetching participants for {course_id}")
#         response = requests.get(url, headers=headers)
        
#         if response.status_code == 200:
#             participants_data = response.json()
#             save_participants_data(participants_data, course_id)
#         else:
#             logging.error(f"Failed to fetch participants for {course_id}. Status code: {response.status_code}")

# # Dans scrapping/scrapping.py - Ajout à votre code existant

# def collect_current_odds():
#     current_date = datetime.now()
#     date_str = current_date.strftime("%d%m%Y")
    
#     logging.info(f"Collecting current odds for {date_str}")
    
#     # Récupérer les réunions du jour
#     reunion_number = 1
#     while True:
#         url = f"https://online.turfinfo.api.pmu.fr/rest/client/61/programme/{date_str}/R{reunion_number}?specialisation=INTERNET"
        
#         headers = {
#             'accept': 'application/json',
#             'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
#         }
        
#         response = requests.get(url, headers=headers)
        
#         if response.status_code == 204:
#             break
#         elif response.status_code == 200:
#             data = response.json()
            
#             for course in data.get('courses', []):
#                 # Ne traiter que les courses qui n'ont pas encore eu lieu
#                 if datetime.fromtimestamp(course.get('heureDepart')/1000) > current_date:
#                     course_number = course.get('numOrdre')
#                     update_course_odds(date_str, reunion_number, course_number)
        
#         reunion_number += 1


#     """Collecte les cotes actuelles pour les courses du jour selon votre structure"""
    
#     if date_str is None:
#         # Si aucune date n'est spécifiée, utiliser la date du jour
#         current_date = datetime.now()
#         date_str = current_date.strftime("%d%m%Y")
#     else:
#         current_date = datetime.strptime(date_str, "%d%m%Y")
    
#     logging.info(f"Collecte des cotes courantes pour {date_str}")
    
#     # Récupérer toutes les réunions du jour
#     reunion_number = 1
#     while True:
#         url = f"https://online.turfinfo.api.pmu.fr/rest/client/61/programme/{date_str}/R{reunion_number}?specialisation=INTERNET"
        
#         headers = {
#             'accept': 'application/json',
#             'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
#         }
        
#         response = requests.get(url, headers=headers)
        
#         if response.status_code == 204:
#             break
#         elif response.status_code == 200:
#             data = response.json()
#             courses = data.get('courses', [])
            
#             for course in courses:
#                 course_number = course.get('numOrdre')
#                 collect_course_odds(date_str, reunion_number, course_number)
        
#         reunion_number += 1

# # Met à jour les cotes d'une course
# def update_course_odds(date_str, reunion_number, course_number):
#     url = f"https://online.turfinfo.api.pmu.fr/rest/client/61/programme/{date_str}/R{reunion_number}/C{course_number}/participants?specialisation=INTERNET"
    
#     headers = {
#         'accept': 'application/json',
#         'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
#     }
    
#     response = requests.get(url, headers=headers)
    
#     if response.status_code == 200:
#         participants_data = response.json().get('participants', [])
        
#         # Mettre à jour les cotes dans la base de données
#         from database.database import update_odds
#         update_odds(date_str, reunion_number, course_number, participants_data)
#     else:
#         logging.error(f"Failed to update odds: {response.status_code}, {date_str}R{reunion_number}C{course_number}")

# def collect_course_odds(date_str, reunion_number, course_number):
#     """Collecte les cotes pour une course spécifique selon votre structure"""
    
#     url = f"https://online.turfinfo.api.pmu.fr/rest/client/61/programme/{date_str}/R{reunion_number}/C{course_number}/participants?specialisation=INTERNET"
    
#     headers = {
#         'accept': 'application/json',
#         'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
#     }
    
#     response = requests.get(url, headers=headers)
    
#     if response.status_code == 200:
#         data = response.json()
#         participants = data.get('participants', [])
        
#         Session = sessionmaker(bind=Engine)
#         session = Session()
        
#         # Récupérer la course en utilisant votre structure
#         course = session.query(Course).filter_by(
#             numReunion=reunion_number,
#             numOrdre=course_number
#         ).first()
        
#         if course:
#             for p_data in participants:
#                 # Trouver le participant dans la base selon votre structure
#                 participant = session.query(Participant).filter_by(
#                     id_course=course.id,
#                     numPmu=p_data.get('numPmu')
#                 ).first()
                
#                 if participant and 'dernierRapportDirect' in p_data and 'rapport' in p_data['dernierRapportDirect']:
#                     cote_value = p_data['dernierRapportDirect']['rapport']
                    
#                     # Mettre à jour la dernière cote enregistrée
#                     participant.dernierRapportDirect = p_data['dernierRapportDirect']
                    
#                     # Récupérer la dernière cote enregistrée pour ce participant selon votre structure
#                     last_cote = session.query(CoteEvolution).filter_by(
#                         id_participant=participant.id
#                     ).order_by(CoteEvolution.horodatage.desc()).first()
                    
#                     variation = None
#                     if last_cote:
#                         variation = cote_value - last_cote.cote
                    
#                     # Enregistrer la nouvelle cote
#                     new_cote = CoteEvolution(
#                         id_participant=participant.id,
#                         cote=cote_value,
#                         variation=variation
#                     )
#                     session.add(new_cote)
                    
#                     logging.info(f"Mise à jour des cotes pour {participant.nom}: {cote_value} (variation: {variation})")
            
#             session.commit()
        
#         session.close()

#     """Collecte les cotes pour une course spécifique"""
    
#     url = f"https://online.turfinfo.api.pmu.fr/rest/client/61/programme/{date_str}/R{reunion_number}/C{course_number}/participants?specialisation=INTERNET"
    
#     headers = {
#         'accept': 'application/json',
#         'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
#     }
    
#     response = requests.get(url, headers=headers)
    
#     if response.status_code == 200:
#         data = response.json()
#         participants = data.get('participants', [])
        
#         Session = sessionmaker(bind=Engine)
#         session = Session()
        
#         # Récupérer la course
#         course = session.query(Course).filter_by(
#             numReunion=reunion_number,
#             numOrdre=course_number
#         ).first()
        
#         if course:
#             for p_data in participants:
#                 # Trouver le participant dans la base
#                 participant = session.query(Participant).filter_by(
#                     course_id=course.id,
#                     numPmu=p_data.get('numPmu')
#                 ).first()
                
#                 if participant and 'dernierRapportDirect' in p_data:
#                     cote_value = p_data['dernierRapportDirect'].get('rapport')
                    
#                     if cote_value:
#                         # Récupérer la dernière cote enregistrée pour ce participant
#                         last_cote = session.query(CoteEvolution).filter_by(
#                             participant_id=participant.id
#                         ).order_by(CoteEvolution.timestamp.desc()).first()
                        
#                         variation = None
#                         if last_cote:
#                             variation = cote_value - last_cote.valeur_cote
                        
#                         # Enregistrer la nouvelle cote
#                         new_cote = CoteEvolution(
#                             participant_id=participant.id,
#                             valeur_cote=cote_value,
#                             variation=variation
#                         )
#                         session.add(new_cote)
                        
#                         logging.info(f"Updated odds for {participant.nom}: {cote_value} (variation: {variation})")
            
#             session.commit()
        
#         session.close()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import logging
import requests
import time
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

# Import des modules personnalisés
from database.setup_database import (
    Base, Course, Participant, Hippodrome, Pays, Reunion, 
    Cheval, Jockey, Participation, CoteEvolution, Incident, 
    CommentaireCourse, PhotoArrivee
)

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Configuration de la base de données
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "pmu_ia",
    "port": "3306",
}
engine = create_engine(f"mysql+mysqlconnector://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}")
Session = sessionmaker(bind=engine)

# Assurez-vous que toutes les tables sont créées
Base.metadata.create_all(engine)

def get_race_dates(start_date, end_date):
    """Calcule les dates intermédiaires entre deux dates données"""
    current_date = start_date
    race_dates = []

    while current_date <= end_date:
        race_dates.append(current_date.strftime("%d%m%Y"))
        current_date += timedelta(days=1)

    return race_dates

def save_pays(pays_data):
    """Sauvegarde les données d'un pays"""
    session = Session()
    try:
        if not pays_data or not pays_data.get('code'):
            return None
            
        existing_pays = session.query(Pays).filter_by(code=pays_data.get('code')).first()
        if not existing_pays:
            pays_obj = Pays(**pays_data)
            session.add(pays_obj)
            session.commit()
            logging.info(f"Saved pays: {pays_data.get('libelle')}")
            return pays_obj.code
        return existing_pays.code
    except Exception as e:
        session.rollback()
        logging.error(f"Error saving pays: {str(e)}")
        return None
    finally:
        session.close()

def save_hippodrome(hippodrome_data):
    """Sauvegarde les données d'un hippodrome"""
    session = Session()
    try:
        if not hippodrome_data or not hippodrome_data.get('code'):
            return None
            
        existing_hippodrome = session.query(Hippodrome).filter_by(code=hippodrome_data.get('code')).first()
        if not existing_hippodrome:
            hippodrome_obj = Hippodrome(**hippodrome_data)
            session.add(hippodrome_obj)
            session.commit()
            logging.info(f"Saved hippodrome: {hippodrome_data.get('libelleLong')}")
            return hippodrome_obj.code
        return existing_hippodrome.code
    except Exception as e:
        session.rollback()
        logging.error(f"Error saving hippodrome: {str(e)}")
        return None
    finally:
        session.close()

def save_reunion(reunion_data):
    """Sauvegarde les données d'une réunion"""
    session = Session()
    try:
        # Conversion de la date
        if 'dateReunion' in reunion_data and isinstance(reunion_data['dateReunion'], int):
            reunion_data['dateReunion'] = datetime.utcfromtimestamp(reunion_data['dateReunion'] / 1000.0)
        
        # Vérifier si la réunion existe déjà
        existing_reunion = (session.query(Reunion)
                           .filter_by(
                               dateReunion=reunion_data.get('dateReunion'),
                               numOfficiel=reunion_data.get('numOfficiel')
                           ).first())
        
        if existing_reunion:
            return existing_reunion.id
        
        # Préparer les données pour la réunion
        data_to_save = {}
        for key, value in reunion_data.items():
            if key not in ['hippodrome', 'pays', 'courses', 'parisEvenement', 'meteo', 'offresInternet', 'regionHippique', 'cagnottes', 'prochaineCourse']:
                data_to_save[key] = value
        
        # Ajouter les clés étrangères
        if 'hippodrome' in reunion_data and reunion_data['hippodrome']:
            data_to_save['hippodrome_code'] = reunion_data['hippodrome'].get('code')
        
        if 'pays' in reunion_data and reunion_data['pays']:
            data_to_save['pays_code'] = reunion_data['pays'].get('code')
        
        # Ajouter les données météo si présentes
        if 'meteo' in reunion_data and reunion_data['meteo']:
            meteo = reunion_data['meteo']
            if 'nebulositeCode' in meteo:
                data_to_save['nebulositeCode'] = meteo.get('nebulositeCode')
            if 'nebulositeLibelleCourt' in meteo:
                data_to_save['nebulositeLibelleCourt'] = meteo.get('nebulositeLibelleCourt')
            if 'nebulositeLibelleLong' in meteo:
                data_to_save['nebulositeLibelleLong'] = meteo.get('nebulositeLibelleLong')
            if 'temperature' in meteo:
                data_to_save['temperature'] = meteo.get('temperature')
            if 'forceVent' in meteo:
                data_to_save['forceVent'] = meteo.get('forceVent')
            if 'directionVent' in meteo:
                data_to_save['directionVent'] = meteo.get('directionVent')
        
        # Créer et sauvegarder la réunion
        reunion_obj = Reunion(**data_to_save)
        session.add(reunion_obj)
        session.commit()
        
        logging.info(f"Saved reunion: {reunion_data.get('numOfficiel')} at {reunion_data.get('dateReunion')}")
        return reunion_obj.id
    
    except Exception as e:
        session.rollback()
        logging.error(f"Error saving reunion: {str(e)}")
        return None
    finally:
        session.close()

def save_course(course_data, reunion_id=None):
    """Sauvegarde les données d'une course"""
    session = Session()
    try:
        # Conversion de l'heure de départ
        if 'heureDepart' in course_data and isinstance(course_data['heureDepart'], int):
            course_data['heureDepart'] = datetime.utcfromtimestamp(course_data['heureDepart'] / 1000.0)
        
        # Vérifier si la course existe déjà
        existing_course = (session.query(Course)
                          .filter_by(
                              heureDepart=course_data.get('heureDepart'),
                              numReunion=course_data.get('numReunion'),
                              numOrdre=course_data.get('numOrdre')
                          ).first())
        
        if existing_course:
            return existing_course.id
        
        # Préparer les données pour la course
        data_to_save = {}
        for key, value in course_data.items():
            if hasattr(Course, key) and key not in ['hippodrome', 'participants', 'ecuries', 'photosArrivee', 'commentaireApresCourse', 'incidents']:
                data_to_save[key] = value
        
        # Ajouter la clé étrangère hippodrome
        if 'hippodrome' in course_data and course_data['hippodrome']:
            data_to_save['hippodrome_code'] = course_data['hippodrome'].get('codeHippodrome')
        
        # Créer et sauvegarder la course
        course_obj = Course(**data_to_save)
        session.add(course_obj)
        session.commit()
        
        course_id = course_obj.id
        
        # Sauvegarder les éléments associés
        if 'commentaireApresCourse' in course_data and course_data['commentaireApresCourse']:
            save_commentaire(course_data['commentaireApresCourse'], course_id)
        
        if 'incidents' in course_data and course_data['incidents']:
            for incident in course_data['incidents']:
                save_incident(incident, course_id)
        
        if 'photosArrivee' in course_data and course_data['photosArrivee']:
            for photo in course_data['photosArrivee']:
                save_photo(photo, course_id)
        
        logging.info(f"Saved course: {course_data.get('libelle')} (ID: {course_id})")
        return course_id
    
    except Exception as e:
        session.rollback()
        logging.error(f"Error saving course: {str(e)}")
        return None
    finally:
        session.close()

def save_incident(incident_data, course_id):
    """Sauvegarde un incident de course"""
    session = Session()
    try:
        incident_obj = Incident(
            id_course=course_id,
            type_incident=incident_data.get('type'),
            numero_participants=json.dumps(incident_data.get('numeroParticipants', []))
        )
        session.add(incident_obj)
        session.commit()
        logging.debug(f"Saved incident for course {course_id}: {incident_data.get('type')}")
        return incident_obj.id
    except Exception as e:
        session.rollback()
        logging.error(f"Error saving incident: {str(e)}")
        return None
    finally:
        session.close()

def save_commentaire(commentaire_data, course_id):
    """Sauvegarde un commentaire de course"""
    session = Session()
    try:
        commentaire_obj = CommentaireCourse(
            id_course=course_id,
            texte=commentaire_data.get('texte'),
            source=commentaire_data.get('source')
        )
        session.add(commentaire_obj)
        session.commit()
        logging.debug(f"Saved commentaire for course {course_id}")
        return commentaire_obj.id
    except Exception as e:
        session.rollback()
        logging.error(f"Error saving commentaire: {str(e)}")
        return None
    finally:
        session.close()

def save_photo(photo_data, course_id):
    """Sauvegarde une photo d'arrivée"""
    session = Session()
    try:
        photo_obj = PhotoArrivee(
            id_course=course_id,
            url=photo_data.get('url'),
            height=photo_data.get('heightSize'),
            width=photo_data.get('widthSize'),
            is_original=photo_data.get('originalSize', False)
        )
        session.add(photo_obj)
        session.commit()
        logging.debug(f"Saved photo for course {course_id}")
        return photo_obj.id
    except Exception as e:
        session.rollback()
        logging.error(f"Error saving photo: {str(e)}")
        return None
    finally:
        session.close()

def save_participant(participant_data, course_id):
    """Sauvegarde un participant à une course"""
    session = Session()
    try:
        # Vérifier si le participant existe déjà
        existing_participant = session.query(Participant).filter_by(
            id_course=course_id,
            numPmu=participant_data.get('numPmu')
        ).first()
        
        if existing_participant:
            return existing_participant.id
        
        # Préparer les données du participant
        data_to_save = {
            'id_course': course_id,
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
        }
        
        # Traitement des champs JSON
        if 'dernierRapportDirect' in participant_data:
            data_to_save['dernierRapportDirect'] = json.dumps(participant_data.get('dernierRapportDirect'))
        
        if 'dernierRapportReference' in participant_data:
            data_to_save['dernierRapportReference'] = json.dumps(participant_data.get('dernierRapportReference'))
        
        # Créer et sauvegarder le participant
        new_participant = Participant(**data_to_save)
        session.add(new_participant)
        session.commit()
        
        # Enregistrer les données du cheval et du jockey
        save_cheval_jockey(participant_data, course_id)
        
        logging.info(f"Saved participant: {participant_data.get('nom')} for course {course_id}")
        return new_participant.id
    
    except Exception as e:
        session.rollback()
        logging.error(f"Error saving participant {participant_data.get('nom', 'unknown')}: {str(e)}")
        return None
    finally:
        session.close()

def save_cheval_jockey(participant_data, course_id):
    """Sauvegarde les données du cheval et du jockey, et crée une participation"""
    session = Session()
    try:
        # Données du cheval
        cheval_data = {
            'nom': participant_data.get('nom'),
            'age': participant_data.get('age'),
            'sexe': participant_data.get('sexe'),
            'proprietaire': participant_data.get('proprietaire')
        }
        
        if 'nomPere' in participant_data:
            cheval_data['nomPere'] = participant_data.get('nomPere')
        
        if 'nomMere' in participant_data:
            cheval_data['nomMere'] = participant_data.get('nomMere')
        
        # Vérifier si le cheval existe déjà
        cheval = session.query(Cheval).filter_by(nom=cheval_data['nom']).first()
        if not cheval:
            cheval = Cheval(**cheval_data)
            session.add(cheval)
            session.flush()  # Pour obtenir l'ID
        
        # Données du jockey
        jockey_nom = participant_data.get('driver')
        if jockey_nom:
            jockey_data = {
                'nom': jockey_nom,
                'pays': participant_data.get('pays', '')
            }
            
            # Vérifier si le jockey existe déjà
            jockey = session.query(Jockey).filter_by(nom=jockey_data['nom']).first()
            if not jockey:
                jockey = Jockey(**jockey_data)
                session.add(jockey)
                session.flush()  # Pour obtenir l'ID
        else:
            jockey = None
        
        # Créer une participation
        if cheval and jockey:
            participation_data = {
                'id_course': course_id,
                'id_cheval': cheval.id,
                'id_jockey': jockey.id,
                'position': participant_data.get('ordreArrivee'),
                'poids': participant_data.get('poids', participant_data.get('handicapPoids')),
                'est_forfait': participant_data.get('statut') == 'NON_PARTANT',
                'statut': participant_data.get('statut')
            }
            
            # Ajouter les cotes
            if 'dernierRapportDirect' in participant_data and participant_data['dernierRapportDirect'] and 'rapport' in participant_data['dernierRapportDirect']:
                participation_data['cote_actuelle'] = participant_data['dernierRapportDirect']['rapport']
            
            if 'dernierRapportReference' in participant_data and participant_data['dernierRapportReference'] and 'rapport' in participant_data['dernierRapportReference']:
                participation_data['cote_initiale'] = participant_data['dernierRapportReference']['rapport']
            
            # Vérifier si la participation existe déjà
            existing_participation = session.query(Participation).filter_by(
                id_course=course_id,
                id_cheval=cheval.id,
                id_jockey=jockey.id
            ).first()
            
            if not existing_participation:
                participation = Participation(**participation_data)
                session.add(participation)
        
        session.commit()
        return True
    
    except Exception as e:
        session.rollback()
        logging.error(f"Error saving cheval/jockey: {str(e)}")
        return False
    finally:
        session.close()

def get_participants(date_str, reunion_number, course_number, courses_data):
    """Récupère et sauvegarde les participants pour une course spécifique"""
    url = f"https://online.turfinfo.api.pmu.fr/rest/client/61/programme/{date_str}/R{reunion_number}/C{course_number}/participants?specialisation=INTERNET"
    
    headers = {
        'accept': 'application/json',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    logging.debug(f"Fetching participants for {date_str}R{reunion_number}C{course_number}")
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            participants_data = response.json()
            
            # Trouver l'ID de la course
            course_id = None
            for course in courses_data:
                if course.get('numReunion') == reunion_number and course.get('numOrdre') == course_number:
                    course_id = course.get('id')
                    break
            
            if not course_id:
                # Si l'ID n'est pas trouvé dans courses_data, chercher dans la base de données
                session = Session()
                course = session.query(Course).filter_by(
                    numReunion=reunion_number,
                    numOrdre=course_number
                ).first()
                session.close()
                
                if course:
                    course_id = course.id
            
            if not course_id:
                logging.error(f"Course ID not found for {date_str}R{reunion_number}C{course_number}")
                return False
            
            # Sauvegarder chaque participant
            count = 0
            for participant_data in participants_data.get('participants', []):
                if save_participant(participant_data, course_id):
                    count += 1
            
            logging.info(f"Saved {count} participants for course {course_id}")
            return True
        else:
            logging.error(f"Failed to fetch participants: {response.status_code}, {date_str}R{reunion_number}C{course_number}")
            return False
    
    except Exception as e:
        logging.error(f"Error in get_participants for {date_str}R{reunion_number}C{course_number}: {str(e)}")
        return False

def save_race_data(reunion_data):
    """Traite et sauvegarde les données d'une réunion et ses courses"""
    try:
        # Sauvegarder les données de pays et d'hippodrome
        if 'pays' in reunion_data and reunion_data['pays']:
            save_pays(reunion_data['pays'])
        
        if 'hippodrome' in reunion_data and reunion_data['hippodrome']:
            save_hippodrome(reunion_data['hippodrome'])
        
        # Sauvegarder la réunion
        reunion_id = save_reunion(reunion_data)
        
        if not reunion_id:
            logging.warning(f"Failed to save reunion {reunion_data.get('numOfficiel')}")
            return []
        
        # Sauvegarder les courses
        courses_saved = []
        for course_data in reunion_data.get('courses', []):
            course_id = save_course(course_data, reunion_id)
            
            if course_id:
                courses_saved.append({
                    'id': course_id,
                    'numReunion': course_data.get('numReunion'),
                    'numOrdre': course_data.get('numOrdre')
                })
        
        logging.info(f"Saved {len(courses_saved)} courses for reunion {reunion_data.get('numOfficiel')}")
        return courses_saved
    
    except Exception as e:
        logging.error(f"Error in save_race_data: {str(e)}")
        return []

def call_api_between_dates(start_date, end_date):
    """Collecte les données pour une période donnée"""
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime("%d%m%Y")
        reunion_number = 1
        
        logging.info(f"Processing date: {current_date.strftime('%Y-%m-%d')}")
        
        while True:
            base_url = "https://online.turfinfo.api.pmu.fr/rest/client/61/programme/{}/{}?specialisation=INTERNET"
            url = base_url.format(date_str, f"R{reunion_number}")
            
            headers = {
                'accept': 'application/json',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            
            logging.debug(f"Requesting API for {date_str}, R{reunion_number}")
            
            try:
                response = requests.get(url, headers=headers)
                
                if response.status_code == 204:
                    # Plus de réunion ce jour-là
                    logging.info(f"No more reunions for {current_date.strftime('%Y-%m-%d')}")
                    break
                elif response.status_code == 200:
                    # Courses disponibles pour cette réunion
                    data = response.json()
                    logging.info(f"Processing reunion {reunion_number} with {len(data.get('courses', []))} courses")
                    
                    # Sauvegarder les données de la réunion et des courses
                    courses_data = save_race_data(data)
                    
                    # Pour chaque course, récupérer les participants
                    for course in data.get('courses', []):
                        course_number = course.get('numOrdre')
                        try:
                            get_participants(date_str, reunion_number, course_number, courses_data)
                        except Exception as e:
                            logging.error(f"Error processing participants for {date_str}R{reunion_number}C{course_number}: {str(e)}")
                else:
                    logging.error(f"API request failed: {response.status_code}, Date: {date_str}, Reunion: {reunion_number}")
            
            except Exception as e:
                logging.error(f"Error processing {date_str}R{reunion_number}: {str(e)}")
            
            # Attendre un peu entre les requêtes pour ne pas surcharger l'API
            time.sleep(0.5)
            reunion_number += 1
        
        current_date += timedelta(days=1)

def main():
    """Fonction principale du script"""
    import argparse
    parser = argparse.ArgumentParser(description='Script de scraping des données PMU')
    parser.add_argument('--start', type=str, help='Date de début (format YYYY-MM-DD)')
    parser.add_argument('--end', type=str, help='Date de fin (format YYYY-MM-DD)')
    parser.add_argument('--days', type=int, default=30, help='Nombre de jours à récupérer (par défaut: 30)')
    
    args = parser.parse_args()
    
    # Définir les dates de début et de fin
    if args.start:
        start_date = datetime.strptime(args.start, "%Y-%m-%d")
    else:
        start_date = datetime.now() - timedelta(days=args.days)
    
    if args.end:
        end_date = datetime.strptime(args.end, "%Y-%m-%d")
    else:
        end_date = datetime.now()
    
    logging.info(f"Starting scraping from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    
    # Lancer le scraping
    call_api_between_dates(start_date, end_date)
    
    logging.info("Scraping complete")

if __name__ == "__main__":
    main()