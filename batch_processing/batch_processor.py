import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
import joblib
import os
import json
from sqlalchemy import create_engine
from concurrent.futures import ProcessPoolExecutor, as_completed

# Import des nouveaux modules
from data_preparation.enhanced_data_prep import EnhancedDataPreparation
from model.dual_prediction_model import DualPredictionModel
from database.database import save_prediction

import json
import os

# Charger la configuration
config_path = 'config/config.json'
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "pmu_ia",
    "port": "3306",
    "connector": "pymysql"
}

if os.path.exists(config_path):
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
            if 'db_config' in config:
                db_config = config['db_config']
    except Exception as e:
        print(f"Error loading config: {e}")

# Modifier la chaîne de connexion
#engine = create_engine(f"mysql+{db_config.get('connector', 'pymysql')}://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}")
class BatchProcessor:
    """Classe pour le traitement par lots des prédictions de courses, avec support pour les deux modèles."""
    
    def __init__(self, data_prep=None, model=None, db_path='pmu_ia', model_path='model/trained_models'):
        """Initialise le processeur par lots avec les nouvelles classes."""
        self.logger = logging.getLogger(__name__)
        self.db_path = db_path
        self.model_path = model_path
        
        
        # Initialiser une connexion à la base de données
        try:
            #self.engine = create_engine(f"mysql+mysqlconnector://{self.db_config['user']}:{self.db_config['password']}@{self.db_config['host']}:{self.db_config['port']}/{self.db_config['database']}")
            self.engine = create_engine(f"mysql+{db_config.get('connector', 'pymysql')}://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}")



            self.logger.info(f"Connexion à la base de données {db_path} établie")
        except Exception as e:
            self.logger.error(f"Erreur de connexion à la BD: {e}")
            self.engine = None
        
        # Utiliser les instances passées ou en créer de nouvelles
        self.data_prep = data_prep or EnhancedDataPreparation(db_path)
        
        # Utiliser le modèle dual passé ou en créer un nouveau
        if model:
            self.model = model
        else:
            self.model = DualPredictionModel(base_path=model_path)
            
            # Essayer de charger les modèles
            standard_model_path = os.path.join(model_path, 'standard_latest.pkl')
            simulation_model_path = os.path.join(model_path, 'simulation_latest.pkl')
            
            if os.path.exists(standard_model_path):
                self.model.load_standard_model(standard_model_path)
            else:
                self.logger.warning(f"Modèle standard non trouvé à {standard_model_path}")
                
            if os.path.exists(simulation_model_path):
                self.model.load_simulation_model(simulation_model_path)
            else:
                self.logger.warning(f"Modèle de simulation non trouvé à {simulation_model_path}")
    
    def train_dual_models(self, days_back=None, test_days=14, 
                        standard_model_type='xgboost', simulation_model_type='xgboost_ranking'):
        """Entraîne les deux modèles (standard et simulation)."""
        
        # Définir un test_size fixe, indépendant de days_back et test_days
        test_size = 0.2
        
        if days_back is None:
            self.logger.info("Entraînement des modèles sur toutes les données disponibles")
        else:
            self.logger.info(f"Entraînement des modèles sur les données des {days_back} derniers jours")
        
        # Préparer les dates de début et fin
        end_date = datetime.now()
        start_date_str = None
        
        if days_back is not None:
            start_date = end_date - timedelta(days=days_back)
            start_date_str = start_date.strftime("%Y-%m-%d")
        
        end_date_str = end_date.strftime("%Y-%m-%d")
        
        # Log informatif
        if start_date_str:
            self.logger.info(f"Récupération des données du {start_date_str} au {end_date_str}")
        else:
            self.logger.info(f"Récupération de toutes les données jusqu'au {end_date_str}")
        
        # Récupérer les données d'entraînement
        training_data = self.data_prep.get_training_data(
            start_date=start_date_str,
            end_date=end_date_str
        )
        
        if training_data.empty:
            self.logger.error("Aucune donnée d'entraînement trouvée")
            return None
        
        self.logger.info(f"Données récupérées: {len(training_data)} échantillons")
        
        # Créer des features avancées
        enhanced_data = self.data_prep.create_advanced_features(training_data)
        
        # Encoder pour le modèle
        prepared_data = self.data_prep.encode_features_for_model(enhanced_data, is_training=True)
        
        # Initialiser les modèles si nécessaire
        if self.model.standard_model is None:
            self.model.initialize_standard_model(model_type=standard_model_type)
        
        if self.model.simulation_model is None:
            self.model.initialize_simulation_model(model_type=simulation_model_type)
        
        # Créer les variables cibles
        final_data = self.model.create_target_variables(prepared_data)
        
        # Entraîner le modèle standard avec un test_size fixe
        self.logger.info(f"Entraînement du modèle standard ({standard_model_type}) avec test_size={test_size}")
        standard_accuracy, standard_path = self.model.train_standard_model(final_data, test_size=test_size)
        
        # Entraîner le modèle de simulation avec le même test_size fixe
        self.logger.info(f"Entraînement du modèle de simulation ({simulation_model_type}) avec test_size={test_size}")
        simulation_metrics, simulation_path = self.model.train_simulation_model(final_data, test_size=test_size)
        
        self.logger.info("Entraînement des modèles terminé")
        
        return {
            'standard_model_path': standard_path,
            'standard_accuracy': standard_accuracy,
            'simulation_model_path': simulation_path,
            'simulation_metrics': simulation_metrics,
            'samples_used': len(final_data)
        }
    
        
    def predict_upcoming_races_standard(self, days_ahead=1, output_dir='predictions'):
        """Prédit les résultats pour toutes les courses à venir avec le modèle standard."""
        if self.model.standard_model is None:
            self.logger.error("Modèle standard non chargé. Impossible de faire des prédictions.")
            return None
        
        self.logger.info(f"Prédiction standard des courses pour les {days_ahead} prochains jours")
        
        # Créer le répertoire de sortie si nécessaire
        os.makedirs(output_dir, exist_ok=True)
        
        # Définir la période de recherche
        now = datetime.now()
        end_date = now + timedelta(days=days_ahead)
        
        # Récupérer les courses à venir
        upcoming_races = self.data_prep.get_course_data(
            start_date=now.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d")
        )
        
        if upcoming_races.empty:
            self.logger.info(f"Aucune course trouvée pour les {days_ahead} prochains jours")
            return []
        
        self.logger.info(f"Traitement de {len(upcoming_races)} courses à venir")
        
        # Stocker les résultats
        all_predictions = []
        
        # Traiter chaque course
        for idx, race in upcoming_races.iterrows():
            race_id = race['id']
            self.logger.info(f"Traitement de la course {race_id} ({idx+1}/{len(upcoming_races)})")
            
            try:
                # Préparer les données pour la prédiction
                prediction_data = self.data_prep.get_participant_data(course_id=race_id)
                
                if prediction_data is None or prediction_data.empty:
                    self.logger.warning(f"Pas de données disponibles pour la course {race_id}")
                    continue
                
                # Créer des features avancées
                enhanced_data = self.data_prep.create_advanced_features(prediction_data)
                
                # Encoder pour le modèle
                prepared_data = self.data_prep.encode_features_for_model(enhanced_data, is_training=False)
                
                # Faire la prédiction avec le modèle standard
                results = self.model.predict_standard(prepared_data)
                
                if results is None:
                    self.logger.warning(f"Échec de la prédiction pour la course {race_id}")
                    continue
                
                # Ajouter des informations sur la course
                results['course_id'] = race_id
                
                # Ajouter les informations disponibles de la course
                for col in ['numReunion', 'numOrdre', 'hippodrome', 'date_heure', 'distance', 'type_course']:
                    if col in race:
                        results[col] = race[col]
                
                # Sauvegarder les prédictions
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_file = f"{output_dir}/prediction_{race_id}_{timestamp}.json"
                
                # Convertir le DataFrame en dictionnaire
                prediction_dict = {
                    'course_id': race_id,
                    'date_heure': str(race['date_heure']) if 'date_heure' in race else None,
                    'lieu': race['lieu'] if 'lieu' in race else None,
                    'distance': race['distance'] if 'distance' in race else None,
                    'type_course': race['type_course'] if 'type_course' in race else None,
                    'predictions': results.to_dict(orient='records'),
                    'timestamp': timestamp,
                    'model_type': 'standard'
                }
                
                # Sauvegarder au format JSON
                with open(output_file, 'w') as f:
                    json.dump(prediction_dict, f, indent=2)
                
                # Sauvegarder aussi dans la base de données
                save_prediction(race_id, json.dumps(results.to_dict(orient='records')), 
                                results['top3_probability'].mean() if 'top3_probability' in results.columns else 0.5)
                
                all_predictions.append(prediction_dict)
                self.logger.info(f"Prédiction pour la course {race_id} sauvegardée dans {output_file}")
                
            except Exception as e:
                self.logger.error(f"Erreur lors de la prédiction pour la course {race_id}: {str(e)}")
        
        self.logger.info(f"Traitement terminé. {len(all_predictions)} prédictions générées.")
        return all_predictions
    
    def simulate_race(self, course_id, selected_horses, simulation_params=None):
        """Simule une course avec des paramètres personnalisés."""
        if self.model.simulation_model is None:
            self.logger.error("Modèle de simulation non chargé. Impossible de faire des simulations.")
            return None
        
        self.logger.info(f"Simulation de la course {course_id} avec {len(selected_horses)} chevaux")
        
        try:
            # Préparer les données pour la simulation
            simulation_data = self.data_prep.prepare_data_for_simulation(
                course_id=course_id,
                selected_horses=selected_horses,
                simulation_params=simulation_params
            )
            
            if simulation_data is None or simulation_data.empty:
                self.logger.warning(f"Pas de données disponibles pour la simulation de la course {course_id}")
                return None
            
            # Faire la prédiction avec le modèle de simulation
            results = self.model.predict_simulation(simulation_data)
            
            if results is None:
                self.logger.warning(f"Échec de la simulation pour la course {course_id}")
                return None
            
            # Ajouter des métadonnées
            results['course_id'] = course_id
            results['simulation_timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Ajouter les paramètres de simulation sous forme de chaîne JSON
            if simulation_params:
                results['simulation_params'] = json.dumps(simulation_params)
            
            # Sauvegarder les résultats de simulation
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_dir = 'simulations'
            os.makedirs(output_dir, exist_ok=True)
            output_file = f"{output_dir}/simulation_{course_id}_{timestamp}.json"
            
            # Convertir en format JSON
            simulation_dict = {
                'course_id': course_id,
                'selected_horses': selected_horses,
                'simulation_params': simulation_params,
                'results': results.to_dict(orient='records'),
                'timestamp': timestamp
            }
            
            # Sauvegarder au format JSON
            with open(output_file, 'w') as f:
                json.dump(simulation_dict, f, indent=2)
            
            self.logger.info(f"Simulation pour la course {course_id} sauvegardée dans {output_file}")
            
            # Sauvegarder aussi dans la base de données (table simulations)
            try:
                from sqlalchemy.orm import sessionmaker
                from database.setup_database import engine, Simulation
                
                Session = sessionmaker(bind=engine)
                session = Session()
                
                simulation_record = Simulation(
                    utilisateur_id=1,  # Utilisateur par défaut (à modifier pour un système multi-utilisateurs)
                    date_simulation=datetime.now(),
                    id_course=course_id,
                    chevaux_selectionnes=json.dumps(selected_horses),
                    resultat_simule=json.dumps(results.to_dict(orient='records'))
                )
                
                session.add(simulation_record)
                session.commit()
                session.close()
                
                self.logger.info(f"Simulation sauvegardée dans la base de données")
            except Exception as e:
                self.logger.error(f"Erreur lors de la sauvegarde en base de données: {str(e)}")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la simulation pour la course {course_id}: {str(e)}")
            return None
    
    def evaluate_past_predictions(self, days_back=7, output_dir='evaluation'):
        """Évalue la qualité des prédictions passées en les comparant aux résultats réels."""
        self.logger.info(f"Évaluation des prédictions des {days_back} derniers jours")
        
        # Créer le répertoire de sortie si nécessaire
        os.makedirs(output_dir, exist_ok=True)
        
        # Définir la période de recherche
        now = datetime.now()
        start_date = now - timedelta(days=days_back)
        
        # Récupérer les courses terminées
        completed_races = self.data_prep.get_course_data(
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=now.strftime("%Y-%m-%d")
        )
        
        if completed_races.empty:
            self.logger.info(f"Aucune course trouvée pour les {days_back} derniers jours")
            return None
        
        # Filtrer les courses terminées avec résultats
        completed_races = completed_races[completed_races['ordreArrivee'].notnull()]
        
        if completed_races.empty:
            self.logger.info(f"Aucune course terminée trouvée pour les {days_back} derniers jours")
            return None
        
        self.logger.info(f"Évaluation de {len(completed_races)} courses terminées")
        
        # Stocker les résultats d'évaluation
        evaluation_results = []
        
        # Traiter chaque course
        for idx, race in completed_races.iterrows():
            race_id = race['id']
            self.logger.info(f"Évaluation de la course {race_id} ({idx+1}/{len(completed_races)})")
            
            try:
                # Récupérer les participants avec leurs positions finales
                participants = self.data_prep.get_participant_data(course_id=race_id)
                
                if participants is None or participants.empty:
                    self.logger.warning(f"Pas de participants trouvés pour la course {race_id}")
                    continue
                
                # Récupérer l'ordre d'arrivée
                ordreArrivee = race['ordreArrivee']
                if isinstance(ordreArrivee, str):
                    try:
                        # Essayer de le parser comme JSON
                        ordreArrivee = json.loads(ordreArrivee)
                    except:
                        ordreArrivee = None
                
                if not ordreArrivee:
                    self.logger.warning(f"Pas d'ordre d'arrivée trouvé pour la course {race_id}")
                    continue
                
                # Vérifier si nous avons des prédictions sauvegardées pour cette course
                prediction_files = [f for f in os.listdir('predictions') if f.startswith(f"prediction_{race_id}_")]
                
                if not prediction_files:
                    self.logger.warning(f"Pas de prédictions trouvées pour la course {race_id}")
                    continue
                
                # Prendre la prédiction la plus récente
                prediction_file = sorted(prediction_files)[-1]
                prediction_path = os.path.join('predictions', prediction_file)
                
                with open(prediction_path, 'r') as f:
                    prediction = json.load(f)
                
                # Évaluer la qualité des prédictions
                if isinstance(prediction.get('predictions'), list):
                    prediction_df = pd.DataFrame(prediction['predictions'])
                else:
                    self.logger.warning(f"Format de prédiction invalide pour la course {race_id}")
                    continue
                
                # Créer un DataFrame pour les résultats réels basés sur l'ordre d'arrivée
                real_positions = []
                for position, numPmu in enumerate(ordreArrivee, 1):
                    if isinstance(numPmu, list):
                        numPmu = numPmu[0]  # Prendre le premier si c'est une liste
                    
                    # Trouver les informations du cheval
                    cheval = participants[participants['numPmu'] == numPmu]
                    if not cheval.empty:
                        real_positions.append({
                            'numPmu': numPmu,
                            'position': position,
                            'nom': cheval.iloc[0]['cheval_nom'] if 'cheval_nom' in cheval.columns else None
                        })
                
                real_df = pd.DataFrame(real_positions)
                
                # Fusionner avec les prédictions
                merged_df = pd.merge(
                    prediction_df,
                    real_df,
                    on=['numPmu'],
                    how='left',
                    suffixes=('_pred', '')
                )
                
                # Calculer les métriques d'évaluation
                metrics = {
                    'course_id': race_id,
                    'date_heure': str(race['date_heure']) if 'date_heure' in race else None,
                    'lieu': race['lieu'] if 'lieu' in race else None
                }
                
                # Est-ce que le cheval avec la plus haute probabilité a gagné?
                if 'top3_probability' in merged_df.columns:
                    winner_pred = merged_df.sort_values('top3_probability', ascending=False).iloc[0]
                    winner_real = merged_df[merged_df['position'] == 1].iloc[0] if len(merged_df[merged_df['position'] == 1]) > 0 else None
                    
                    metrics['predicted_winner'] = winner_pred['nom'] if 'nom' in winner_pred else None
                    metrics['predicted_winner_probability'] = float(winner_pred['top3_probability'])
                    metrics['actual_winner'] = winner_real['nom'] if winner_real is not None and 'nom' in winner_real else 'Unknown'
                    
                    if metrics['predicted_winner'] and metrics['actual_winner'] and metrics['actual_winner'] != 'Unknown':
                        metrics['winner_correctly_predicted'] = metrics['predicted_winner'] == metrics['actual_winner']
                    else:
                        metrics['winner_correctly_predicted'] = False
                
                # Top-N Accuracy
                for n in [2, 3, 5]:
                    if 'predicted_rank' in merged_df.columns and 'position' in merged_df.columns:
                        top_n_pred = set(merged_df.sort_values('predicted_rank').head(n)['numPmu'].tolist())
                        top_n_actual = set(merged_df.sort_values('position').head(n)['numPmu'].tolist())
                        
                        intersection = len(top_n_pred.intersection(top_n_actual))
                        accuracy = intersection / min(n, len(top_n_actual)) if len(top_n_actual) > 0 else 0
                        
                        metrics[f'top_{n}_accuracy'] = accuracy
                
                # Spearman's rank correlation
                if 'predicted_rank' in merged_df.columns and 'position' in merged_df.columns:
                    # Enlever les lignes avec des valeurs manquantes
                    valid_df = merged_df.dropna(subset=['predicted_rank', 'position'])
                    
                    if len(valid_df) >= 3:  # Besoin d'au moins 3 points pour une corrélation significative
                        from scipy.stats import spearmanr
                        correlation, p_value = spearmanr(valid_df['predicted_rank'], valid_df['position'])
                        
                        metrics['rank_correlation'] = correlation
                        metrics['rank_correlation_p_value'] = p_value
                
                evaluation_results.append(metrics)
                
                # Sauvegarder les résultats d'évaluation
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_file = f"{output_dir}/evaluation_{race_id}_{timestamp}.json"
                
                with open(output_file, 'w') as f:
                    json.dump(metrics, f, indent=2)
                
                self.logger.info(f"Évaluation pour la course {race_id} sauvegardée dans {output_file}")
                
            except Exception as e:
                self.logger.error(f"Erreur lors de l'évaluation pour la course {race_id}: {str(e)}")
        
        # Agréger les résultats d'évaluation
        if evaluation_results:
            evaluation_df = pd.DataFrame(evaluation_results)
            
            # Calculer les moyennes
            summary = {
                'total_races_evaluated': len(evaluation_df),
                'winner_prediction_accuracy': evaluation_df['winner_correctly_predicted'].mean() if 'winner_correctly_predicted' in evaluation_df.columns else None,
                'avg_top_2_accuracy': evaluation_df['top_2_accuracy'].mean() if 'top_2_accuracy' in evaluation_df.columns else None,
                'avg_top_3_accuracy': evaluation_df['top_3_accuracy'].mean() if 'top_3_accuracy' in evaluation_df.columns else None,
                'avg_top_5_accuracy': evaluation_df['top_5_accuracy'].mean() if 'top_5_accuracy' in evaluation_df.columns else None,
                'avg_rank_correlation': evaluation_df['rank_correlation'].mean() if 'rank_correlation' in evaluation_df.columns else None,
                'evaluation_period': f"{start_date.strftime('%Y-%m-%d')} to {now.strftime('%Y-%m-%d')}",
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Sauvegarder le résumé
            summary_file = f"{output_dir}/evaluation_summary_{now.strftime('%Y%m%d')}.json"
            
            with open(summary_file, 'w') as f:
                json.dump(summary, f, indent=2)
            
            self.logger.info(f"Résumé de l'évaluation sauvegardé dans {summary_file}")
            
            return summary
        
        return None
    
    # Méthode de compatibilité pour faciliter la migration
    def predict_upcoming_races(self, days_ahead=1, output_dir='predictions'):
        """Méthode de compatibilité qui appelle la nouvelle méthode predict_upcoming_races_standard"""
        return self.predict_upcoming_races_standard(days_ahead, output_dir)