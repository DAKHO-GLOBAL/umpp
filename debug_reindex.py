import pandas as pd
import numpy as np
import logging
from datetime import datetime
from data_preparation.enhanced_data_prep import EnhancedDataPreparation
from model.dual_prediction_model import DualPredictionModel

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def debug_training_process():
    logger.info("Starting debug process")
    
    # Initialiser les classes
    data_prep = EnhancedDataPreparation()
    
    # Récupérer les données
    end_date = datetime.now()
    start_date = end_date - pd.Timedelta(days=30)  # Réduire à 30 jours pour le débogage
    
    logger.info(f"Getting training data from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    
    # 1. Récupérer les données - ajouter des vérifications d'index
    training_data = data_prep.get_training_data(
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d")
    )
    
    if training_data.empty:
        logger.error("No training data found")
        return
    
    logger.info(f"Training data shape: {training_data.shape}")
    logger.info(f"Training data has duplicate indices: {training_data.index.duplicated().sum()}")
    
    # Force reset index
    training_data = training_data.reset_index(drop=True)
    logger.info(f"After reset_index, duplicate indices: {training_data.index.duplicated().sum()}")
    
    # 2. Créer des features avancées
    try:
        logger.info("Creating advanced features")
        enhanced_data = data_prep.create_advanced_features(training_data)
        logger.info(f"Enhanced data shape: {enhanced_data.shape}")
        logger.info(f"Enhanced data has duplicate indices: {enhanced_data.index.duplicated().sum()}")
        
        # Force reset index again
        enhanced_data = enhanced_data.reset_index(drop=True)
        logger.info(f"After reset_index, duplicate indices: {enhanced_data.index.duplicated().sum()}")
    except Exception as e:
        logger.error(f"Error in create_advanced_features: {str(e)}")
        return
    
    # 3. Encoder pour le modèle
    try:
        logger.info("Encoding features for modeling")
        prepared_data = data_prep.encode_features_for_model(enhanced_data, is_training=True)
        logger.info(f"Prepared data shape: {prepared_data.shape}")
        logger.info(f"Prepared data has duplicate indices: {prepared_data.index.duplicated().sum()}")
        
        # Force reset index again
        prepared_data = prepared_data.reset_index(drop=True)
        logger.info(f"After reset_index, duplicate indices: {prepared_data.index.duplicated().sum()}")
    except Exception as e:
        logger.error(f"Error in encode_features_for_model: {str(e)}")
        return
    
    # 4. Créer les variables cibles
    try:
        logger.info("Creating target variables")
        model = DualPredictionModel()
        final_data = model.create_target_variables(prepared_data)
        logger.info(f"Final data shape: {final_data.shape}")
        logger.info(f"Final data has duplicate indices: {final_data.index.duplicated().sum()}")
        
        # Force reset index again
        final_data = final_data.reset_index(drop=True)
        logger.info(f"After reset_index, duplicate indices: {final_data.index.duplicated().sum()}")
    except Exception as e:
        logger.error(f"Error in create_target_variables: {str(e)}")
        return
    
    # 5. Sélectionner les features
    try:
        logger.info("Selecting features")
        feature_cols = model.select_features(final_data, 'target_place')
        logger.info(f"Selected {len(feature_cols)} features")
        
        # Vérifier pour les NaN dans les features
        X = final_data[feature_cols]
        y = final_data['target_place']
        
        logger.info(f"X shape: {X.shape}")
        logger.info(f"X has NaN values: {X.isna().any().any()}")
        logger.info(f"y shape: {y.shape}")
        logger.info(f"y has NaN values: {y.isna().any()}")
        
        # Vérifier si les indices sont alignés
        logger.info(f"X index equals y index: {X.index.equals(y.index)}")
    except Exception as e:
        logger.error(f"Error in feature selection: {str(e)}")
        return
    
    logger.info("Debug process completed successfully - no errors detected")

if __name__ == "__main__":
    debug_training_process()