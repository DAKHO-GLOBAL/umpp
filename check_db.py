# Créez un fichier check_db.py
import pandas as pd
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

# Vérifier les tables
with engine.connect() as conn:
    result = conn.execute(text("SHOW TABLES"))
    tables = [row[0] for row in result]
    print(f"Tables in database: {tables}")

    # Vérifier les courses
    result = conn.execute(text("SELECT COUNT(*) FROM courses"))
    count = result.scalar()
    print(f"Number of courses: {count}")

    # Vérifier les courses avec résultats
    result = conn.execute(text("SELECT COUNT(*) FROM courses WHERE ordreArrivee IS NOT NULL"))
    count = result.scalar()
    print(f"Number of courses with results: {count}")

    # Vérifier les participants
    if 'participations' in tables:
        result = conn.execute(text("SELECT COUNT(*) FROM participations"))
        count = result.scalar()
        print(f"Number of participations: {count}")