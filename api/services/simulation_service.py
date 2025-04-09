# simulation_service.py
# api/services/simulation_service.py
import json
import logging
from datetime import datetime, timedelta
from flask import current_app
from extensions import db
from sqlalchemy import func, and_, text

# Importation du modèle de prédiction existant
from model.dual_prediction_model import DualPredictionModel
from data_preparation.enhanced_data_prep import EnhancedDataPreparation

class SimulationService:
    """Service pour gérer les simulations de courses"""
    
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
            # Charger le modèle de simulation
            simulation_model_path = f"{current_app.config.get('MODEL_PATH')}/simulation_top7_xgboost_ranking_latest.pkl"
            self.model.load_simulation_model(simulation_model_path)
            
            self.logger.info("Simulation model loaded successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to load simulation model: {str(e)}")
            # Tenter de l'initialiser
            try:
                self.model.initialize_simulation_model()
                self.logger.info("Initialized new simulation model")
                return True
            except Exception as e2:
                self.logger.error(f"Failed to initialize simulation model: {str(e2)}")
                return False

    def simulate_course(self, course_id, selected_horses=None, simulation_params=None, 
                       horse_modifications=None, weather_conditions=None, track_conditions=None,
                       simulation_type='basic'):
        """Effectue une simulation personnalisée pour une course"""
        try:
            # Vérifier que la course existe
            query = text("""
                SELECT c.id, c.date_heure, c.lieu, c.type_course, c.distance, c.terrain
                FROM courses c
                WHERE c.id = :course_id
            """)
            
            course = db.session.execute(query, {"course_id": course_id}).fetchone()
            
            if not course:
                raise ValueError(f"Course with ID {course_id} not found")
            
            # Préparer les données pour la simulation
            # Si des chevaux spécifiques sont sélectionnés, les utiliser; sinon, prendre tous les chevaux
            simulation_data = self.data_prep.prepare_data_for_simulation(
                course_id=course_id,
                selected_horses=selected_horses
            )
            
            if simulation_data is None or simulation_data.empty:
                raise ValueError(f"No data available for simulation of course {course_id}")
            
            # Appliquer les modifications demandées
            if horse_modifications:
                simulation_data = self._apply_horse_modifications(simulation_data, horse_modifications)
            
            # Appliquer les modifications de conditions météo si spécifiées
            if weather_conditions:
                simulation_data = self._apply_weather_conditions(simulation_data, weather_conditions)
            
            # Appliquer les modifications de conditions de piste si spécifiées
            if track_conditions:
                simulation_data = self._apply_track_conditions(simulation_data, track_conditions)
            
            # Effectuer la simulation avec le modèle
            if simulation_type == 'basic':
                # Utiliser predict_top7 avec les paramètres par défaut
                results = self.model.predict_top7(simulation_data)
            else:
                # Simulation avancée avec plus de détails
                results = self.model.predict_top7(simulation_data)
                
                # Ajouter des métriques supplémentaires pour les simulations avancées
                # Comme la confiance, l'écart attendu, etc.
                # Ces calculs seraient spécifiques à votre modèle
            
            # Convertir le DataFrame en dictionnaire
            results_dict = results.to_dict(orient='records')
            
            # Génération des données d'animation
            animation_data = self._generate_animation_data(results_dict, course_id)
            
            # Sauvegarder la simulation dans la base de données
            simulation_id = self._save_simulation_to_db(
                course_id, 
                simulation_type, 
                selected_horses, 
                simulation_params, 
                horse_modifications,
                weather_conditions,
                track_conditions,
                results_dict
            )
            
            return {
                'simulation_id': simulation_id,
                'timestamp': datetime.now().isoformat(),
                'data': results_dict,
                'animation_data': animation_data
            }
            
        except Exception as e:
            self.logger.error(f"Error simulating course {course_id}: {str(e)}")
            raise

    def _apply_horse_modifications(self, simulation_data, horse_modifications):
        """Applique des modifications spécifiques aux chevaux pour la simulation"""
        try:
            # Pour chaque cheval à modifier
            for horse_id, modifications in horse_modifications.items():
                # Trouver les lignes correspondant à ce cheval
                horse_mask = simulation_data['id_cheval'] == int(horse_id)
                
                if not horse_mask.any():
                    continue  # Cheval non trouvé dans les données
                
                # Appliquer chaque modification
                for param, value in modifications.items():
                    if param in simulation_data.columns:
                        # Appliquer directement si le paramètre existe
                        simulation_data.loc[horse_mask, param] = value
                    elif param == 'poids_forme':
                        # Modification spéciale: combinaison de poids et condition physique
                        if 'poids' in simulation_data.columns:
                            # Modifier le poids
                            simulation_data.loc[horse_mask, 'poids'] = value
                    elif param == 'forme':
                        # Modification de la forme du cheval (expérience, condition physique)
                        if 'win_rate' in simulation_data.columns:
                            # Ajuster le taux de victoire selon la forme
                            current_win_rate = simulation_data.loc[horse_mask, 'win_rate'].values[0]
                            modifier = 1.0 + (value - 5) / 10.0  # Modifier de ±50% basé sur une échelle de 0-10
                            simulation_data.loc[horse_mask, 'win_rate'] = current_win_rate * modifier
            
            return simulation_data
            
        except Exception as e:
            self.logger.error(f"Error applying horse modifications: {str(e)}")
            return simulation_data

    def _apply_weather_conditions(self, simulation_data, weather_conditions):
        """Applique des conditions météorologiques à la simulation"""
        try:
            # Définir le type de météo
            if 'weather_type' in weather_conditions:
                weather_type = weather_conditions['weather_type']
                
                # Créer une nouvelle colonne ou remplacer l'existante
                if 'nebulositeLibelleCourt' in simulation_data.columns:
                    simulation_data['nebulositeLibelleCourt'] = weather_type
                else:
                    simulation_data['weather_type'] = weather_type
            
            # Définir la température
            if 'temperature' in weather_conditions:
                simulation_data['temperature'] = weather_conditions['temperature']
            
            # Définir les conditions de vent
            if 'wind_speed' in weather_conditions:
                simulation_data['forceVent'] = weather_conditions['wind_speed']
                
            if 'wind_direction' in weather_conditions:
                simulation_data['directionVent'] = weather_conditions['wind_direction']
            
            return simulation_data
            
        except Exception as e:
            self.logger.error(f"Error applying weather conditions: {str(e)}")
            return simulation_data

    def _apply_track_conditions(self, simulation_data, track_conditions):
        """Applique des conditions de piste à la simulation"""
        try:
            # Définir l'état du terrain
            if 'terrain' in track_conditions:
                if 'terrain' in simulation_data.columns:
                    simulation_data['terrain'] = track_conditions['terrain']
            
            # Définir la corde
            if 'corde' in track_conditions:
                if 'corde' in simulation_data.columns:
                    simulation_data['corde'] = track_conditions['corde']
            
            # Autres facteurs de piste
            if 'difficulty' in track_conditions:
                # Appliquer un facteur de difficulté général
                # Cette implémentation dépend de votre modèle
                difficulty = track_conditions['difficulty']
                
                # Exemple: affecter différemment les chevaux selon leur expérience
                if 'nb_courses_total' in simulation_data.columns:
                    # Les chevaux expérimentés sont moins affectés par la difficulté
                    for idx, row in simulation_data.iterrows():
                        experience = row['nb_courses_total']
                        experience_factor = min(1.0, experience / 20.0)  # Plafonné à 1.0
                        
                        # Effet inversement proportionnel à l'expérience
                        effect = difficulty * (1.0 - experience_factor)
                        
                        # Appliquer l'effet sur une caractéristique pertinente
                        if 'win_rate' in simulation_data.columns:
                            current_win_rate = simulation_data.at[idx, 'win_rate']
                            adjusted_win_rate = current_win_rate * (1.0 - effect/10.0)  # Réduire d'un pourcentage
                            simulation_data.at[idx, 'win_rate'] = adjusted_win_rate
            
            return simulation_data
            
        except Exception as e:
            self.logger.error(f"Error applying track conditions: {str(e)}")
            return simulation_data

# api/services/simulation_service.py (suite)

    def _generate_animation_data(self, simulation_results, course_id):
        """Génère des données pour l'animation de la course"""
        try:
            # Récupérer les données de la course
            query = text("""
                SELECT c.distance, c.type_course
                FROM courses c
                WHERE c.id = :course_id
            """)
            
            course = db.session.execute(query, {"course_id": course_id}).fetchone()
            
            if not course:
                return None
            
            # Trier les résultats par rang prédit
            sorted_results = sorted(simulation_results, key=lambda x: x.get('predicted_rank', float('inf')))
            
            # Définir la distance de la course
            distance = course.distance if course.distance else 2000
            
            # Créer les positions des chevaux à différents moments de la course
            animation_data = {
                'distance': distance,
                'type_course': course.type_course,
                'checkpoints': [0, 0.25, 0.5, 0.75, 1.0],  # Points de contrôle (% de la course)
                'horses': []
            }
            
            # Pour chaque cheval
            for idx, horse in enumerate(sorted_results):
                # Générer couleur unique basée sur l'index (pour visualisation)
                color = f"#{(idx * 13) % 256:02x}{(idx * 89) % 256:02x}{(idx * 179) % 256:02x}"
                
                # Créer un "scénario" de course pour ce cheval basé sur sa probabilité
                positions = self._generate_horse_race_scenario(
                    rank=horse.get('predicted_rank', idx+1),
                    win_prob=horse.get('in_top1_prob', 0),
                    total_horses=len(sorted_results)
                )
                
                horse_data = {
                    'id': horse.get('id_cheval'),
                    'name': horse.get('cheval_nom', f"Cheval {horse.get('id_cheval')}"),
                    'color': color,
                    'number': horse.get('numPmu', idx+1),
                    'final_rank': horse.get('predicted_rank', idx+1),
                    'positions': positions  # Position relative à chaque checkpoint (0-1, où 0 = premier, 1 = dernier)
                }
                
                animation_data['horses'].append(horse_data)
            
            return animation_data
            
        except Exception as e:
            self.logger.error(f"Error generating animation data: {str(e)}")
            return None

    def _generate_horse_race_scenario(self, rank, win_prob, total_horses):
        """Génère un scénario de course pour un cheval basé sur son rang final prédit et sa probabilité de victoire"""
        import random
        import numpy as np
        
        positions = []
        
        # Position initiale (départ) - légèrement aléatoire
        start_pos = random.uniform(0.2, 0.8)
        positions.append(start_pos)
        
        # Position mi-parcours - se rapproche de la position finale
        # Les favoris ont tendance à remonter, les outsiders à reculer
        if rank <= 3:
            # Favoris : généralement à l'avant à mi-parcours
            mid_pos = random.uniform(0, 0.4)
        elif rank <= total_horses * 0.5:
            # Milieu de peloton : position moyenne
            mid_pos = random.uniform(0.3, 0.7)
        else:
            # Fin de peloton : généralement en retrait
            mid_pos = random.uniform(0.6, 1.0)
        
        positions.append(mid_pos)
        
        # Position aux 3/4 du parcours - encore plus proche de la position finale
        # Avec un peu de variabilité basée sur la probabilité de victoire
        variability = 1 - win_prob  # Plus la probabilité est élevée, moins il y a de variabilité
        three_quarter_pos = (rank - 1) / (total_horses - 1) if total_horses > 1 else 0
        three_quarter_pos = max(0, min(1, three_quarter_pos + random.uniform(-0.2, 0.2) * variability))
        positions.append(three_quarter_pos)
        
        # Position avant l'arrivée - presque la position finale
        pre_final_pos = (rank - 1) / (total_horses - 1) if total_horses > 1 else 0
        pre_final_pos = max(0, min(1, pre_final_pos + random.uniform(-0.1, 0.1) * variability))
        positions.append(pre_final_pos)
        
        # Position finale - exactement le rang prédit
        final_pos = (rank - 1) / (total_horses - 1) if total_horses > 1 else 0
        positions.append(final_pos)
        
        return positions

    def _save_simulation_to_db(self, course_id, simulation_type, selected_horses, simulation_params,
                              horse_modifications, weather_conditions, track_conditions, results):
        """Sauvegarde la simulation dans la base de données"""
        try:
            # Convertir les listes et dictionnaires en JSON
            selected_horses_json = json.dumps(selected_horses) if selected_horses else "[]"
            simulation_params_json = json.dumps(simulation_params) if simulation_params else "{}"
            horse_modifications_json = json.dumps(horse_modifications) if horse_modifications else "{}"
            weather_conditions_json = json.dumps(weather_conditions) if weather_conditions else "{}"
            track_conditions_json = json.dumps(track_conditions) if track_conditions else "{}"
            results_json = json.dumps(results)
            
            # Sélectionner le modèle actif pour ce type de simulation
            query = text("""
                SELECT id
                FROM model_versions
                WHERE model_category = 'simulation'
                AND is_active = 1
                LIMIT 1
            """)
            
            model_result = db.session.execute(query).fetchone()
            model_id = model_result.id if model_result else None
            
            # Préparer l'insertion
            query = text("""
                INSERT INTO simulations 
                (course_id, simulation_type, selected_horses, simulation_params, 
                 horse_modifications, weather_conditions, track_conditions,
                 resultat_simule, model_version_id, created_at)
                VALUES (:course_id, :simulation_type, :selected_horses, :simulation_params,
                        :horse_modifications, :weather_conditions, :track_conditions,
                        :results, :model_id, :created_at)
                RETURNING id
            """)
            
            # Exécuter l'insertion
            result = db.session.execute(query, {
                "course_id": course_id,
                "simulation_type": simulation_type,
                "selected_horses": selected_horses_json,
                "simulation_params": simulation_params_json,
                "horse_modifications": horse_modifications_json,
                "weather_conditions": weather_conditions_json,
                "track_conditions": track_conditions_json,
                "results": results_json,
                "model_id": model_id,
                "created_at": datetime.now()
            })
            
            # Récupérer l'ID généré
            simulation_id = result.fetchone()[0] if result else None
            
            db.session.commit()
            
            return simulation_id
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error saving simulation to database: {str(e)}")
            return None

    def log_simulation_usage(self, user_id, course_id, simulation_type, selected_horses):
        """Enregistre l'utilisation d'une simulation par un utilisateur"""
        try:
            # Insérer dans la table d'usage
            query = text("""
                INSERT INTO simulation_usage 
                (user_id, course_id, simulation_type, selected_horses, used_at)
                VALUES (:user_id, :course_id, :simulation_type, :selected_horses, :used_at)
            """)
            
            db.session.execute(query, {
                "user_id": user_id,
                "course_id": course_id,
                "simulation_type": simulation_type,
                "selected_horses": json.dumps(selected_horses) if selected_horses else "[]",
                "used_at": datetime.now()
            })
            
            db.session.commit()
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error logging simulation usage: {str(e)}")

    def get_simulations_count_today(self, user_id):
        """Récupère le nombre de simulations utilisées aujourd'hui par l'utilisateur"""
        try:
            # Récupérer le début de la journée
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Requête SQL pour compter les simulations
            query = text("""
                SELECT COUNT(*) AS count
                FROM simulation_usage
                WHERE user_id = :user_id
                AND used_at >= :today_start
            """)
            
            result = db.session.execute(query, {"user_id": user_id, "today_start": today_start}).fetchone()
            
            return result.count if result else 0
            
        except Exception as e:
            self.logger.error(f"Error counting simulations used today: {str(e)}")
            return 0

    def get_user_simulation_history(self, user_id, page=1, per_page=10):
        """Récupère l'historique des simulations d'un utilisateur"""
        try:
            # Calculer l'offset pour la pagination
            offset = (page - 1) * per_page
            
            # Requête SQL pour récupérer les simulations
            query = text("""
                SELECT su.id, su.course_id, su.simulation_type, su.selected_horses, su.used_at,
                       c.lieu, c.date_heure, c.libelle, c.type_course,
                       s.resultat_simule
                FROM simulation_usage su
                JOIN courses c ON su.course_id = c.id
                LEFT JOIN simulations s ON (
                    su.course_id = s.course_id AND 
                    su.simulation_type = s.simulation_type AND
                    su.selected_horses = s.selected_horses
                )
                WHERE su.user_id = :user_id
                ORDER BY su.used_at DESC
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
                simulation = {
                    "id": row.id,
                    "course_id": row.course_id,
                    "simulation_type": row.simulation_type,
                    "selected_horses": json.loads(row.selected_horses) if row.selected_horses else [],
                    "used_at": row.used_at.isoformat() if row.used_at else None,
                    "lieu": row.lieu,
                    "date_heure": row.date_heure.isoformat() if row.date_heure else None,
                    "libelle": row.libelle,
                    "type_course": row.type_course,
                    "resultat_simule": json.loads(row.resultat_simule) if row.resultat_simule else None
                }
                history_data.append(simulation)
            
            # Compter le nombre total de simulations pour la pagination
            count_query = text("""
                SELECT COUNT(*) AS count
                FROM simulation_usage
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
            self.logger.error(f"Error retrieving simulation history: {str(e)}")
            return {'count': 0, 'total_pages': 0, 'data': []}

    def get_simulation_by_id(self, simulation_id, user_id):
        """Récupère les détails d'une simulation spécifique"""
        try:
            # Vérifier que la simulation appartient à l'utilisateur
            query = text("""
                SELECT su.id, su.course_id, su.simulation_type, su.selected_horses, su.used_at,
                       c.lieu, c.date_heure, c.libelle, c.type_course,
                       s.resultat_simule, s.horse_modifications, s.weather_conditions, s.track_conditions
                FROM simulation_usage su
                JOIN courses c ON su.course_id = c.id
                LEFT JOIN simulations s ON (
                    su.course_id = s.course_id AND 
                    su.simulation_type = s.simulation_type AND
                    su.selected_horses = s.selected_horses
                )
                WHERE su.id = :simulation_id AND su.user_id = :user_id
            """)
            
            result = db.session.execute(query, {
                "simulation_id": simulation_id,
                "user_id": user_id
            }).fetchone()
            
            if not result:
                return None
            
            # Convertir en dictionnaire
            simulation = {
                "id": result.id,
                "course_id": result.course_id,
                "simulation_type": result.simulation_type,
                "selected_horses": json.loads(result.selected_horses) if result.selected_horses else [],
                "used_at": result.used_at.isoformat() if result.used_at else None,
                "lieu": result.lieu,
                "date_heure": result.date_heure.isoformat() if result.date_heure else None,
                "libelle": result.libelle,
                "type_course": result.type_course,
                "results": json.loads(result.resultat_simule) if result.resultat_simule else None,
                "horse_modifications": json.loads(result.horse_modifications) if result.horse_modifications else None,
                "weather_conditions": json.loads(result.weather_conditions) if result.weather_conditions else None,
                "track_conditions": json.loads(result.track_conditions) if result.track_conditions else None
            }
            
            # Récupérer les données d'animation si disponibles
            animation_data = self.get_simulation_animation(simulation_id)
            if animation_data:
                simulation['animation_data'] = animation_data
            
            return simulation
            
        except Exception as e:
            self.logger.error(f"Error retrieving simulation {simulation_id}: {str(e)}")
            return None

    def get_simulation_animation(self, simulation_id):
        """Récupère les données d'animation pour une simulation"""
        try:
            # D'abord récupérer la simulation
            query = text("""
                SELECT s.course_id, s.resultat_simule
                FROM simulations s
                JOIN simulation_usage su ON s.course_id = su.course_id 
                                        AND s.simulation_type = su.simulation_type
                WHERE su.id = :simulation_id
            """)
            
            result = db.session.execute(query, {"simulation_id": simulation_id}).fetchone()
            
            if not result:
                return None
            
            # Générer les données d'animation
            results = json.loads(result.resultat_simule) if result.resultat_simule else None
            
            if not results:
                return None
            
            return self._generate_animation_data(results, result.course_id)
            
        except Exception as e:
            self.logger.error(f"Error retrieving animation data for simulation {simulation_id}: {str(e)}")
            return None

    def analyze_parameter_impact(self, course_id, selected_horses, modifications, simulation_results):
        """Analyse l'impact des modifications de paramètres sur les résultats de la simulation"""
        try:
            # Récupérer les données de la course sans modifications
            baseline_simulation = self.simulate_course(
                course_id, 
                selected_horses=selected_horses,
                simulation_type='basic'
            )
            
            baseline_results = baseline_simulation['data']
            
            # Convertir en dictionnaires pour faciliter la comparaison
            baseline_dict = {str(horse['id_cheval']): horse for horse in baseline_results}
            modified_dict = {str(horse['id_cheval']): horse for horse in simulation_results}
            
            # Analyser les changements pour chaque cheval modifié
            impact_analysis = []
            
            for horse_id, horse_mods in modifications.items():
                if horse_id in baseline_dict and horse_id in modified_dict:
                    baseline_horse = baseline_dict[horse_id]
                    modified_horse = modified_dict[horse_id]
                    
                    # Calculer les différences
                    rank_before = baseline_horse.get('predicted_rank', 0)
                    rank_after = modified_horse.get('predicted_rank', 0)
                    rank_change = rank_before - rank_after  # Positif = amélioration
                    
                    prob_before = baseline_horse.get('in_top3_prob', 0)
                    prob_after = modified_horse.get('in_top3_prob', 0)
                    prob_change = prob_after - prob_before
                    
                    # Créer l'analyse d'impact
                    impact = {
                        'id_cheval': horse_id,
                        'name': modified_horse.get('cheval_nom', f"Cheval {horse_id}"),
                        'modifications': horse_mods,
                        'rank_before': rank_before,
                        'rank_after': rank_after,
                        'rank_change': rank_change,
                        'probability_before': prob_before,
                        'probability_after': prob_after,
                        'probability_change': prob_change,
                        'impact_assessment': self._assess_impact(rank_change, prob_change)
                    }
                    
                    impact_analysis.append(impact)
            
            return impact_analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing parameter impact: {str(e)}")
            return []

    def _assess_impact(self, rank_change, prob_change):
        """Évalue l'impact global des modifications"""
        if rank_change > 3 or prob_change > 0.2:
            return "Très positif"
        elif rank_change > 1 or prob_change > 0.1:
            return "Positif"
        elif rank_change < -3 or prob_change < -0.2:
            return "Très négatif"
        elif rank_change < -1 or prob_change < -0.1:
            return "Négatif"
        else:
            return "Marginal"

    def compare_multiple_scenarios(self, course_id, scenarios):
        """Compare plusieurs scénarios de simulation"""
        try:
            results = []
            
            # Exécuter chaque scénario
            for idx, scenario in enumerate(scenarios):
                # Extraire les paramètres du scénario
                selected_horses = scenario.get('selected_horses', [])
                simulation_params = scenario.get('simulation_params', {})
                horse_modifications = scenario.get('horse_modifications', {})
                weather_conditions = scenario.get('weather_conditions', None)
                track_conditions = scenario.get('track_conditions', None)
                scenario_name = scenario.get('name', f"Scénario {idx+1}")
                
                # Exécuter la simulation
                sim_result = self.simulate_course(
                    course_id, 
                    selected_horses=selected_horses, 
                    simulation_params=simulation_params,
                    horse_modifications=horse_modifications,
                    weather_conditions=weather_conditions,
                    track_conditions=track_conditions,
                    simulation_type='advanced'
                )
                
                # Ajouter le nom du scénario
                sim_result['scenario_name'] = scenario_name
                results.append(sim_result)
            
            # Analyser les différences entre les scénarios
            comparative_analysis = self._analyze_scenario_differences(results)
            
            return {
                'timestamp': datetime.now().isoformat(),
                'data': results,
                'analysis': comparative_analysis
            }
            
        except Exception as e:
            self.logger.error(f"Error comparing scenarios for course {course_id}: {str(e)}")
            raise

    def _analyze_scenario_differences(self, scenario_results):
        """Analyse les différences entre plusieurs scénarios"""
        try:
            # Extraire les résultats de chaque scénario
            scenarios_data = []
            
            for scenario in scenario_results:
                scenarios_data.append({
                    'name': scenario.get('scenario_name', "Scénario sans nom"),
                    'results': scenario.get('data', [])
                })
            
            if len(scenarios_data) < 2:
                return {"message": "Au moins deux scénarios sont nécessaires pour une comparaison"}
            
            # Trouver tous les chevaux à travers tous les scénarios
            all_horses = set()
            for scenario in scenarios_data:
                for horse in scenario['results']:
                    all_horses.add(str(horse.get('id_cheval')))
            
            # Comparer les rangs et probabilités de chaque cheval dans chaque scénario
            comparison = []
            
            for horse_id in all_horses:
                horse_comparison = {'id_cheval': horse_id, 'scenarios': []}
                
                # Récupérer le nom du cheval du premier scénario où il apparaît
                for scenario in scenarios_data:
                    for horse in scenario['results']:
                        if str(horse.get('id_cheval')) == horse_id:
                            horse_comparison['name'] = horse.get('cheval_nom', f"Cheval {horse_id}")
                            break
                    if 'name' in horse_comparison:
                        break
                
                # Comparer à travers les scénarios
                for scenario in scenarios_data:
                    # Trouver le cheval dans ce scénario
                    horse_data = None
                    for horse in scenario['results']:
                        if str(horse.get('id_cheval')) == horse_id:
                            horse_data = horse
                            break
                    
                    # Ajouter les données du scénario
                    if horse_data:
                        horse_comparison['scenarios'].append({
                            'scenario_name': scenario['name'],
                            'rank': horse_data.get('predicted_rank', 0),
                            'win_probability': horse_data.get('in_top1_prob', 0),
                            'top3_probability': horse_data.get('in_top3_prob', 0)
                        })
                    else:
                        # Le cheval n'est pas dans ce scénario
                        horse_comparison['scenarios'].append({
                            'scenario_name': scenario['name'],
                            'rank': None,
                            'win_probability': 0,
                            'top3_probability': 0
                        })
                
                comparison.append(horse_comparison)
            
            # Trier par la moyenne des rangs (pour mettre les meilleurs chevaux en premier)
            def avg_rank(horse_comp):
                ranks = [s['rank'] for s in horse_comp['scenarios'] if s['rank'] is not None]
                return sum(ranks) / len(ranks) if ranks else float('inf')
            
            comparison.sort(key=avg_rank)
            
            # Ajouter une analyse globale
            global_analysis = {
                'total_horses': len(all_horses),
                'total_scenarios': len(scenarios_data),
                'best_scenario': self._find_best_scenario(scenarios_data),
                'key_differences': self._find_key_differences(comparison, scenarios_data)
            }
            
            return {
                'horse_comparison': comparison,
                'global_analysis': global_analysis
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing scenario differences: {str(e)}")
            return {"message": "Erreur lors de l'analyse des différences de scénarios"}

    def _find_best_scenario(self, scenarios_data):
        """Détermine le meilleur scénario basé sur les performances globales"""
        try:
            # Calculer un score pour chaque scénario
            # Plus le score est élevé, meilleur est le scénario
            scenario_scores = []
            
            for scenario in scenarios_data:
                # Calculer le score moyen des chevaux
                total_score = 0
                for horse in scenario['results']:
                    # Le score est basé sur la probabilité de gagner et d'être dans le top 3
                    horse_score = horse.get('in_top1_prob', 0) * 3 + horse.get('in_top3_prob', 0)
                    total_score += horse_score
                
                avg_score = total_score / len(scenario['results']) if scenario['results'] else 0
                
                scenario_scores.append({
                    'name': scenario['name'],
                    'score': avg_score
                })
            
            # Trier par score décroissant
            scenario_scores.sort(key=lambda x: x['score'], reverse=True)
            
            # Retourner le meilleur scénario
            if scenario_scores:
                return {
                    'name': scenario_scores[0]['name'],
                    'score': scenario_scores[0]['score'],
                    'all_scores': scenario_scores
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error finding best scenario: {str(e)}")
            return None

    def _find_key_differences(self, horse_comparison, scenarios_data):
        """Identifie les différences clés entre les scénarios"""
        try:
            key_differences = []
            
            # Trouver les chevaux avec les plus grandes variations de rang
            for horse in horse_comparison:
                ranks = [s['rank'] for s in horse['scenarios'] if s['rank'] is not None]
                
                if len(ranks) < 2:
                    continue
                
                min_rank = min(ranks)
                max_rank = max(ranks)
                rank_range = max_rank - min_rank
                
                # Si la variation est significative
                if rank_range >= 3:
                    # Trouver les scénarios avec les meilleurs et pires rangs
                    best_scenario = None
                    worst_scenario = None
                    
                    for s in horse['scenarios']:
                        if s['rank'] == min_rank:
                            best_scenario = s['scenario_name']
                        if s['rank'] == max_rank:
                            worst_scenario = s['scenario_name']
                    
                    key_differences.append({
                        'type': 'rank_variation',
                        'horse_id': horse['id_cheval'],
                        'horse_name': horse.get('name', f"Cheval {horse['id_cheval']}"),
                        'variation': rank_range,
                        'best_scenario': best_scenario,
                        'worst_scenario': worst_scenario,
                        'best_rank': min_rank,
                        'worst_rank': max_rank
                    })
            
            # Trier par variation décroissante
            key_differences.sort(key=lambda x: x['variation'], reverse=True)
            
            return key_differences[:5]  # Retourner les 5 différences les plus importantes
            
        except Exception as e:
            self.logger.error(f"Error finding key differences: {str(e)}")
            return []