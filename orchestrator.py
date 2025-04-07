#!/usr/bin/env python
import argparse
import logging
from logging.config import fileConfig
import os
import json
from datetime import datetime, timedelta
import schedule
import time

# Import des modules mis à jour
from data_preparation.enhanced_data_prep import EnhancedDataPreparation
from model.dual_prediction_model import DualPredictionModel
from analysis.historical_analysis import HistoricalAnalysis
from model.model_evaluation import ModelEvaluation
from batch_processing.batch_processor import BatchProcessor

# Configuration du logging
fileConfig('logger/logging_config.ini')
logger = logging.getLogger(__name__)

class PMUOrchestrateur:
    """Orchestrateur pour le système de prédiction de courses PMU."""
    
    def __init__(self, config_path='config/config.json'):
        """Initialise l'orchestrateur avec la configuration."""
        self.logger = logging.getLogger(__name__)
        
        # Charger la configuration
        self.config = self._load_config(config_path)
        
        # Initialiser les composants avec les nouvelles classes
        self.data_prep = EnhancedDataPreparation(self.config.get('db_path', 'pmu_ia'))
        
        # Initialiser le modèle double
        self.model = DualPredictionModel(base_path=self.config.get('model_path', 'model/trained_models'))
        
        # Initialiser le batch processor
        self.batch_processor = BatchProcessor(
            data_prep=self.data_prep,
            model=self.model,
            db_path=self.config.get('db_path', 'pmu_ia'),
            model_path=self.config.get('model_path', 'model/trained_models')
        )
    
    def _load_config(self, config_path):
        """Charge la configuration depuis un fichier JSON."""
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                self.logger.info(f"Configuration chargée depuis {config_path}")
                return config
            else:
                self.logger.warning(f"Fichier de configuration {config_path} non trouvé. Utilisation des valeurs par défaut.")
                return self._create_default_config(config_path)
        except Exception as e:
            self.logger.error(f"Erreur lors du chargement de la configuration: {str(e)}")
            return self._create_default_config(config_path)
    
    def _create_default_config(self, config_path):
        """Crée une configuration par défaut avec support pour les deux modèles."""
        config = {
            'db_path': 'pmu_ia',  # Base de données MySQL
            'model_path': 'model/trained_models',
            'scraping': {
                'days_back': 7,
                'schedule': {
                    'time': '00:00',  # Minuit
                    'frequency': 'daily'
                }
            },
            'prediction': {
                'days_ahead': 1,
                'schedule': {
                    'time': '07:00',  # 7h du matin
                    'frequency': 'daily'
                }
            },
            'evaluation': {
                'days_back': 30,
                'schedule': {
                    'time': '23:00',  # 23h du soir
                    'frequency': 'weekly',
                    'day': 'sunday'
                }
            },
            'training': {
                'days_back': 300,
                'test_days': 65,
                'standard_model_type': 'xgboost',  # Type du modèle standard
                'simulation_model_type': 'xgboost_ranking',  # Type du modèle de simulation
                'schedule': {
                    'time': '01:00',  # 1h du matin
                    'frequency': 'monthly',
                    'day': 1
                }
            }
        }
        
        # Créer le répertoire si nécessaire
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        # Sauvegarder la configuration
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        self.logger.info(f"Configuration par défaut créée et sauvegardée dans {config_path}")
        return config
    
    def run_scraping(self):
        """Exécute le scraping des données PMU."""
        self.logger.info("Démarrage du scraping des données PMU")
        
        try:
            days_back = self.config.get('scraping', {}).get('days_back', 7)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            self.logger.info(f"Scraping des données du {start_date.strftime('%Y-%m-%d')} au {end_date.strftime('%Y-%m-%d')}")
            
            # Importer ici pour éviter les dépendances circulaires
            from scrapping.scrapping import call_api_between_dates
            call_api_between_dates(start_date, end_date)
            
            self.logger.info("Scraping des données terminé avec succès")
        except Exception as e:
            self.logger.error(f"Erreur lors du scraping des données: {str(e)}")
    
    def run_predictions(self):
        """Exécute les prédictions pour les courses à venir avec le modèle standard."""
        self.logger.info("Démarrage des prédictions pour les courses à venir")
        
        try:
            days_ahead = self.config.get('prediction', {}).get('days_ahead', 1)
            
            self.logger.info(f"Prédiction des courses pour les {days_ahead} prochains jours")
            
            # Utiliser le nouveau batch processor avec le modèle standard
            predictions = self.batch_processor.predict_upcoming_races_standard(days_ahead=days_ahead)
            
            if predictions:
                self.logger.info(f"Prédictions générées pour {len(predictions)} courses")
            else:
                self.logger.warning("Aucune prédiction générée")
                
        except Exception as e:
            self.logger.error(f"Erreur lors des prédictions: {str(e)}")
    
    def run_evaluation(self):
        """Évalue les prédictions passées."""
        self.logger.info("Démarrage de l'évaluation des prédictions passées")
        
        try:
            days_back = self.config.get('evaluation', {}).get('days_back', 30)
            
            self.logger.info(f"Évaluation des prédictions des {days_back} derniers jours")
            
            summary = self.batch_processor.evaluate_past_predictions(days_back=days_back)
            
            if summary:
                self.logger.info(f"Résultats de l'évaluation: {summary}")
            else:
                self.logger.warning("Aucun résultat d'évaluation disponible")
                
        except Exception as e:
            self.logger.error(f"Erreur lors de l'évaluation: {str(e)}")
    
    def run_training(self):
        """Entraîne les deux modèles (standard et simulation) sur les données historiques."""
        self.logger.info("Démarrage de l'entraînement des modèles")
        
        try:
            # Récupérer les valeurs depuis la configuration
            days_back = self.config.get('training', {}).get('days_back', 300)
            test_days = self.config.get('training', {}).get('test_days', 60)
            standard_model_type = self.config.get('training', {}).get('standard_model_type', 'xgboost')
            simulation_model_type = self.config.get('training', {}).get('simulation_model_type', 'xgboost_ranking')
            
            self.logger.info(f"Entraînement des modèles sur les données des {days_back} derniers jours")
            
            # Entraîner les deux modèles - Passez les arguments correctement
            result = self.batch_processor.train_dual_models(
                days_back=days_back,  # Utilisez la valeur numérique depuis la config
                test_days=test_days,
                standard_model_type=standard_model_type,
                simulation_model_type=simulation_model_type
            )
            
            if result:
                self.logger.info(f"Modèles entraînés avec succès:")
                self.logger.info(f"Modèle standard ({standard_model_type}): {result['standard_model_path']}")
                self.logger.info(f"Précision: {result['standard_accuracy']:.4f}")
                self.logger.info(f"Modèle de simulation ({simulation_model_type}): {result['simulation_model_path']}")
                
                # Mettre à jour les chemins des modèles dans la configuration
                self.config['standard_model_path'] = result['standard_model_path']
                self.config['simulation_model_path'] = result['simulation_model_path']
                
                with open('config/config.json', 'w') as f:
                    json.dump(self.config, f, indent=2)
                
                self.logger.info("Configuration mise à jour avec les nouveaux modèles")
            else:
                self.logger.warning("Échec de l'entraînement des modèles")
                    
        except Exception as e:
            self.logger.error(f"Erreur lors de l'entraînement: {str(e)}")
    
    def run_simulation(self, course_id, selected_horses, simulation_params=None):
        """Exécute une simulation personnalisée pour une course."""
        self.logger.info(f"Démarrage de la simulation pour la course {course_id}")
        
        try:
            # Vérifier si le modèle de simulation est chargé
            if not hasattr(self.model, 'simulation_model') or self.model.simulation_model is None:
                self.logger.warning("Modèle de simulation non chargé. Tentative de chargement...")
                simulation_model_path = self.config.get('simulation_model_path')
                if simulation_model_path and os.path.exists(simulation_model_path):
                    self.model.load_simulation_model(simulation_model_path)
                else:
                    self.logger.error("Impossible de charger le modèle de simulation")
                    return None
            
            # Exécuter la simulation
            results = self.batch_processor.simulate_race(
                course_id=course_id,
                selected_horses=selected_horses,
                simulation_params=simulation_params
            )
            
            if results is not None:
                self.logger.info(f"Simulation réussie pour la course {course_id}")
                return results
            else:
                self.logger.warning(f"Échec de la simulation pour la course {course_id}")
                return None
                
        except Exception as e:
            self.logger.error(f"Erreur lors de la simulation: {str(e)}")
            return None
    
    def schedule_jobs(self):
        """Planifie les tâches selon la configuration."""
        self.logger.info("Planification des tâches récurrentes")
        
        # Scraping
        scraping_config = self.config.get('scraping', {}).get('schedule', {})
        scraping_time = scraping_config.get('time', '00:00')
        scraping_frequency = scraping_config.get('frequency', 'daily')
        
        if scraping_frequency == 'daily':
            schedule.every().day.at(scraping_time).do(self.run_scraping)
            self.logger.info(f"Scraping planifié tous les jours à {scraping_time}")
        elif scraping_frequency == 'weekly':
            day = scraping_config.get('day', 'monday').lower()
            getattr(schedule.every(), day).at(scraping_time).do(self.run_scraping)
            self.logger.info(f"Scraping planifié tous les {day} à {scraping_time}")
        
        # Prédictions
        prediction_config = self.config.get('prediction', {}).get('schedule', {})
        prediction_time = prediction_config.get('time', '07:00')
        prediction_frequency = prediction_config.get('frequency', 'daily')
        
        if prediction_frequency == 'daily':
            schedule.every().day.at(prediction_time).do(self.run_predictions)
            self.logger.info(f"Prédictions planifiées tous les jours à {prediction_time}")
        elif prediction_frequency == 'weekly':
            day = prediction_config.get('day', 'monday').lower()
            getattr(schedule.every(), day).at(prediction_time).do(self.run_predictions)
            self.logger.info(f"Prédictions planifiées tous les {day} à {prediction_time}")
        
        # Évaluation
        evaluation_config = self.config.get('evaluation', {}).get('schedule', {})
        evaluation_time = evaluation_config.get('time', '23:00')
        evaluation_frequency = evaluation_config.get('frequency', 'weekly')
        
        if evaluation_frequency == 'daily':
            schedule.every().day.at(evaluation_time).do(self.run_evaluation)
            self.logger.info(f"Évaluation planifiée tous les jours à {evaluation_time}")
        elif evaluation_frequency == 'weekly':
            day = evaluation_config.get('day', 'sunday').lower()
            getattr(schedule.every(), day).at(evaluation_time).do(self.run_evaluation)
            self.logger.info(f"Évaluation planifiée tous les {day} à {evaluation_time}")
        
        # Entraînement
        training_config = self.config.get('training', {}).get('schedule', {})
        training_time = training_config.get('time', '01:00')
        training_frequency = training_config.get('frequency', 'monthly')
        
        if training_frequency == 'daily':
            schedule.every().day.at(training_time).do(self.run_training)
            self.logger.info(f"Entraînement planifié tous les jours à {training_time}")
        elif training_frequency == 'weekly':
            day = training_config.get('day', 'monday').lower()
            getattr(schedule.every(), day).at(training_time).do(self.run_training)
            self.logger.info(f"Entraînement planifié tous les {day} à {training_time}")
        elif training_frequency == 'monthly':
            day = training_config.get('day', 1)
            # Pour les tâches mensuelles, il faut vérifier la date à chaque exécution
            def monthly_training_check():
                if datetime.now().day == day:
                    self.run_training()
            
            # Exécuter la vérification tous les jours à l'heure spécifiée
            schedule.every().day.at(training_time).do(monthly_training_check)
            self.logger.info(f"Entraînement planifié le {day} de chaque mois à {training_time}")
        
        self.logger.info("Toutes les tâches ont été planifiées")
    
    def run_scheduler(self):
        """Lance le planificateur de tâches."""
        self.logger.info("Démarrage du planificateur de tâches")
        
        # Planifier les tâches
        self.schedule_jobs()
        
        # Boucle principale du planificateur
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Vérifier toutes les minutes
        except KeyboardInterrupt:
            self.logger.info("Arrêt du planificateur de tâches")
    
    def run_all(self):
        """Exécute toutes les tâches principales en séquence."""
        self.logger.info("Exécution de toutes les tâches principales")
        
        # 1. Scraping
        self.run_scraping()
        
        # 2. Entraînement (si nécessaire)
        standard_model_path = self.config.get('standard_model_path')
        simulation_model_path = self.config.get('simulation_model_path')
        
        if (not standard_model_path or not os.path.exists(standard_model_path) or 
            not simulation_model_path or not os.path.exists(simulation_model_path)):
            self.logger.info("Modèles non trouvés. Entraînement de nouveaux modèles.")
            self.run_training()
        
        # 3. Prédictions
        self.run_predictions()
        
        # 4. Évaluation
        self.run_evaluation()

    def train_models(days_back=360, test_size=0.2, standard_model_type='xgboost', simulation_model_type='xgboost_ranking'):
        """Entraîne les deux modèles avec les données des derniers jours"""
        logger = logging.getLogger(__name__)
        logger.info(f"Starting model training with {days_back} days of data")
        
        # Préparer les données
        data_prep = EnhancedDataPreparation()
        
        # Définir la période d'entraînement
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back) if days_back else None
        
        if start_date:
            logger.info(f"Getting training data from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        else:
            logger.info(f"Getting all available training data up to {end_date.strftime('%Y-%m-%d')}")
        
        # Récupérer les données
        start_date_str = start_date.strftime("%Y-%m-%d") if start_date else None
        training_data = data_prep.get_training_data(
            start_date=start_date_str,
            end_date=end_date.strftime("%Y-%m-%d")
        )
        
        if training_data.empty:
            logger.error("No training data found")
            return False
        
        # CORRECTION : S'assurer que l'index est réinitialisé dès le départ
        training_data = training_data.reset_index(drop=True)
        
        logger.info(f"Retrieved {len(training_data)} samples for training")
        
        # Créer des features avancées
        enhanced_data = data_prep.create_advanced_features(training_data)
        enhanced_data = enhanced_data.reset_index(drop=True)
        
        # Encoder pour le modèle
        prepared_data = data_prep.encode_features_for_model(enhanced_data, is_training=True)
        prepared_data = prepared_data.reset_index(drop=True)
        
        # Initialiser les modèles
        model = DualPredictionModel()
        
        # Entraîner le modèle standard
        logger.info(f"Training standard model with {standard_model_type}")
        standard_accuracy, standard_path = model.train_standard_model(prepared_data, test_size=test_size)
        
        # Entraîner le modèle de simulation
        logger.info(f"Training simulation model with {simulation_model_type}")
        simulation_metrics, simulation_path = model.train_simulation_model(prepared_data, test_size=test_size)
        
        logger.info("Model training completed")
        logger.info(f"Standard model accuracy: {standard_accuracy:.4f}")
        logger.info(f"Simulation model metrics: {simulation_metrics}")
        
        return {
            'standard_model': {
                'accuracy': standard_accuracy,
                'path': standard_path
            },
            'simulation_model': {
                'metrics': simulation_metrics,
                'path': simulation_path
            }
        }
        
def parse_args():
    """Parse les arguments de ligne de commande."""
    parser = argparse.ArgumentParser(description='Orchestrateur du système de prédiction PMU')
    
    parser.add_argument('--config', type=str, default='config/config.json',
                        help='Chemin vers le fichier de configuration')
    
    parser.add_argument('--action', type=str, 
                        choices=['all', 'scrape', 'predict', 'evaluate', 'train', 'schedule', 'simulate'],
                        default='all', help='Action à exécuter')
    
    # Arguments pour les actions spécifiques
    parser.add_argument('--days-back', type=int,
                        help='Nombre de jours en arrière pour le scraping ou l\'évaluation')
    
    parser.add_argument('--days-ahead', type=int,
                        help='Nombre de jours en avant pour les prédictions')
    
    # Arguments pour la simulation
    parser.add_argument('--course-id', type=int,
                        help='ID de la course à simuler')
    
    parser.add_argument('--horses', type=str,
                        help='Liste des IDs de chevaux séparés par des virgules')
    
    parser.add_argument('--jockey-id', type=int,
                        help='ID du jockey pour la simulation')
    
    parser.add_argument('--weight', type=int,
                        help='Poids pour la simulation')
    
    parser.add_argument('--meteo', type=str, choices=['Ensoleillé', 'Nuageux', 'Pluie', 'Brouillard'],
                        help='Condition météo pour la simulation')
    
    return parser.parse_args()

def main():
    """Fonction principale."""
    args = parse_args()
    
    # Initialiser l'orchestrateur
    orchestrateur = PMUOrchestrateur(config_path=args.config)
    
    # Exécuter l'action demandée
    if args.action == 'all':
        orchestrateur.run_all()
    
    elif args.action == 'scrape':
        if args.days_back:
            orchestrateur.config['scraping']['days_back'] = args.days_back
        orchestrateur.run_scraping()
    
    elif args.action == 'predict':
        if args.days_ahead:
            orchestrateur.config['prediction']['days_ahead'] = args.days_ahead
        orchestrateur.run_predictions()
    
    elif args.action == 'evaluate':
        if args.days_back:
            orchestrateur.config['evaluation']['days_back'] = args.days_back
        orchestrateur.run_evaluation()
    
    elif args.action == 'train':
        if args.days_back:
            orchestrateur.config['training']['days_back'] = args.days_back
        orchestrateur.run_training()
    
    elif args.action == 'schedule':
        orchestrateur.run_scheduler()
        
    elif args.action == 'simulate':
        # Vérifier les arguments requis
        if not args.course_id:
            print("Erreur: l'argument --course-id est requis pour la simulation")
            return
        
        if not args.horses:
            print("Erreur: l'argument --horses est requis pour la simulation")
            return
        
        # Convertir la liste de chevaux en liste d'entiers
        selected_horses = [int(horse) for horse in args.horses.split(',')]
        
        # Construire les paramètres de simulation
        simulation_params = {}
        
        if args.jockey_id:
            simulation_params['jockey_id'] = args.jockey_id
        
        if args.weight:
            simulation_params['poids'] = args.weight
            
        if args.meteo:
            simulation_params['meteo'] = args.meteo
        
        # Exécuter la simulation
        results = orchestrateur.run_simulation(
            course_id=args.course_id,
            selected_horses=selected_horses,
            simulation_params=simulation_params
        )
        
        if results is not None:
            print(f"Résultats de la simulation pour la course {args.course_id}:")
            print(f"Classement simulé:")
            for i, row in results.iterrows():
                print(f"{i+1}. {row['cheval_nom']} - Score: {row['predicted_score']:.4f}")
        else:
            print("La simulation a échoué. Consultez les logs pour plus de détails.")

if __name__ == '__main__':
    main()