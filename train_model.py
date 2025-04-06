# 4. SCRIPT D'ENTRAÎNEMENT PRINCIPAL
# ------------------------------

# train_models.py
#!/usr/bin/env python
from datetime import datetime
import logging
import os
from orchestrator import train_models

def setup_logging():
    """Configure le logging pour les scripts d'entraînement"""
    log_dir = 'logs'
    os.makedirs(log_dir, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f"{log_dir}/training_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
            logging.StreamHandler()
        ]
    )

if __name__ == "__main__":
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Starting model training script")
    
    # Définir les paramètres d'entraînement
    training_params = {
        'days_back': 180,
        'test_size': 0.2,
        'standard_model_type': 'xgboost',
        'simulation_model_type': 'xgboost_ranking'
    }
    
    logger.info(f"Training parameters: {training_params}")
    
    # Lancer l'entraînement
    results = train_models(**training_params)
    
    if results:
        logger.info("Training completed successfully!")
        logger.info(f"Standard model: {results['standard_model']}")
        logger.info(f"Simulation model: {results['simulation_model']}")
    else:
        logger.error("Training failed")
