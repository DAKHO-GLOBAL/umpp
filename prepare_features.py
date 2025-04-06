#!/usr/bin/env python
# prepare_features.py
# Script pour préparer un ensemble de données prêt pour l'entraînement

import os
import argparse
import logging
from datetime import datetime, timedelta
import pandas as pd
from data_preparation.enhanced_data_prep import EnhancedDataPreparation

def parse_args():
    """Parse les arguments de la ligne de commande"""
    parser = argparse.ArgumentParser(description='Prepare features for model training')
    
    parser.add_argument('--days-back', type=int, default=180,
                        help='Number of days of historical data to use')
    
    parser.add_argument('--output-dir', type=str, default='data',
                        help='Directory to save prepared features')
    
    parser.add_argument('--filename', type=str, default=None,
                        help='Filename for output (default: features_YYYYMMDD.csv)')
    
    return parser.parse_args()

def setup_logging():
    """Configure le logging"""
    log_dir = 'logs'
    os.makedirs(log_dir, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f"{log_dir}/feature_preparation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
            logging.StreamHandler()
        ]
    )

def prepare_features(days_back, output_dir, filename=None):
    """Prépare les features et les sauvegarde dans un fichier CSV"""
    logger = logging.getLogger(__name__)
    
    # Créer le répertoire de sortie si nécessaire
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialiser la classe de préparation des données
    data_prep = EnhancedDataPreparation()
    
    # Définir la période d'extraction
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    
    logger.info(f"Extracting data from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    
    # Récupérer les données
    raw_data = data_prep.get_training_data(
        start_date=start_date.strftime('%Y-%m-%d'),
        end_date=end_date.strftime('%Y-%m-%d')
    )
    
    if raw_data.empty:
        logger.error("No data found for the specified period")
        return None
    
    logger.info(f"Retrieved {len(raw_data)} records from database")
    
    # Vérifier la qualité des données
    missing_cols = [col for col in ['id_cheval', 'id_jockey', 'position'] if col not in raw_data.columns]
    if missing_cols:
        logger.error(f"Missing critical columns: {missing_cols}")
        return None
    
    # Créer des features avancées
    logger.info("Creating advanced features")
    enhanced_data = data_prep.create_advanced_features(raw_data)
    
    # Encoder les features pour le modèle
    logger.info("Encoding features for modeling")
    prepared_data = data_prep.encode_features_for_model(enhanced_data, is_training=True)
    
    # Créer les variables cibles
    logger.info("Creating target variables")
    from model.dual_prediction_model import DualPredictionModel
    model = DualPredictionModel()
    final_data = model.create_target_variables(prepared_data)
    
    # Générer le nom du fichier si non spécifié
    if filename is None:
        filename = f"features_{datetime.now().strftime('%Y%m%d')}.csv"
    
    # Chemin complet du fichier
    output_path = os.path.join(output_dir, filename)
    
    # Sauvegarder les données préparées
    final_data.to_csv(output_path, index=False)
    logger.info(f"Features saved to {output_path}")
    
    # Quelques statistiques sur les données
    logger.info(f"Dataset statistics:")
    logger.info(f"  Total samples: {len(final_data)}")
    logger.info(f"  Number of courses: {final_data['id_course'].nunique()}")
    logger.info(f"  Number of horses: {final_data['id_cheval'].nunique()}")
    logger.info(f"  Number of jockeys: {final_data['id_jockey'].nunique()}")
    logger.info(f"  Winners (position=1): {len(final_data[final_data['position'] == 1])}")
    logger.info(f"  Top 3 finishers: {len(final_data[final_data['position'] <= 3])}")
    logger.info(f"  Feature count: {len(final_data.columns)}")
    
    # Sauvegarder aussi les encodeurs pour une utilisation future
    data_prep.save_encoders()
    
    return output_path

if __name__ == "__main__":
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Starting feature preparation script")
    
    args = parse_args()
    
    prepared_file = prepare_features(
        days_back=args.days_back,
        output_dir=args.output_dir,
        filename=args.filename
    )
    
    if prepared_file:
        logger.info(f"Feature preparation completed successfully: {prepared_file}")
    else:
        logger.error("Feature preparation failed")