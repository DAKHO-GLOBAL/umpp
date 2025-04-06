# #!/usr/bin/env python3
# # -*- coding: utf-8 -*-

# import json
# import logging
# import requests
# import time
# from datetime import datetime, timedelta
# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker
# from sqlalchemy.exc import SQLAlchemyError

# # Configuration du logging
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(levelname)s - %(message)s',
#     datefmt='%Y-%m-%d %H:%M:%S'
# )

# # Import des modules personnalisés - important d'importer après la config logging
# from database.setup_database import Base, Course, Participant, Hippodrome, Pays, Reunion
# from database.setup_database import Cheval, Jockey, Participation, CoteEvolution, engine

# # Assurez-vous que toutes les tables sont créées
# Base.metadata.create_all(engine)
# Session = sessionmaker(bind=engine)

# # Mapping des champs API vers les colonnes de base de données
# COURSE_MAPPING = {
#     'heureDepart': 'date_heure',
#     'libelle': 'libelle',
#     'distance': 'distance',
#     'distanceUnit': 'distanceUnit',
#     'numOrdre': 'num_course',
#     'specialite': 'type_course'
# }

# def get_race_dates(start_date, end_date):
#     """Calcule les dates intermédiaires entre deux dates données"""
#     current_date = start_date
#     race_dates = []

#     while current_date <= end_date:
#         race_dates.append(current_date.strftime("%d%m%Y"))
#         current_date += timedelta(days=1)

#     return race_dates

# def save_pays(pays_data):
#     """Sauvegarde les données d'un pays"""
#     if not pays_data or not pays_data.get('code'):
#         return None
    
#     session = Session()
#     try:
#         existing_pays = session.query(Pays).filter_by(code=pays_data.get('code')).first()
#         if not existing_pays:
#             pays_obj = Pays(
#                 code=pays_data.get('code'),
#                 libelle=pays_data.get('libelle')
#             )
#             session.add(pays_obj)
#             session.commit()
#             logging.info(f"Saved pays: {pays_data.get('libelle')}")
#             return pays_obj.code
#         return existing_pays.code
#     except Exception as e:
#         session.rollback()
#         logging.error(f"Error saving pays: {str(e)}")
#         return None
#     finally:
#         session.close()

# def save_hippodrome(hippodrome_data):
#     """Sauvegarde les données d'un hippodrome"""
#     if not hippodrome_data or not hippodrome_data.get('code'):
#         return None
    
#     session = Session()
#     try:
#         existing_hippodrome = session.query(Hippodrome).filter_by(code=hippodrome_data.get('code')).first()
#         if not existing_hippodrome:
#             hippodrome_obj = Hippodrome(
#                 code=hippodrome_data.get('code'),
#                 libelleCourt=hippodrome_data.get('libelleCourt'),
#                 libelleLong=hippodrome_data.get('libelleLong')
#             )
#             session.add(hippodrome_obj)
#             session.commit()
#             logging.info(f"Saved hippodrome: {hippodrome_data.get('libelleLong')}")
#             return hippodrome_obj.code
#         return existing_hippodrome.code
#     except Exception as e:
#         session.rollback()
#         logging.error(f"Error saving hippodrome: {str(e)}")
#         return None
#     finally:
#         session.close()

# def save_reunion(reunion_data):
#     """Sauvegarde les données d'une réunion"""
#     session = Session()
#     try:
#         # Conversion de la date
#         date_reunion = None
#         if 'dateReunion' in reunion_data and isinstance(reunion_data['dateReunion'], int):
#             date_reunion = datetime.utcfromtimestamp(reunion_data['dateReunion'] / 1000.0)
        
#         # Vérifier si la réunion existe déjà
#         existing_reunion = (session.query(Reunion)
#                            .filter_by(
#                                dateReunion=date_reunion,
#                                numOfficiel=reunion_data.get('numOfficiel')
#                            ).first())
        
#         if existing_reunion:
#             return existing_reunion.id
        
#         # Préparer les données pour la réunion
#         reunion_obj = Reunion(
#             dateReunion=date_reunion,
#             numOfficiel=reunion_data.get('numOfficiel'),
#             numExterne=reunion_data.get('numExterne'),
#             nature=reunion_data.get('nature'),
#             audience=reunion_data.get('audience'),
#             statut=reunion_data.get('statut')
#         )
        
#         # Ajouter les clés étrangères
#         if 'hippodrome' in reunion_data and reunion_data['hippodrome'] and 'code' in reunion_data['hippodrome']:
#             reunion_obj.hippodrome_code = reunion_data['hippodrome'].get('code')
        
#         if 'pays' in reunion_data and reunion_data['pays'] and 'code' in reunion_data['pays']:
#             reunion_obj.pays_code = reunion_data['pays'].get('code')
        
#         # Ajouter les données météo si présentes
#         if 'meteo' in reunion_data and reunion_data['meteo']:
#             meteo = reunion_data['meteo']
#             if hasattr(reunion_obj, 'nebulositeCode'):
#                 reunion_obj.nebulositeCode = meteo.get('nebulositeCode')
#             if hasattr(reunion_obj, 'nebulositeLibelleCourt'):
#                 reunion_obj.nebulositeLibelleCourt = meteo.get('nebulositeLibelleCourt')
#             if hasattr(reunion_obj, 'nebulositeLibelleLong'):
#                 reunion_obj.nebulositeLibelleLong = meteo.get('nebulositeLibelleLong')
#             if hasattr(reunion_obj, 'temperature'):
#                 reunion_obj.temperature = meteo.get('temperature')
#             if hasattr(reunion_obj, 'forceVent'):
#                 reunion_obj.forceVent = meteo.get('forceVent')
#             if hasattr(reunion_obj, 'directionVent'):
#                 reunion_obj.directionVent = meteo.get('directionVent')
        
#         # Créer et sauvegarder la réunion
#         session.add(reunion_obj)
#         session.commit()
        
#         logging.info(f"Saved reunion: {reunion_data.get('numOfficiel')} at {date_reunion}")
#         return reunion_obj.id
    
#     except Exception as e:
#         session.rollback()
#         logging.error(f"Error saving reunion: {str(e)}")
#         return None
#     finally:
#         session.close()

# def save_course(course_data, reunion_id=None):
#     """Sauvegarde les données d'une course"""
#     session = Session()
#     try:
#         # Conversion de l'heure de départ
#         date_heure = None
#         if 'heureDepart' in course_data and isinstance(course_data['heureDepart'], int):
#             date_heure = datetime.utcfromtimestamp(course_data['heureDepart'] / 1000.0)
        
#         # Vérifier si la course existe déjà
#         existing_course = None
#         if date_heure:
#             existing_course = (session.query(Course)
#                               .filter_by(
#                                   date_heure=date_heure,
#                                   num_course=course_data.get('numOrdre')
#                               ).first())
        
#         if existing_course:
#             return existing_course.id
        
#         # Préparer les données de base pour la course
#         course_obj = Course(
#             date_heure=date_heure,
#             num_course=course_data.get('numOrdre'),
#             libelle=course_data.get('libelle'),
#             type_course=course_data.get('specialite'),
#             distance=course_data.get('distance'),
#             terrain=""  # Champ obligatoire dans votre schéma mais pas dans l'API
#         )
        
#         # Lieu (hippodrome)
#         if 'hippodrome' in course_data and course_data['hippodrome'] and 'libelleLong' in course_data['hippodrome']:
#             course_obj.lieu = course_data['hippodrome'].get('libelleLong')
        
#         # Ordre d'arrivée si disponible
#         if 'ordreArrivee' in course_data:
#             course_obj.ordreArrivee = json.dumps(course_data['ordreArrivee'])
        
#         # Créer et sauvegarder la course
#         session.add(course_obj)
#         session.commit()
        
#         course_id = course_obj.id
#         logging.info(f"Saved course: {course_data.get('libelle')} (ID: {course_id})")
#         return course_id
    
#     except Exception as e:
#         session.rollback()
#         logging.error(f"Error saving course: {str(e)}")
#         return None
#     finally:
#         session.close()

# def save_participant(participant_data, course_id):
#     """Sauvegarde un participant à une course"""
#     if not course_id:
#         logging.error("Cannot save participant: course_id is missing")
#         return None
        
#     session = Session()
#     try:
#         # Vérifier si le participant existe déjà
#         existing_participant = session.query(Participant).filter_by(
#             id_course=course_id,
#             numPmu=participant_data.get('numPmu')
#         ).first()
        
#         if existing_participant:
#             return existing_participant.id
        
#         # Préparer les données du participant
#         participant_obj = Participant(
#             id_course=course_id,
#             numPmu=participant_data.get('numPmu'),
#             nom=participant_data.get('nom'),
#             age=participant_data.get('age'),
#             sexe=participant_data.get('sexe'),
#             race=participant_data.get('race'),
#             statut=participant_data.get('statut'),
#             driver=participant_data.get('driver'),
#             entraineur=participant_data.get('entraineur'),
#             proprietaire=participant_data.get('proprietaire'),
#             musique=participant_data.get('musique'),
#             incident=participant_data.get('incident'),
#             ordreArrivee=participant_data.get('ordreArrivee'),
#             tempsObtenu=participant_data.get('tempsObtenu'),
#             reductionKilometrique=participant_data.get('reductionKilometrique')
#         )
        
#         # Traitement des champs JSON
#         if 'dernierRapportDirect' in participant_data:
#             participant_obj.dernierRapportDirect = json.dumps(participant_data.get('dernierRapportDirect'))
        
#         if 'dernierRapportReference' in participant_data:
#             participant_obj.dernierRapportReference = json.dumps(participant_data.get('dernierRapportReference'))
        
#         # Créer et sauvegarder le participant
#         session.add(participant_obj)
#         session.commit()
        
#         # Enregistrer les données du cheval et du jockey
#         try:
#             save_cheval_jockey(participant_data, course_id)
#         except Exception as e:
#             logging.warning(f"Could not save cheval/jockey data: {str(e)}")
        
#         logging.info(f"Saved participant: {participant_data.get('nom')} for course {course_id}")
#         return participant_obj.id
    
#     except Exception as e:
#         session.rollback()
#         logging.error(f"Error saving participant {participant_data.get('nom', 'unknown')}: {str(e)}")
#         return None
#     finally:
#         session.close()

# def save_cheval_jockey(participant_data, course_id):
#     """Sauvegarde les données du cheval et du jockey, et crée une participation"""
#     session = Session()
#     try:
#         # Données du cheval
#         cheval_data = {
#             'nom': participant_data.get('nom'),
#             'age': participant_data.get('age'),
#             'sexe': participant_data.get('sexe'),
#             'proprietaire': participant_data.get('proprietaire')
#         }
        
#         # Vérifier si le cheval existe déjà
#         cheval = session.query(Cheval).filter_by(nom=cheval_data['nom']).first()
#         if not cheval:
#             cheval = Cheval(**cheval_data)
#             session.add(cheval)
#             session.flush()  # Pour obtenir l'ID
        
#         # Données du jockey
#         jockey_nom = participant_data.get('driver')
#         if jockey_nom:
#             # Vérifier si le jockey existe déjà
#             jockey = session.query(Jockey).filter_by(nom=jockey_nom).first()
#             if not jockey:
#                 jockey = Jockey(
#                     nom=jockey_nom,
#                     pays=participant_data.get('pays', '')
#                 )
#                 session.add(jockey)
#                 session.flush()  # Pour obtenir l'ID
#         else:
#             jockey = None
        
#         # Créer une participation
#         if cheval and jockey:
#             # Vérifier si la participation existe déjà
#             existing_participation = session.query(Participation).filter_by(
#                 id_course=course_id,
#                 id_cheval=cheval.id,
#                 id_jockey=jockey.id
#             ).first()
            
#             if not existing_participation:
#                 # Préparer les données de participation
#                 participation_data = {
#                     'id_course': course_id,
#                     'id_cheval': cheval.id,
#                     'id_jockey': jockey.id,
#                     'position': participant_data.get('ordreArrivee'),
#                     'est_forfait': participant_data.get('statut') == 'NON_PARTANT',
#                     'statut': participant_data.get('statut')
#                 }
                
#                 # Gérer le poids
#                 if 'poids' in participant_data:
#                     participation_data['poids'] = participant_data.get('poids')
#                 elif 'handicapPoids' in participant_data:
#                     participation_data['poids'] = participant_data.get('handicapPoids')
                
#                 # Ajouter les cotes
#                 if 'dernierRapportDirect' in participant_data and participant_data['dernierRapportDirect'] and 'rapport' in participant_data['dernierRapportDirect']:
#                     participation_data['cote_actuelle'] = participant_data['dernierRapportDirect']['rapport']
                
#                 if 'dernierRapportReference' in participant_data and participant_data['dernierRapportReference'] and 'rapport' in participant_data['dernierRapportReference']:
#                     participation_data['cote_initiale'] = participant_data['dernierRapportReference']['rapport']
                
#                 participation = Participation(**participation_data)
#                 session.add(participation)
        
#         session.commit()
#         return True
    
#     except Exception as e:
#         session.rollback()
#         logging.error(f"Error saving cheval/jockey: {str(e)}")
#         return False
#     finally:
#         session.close()

# def get_participants(date_str, reunion_number, course_number, courses_saved):
#     """Récupère et sauvegarde les participants pour une course spécifique"""
#     url = f"https://online.turfinfo.api.pmu.fr/rest/client/61/programme/{date_str}/R{reunion_number}/C{course_number}/participants?specialisation=INTERNET"
    
#     headers = {
#         'accept': 'application/json',
#         'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
#     }
    
#     logging.debug(f"Fetching participants for {date_str}R{reunion_number}C{course_number}")
    
#     try:
#         response = requests.get(url, headers=headers)
        
#         if response.status_code == 200:
#             participants_data = response.json()
            
#             # Trouver la bonne course dans les courses sauvegardées
#             course_id = None
#             for course in courses_saved:
#                 if (course.get('numReunion') == reunion_number and
#                     course.get('numOrdre') == course_number):
#                     course_id = course.get('id')
#                     break
            
#             if not course_id:
#                 logging.error(f"Course ID not found for {date_str}R{reunion_number}C{course_number}")
#                 return False
            
#             # Sauvegarder chaque participant
#             count = 0
#             for participant_data in participants_data.get('participants', []):
#                 if save_participant(participant_data, course_id):
#                     count += 1
            
#             logging.info(f"Saved {count} participants for course {course_id}")
#             return True
#         else:
#             logging.error(f"Failed to fetch participants: {response.status_code}, {date_str}R{reunion_number}C{course_number}")
#             return False
    
#     except Exception as e:
#         logging.error(f"Error in get_participants for {date_str}R{reunion_number}C{course_number}: {str(e)}")
#         return False

# def save_race_data(reunion_data):
#     """Traite et sauvegarde les données d'une réunion et ses courses"""
#     try:
#         # Sauvegarder les données de pays et d'hippodrome
#         if 'pays' in reunion_data and reunion_data['pays']:
#             save_pays(reunion_data['pays'])
        
#         if 'hippodrome' in reunion_data and reunion_data['hippodrome']:
#             save_hippodrome(reunion_data['hippodrome'])
        
#         # Sauvegarder la réunion
#         reunion_id = save_reunion(reunion_data)
        
#         if not reunion_id:
#             logging.warning(f"Failed to save reunion {reunion_data.get('numOfficiel')}")
#             return []
        
#         # Sauvegarder les courses
#         courses_saved = []
#         for course_data in reunion_data.get('courses', []):
#             course_id = save_course(course_data, reunion_id)
            
#             if course_id:
#                 courses_saved.append({
#                     'id': course_id,
#                     'numReunion': course_data.get('numReunion'),
#                     'numOrdre': course_data.get('numOrdre')
#                 })
        
#         logging.info(f"Saved {len(courses_saved)} courses for reunion {reunion_data.get('numOfficiel')}")
#         return courses_saved
    
#     except Exception as e:
#         logging.error(f"Error in save_race_data: {str(e)}")
#         return []

# def call_api_between_dates(start_date, end_date):
#     """Collecte les données pour une période donnée"""
#     current_date = start_date
#     while current_date <= end_date:
#         date_str = current_date.strftime("%d%m%Y")
#         reunion_number = 1
        
#         logging.info(f"Processing date: {current_date.strftime('%Y-%m-%d')}")
        
#         while True:
#             base_url = "https://online.turfinfo.api.pmu.fr/rest/client/61/programme/{}/{}?specialisation=INTERNET"
#             url = base_url.format(date_str, f"R{reunion_number}")
            
#             headers = {
#                 'accept': 'application/json',
#                 'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
#             }
            
#             logging.debug(f"Requesting API for {date_str}, R{reunion_number}")
            
#             try:
#                 response = requests.get(url, headers=headers)
                
#                 if response.status_code == 204:
#                     # Plus de réunion ce jour-là
#                     logging.info(f"No more reunions for {current_date.strftime('%Y-%m-%d')}")
#                     break
#                 elif response.status_code == 200:
#                     # Courses disponibles pour cette réunion
#                     data = response.json()
#                     logging.info(f"Processing reunion {reunion_number} with {len(data.get('courses', []))} courses")
                    
#                     # Sauvegarder les données de la réunion et des courses
#                     courses_saved = save_race_data(data)
                    
#                     # Pour chaque course, récupérer les participants
#                     for course in data.get('courses', []):
#                         course_number = course.get('numOrdre')
#                         try:
#                             get_participants(date_str, reunion_number, course_number, courses_saved)
#                         except Exception as e:
#                             logging.error(f"Error processing participants for {date_str}R{reunion_number}C{course_number}: {str(e)}")
#                 else:
#                     logging.error(f"API request failed: {response.status_code}, Date: {date_str}, Reunion: {reunion_number}")
            
#             except Exception as e:
#                 logging.error(f"Error processing {date_str}R{reunion_number}: {str(e)}")
            
#             # Attendre un peu entre les requêtes pour ne pas surcharger l'API
#             time.sleep(0.5)
#             reunion_number += 1
        
#         current_date += timedelta(days=1)

# def main():
#     """Fonction principale du script"""
#     import argparse
#     parser = argparse.ArgumentParser(description='Script de scraping des données PMU')
#     parser.add_argument('--start', type=str, help='Date de début (format YYYY-MM-DD)')
#     parser.add_argument('--end', type=str, help='Date de fin (format YYYY-MM-DD)')
#     parser.add_argument('--days', type=int, default=30, help='Nombre de jours à récupérer (par défaut: 30)')
    
#     args = parser.parse_args()
    
#     # Définir les dates de début et de fin
#     if args.start:
#         start_date = datetime.strptime(args.start, "%Y-%m-%d")
#     else:
#         start_date = datetime.now() - timedelta(days=args.days)
    
#     if args.end:
#         end_date = datetime.strptime(args.end, "%Y-%m-%d")
#     else:
#         end_date = datetime.now()
    
#     logging.info(f"Starting scraping from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    
#     # Lancer le scraping
#     call_api_between_dates(start_date, end_date)
    
#     logging.info("Scraping complete")

# if __name__ == "__main__":
#     main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import requests
import json
from datetime import datetime, timedelta
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
import time

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Importez vos modèles de base de données
from database.setup_database import CommentaireCourse, CoteHistorique, Incident, PhotoArrivee, PmuCourse, engine, Course, Reunion, Pays, Hippodrome, Base, Participant, Cheval, Jockey, Participation

# Créez une session
Session = sessionmaker(bind=engine)
def save_commentaire(course_id, commentaire_data):
    if not commentaire_data or 'texte' not in commentaire_data:
        return
        
    session = Session()
    try:
        commentaire = CommentaireCourse(
            id_course=course_id,
            texte=commentaire_data['texte'],
            source=commentaire_data.get('source')
        )
        session.add(commentaire)
        session.commit()
    except Exception as e:
        session.rollback()
        logging.error(f"Error saving comment: {str(e)}")
    finally:
        session.close()

def save_incidents(course_id, incidents_data):
    if not incidents_data:
        return
        
    session = Session()
    try:
        for incident in incidents_data:
            inc = Incident(
                id_course=course_id,
                type_incident=incident.get('type'),
                numero_participants=json.dumps(incident.get('numeroParticipants', []))
            )
            session.add(inc)
        session.commit()
    except Exception as e:
        session.rollback()
        logging.error(f"Error saving incidents: {str(e)}")
    finally:
        session.close()
def save_photos(course_id, photos_data):
    if not photos_data:
        return
        
    session = Session()
    try:
        for photo in photos_data:
            p = PhotoArrivee(
                id_course=course_id,
                url=photo.get('url'),
                height=photo.get('heightSize'),
                width=photo.get('widthSize'),
                is_original=photo.get('originalSize', False)
            )
            session.add(p)
        session.commit()
    except Exception as e:
        session.rollback()
        logging.error(f"Error saving photos: {str(e)}")
    finally:
        session.close()
def save_course_from_json(course_data):
    """Sauvegarde une course à partir des données JSON complètes"""
    session = Session()
    try:
        # Vérifiez d'abord les colonnes réelles de la table PmuCourse
        inspector = inspect(engine)
        actual_columns = [column['name'] for column in inspector.get_columns('pmu_courses')]
        logging.info(f"Available columns in pmu_courses table: {actual_columns}")
        
        # Conversion de l'heure de départ
        date_heure = None
        if 'heureDepart' in course_data and isinstance(course_data['heureDepart'], int):
            date_heure = datetime.fromtimestamp(course_data['heureDepart'] / 1000.0)
        
        # Créer un dictionnaire avec les données de la course
        course_dict = {}
        
        # Mapping des champs de l'API vers les champs de la base de données
        field_mapping = {
            'heureDepart': 'heureDepart',
            'distance': 'distance',
            'numOrdre': 'numOrdre',
            'specialite': 'specialite',
            'libelle': 'libelle',
            'libelleCourt': 'libelleCourt',
            'distanceUnit': 'distanceUnit',
            'corde': 'corde',
            'discipline': 'discipline',
            'nombreDeclaresPartants': 'nombreDeclaresPartants',
            'ordreArrivee': 'ordreArrivee',
            'categorieStatut': 'categorieStatut',
            'statut': 'statut',
            'dureeCourse': 'dureeCourse',
            'numReunion': 'numReunion',
            'numExterne': 'numExterne',
            'categorieParticularite': 'categorieParticularite',
            'conditionSexe': 'conditionSexe',
            'montantPrix': 'montantPrix',
            'timezoneOffset': 'timezoneOffset'
        }
        
        # Ajouter uniquement les champs qui existent dans notre table
        for api_field, db_field in field_mapping.items():
            if db_field in actual_columns and api_field in course_data:
                # Traitement spécial pour les dates et les JSON
                if api_field == 'heureDepart':
                    course_dict[db_field] = date_heure
                elif api_field == 'ordreArrivee' and db_field in actual_columns:
                    # Convertir en JSON si nécessaire
                    if course_data.get(api_field):
                        course_dict[db_field] = course_data.get(api_field)  # Déjà JSON dans PmuCourse
                else:
                    course_dict[db_field] = course_data.get(api_field)
            
        # Ajouter l'hippodrome s'il existe
        if 'hippodrome' in course_data and 'code' in course_data['hippodrome'] and 'hippodrome_code' in actual_columns:
            course_dict['hippodrome_code'] = course_data['hippodrome'].get('code')
        
        # Créer un nouvel objet PmuCourse
        course_obj = PmuCourse(**course_dict)
        
        # Sauvegarder
        session.add(course_obj)
        session.commit()
        
        course_id = course_obj.id
        logging.info(f"Successfully saved PmuCourse {course_data.get('libelle')} with ID {course_id}")
        
        # Maintenant que nous avons course_id, nous pouvons sauvegarder les données associées
        if 'commentaireApresCourse' in course_data and course_id:
            save_commentaire(course_id, course_data['commentaireApresCourse'])
        
        if 'incidents' in course_data and course_id:
            save_incidents(course_id, course_data['incidents'])
        
        if 'photosArrivee' in course_data and course_id:
            save_photos(course_id, course_data['photosArrivee'])
        
        # Option: créer aussi un enregistrement dans la table "courses" simplifiée
        # pour garder la compatibilité avec votre modèle de prédiction
        try:
            simple_course = Course(
                date_heure=date_heure,
                lieu=course_data['hippodrome'].get('libelleLong') if 'hippodrome' in course_data else None,
                type_course=course_data.get('specialite'),
                distance=course_data.get('distance'),
                terrain="",  # Champ obligatoire
                num_course=course_data.get('numOrdre'),
                libelle=course_data.get('libelle'),
                pmu_course_id=course_id  # Liaison avec la table pmu_courses
            )
            session.add(simple_course)
            session.commit()
            logging.info(f"Also created simplified Course record with ID {simple_course.id}")
        except Exception as e:
            logging.warning(f"Could not create simplified Course record: {str(e)}")
        
        return course_id
        
    except Exception as e:
        session.rollback()
        logging.error(f"Error saving course: {str(e)}")
        return None
    finally:
        session.close()


def save_reunion_data(reunion_data):
    """Sauvegarde les données d'une réunion complète"""
    try:
        # Sauvegarder les données du pays
        if 'pays' in reunion_data and reunion_data['pays']:
            save_pays(reunion_data['pays'])
        
        # Sauvegarder les données de l'hippodrome
        if 'hippodrome' in reunion_data and reunion_data['hippodrome']:
            save_hippodrome(reunion_data['hippodrome'])
        
        # Sauvegarder la réunion
        reunion_id = save_reunion(reunion_data)
        
        # Sauvegarder chaque course
        courses_saved = []
        for course_data in reunion_data.get('courses', []):
            course_id = save_course_from_json(course_data)
            
            if course_id:
                courses_saved.append({
                    'id': course_id,
                    'numReunion': course_data.get('numReunion'),
                    'numOrdre': course_data.get('numOrdre')
                })
                
                # Essayer d'obtenir les participants maintenant
                date_str = datetime.fromtimestamp(reunion_data['dateReunion'] / 1000).strftime("%d%m%Y")
                reunion_number = course_data.get('numReunion')
                course_number = course_data.get('numOrdre')
                
                # Attendre un peu avant de faire une autre requête
                time.sleep(1)
                
                get_participants(date_str, reunion_number, course_number, course_id)
        
        logging.info(f"Saved {len(courses_saved)} courses for reunion {reunion_data.get('numOfficiel')}")
        return courses_saved
    
    except Exception as e:
        logging.error(f"Error in save_reunion_data: {str(e)}")
        return []

def save_pays(pays_data):
    """Sauvegarde les données d'un pays"""
    if not pays_data or not pays_data.get('code'):
        return None
    
    session = Session()
    try:
        existing_pays = session.query(Pays).filter_by(code=pays_data.get('code')).first()
        if not existing_pays:
            pays_obj = Pays(
                code=pays_data.get('code'),
                libelle=pays_data.get('libelle')
            )
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
    if not hippodrome_data or not hippodrome_data.get('code'):
        return None
    
    session = Session()
    try:
        existing_hippodrome = session.query(Hippodrome).filter_by(code=hippodrome_data.get('code')).first()
        if not existing_hippodrome:
            hippodrome_obj = Hippodrome(
                code=hippodrome_data.get('code'),
                libelleCourt=hippodrome_data.get('libelleCourt'),
                libelleLong=hippodrome_data.get('libelleLong')
            )
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
        # Vérifier les colonnes existantes
        inspector = inspect(engine)
        valid_columns = [column['name'] for column in inspector.get_columns('pmu_reunions')]
        
        # Conversion de la date
        date_reunion = None
        if 'dateReunion' in reunion_data and isinstance(reunion_data['dateReunion'], int):
            date_reunion = datetime.fromtimestamp(reunion_data['dateReunion'] / 1000.0)
        
        # Vérifier si la réunion existe déjà
        existing_reunion = None
        if date_reunion:
            existing_reunion = (session.query(Reunion)
                              .filter_by(
                                  dateReunion=date_reunion,
                                  numOfficiel=reunion_data.get('numOfficiel')
                              ).first())
        
        if existing_reunion:
            return existing_reunion.id
        
        # Créer un dictionnaire avec les données valides
        reunion_dict = {
            'dateReunion': date_reunion,
            'numOfficiel': reunion_data.get('numOfficiel'),
            'numExterne': reunion_data.get('numExterne'),
            'nature': reunion_data.get('nature'),
            'audience': reunion_data.get('audience'),
            'statut': reunion_data.get('statut')
        }
        
        # Ajouter uniquement les champs qui existent dans la table
        reunion_dict = {k: v for k, v in reunion_dict.items() if k in valid_columns}
        
        # Ajouter les clés étrangères
        if 'hippodrome_code' in valid_columns and 'hippodrome' in reunion_data and reunion_data['hippodrome'] and 'code' in reunion_data['hippodrome']:
            reunion_dict['hippodrome_code'] = reunion_data['hippodrome'].get('code')
        
        if 'pays_code' in valid_columns and 'pays' in reunion_data and reunion_data['pays'] and 'code' in reunion_data['pays']:
            reunion_dict['pays_code'] = reunion_data['pays'].get('code')
        
        # Ajouter les données météo si présentes
        if 'meteo' in reunion_data and reunion_data['meteo']:
            meteo = reunion_data['meteo']
            meteo_fields = [
                'nebulositeCode', 'nebulositeLibelleCourt', 'nebulositeLibelleLong',
                'temperature', 'forceVent', 'directionVent'
            ]
            
            for field in meteo_fields:
                if field in valid_columns and field in meteo:
                    reunion_dict[field] = meteo.get(field)
        
        # Créer l'objet Reunion
        reunion_obj = Reunion(**reunion_dict)
        session.add(reunion_obj)
        session.commit()
        
        logging.info(f"Saved reunion: {reunion_data.get('numOfficiel')} at {date_reunion}")
        return reunion_obj.id
    
    except Exception as e:
        session.rollback()
        logging.error(f"Error saving reunion: {str(e)}")
        return None
    finally:
        session.close()

def get_participants(date_str, reunion_number, course_number, course_id):
    """Récupère et sauvegarde les participants pour une course spécifique"""
    url = f"https://online.turfinfo.api.pmu.fr/rest/client/61/programme/{date_str}/R{reunion_number}/C{course_number}/participants?specialisation=INTERNET"
    
    headers = {
        'accept': 'application/json',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    logging.info(f"Fetching participants for {date_str}R{reunion_number}C{course_number}")
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            participants_data = response.json()
            
            # Sauvegarder chaque participant
            count = 0
            for participant_data in participants_data.get('participants', []):
                if save_participant(participant_data, course_id):
                    count += 1
            
            logging.info(f"Saved {count} participants for course {course_id}")
            return True
        elif response.status_code == 204:
            # C'est normal dans certains cas (pas de participants disponibles)
            logging.info(f"No participants data available for {date_str}R{reunion_number}C{course_number} (status 204)")
            return True
        else:
            logging.error(f"Failed to fetch participants: {response.status_code}, {date_str}R{reunion_number}C{course_number}")
            return False
    
    except Exception as e:
        logging.error(f"Error in get_participants for {date_str}R{reunion_number}C{course_number}: {str(e)}")
        return False

def save_participant(participant_data, course_id):
    """Sauvegarde un participant à une course dans la table pmu_participants"""
    session = Session()
    try:
        # D'abord sauvegarder le cheval et le jockey
        cheval_id = save_cheval(participant_data)
        jockey_id = save_jockey(participant_data)
        
        # Vérifier si le participant existe déjà
        existing_participant = session.query(Participant).filter_by(
            id_course=course_id,
            numPmu=participant_data.get('numPmu')
        ).first()
        
        # Préparer les données du participant
        participant_dict = {
            'id_course': course_id,
            'numPmu': participant_data.get('numPmu'),
            'nom': participant_data.get('nom'),
            'age': participant_data.get('age'),
            'sexe': participant_data.get('sexe'),
            'race': participant_data.get('race'),
            'statut': participant_data.get('statut'),
            'driver': participant_data.get('driver'),
            'jockey': participant_data.get('jockey'),
            'entraineur': participant_data.get('entraineur'),
            'proprietaire': participant_data.get('proprietaire'),
            'musique': participant_data.get('musique'),
            'incident': participant_data.get('incident'),
            'ordreArrivee': participant_data.get('ordreArrivee'),
            'tempsObtenu': participant_data.get('tempsObtenu'),
            'reductionKilometrique': participant_data.get('reductionKilometrique'),
            'dernierRapportDirect': participant_data.get('dernierRapportDirect'),
            'dernierRapportReference': participant_data.get('dernierRapportReference'),
            'cheval_id': cheval_id,
            'jockey_id': jockey_id
        }
        
        # Gérer les cas spéciaux
        if 'handicapPoids' in participant_data:
            participant_dict['handicapPoids'] = participant_data.get('handicapPoids')
        
        if existing_participant:
            # Mettre à jour les champs
            for key, value in participant_dict.items():
                if hasattr(existing_participant, key):
                    setattr(existing_participant, key, value)
            
            logging.info(f"Updated participant {participant_data.get('nom')} in course {course_id}")
            participant_id = existing_participant.id
        else:
            # Créer un nouveau participant
            new_participant = Participant(**participant_dict)
            session.add(new_participant)
            session.flush()  # Pour obtenir l'ID avant le commit
            participant_id = new_participant.id
            logging.info(f"Created new participant {participant_data.get('nom')} in course {course_id}")
        
        session.commit()
        
        # Option: créer aussi un enregistrement dans la table participations
        try:
            # Trouver l'ID de la course simplifiée
            course_simple = session.query(Course).filter_by(pmu_course_id=course_id).first()
            
            if course_simple:
                # Extraire les cotes si disponibles
                cote_actuelle = None
                if isinstance(participant_data.get('dernierRapportDirect'), dict) and 'rapport' in participant_data['dernierRapportDirect']:
                    cote_actuelle = participant_data['dernierRapportDirect']['rapport']
                
                cote_initiale = None
                if isinstance(participant_data.get('dernierRapportReference'), dict) and 'rapport' in participant_data['dernierRapportReference']:
                    cote_initiale = participant_data['dernierRapportReference']['rapport']
                
                # Créer/mettre à jour participation
                participation_simple = session.query(Participation).filter_by(
                    id_course=course_simple.id,
                    id_cheval=cheval_id
                ).first()
                
                if participation_simple:
                    participation_simple.position = participant_data.get('ordreArrivee')
                    participation_simple.cote_actuelle = cote_actuelle
                    participation_simple.cote_initiale = cote_initiale
                    participation_simple.statut = participant_data.get('statut')
                    participation_simple.est_forfait = participant_data.get('statut') == 'NON_PARTANT'
                    participation_simple.id_jockey = jockey_id
                    if 'handicapPoids' in participant_data:
                        participation_simple.poids = participant_data.get('handicapPoids')
                else:
                    new_participation = Participation(
                        id_course=course_simple.id,
                        id_cheval=cheval_id,
                        id_jockey=jockey_id,
                        position=participant_data.get('ordreArrivee'),
                        cote_actuelle=cote_actuelle,
                        cote_initiale=cote_initiale,
                        statut=participant_data.get('statut'),
                        est_forfait=participant_data.get('statut') == 'NON_PARTANT',
                        poids=participant_data.get('handicapPoids') if 'handicapPoids' in participant_data else None,
                        numPmu=participant_data.get('numPmu')
                    )
                    session.add(new_participation)
                
                session.commit()
        except Exception as e:
            logging.warning(f"Could not create/update simplified participation: {str(e)}")
        
        return True
        
    except Exception as e:
        session.rollback()
        logging.error(f"Error saving participant: {str(e)}")
        return False
    finally:
        session.close()
        
def save_cheval(participant_data):
    """Sauvegarde les données d'un cheval"""
    session = Session()
    try:
        # Vérifier si le cheval existe déjà
        cheval = session.query(Cheval).filter_by(nom=participant_data.get('nom')).first()
        
        if cheval:
            return cheval.id
        
        # Créer un nouveau cheval
        cheval_data = {
            'nom': participant_data.get('nom'),
            'age': participant_data.get('age'),
            'sexe': participant_data.get('sexe'),
            'proprietaire': participant_data.get('proprietaire')
        }
        
        # Ajouter généalogie si disponible
        if 'nomPere' in participant_data:
            cheval_data['nomPere'] = participant_data.get('nomPere')
        
        if 'nomMere' in participant_data:
            cheval_data['nomMere'] = participant_data.get('nomMere')
        
        cheval = Cheval(**cheval_data)
        session.add(cheval)
        session.commit()
        
        return cheval.id
    
    except Exception as e:
        session.rollback()
        logging.error(f"Error saving cheval: {str(e)}")
        return None
    finally:
        session.close()

def save_jockey(participant_data):
    """Sauvegarde les données d'un jockey"""
    # Utiliser le driver pour les courses attelées
    jockey_name = participant_data.get('driver') or participant_data.get('jockey')
    
    if not jockey_name:
        return None
        
    session = Session()
    try:
        # Vérifier si le jockey existe déjà
        jockey = session.query(Jockey).filter_by(nom=jockey_name).first()
        
        if jockey:
            return jockey.id
        
        # Créer un nouveau jockey
        jockey_data = {
            'nom': jockey_name,
            'pays': participant_data.get('pays', '')
        }
        
        jockey = Jockey(**jockey_data)
        session.add(jockey)
        session.commit()
        
        return jockey.id
    
    except Exception as e:
        session.rollback()
        logging.error(f"Error saving jockey: {str(e)}")
        return None
    finally:
        session.close()

def process_json_data(json_data):
    """Traite les données JSON d'une réunion complète"""
    try:
        # Vérifier si les données sont sous forme de chaîne
        if isinstance(json_data, str):
            reunion_data = json.loads(json_data)
        else:
            reunion_data = json_data
        
        # Sauvegarder les données
        save_reunion_data(reunion_data)
        
        return True
    except Exception as e:
        logging.error(f"Error processing JSON data: {str(e)}")
        return False

def scrape_today():
    """Récupère les données des courses du jour"""
    today = datetime.now()
    date_str = today.strftime("%d%m%Y")
    
    logging.info(f"Scraping data for today: {today.strftime('%Y-%m-%d')}")
    
    reunion_number = 1
    
    while True:
        url = f"https://online.turfinfo.api.pmu.fr/rest/client/61/programme/{date_str}/R{reunion_number}?specialisation=INTERNET"
        
        headers = {
            'accept': 'application/json',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        try:
            response = requests.get(url, headers=headers)
            
            if response.status_code == 204:
                logging.info(f"No more reunions for today")
                break
            elif response.status_code == 200:
                reunion_data = response.json()
                
                logging.info(f"Processing reunion {reunion_number} with {len(reunion_data.get('courses', []))} courses")
                
                # Traiter les données de la réunion complète
                process_json_data(reunion_data)
            else:
                logging.error(f"Failed to fetch reunion: {response.status_code}")
                break
                
        except Exception as e:
            logging.error(f"Error processing reunion {reunion_number}: {str(e)}")
            break
            
        reunion_number += 1

def process_json_file(file_path):
    """Traite un fichier JSON local contenant des données PMU"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reunion_data = json.load(f)
        
        logging.info(f"Processing JSON file: {file_path}")
        
        # Traiter les données
        process_json_data(reunion_data)
        
        return True
    except Exception as e:
        logging.error(f"Error processing JSON file {file_path}: {str(e)}")
        return False
def scrape_specific_date(date):
    """Récupère les données des courses pour une date spécifique"""
    date_str = date.strftime("%d%m%Y")
    
    logging.info(f"Scraping data for date: {date.strftime('%Y-%m-%d')}")
    
    reunion_number = 1
    
    while True:
        url = f"https://online.turfinfo.api.pmu.fr/rest/client/61/programme/{date_str}/R{reunion_number}?specialisation=INTERNET"
        
        headers = {
            'accept': 'application/json',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        try:
            response = requests.get(url, headers=headers)
            
            if response.status_code == 204:
                logging.info(f"No more reunions for {date.strftime('%Y-%m-%d')}")
                break
            elif response.status_code == 200:
                reunion_data = response.json()
                
                logging.info(f"Processing reunion {reunion_number} with {len(reunion_data.get('courses', []))} courses")
                
                # Traiter les données de la réunion complète
                process_json_data(reunion_data)
            else:
                logging.error(f"Failed to fetch reunion: {response.status_code}")
                break
                
        except Exception as e:
            logging.error(f"Error processing reunion {reunion_number}: {str(e)}")
            break
            
        reunion_number += 1

def call_api_between_dates(start_date, end_date):
    """Collecte les données pour une période donnée"""
    current_date = start_date
    while current_date <= end_date:
        scrape_specific_date(current_date)
        current_date += timedelta(days=1)
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == 'file' and len(sys.argv) > 2:
            # Traiter un fichier JSON local
            process_json_file(sys.argv[2])
        elif sys.argv[1] == 'date' and len(sys.argv) > 2:
            # Récupérer les données pour une date spécifique
            date_str = sys.argv[2]
            try:
                date_obj = datetime.strptime(date_str, "%Y%m%d")
                scrape_specific_date(date_obj)
            except ValueError:
                print(f"Invalid date format. Use YYYYMMDD")
        elif sys.argv[1] == 'range' and len(sys.argv) > 2:
            # Récupérer les données pour une plage de jours
            try:
                days = int(sys.argv[2])
                today = datetime.now()
                if days >= 0:
                    # Jours dans le futur
                    start_date = today
                    end_date = today + timedelta(days=days)
                else:
                    # Jours dans le passé
                    start_date = today + timedelta(days=days)  # days est négatif
                    end_date = today
                
                logging.info(f"Scraping data from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
                call_api_between_dates(start_date, end_date)
            except ValueError:
                print("Please provide a valid number of days")
        else:
            # Usage
            print("Usage:")
            print("  python scraping.py                    - Scrape today's data")
            print("  python scraping.py file <path>        - Process a local JSON file")
            print("  python scraping.py date YYYYMMDD      - Scrape data for specific date")
            print("  python scraping.py range N            - Scrape data for N days from today")
            print("  python scraping.py range -N           - Scrape data for N days before today")
    else:
        # Récupérer les données du jour
        scrape_today()