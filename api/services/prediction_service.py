# prediction_service.py
# api/services/prediction_service.py
import json
import logging
from datetime import datetime, timedelta
from flask import current_app
from extensions import db
from sqlalchemy import func, and_, text

# Importation du modèle de prédiction existant
from model.dual_prediction_model import DualPredictionModel
from data_preparation.enhanced_data_prep import EnhancedDataPreparation

class PredictionService:
    """Service pour gérer les prédictions de courses"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Initialiser les classes du projet existant
        self.data_prep = EnhancedDataPreparation()
        self.model = DualPredictionModel(base_path=current_app.config.get('MODEL_PATH', 'model/trained_models'))
        
        # Charger les modèles préentraînés
        self._load_models()
    
    def _load_models(self):
        """Charge les modèles préentraînés nécessaires"""
        try:
            # Charger le modèle standard
            standard_model_path = f"{current_app.config.get('MODEL_PATH')}/enhanced_xgboost_latest.pkl"
            self.model.load_standard_model(standard_model_path)
            
            # Charger le modèle de simulation (Top 7)
            simulation_model_path = f"{current_app.config.get('MODEL_PATH')}/simulation_top7_xgboost_ranking_latest.pkl"
            self.model.load_simulation_model(simulation_model_path)
            
            self.logger.info("Prediction models loaded successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to load prediction models: {str(e)}")
            # Tenter de charger d'autres versions si disponibles
            try:
                self.model.initialize_standard_model()
                self.model.initialize_simulation_model()
                self.logger.info("Initialized new prediction models")
                return True
            except Exception as e2:
                self.logger.error(f"Failed to initialize models: {str(e2)}")
                return False

    def get_upcoming_races(self, days_ahead=1):
        """Récupère les courses à venir dans les prochains jours"""
        try:
            # Utiliser la fonction existante pour récupérer les courses à venir
            now = datetime.now()
            end_date = now + timedelta(days=days_ahead)
            
            # Requête SQL directe pour éviter les problèmes d'ORM avec SQLAlchemy
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
            """)
            
            result = db.session.execute(query, {"now": now, "end_date": end_date})
            
            # Convertir le résultat en liste de dictionnaires
            upcoming_races = []
            for row in result:
                race = {
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
                upcoming_races.append(race)
            
            return upcoming_races
        except Exception as e:
            self.logger.error(f"Error getting upcoming races: {str(e)}")
            return []

    def predict_course(self, course_id, prediction_type='standard'):
        """Effectue une prédiction pour une course donnée"""
        try:
            # Vérifier que la course existe et n'est pas déjà terminée
            query = text("""
                SELECT c.id, c.date_heure, c.lieu, h.libelleLong AS hippodrome_nom, 
                       c.type_course, c.distance, c.terrain, c.num_course, c.libelle,
                       c.position IS NOT NULL AS is_finished
                FROM courses c
                LEFT JOIN pmu_hippodromes h ON c.lieu = h.libelleLong
                WHERE c.id = :course_id
            """)
            
            result = db.session.execute(query, {"course_id": course_id}).fetchone()
            
            if not result:
                raise ValueError(f"Course with ID {course_id} not found")
            
            if result.is_finished:
                raise ValueError("Cannot predict a race that has already finished")
            
            # Utiliser votre système existant pour la prédiction
            # Préparer les données pour la prédiction
            prediction_data = self.data_prep.get_participant_data(course_id=course_id)
            
            if prediction_data is None or prediction_data.empty:
                raise ValueError(f"No participants found for course {course_id}")
            
            # Créer des features avancées
            enhanced_data = self.data_prep.create_advanced_features(prediction_data)
            
            # Encoder pour le modèle
            prepared_data = self.data_prep.encode_features_for_model(enhanced_data, is_training=False)
            
            # Faire la prédiction selon le type demandé
            if prediction_type == 'standard' or prediction_type == 'top3':
                # Prédiction standard (top 3)
                predictions = self.model.predict_standard(prepared_data)
            elif prediction_type == 'top7':
                # Prédiction Top 7
                predictions = self.model.predict_top7(prepared_data)
            else:
                raise ValueError(f"Unsupported prediction type: {prediction_type}")
            
            # Convertir le DataFrame en dictionnaire
            predictions_dict = predictions.to_dict(orient='records')
            
            # Sauvegarder la prédiction dans la base de données
            self._save_prediction_to_db(course_id, prediction_type, predictions_dict)
            
            # Retourner le résultat
            return {
                'timestamp': datetime.now().isoformat(),
                'data': predictions_dict
            }
            
        except Exception as e:
            self.logger.error(f"Error predicting course {course_id}: {str(e)}")
            raise

    def predict_course_realtime(self, course_id, latest_odds=None):
        """Effectue une prédiction en temps réel avec les dernières cotes"""
        try:
            # Récupérer les dernières cotes si non fournies
            if latest_odds is None:
                latest_odds = self.get_latest_odds(course_id)
            
            # Effectuer une prédiction standard
            prediction = self.predict_course(course_id, prediction_type='top7')
            
            # Mettre à jour les prédictions avec les dernières cotes
            for horse in prediction['data']:
                if str(horse['id_cheval']) in latest_odds:
                    horse['cote_actuelle'] = latest_odds[str(horse['id_cheval'])]
                    # Ajuster les probabilités en fonction des cotes
                    # (Logique simplifiée, à affiner selon votre modèle)
                    if horse['cote_actuelle'] < horse.get('cote_precedente', float('inf')):
                        # La cote a baissé = plus de chances de gagner
                        horse['in_top1_prob'] *= 1.1
                        horse['in_top3_prob'] *= 1.05
                    elif horse['cote_actuelle'] > horse.get('cote_precedente', 0):
                        # La cote a augmenté = moins de chances de gagner
                        horse['in_top1_prob'] *= 0.9
                        horse['in_top3_prob'] *= 0.95
            
            # Recalculer le rang prédit en fonction des probabilités mises à jour
            sorted_horses = sorted(prediction['data'], key=lambda x: x['in_top1_prob'], reverse=True)
            for idx, horse in enumerate(sorted_horses):
                horse['predicted_rank'] = idx + 1
            
            # Remettre les résultats dans le bon format
            prediction['data'] = sorted_horses
            prediction['timestamp'] = datetime.now().isoformat()
            
            return prediction
            
        except Exception as e:
            self.logger.error(f"Error in realtime prediction for course {course_id}: {str(e)}")
            raise

    def get_latest_odds(self, course_id):
        """Récupère les dernières cotes pour une course"""
        try:
            # Requête SQL pour obtenir les dernières cotes
            query = text("""
                SELECT p.id_cheval, p.cote_actuelle
                FROM participations p
                WHERE p.id_course = :course_id
            """)
            
            result = db.session.execute(query, {"course_id": course_id})
            
            # Convertir en dictionnaire {id_cheval: cote}
            latest_odds = {}
            for row in result:
                latest_odds[str(row.id_cheval)] = row.cote_actuelle if row.cote_actuelle else None
            
            return latest_odds
            
        except Exception as e:
            self.logger.error(f"Error getting latest odds for course {course_id}: {str(e)}")
            return {}



    def detect_prediction_changes(self, course_id, current_prediction):
        """Détecte les changements entre la prédiction actuelle et la précédente"""
        try:
            # Récupérer la dernière prédiction sauvegardée
            query = text("""
                SELECT prediction_data
                FROM predictions
                WHERE course_id = :course_id
                ORDER BY created_at DESC
                LIMIT 1
            """)
            
            result = db.session.execute(query, {"course_id": course_id}).fetchone()
            
            if not result or not result.prediction_data:
                return []  # Pas de prédiction précédente
            
            # Convertir les données sauvegardées
            previous_prediction = json.loads(result.prediction_data)
            
            # Comparer les prédictions
            changes = []
            
            # Convertir les listes en dictionnaires pour une recherche plus rapide
            prev_dict = {str(horse['id_cheval']): horse for horse in previous_prediction}
            curr_dict = {str(horse['id_cheval']): horse for horse in current_prediction}
            
            # Détecter les chevaux qui ont progressé ou régressé dans le classement
            for cheval_id, curr_horse in curr_dict.items():
                if cheval_id in prev_dict:
                    prev_horse = prev_dict[cheval_id]
                    
                    # Changement de rang
                    prev_rank = prev_horse.get('predicted_rank', 0)
                    curr_rank = curr_horse.get('predicted_rank', 0)
                    rank_change = prev_rank - curr_rank  # Positif = amélioration
                    
                    # Changement de probabilité dans le top 3
                    prev_prob = prev_horse.get('in_top3_prob', 0)
                    curr_prob = curr_horse.get('in_top3_prob', 0)
                    prob_change = curr_prob - prev_prob
                    
                    # Ne rapporter que les changements significatifs
                    if abs(rank_change) >= 2 or abs(prob_change) >= 0.1:
                        changes.append({
                            'id_cheval': cheval_id,
                            'nom': curr_horse.get('cheval_nom', f"Cheval {cheval_id}"),
                            'previous_rank': prev_rank,
                            'current_rank': curr_rank,
                            'rank_change': rank_change,
                            'previous_probability': prev_prob,
                            'current_probability': curr_prob,
                            'probability_change': prob_change,
                            'significance': 'high' if (abs(rank_change) >= 3 or abs(prob_change) >= 0.2) else 'medium'
                        })
            
            # Trier les changements par importance
            changes.sort(key=lambda x: (x['significance'] == 'high', abs(x['rank_change'])), reverse=True)
            
            return changes
            
        except Exception as e:
            self.logger.error(f"Error detecting prediction changes for course {course_id}: {str(e)}")
            return []

    def generate_prediction_comments(self, prediction_data, detailed=False):
        """Génère des commentaires automatisés sur les prédictions"""
        try:
            comments = []
            
            # Assurer que la prédiction est triée par rang
            sorted_pred = sorted(prediction_data, key=lambda x: x.get('predicted_rank', float('inf')))
            
            # Commentaire sur le favori
            if sorted_pred:
                favorite = sorted_pred[0]
                fav_name = favorite.get('cheval_nom', "Le favori")
                fav_prob = favorite.get('in_top3_prob', 0) * 100
                
                confidence = "élevée" if fav_prob > 75 else "moyenne" if fav_prob > 50 else "faible"
                comments.append(f"{fav_name} est notre favori pour cette course avec une confiance {confidence} ({fav_prob:.1f}%).")
                
                # Ajouter un commentaire sur les facteurs déterminants
                if 'cote_actuelle' in favorite:
                    comments.append(f"La cote actuelle de {favorite.get('cote_actuelle')} reflète bien son statut de favori.")
                
                if detailed and len(sorted_pred) >= 3:
                    # Commentaires sur les 3 premiers
                    podium = sorted_pred[:3]
                    comments.append(f"Notre podium prédit: {podium[0].get('cheval_nom')}, {podium[1].get('cheval_nom')} et {podium[2].get('cheval_nom')}.")
                    
                    # Chercher les outsiders potentiels
                    outsiders = []
                    for horse in sorted_pred[3:7]:
                        if horse.get('in_top3_prob', 0) > 0.2:  # 20% de chances d'être dans le top 3
                            outsiders.append(horse)
                    
                    if outsiders:
                        outsider_names = [h.get('cheval_nom', f"Cheval {h.get('id_cheval')}") for h in outsiders]
                        comments.append(f"Outsider(s) à surveiller: {', '.join(outsider_names)}.")
                    
                    if len(sorted_pred) >= 7:
                        # Commentaire sur les combinaisons Quinté possibles
                        comments.append(f"Pour un jeu de type Quinté, nous recommandons de considérer les 7 premiers chevaux de notre prédiction.")
            
            return comments
            
        except Exception as e:
            self.logger.error(f"Error generating prediction comments: {str(e)}")
            return ["Aucun commentaire disponible pour cette prédiction."]

    def generate_betting_suggestions(self, prediction_data):
        """Génère des suggestions de paris basées sur les prédictions"""
        try:
            suggestions = {}
            
            # Assurer que la prédiction est triée par rang
            sorted_pred = sorted(prediction_data, key=lambda x: x.get('predicted_rank', float('inf')))
            
            if len(sorted_pred) < 3:
                return {"message": "Pas assez de chevaux pour générer des suggestions de paris"}
            
            # IDs des chevaux pour différents types de paris
            top_horses = [int(horse.get('id_cheval')) for horse in sorted_pred[:7]]
            
            # Simple gagnant
            suggestions['simple_gagnant'] = {
                'type': 'Simple Gagnant',
                'description': 'Pari sur le cheval gagnant uniquement',
                'selection': [top_horses[0]],
                'confiance': float(sorted_pred[0].get('in_top1_prob', 0))
            }
            
            # Simple placé
            suggestions['simple_place'] = {
                'type': 'Simple Placé',
                'description': 'Pari sur un cheval finissant dans les 3 premiers',
                'selection': [top_horses[0]],
                'confiance': float(sorted_pred[0].get('in_top3_prob', 0))
            }
            
            if len(top_horses) >= 2:
                # Couplé ordre
                suggestions['couple_ordre'] = {
                    'type': 'Couplé Ordre',
                    'description': 'Pari sur les 2 premiers chevaux dans l\'ordre exact',
                    'selection': top_horses[:2],
                    'confiance': float(sorted_pred[0].get('in_top1_prob', 0) * sorted_pred[1].get('in_top3_prob', 0) * 0.8)
                }
                
                # Couplé désordre
                suggestions['couple_desordre'] = {
                    'type': 'Couplé Désordre',
                    'description': 'Pari sur les 2 premiers chevaux dans n\'importe quel ordre',
                    'selection': top_horses[:2],
                    'confiance': float(sorted_pred[0].get('in_top3_prob', 0) * sorted_pred[1].get('in_top3_prob', 0))
                }
            
            if len(top_horses) >= 3:
                # Tiercé ordre
                suggestions['tierce_ordre'] = {
                    'type': 'Tiercé Ordre',
                    'description': 'Pari sur les 3 premiers chevaux dans l\'ordre exact',
                    'selection': top_horses[:3],
                    'confiance': float(sorted_pred[0].get('in_top1_prob', 0) * sorted_pred[1].get('in_top3_prob', 0) * sorted_pred[2].get('in_top3_prob', 0) * 0.6)
                }
                
                # Tiercé désordre
                suggestions['tierce_desordre'] = {
                    'type': 'Tiercé Désordre',
                    'description': 'Pari sur les 3 premiers chevaux dans n\'importe quel ordre',
                    'selection': top_horses[:3],
                    'confiance': float(sorted_pred[0].get('in_top3_prob', 0) * sorted_pred[1].get('in_top3_prob', 0) * sorted_pred[2].get('in_top3_prob', 0))
                }
            
            if len(top_horses) >= 4:
                # Quarté
                suggestions['quarte_desordre'] = {
                    'type': 'Quarté Désordre',
                    'description': 'Pari sur les 4 premiers chevaux dans n\'importe quel ordre',
                    'selection': top_horses[:4],
                    'confiance': float(sorted_pred[0].get('in_top5_prob', 0) * sorted_pred[1].get('in_top5_prob', 0) * 
                                      sorted_pred[2].get('in_top5_prob', 0) * sorted_pred[3].get('in_top5_prob', 0))
                }
            
            if len(top_horses) >= 5:
                # Quinté
                suggestions['quinte_desordre'] = {
                    'type': 'Quinté Désordre',
                    'description': 'Pari sur les 5 premiers chevaux dans n\'importe quel ordre',
                    'selection': top_horses[:5],
                    'confiance': float(sorted_pred[0].get('in_top7_prob', 0) * sorted_pred[1].get('in_top7_prob', 0) * 
                                      sorted_pred[2].get('in_top7_prob', 0) * sorted_pred[3].get('in_top7_prob', 0) * 
                                      sorted_pred[4].get('in_top7_prob', 0))
                }
            
            if len(top_horses) >= 7:
                # Suggestion Top 7
                suggestions['top7'] = {
                    'type': 'Top 7',
                    'description': 'Prédiction des 7 premiers chevaux',
                    'selection': top_horses[:7],
                    'confiance': float(sorted_pred[0].get('in_top7_prob', 0) * sorted_pred[1].get('in_top7_prob', 0) * 
                                      sorted_pred[2].get('in_top7_prob', 0) * sorted_pred[3].get('in_top7_prob', 0) * 
                                      sorted_pred[4].get('in_top7_prob', 0) * sorted_pred[5].get('in_top7_prob', 0) * 
                                      sorted_pred[6].get('in_top7_prob', 0))
                }
            
            return suggestions
            
        except Exception as e:
            self.logger.error(f"Error generating betting suggestions: {str(e)}")
            return {"message": "Impossible de générer des suggestions de paris"}

    def _save_prediction_to_db(self, course_id, prediction_type, prediction_data):
        """Sauvegarde la prédiction dans la base de données"""
        try:
            # Sélectionner le modèle actif pour ce type de prédiction
            query = text("""
                SELECT id
                FROM model_versions
                WHERE model_category = :model_category
                AND is_active = 1
                LIMIT 1
            """)
            
            model_category = 'standard' if prediction_type in ['standard', 'top3'] else 'simulation'
            model_result = db.session.execute(query, {"model_category": model_category}).fetchone()
            
            model_id = model_result.id if model_result else None
            
            # Préparer l'insertion
            query = text("""
                INSERT INTO predictions 
                (course_id, prediction_type, prediction_data, model_version_id, created_at)
                VALUES (:course_id, :prediction_type, :prediction_data, :model_id, :created_at)
            """)
            
            # Exécuter l'insertion
            db.session.execute(query, {
                "course_id": course_id,
                "prediction_type": prediction_type,
                "prediction_data": json.dumps(prediction_data),
                "model_id": model_id,
                "created_at": datetime.now()
            })
            
            db.session.commit()
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error saving prediction to database: {str(e)}")

    def log_prediction_usage(self, user_id, course_id, prediction_type):
        """Enregistre l'utilisation d'une prédiction par un utilisateur"""
        try:
            # Insérer dans la table d'usage
            query = text("""
                INSERT INTO prediction_usage 
                (user_id, course_id, prediction_type, used_at)
                VALUES (:user_id, :course_id, :prediction_type, :used_at)
            """)
            
            db.session.execute(query, {
                "user_id": user_id,
                "course_id": course_id,
                "prediction_type": prediction_type,
                "used_at": datetime.now()
            })
            
            db.session.commit()
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error logging prediction usage: {str(e)}")

    def get_predictions_count_today(self, user_id):
        """Récupère le nombre de prédictions utilisées aujourd'hui par l'utilisateur"""
        try:
            # Récupérer le début de la journée
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Requête SQL pour compter les prédictions
            query = text("""
                SELECT COUNT(*) AS count
                FROM prediction_usage
                WHERE user_id = :user_id
                AND used_at >= :today_start
            """)
            
            result = db.session.execute(query, {"user_id": user_id, "today_start": today_start}).fetchone()
            
            return result.count if result else 0
            
        except Exception as e:
            self.logger.error(f"Error counting predictions used today: {str(e)}")
            return 0

    def get_user_prediction_history(self, user_id, page=1, per_page=10):
        """Récupère l'historique des prédictions d'un utilisateur"""
        try:
            # Calculer l'offset pour la pagination
            offset = (page - 1) * per_page
            
            # Requête SQL pour récupérer les prédictions
            query = text("""
                SELECT pu.id, pu.course_id, pu.prediction_type, pu.used_at,
                       c.lieu, c.date_heure, c.libelle, c.type_course,
                       p.prediction_data
                FROM prediction_usage pu
                JOIN courses c ON pu.course_id = c.id
                LEFT JOIN predictions p ON (pu.course_id = p.course_id AND pu.prediction_type = p.prediction_type)
                WHERE pu.user_id = :user_id
                ORDER BY pu.used_at DESC
                LIMIT :limit OFFSET :offset
            """)
            
            result = db.session.execute(query, {
                "user_id": user_id,
                "limit": per_page,
                "offset": offset
            })
            
            # Convertir le résultat en liste de dictionnaires
            history_data = []
            for row in result:
                prediction = {
                    "id": row.id,
                    "course_id": row.course_id,
                    "prediction_type": row.prediction_type,
                    "used_at": row.used_at.isoformat() if row.used_at else None,
                    "lieu": row.lieu,
                    "date_heure": row.date_heure.isoformat() if row.date_heure else None,
                    "libelle": row.libelle,
                    "type_course": row.type_course,
                    "prediction_data": json.loads(row.prediction_data) if row.prediction_data else None
                }
                history_data.append(prediction)
            
            # Compter le nombre total de prédictions pour la pagination
            count_query = text("""
                SELECT COUNT(*) AS count
                FROM prediction_usage
                WHERE user_id = :user_id
            """)
            
            count_result = db.session.execute(count_query, {"user_id": user_id}).fetchone()
            total_count = count_result.count if count_result else 0
            
            # Calculer le nombre total de pages
            total_pages = (total_count + per_page - 1) // per_page
            
            return {
                'count': total_count,
                'total_pages': total_pages,
                'data': history_data
            }
            
        except Exception as e:
            self.logger.error(f"Error retrieving prediction history: {str(e)}")
            return {'count': 0, 'total_pages': 0, 'data': []}