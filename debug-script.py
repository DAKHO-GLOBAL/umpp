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

def check_duplicates(df, stage_name, drop=False):
    """Vérifie et signale les index dupliqués dans un DataFrame"""
    duplicated = df.index[df.index.duplicated()]
    n_dupes = len(duplicated)
    if n_dupes > 0:
        logger.warning(f"DUPLICATES DETECTED at {stage_name}: {n_dupes} duplicate indexes")
        logger.warning(f"Sample duplicate indexes: {duplicated.tolist()[:5]}")
        if drop:
            logger.warning(f"Dropping duplicate indexes at {stage_name}")
            df = df[~df.index.duplicated(keep='first')]
    else:
        logger.info(f"No duplicates at {stage_name}")
    return df

def debug_process():
    """Exécute le processus d'entraînement en mode debug"""
    logger.info("🚀 Starting debug process for training")
    
    # Initialiser les classes
    data_prep = EnhancedDataPreparation()
    model = DualPredictionModel()
    
    # 1. Récupérer les données
    logger.info("📥 Getting training data")
    training_data = data_prep.get_training_data()
    
    if training_data.empty:
        logger.error("❌ No training data found")
        return
    
    logger.info(f"✅ Retrieved {len(training_data)} samples")
    training_data = check_duplicates(training_data, "initial training data", drop=True)
    training_data = training_data.reset_index(drop=True)
    
    # 2. Créer des features avancées
    logger.info("🧠 Creating advanced features")
    enhanced_data = data_prep.create_advanced_features(training_data)
    enhanced_data = check_duplicates(enhanced_data, "after create_advanced_features", drop=True)
    enhanced_data = enhanced_data.reset_index(drop=True)
    
    # 3. Encoder pour le modèle
    logger.info("🎛️ Encoding features")
    prepared_data = data_prep.encode_features_for_model(enhanced_data, is_training=True)
    prepared_data = check_duplicates(prepared_data, "after encode_features_for_model", drop=True)
    prepared_data = prepared_data.reset_index(drop=True)
    
    # 4. Créer les variables cibles
    logger.info("🎯 Creating target variables")
    final_data = model.create_target_variables(prepared_data)
    final_data = check_duplicates(final_data, "after create_target_variables", drop=True)
    final_data = final_data.reset_index(drop=True)
    
    # 5. Vérifier les opérations critiques
    logger.info("🔍 Checking critical operations")
    feature_cols = model.select_features(final_data, 'target_place')
    X = final_data[feature_cols]
    y = final_data['target_place']
    
    logger.info(f"📊 Feature columns selected: {len(feature_cols)}")
    X = check_duplicates(X, "feature selection X", drop=True)
    y_df = pd.DataFrame(y)
    y_df = check_duplicates(y_df, "feature selection y", drop=True)
    
    logger.info("✅ Debug process completed without crash 🎉")

if __name__ == "__main__":
    logger.info("🟢 Starting debug script")
    debug_process()
    logger.info("🟣 Debug script completed")
