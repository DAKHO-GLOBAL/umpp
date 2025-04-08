#!/usr/bin/env python
import argparse
import logging
from logging.config import fileConfig
import os
import json
from datetime import datetime, timedelta
import pandas as pd
import schedule
import time

# Import des modules mis à jour
from data_preparation.enhanced_data_prep import EnhancedDataPreparation
from model.dual_prediction_model import DualPredictionModel
from analysis.historical_analysis import HistoricalAnalysis
from model.model_evaluation import ModelEvaluation
from batch_processing.batch_processor import BatchProcessor

class PMUOrchestrateur:
    """
    Orchestrateur amélioré pour le système de prédiction PMU,
    optimisé pour les paris de type Top 7 (Quinté).
    """
    
    def __init__(self, config_path='config/config.json'):
        """Initialise l'orchestrateur avec la configuration."""
        self.logger = logging.getLogger(__name__)
        
        # Charger la configuration
        self.config = self._load_config(config_path)
        
        # Initialiser la préparation des données avec fonctionnalités améliorées
        self.data_prep = EnhancedDataPreparation(self.config.get('db_path', 'pmu_ia'))
        
        # Charger les encodeurs si disponibles
        self.data_prep.load_encoders()
        
        # Initialiser le modèle dual avec support pour le Top 7
        self.model = DualPredictionModel(base_path=self.config.get('model_path', 'model/trained_models'))
        
        # Charger les modèles existants
        self._load_models()
    
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
        """Crée une configuration par défaut avec support pour le Top 7."""
        config = {
            'db_path': 'pmu_ia',
            'model_path': 'model/trained_models',
            'scraping': {
                'days_back': 7,
                'schedule': {
                    'time': '00:00',
                    'frequency': 'daily'
                }
            },
            'prediction': {
                'days_ahead': 1,
                'top_n_features': 30,
                'schedule': {
                    'time': '07:00',
                    'frequency': 'daily'
                }
            },
            'evaluation': {
                'days_back': 30,
                'include_top7': True,
                'schedule': {
                    'time': '23:00',
                    'frequency': 'weekly',
                    'day': 'sunday'
                }
            },
            'training': {
                'days_back': 180,
                'test_size': 0.2,
                'standard_model_type': 'xgboost',
                'simulation_model_type': 'xgboost_ranking',
                'top_n_features': 30,
                'schedule': {
                    'time': '01:00',
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
    
    def _load_models(self):
        """Charge les modèles existants."""
        # Chercher le modèle standard le plus récent
        standard_model_path = self.config.get('standard_model_path')
        if standard_model_path and os.path.exists(standard_model_path):
            self.model.load_standard_model(standard_model_path)
        else:
            # Chercher automatiquement le modèle standard le plus récent
            model_dir = self.config.get('model_path', 'model/trained_models')
            standard_models = [f for f in os.listdir(model_dir) if f.startswith('standard_') and f.endswith('.pkl')]
            if standard_models:
                latest_model = sorted(standard_models)[-1]
                self.model.load_standard_model(os.path.join(model_dir, latest_model))
                self.logger.info(f"Modèle standard chargé automatiquement: {latest_model}")
        
        # Chercher le modèle de simulation Top 7 le plus récent
        simulation_model_path = self.config.get('simulation_top7_model_path')
        if simulation_model_path and os.path.exists(simulation_model_path):
            self.model.load_simulation_model(simulation_model_path)
        else:
            # Chercher automatiquement le modèle de simulation Top 7 le plus récent
            model_dir = self.config.get('model_path', 'model/trained_models')
            simulation_models = [f for f in os.listdir(model_dir) if f.startswith('simulation_top7_') and f.endswith('.pkl')]
            if simulation_models:
                latest_model = sorted(simulation_models)[-1]
                self.model.load_simulation_model(os.path.join(model_dir, latest_model))
                self.logger.info(f"Modèle de simulation Top 7 chargé automatiquement: {latest_model}")
            else:
                # Essayer de charger un modèle de simulation standard
                simulation_models = [f for f in os.listdir(model_dir) if f.startswith('simulation_') and f.endswith('.pkl')]
                if simulation_models:
                    latest_model = sorted(simulation_models)[-1]
                    self.model.load_simulation_model(os.path.join(model_dir, latest_model))
                    self.logger.info(f"Modèle de simulation standard chargé: {latest_model}")
    
    def train_enhanced_models(self):
        """Entraîne les modèles avec les features améliorées."""
        self.logger.info("Démarrage de l'entraînement des modèles améliorés")
        
        # Récupérer les paramètres d'entraînement
        days_back = self.config.get('training', {}).get('days_back', 180)
        test_size = self.config.get('training', {}).get('test_size', 0.2)
        top_n_features = self.config.get('training', {}).get('top_n_features', 30)
        
        # Récupérer les données
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        self.logger.info(f"Récupération des données du {start_date.strftime('%Y-%m-%d')} au {end_date.strftime('%Y-%m-%d')}")
        
        # Obtenir les données d'entraînement
        training_data = self.data_prep.get_training_data(
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d')
        )
        
        if training_data.empty:
            self.logger.error("Aucune donnée d'entraînement trouvée")
            return None
        
        self.logger.info(f"Données récupérées: {len(training_data)} échantillons")
        
        # Créer des features avancées avec l'implémentation améliorée
        enhanced_data = self.data_prep.create_enhanced_features(training_data)
        
        # Créer les variables cibles
        prepared_data = self.model.create_target_variables(enhanced_data)
        
        # Entraîner le modèle standard amélioré
        self.logger.info(f"Entraînement du modèle standard amélioré")
        standard_metrics, standard_path = self.model.train_with_enhanced_features(
            prepared_data, 
            target_col='target_place',
            test_size=test_size,
            top_n_features=top_n_features
        )
        
        # Entraîner le modèle de simulation optimisé pour le Top 7
        self.logger.info(f"Entraînement du modèle de simulation optimisé pour le Top 7")
        simulation_metrics, simulation_path = self.model.train_top7_simulation_model(
            prepared_data,
            test_size=test_size,
            top_n_features=top_n_features
        )
        
        # Mettre à jour la configuration avec les nouveaux chemins de modèles
        self.config['standard_model_path'] = standard_path
        self.config['simulation_top7_model_path'] = simulation_path
        
        with open('config/config.json', 'w') as f:
            json.dump(self.config, f, indent=2)
        
        self.logger.info("Configuration mise à jour avec les nouveaux modèles")
        
        return {
            'standard_model': {
                'path': standard_path,
                'accuracy': standard_metrics
            },
            'simulation_model': {
                'path': simulation_path,
                'metrics': simulation_metrics
            }
        }
    
    def predict_course_top7(self, course_id):
        """
        Prédit les 7 premiers chevaux pour une course spécifique,
        optimisé pour les paris de type Quinté.
        """
        self.logger.info(f"Prédiction Top 7 pour la course {course_id}")
        
        # Vérifier si le modèle de simulation est chargé
        if self.model.simulation_model is None:
            self.logger.error("Modèle de simulation non chargé. Impossible de faire des prédictions Top 7.")
            return None
        
        # Préparer les données pour la prédiction
        try:
            # Récupérer les participants
            participants_data = self.data_prep.get_participant_data(course_id=course_id)
            
            if participants_data is None or participants_data.empty:
                self.logger.error(f"Pas de participants trouvés pour la course {course_id}")
                return None
            
            # Créer des features avancées
            enhanced_data = self.data_prep.create_enhanced_features(participants_data)
            
            # Faire la prédiction Top 7
            results = self.model.predict_top7(enhanced_data)
            
            if results is None:
                self.logger.error(f"Échec de la prédiction Top 7 pour la course {course_id}")
                return None
            
            # Sauvegarder les prédictions
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_dir = 'predictions'
            os.makedirs(output_dir, exist_ok=True)
            output_file = f"{output_dir}/prediction_top7_{course_id}_{timestamp}.json"
            
            # Convertir en format JSON
            prediction_dict = {
                'course_id': course_id,
                'date_prediction': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'predictions': results.to_dict(orient='records'),
                'model_type': 'simulation_top7'
            }
            
            # Sauvegarder au format JSON
            with open(output_file, 'w') as f:
                json.dump(prediction_dict, f, indent=2)
            
            self.logger.info(f"Prédiction Top 7 pour la course {course_id} sauvegardée dans {output_file}")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la prédiction Top 7 pour la course {course_id}: {str(e)}")
            return None
    
    def simulate_custom_top7(self, course_id, selected_horses=None, simulation_params=None):
        """
        Simule une course personnalisée avec prédiction des 7 premiers chevaux.
        
        Args:
            course_id: ID de la course
            selected_horses: Liste des IDs de chevaux sélectionnés (None = tous les chevaux)
            simulation_params: Paramètres personnalisés pour la simulation
        """
        self.logger.info(f"Simulation Top 7 personnalisée pour la course {course_id}")
        
        # Vérifier si le modèle de simulation est chargé
        if self.model.simulation_model is None:
            self.logger.error("Modèle de simulation non chargé. Impossible de faire des simulations.")
            return None
        
        try:
            # Récupérer les participants
            participants_data = self.data_prep.get_participant_data(course_id=course_id)
            
            if participants_data is None or participants_data.empty:
                self.logger.error(f"Pas de participants trouvés pour la course {course_id}")
                return None
            
            # Filtrer pour ne garder que les chevaux sélectionnés
            if selected_horses:
                participants_data = participants_data[participants_data['id_cheval'].isin(selected_horses)]
                
                if participants_data.empty:
                    self.logger.error(f"Aucun des chevaux sélectionnés n'est inscrit dans cette course")
                    return None
            
            # Modifier les paramètres de simulation si fournis
            if simulation_params:
                for param, value in simulation_params.items():
                    if param in participants_data.columns:
                        participants_data[param] = value
            
            # Créer des features avancées
            enhanced_data = self.data_prep.create_enhanced_features(participants_data)
            
            # Faire la simulation Top 7
            results = self.model.predict_top7(enhanced_data)
            
            if results is None:
                self.logger.error(f"Échec de la simulation Top 7 pour la course {course_id}")
                return None
            
            # Sauvegarder les résultats de simulation
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_dir = 'simulations'
            os.makedirs(output_dir, exist_ok=True)
            output_file = f"{output_dir}/simulation_top7_{course_id}_{timestamp}.json"
            
            # Convertir en format JSON
            simulation_dict = {
                'course_id': course_id,
                'date_simulation': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'selected_horses': selected_horses,
                'simulation_params': simulation_params,
                'results': results.to_dict(orient='records'),
                'model_type': 'simulation_top7'
            }
            
            # Sauvegarder au format JSON
            with open(output_file, 'w') as f:
                json.dump(simulation_dict, f, indent=2)
            
            self.logger.info(f"Simulation Top 7 pour la course {course_id} sauvegardée dans {output_file}")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la simulation Top 7 pour la course {course_id}: {str(e)}")
            return None
    
    def get_upcoming_races(self, days_ahead=1):
        """
        Récupère les courses à venir dans les prochains jours.
        """
        self.logger.info(f"Récupération des courses pour les {days_ahead} prochains jours")
        
        now = datetime.now()
        end_date = now + timedelta(days=days_ahead)
        
        # Récupérer les courses à venir
        query = f"""
        SELECT c.*, h.libelleLong AS hippodrome_nom 
        FROM courses c
        LEFT JOIN pmu_hippodromes h ON c.lieu = h.libelleLong
        WHERE c.date_heure BETWEEN '{now.strftime('%Y-%m-%d')}' AND '{end_date.strftime('%Y-%m-%d')}'
        ORDER BY c.date_heure ASC
        """
        
        try:
            upcoming_races = pd.read_sql_query(query, self.data_prep.engine)
            
            if upcoming_races.empty:
                self.logger.info(f"Aucune course trouvée pour les {days_ahead} prochains jours")
                return []
            
            self.logger.info(f"Trouvé {len(upcoming_races)} courses à venir")
            return upcoming_races
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération des courses à venir: {str(e)}")
            return []
    
    def batch_predict_top7(self, days_ahead=1):
        """
        Exécute des prédictions Top 7 par lot pour toutes les courses à venir.
        """
        self.logger.info(f"Prédiction par lot Top 7 pour les {days_ahead} prochains jours")
        
        # Récupérer les courses à venir
        upcoming_races = self.get_upcoming_races(days_ahead)
        
        if not len(upcoming_races):
            return []
        
        # Stocker les résultats
        all_predictions = []
        
        # Traiter chaque course
        for idx, race in upcoming_races.iterrows():
            race_id = race['id']
            self.logger.info(f"Traitement de la course {race_id} - {race['lieu'] if 'lieu' in race else 'Unknown'} ({idx+1}/{len(upcoming_races)})")
            
            # Faire la prédiction Top 7
            predictions = self.predict_course_top7(race_id)
            
            if predictions is not None:
                all_predictions.append({
                    'course_id': race_id,
                    'lieu': race['lieu'] if 'lieu' in race else 'Unknown',
                    'date_heure': str(race['date_heure']) if 'date_heure' in race else None,
                    'predictions': predictions.to_dict(orient='records')
                })
        
        self.logger.info(f"Prédictions par lot Top 7 terminées. {len(all_predictions)} prédictions générées.")
        return all_predictions
    
    def run_course_analysis(self, course_id):
        """
        Analyse détaillée d'une course spécifique avec tous les indicateurs disponibles.
        """
        self.logger.info(f"Analyse détaillée de la course {course_id}")
        
        try:
            # Récupérer les informations de la course
            course_query = f"""
            SELECT c.*, h.libelleLong AS hippodrome_nom,
                   pc.montantPrix, pc.categorieParticularite,
                   pc.corde, pc.categorieStatut
            FROM courses c
            LEFT JOIN pmu_hippodromes h ON c.lieu = h.libelleLong
            LEFT JOIN pmu_courses pc ON c.pmu_course_id = pc.id
            WHERE c.id = {course_id}
            """
            
            course_data = pd.read_sql_query(course_query, self.data_prep.engine)
            
            if course_data.empty:
                self.logger.error(f"Course {course_id} non trouvée")
                return None
            
            course_info = course_data.iloc[0].to_dict()
            
            # Récupérer les participants
            participants_data = self.data_prep.get_participant_data(course_id=course_id)
            
            if participants_data is None or participants_data.empty:
                self.logger.error(f"Pas de participants trouvés pour la course {course_id}")
                return None
            
            # Créer des features avancées
            enhanced_data = self.data_prep.create_enhanced_features(participants_data)
            
            # Faire la prédiction Top 7
            top7_predictions = self.model.predict_top7(enhanced_data)
            
            # Faire la prédiction standard (Top 3)
            top3_predictions = None
            if self.model.standard_model is not None:
                # Encoder pour le modèle standard
                prepared_data = self.data_prep.encode_features_for_model(enhanced_data, is_training=False)
                top3_predictions = self.model.predict_standard(prepared_data)
            
            # Récupérer les commentaires et informations supplémentaires
            commentaire_query = f"""
            SELECT texte FROM commentaires_course
            WHERE id_course = {course_id}
            """
            
            commentaires = pd.read_sql_query(commentaire_query, self.data_prep.engine)
            
            # Construire le rapport d'analyse
            analysis_report = {
                'course': course_info,
                'nombre_participants': len(participants_data),
                'top7_predictions': top7_predictions.to_dict(orient='records') if top7_predictions is not None else None,
                'top3_predictions': top3_predictions.to_dict(orient='records') if top3_predictions is not None else None,
                'commentaires': commentaires['texte'].tolist() if not commentaires.empty else [],
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Générer des suggestions de paris
            bets_suggestions = self._generate_betting_suggestions(top7_predictions)
            analysis_report['paris_suggeres'] = bets_suggestions
            
            # Sauvegarder le rapport
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_dir = 'analyses'
            os.makedirs(output_dir, exist_ok=True)
            output_file = f"{output_dir}/analyse_{course_id}_{timestamp}.json"
            
            with open(output_file, 'w') as f:
                json.dump(analysis_report, f, indent=2)
            
            self.logger.info(f"Analyse de la course {course_id} sauvegardée dans {output_file}")
            
            return analysis_report
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'analyse de la course {course_id}: {str(e)}")
            return None
    
    def _generate_betting_suggestions(self, predictions):
        """
        Génère des suggestions de paris basées sur les prédictions.
        """
        if predictions is None or len(predictions) < 7:
            return None
        
        # Récupérer les chevaux dans l'ordre prédit
        top_horses = predictions.sort_values('predicted_rank').head(7)
        
        # Suggestions pour différents types de paris
        betting_suggestions = {
            'simple_gagnant': {
                'type': 'Simple Gagnant',
                'description': 'Pari sur le cheval gagnant uniquement',
                'selection': [int(top_horses.iloc[0]['id_cheval'])],
                'confiance': float(top_horses.iloc[0]['in_top1_prob'])
            },
            'simple_place': {
                'type': 'Simple Placé',
                'description': 'Pari sur un cheval finissant dans les 3 premiers',
                'selection': [int(top_horses.iloc[0]['id_cheval'])],
                'confiance': float(top_horses.iloc[0]['in_top3_prob'])
            },
            'couple_ordre': {
                'type': 'Couplé Ordre',
                'description': 'Pari sur les 2 premiers chevaux dans l\'ordre exact',
                'selection': [int(top_horses.iloc[0]['id_cheval']), int(top_horses.iloc[1]['id_cheval'])],
                'confiance': float(top_horses.iloc[0]['in_top1_prob'] * top_horses.iloc[1]['in_top3_prob'] * 0.8)
            },
            'couple_desordre': {
                'type': 'Couplé Désordre',
                'description': 'Pari sur les 2 premiers chevaux dans n\'importe quel ordre',
                'selection': [int(top_horses.iloc[0]['id_cheval']), int(top_horses.iloc[1]['id_cheval'])],
                'confiance': float(top_horses.iloc[0]['in_top3_prob'] * top_horses.iloc[1]['in_top3_prob'])
            },
            'tierce_ordre': {
                'type': 'Tiercé Ordre',
                'description': 'Pari sur les 3 premiers chevaux dans l\'ordre exact',
                'selection': [int(top_horses.iloc[0]['id_cheval']), int(top_horses.iloc[1]['id_cheval']), int(top_horses.iloc[2]['id_cheval'])],
                'confiance': float(top_horses.iloc[0]['in_top1_prob'] * top_horses.iloc[1]['in_top3_prob'] * top_horses.iloc[2]['in_top3_prob'] * 0.6)
            },
            'tierce_desordre': {
                'type': 'Tiercé Désordre',
                'description': 'Pari sur les 3 premiers chevaux dans n\'importe quel ordre',
                'selection': [int(top_horses.iloc[0]['id_cheval']), int(top_horses.iloc[1]['id_cheval']), int(top_horses.iloc[2]['id_cheval'])],
                'confiance': float(top_horses.iloc[0]['in_top3_prob'] * top_horses.iloc[1]['in_top3_prob'] * top_horses.iloc[2]['in_top3_prob'])
            },
            'quarte_ordre': {
                'type': 'Quarté Ordre',
                'description': 'Pari sur les 4 premiers chevaux dans l\'ordre exact',
                'selection': [int(top_horses.iloc[0]['id_cheval']), int(top_horses.iloc[1]['id_cheval']), 
                             int(top_horses.iloc[2]['id_cheval']), int(top_horses.iloc[3]['id_cheval'])],
                'confiance': float(top_horses.iloc[0]['in_top1_prob'] * top_horses.iloc[1]['in_top3_prob'] * 
                                  top_horses.iloc[2]['in_top5_prob'] * top_horses.iloc[3]['in_top5_prob'] * 0.4)
            },
            'quarte_desordre': {
                'type': 'Quarté Désordre',
                'description': 'Pari sur les 4 premiers chevaux dans n\'importe quel ordre',
                'selection': [int(top_horses.iloc[0]['id_cheval']), int(top_horses.iloc[1]['id_cheval']), 
                             int(top_horses.iloc[2]['id_cheval']), int(top_horses.iloc[3]['id_cheval'])],
                'confiance': float(top_horses.iloc[0]['in_top5_prob'] * top_horses.iloc[1]['in_top5_prob'] * 
                                  top_horses.iloc[2]['in_top5_prob'] * top_horses.iloc[3]['in_top5_prob'])
            },
            'quinte_ordre': {
                'type': 'Quinté Ordre',
                'description': 'Pari sur les 5 premiers chevaux dans l\'ordre exact',
                'selection': [int(top_horses.iloc[0]['id_cheval']), int(top_horses.iloc[1]['id_cheval']), 
                             int(top_horses.iloc[2]['id_cheval']), int(top_horses.iloc[3]['id_cheval']), 
                             int(top_horses.iloc[4]['id_cheval'])],
                'confiance': float(top_horses.iloc[0]['in_top1_prob'] * top_horses.iloc[1]['in_top3_prob'] * 
                                  top_horses.iloc[2]['in_top5_prob'] * top_horses.iloc[3]['in_top7_prob'] * 
                                  top_horses.iloc[4]['in_top7_prob'] * 0.2)
            },
            'quinte_desordre': {
                'type': 'Quinté Désordre',
                'description': 'Pari sur les 5 premiers chevaux dans n\'importe quel ordre',
                'selection': [int(top_horses.iloc[0]['id_cheval']), int(top_horses.iloc[1]['id_cheval']), 
                             int(top_horses.iloc[2]['id_cheval']), int(top_horses.iloc[3]['id_cheval']), 
                             int(top_horses.iloc[4]['id_cheval'])],
                'confiance': float(top_horses.iloc[0]['in_top7_prob'] * top_horses.iloc[1]['in_top7_prob'] * 
                                  top_horses.iloc[2]['in_top7_prob'] * top_horses.iloc[3]['in_top7_prob'] * 
                                  top_horses.iloc[4]['in_top7_prob'])
            },
            'top7': {
                'type': 'Top 7',
                'description': 'Prédiction des 7 premiers chevaux',
                'selection': [int(top_horses.iloc[i]['id_cheval']) for i in range(7)],
                'confiance': float(top_horses.iloc[0]['in_top7_prob'] * top_horses.iloc[1]['in_top7_prob'] * 
                                  top_horses.iloc[2]['in_top7_prob'] * top_horses.iloc[3]['in_top7_prob'] * 
                                  top_horses.iloc[4]['in_top7_prob'] * top_horses.iloc[5]['in_top7_prob'] * 
                                  top_horses.iloc[6]['in_top7_prob'])
            }
        }
        
        return betting_suggestions
    
    def run_training(self, optimize_for_top7=False):
        """Entraîne les modèles sur les données historiques avec support optionnel pour Top 7."""
        self.logger.info("Démarrage de l'entraînement des modèles")
        
        try:
            # Récupérer les paramètres d'entraînement
            days_back = self.config.get('training', {}).get('days_back', 180)
            test_size = self.config.get('training', {}).get('test_size', 0.2)
            standard_model_type = self.config.get('training', {}).get('standard_model_type', 'xgboost')
            simulation_model_type = self.config.get('training', {}).get('simulation_model_type', 'xgboost_ranking')
            top_n_features = self.config.get('training', {}).get('top_n_features', 30)
            
            self.logger.info(f"Entraînement des modèles sur les données des {days_back} derniers jours")
            
            # Définir la période d'entraînement
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            self.logger.info(f"Récupération des données du {start_date.strftime('%Y-%m-%d')} au {end_date.strftime('%Y-%m-%d')}")
            
            # Récupérer les données
            training_data = self.data_prep.get_training_data(
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d")
            )
            
            if training_data.empty:
                self.logger.error("Aucune donnée d'entraînement trouvée")
                return False
            
            self.logger.info(f"Données récupérées: {len(training_data)} échantillons")
            
            # Créer des features avancées
            enhanced_data = self.data_prep.create_enhanced_features(training_data)
            
            # Créer les variables cibles
            prepared_data = self.model.create_target_variables(enhanced_data)
            
            # Entraîner le modèle standard
            self.logger.info(f"Entraînement du modèle standard ({standard_model_type})")
            
            if optimize_for_top7:
                # Utiliser la méthode d'entraînement améliorée avec sélection de features enrichie
                standard_accuracy, standard_path = self.model.train_with_enhanced_features(
                    prepared_data, 
                    target_col='target_place',
                    test_size=test_size,
                    top_n_features=top_n_features
                )
            else:
                # Utiliser la méthode d'entraînement standard existante
                standard_accuracy, standard_path = self.model.train_standard_model(prepared_data, test_size=test_size)
            
            # Entraîner le modèle de simulation
            self.logger.info(f"Entraînement du modèle de simulation ({simulation_model_type})")
            
            if optimize_for_top7:
                # Utiliser le modèle optimisé pour le Top 7
                simulation_metrics, simulation_path = self.model.train_top7_simulation_model(
                    prepared_data,
                    test_size=test_size,
                    top_n_features=top_n_features
                )
            else:
                # Utiliser la méthode d'entraînement de simulation standard
                simulation_metrics, simulation_path = self.model.train_simulation_model(prepared_data, test_size=test_size)
            
            # Mettre à jour les chemins des modèles dans la configuration
            if optimize_for_top7:
                self.config['standard_enhanced_model_path'] = standard_path
                self.config['simulation_top7_model_path'] = simulation_path
            else:
                self.config['standard_model_path'] = standard_path
                self.config['simulation_model_path'] = simulation_path
            
            # Sauvegarder la configuration mise à jour
            with open('config/config.json', 'w') as f:
                json.dump(self.config, f, indent=2)
            
            self.logger.info("Entraînement des modèles terminé")
            self.logger.info(f"Modèle standard ({standard_model_type}): {standard_path}")
            self.logger.info(f"Précision: {standard_accuracy:.4f}")
            self.logger.info(f"Modèle de simulation ({simulation_model_type}): {simulation_path}")
            
            # Configuration mise à jour avec les nouveaux modèles
            self.logger.info("Configuration mise à jour avec les nouveaux modèles")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'entraînement: {str(e)}")
            return False

def parse_args():
    """Parse les arguments de ligne de commande."""
    parser = argparse.ArgumentParser(description='Orchestrateur du système de prédiction PMU')
    
    parser.add_argument('--config', type=str, default='config/config.json',
                        help='Chemin vers le fichier de configuration')
    
    parser.add_argument('--action', type=str, 
                        choices=['all', 'scrape', 'predict', 'evaluate', 'train', 'schedule', 'simulate'],
                        default='all', help='Action à exécuter')
    
    # Arguments pour l'optimisation Top 7
    parser.add_argument('--top7', action='store_true',
                       help='Optimiser les modèles pour les prédictions Top 7 (Quinté)')
    
    parser.add_argument('--quinte', action='store_true',
                       help='Alias pour --top7')
    
    # Autres arguments existants...
    
    args = parser.parse_args()
    
    # Gérer l'alias quinte → top7
    if args.quinte:
        args.top7 = True
    
    return args
def main():
    """Fonction principale."""
    args = parse_args()
    
    # Initialiser l'orchestrateur
    orchestrateur = PMUOrchestrateur(config_path=args.config)
    
    # Exécuter l'action demandée
    if args.action == 'train':
        optimize_for_top7 = args.top7 or args.quinte
        orchestrateur.run_training(optimize_for_top7=optimize_for_top7)
        
    # Autres actions...
    elif args.action == 'scrape':
        orchestrateur.run_scraping()
    # etc.
    
    elif args.action == 'predict':
        # Exemple d'utilisation de la prédiction
        course_id = 12345  # Remplacer par l'ID de la course souhaitée
        predictions = orchestrateur.predict_course_top7(course_id)
        print(predictions)
    
    elif args.action == 'simulate':
        # Exemple d'utilisation de la simulation
        course_id = 12345  # Remplacer par l'ID de la course souhaitée
        selected_horses = [1, 2, 3]  # Liste des chevaux sélectionnés
        simulation_params = {'param1': 'value1'}  # Paramètres personnalisés pour la simulation
        results = orchestrateur.simulate_custom_top7(course_id, selected_horses, simulation_params)
        print(results)
    
    elif args.action == 'evaluate':
        # Exemple d'utilisation de l'évaluation
        course_id = 12345  # Remplacer par l'ID de la course souhaitée
        analysis_report = orchestrateur.run_course_analysis(course_id)
        print(analysis_report)
    
    elif args.action == 'schedule':
        # Exemple d'utilisation de la planification
        orchestrateur.schedule_tasks()
    
    else:
        print("Aucune action valide spécifiée.")
if __name__ == '__main__':
    main()