#j'ai deja # api/services/course_service.py implementé oubien il y a une incoerence et tu veux reprendre ? sinon fait seulement les partie manquantes selon le shema etabli
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
                    "date_heure": row.date_heure.isoformat() if row.date_heure else None,
                    "lieu": row.lieu,
                    "hippodrome_nom": row.hippodrome_nom,
                    "type_course": row.type_course,
                    "distance": row.distance,
                    "terrain": row.terrain,
                    "num_course": row.num_course,
                    "libelle": row.libelle,
                    "nb_participants": row.nb_participants
                }
                courses.append(course)
            
            # Compter le nombre total de courses pour la pagination
            count_query = text("""
                SELECT COUNT(*) AS count
                FROM courses c
                WHERE c.date_heure BETWEEN :now AND :end_date
            """)
            
            count_result = db.session.execute(count_query, {"now": now, "end_date": end_date}).fetchone()
            total_count = count_result.count if count_result else 0
            
            # Calculer le nombre total de pages
            total_pages = (total_count + per_page - 1) // per_page
            
            return {
                'count': total_count,
                'total_pages': total_pages,
                'data': courses
            }
            
        except Exception as e:
            self.logger.error(f"Error getting upcoming courses: {str(e)}")
            return {'count': 0, 'total_pages': 0, 'data': []}
    
    def get_course_by_id(self, course_id):
        """Récupère les détails d'une course spécifique"""
        try:
            query = text("""
                SELECT c.*, h.libelleLong AS hippodrome_nom,
                       pc.montantPrix, pc.categorieParticularite,
                       pc.corde, pc.categorieStatut, pc.discipline,
                       r.temperature, r.forceVent, r.directionVent, r.nebulositeLibelleCourt,
                       COUNT(p.id) AS nb_participants
                FROM courses c
                LEFT JOIN pmu_hippodromes h ON c.lieu = h.libelleLong
                LEFT JOIN pmu_courses pc ON c.pmu_course_id = pc.id
                LEFT JOIN pmu_reunions r ON pc.reunion_id = r.id
                LEFT JOIN participations p ON c.id = p.id_course
                WHERE c.id = :course_id
                GROUP BY c.id
            """)
            
            result = db.session.execute(query, {"course_id": course_id}).fetchone()
            
            if not result:
                return None
            
            # Convertir en dictionnaire
            course = {}
            for column in result._mapping.keys():
                value = getattr(result, column)
                if isinstance(value, datetime):
                    value = value.isoformat()
                course[column] = value
            
            # Ajout d'informations supplémentaires
            # Récupérer les incidents si disponibles
            incidents_query = text("""
                SELECT i.type_incident, i.numero_participants
                FROM incidents i
                WHERE i.id_course = :course_id
            """)
            
            incidents = db.session.execute(incidents_query, {"course_id": course_id}).fetchall()
            course['incidents'] = [{'type': inc.type_incident, 'participants': json.loads(inc.numero_participants) if inc.numero_participants else []} for inc in incidents]
            
            return course
            
        except Exception as e:
            self.logger.error(f"Error getting course {course_id}: {str(e)}")
            return None
    
    def get_course_participants(self, course_id):
        """Récupère la liste des participants à une course"""
        try:
            query = text("""
                SELECT p.*, c.nom AS cheval_nom, c.age, c.sexe, c.nomPere, c.nomMere,
                       j.nom AS jockey_nom, j.pays AS jockey_pays,
                       pp.numPmu, pp.musique
                FROM participations p
                JOIN chevaux c ON p.id_cheval = c.id
                JOIN jockeys j ON p.id_jockey = j.id
                LEFT JOIN pmu_participants pp ON (p.id_course = pp.id_course AND p.id_cheval = pp.cheval_id)
                WHERE p.id_course = :course_id
                ORDER BY p.numPmu ASC
            """)
            
            result = db.session.execute(query, {"course_id": course_id})
            
            participants = []
            for row in result:
                # Convertir en dictionnaire
                participant = {}
                for column in row._mapping.keys():
                    value = getattr(row, column)
                    if isinstance(value, datetime):
                        value = value.isoformat()
                    participant[column] = value
                
                participants.append(participant)
            
            return participants
            
        except Exception as e:
            self.logger.error(f"Error getting participants for course {course_id}: {str(e)}")
            return []
    
    def get_course_odds(self, course_id):
        """Récupère les cotes des participants à une course"""
        try:
            query = text("""
                SELECT p.id_cheval, c.nom AS cheval_nom, p.cote_initiale, p.cote_actuelle,
                       pp.numPmu, pp.dernierRapportDirect, pp.dernierRapportReference
                FROM participations p
                JOIN chevaux c ON p.id_cheval = c.id
                LEFT JOIN pmu_participants pp ON (p.id_course = pp.id_course AND p.id_cheval = pp.cheval_id)
                WHERE p.id_course = :course_id
                ORDER BY p.cote_actuelle ASC
            """)
            
            result = db.session.execute(query, {"course_id": course_id})
            
            odds = []
            for row in result:
                # Extraire les cotes des JSON si disponibles
                cote_actuelle = row.cote_actuelle
                cote_initiale = row.cote_initiale
                
                if not cote_actuelle and row.dernierRapportDirect:
                    try:
                        rapport_direct = json.loads(row.dernierRapportDirect) if isinstance(row.dernierRapportDirect, str) else row.dernierRapportDirect
                        if rapport_direct and 'rapport' in rapport_direct:
                            cote_actuelle = rapport_direct['rapport']
                    except (json.JSONDecodeError, TypeError):
                        pass
                
                if not cote_initiale and row.dernierRapportReference:
                    try:
                        rapport_reference = json.loads(row.dernierRapportReference) if isinstance(row.dernierRapportReference, str) else row.dernierRapportReference
                        if rapport_reference and 'rapport' in rapport_reference:
                            cote_initiale = rapport_reference['rapport']
                    except (json.JSONDecodeError, TypeError):
                        pass
                
                odds.append({
                    "id_cheval": row.id_cheval,
                    "cheval_nom": row.cheval_nom,
                    "numPmu": row.numPmu,
                    "cote_initiale": cote_initiale,
                    "cote_actuelle": cote_actuelle
                })
            
            return {
                'timestamp': datetime.now().isoformat(),
                'data': odds
            }
            
        except Exception as e:
            self.logger.error(f"Error getting odds for course {course_id}: {str(e)}")
            return {'timestamp': datetime.now().isoformat(), 'data': []}
    
    def get_course_odds_history(self, course_id):
        """Récupère l'historique des cotes pour une course"""
        try:
            query = text("""
                SELECT ch.id_participation, ch.horodatage, ch.cote,
                       p.id_cheval, c.nom AS cheval_nom, p.numPmu
                FROM cote_historique ch
                JOIN participations p ON ch.id_participation = p.id
                JOIN chevaux c ON p.id_cheval = c.id
                WHERE p.id_course = :course_id
                ORDER BY ch.horodatage DESC
            """)
            
            result = db.session.execute(query, {"course_id": course_id})
            
            # Organiser par cheval et par heure
            history_by_horse = {}
            
            for row in result:
                cheval_id = row.id_cheval
                
                if cheval_id not in history_by_horse:
                    history_by_horse[cheval_id] = {
                        "id_cheval": cheval_id,
                        "cheval_nom": row.cheval_nom,
                        "numPmu": row.numPmu,
                        "historique": []
                    }
                
                history_by_horse[cheval_id]["historique"].append({
                    "horodatage": row.horodatage.isoformat() if row.horodatage else None,
                    "cote": row.cote
                })
            
            return list(history_by_horse.values())
            
        except Exception as e:
            self.logger.error(f"Error getting odds history for course {course_id}: {str(e)}")
            return []
    
    def get_course_results(self, course_id):
        """Récupère les résultats d'une course terminée"""
        try:
            # Vérifier si la course est terminée
            course_query = text("""
                SELECT c.ordreArrivee, c.date_heure
                FROM courses c
                WHERE c.id = :course_id
            """)
            
            course = db.session.execute(course_query, {"course_id": course_id}).fetchone()
            
            if not course or not course.ordreArrivee:
                return None
            
            # Récupérer les participants avec leurs positions finales
            query = text("""
                SELECT p.position, p.id_cheval, c.nom AS cheval_nom, 
                       j.nom AS jockey_nom, p.cote_actuelle,
                       pp.numPmu, pp.tempsObtenu, pp.reductionKilometrique
                FROM participations p
                JOIN chevaux c ON p.id_cheval = c.id
                JOIN jockeys j ON p.id_jockey = j.id
                LEFT JOIN pmu_participants pp ON (p.id_course = pp.id_course AND p.id_cheval = pp.cheval_id)
                WHERE p.id_course = :course_id
                ORDER BY p.position ASC
            """)
            
            result = db.session.execute(query, {"course_id": course_id})
            
            participants = []
            for row in result:
                participant = {
                    "position": row.position,
                    "id_cheval": row.id_cheval,
                    "cheval_nom": row.cheval_nom,
                    "jockey_nom": row.jockey_nom,
                    "cote": row.cote_actuelle,
                    "numPmu": row.numPmu,
                    "temps": row.tempsObtenu,
                    "reduction": row.reductionKilometrique
                }
                participants.append(participant)
            
            # Récupérer les rapports officiels
            rapports_query = text("""
                SELECT * 
                FROM rapports_pmu
                WHERE id_course = :course_id
            """)
            
            rapports_result = db.session.execute(rapports_query, {"course_id": course_id}).fetchone()
            rapports = None
            
            if rapports_result:
                rapports = {}
                for column in rapports_result._mapping.keys():
                    if column != 'id' and column != 'id_course':
                        rapports[column] = getattr(rapports_result, column)
            
            return {
                "date_resultat": course.date_heure.isoformat() if course.date_heure else None,
                "participants": participants,
                "rapports": rapports
            }
            
        except Exception as e:
            self.logger.error(f"Error getting results for course {course_id}: {str(e)}")
            return None
    
    def get_course_photos(self, course_id):
        """Récupère les photos d'arrivée d'une course"""
        try:
            query = text("""
                SELECT p.id, p.url, p.height, p.width, p.is_original
                FROM photos_arrivee p
                WHERE p.id_course = :course_id
                ORDER BY p.is_original DESC
            """)
            
            result = db.session.execute(query, {"course_id": course_id})
            
            photos = []
            for row in result:
                photo = {
                    "id": row.id,
                    "url": row.url,
                    "height": row.height,
                    "width": row.width,
                    "is_original": row.is_original
                }
                photos.append(photo)
            
            return photos
            
        except Exception as e:
            self.logger.error(f"Error getting photos for course {course_id}: {str(e)}")
            return []
    
    def get_course_comments(self, course_id):
        """Récupère les commentaires officiels d'une course"""
        try:
            query = text("""
                SELECT c.id, c.texte, c.source, c.created_at
                FROM commentaires_course c
                WHERE c.id_course = :course_id
                ORDER BY c.created_at DESC
            """)
            
            result = db.session.execute(query, {"course_id": course_id})
            
            comments = []
            for row in result:
                comment = {
                    "id": row.id,
                    "texte": row.texte,
                    "source": row.source,
                    "created_at": row.created_at.isoformat() if row.created_at else None
                }
                comments.append(comment)
            
            return comments
            
        except Exception as e:
            self.logger.error(f"Error getting comments for course {course_id}: {str(e)}")
            return []
    
    def search_courses(self, date_from=None, date_to=None, hippodrome=None, 
                      course_type=None, cheval_id=None, jockey_id=None,
                      page=1, per_page=20):
        """Recherche de courses selon divers critères"""
        try:
            # Calculer l'offset pour la pagination
            offset = (page - 1) * per_page
            
            # Construire la requête de base
            query_str = """
                SELECT c.id, c.date_heure, c.lieu, c.type_course, c.distance, 
                       c.terrain, c.num_course, c.libelle, h.libelleLong AS hippodrome_nom,
                       COUNT(DISTINCT p.id) AS nb_participants
                FROM courses c
                LEFT JOIN pmu_hippodromes h ON c.lieu = h.libelleLong
                LEFT JOIN participations p ON c.id = p.id_course
            """
            
            # Ajouter les conditions de recherche
            conditions = []
            params = {}
            
            # Filtres de date
            if date_from:
                conditions.append("c.date_heure >= :date_from")
                params["date_from"] = date_from
            
            if date_to:
                conditions.append("c.date_heure <= :date_to")
                params["date_to"] = date_to
            
            # Filtre par hippodrome
            if hippodrome:
                conditions.append("(c.lieu LIKE :hippodrome OR h.libelleLong LIKE :hippodrome)")
                params["hippodrome"] = f"%{hippodrome}%"
            
            # Filtre par type de course
            if course_type:
                conditions.append("c.type_course LIKE :course_type")
                params["course_type"] = f"%{course_type}%"
            
            # Filtre par cheval
            if cheval_id:
                query_str += " JOIN participations p_cheval ON c.id = p_cheval.id_course"
                conditions.append("p_cheval.id_cheval = :cheval_id")
                params["cheval_id"] = cheval_id
            
            # Filtre par jockey
            if jockey_id:
                query_str += " JOIN participations p_jockey ON c.id = p_jockey.id_course"
                conditions.append("p_jockey.id_jockey = :jockey_id")
                params["jockey_id"] = jockey_id
            
            # Ajouter les conditions à la requête
            if conditions:
                query_str += " WHERE " + " AND ".join(conditions)
            
            # Grouper par course
            query_str += " GROUP BY c.id"
            
            # Trier par date
            query_str += " ORDER BY c.date_heure DESC"
            
            # Ajouter la pagination
            query_str += " LIMIT :limit OFFSET :offset"
            params["limit"] = per_page
            params["offset"] = offset
            
            # Exécuter la requête
            query = text(query_str)
            result = db.session.execute(query, params)
            
            courses = []
            for row in result:
                course = {
                    "id": row.id,
                    "date_heure": row.date_heure.isoformat() if row.date_heure else None,
                    "lieu": row.lieu,
                    "hippodrome_nom": row.hippodrome_nom,
                    "type_course": row.type_course,
                    "distance": row.distance,
                    "terrain": row.terrain,
                    "num_course": row.num_course,
                    "libelle": row.libelle,
                    "nb_participants": row.nb_participants
                }
                courses.append(course)
            
            # Compter le nombre total pour la pagination
            count_query_str = """
                SELECT COUNT(DISTINCT c.id) AS count
                FROM courses c
                LEFT JOIN pmu_hippodromes h ON c.lieu = h.libelleLong
            """
            
            # Ajouter les mêmes filtres à la requête count
            if cheval_id:
                count_query_str += " JOIN participations p_cheval ON c.id = p_cheval.id_course"
            
            if jockey_id:
                count_query_str += " JOIN participations p_jockey ON c.id = p_jockey.id_course"
            
            if conditions:
                count_query_str += " WHERE " + " AND ".join(conditions)
            
            count_query = text(count_query_str)
            count_result = db.session.execute(count_query, params).fetchone()
            total_count = count_result.count if count_result else 0
            
            # Calculer le nombre total de pages
            total_pages = (total_count + per_page - 1) // per_page
            
            return {
                'count': total_count,
                'total_pages': total_pages,
                'data': courses
            }
            
        except Exception as e:
            self.logger.error(f"Error searching courses: {str(e)}")
            return {'count': 0, 'total_pages': 0, 'data': []}