#!/usr/bin/env python3
import logging
from logging.config import fileConfig
from datetime import datetime, timedelta
from scrapping.scrapping import call_api_between_dates

# Configuration du logging
fileConfig('logger/logging_config.ini')
logger = logging.getLogger(__name__)

def main():
    """
    Script principal pour l'import initial des données PMU.
    Collecte les données des courses des 90 derniers jours.
    """
    logger.info("Démarrage de l'import initial des données PMU")
    
    # Période de collecte: 90 derniers jours
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    
    logger.info(f"Collecte des données du {start_date.strftime('%Y-%m-%d')} au {end_date.strftime('%Y-%m-%d')}")
    
    try:
        # Appel à la fonction de scraping
        call_api_between_dates(start_date, end_date)
        
        logger.info("Import initial des données terminé avec succès")
    except Exception as e:
        logger.error(f"Erreur lors de l'import initial des données: {str(e)}")

if __name__ == "__main__":
    main()