import logging
import requests
from datetime import datetime, timedelta

from sqlalchemy import Engine
from data_traitement.traitement import save_race_data
from sqlalchemy.orm import sessionmaker

from database.database import save_participants_data
from database.setup_database import CoteEvolution, Course, Participant
# Calcul les dates intermédiaires entre deux dates données
def get_race_dates(start_date, end_date):
    current_date = start_date
    race_dates = []

    while current_date <= end_date:
        race_dates.append(current_date.strftime("%d%m%Y"))
        current_date += timedelta(days=1)

    return race_dates

# Apelle l'api pmu afin de récupérer l'ensemble des données des courses, réunions, hippodrome, participants
# Collecte les données entre deux dates
def call_api_between_dates(start_date, end_date):
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime("%d%m%Y")
        reunion_number = 1
        
        while True:
            base_url = "https://online.turfinfo.api.pmu.fr/rest/client/61/programme/{}/{}?specialisation=INTERNET"
            url = base_url.format(date_str, f"R{reunion_number}")
            
            headers = {
                'accept': 'application/json',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            
            logging.debug(f"Attempting to call API for {date_str}, R{reunion_number}")
            response = requests.get(url, headers=headers)
            
            if response.status_code == 204:
                # Plus de réunion ce jour-là
                logging.info(f"No more reunion [{reunion_number}] on {current_date} : 204")
                break
            elif response.status_code == 200:
                # Courses disponibles pour cette réunion
                data = response.json()
                logging.debug(f"Response 200 for reunions [{reunion_number}] on {current_date}")
                
                # Sauvegarder les données de courses
                courses_data = save_race_data(data)
                
                # Pour chaque course, récupérer les participants
                for course in data.get('courses', []):
                    course_number = course.get('numOrdre')
                    get_participants(date_str, reunion_number, course_number, courses_data)
            else:
                logging.error(f"API request failed: {response.status_code}, Date: {date_str}, Reunion: {reunion_number}")
            
            reunion_number += 1
        
        current_date += timedelta(days=1)
# Récupère les données des participants pour une course
def get_participants(date_str, reunion_number, course_number, courses_data):
    url = f"https://online.turfinfo.api.pmu.fr/rest/client/61/programme/{date_str}/R{reunion_number}/C{course_number}/participants?specialisation=INTERNET"
    
    headers = {
        'accept': 'application/json',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    logging.debug(f"Fetching participants for {date_str}R{reunion_number}C{course_number}")
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        participants_data = response.json()
        
        # Identifier la course dans les données sauvegardées
        course_id = None
        for course_info in courses_data:
            if (course_info['num_reunion'] == reunion_number and 
                course_info['num_course'] == course_number):
                course_id = course_info['id']
                break
        
        if course_id:
            save_participants_data(participants_data, course_id)
        else:
            logging.error(f"Course not found in saved data: {date_str}R{reunion_number}C{course_number}")
    else:
        logging.error(f"Failed to fetch participants: {response.status_code}, {date_str}R{reunion_number}C{course_number}")


def scrap_participants(current_date, reunion_number, data):
    """Récupère les participants pour chaque course d'une réunion"""
    courses = data.get('courses', [])
    
    for course in courses:
        course_number = course.get('numOrdre')
        course_id = f"{current_date.strftime('%d%m%Y')}R{reunion_number}C{course_number}"
        
        # Construire l'URL de l'API pour les participants
        url = f"https://online.turfinfo.api.pmu.fr/rest/client/61/programme/{current_date.strftime('%d%m%Y')}/R{reunion_number}/C{course_number}/participants?specialisation=INTERNET"
        
        headers = {
            'accept': 'application/json',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        logging.debug(f"Fetching participants for {course_id}")
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            participants_data = response.json()
            save_participants_data(participants_data, course_id)
        else:
            logging.error(f"Failed to fetch participants for {course_id}. Status code: {response.status_code}")

# Dans scrapping/scrapping.py - Ajout à votre code existant

def collect_current_odds():
    current_date = datetime.now()
    date_str = current_date.strftime("%d%m%Y")
    
    logging.info(f"Collecting current odds for {date_str}")
    
    # Récupérer les réunions du jour
    reunion_number = 1
    while True:
        url = f"https://online.turfinfo.api.pmu.fr/rest/client/61/programme/{date_str}/R{reunion_number}?specialisation=INTERNET"
        
        headers = {
            'accept': 'application/json',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 204:
            break
        elif response.status_code == 200:
            data = response.json()
            
            for course in data.get('courses', []):
                # Ne traiter que les courses qui n'ont pas encore eu lieu
                if datetime.fromtimestamp(course.get('heureDepart')/1000) > current_date:
                    course_number = course.get('numOrdre')
                    update_course_odds(date_str, reunion_number, course_number)
        
        reunion_number += 1


    """Collecte les cotes actuelles pour les courses du jour selon votre structure"""
    
    if date_str is None:
        # Si aucune date n'est spécifiée, utiliser la date du jour
        current_date = datetime.now()
        date_str = current_date.strftime("%d%m%Y")
    else:
        current_date = datetime.strptime(date_str, "%d%m%Y")
    
    logging.info(f"Collecte des cotes courantes pour {date_str}")
    
    # Récupérer toutes les réunions du jour
    reunion_number = 1
    while True:
        url = f"https://online.turfinfo.api.pmu.fr/rest/client/61/programme/{date_str}/R{reunion_number}?specialisation=INTERNET"
        
        headers = {
            'accept': 'application/json',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 204:
            break
        elif response.status_code == 200:
            data = response.json()
            courses = data.get('courses', [])
            
            for course in courses:
                course_number = course.get('numOrdre')
                collect_course_odds(date_str, reunion_number, course_number)
        
        reunion_number += 1

# Met à jour les cotes d'une course
def update_course_odds(date_str, reunion_number, course_number):
    url = f"https://online.turfinfo.api.pmu.fr/rest/client/61/programme/{date_str}/R{reunion_number}/C{course_number}/participants?specialisation=INTERNET"
    
    headers = {
        'accept': 'application/json',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        participants_data = response.json().get('participants', [])
        
        # Mettre à jour les cotes dans la base de données
        from database.database import update_odds
        update_odds(date_str, reunion_number, course_number, participants_data)
    else:
        logging.error(f"Failed to update odds: {response.status_code}, {date_str}R{reunion_number}C{course_number}")

def collect_course_odds(date_str, reunion_number, course_number):
    """Collecte les cotes pour une course spécifique selon votre structure"""
    
    url = f"https://online.turfinfo.api.pmu.fr/rest/client/61/programme/{date_str}/R{reunion_number}/C{course_number}/participants?specialisation=INTERNET"
    
    headers = {
        'accept': 'application/json',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        participants = data.get('participants', [])
        
        Session = sessionmaker(bind=Engine)
        session = Session()
        
        # Récupérer la course en utilisant votre structure
        course = session.query(Course).filter_by(
            numReunion=reunion_number,
            numOrdre=course_number
        ).first()
        
        if course:
            for p_data in participants:
                # Trouver le participant dans la base selon votre structure
                participant = session.query(Participant).filter_by(
                    id_course=course.id,
                    numPmu=p_data.get('numPmu')
                ).first()
                
                if participant and 'dernierRapportDirect' in p_data and 'rapport' in p_data['dernierRapportDirect']:
                    cote_value = p_data['dernierRapportDirect']['rapport']
                    
                    # Mettre à jour la dernière cote enregistrée
                    participant.dernierRapportDirect = p_data['dernierRapportDirect']
                    
                    # Récupérer la dernière cote enregistrée pour ce participant selon votre structure
                    last_cote = session.query(CoteEvolution).filter_by(
                        id_participant=participant.id
                    ).order_by(CoteEvolution.horodatage.desc()).first()
                    
                    variation = None
                    if last_cote:
                        variation = cote_value - last_cote.cote
                    
                    # Enregistrer la nouvelle cote
                    new_cote = CoteEvolution(
                        id_participant=participant.id,
                        cote=cote_value,
                        variation=variation
                    )
                    session.add(new_cote)
                    
                    logging.info(f"Mise à jour des cotes pour {participant.nom}: {cote_value} (variation: {variation})")
            
            session.commit()
        
        session.close()

    """Collecte les cotes pour une course spécifique"""
    
    url = f"https://online.turfinfo.api.pmu.fr/rest/client/61/programme/{date_str}/R{reunion_number}/C{course_number}/participants?specialisation=INTERNET"
    
    headers = {
        'accept': 'application/json',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        participants = data.get('participants', [])
        
        Session = sessionmaker(bind=Engine)
        session = Session()
        
        # Récupérer la course
        course = session.query(Course).filter_by(
            numReunion=reunion_number,
            numOrdre=course_number
        ).first()
        
        if course:
            for p_data in participants:
                # Trouver le participant dans la base
                participant = session.query(Participant).filter_by(
                    course_id=course.id,
                    numPmu=p_data.get('numPmu')
                ).first()
                
                if participant and 'dernierRapportDirect' in p_data:
                    cote_value = p_data['dernierRapportDirect'].get('rapport')
                    
                    if cote_value:
                        # Récupérer la dernière cote enregistrée pour ce participant
                        last_cote = session.query(CoteEvolution).filter_by(
                            participant_id=participant.id
                        ).order_by(CoteEvolution.timestamp.desc()).first()
                        
                        variation = None
                        if last_cote:
                            variation = cote_value - last_cote.valeur_cote
                        
                        # Enregistrer la nouvelle cote
                        new_cote = CoteEvolution(
                            participant_id=participant.id,
                            valeur_cote=cote_value,
                            variation=variation
                        )
                        session.add(new_cote)
                        
                        logging.info(f"Updated odds for {participant.nom}: {cote_value} (variation: {variation})")
            
            session.commit()
        
        session.close()