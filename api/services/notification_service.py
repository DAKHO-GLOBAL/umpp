# notification_service.py
# api/services/notification_service.py
import logging
import json
from datetime import datetime, timedelta
from flask import current_app
from api import db
from sqlalchemy import func, and_, text

class NotificationService:
    """Service pour gérer les notifications aux utilisateurs"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def create_notification(self, user_id, notification_type, title, message, data=None, send_email=False, send_push=False):
        """Crée une nouvelle notification pour un utilisateur"""
        try:
            # Préparer les données
            query = text("""
            INSERT INTO notifications
                (user_id, notification_type, title, message, data, read, created_at, updated_at)
            VALUES
                (:user_id, :notification_type, :title, :message, :data, :read, :created_at, :updated_at)
            RETURNING id
            """)
            
            now = datetime.now()
            
            # Exécuter la requête
            result = db.session.execute(query, {
                "user_id": user_id,
                "notification_type": notification_type,
                "title": title,
                "message": message,
                "data": json.dumps(data) if data else None,
                "read": False,
                "created_at": now,
                "updated_at": now
            })
            
            notification_id = result.fetchone()[0] if result else None
            
            db.session.commit()
            
            # Envoyer par email si demandé
            if send_email:
                self._send_email_notification(user_id, title, message, data)
            
            # Envoyer une notification push si demandé
            if send_push:
                self._send_push_notification(user_id, title, message, data)
            
            return notification_id
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error creating notification: {str(e)}")
            return None
    
    def get_user_notifications(self, user_id, page=1, per_page=20, unread_only=False):
        """Récupère les notifications d'un utilisateur"""
        try:
            # Calculer l'offset pour la pagination
            offset = (page - 1) * per_page
            
            # Construire la requête
            query_str = """
            SELECT id, notification_type, title, message, data, read, created_at, updated_at
            FROM notifications
            WHERE user_id = :user_id
            """
            
            if unread_only:
                query_str += " AND read = false"
            
            query_str += " ORDER BY created_at DESC LIMIT :limit OFFSET :offset"
            
            # Exécuter la requête
            query = text(query_str)
            result = db.session.execute(query, {
                "user_id": user_id,
                "limit": per_page,
                "offset": offset
            })
            
            # Convertir le résultat en liste de dictionnaires
            notifications = []
            for row in result:
                notification = {
                    "id": row.id,
                    "notification_type": row.notification_type,
                    "title": row.title,
                    "message": row.message,
                    "data": json.loads(row.data) if row.data else None,
                    "read": row.read,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                    "updated_at": row.updated_at.isoformat() if row.updated_at else None
                }
                notifications.append(notification)
            
            # Compter le nombre total de notifications
            count_query_str = """
            SELECT COUNT(*) AS count
            FROM notifications
            WHERE user_id = :user_id
            """
            
            if unread_only:
                count_query_str += " AND read = false"
            
            count_query = text(count_query_str)
            count_result = db.session.execute(count_query, {"user_id": user_id}).fetchone()
            total_count = count_result.count if count_result else 0
            
            # Calculer le nombre total de pages
            total_pages = (total_count + per_page - 1) // per_page
            
            return {
                'count': total_count,
                'total_pages': total_pages,
                'data': notifications
            }
            
        except Exception as e:
            self.logger.error(f"Error getting notifications: {str(e)}")
            return {'count': 0, 'total_pages': 0, 'data': []}
    
    def mark_notification_as_read(self, notification_id, user_id):
        """Marque une notification comme lue"""
        try:
            # Vérifier que la notification appartient à l'utilisateur
            query = text("""
            UPDATE notifications
            SET read = true, updated_at = :updated_at
            WHERE id = :notification_id AND user_id = :user_id
            RETURNING id
            """)
            
            result = db.session.execute(query, {
                "notification_id": notification_id,
                "user_id": user_id,
                "updated_at": datetime.now()
            })
            
            success = result.fetchone() is not None
            
            db.session.commit()
            
            return success
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error marking notification as read: {str(e)}")
            return False
    
    def mark_all_as_read(self, user_id):
        """Marque toutes les notifications d'un utilisateur comme lues"""
        try:
            query = text("""
            UPDATE notifications
            SET read = true, updated_at = :updated_at
            WHERE user_id = :user_id AND read = false
            """)
            
            db.session.execute(query, {
                "user_id": user_id,
                "updated_at": datetime.now()
            })
            
            db.session.commit()
            
            return True
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error marking all notifications as read: {str(e)}")
            return False
    
    def delete_notification(self, notification_id, user_id):
        """Supprime une notification"""
        try:
            query = text("""
            DELETE FROM notifications
            WHERE id = :notification_id AND user_id = :user_id
            RETURNING id
            """)
            
            result = db.session.execute(query, {
                "notification_id": notification_id,
                "user_id": user_id
            })
            
            success = result.fetchone() is not None
            
            db.session.commit()
            
            return success
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error deleting notification: {str(e)}")
            return False
    
    def get_unread_count(self, user_id):
        """Récupère le nombre de notifications non lues pour un utilisateur"""
        try:
            query = text("""
            SELECT COUNT(*) AS count
            FROM notifications
            WHERE user_id = :user_id AND read = false
            """)
            
            result = db.session.execute(query, {"user_id": user_id}).fetchone()
            
            return result.count if result else 0
            
        except Exception as e:
            self.logger.error(f"Error getting unread count: {str(e)}")
            return 0
    
    def create_course_prediction_notification(self, user_id, course_id, prediction_type, interesting_picks):
        """Crée une notification pour une prédiction de course intéressante"""
        try:
            # Récupérer les infos de la course
            query = text("""
            SELECT c.id, c.date_heure, c.lieu, c.libelle
            FROM courses c
            WHERE c.id = :course_id
            """)
            
            course = db.session.execute(query, {"course_id": course_id}).fetchone()
            
            if not course:
                return None
            
            # Créer un titre et un message
            title = f"Nouvelle prédiction pour {course.lieu}"
            
            # Créer un message personnalisé selon le type de prédiction
            if prediction_type == 'standard':
                message = f"Prédiction standard pour la course {course.libelle} du {course.date_heure.strftime('%d/%m/%Y à %H:%M')}."
            elif prediction_type == 'top3':
                message = f"Prédiction Top 3 disponible pour {course.libelle} au {course.lieu}."
            elif prediction_type == 'top7':
                message = f"Prédiction Top 7 complète disponible pour {course.libelle} au {course.lieu}."
            else:
                message = f"Nouvelle prédiction disponible pour {course.lieu}."
            
            # Préparer les données supplémentaires
            data = {
                "course_id": course_id,
                "prediction_type": prediction_type,
                "course_datetime": course.date_heure.isoformat() if course.date_heure else None,
                "lieu": course.lieu,
                "libelle": course.libelle,
                "interesting_picks": interesting_picks
            }
            
            # Créer la notification
            notification_id = self.create_notification(
                user_id=user_id,
                notification_type="prediction",
                title=title,
                message=message,
                data=data,
                send_email=False,  # À configurer selon les préférences utilisateur
                send_push=False    # À configurer selon les préférences utilisateur
            )
            
            return notification_id
            
        except Exception as e:
            self.logger.error(f"Error creating prediction notification: {str(e)}")
            return None
    
    def create_odds_change_notification(self, user_id, course_id, changed_horses):
        """Crée une notification pour un changement significatif de cotes"""
        try:
            # Récupérer les infos de la course
            query = text("""
            SELECT c.id, c.date_heure, c.lieu, c.libelle
            FROM courses c
            WHERE c.id = :course_id
            """)
            
            course = db.session.execute(query, {"course_id": course_id}).fetchone()
            
            if not course:
                return None
            
            # Créer un titre et un message
            title = f"Mouvement de cotes pour {course.lieu}"
            
            # Déterminer le premier cheval avec le mouvement le plus important
            if changed_horses and len(changed_horses) > 0:
                most_significant = changed_horses[0]
                message = f"Changement significatif pour {most_significant['cheval_nom']} à {course.lieu}."
                if len(changed_horses) > 1:
                    message += f" {len(changed_horses) - 1} autres chevaux ont également des mouvements de cotes."
            else:
                message = f"Mouvements de cotes détectés pour la course à {course.lieu}."
            
            # Préparer les données supplémentaires
            data = {
                "course_id": course_id,
                "course_datetime": course.date_heure.isoformat() if course.date_heure else None,
                "lieu": course.lieu,
                "libelle": course.libelle,
                "changed_horses": changed_horses
            }
            
            # Créer la notification
            notification_id = self.create_notification(
                user_id=user_id,
                notification_type="odds_change",
                title=title,
                message=message,
                data=data,
                send_email=False,  # À configurer selon les préférences utilisateur
                send_push=False    # À configurer selon les préférences utilisateur
            )
            
            return notification_id
            
        except Exception as e:
            self.logger.error(f"Error creating odds change notification: {str(e)}")
            return None
    
    def create_upcoming_course_notification(self, user_id, course_id, time_before_start):
        """Crée une notification pour une course à venir"""
        try:
            # Récupérer les infos de la course
            query = text("""
            SELECT c.id, c.date_heure, c.lieu, c.libelle, COUNT(p.id) AS nb_participants
            FROM courses c
            LEFT JOIN participations p ON c.id = p.id_course
            WHERE c.id = :course_id
            GROUP BY c.id
            """)
            
            course = db.session.execute(query, {"course_id": course_id}).fetchone()
            
            if not course:
                return None
            
            # Créer un titre et un message
            if time_before_start >= 60:
                hours = time_before_start // 60
                title = f"Course dans {hours}h à {course.lieu}"
                message = f"Rappel: {course.libelle} démarre dans {hours} heure(s) à {course.lieu}."
            else:
                title = f"Course imminente à {course.lieu}"
                message = f"Attention: {course.libelle} démarre dans {time_before_start} minutes à {course.lieu}."
            
            # Préparer les données supplémentaires
            data = {
                "course_id": course_id,
                "course_datetime": course.date_heure.isoformat() if course.date_heure else None,
                "lieu": course.lieu,
                "libelle": course.libelle,
                "nb_participants": course.nb_participants,
                "time_before_start": time_before_start
            }
            
            # Créer la notification
            notification_id = self.create_notification(
                user_id=user_id,
                notification_type="upcoming_course",
                title=title,
                message=message,
                data=data,
                send_email=False,  # À configurer selon les préférences utilisateur
                send_push=False    # À configurer selon les préférences utilisateur
            )
            
            return notification_id
            
        except Exception as e:
            self.logger.error(f"Error creating upcoming course notification: {str(e)}")
            return None
    
    def _send_email_notification(self, user_id, title, message, data):
        """Envoie une notification par email"""
        try:
            # Récupérer l'email de l'utilisateur
            query = text("""
            SELECT email
            FROM users
            WHERE id = :user_id
            """)
            
            result = db.session.execute(query, {"user_id": user_id}).fetchone()
            
            if not result:
                self.logger.error(f"User not found for email notification: {user_id}")
                return False
            
            email = result.email
            
            # Importer le service d'email
            from utils.email_sender import send_email
            
            # Envoyer l'email
            send_email(
                recipient=email,
                subject=title,
                body=message,
                data=data
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending email notification: {str(e)}")
            return False
    
    def _send_push_notification(self, user_id, title, message, data):
        """Envoie une notification push"""
        try:
            # Récupérer le token de notification de l'utilisateur
            query = text("""
            SELECT notification_token
            FROM user_devices
            WHERE user_id = :user_id AND notification_enabled = true
            ORDER BY last_used_at DESC
            LIMIT 1
            """)
            
            result = db.session.execute(query, {"user_id": user_id}).fetchone()
            
            if not result or not result.notification_token:
                self.logger.debug(f"No notification token found for user: {user_id}")
                return False
            
            token = result.notification_token
            
            # Importer le service de notification push
            from utils.firebase_client import send_push_notification
            
            # Envoyer la notification push
            send_push_notification(
                token=token,
                title=title,
                body=message,
                data=data
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending push notification: {str(e)}")
            return False