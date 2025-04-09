# data_updater.py
# api/tasks/data_updater.py
import logging
import traceback
import requests
import json
from datetime import datetime, timedelta
from sqlalchemy import text
from flask import current_app
import pandas as pd
import numpy as np
import time

from extensions import db
from models.course import Course, Participation, Cheval, Jockey, CoteHistorique
from data_traitement.traitement import save_race_data, save_participants_data

logger = logging.getLogger(__name__)

def run_scraping(days_back=7, specific_date=None):
    """
    Exécute le scraping des données PMU pour les jours spécifiés.
    
    Args:
        days_back (int): Nombre de jours en arrière à scraper
        specific_date (str): Date spécifique à scraper (format: YYYY-MM-DD)
        
    Returns:
        dict: Résultats du scraping
    """
    logger.info(f"Starting PMU data scraping task: days_back={days_back}, specific_date={specific_date}")
    
    results = {
        'start_time': datetime.now().isoformat(),
        'status': 'success',
        'courses_scraped': 0,
        'participants_scraped': 0,
        'errors': []
    }
    
    try:
        # Définir les dates à scraper
        dates_to_scrape = []
        
        if specific_date:
            # Scraper une date spécifique
            try:
                date_obj = datetime.strptime(specific_date, '%Y-%m-%d')
                dates_to_scrape.append(date_obj)
            except ValueError:
                error_msg = f"Invalid date format: {specific_date}. Expected format: YYYY-MM-DD"
                logger.error(error_msg)
                results['errors'].append(error_msg)
                results['status'] = 'error'
                return results
        else:
            # Scraper les jours précédents
            for i in range(days_back):
                date_obj = datetime.now() - timedelta(days=i)
                dates_to_scrape.append(date_obj)
        
        # Scraper chaque date
        for date_obj in dates_to_scrape:
            date_str = date_obj.strftime('%Y-%m-%d')
            logger.info(f"Scraping PMU data for date: {date_str}")
            
            courses_scraped, participants_scraped, errors = scrape_date(date_obj)
            
            results['courses_scraped'] += courses_scraped
            results['participants_scraped'] += participants_scraped
            results['errors'].extend(errors)
        
        # Mettre à jour le statut final
        if len(results['errors']) > 0:
            results['status'] = 'partial_success'
        
        results['end_time'] = datetime.now().isoformat()
        results['duration_seconds'] = (datetime.fromisoformat(results['end_time']) - 
                                      datetime.fromisoformat(results['start_time'])).total_seconds()
        
        logger.info(f"PMU data scraping completed: {results['courses_scraped']} courses scraped")
        return results
        
    except Exception as e:
        error_msg = f"Error in scraping task: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        
        results['status'] = 'error'
        results['errors'].append(error_msg)
        results['end_time'] = datetime.now().isoformat()
        results['duration_seconds'] = (datetime.fromisoformat(results['end_time']) - 
                                      datetime.fromisoformat(results['start_time'])).total_seconds()
        
        return results

def scrape_date(date_obj):
    """
    Scrape les données PMU pour une date spécifique.
    
    Args:
        date_obj (datetime): Date à scraper
        
    Returns:
        tuple: (courses_scraped, participants_scraped, errors)
    """
    date_str = date_obj.strftime('%Y-%m-%d')
    base_url = "https://online.turfinfo.pmu.fr/rest/client/1/programme"
    
    courses_scraped = 0
    participants_scraped = 0
    errors = []
    
    try:
        # Récupérer la liste des réunions pour cette date
        reunions_url = f"{base_url}/jour?dateCourse={date_str}&meteo=true&specialisation=PLAT,OBSTACLE"
        response = requests.get(reunions_url)
        
        if response.status_code != 200:
            error_msg = f"Failed to retrieve reunions for date {date_str}: HTTP {response.status_code}"
            logger.error(error_msg)
            errors.append(error_msg)
            return courses_scraped, participants_scraped, errors
        
        reunions_data = response.json()
        
        # Parcourir les réunions
        for reunion in reunions_data.get('reunions', []):
            reunion_num = reunion.get('numReunion')
            logger.info(f"Processing reunion {reunion_num} for date {date_str}")
            
            try:
                # Récupérer les détails de la réunion
                reunion_url = f"{base_url}/reunion/{reunion_num}?dateCourse={date_str}"
                reunion_response = requests.get(reunion_url)
                
                if reunion_response.status_code != 200:
                    error_msg = f"Failed to retrieve reunion {reunion_num} details: HTTP {reunion_response.status_code}"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    continue
                
                reunion_details = reunion_response.json()
                
                # Enregistrer les données de la réunion et les courses
                saved_courses = save_race_data(reunion_details)
                courses_scraped += len(saved_courses)
                
                # Récupérer les participants pour chaque course
                for course_info in saved_courses:
                    course_id = course_info['id']
                    num_reunion = course_info['num_reunion']
                    num_course = course_info['num_course']
                    
                    try:
                        # Récupérer les participants
                        participants_url = f"{base_url}/reunion/{num_reunion}/course/{num_course}?dateCourse={date_str}"
                        participants_response = requests.get(participants_url)
                        
                        if participants_response.status_code != 200:
                            error_msg = f"Failed to retrieve participants for course {num_course}: HTTP {participants_response.status_code}"
                            logger.error(error_msg)
                            errors.append(error_msg)
                            continue
                        
                        participants_data = participants_response.json()
                        
                        # Enregistrer les participants
                        save_participants_data(participants_data, course_id)
                        participants_scraped += len(participants_data.get('participants', []))
                        
                        # Ajouter un petit délai pour éviter de surcharger l'API
                        time.sleep(0.5)
                        
                    except Exception as e:
                        error_msg = f"Error processing participants for course {num_course}: {str(e)}"
                        logger.error(error_msg)
                        errors.append(error_msg)
                        continue
                
                # Ajouter un petit délai pour éviter de surcharger l'API
                time.sleep(1)
                
            except Exception as e:
                error_msg = f"Error processing reunion {reunion_num}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
                continue
        
        return courses_scraped, participants_scraped, errors
        
    except Exception as e:
        error_msg = f"Error scraping date {date_str}: {str(e)}"
        logger.error(error_msg)
        errors.append(error_msg)
        return courses_scraped, participants_scraped, errors

def update_odds(course_id=None, all_upcoming=False):
    """
    Met à jour les cotes des courses.
    
    Args:
        course_id (int): ID de la course spécifique à mettre à jour
        all_upcoming (bool): Mettre à jour toutes les courses à venir
        
    Returns:
        dict: Résultats de la mise à jour
    """
    logger.info(f"Starting odds update task: course_id={course_id}, all_upcoming={all_upcoming}")
    
    results = {
        'start_time': datetime.now().isoformat(),
        'status': 'success',
        'courses_updated': 0,
        'odds_updated': 0,
        'errors': []
    }
    
    try:
        # Déterminer les courses à mettre à jour
        if course_id:
            # Mettre à jour une course spécifique
            courses_query = text("""
                SELECT c.id, c.pmu_course_id, pc.numReunion, pc.numOrdre, c.date_heure
                FROM courses c
                JOIN pmu_courses pc ON c.pmu_course_id = pc.id
                WHERE c.id = :course_id
            """)
            
            courses = db.session.execute(courses_query, {"course_id": course_id}).fetchall()
            
        elif all_upcoming:
            # Mettre à jour toutes les courses à venir
            now = datetime.now()
            courses_query = text("""
                SELECT c.id, c.pmu_course_id, pc.numReunion, pc.numOrdre, c.date_heure
                FROM courses c
                JOIN pmu_courses pc ON c.pmu_course_id = pc.id
                WHERE c.date_heure > :now
                ORDER BY c.date_heure ASC
            """)
            
            courses = db.session.execute(courses_query, {"now": now}).fetchall()
        else:
            error_msg = "Either course_id or all_upcoming must be specified"
            logger.error(error_msg)
            results['errors'].append(error_msg)
            results['status'] = 'error'
            return results
        
        # Parcourir les courses
        for course in courses:
            course_id = course.id
            date_str = course.date_heure.strftime('%Y-%m-%d')
            num_reunion = course.numReunion
            num_course = course.numOrdre
            
            try:
                # Récupérer les participants et leurs cotes actuelles
                base_url = "https://online.turfinfo.pmu.fr/rest/client/1/programme"
                participants_url = f"{base_url}/reunion/{num_reunion}/course/{num_course}?dateCourse={date_str}"
                
                response = requests.get(participants_url)
                
                if response.status_code != 200:
                    error_msg = f"Failed to retrieve participants for course {course_id}: HTTP {response.status_code}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
                    continue
                
                participants_data = response.json().get('participants', [])
                
                # Mettre à jour les cotes
                for participant in participants_data:
                    cheval_nom = participant.get('nom')
                    
                    # Récupérer la participation
                    participation_query = text("""
                        SELECT p.id, p.id_cheval, p.cote_actuelle
                        FROM participations p
                        JOIN chevaux c ON p.id_cheval = c.id
                        WHERE p.id_course = :course_id AND c.nom = :cheval_nom
                    """)
                    
                    participation = db.session.execute(participation_query, {
                        "course_id": course_id,
                        "cheval_nom": cheval_nom
                    }).fetchone()
                    
                    if not participation:
                        continue
                    
                    # Extraire la cote
                    cote = None
                    if participant.get('dernierRapportDirect') and 'rapport' in participant['dernierRapportDirect']:
                        cote = participant['dernierRapportDirect']['rapport']
                    
                    if not cote:
                        continue
                    
                    # Vérifier si la cote a changé
                    if participation.cote_actuelle != cote:
                        # Mettre à jour la cote actuelle
                        update_query = text("""
                            UPDATE participations
                            SET cote_actuelle = :cote
                            WHERE id = :participation_id
                        """)
                        
                        db.session.execute(update_query, {
                            "participation_id": participation.id,
                            "cote": cote
                        })
                        
                        # Enregistrer l'historique des cotes
                        history_query = text("""
                            INSERT INTO cote_historique (id_participation, horodatage, cote)
                            VALUES (:participation_id, :horodatage, :cote)
                        """)
                        
                        db.session.execute(history_query, {
                            "participation_id": participation.id,
                            "horodatage": datetime.now(),
                            "cote": cote
                        })
                        
                        results['odds_updated'] += 1
                
                db.session.commit()
                results['courses_updated'] += 1
                
                # Ajouter un petit délai pour éviter de surcharger l'API
                time.sleep(1)
                
            except Exception as e:
                db.session.rollback()
                error_msg = f"Error updating odds for course {course_id}: {str(e)}"
                logger.error(error_msg)
                results['errors'].append(error_msg)
                continue
        
        # Mettre à jour le statut final
        if len(results['errors']) > 0:
            results['status'] = 'partial_success'
        
        results['end_time'] = datetime.now().isoformat()
        results['duration_seconds'] = (datetime.fromisoformat(results['end_time']) - 
                                      datetime.fromisoformat(results['start_time'])).total_seconds()
        
        logger.info(f"Odds update completed: {results['courses_updated']} courses updated, {results['odds_updated']} odds updated")
        return results
        
    except Exception as e:
        error_msg = f"Error in odds update task: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        
        results['status'] = 'error'
        results['errors'].append(error_msg)
        results['end_time'] = datetime.now().isoformat()
        results['duration_seconds'] = (datetime.fromisoformat(results['end_time']) - 
                                      datetime.fromisoformat(results['start_time'])).total_seconds()
        
        return results

def update_results(course_id=None, all_past=False, days_back=1):
    """
    Met à jour les résultats des courses terminées.
    
    Args:
        course_id (int): ID de la course spécifique à mettre à jour
        all_past (bool): Mettre à jour toutes les courses passées sans résultats
        days_back (int): Nombre de jours en arrière à considérer
        
    Returns:
        dict: Résultats de la mise à jour
    """
    logger.info(f"Starting results update task: course_id={course_id}, all_past={all_past}, days_back={days_back}")
    
    results = {
        'start_time': datetime.now().isoformat(),
        'status': 'success',
        'courses_updated': 0,
        'errors': []
    }
    
    try:
        # Déterminer les courses à mettre à jour
        if course_id:
            # Mettre à jour une course spécifique
            courses_query = text("""
                SELECT c.id, c.pmu_course_id, pc.numReunion, pc.numOrdre, c.date_heure
                FROM courses c
                JOIN pmu_courses pc ON c.pmu_course_id = pc.id
                WHERE c.id = :course_id
            """)
            
            courses = db.session.execute(courses_query, {"course_id": course_id}).fetchall()
            
        elif all_past:
            # Mettre à jour toutes les courses passées sans résultats
            now = datetime.now()
            past_date = now - timedelta(days=days_back)
            
            courses_query = text("""
                SELECT c.id, c.pmu_course_id, pc.numReunion, pc.numOrdre, c.date_heure
                FROM courses c
                JOIN pmu_courses pc ON c.pmu_course_id = pc.id
                WHERE c.date_heure < :now 
                AND c.date_heure > :past_date
                AND c.ordreArrivee IS NULL
                ORDER BY c.date_heure DESC
            """)
            
            courses = db.session.execute(courses_query, {"now": now, "past_date": past_date}).fetchall()
        else:
            error_msg = "Either course_id or all_past must be specified"
            logger.error(error_msg)
            results['errors'].append(error_msg)
            results['status'] = 'error'
            return results
        
        # Parcourir les courses
        for course in courses:
            course_id = course.id
            date_str = course.date_heure.strftime('%Y-%m-%d')
            num_reunion = course.numReunion
            num_course = course.numOrdre
            
            try:
                # Récupérer les résultats
                base_url = "https://online.turfinfo.pmu.fr/rest/client/1/programme"
                results_url = f"{base_url}/reunion/{num_reunion}/course/{num_course}/rapports?dateCourse={date_str}"
                
                response = requests.get(results_url)
                
                if response.status_code != 200:
                    error_msg = f"Failed to retrieve results for course {course_id}: HTTP {response.status_code}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
                    continue
                
                results_data = response.json()
                
                # Vérifier si les résultats sont disponibles
                if not results_data.get('ordreArrivee'):
                    logger.info(f"No results available yet for course {course_id}")
                    continue
                
                # Mettre à jour l'ordre d'arrivée
                ordre_arrivee = results_data.get('ordreArrivee')
                
                update_query = text("""
                    UPDATE courses
                    SET ordreArrivee = :ordre_arrivee
                    WHERE id = :course_id
                """)
                
                db.session.execute(update_query, {
                    "course_id": course_id,
                    "ordre_arrivee": json.dumps(ordre_arrivee)
                })
                
                # Mettre à jour les positions des participants
                if ordre_arrivee and len(ordre_arrivee) > 0:
                    for position, horse_num in enumerate(ordre_arrivee, start=1):
                        # Trouver le participant avec ce numéro
                        participant_query = text("""
                            UPDATE participations
                            SET position = :position
                            WHERE id_course = :course_id AND numPmu = :horse_num
                        """)
                        
                        db.session.execute(participant_query, {
                            "position": position,
                            "course_id": course_id,
                            "horse_num": horse_num
                        })
                
                # Enregistrer les rapports
                if results_data.get('rapports'):
                    rapports = results_data.get('rapports')
                    
                    # Vérifier si les rapports existent déjà
                    check_query = text("""
                        SELECT id FROM rapports_pmu WHERE id_course = :course_id
                    """)
                    
                    existing = db.session.execute(check_query, {"course_id": course_id}).fetchone()
                    
                    if existing:
                        # Mettre à jour les rapports existants
                        update_rapport_query = text("""
                            UPDATE rapports_pmu
                            SET rapports_data = :rapports_data,
                                updated_at = :updated_at
                            WHERE id_course = :course_id
                        """)
                        
                        db.session.execute(update_rapport_query, {
                            "course_id": course_id,
                            "rapports_data": json.dumps(rapports),
                            "updated_at": datetime.now()
                        })
                    else:
                        # Créer de nouveaux rapports
                        insert_rapport_query = text("""
                            INSERT INTO rapports_pmu
                            (id_course, rapports_data, created_at)
                            VALUES (:course_id, :rapports_data, :created_at)
                        """)
                        
                        db.session.execute(insert_rapport_query, {
                            "course_id": course_id,
                            "rapports_data": json.dumps(rapports),
                            "created_at": datetime.now()
                        })
                
                db.session.commit()
                results['courses_updated'] += 1
                
                # Ajouter un petit délai pour éviter de surcharger l'API
                time.sleep(1)
                
            except Exception as e:
                db.session.rollback()
                error_msg = f"Error updating results for course {course_id}: {str(e)}"
                logger.error(error_msg)
                results['errors'].append(error_msg)
                continue
        
        # Mettre à jour le statut final
        if len(results['errors']) > 0:
            results['status'] = 'partial_success'
        
        results['end_time'] = datetime.now().isoformat()
        results['duration_seconds'] = (datetime.fromisoformat(results['end_time']) - 
                                      datetime.fromisoformat(results['start_time'])).total_seconds()
        
        logger.info(f"Results update completed: {results['courses_updated']} courses updated")
        return results
        
    except Exception as e:
        error_msg = f"Error in results update task: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        results['status'] = 'error'
        results['errors'].append(error_msg)
        results['end_time'] = datetime.now().isoformat()
        results['duration_seconds'] = (datetime.fromisoformat(results['end_time']) - 
                                      datetime.fromisoformat(results['start_time'])).total_seconds()
        return results
def run_all_tasks():
    """
    Exécute toutes les tâches de mise à jour des données dans l'ordre recommandé.
    
    Returns:
        dict: Résultats de toutes les tâches
    """
    logger.info("Starting all data update tasks")
    
    results = {
        'start_time': datetime.now().isoformat(),
        'scraping_results': None,
        'odds_update_results': None,
        'results_update_results': None,
        'status': 'success'
    }
    
    try:
        # Lire la configuration
        config_path = current_app.config.get('CONFIG_PATH', 'config/config.json')
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # 1. Scraping des données récentes
        days_back = config.get('scraping', {}).get('days_back', 7)
        scraping_results = run_scraping(days_back=days_back)
        results['scraping_results'] = scraping_results
        
        # Vérifier si le scraping a réussi au moins partiellement
        if scraping_results['status'] == 'error':
            logger.error("Scraping task failed, continuing with other tasks")
            results['status'] = 'partial_success'
        
        # 2. Mise à jour des cotes pour les courses à venir
        odds_update_results = update_odds(all_upcoming=True)
        results['odds_update_results'] = odds_update_results
        
        # Vérifier si la mise à jour des cotes a réussi
        if odds_update_results['status'] == 'error':
            logger.error("Odds update task failed, continuing with other tasks")
            results['status'] = 'partial_success'
        
        # 3. Mise à jour des résultats pour les courses récentes
        days_back = config.get('evaluation', {}).get('days_back', 1)
        results_update_results = update_results(all_past=True, days_back=days_back)
        results['results_update_results'] = results_update_results
        
        # Vérifier si la mise à jour des résultats a réussi
        if results_update_results['status'] == 'error':
            logger.error("Results update task failed")
            results['status'] = 'partial_success'
        
        # Calculer le temps total d'exécution
        results['end_time'] = datetime.now().isoformat()
        results['duration_seconds'] = (datetime.fromisoformat(results['end_time']) - 
                                      datetime.fromisoformat(results['start_time'])).total_seconds()
        
        # Journal de fin
        logger.info(f"All data update tasks completed with status: {results['status']}")
        logger.info(f"Total execution time: {results['duration_seconds']} seconds")
        
        return results
        
    except Exception as e:
        error_msg = f"Error executing all tasks: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        
        results['status'] = 'error'
        results['error_message'] = error_msg
        results['end_time'] = datetime.now().isoformat()
        results['duration_seconds'] = (datetime.fromisoformat(results['end_time']) - 
                                      datetime.fromisoformat(results['start_time'])).total_seconds()
        
        return results

def schedule_tasks():
    """
    Configure la planification des tâches récurrentes selon la configuration.
    Cette fonction est appelée au démarrage de l'application.
    """
    try:
        # Cette fonction serait utilisée avec un planificateur comme APScheduler
        # Pour configurer l'exécution périodique des tâches selon la configuration
        logger.info("Setting up scheduled tasks")
        
        # Lire la configuration
        config_path = current_app.config.get('CONFIG_PATH', 'config/config.json')
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Récupérer le planificateur
        scheduler = current_app.scheduler
        
        # Planifier la tâche de scraping
        scraping_config = config.get('scraping', {})
        if scraping_config.get('schedule', {}).get('frequency') == 'daily':
            time_str = scraping_config.get('schedule', {}).get('time', '00:00')
            hour, minute = map(int, time_str.split(':'))
            
            scheduler.add_job(
                run_scraping,
                'cron',
                hour=hour,
                minute=minute,
                kwargs={'days_back': scraping_config.get('days_back', 1)},
                id='daily_scraping',
                replace_existing=True
            )
            logger.info(f"Scheduled daily scraping task at {time_str}")
        
        # Planifier la mise à jour des cotes
        prediction_config = config.get('prediction', {})
        if prediction_config.get('schedule', {}).get('frequency') == 'daily':
            time_str = prediction_config.get('schedule', {}).get('time', '07:00')
            hour, minute = map(int, time_str.split(':'))
            
            scheduler.add_job(
                update_odds,
                'cron',
                hour=hour,
                minute=minute,
                kwargs={'all_upcoming': True},
                id='daily_odds_update',
                replace_existing=True
            )
            logger.info(f"Scheduled daily odds update task at {time_str}")
        
        # Planifier la mise à jour des résultats
        evaluation_config = config.get('evaluation', {})
        if evaluation_config.get('schedule', {}).get('frequency') == 'daily':
            time_str = evaluation_config.get('schedule', {}).get('time', '23:00')
            hour, minute = map(int, time_str.split(':'))
            
            scheduler.add_job(
                update_results,
                'cron',
                hour=hour,
                minute=minute,
                kwargs={'all_past': True, 'days_back': evaluation_config.get('days_back', 1)},
                id='daily_results_update',
                replace_existing=True
            )
            logger.info(f"Scheduled daily results update task at {time_str}")
        
        # Planifier l'exécution de toutes les tâches (hebdomadaire)
        if evaluation_config.get('schedule', {}).get('frequency') == 'weekly':
            time_str = evaluation_config.get('schedule', {}).get('time', '01:00')
            day = evaluation_config.get('schedule', {}).get('day', 'sunday')
            hour, minute = map(int, time_str.split(':'))
            
            scheduler.add_job(
                run_all_tasks,
                'cron',
                day_of_week=day.lower(),
                hour=hour,
                minute=minute,
                id='weekly_all_tasks',
                replace_existing=True
            )
            logger.info(f"Scheduled weekly all tasks execution on {day} at {time_str}")
        
        logger.info("All tasks scheduled successfully")
        
    except Exception as e:
        logger.error(f"Error scheduling tasks: {str(e)}")
        logger.error(traceback.format_exc())