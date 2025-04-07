# Architecture du système de prédiction PMU
# =======================================

# 1. TRAITEMENT DES DONNÉES
# ------------------------------

# data_preparation/enhanced_data_prep.py
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from sklearn.preprocessing import LabelEncoder, StandardScaler, OneHotEncoder
from datetime import datetime, timedelta
import logging
import joblib
import os

import json
import os

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

# Modifier la chaîne de connexion
#engine = create_engine(f"mysql+{db_config.get('connector', 'pymysql')}://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}")

class EnhancedDataPreparation:
    """Version améliorée de la classe DataPreparation avec des fonctionnalités supplémentaires"""
    
    def __init__(self, db_path='pmu_ia'):
        """Initialise la connexion à la base de données et les encodeurs."""
        self.engine = create_engine(f"mysql+{db_config.get('connector', 'pymysql')}://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}")

        self.label_encoders = {}
        self.one_hot_encoders = {}
        self.scaler = StandardScaler()
        self.logger = logging.getLogger(__name__)
        
        # Créer le dossier pour stocker les encodeurs
        os.makedirs('data_preparation/encoders', exist_ok=True)
    
    def load_encoders(self, folder_path='data_preparation/encoders'):
        """Charge les encodeurs pré-entraînés"""
        try:
            if os.path.exists(f'{folder_path}/label_encoders.pkl'):
                self.label_encoders = joblib.load(f'{folder_path}/label_encoders.pkl')
                self.logger.info("Label encoders loaded successfully")
            
            if os.path.exists(f'{folder_path}/one_hot_encoders.pkl'):
                self.one_hot_encoders = joblib.load(f'{folder_path}/one_hot_encoders.pkl')
                self.logger.info("One-hot encoders loaded successfully")
            
            if os.path.exists(f'{folder_path}/scaler.pkl'):
                self.scaler = joblib.load(f'{folder_path}/scaler.pkl')
                self.logger.info("Scaler loaded successfully")
        
        except Exception as e:
            self.logger.error(f"Error loading encoders: {str(e)}")
    
    def save_encoders(self, folder_path='data_preparation/encoders'):
        """Sauvegarde les encodeurs entraînés"""
        try:
            joblib.dump(self.label_encoders, f'{folder_path}/label_encoders.pkl')
            joblib.dump(self.one_hot_encoders, f'{folder_path}/one_hot_encoders.pkl')
            joblib.dump(self.scaler, f'{folder_path}/scaler.pkl')
            self.logger.info("Encoders saved successfully")
        
        except Exception as e:
            self.logger.error(f"Error saving encoders: {str(e)}")
    
    def get_training_data(self, start_date=None, end_date=None, limit=None):
        """Récupère un ensemble de données pour l'entraînement avec résultats connus"""
        # Récupérer les courses terminées
        # courses_query = """
        # SELECT c.*, h.libelleLong AS hippodrome_nom 
        # FROM courses c
        # LEFT JOIN pmu_hippodromes h ON c.lieu = h.libelleLong
        # WHERE c.ordreArrivee IS NOT NULL
        # """
        courses_query = """
        SELECT c.*, h.libelleLong AS hippodrome_nom 
        FROM courses c
        LEFT JOIN pmu_hippodromes h ON c.lieu = h.libelleLong
        """
        
        conditions = []
        if start_date:
            conditions.append(f"c.date_heure >= '{start_date}'")
        if end_date:
            conditions.append(f"c.date_heure <= '{end_date}'")
            
        if conditions:
            courses_query += " AND " + " AND ".join(conditions)
            
        courses_query += " ORDER BY c.date_heure DESC"
        
        if limit:
            courses_query += f" LIMIT {limit}"
            
        courses_df = pd.read_sql_query(courses_query, self.engine)
        
        if courses_df.empty:
            self.logger.warning("No courses found with results")
            return pd.DataFrame()
        
        # Récupérer les participants pour ces courses
        all_participants = []
        
        for _, course in courses_df.iterrows():
            participants_query = f"""
            SELECT p.*, c.nom AS cheval_nom, c.age, c.sexe, j.nom AS jockey_nom 
            FROM participations p
            JOIN chevaux c ON p.id_cheval = c.id
            JOIN jockeys j ON p.id_jockey = j.id
            WHERE p.id_course = {course['id']}
            """
            
            participants = pd.read_sql_query(participants_query, self.engine)
            
            if not participants.empty:
                # Ajouter les infos de la course
                for col in course.index:
                    if col not in participants.columns:
                        participants[col] = course[col]
                
                all_participants.append(participants)
        
        if not all_participants:
            self.logger.warning("No participants found for the courses")
            return pd.DataFrame()
        
        # Combiner tous les participants
        training_data = pd.concat(all_participants, ignore_index=True)
        
        return training_data
    
    def create_advanced_features(self, df):
        """Crée des features avancées basées sur les données historiques"""
        self.logger.info("Creating advanced features")
        
        # Récupérer les historiques pour chaque cheval et jockey
        for index, row in df.iterrows():
            # Exclure la course actuelle pour éviter les fuites de données
            history_query = f"""
            SELECT p.position, c.date_heure, c.lieu, c.distance, c.type_course
            FROM participations p
            JOIN courses c ON p.id_course = c.id
            WHERE p.id_cheval = {row['id_cheval']}
            AND p.id_course != {row['id_course']}
            ORDER BY c.date_heure DESC
            LIMIT 10
            """
            
            history = pd.read_sql_query(history_query, self.engine)
            
            if not history.empty:
                # Calculer les features avancées de tendance
                df.at[index, 'recent_form'] = history['position'].mean()
                
                # Tendance de performance (amélioration ou dégradation)
                if len(history) >= 3:
                    recent_avg = history.iloc[:3]['position'].mean()
                    older_avg = history.iloc[3:]['position'].mean() if len(history) > 3 else None
                    
                    if older_avg and older_avg > 0:
                        df.at[index, 'trend'] = (older_avg - recent_avg) / older_avg
                    else:
                        df.at[index, 'trend'] = 0
                else:
                    df.at[index, 'trend'] = 0
                
                # Performance sur des courses similaires (même distance/type)
                similar_races = history[
                    (history['distance'] >= row['distance'] - 200) &
                    (history['distance'] <= row['distance'] + 200) &
                    (history['type_course'] == row['type_course'])
                ]
                
                if not similar_races.empty:
                    df.at[index, 'similar_races_perf'] = similar_races['position'].mean()
                else:
                    df.at[index, 'similar_races_perf'] = np.nan
                
                # Performance sur le même hippodrome
                same_venue = history[history['lieu'] == row['lieu']]
                if not same_venue.empty:
                    df.at[index, 'same_venue_perf'] = same_venue['position'].mean()
                else:
                    df.at[index, 'same_venue_perf'] = np.nan
            
            # Ajouter les features du jockey
            jockey_query = f"""
            SELECT p.position
            FROM participations p
            JOIN courses c ON p.id_course = c.id
            WHERE p.id_jockey = {row['id_jockey']}
            AND p.id_course != {row['id_course']}
            ORDER BY c.date_heure DESC
            LIMIT 50
            """
            
            jockey_history = pd.read_sql_query(jockey_query, self.engine)
            
            if not jockey_history.empty:
                df.at[index, 'jockey_recent_form'] = jockey_history.iloc[:10]['position'].mean() if len(jockey_history) >= 10 else jockey_history['position'].mean()
                df.at[index, 'jockey_win_rate'] = (jockey_history['position'] == 1).mean() * 100
            else:
                df.at[index, 'jockey_recent_form'] = np.nan
                df.at[index, 'jockey_win_rate'] = 0
        
        # Normaliser les cotes dans le contexte de la course
        if 'cote_actuelle' in df.columns:
            df['normalized_odds'] = df.groupby('id_course')['cote_actuelle'].transform(
                lambda x: x / x.mean()
            )
            
            # Rang des favoris
            df['favorite_rank'] = df.groupby('id_course')['cote_actuelle'].rank()
        
        # Compléter les valeurs manquantes
        numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
        for col in numeric_cols:
            if df[col].isna().any():
                df[col].fillna(df[col].median(), inplace=True)
        
        return df
    
    def encode_features_for_model(self, df, is_training=True):
        """Encode les features pour le ML, avec support pour l'inférence"""
        self.logger.info("Encoding features for modeling")
        
        # Colonnes catégorielles à encoder
        categorical_cols = ['sexe', 'type_course', 'lieu', 'jockey_nom']
        categorical_cols = [col for col in categorical_cols if col in df.columns]
        
        # Label Encoding pour les colonnes avec haute cardinalité
        high_cardinality = ['lieu', 'jockey_nom']
        high_cardinality = [col for col in high_cardinality if col in df.columns]
        
        for col in high_cardinality:
            if is_training or col not in self.label_encoders:
                self.label_encoders[col] = LabelEncoder()
                df[f"{col}_encoded"] = self.label_encoders[col].fit_transform(df[col])
            else:
                # Gérer les nouvelles catégories en inférence
                unseen_categories = set(df[col]) - set(self.label_encoders[col].classes_)
                if unseen_categories:
                    # Approche simple: assigner une valeur spéciale pour les catégories inconnues
                    df[f"{col}_encoded"] = df[col].apply(
                        lambda x: self.label_encoders[col].transform([x])[0] if x in self.label_encoders[col].classes_ else -1
                    )
                else:
                    df[f"{col}_encoded"] = self.label_encoders[col].transform(df[col])
        
        # One-Hot Encoding pour les colonnes à faible cardinalité
        low_cardinality = [col for col in categorical_cols if col not in high_cardinality]
        
        for col in low_cardinality:
            if is_training or col not in self.one_hot_encoders:
                self.one_hot_encoders[col] = OneHotEncoder(sparse=False, handle_unknown='ignore')
                encoded = self.one_hot_encoders[col].fit_transform(df[[col]])
                
                # Créer des colonnes pour chaque catégorie
                categories = self.one_hot_encoders[col].categories_[0]
                for i, category in enumerate(categories):
                    df[f"{col}_{category}"] = encoded[:, i]
            else:
                encoded = self.one_hot_encoders[col].transform(df[[col]])
                categories = self.one_hot_encoders[col].categories_[0]
                for i, category in enumerate(categories):
                    df[f"{col}_{category}"] = encoded[:, i]
        
        # Normalisation des features numériques
        numeric_features = [
            'age', 'poids', 'cote_actuelle', 'normalized_odds',
            'win_rate', 'place_rate', 'recent_form', 'trend',
            'jockey_win_rate', 'jockey_recent_form', 'similar_races_perf'
        ]
        
        # Ne garder que les colonnes qui existent
        numeric_features = [col for col in numeric_features if col in df.columns]
        
        if numeric_features:
            if is_training:
                normalized_features = self.scaler.fit_transform(df[numeric_features])
            else:
                normalized_features = self.scaler.transform(df[numeric_features])
            
            # Remplacer les colonnes par les versions normalisées
            for i, col in enumerate(numeric_features):
                df[f"{col}_norm"] = normalized_features[:, i]
        
        # Si en mode entraînement, sauvegarder les encodeurs
        if is_training:
            self.save_encoders()
        
        return df
    
    def prepare_data_for_simulation(self, course_id, selected_horses):
        """Prépare les données pour la simulation avec des chevaux sélectionnés par l'utilisateur"""
        self.logger.info(f"Preparing simulation data for course {course_id} with {len(selected_horses)} horses")
        
        # Récupérer les données de la course
        course_query = f"""
        SELECT * FROM courses WHERE id = {course_id}
        """
        course_data = pd.read_sql_query(course_query, self.engine)
        
        if course_data.empty:
            self.logger.error(f"Course with ID {course_id} not found")
            return None
        
        # Récupérer les participants habituels de la course
        participants_query = f"""
        SELECT p.*, c.nom AS cheval_nom, c.age, c.sexe, j.nom AS jockey_nom 
        FROM participations p
        JOIN chevaux c ON p.id_cheval = c.id
        JOIN jockeys j ON p.id_jockey = j.id
        WHERE p.id_course = {course_id}
        """
        participants = pd.read_sql_query(participants_query, self.engine)
        
        if participants.empty:
            self.logger.error(f"No participants found for course {course_id}")
            return None
        
        # Filtrer pour ne garder que les chevaux sélectionnés
        selected_participants = participants[participants['id_cheval'].isin(selected_horses)]
        
        if selected_participants.empty:
            self.logger.error("None of the selected horses are participating in this course")
            return None
        
        # Créer des features avancées
        enhanced_data = self.create_advanced_features(selected_participants)
        
        # Encoder pour le modèle (en mode inférence)
        prepared_data = self.encode_features_for_model(enhanced_data, is_training=False)
        
        return prepared_data


