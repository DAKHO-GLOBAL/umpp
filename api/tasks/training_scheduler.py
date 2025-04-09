# training_scheduler.py
# training_scheduler.py
# api/tasks/training_scheduler.py
import logging
import traceback
import os
import json
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from sqlalchemy import text
from flask import current_app

from extensions import db
from model.dual_prediction_model import DualPredictionModel
from data_preparation.enhanced_data_prep import EnhancedDataPreparation

logger = logging.getLogger(__name__)

def train_models(days_back=300, model_type='xgboost'):
    """
    Entraîne les modèles de prédiction.
    
    Args:
        days_back (int): Nombre de jours de données à utiliser pour l'entraînement
        model_type (str): Type de modèle à entraîner
        
    Returns:
        dict: Résultats de l'entraînement
    """
    logger.info(f"Starting model training task: days_back={days_back}, model_type={model_type}")
    
    results = {
        'start_time': datetime.now().isoformat(),
        'status': 'success',
        'models_trained': [],
        'metrics': {},
        'errors': []
    }
    
    try:
        # Initialiser le préparateur de données
        data_prep = EnhancedDataPreparation()
        
        # Initialiser le modèle
        model = DualPredictionModel(base_path=current_app.config.get('MODEL_PATH', 'model/trained_models'))
        
        # Charger les données d'entraînement
        cutoff_date = datetime.now() - timedelta(days=days_back)
        test_days = 60  # Derniers 60 jours pour le test
        
        logger.info(f"Loading training data from {cutoff_date}")
        
        try:
            # Charger les données des courses passées
            training_data = data_prep.load_historical_data(cutoff_date)
            
            if training_data is None or training_data.empty:
                error_msg = "No historical data available for training"
                logger.error(error_msg)
                results['errors'].append(error_msg)
                results['status'] = 'error'
                return results
            
            logger.info(f"Loaded {len(training_data)} samples for training")
            
            # Créer des features avancées
            enhanced_data = data_prep.create_advanced_features(training_data)
            
            # Séparer les données d'entraînement et de test
            test_cutoff = datetime.now() - timedelta(days=test_days)
            
            if 'date_heure' in enhanced_data.columns:
                train_data = enhanced_data[enhanced_data['date_heure'] < test_cutoff]
                test_data = enhanced_data[enhanced_data['date_heure'] >= test_cutoff]
            else:
                # Si pas de date, utiliser une séparation 80/20
                train_size = int(len(enhanced_data) * 0.8)
                train_data = enhanced_data.iloc[:train_size]
                test_data = enhanced_data.iloc[train_size:]
            
            logger.info(f"Train set: {len(train_data)} samples, Test set: {len(test_data)} samples")
            
            # Préparer les données pour l'entraînement
            X_train, y_train = data_prep.prepare_training_data(train_data)
            X_test, y_test = data_prep.prepare_training_data(test_data)
            
            # Entraîner les modèles
            models_trained = []
            
            # 1. Modèle standard (classification binaire pour Top 3)
            try:
                logger.info("Training standard model (Top 3 classification)")
                
                standard_metrics = model.train_standard_model(
                    X_train, y_train, X_test, y_test, 
                    model_type=model_type
                )
                
                # Enregistrer le modèle
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                standard_model_path = f"standard_{model_type}_{timestamp}.pkl"
                full_path = model.save_standard_model(standard_model_path)
                
                # Mettre à jour les résultats
                models_trained.append({
                    'name': 'standard',
                    'type': model_type,
                    'file_path': full_path,
                    'metrics': standard_metrics,
                    'sample_count': len(X_train)
                })
                
                # Enregistrer dans la base de données
                register_model_in_db(
                    model_type=f"{model_type}_standard",
                    model_category='standard',
                    hyperparameters=model.standard_model_params,
                    metrics=standard_metrics,
                    file_path=full_path,
                    sample_count=len(X_train),
                    feature_count=X_train.shape[1] if hasattr(X_train, 'shape') else 0
                )
                
                logger.info(f"Standard model trained successfully: {standard_metrics}")
                
            except Exception as e:
                error_msg = f"Error training standard model: {str(e)}"
                logger.error(error_msg)
                logger.error(traceback.format_exc())
                results['errors'].append(error_msg)
            
            # 2. Modèle de simulation (Ranking pour Top 7)
            try:
                logger.info("Training simulation model (Top 7 ranking)")
                
                simulation_metrics = model.train_simulation_model(
                    X_train, y_train, X_test, y_test, 
                    model_type=f"{model_type}_ranking"
                )
                
                # Enregistrer le modèle
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                simulation_model_path = f"simulation_top7_{model_type}_ranking_{timestamp}.pkl"
                full_path = model.save_simulation_model(simulation_model_path)
                
                # Mettre à jour les résultats
                models_trained.append({
                    'name': 'simulation_top7',
                    'type': f"{model_type}_ranking",
                    'file_path': full_path,
                    'metrics': simulation_metrics,
                    'sample_count': len(X_train)
                })
                
                # Enregistrer dans la base de données
                register_model_in_db(
                    model_type=f"{model_type}_ranking",
                    model_category='simulation',
                    hyperparameters=model.simulation_model_params,
                    metrics=simulation_metrics,
                    file_path=full_path,
                    sample_count=len(X_train),
                    feature_count=X_train.shape[1] if hasattr(X_train, 'shape') else 0
                )
                
                logger.info(f"Simulation model trained successfully: {simulation_metrics}")
                
            except Exception as e:
                error_msg = f"Error training simulation model: {str(e)}"
                logger.error(error_msg)
                logger.error(traceback.format_exc())
                results['errors'].append(error_msg)
            
            # 3. Modèle amélioré (Enhanced version avec features additionnelles)
            try:
                logger.info("Training enhanced model")
                
                # Ajouter des features supplémentaires
                enhanced_X_train, enhanced_y_train = data_prep.create_enhanced_features(X_train, y_train)
                enhanced_X_test, enhanced_y_test = data_prep.create_enhanced_features(X_test, y_test)
                
                enhanced_metrics = model.train_enhanced_model(
                    enhanced_X_train, enhanced_y_train, enhanced_X_test, enhanced_y_test, 
                    model_type=model_type
                )
                
                # Enregistrer le modèle
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                enhanced_model_path = f"enhanced_{model_type}_{timestamp}.pkl"
                full_path = model.save_enhanced_model(enhanced_model_path)
                
                # Mettre à jour les résultats
                models_trained.append({
                    'name': 'enhanced',
                    'type': model_type,
                    'file_path': full_path,
                    'metrics': enhanced_metrics,
                    'sample_count': len(enhanced_X_train)
                })
                
                # Enregistrer dans la base de données
                register_model_in_db(
                    model_type=f"{model_type}_enhanced",
                    model_category='standard',
                    hyperparameters=model.enhanced_model_params,
                    metrics=enhanced_metrics,
                    file_path=full_path,
                    sample_count=len(enhanced_X_train),
                    feature_count=enhanced_X_train.shape[1] if hasattr(enhanced_X_train, 'shape') else 0
                )
                
                logger.info(f"Enhanced model trained successfully: {enhanced_metrics}")
                
            except Exception as e:
                error_msg = f"Error training enhanced model: {str(e)}"
                logger.error(error_msg)
                logger.error(traceback.format_exc())
                results['errors'].append(error_msg)
            
            # Mettre à jour le résultat
            results['models_trained'] = models_trained
            
            # Agréger les métriques
            all_metrics = {}
            for trained_model in models_trained:
                all_metrics[trained_model['name']] = trained_model['metrics']
            
            results['metrics'] = all_metrics
            
        except Exception as e:
            error_msg = f"Error in training data preparation: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            results['errors'].append(error_msg)
            results['status'] = 'error'
        
        # Mettre à jour le statut final
        if len(results['errors']) > 0 and not results['models_trained']:
            results['status'] = 'error'
        elif len(results['errors']) > 0:
            results['status'] = 'partial_success'
        
        results['end_time'] = datetime.now().isoformat()
        results['duration_seconds'] = (datetime.fromisoformat(results['end_time']) - 
                                    datetime.fromisoformat(results['start_time'])).total_seconds()
        
        logger.info(f"Model evaluation completed: {len(results['models_evaluated'])} models evaluated")
        return results
        
    except Exception as e:
        error_msg = f"Error in model evaluation task: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        
        results['status'] = 'error'
        results['errors'].append(error_msg)
        results['end_time'] = datetime.now().isoformat()
        results['duration_seconds'] = (datetime.fromisoformat(results['end_time']) - 
                                      datetime.fromisoformat(results['start_time'])).total_seconds()
        
        return results

def register_model_in_db(model_type, model_category, hyperparameters, metrics, file_path, sample_count, feature_count=0):
    """
    Enregistre un nouveau modèle dans la base de données.
    
    Args:
        model_type (str): Type du modèle
        model_category (str): Catégorie du modèle (standard, simulation)
        hyperparameters (dict): Hyperparamètres du modèle
        metrics (dict): Métriques d'évaluation
        file_path (str): Chemin du fichier du modèle
        sample_count (int): Nombre d'échantillons utilisés pour l'entraînement
        feature_count (int): Nombre de features utilisées
        
    Returns:
        int: ID du modèle enregistré
    """
    try:
        # Préparer les données pour l'insertion
        query = text("""
            INSERT INTO model_versions
            (model_type, model_category, hyperparameters, training_date, 
             accuracy, precision_score, recall_score, f1_score, log_loss,
             file_path, feature_count, sample_count, validation_method, is_active, created_at)
            VALUES
            (:model_type, :model_category, :hyperparameters, :training_date, 
             :accuracy, :precision_score, :recall_score, :f1_score, :log_loss,
             :file_path, :feature_count, :sample_count, :validation_method, :is_active, :created_at)
            RETURNING id
        """)
        
        # Extraire les métriques
        accuracy = metrics.get('accuracy', 0)
        precision = metrics.get('precision', 0)
        recall = metrics.get('recall', 0)
        f1_score = metrics.get('f1', 0)
        log_loss = metrics.get('log_loss', 0)
        
        # Exécuter l'insertion
        result = db.session.execute(query, {
            "model_type": model_type,
            "model_category": model_category,
            "hyperparameters": json.dumps(hyperparameters),
            "training_date": datetime.now(),
            "accuracy": accuracy,
            "precision_score": precision,
            "recall_score": recall,
            "f1_score": f1_score,
            "log_loss": log_loss,
            "file_path": file_path,
            "feature_count": feature_count,
            "sample_count": sample_count,
            "validation_method": "train_test_split",
            "is_active": False,  # Par défaut, le modèle n'est pas actif
            "created_at": datetime.now()
        })
        
        model_id = result.fetchone()[0]
        db.session.commit()
        
        logger.info(f"Model registered in database with ID {model_id}")
        return model_id
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error registering model in database: {str(e)}")
        logger.error(traceback.format_exc())
        return None

def update_model_metrics(model_id, metrics):
    """
    Met à jour les métriques d'un modèle existant.
    
    Args:
        model_id (int): ID du modèle
        metrics (dict): Nouvelles métriques d'évaluation
        
    Returns:
        bool: True si la mise à jour a réussi, False sinon
    """
    try:
        # Extraire les métriques
        accuracy = metrics.get('accuracy', 0)
        precision = metrics.get('precision', 0)
        recall = metrics.get('recall', 0)
        f1_score = metrics.get('f1', 0)
        log_loss = metrics.get('log_loss', 0)
        
        # Préparer les données pour la mise à jour
        query = text("""
            UPDATE model_versions
            SET accuracy = :accuracy,
                precision_score = :precision_score,
                recall_score = :recall_score,
                f1_score = :f1_score,
                log_loss = :log_loss,
                updated_at = :updated_at
            WHERE id = :model_id
        """)
        
        # Exécuter la mise à jour
        db.session.execute(query, {
            "model_id": model_id,
            "accuracy": accuracy,
            "precision_score": precision,
            "recall_score": recall,
            "f1_score": f1_score,
            "log_loss": log_loss,
            "updated_at": datetime.now()
        })
        
        db.session.commit()
        
        logger.info(f"Model metrics updated for ID {model_id}")
        return True
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating model metrics: {str(e)}")
        logger.error(traceback.format_exc())
        return False

def activate_best_models():
    """
    Active les meilleurs modèles basés sur les métriques d'évaluation récentes.
    
    Returns:
        dict: Résultats de l'activation
    """
    logger.info("Starting best model activation task")
    
    results = {
        'start_time': datetime.now().isoformat(),
        'status': 'success',
        'models_activated': [],
        'models_deactivated': [],
        'errors': []
    }
    
    try:
        # Récupérer les modèles par catégorie
        categories = ['standard', 'simulation']
        
        for category in categories:
            try:
                # Trouver le meilleur modèle pour cette catégorie
                query = text("""
                    SELECT id, model_type, f1_score, file_path
                    FROM model_versions
                    WHERE model_category = :category
                    AND created_at > NOW() - INTERVAL '30 days'
                    ORDER BY f1_score DESC, accuracy DESC, created_at DESC
                    LIMIT 1
                """)
                
                best_model = db.session.execute(query, {"category": category}).fetchone()
                
                if not best_model:
                    logger.info(f"No recent models found for category {category}")
                    continue
                
                # Désactiver tous les modèles de cette catégorie
                deactivate_query = text("""
                    UPDATE model_versions
                    SET is_active = FALSE
                    WHERE model_category = :category
                    AND is_active = TRUE
                    RETURNING id
                """)
                
                deactivated = db.session.execute(deactivate_query, {"category": category}).fetchall()
                deactivated_ids = [row.id for row in deactivated]
                results['models_deactivated'].extend(deactivated_ids)
                
                # Activer le meilleur modèle
                activate_query = text("""
                    UPDATE model_versions
                    SET is_active = TRUE
                    WHERE id = :model_id
                """)
                
                db.session.execute(activate_query, {"model_id": best_model.id})
                
                results['models_activated'].append({
                    'id': best_model.id,
                    'category': category,
                    'type': best_model.model_type,
                    'f1_score': best_model.f1_score,
                    'file_path': best_model.file_path
                })
                
                logger.info(f"Activated model {best_model.id} for category {category}")
                
            except Exception as e:
                error_msg = f"Error activating best model for category {category}: {str(e)}"
                logger.error(error_msg)
                logger.error(traceback.format_exc())
                results['errors'].append(error_msg)
                continue
        
        db.session.commit()
        
        # Mettre à jour les chemins des modèles dans le fichier de configuration
        try:
            update_model_paths_in_config(results['models_activated'])
        except Exception as e:
            error_msg = f"Error updating model paths in config: {str(e)}"
            logger.error(error_msg)
            results['errors'].append(error_msg)
        
        # Mettre à jour le statut final
        if len(results['errors']) > 0 and not results['models_activated']:
            results['status'] = 'error'
        elif len(results['errors']) > 0:
            results['status'] = 'partial_success'
        
        results['end_time'] = datetime.now().isoformat()
        results['duration_seconds'] = (datetime.fromisoformat(results['end_time']) - 
                                      datetime.fromisoformat(results['start_time'])).total_seconds()
        
        logger.info(f"Best model activation completed: {len(results['models_activated'])} models activated")
        return results
        
    except Exception as e:
        db.session.rollback()
        error_msg = f"Error in best model activation task: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        
        results['status'] = 'error'
        results['errors'].append(error_msg)
        results['end_time'] = datetime.now().isoformat()
        results['duration_seconds'] = (datetime.fromisoformat(results['end_time']) - 
                                      datetime.fromisoformat(results['start_time'])).total_seconds()
        
        return results

def update_model_paths_in_config(activated_models):
    """
    Met à jour les chemins des modèles actifs dans le fichier de configuration.
    
    Args:
        activated_models (list): Liste des modèles activés
        
    Returns:
        bool: True si la mise à jour a réussi, False sinon
    """
    try:
        # Charger le fichier de configuration
        config_path = 'config/config.json'
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Mettre à jour les chemins des modèles
        for model_info in activated_models:
            category = model_info['category']
            file_path = model_info['file_path']
            
            if category == 'standard':
                if 'enhanced' in model_info['type'].lower():
                    config['standard_enhanced_model_path'] = file_path
                else:
                    config['standard_model_path'] = file_path
            elif category == 'simulation':
                if 'top7' in model_info['type'].lower():
                    config['simulation_top7_model_path'] = file_path
                else:
                    config['simulation_model_path'] = file_path
        
        # Mise à jour de la date du modèle
        today = datetime.now().strftime('%Y%m%d')
        config['model_update_date'] = today
        
        # Enregistrer la configuration mise à jour
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"Model paths updated in config file: {config_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error updating model paths in config: {str(e)}")
        logger.error(traceback.format_exc())
        results = {
            'start_time': datetime.now().isoformat(),
            'end_time': datetime.now().isoformat()
        }
        return (datetime.fromisoformat(results['end_time']) - datetime.fromisoformat(results['start_time'])).total_seconds()
        
        logger.info(f"Model training completed: {len(results['models_trained'])} models trained")
        return results
        
    except Exception as e:
        error_msg = f"Error in model training task: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        
        results['status'] = 'error'
        results['errors'].append(error_msg)
        results['end_time'] = datetime.now().isoformat()
        results['duration_seconds'] = (datetime.fromisoformat(results['end_time']) - 
                                      datetime.fromisoformat(results['start_time'])).total_seconds()
        
        return results

def evaluate_models(days_back=65):
    """
    Évalue les performances des modèles de prédiction.
    
    Args:
        days_back (int): Nombre de jours de données à utiliser pour l'évaluation
        
    Returns:
        dict: Résultats de l'évaluation
    """
    logger.info(f"Starting model evaluation task: days_back={days_back}")
    
    results = {
        'start_time': datetime.now().isoformat(),
        'status': 'success',
        'models_evaluated': [],
        'metrics': {},
        'errors': []
    }
    
    try:
        # Initialiser le préparateur de données
        data_prep = EnhancedDataPreparation()
        
        # Charger les données d'évaluation
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        logger.info(f"Loading evaluation data from {cutoff_date}")
        
        try:
            # Charger les données des courses passées avec résultats
            evaluation_data = data_prep.load_evaluation_data(cutoff_date)
            
            if evaluation_data is None or evaluation_data.empty:
                error_msg = "No evaluation data available"
                logger.error(error_msg)
                results['errors'].append(error_msg)
                results['status'] = 'error'
                return results
            
            logger.info(f"Loaded {len(evaluation_data)} samples for evaluation")
            
            # Créer des features avancées
            enhanced_data = data_prep.create_advanced_features(evaluation_data)
            
            # Préparer les données pour l'évaluation
            X_eval, y_eval = data_prep.prepare_training_data(enhanced_data)
            
            # Récupérer les modèles actifs
            models_query = text("""
                SELECT id, model_type, model_category, file_path, is_active
                FROM model_versions
                WHERE is_active = TRUE
                OR id IN (
                    SELECT id
                    FROM model_versions
                    WHERE created_at > :cutoff_date
                    ORDER BY created_at DESC
                    LIMIT 5
                )
            """)
            
            models_result = db.session.execute(models_query, {"cutoff_date": cutoff_date}).fetchall()
            
            if not models_result:
                logger.info("No models found for evaluation")
                results['status'] = 'success'
                results['end_time'] = datetime.now().isoformat()
                results['duration_seconds'] = 0
                return results
            
            # Évaluer chaque modèle
            models_evaluated = []
            all_metrics = {}
            
            for model_row in models_result:
                model_id = model_row.id
                model_type = model_row.model_type
                model_category = model_row.model_category
                file_path = model_row.file_path
                is_active = model_row.is_active
                
                try:
                    logger.info(f"Evaluating model {model_id}: {model_type} ({model_category})")
                    
                    # Initialiser le modèle avec le chemin du fichier
                    model = DualPredictionModel(base_path=os.path.dirname(file_path))
                    
                    # Charger le modèle selon sa catégorie
                    if model_category == 'standard':
                        model.load_standard_model(os.path.basename(file_path))
                        
                        # Évaluation différenciée selon le type de modèle
                        if 'enhanced' in model_type.lower():
                            # Créer des features supplémentaires pour le modèle amélioré
                            enhanced_X_eval, enhanced_y_eval = data_prep.create_enhanced_features(X_eval, y_eval)
                            metrics = model.evaluate_standard_model(enhanced_X_eval, enhanced_y_eval)
                        else:
                            metrics = model.evaluate_standard_model(X_eval, y_eval)
                            
                    elif model_category == 'simulation':
                        model.load_simulation_model(os.path.basename(file_path))
                        metrics = model.evaluate_simulation_model(X_eval, y_eval)
                    else:
                        logger.warning(f"Unknown model category: {model_category}")
                        continue
                    
                    # Mettre à jour les résultats
                    model_result = {
                        'id': model_id,
                        'type': model_type,
                        'category': model_category,
                        'is_active': is_active,
                        'file_path': file_path,
                        'metrics': metrics
                    }
                    
                    models_evaluated.append(model_result)
                    all_metrics[f"{model_category}_{model_id}"] = metrics
                    
                    # Mettre à jour les métriques dans la base de données
                    update_model_metrics(model_id, metrics)
                    
                    logger.info(f"Model {model_id} evaluated successfully: {metrics}")
                    
                except Exception as e:
                    error_msg = f"Error evaluating model {model_id}: {str(e)}"
                    logger.error(error_msg)
                    logger.error(traceback.format_exc())
                    results['errors'].append(error_msg)
            
            # Mettre à jour le résultat
            results['models_evaluated'] = models_evaluated
            results['metrics'] = all_metrics
            
        except Exception as e:
            error_msg = f"Error in evaluation data preparation: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            results['errors'].append(error_msg)
            results['status'] = 'error'
        
        # Mettre à jour le statut final
        if len(results['errors']) > 0 and not results['models_evaluated']:
            results['status'] = 'error'
        elif len(results['errors']) > 0:
            results['status'] = 'partial_success'
        
        results['end_time'] = datetime.now().isoformat()
        results['duration_seconds'] = (datetime.fromisoformat(results['end_time']) - 
                                      datetime.fromisoformat(results['start_time'])).total_seconds()
        logger.info(f"Model evaluation completed: {len(results['models_evaluated'])} models evaluated")
        return results
    except Exception as e:
        db.session.rollback()
        error_msg = f"Error in model evaluation task: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        
        results['status'] = 'error'
        results['errors'].append(error_msg)
        results['end_time'] = datetime.now().isoformat()
        results['duration_seconds'] = (datetime.fromisoformat(results['end_time']) - 
                                      datetime.fromisoformat(results['start_time'])).total_seconds()
        
        return results
def schedule_model_training():
    """
    Planifie l'entraînement des modèles de prédiction.
    
    Returns:
        dict: Résultats de la planification
    """
    logger.info("Starting model training scheduling task")
    
    results = {
        'start_time': datetime.now().isoformat(),
        'status': 'success',
        'scheduled_tasks': [],
        'errors': []
    }
    
    try:
        # Charger les paramètres de planification depuis le fichier de configuration
        config_path = 'config/scheduling_config.json'
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Extraire les paramètres de planification
        training_days_back = config.get('training_days_back', 300)
        training_model_type = config.get('training_model_type', 'xgboost')
        
        # Planifier l'entraînement
        task_id = f"train_models_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        task_info = {
            'id': task_id,
            'task_name': 'train_models',
            'params': {
                'days_back': training_days_back,
                'model_type': training_model_type
            },
            'status': 'scheduled',
            'start_time': datetime.now().isoformat()
        }
        
        results['scheduled_tasks'].append(task_info)
        
        logger.info(f"Scheduled task {task_id}: {task_info}")
        
        # Enregistrer la tâche dans la base de données ou un fichier
        # (Implémentation spécifique à votre application)
        
        results['end_time'] = datetime.now().isoformat()
        results['duration_seconds'] = (datetime.fromisoformat(results['end_time']) - 
                                      datetime.fromisoformat(results['start_time'])).total_seconds()
        
        logger.info(f"Model training scheduling completed: {len(results['scheduled_tasks'])} tasks scheduled")
        return results
        
    except Exception as e:
        error_msg = f"Error in model training scheduling task: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        
        results['status'] = 'error'
        results['errors'].append(error_msg)
        results['end_time'] = datetime.now().isoformat()
        results['duration_seconds'] = (datetime.fromisoformat(results['end_time']) - 
                                      datetime.fromisoformat(results['start_time'])).total_seconds()
        return results
