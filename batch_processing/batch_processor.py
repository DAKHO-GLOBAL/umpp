import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
import joblib
import os
import json
from sqlalchemy import create_engine
from concurrent.futures import ProcessPoolExecutor, as_completed

# Import des modules personnalisés
from data_preparation.data_preparation import DataPreparation
from model.prediction_model import PredictionModel

class BatchProcessor:
    """Classe pour le traitement par lots des prédictions de courses."""
    
    def __init__(self, db_path='database/db/pmu_data.db', model_path='model/trained_models/horse_race_model.pkl'):
        """Initialise le processeur par lots."""
        self.logger = logging.getLogger(__name__)
        self.db_path = db_path
        self.engine = create_engine(f'sqlite:///{db_path}')
        self.data_prep = DataPreparation(db_path)
        
        # Charger le modèle
        if os.path.exists(model_path):
            try:
                self.model = PredictionModel()
                self.model.model = joblib.load(model_path)
                self.logger.info(f"Modèle chargé depuis {model_path}")
            except Exception as e:
                self.logger.error(f"Erreur lors du chargement du modèle: {e}")
                self.model = None
        else:
            self.logger.warning(f"Fichier de modèle {model_path} non trouvé")
            self.model = None
    
    def predict_upcoming_races(self, days_ahead=1, output_dir='predictions'):
        """Prédit les résultats pour toutes les courses à venir dans les prochains jours."""
        if self.model is None or self.model.model is None:
            self.logger.error("Aucun modèle disponible pour les prédictions")
            return None
        
        self.logger.info(f"Prédiction des courses pour les {days_ahead} prochains jours")
        
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
                prediction_data = self.data_prep.prepare_data_for_prediction(course_id=race_id)
                
                if prediction_data is None or prediction_data.empty:
                    self.logger.warning(f"Pas de données disponibles pour la course {race_id}")
                    continue
                
                # Faire la prédiction
                results = self.model.predict_ranking(prediction_data, race_id)
                
                if results is None:
                    self.logger.warning(f"Échec de la prédiction pour la course {race_id}")
                    continue
                
                # Ajouter des informations sur la course
                results['course_id'] = race_id
                results['reunion_num'] = race['numReunion'] if 'numReunion' in race else None
                results['course_num'] = race['numOrdre'] if 'numOrdre' in race else None
                results['hippodrome'] = race['hippodrome_code'] if 'hippodrome_code' in race else None
                results['course_date'] = race['heureDepart'] if 'heureDepart' in race else None
                
                # Sauvegarder les prédictions
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_file = f"{output_dir}/prediction_{race_id}_{timestamp}.json"
                
                # Convertir le DataFrame en dictionnaire
                prediction_dict = {
                    'course_id': race_id,
                    'reunion_num': results['reunion_num'].iloc[0] if 'reunion_num' in results else None,
                    'course_num': results['course_num'].iloc[0] if 'course_num' in results else None,
                    'hippodrome': results['hippodrome'].iloc[0] if 'hippodrome' in results else None,
                    'course_date': str(results['course_date'].iloc[0]) if 'course_date' in results else None,
                    'predictions': results.drop(['course_id', 'reunion_num', 'course_num', 'hippodrome', 'course_date'], axis=1, errors='ignore').to_dict(orient='records'),
                    'timestamp': timestamp
                }
                
                # Sauvegarder au format JSON
                with open(output_file, 'w') as f:
                    json.dump(prediction_dict, f, indent=2)
                
                all_predictions.append(prediction_dict)
                self.logger.info(f"Prédiction pour la course {race_id} sauvegardée dans {output_file}")
                
            except Exception as e:
                self.logger.error(f"Erreur lors de la prédiction pour la course {race_id}: {str(e)}")
        
        self.logger.info(f"Traitement terminé. {len(all_predictions)} prédictions générées.")
        return all_predictions
    
    def parallel_predict_upcoming_races(self, days_ahead=1, output_dir='predictions', max_workers=4):
        """Version parallèle de predict_upcoming_races pour améliorer les performances."""
        if self.model is None or self.model.model is None:
            self.logger.error("Aucun modèle disponible pour les prédictions")
            return None
        
        self.logger.info(f"Prédiction parallèle des courses pour les {days_ahead} prochains jours")
        
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
        
        self.logger.info(f"Traitement parallèle de {len(upcoming_races)} courses à venir")
        
        # Fonction de traitement pour chaque course
        def process_race(race):
            race_id = race['id']
            try:
                # Préparer les données pour la prédiction
                data_prep = DataPreparation(self.db_path)
                prediction_data = data_prep.prepare_data_for_prediction(course_id=race_id)
                
                if prediction_data is None or prediction_data.empty:
                    return None
                
                # Faire la prédiction
                model = PredictionModel()
                model.model = joblib.load('model/trained_models/horse_race_model.pkl')
                results = model.predict_ranking(prediction_data, race_id)
                
                if results is None:
                    return None
                
                # Ajouter des informations sur la course
                results['course_id'] = race_id
                results['reunion_num'] = race['numReunion'] if 'numReunion' in race else None
                results['course_num'] = race['numOrdre'] if 'numOrdre' in race else None
                results['hippodrome'] = race['hippodrome_code'] if 'hippodrome_code' in race else None
                results['course_date'] = race['heureDepart'] if 'heureDepart' in race else None
                
                # Convertir le DataFrame en dictionnaire
                prediction_dict = {
                    'course_id': race_id,
                    'reunion_num': results['reunion_num'].iloc[0] if 'reunion_num' in results else None,
                    'course_num': results['course_num'].iloc[0] if 'course_num' in results else None,
                    'hippodrome': results['hippodrome'].iloc[0] if 'hippodrome' in results else None,
                    'course_date': str(results['course_date'].iloc[0]) if 'course_date' in results else None,
                    'predictions': results.drop(['course_id', 'reunion_num', 'course_num', 'hippodrome', 'course_date'], axis=1, errors='ignore').to_dict(orient='records'),
                    'timestamp': datetime.now().strftime('%Y%m%d_%H%M%S')
                }
                
                return prediction_dict
            except Exception as e:
                self.logger.error(f"Erreur lors de la prédiction pour la course {race_id}: {str(e)}")
                return None
        
        # Stocker les résultats
        all_predictions = []
        
        # Utiliser ProcessPoolExecutor pour le traitement parallèle
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            # Soumettre les tâches
            future_to_race = {executor.submit(process_race, race): race['id'] for _, race in upcoming_races.iterrows()}
            
            # Traiter les résultats au fur et à mesure qu'ils sont disponibles
            for future in as_completed(future_to_race):
                race_id = future_to_race[future]
                try:
                    prediction_dict = future.result()
                    if prediction_dict:
                        # Sauvegarder au format JSON
                        output_file = f"{output_dir}/prediction_{race_id}_{prediction_dict['timestamp']}.json"
                        with open(output_file, 'w') as f:
                            json.dump(prediction_dict, f, indent=2)
                        
                        all_predictions.append(prediction_dict)
                        self.logger.info(f"Prédiction pour la course {race_id} sauvegardée dans {output_file}")
                except Exception as e:
                    self.logger.error(f"Erreur lors du traitement du résultat pour la course {race_id}: {str(e)}")
        
        self.logger.info(f"Traitement parallèle terminé. {len(all_predictions)} prédictions générées.")
        return all_predictions
    
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
        completed_races = completed_races[completed_races['statut'].str.contains('ARRIVEE', na=False)]
        
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
                prediction_df = pd.DataFrame(prediction['predictions'])
                
                # Fusionner avec les résultats réels
                merged_df = pd.merge(
                    prediction_df,
                    participants[['numPmu', 'ordreArrivee', 'nom']],
                    on=['numPmu', 'nom'],
                    how='left'
                )
                
                # Calculer les métriques d'évaluation
                metrics = {
                    'course_id': race_id,
                    'reunion_num': race['numReunion'] if 'numReunion' in race else None,
                    'course_num': race['numOrdre'] if 'numOrdre' in race else None,
                    'hippodrome': race['hippodrome_code'] if 'hippodrome_code' in race else None,
                    'course_date': str(race['heureDepart']) if 'heureDepart' in race else None
                }
                
                # Est-ce que le cheval avec la plus haute probabilité a gagné?
                if 'win_probability' in merged_df.columns and 'ordreArrivee' in merged_df.columns:
                    winner_pred = merged_df.sort_values('win_probability', ascending=False).iloc[0]
                    winner_real = merged_df[merged_df['ordreArrivee'] == 1].iloc[0] if len(merged_df[merged_df['ordreArrivee'] == 1]) > 0 else None
                    
                    metrics['predicted_winner'] = winner_pred['nom']
                    metrics['predicted_winner_odds'] = winner_pred['win_probability']
                    metrics['actual_winner'] = winner_real['nom'] if winner_real is not None else 'Unknown'
                    metrics['winner_correctly_predicted'] = winner_pred['nom'] == metrics['actual_winner']
                
                # Top-N Accuracy
                for n in [2, 3, 5]:
                    if 'predicted_rank' in merged_df.columns and 'ordreArrivee' in merged_df.columns:
                        top_n_pred = set(merged_df.sort_values('predicted_rank').head(n)['numPmu'].tolist())
                        top_n_actual = set(merged_df.sort_values('ordreArrivee').head(n)['numPmu'].tolist())
                        
                        intersection = len(top_n_pred.intersection(top_n_actual))
                        accuracy = intersection / min(n, len(top_n_actual)) if len(top_n_actual) > 0 else 0
                        
                        metrics[f'top_{n}_accuracy'] = accuracy
                
                # Spearman's rank correlation
                if 'predicted_rank' in merged_df.columns and 'ordreArrivee' in merged_df.columns:
                    # Enlever les lignes avec des valeurs manquantes
                    valid_df = merged_df.dropna(subset=['predicted_rank', 'ordreArrivee'])
                    
                    if len(valid_df) >= 3:  # Besoin d'au moins 3 points pour une corrélation significative
                        from scipy.stats import spearmanr
                        correlation, p_value = spearmanr(valid_df['predicted_rank'], valid_df['ordreArrivee'])
                        
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
    
    def batch_train_test(self, days_back=30, test_days=7, model_type='xgboost', output_dir='model/trained_models'):
        """Entraîne un modèle sur les données historiques et le teste sur les données plus récentes."""
        self.logger.info(f"Entraînement et test par lots sur les données des {days_back} derniers jours")
        
        # Créer le répertoire de sortie si nécessaire
        os.makedirs(output_dir, exist_ok=True)
        
        # Définir la période d'entraînement et de test
        now = datetime.now()
        train_end = now - timedelta(days=test_days)
        train_start = train_end - timedelta(days=days_back - test_days)
        test_start = train_end
        test_end = now
        
        self.logger.info(f"Période d'entraînement: {train_start.strftime('%Y-%m-%d')} à {train_end.strftime('%Y-%m-%d')}")
        self.logger.info(f"Période de test: {test_start.strftime('%Y-%m-%d')} à {test_end.strftime('%Y-%m-%d')}")
        
        # Récupérer les courses terminées pour l'entraînement
        train_races = self.data_prep.get_course_data(
            start_date=train_start.strftime("%Y-%m-%d"),
            end_date=train_end.strftime("%Y-%m-%d")
        )
        
        if train_races.empty:
            self.logger.error(f"Aucune course trouvée pour la période d'entraînement")
            return None
        
        # Filtrer les courses terminées avec résultats
        train_races = train_races[train_races['statut'].str.contains('ARRIVEE', na=False)]
        
        if train_races.empty:
            self.logger.error(f"Aucune course terminée trouvée pour la période d'entraînement")
            return None
        
        self.logger.info(f"Entraînement sur {len(train_races)} courses")
        
        # Récupérer les participants pour les courses d'entraînement
        train_participants = []
        
        for idx, race in train_races.iterrows():
            race_id = race['id']
            participants = self.data_prep.get_participant_data(course_id=race_id)
            
            if participants is not None and not participants.empty:
                # Ajouter des informations de course
                for col in race.index:
                    if col not in participants.columns:
                        participants[col] = race[col]
                
                train_participants.append(participants)
        
        if not train_participants:
            self.logger.error(f"Aucun participant trouvé pour les courses d'entraînement")
            return None
        
        # Concaténer tous les participants
        train_data = pd.concat(train_participants, ignore_index=True)
        
        # Initialiser le modèle
        model = PredictionModel(model_type=model_type)
        model.initialize_model()
        
        # Créer la variable cible
        train_data = model.create_target_variable(train_data, type_target='place')
        
        # Améliorer les features
        train_data = model.enhance_features(train_data)
        
        # Entraîner le modèle
        self.logger.info(f"Entraînement du modèle {model_type} avec {len(train_data)} échantillons")
        model.train(train_data, target_col='target', group_col='course_id')
        
        # Récupérer les courses terminées pour le test
        test_races = self.data_prep.get_course_data(
            start_date=test_start.strftime("%Y-%m-%d"),
            end_date=test_end.strftime("%Y-%m-%d")
        )
        
        if test_races.empty:
            self.logger.warning(f"Aucune course trouvée pour la période de test")
            
            # Sauvegarder le modèle malgré tout
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            model_path = f"{output_dir}/{model_type}_model_{timestamp}.pkl"
            model.save_model(model_path)
            
            self.logger.info(f"Modèle sauvegardé dans {model_path}")
            
            return {
                'model_path': model_path,
                'training_samples': len(train_data),
                'test_results': None
            }
        
        # Filtrer les courses terminées avec résultats
        test_races = test_races[test_races['statut'].str.contains('ARRIVEE', na=False)]
        
        if test_races.empty:
            self.logger.warning(f"Aucune course terminée trouvée pour la période de test")
            
            # Sauvegarder le modèle malgré tout
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            model_path = f"{output_dir}/{model_type}_model_{timestamp}.pkl"
            model.save_model(model_path)
            
            self.logger.info(f"Modèle sauvegardé dans {model_path}")
            
            return {
                'model_path': model_path,
                'training_samples': len(train_data),
                'test_results': None
            }
        
        self.logger.info(f"Test sur {len(test_races)} courses")
        
        # Évaluer le modèle sur les données de test
        test_results = []
        
        for idx, race in test_races.iterrows():
            race_id = race['id']
            
            try:
                # Préparer les données pour la prédiction
                prediction_data = self.data_prep.prepare_data_for_prediction(course_id=race_id)
                
                if prediction_data is None or prediction_data.empty:
                    self.logger.warning(f"Pas de données disponibles pour la course {race_id}")
                    continue
                
                # Faire la prédiction
                results = model.predict_ranking(prediction_data, race_id)
                
                if results is None:
                    self.logger.warning(f"Échec de la prédiction pour la course {race_id}")
                    continue
                
                # Récupérer les résultats réels
                participants = self.data_prep.get_participant_data(course_id=race_id)
                
                # Fusionner avec les résultats réels
                merged_df = pd.merge(
                    results,
                    participants[['numPmu', 'ordreArrivee', 'nom']],
                    on=['numPmu', 'nom'],
                    how='left'
                )
                
                # Calculer les métriques d'évaluation
                metrics = {
                    'course_id': race_id,
                    'reunion_num': race['numReunion'] if 'numReunion' in race else None,
                    'course_num': race['numOrdre'] if 'numOrdre' in race else None,
                    'hippodrome': race['hippodrome_code'] if 'hippodrome_code' in race else None,
                    'course_date': str(race['heureDepart']) if 'heureDepart' in race else None
                }
                
                # Est-ce que le cheval avec la plus haute probabilité a gagné?
                if 'win_probability' in merged_df.columns and 'ordreArrivee' in merged_df.columns:
                    winner_pred = merged_df.sort_values('win_probability', ascending=False).iloc[0]
                    winner_real = merged_df[merged_df['ordreArrivee'] == 1].iloc[0] if len(merged_df[merged_df['ordreArrivee'] == 1]) > 0 else None
                    
                    metrics['predicted_winner'] = winner_pred['nom']
                    metrics['predicted_winner_odds'] = winner_pred['win_probability']
                    metrics['actual_winner'] = winner_real['nom'] if winner_real is not None else 'Unknown'
                    metrics['winner_correctly_predicted'] = winner_pred['nom'] == metrics['actual_winner']
                
                # Top-N Accuracy
                for n in [2, 3, 5]:
                    if 'predicted_rank' in merged_df.columns and 'ordreArrivee' in merged_df.columns:
                        top_n_pred = set(merged_df.sort_values('predicted_rank').head(n)['numPmu'].tolist())
                        top_n_actual = set(merged_df.sort_values('ordreArrivee').head(n)['numPmu'].tolist())
                        
                        intersection = len(top_n_pred.intersection(top_n_actual))
                        accuracy = intersection / min(n, len(top_n_actual)) if len(top_n_actual) > 0 else 0
                        
                        metrics[f'top_{n}_accuracy'] = accuracy
                
                # Spearman's rank correlation
                if 'predicted_rank' in merged_df.columns and 'ordreArrivee' in merged_df.columns:
                    # Enlever les lignes avec des valeurs manquantes
                    valid_df = merged_df.dropna(subset=['predicted_rank', 'ordreArrivee'])
                    
                    if len(valid_df) >= 3:  # Besoin d'au moins 3 points pour une corrélation significative
                        from scipy.stats import spearmanr
                        correlation, p_value = spearmanr(valid_df['predicted_rank'], valid_df['ordreArrivee'])
                        
                        metrics['rank_correlation'] = correlation
                        metrics['rank_correlation_p_value'] = p_value
                
                test_results.append(metrics)
                
            except Exception as e:
                self.logger.error(f"Erreur lors de l'évaluation pour la course {race_id}: {str(e)}")
        
        # Agréger les résultats de test
        if test_results:
            test_df = pd.DataFrame(test_results)
            
            # Calculer les moyennes
            summary = {
                'total_races_evaluated': len(test_df),
                'winner_prediction_accuracy': test_df['winner_correctly_predicted'].mean() if 'winner_correctly_predicted' in test_df.columns else None,
                'avg_top_2_accuracy': test_df['top_2_accuracy'].mean() if 'top_2_accuracy' in test_df.columns else None,
                'avg_top_3_accuracy': test_df['top_3_accuracy'].mean() if 'top_3_accuracy' in test_df.columns else None,
                'avg_top_5_accuracy': test_df['top_5_accuracy'].mean() if 'top_5_accuracy' in test_df.columns else None,
                'avg_rank_correlation': test_df['rank_correlation'].mean() if 'rank_correlation' in test_df.columns else None
            }
            
            self.logger.info(f"Résultats du test: {summary}")
        else:
            summary = None
            self.logger.warning("Aucun résultat de test disponible")
        
        # Sauvegarder le modèle
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        model_path = f"{output_dir}/{model_type}_model_{timestamp}.pkl"
        model.save_model(model_path)
        
        self.logger.info(f"Modèle sauvegardé dans {model_path}")
        
        # Sauvegarder également une copie comme "latest" pour un accès facile
        latest_path = f"{output_dir}/{model_type}_model_latest.pkl"
        model.save_model(latest_path)
        
        # Sauvegarder le résumé du test
        if summary:
            summary_file = f"{output_dir}/{model_type}_test_summary_{timestamp}.json"
            
            with open(summary_file, 'w') as f:
                json.dump(summary, f, indent=2)
            
            self.logger.info(f"Résumé du test sauvegardé dans {summary_file}")
        
        return {
            'model_path': model_path,
            'training_samples': len(train_data),
            'test_results': summary
        }