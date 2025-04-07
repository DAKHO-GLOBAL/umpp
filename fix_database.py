#!/usr/bin/env python3
from sqlalchemy import create_engine, text
import os
import json

# Charger la configuration
config_path = 'config/config.json'
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "pmu_ia",
    "port": "3306",
    "connector": "pymysql"
}

if os.path.exists(config_path):
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
            if 'db_config' in config:
                db_config = config['db_config']
    except Exception as e:
        print(f"Error loading config: {e}")

# Créer une connexion à la base de données
engine = create_engine(f"mysql+{db_config.get('connector', 'pymysql')}://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}")

with engine.connect() as conn:
    # Vérifier si la table predictions existe
    result = conn.execute(text("SHOW TABLES LIKE 'predictions'"))
    if result.fetchone():
        # Mettre à jour la colonne model_version_id pour qu'elle accepte NULL
        conn.execute(text("ALTER TABLE predictions MODIFY COLUMN model_version_id INT NULL"))
        print("Table 'predictions' updated to allow NULL model_version_id")
    
    # Créer les tables manquantes
    from database.setup_database import Base, engine
    # Supprimer les relations problématiques temporairement
    from database.setup_database import Prediction, ModelVersion
    
    # Créer les tables
    Base.metadata.create_all(engine)
    print("Tables created successfully")

print("Database fixed successfully!")