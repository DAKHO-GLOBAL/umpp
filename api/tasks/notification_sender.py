# notification_sender.py
# notification_sender.py
# api/tasks/notification_sender.py
import logging
import traceback
from datetime import datetime, timedelta
from sqlalchemy import text
from flask import current_app

from api import db
from api.services.notification_service import NotificationService
from api.services.prediction_service import PredictionService
from api.services.course_service import CourseService

logger = logging.getLogger(__name__)

def send_notifications(notification_type=None):
    """
    Envoie des notifications aux utilisateurs selon le type spécifié.
    
    Args:
        notification_type (str): Type de notification à envoyer (prediction, odds_change, upcoming_course)
                                Si None, tous les types sont envoyés
    
    Returns:
        dict: Résultats de l'envoi de notifications
    """
    logger.info(f"Starting notification sending task: notification_type={notification_type}")
    
    results = {
        'start_time': datetime.now().isoformat(),
        'status': 'success',
        'notifications_sent': 0,
        'users_notified': 0,
        'by_type': {},
        'errors': []
    }
    
    try:
        # Initialiser le service de notification
        notification_service = NotificationService()
        
        # Déterminer les types de notifications à envoyer
        types_to_send = []
        
        if notification_type:
            types_to_send.append(notification_type)
        else:
            types_to_send = ['prediction', 'odds_change', 'upcoming_course']
        
        # Envoyer chaque type de notification
        for notif_type in types_to_send:
            try:
                # Compter avant
                count_before = results['notifications_sent']
                
                if notif_type == 'prediction':
                    prediction_results = send_prediction_notifications()
                    results['notifications_sent'] += prediction_results['notifications_sent']
                    results['users_notified'] += prediction_results['users_notified']
                    results['errors'].extend(prediction_results['errors'])
                elif notif_type == 'odds_change':
                    odds_results = send_odds_change_notifications()
                    results['notifications_sent'] += odds_results['notifications_sent']
                    results['users_notified'] += odds_results['users_notified']
                    results['errors'].extend(odds_results['errors'])
                elif notif_type == 'upcoming_course':
                    upcoming_results = send_upcoming_course_notifications()
                    results['notifications_sent'] += upcoming_results['notifications_sent']
                    results['users_notified'] += upcoming_results['users_notified']
                    results['errors'].extend(upcoming_results['errors'])
                
                # Calculer le nombre de notifications pour ce type
                count_after = results['notifications_sent']
                results['by_type'][notif_type] = count_after - count_before
                
            except Exception as e:
                error_msg = f"Error sending {notif_type} notifications: {str(e)}"
                logger.error(error_msg)
                results['errors'].append(error_msg)
                continue
        
        # Mettre à jour le statut final
        if len(results['errors']) > 0:
            results['status'] = 'partial_success'
        
        results['end_time'] = datetime.now().isoformat()
        results['duration_seconds'] = (datetime.fromisoformat(results['end_time']) - 
                                      datetime.fromisoformat(results['start_time'])).total_seconds()
        
        logger.info(f"Notification sending completed: {results['notifications_sent']} notifications sent to {results['users_notified']} users")
        return results
        
    except Exception as e:
        error_msg = f"Error in notification sending task: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        
        results['status'] = 'error'
        results['errors'].append(error_msg)
        results['end_time'] = datetime.now().isoformat()
        results['duration_seconds'] = (datetime.fromisoformat(results['end_time']) - 
                                      datetime.fromisoformat(results['start_time'])).total_seconds()
        
        return results

def send_prediction_notifications():
    """
    Envoie des notifications pour les nouvelles prédictions.
    
    Returns:
        dict: Résultats de l'envoi de notifications
    """
    logger.info("Sending prediction notifications")
    
    results = {
        'notifications_sent': 0,
        'users_notified': 0,
        'errors': []
    }
    
    try:
        # Initialiser les services
        notification_service = NotificationService()
        prediction_service = PredictionService()
        course_service = CourseService()
        
        # Récupérer les prédictions récentes (dernières 3 heures)
        three_hours_ago = datetime.now() - timedelta(hours=3)
        
        predictions_query = text("""
            SELECT p.id, p.course_id, p.prediction_type, p.prediction_data, p.created_at,
                   c.lieu, c.date_heure, c.libelle
            FROM predictions p
            JOIN courses c ON p.course_id = c.id
            WHERE p.created_at > :three_hours_ago
            AND c.date_heure > NOW()
            AND p.id NOT IN (
                SELECT DISTINCT n.data->>'prediction_id'
                FROM notifications n
                WHERE n.notification_type = 'prediction'
                AND n.data ? 'prediction_id'
            )
            ORDER BY p.created_at DESC
        """)
        
        predictions_result = db.session.execute(predictions_query, {"three_hours_ago": three_hours_ago})
        
        # Récupérer les utilisateurs qui doivent recevoir des notifications
        users_query = text("""
            SELECT u.id, u.email, u.first_name, ns.email_notifications, ns.push_notifications, 
                   ns.notify_predictions
            FROM users u
            JOIN notification_settings ns ON u.id = ns.user_id
            WHERE u.is_active = TRUE
            AND u.is_verified = TRUE
            AND ns.notify_predictions = TRUE
            AND (
                u.subscription_level != 'free'
                OR (
                    u.subscription_level = 'free'
                    AND u.created_at > :one_week_ago
                )
            )
        """)
        
        one_week_ago = datetime.now() - timedelta(days=7)
        users_result = db.session.execute(users_query, {"one_week_ago": one_week_ago})
        
        users = [
            {
                'id': row.id,
                'email': row.email,
                'first_name': row.first_name,
                'email_notifications': row.email_notifications,
                'push_notifications': row.push_notifications
            }
            for row in users_result
        ]
        
        # Pour chaque prédiction, envoyer des notifications aux utilisateurs
        for prediction in predictions_result:
            try:
                # Préparer les données de la notification
                course_id = prediction.course_id
                prediction_id = prediction.id
                prediction_type = prediction.prediction_type
                prediction_data = prediction.prediction_data
                
                course_info = {
                    'id': course_id,
                    'lieu': prediction.lieu,
                    'date_heure': prediction.date_heure.isoformat(),
                    'libelle': prediction.libelle
                }
                
                # Générer des commentaires automatisés
                comments = prediction_service.generate_prediction_comments(prediction_data, detailed=False)
                
                # Préparer les picks intéressants
                interesting_picks = []
                try:
                    # Convertir prediction_data en liste si ce n'est pas déjà le cas
                    if isinstance(prediction_data, str):
                        import json
                        prediction_data = json.loads(prediction_data)
                    
                    # Extraire les 3 premiers chevaux
                    sorted_horses = sorted(prediction_data, key=lambda x: x.get('predicted_rank', float('inf')))
                    interesting_picks = [
                        {
                            'id_cheval': horse.get('id_cheval'),
                            'cheval_nom': horse.get('cheval_nom', f"Cheval {horse.get('id_cheval')}"),
                            'cote': horse.get('cote_actuelle'),
                            'probabilite': horse.get('in_top3_prob', 0)
                        }
                        for horse in sorted_horses[:3]
                    ]
                except Exception as e:
                    logger.error(f"Error extracting interesting picks: {str(e)}")
                
                # Pour chaque utilisateur, créer et envoyer la notification
                notified_users = set()
                
                for user in users:
                    user_id = user['id']
                    
                    # Vérifier si l'utilisateur a déjà consulté cette course
                    check_query = text("""
                        SELECT id
                        FROM prediction_usage
                        WHERE user_id = :user_id
                        AND course_id = :course_id
                    """)
                    
                    already_viewed = db.session.execute(check_query, {
                        "user_id": user_id,
                        "course_id": course_id
                    }).fetchone() is not None
                    
                    # Si l'utilisateur a déjà consulté cette course, ne pas envoyer de notification
                    if already_viewed:
                        continue
                    
                    # Créer la notification
                    notification_id = notification_service.create_course_prediction_notification(
                        user_id=user_id,
                        course_id=course_id,
                        prediction_type=prediction_type,
                        interesting_picks=interesting_picks
                    )
                    
                    if notification_id:
                        results['notifications_sent'] += 1
                        notified_users.add(user_id)
                    
                # Mettre à jour le nombre d'utilisateurs notifiés
                results['users_notified'] = len(notified_users)
                
            except Exception as e:
                error_msg = f"Error sending prediction notification for course {prediction.course_id}: {str(e)}"
                logger.error(error_msg)
                results['errors'].append(error_msg)
                continue
        
        return results
        
    except Exception as e:
        error_msg = f"Error in send_prediction_notifications: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        results['errors'].append(error_msg)
        return results

def send_odds_change_notifications():
    """
    Envoie des notifications pour les changements significatifs de cotes.
    
    Returns:
        dict: Résultats de l'envoi de notifications
    """
    logger.info("Sending odds change notifications")
    
    results = {
        'notifications_sent': 0,
        'users_notified': 0,
        'errors': []
    }
    
    try:
        # Initialiser les services
        notification_service = NotificationService()
        prediction_service = PredictionService()
        course_service = CourseService()
        
        # Récupérer les changements récents de cotes (dernière heure)
        one_hour_ago = datetime.now() - timedelta(hours=1)
        
        odds_changes_query = text("""
            WITH latest_odds AS (
                SELECT p.id_course, p.id_cheval, p.cote_actuelle,
                       c.nom AS cheval_nom, co.lieu, co.date_heure, co.libelle
                FROM participations p
                JOIN chevaux c ON p.id_cheval = c.id
                JOIN courses co ON p.id_course = co.id
                WHERE co.date_heure > NOW()
            ),
            previous_odds AS (
                SELECT ch.id_participation, MAX(ch.horodatage) AS last_update, ch.cote
                FROM cote_historique ch
                JOIN participations p ON ch.id_participation = p.id
                JOIN courses c ON p.id_course = c.id
                WHERE ch.horodatage < :one_hour_ago
                AND c.date_heure > NOW()
                GROUP BY ch.id_participation
            ),
            significant_changes AS (
                SELECT lo.id_course, lo.id_cheval, lo.cheval_nom, lo.cote_actuelle,
                       po.cote AS cote_precedente,
                       ((lo.cote_actuelle - po.cote) / po.cote) * 100 AS variation_percent,
                       lo.lieu, lo.date_heure, lo.libelle
                FROM latest_odds lo
                JOIN participations p ON lo.id_course = p.id_course AND lo.id_cheval = p.id_cheval
                JOIN previous_odds po ON po.id_participation = p.id
                WHERE ABS(((lo.cote_actuelle - po.cote) / po.cote) * 100) > 15  -- Variation de plus de 15%
                AND lo.cote_actuelle < 30  -- Ignorer les cotes trop élevées
            )
            SELECT * FROM significant_changes
            ORDER BY ABS(variation_percent) DESC
        """)
        
        odds_changes_result = db.session.execute(odds_changes_query, {"one_hour_ago": one_hour_ago})
        
        # Regrouper les changements par course
        changes_by_course = {}
        
        for change in odds_changes_result:
            course_id = change.id_course
            
            if course_id not in changes_by_course:
                changes_by_course[course_id] = {
                    'course_info': {
                        'id': course_id,
                        'lieu': change.lieu,
                        'date_heure': change.date_heure.isoformat(),
                        'libelle': change.libelle
                    },
                    'changes': []
                }
            
            changes_by_course[course_id]['changes'].append({
                'id_cheval': change.id_cheval,
                'cheval_nom': change.cheval_nom,
                'cote_actuelle': change.cote_actuelle,
                'cote_precedente': change.cote_precedente,
                'variation': change.cote_actuelle - change.cote_precedente,
                'variation_percent': change.variation_percent
            })
        
        # Si aucun changement significatif, sortir
        if not changes_by_course:
            logger.info("No significant odds changes found")
            return results
        
        # Récupérer les utilisateurs qui doivent recevoir des notifications
        users_query = text("""
            SELECT u.id, u.email, u.first_name, ns.email_notifications, ns.push_notifications, 
                   ns.notify_odds_changes
            FROM users u
            JOIN notification_settings ns ON u.id = ns.user_id
            WHERE u.is_active = TRUE
            AND u.is_verified = TRUE
            AND ns.notify_odds_changes = TRUE
            AND (
                u.subscription_level IN ('standard', 'premium')
                OR (
                    u.subscription_level = 'free'
                    AND u.created_at > :one_week_ago
                )
            )
        """)
        
        one_week_ago = datetime.now() - timedelta(days=7)
        users_result = db.session.execute(users_query, {"one_week_ago": one_week_ago})
        
        users = [
            {
                'id': row.id,
                'email': row.email,
                'first_name': row.first_name,
                'email_notifications': row.email_notifications,
                'push_notifications': row.push_notifications
            }
            for row in users_result
        ]
        
        # Pour chaque course avec des changements, envoyer des notifications
        for course_id, course_data in changes_by_course.items():
            try:
                course_info = course_data['course_info']
                changed_horses = sorted(
                    course_data['changes'], 
                    key=lambda x: abs(x['variation_percent']),
                    reverse=True
                )
                
                # Pour chaque utilisateur, créer et envoyer la notification
                notified_users = set()
                
                for user in users:
                    user_id = user['id']
                    
                    # Créer la notification
                    notification_id = notification_service.create_odds_change_notification(
                        user_id=user_id,
                        course_id=course_id,
                        changed_horses=changed_horses
                    )
                    
                    if notification_id:
                        results['notifications_sent'] += 1
                        notified_users.add(user_id)
                
                # Mettre à jour le nombre d'utilisateurs notifiés
                results['users_notified'] = len(notified_users)
                
            except Exception as e:
                error_msg = f"Error sending odds change notification for course {course_id}: {str(e)}"
                logger.error(error_msg)
                results['errors'].append(error_msg)
                continue
        
        return results
        
    except Exception as e:
        error_msg = f"Error in send_odds_change_notifications: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        results['errors'].append(error_msg)
        return results

def send_upcoming_course_notifications():
    """
    Envoie des notifications pour les courses imminentes.
    
    Returns:
        dict: Résultats de l'envoi de notifications
    """
    logger.info("Sending upcoming course notifications")
    
    results = {
        'notifications_sent': 0,
        'users_notified': 0,
        'errors': []
    }
    
    try:
        # Initialiser les services
        notification_service = NotificationService()
        
        # Récupérer les courses imminentes (dans les 2 prochaines heures)
        now = datetime.now()
        two_hours_later = now + timedelta(hours=2)
        
        # Configuration des périodes de notification
        notification_periods = [
            {'minutes': 120, 'seconds': 120*60 - 5*60, 'label': '2 heures'},  # 2h (tolérance 5 min)
            {'minutes': 60, 'seconds': 60*60 - 5*60, 'label': '1 heure'},     # 1h (tolérance 5 min)
            {'minutes': 30, 'seconds': 30*60 - 3*60, 'label': '30 minutes'},  # 30 min (tolérance 3 min)
            {'minutes': 15, 'seconds': 15*60 - 2*60, 'label': '15 minutes'}   # 15 min (tolérance 2 min)
        ]
        
        # Récupérer les courses à venir dans les 2 prochaines heures
        upcoming_query = text("""
            SELECT c.id, c.date_heure, c.lieu, c.libelle, c.type_course,
                   COUNT(p.id) AS nb_participants,
                   EXTRACT(EPOCH FROM (c.date_heure - NOW())) AS seconds_until_start
            FROM courses c
            LEFT JOIN participations p ON c.id = p.id_course
            WHERE c.date_heure BETWEEN :now AND :two_hours_later
            GROUP BY c.id
            ORDER BY c.date_heure ASC
        """)
        
        upcoming_result = db.session.execute(upcoming_query, {"now": now, "two_hours_later": two_hours_later})
        
        # Récupérer les utilisateurs qui doivent recevoir des notifications
        users_query = text("""
            SELECT u.id, u.email, u.first_name, ns.email_notifications, ns.push_notifications, 
                   ns.notify_upcoming_races, ns.min_minutes_before_race
            FROM users u
            JOIN notification_settings ns ON u.id = ns.user_id
            WHERE u.is_active = TRUE
            AND u.is_verified = TRUE
            AND ns.notify_upcoming_races = TRUE
        """)
        
        users_result = db.session.execute(users_query)
        
        users = [
            {
                'id': row.id,
                'email': row.email,
                'first_name': row.first_name,
                'email_notifications': row.email_notifications,
                'push_notifications': row.push_notifications,
                'min_minutes_before_race': row.min_minutes_before_race
            }
            for row in users_result
        ]
        
        # Pour chaque course imminente, vérifier si des notifications doivent être envoyées
        for course in upcoming_result:
            try:
                course_id = course.id
                seconds_until_start = course.seconds_until_start
                minutes_until_start = int(seconds_until_start / 60)
                
                # Déterminer la période de notification appropriée
                current_period = None
                for period in notification_periods:
                    if abs(seconds_until_start - period['seconds']) < 300:  # Tolérance 5 minutes
                        current_period = period
                        break
                
                if current_period is None:
                    continue  # Pas de période correspondante
                
                # Vérifier si une notification a déjà été envoyée pour cette course et cette période
                check_query = text("""
                    SELECT id
                    FROM notifications
                    WHERE notification_type = 'upcoming_course'
                    AND data->>'course_id' = :course_id
                    AND data->>'time_before_start' = :minutes
                    AND created_at > NOW() - INTERVAL '3 hours'
                """)
                
                already_notified = db.session.execute(check_query, {
                    "course_id": str(course_id),
                    "minutes": str(current_period['minutes'])
                }).fetchone() is not None
                
                if already_notified:
                    continue  # Déjà notifié pour cette période
                
                # Préparer les données de la course
                course_info = {
                    'id': course_id,
                    'lieu': course.lieu,
                    'date_heure': course.date_heure.isoformat(),
                    'libelle': course.libelle,
                    'type_course': course.type_course,
                    'nb_participants': course.nb_participants
                }
                
                # Pour chaque utilisateur, vérifier si la notification doit être envoyée
                notified_users = set()
                
                for user in users:
                    user_id = user['id']
                    min_minutes = user['min_minutes_before_race']
                    
                    # Ne pas notifier si la course est trop proche selon les préférences
                    if minutes_until_start < min_minutes:
                        continue
                    
                    # Créer la notification
                    notification_id = notification_service.create_upcoming_course_notification(
                        user_id=user_id,
                        course_id=course_id,
                        time_before_start=current_period['minutes']
                    )
                    
                    if notification_id:
                        results['notifications_sent'] += 1
                        notified_users.add(user_id)
                
                # Mettre à jour le nombre d'utilisateurs notifiés
                results['users_notified'] += len(notified_users)
                
            except Exception as e:
                error_msg = f"Error sending upcoming course notification for course {course.id}: {str(e)}"
                logger.error(error_msg)
                results['errors'].append(error_msg)
                continue
        
        return results
        
    except Exception as e:
        error_msg = f"Error in send_upcoming_course_notifications: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        results['errors'].append(error_msg)
        return results