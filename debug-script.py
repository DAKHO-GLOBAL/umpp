#!/usr/bin/env python
import pandas as pd
import numpy as np
import logging
from datetime import datetime
import os

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Importer les modules problématiques
from data_preparation.enhanced_data_prep import EnhancedDataPreparation
from model.dual_prediction_model import DualPredictionModel

def check_duplicates(df, stage_name):
    """Vérifie et signale les index dupliqués dans un DataFrame"""
    dupes = df.index.duplicated().sum()
    if dupes > 0:
        logger.warning(f"DUPLICATES DETECTED at {stage_name}: {dupes} duplicate indexes")
        logger.warning(f"Sample duplicate indexes: {df.index[df.index.duplicated()].tolist()[:5]}")
        return True
    else:
        logger.info(f"No duplicates at {stage_name}")
        return False

def debug_process():
    """Exécute le processus d'entraînement en mode debug"""
    logger.info("Starting debug process for training")
    
    # Initialiser les classes
    data_prep = EnhancedDataPreparation()
    model = DualPredictionModel()
    
    # 1. Récupérer les données
    logger.info("Getting training data")
    training_data = data_prep.get_training_data()
    
    # Vérifier les index dupliqués
    if training_data.empty:
        logger.error("No training data found")
        return
    
    logger.info(f"Retrieved {len(training_data)} samples")
    check_duplicates(training_data, "initial training data")
    
    # Forcer la réinitialisation de l'index à ce stade
    training_data = training_data.reset_index(drop=True)
    
    # 2. Créer des features avancées
    logger.info("Creating advanced features")
    enhanced_data = data_prep.create_advanced_features(training_data)
    check_duplicates(enhanced_data, "after create_advanced_features")
    
    # Forcer la réinitialisation de l'index à ce stade
    enhanced_data = enhanced_data.reset_index(drop=True)
    
    # 3. Encoder pour le modèle
    logger.info("Encoding features")
    prepared_data = data_prep.encode_features_for_model(enhanced_data, is_training=True)
    check_duplicates(prepared_data, "after encode_features_for_model")
    
    # Forcer la réinitialisation de l'index à ce stade
    prepared_data = prepared_data.reset_index(drop=True)
    
    # 4. Créer les variables cibles
    logger.info("Creating target variables")
    final_data = model.create_target_variables(prepared_data)
    check_duplicates(final_data, "after create_target_variables")
    
    # Forcer la réinitialisation de l'index à ce stade
    final_data = final_data.reset_index(drop=True)
    
    # 5. Vérifier les opérations critiques
    logger.info("Checking critical operations")
    
    # Vérifier la sélection de features
    feature_cols = model.select_features(final_data, 'target_place')
    X = final_data[feature_cols]
    y = final_data['target_place']
    
    logger.info(f"Feature columns: {len(feature_cols)}")
    check_duplicates(X, "feature selection X")
    check_duplicates(pd.DataFrame(y), "feature selection y")
    
    logger.info("Debug process completed")

if __name__ == "__main__":
    logger.info("Starting debug script")
    debug_process()
    logger.info("Debug script completed")