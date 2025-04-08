# api/services/course_service.py
import json
import logging
from datetime import datetime, timedelta
from flask import current_app
from api import db
from sqlalchemy import func, and_, text

class CourseService:
    """Service pour gérer les informations sur les courses"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def get_upcoming_courses(self, days=1, page=1, per_page=20):
        """Récupère les courses à venir dans les prochains jours"""
        try:
            # Calculer l'offset pour la pagination
            offset = (page - 1) * per_page
            
            # Définir la période de recherche
            now = datetime.now()
            end_date = now + timedelta(days=days)
            
            # Requête SQL pour récupérer les courses à venir
            query = text("""
                SELECT c.id, c.date_heure, c.lieu, h.libelleLong AS hippodrome_nom,
                       c.type_course, c.distance, c.terrain, c.num_course, c.libelle,
                       COUNT(p.id) AS nb_participants
                FROM courses c
                LEFT JOIN pmu_hippodromes h ON c.lieu = h.libelleLong
                LEFT JOIN participations p ON c.id = p.id_course
                WHERE c.date_heure BETWEEN :now AND :end_date
                GROUP BY c.id
                ORDER BY c.date_heure ASC
                LIMIT :limit OFFSET :offset
            """)
            
            result = db.session.execute(query, {
                "now": now,
                "end_date": end_date,
                "limit": per_page,
                "offset": offset
            })
            
            # Convertir le résultat en liste de dictionnaires
            courses = []
            for row in result:
                course = {
                    "id": row.id,