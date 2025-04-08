# Architecture du système de prédiction PMU
# =======================================

# 1. TRAITEMENT DES DONNÉES
# ------------------------------

# data_preparation/enhanced_data_prep.py
# import pandas as pd
# import numpy as np
# from sqlalchemy import create_engine, text
# from sklearn.preprocessing import LabelEncoder, StandardScaler, OneHotEncoder
# from datetime import datetime, timedelta
# import logging
# import joblib
# import os
# import re

# class EnhancedDataPreparation:
#     """Version améliorée de la classe DataPreparation avec des fonctionnalités supplémentaires pour les deux modèles"""
    
#     def __init__(self, db_path='pmu_ia'):
#         """Initialise la connexion à la base de données et les encodeurs."""
#         self.engine = create_engine(f'mysql://root:@localhost/{db_path}')
#         self.label_encoders = {}
#         self.one_hot_encoders = {}
#         self.scaler = StandardScaler()
#         self.logger = logging.getLogger(__name__)
        
#         # Créer le dossier pour stocker les encodeurs
#         os.makedirs('data_preparation/encoders', exist_ok=True)
    
#     def load_encoders(self, folder_path='data_preparation/encoders'):
#         """Charge les encodeurs pré-entraînés"""
#         try:
#             if os.path.exists(f'{folder_path}/label_encoders.pkl'):
#                 self.label_encoders = joblib.load(f'{folder_path}/label_encoders.pkl')
#                 self.logger.info("Label encoders loaded successfully")
            
#             if os.path.exists(f'{folder_path}/one_hot_encoders.pkl'):
#                 self.one_hot_encoders = joblib.load(f'{folder_path}/one_hot_encoders.pkl')
#                 self.logger.info("One-hot encoders loaded successfully")
            
#             if os.path.exists(f'{folder_path}/scaler.pkl'):
#                 self.scaler = joblib.load(f'{folder_path}/scaler.pkl')
#                 self.logger.info("Scaler loaded successfully")
        
#         except Exception as e:
#             self.logger.error(f"Error loading encoders: {str(e)}")
    
#     def save_encoders(self, folder_path='data_preparation/encoders'):
#         """Sauvegarde les encodeurs entraînés"""
#         try:
#             joblib.dump(self.label_encoders, f'{folder_path}/label_encoders.pkl')
#             joblib.dump(self.one_hot_encoders, f'{folder_path}/one_hot_encoders.pkl')
#             joblib.dump(self.scaler, f'{folder_path}/scaler.pkl')
#             self.logger.info("Encoders saved successfully")
        
#         except Exception as e:
#             self.logger.error(f"Error saving encoders: {str(e)}")
    
#     def get_training_data(self, start_date=None, end_date=None, limit=None):
#         """Récupère un ensemble de données pour l'entraînement avec résultats connus"""
#         # Récupérer les courses terminées avec résultats
#         courses_query = """
#         SELECT c.*, h.libelleLong AS hippodrome_nom 
#         FROM courses c
#         LEFT JOIN pmu_hippodromes h ON c.lieu = h.libelleLong
#         WHERE c.ordreArrivee IS NOT NULL
#         """
        
#         conditions = []
#         if start_date:
#             conditions.append(f"c.date_heure >= '{start_date}'")
#         if end_date:
#             conditions.append(f"c.date_heure <= '{end_date}'")
            
#         if conditions:
#             courses_query += " AND " + " AND ".join(conditions)
            
#         courses_query += " ORDER BY c.date_heure DESC"
        
#         if limit:
#             courses_query += f" LIMIT {limit}"
            
#         courses_df = pd.read_sql_query(courses_query, self.engine)
        
#         if courses_df.empty:
#             self.logger.warning("No courses found with results")
#             return pd.DataFrame()
        
#         # Récupérer les participants pour ces courses
#         all_participants = []
        
#         for _, course in courses_df.iterrows():
#             # Requête pour obtenir toutes les données nécessaires en une seule fois
#             participants_query = f"""
#             SELECT p.*, ch.nom AS cheval_nom, ch.age, ch.sexe, ch.proprietaire, 
#                    ch.nomPere, ch.nomMere, j.nom AS jockey_nom, j.pays AS jockey_pays,
#                    c.lieu, c.type_course, c.distance, c.terrain, c.num_course, c.corde,
#                    pp.numPmu, pp.dernierRapportDirect, pp.dernierRapportReference,
#                    pp.driver, pp.musique, i.type_incident
#             FROM participations p
#             JOIN chevaux ch ON p.id_cheval = ch.id
#             JOIN jockeys j ON p.id_jockey = j.id
#             JOIN courses c ON p.id_course = c.id
#             LEFT JOIN pmu_participants pp ON (p.id_course = pp.id_course AND p.numPmu = pp.numPmu)
#             LEFT JOIN incidents i ON (i.id_course = c.id AND FIND_IN_SET(p.numPmu, i.numero_participants))
#             WHERE p.id_course = {course['id']}
#             """
            
#             participants = pd.read_sql_query(participants_query, self.engine)
            
#             if not participants.empty:
#                 # Ajouter les infos météo de la réunion si disponibles
#                 meteo_query = f"""
#                 SELECT r.temperature, r.forceVent, r.directionVent, r.nebulositeLibelleCourt
#                 FROM pmu_reunions r
#                 JOIN pmu_courses pc ON r.id = pc.reunion_id
#                 JOIN courses c ON c.pmu_course_id = pc.id
#                 WHERE c.id = {course['id']}
#                 """
                
#                 meteo_data = pd.read_sql_query(meteo_query, self.engine)
                
#                 if not meteo_data.empty:
#                     for col in meteo_data.columns:
#                         participants[col] = meteo_data.iloc[0][col]
                
#                 # Récupérer les commentaires si disponibles
#                 comments_query = f"""
#                 SELECT texte FROM commentaires_course
#                 WHERE id_course = {course['id']}
#                 """
                
#                 comments = pd.read_sql_query(comments_query, self.engine)
                
#                 if not comments.empty:
#                     participants['commentaire'] = comments.iloc[0]['texte']
                
#                 all_participants.append(participants)
        
#         if not all_participants:
#             self.logger.warning("No participants found for the courses")
#             return pd.DataFrame()
        
#         # Combiner tous les participants
#         training_data = pd.concat(all_participants, ignore_index=True)
        
#         return training_data
    
#     def parse_musique(self, musique_str):
#         """Parse la chaîne 'musique' (performances passées) en valeurs numériques"""
#         if pd.isna(musique_str) or not musique_str:
#             return []
        
#         # Extraire tous les chiffres et 'p' (positions)
#         performances = re.findall(r'(\d+|[pPaAtTdDrR])', musique_str)
        
#         # Convertir en valeurs numériques (p=0 pour les abandons, etc.)
#         numeric_values = []
#         for perf in performances[:5]:  # Limiter aux 5 dernières performances
#             if perf.isdigit():
#                 numeric_values.append(int(perf))
#             else:
#                 numeric_values.append(0)  # 0 pour les non-finishes
        
#         # Ajouter des zéros si moins de 5 performances
#         while len(numeric_values) < 5:
#             numeric_values.append(0)
        
#         return numeric_values
    
#     def create_advanced_features(self, df):
#         """Crée des features avancées basées sur les données historiques et statiques"""
#         self.logger.info(f"Creating advanced features for {len(df)} rows")
        
#         # 1. Extraire et analyser la musique (performances passées)
#         df['musique_parsed'] = df['musique'].apply(self.parse_musique)
        
#         # Créer des colonnes pour chaque position passée
#         for i in range(5):
#             df[f'perf_{i+1}'] = df['musique_parsed'].apply(
#                 lambda x: x[i] if i < len(x) else 0
#             )
        
#         # Calculer des métriques sur les performances passées
#         df['perf_mean'] = df['musique_parsed'].apply(
#             lambda x: np.mean([v for v in x if v > 0]) if any(v > 0 for v in x) else 0
#         )
        
#         df['perf_trend'] = df['musique_parsed'].apply(
#             lambda x: (np.mean([x[i] for i in range(min(2, len(x))) if x[i] > 0]) - 
#                        np.mean([x[i] for i in range(2, min(5, len(x))) if x[i] > 0]))
#             if len([v for v in x if v > 0]) >= 3 else 0
#         )
        
#         # 2. Extraire les données de cotes depuis JSON
#         if 'dernierRapportDirect' in df.columns:
#             df['cote_json'] = df['dernierRapportDirect'].apply(
#                 lambda x: float(eval(x)['rapport']) if pd.notna(x) and isinstance(x, str) and 'rapport' in eval(x) else np.nan
#             )
            
#             # Utiliser la valeur de la colonne cote_actuelle si disponible, sinon prendre la valeur du JSON
#             if 'cote_actuelle' in df.columns:
#                 df['cote_final'] = df.apply(
#                     lambda row: row['cote_actuelle'] if pd.notna(row['cote_actuelle']) else row['cote_json'], 
#                     axis=1
#                 )
#             else:
#                 df['cote_final'] = df['cote_json']
#         elif 'cote_actuelle' in df.columns:
#             df['cote_final'] = df['cote_actuelle']
        
#         # 3. Récupérer les historiques pour chaque cheval et jockey
#         for index, row in df.iterrows():
#             # Exclure la course actuelle pour éviter les fuites de données
#             history_query = f"""
#             SELECT p.position, c.date_heure, c.lieu, c.distance, c.type_course
#             FROM participations p
#             JOIN courses c ON p.id_course = c.id
#             WHERE p.id_cheval = {row['id_cheval']}
#             AND p.id_course != {row['id_course']}
#             ORDER BY c.date_heure DESC
#             LIMIT 10
#             """
            
#             history = pd.read_sql_query(history_query, self.engine)
            
#             if not history.empty:
#                 # Calculer les statistiques de performance
#                 df.at[index, 'nb_courses_total'] = len(history)
#                 df.at[index, 'win_rate'] = (history['position'] == 1).mean() * 100
#                 df.at[index, 'place_rate'] = (history['position'] <= 3).mean() * 100
#                 df.at[index, 'recent_form'] = history['position'].mean()
                
#                 # Calculer la tendance (amélioration ou dégradation)
#                 if len(history) >= 3:
#                     recent_avg = history.iloc[:3]['position'].mean()
#                     older_avg = history.iloc[3:]['position'].mean() if len(history) > 3 else None
                    
#                     if older_avg and older_avg > 0:
#                         df.at[index, 'trend'] = (older_avg - recent_avg) / older_avg
#                     else:
#                         df.at[index, 'trend'] = 0
#                 else:
#                     df.at[index, 'trend'] = 0
                
#                 # Performance sur des courses similaires (même distance/type)
#                 similar_races = history[
#                     (history['distance'] >= row['distance'] - 200) &
#                     (history['distance'] <= row['distance'] + 200) &
#                     (history['type_course'] == row['type_course'])
#                 ]
                
#                 if not similar_races.empty:
#                     df.at[index, 'similar_races_perf'] = similar_races['position'].mean()
#                     df.at[index, 'similar_races_count'] = len(similar_races)
#                 else:
#                     df.at[index, 'similar_races_perf'] = np.nan
#                     df.at[index, 'similar_races_count'] = 0
                
#                 # Performance sur le même hippodrome
#                 same_venue = history[history['lieu'] == row['lieu']]
#                 if not same_venue.empty:
#                     df.at[index, 'same_venue_perf'] = same_venue['position'].mean()
#                     df.at[index, 'same_venue_count'] = len(same_venue)
#                 else:
#                     df.at[index, 'same_venue_perf'] = np.nan
#                     df.at[index, 'same_venue_count'] = 0
#             else:
#                 # Valeurs par défaut si pas d'historique
#                 df.at[index, 'nb_courses_total'] = 0
#                 df.at[index, 'win_rate'] = 0
#                 df.at[index, 'place_rate'] = 0
#                 df.at[index, 'recent_form'] = np.nan
#                 df.at[index, 'trend'] = 0
#                 df.at[index, 'similar_races_perf'] = np.nan
#                 df.at[index, 'similar_races_count'] = 0
#                 df.at[index, 'same_venue_perf'] = np.nan
#                 df.at[index, 'same_venue_count'] = 0
            
#             # Statistiques du jockey
#             jockey_query = f"""
#             SELECT p.position
#             FROM participations p
#             JOIN courses c ON p.id_course = c.id
#             WHERE p.id_jockey = {row['id_jockey']}
#             AND p.id_course != {row['id_course']}
#             ORDER BY c.date_heure DESC
#             LIMIT 50
#             """
            
#             jockey_history = pd.read_sql_query(jockey_query, self.engine)
            
#             if not jockey_history.empty:
#                 df.at[index, 'jockey_win_rate'] = (jockey_history['position'] == 1).mean() * 100
#                 df.at[index, 'jockey_place_rate'] = (jockey_history['position'] <= 3).mean() * 100
#                 df.at[index, 'jockey_avg_position'] = jockey_history['position'].mean()
#                 df.at[index, 'jockey_races_count'] = len(jockey_history)
#             else:
#                 df.at[index, 'jockey_win_rate'] = 0
#                 df.at[index, 'jockey_place_rate'] = 0
#                 df.at[index, 'jockey_avg_position'] = np.nan
#                 df.at[index, 'jockey_races_count'] = 0
            
#             # Statistiques combinées cheval-jockey
#             team_query = f"""
#             SELECT p.position
#             FROM participations p
#             JOIN courses c ON p.id_course = c.id
#             WHERE p.id_cheval = {row['id_cheval']} 
#             AND p.id_jockey = {row['id_jockey']}
#             AND p.id_course != {row['id_course']}
#             ORDER BY c.date_heure DESC
#             """
            
#             team_history = pd.read_sql_query(team_query, self.engine)
            
#             if not team_history.empty:
#                 df.at[index, 'team_win_rate'] = (team_history['position'] == 1).mean() * 100
#                 df.at[index, 'team_races_count'] = len(team_history)
#             else:
#                 df.at[index, 'team_win_rate'] = 0
#                 df.at[index, 'team_races_count'] = 0
        
#         # 4. Normaliser les cotes dans le contexte de la course
#         if 'cote_final' in df.columns:
#             df['normalized_odds'] = df.groupby('id_course')['cote_final'].transform(
#                 lambda x: x / x.mean() if x.mean() > 0 else 1
#             )
            
#             # Rang des favoris (1 = plus basse cote = plus favorisé)
#             df['favorite_rank'] = df.groupby('id_course')['cote_final'].rank()
        
#         # 5. Features météo
#         # Convertir la nébulosité en valeur numérique
#         if 'nebulositeLibelleCourt' in df.columns:
#             nebul_mapping = {
#                 'Ensoleillé': 0,
#                 'Peu Nuageux': 1,
#                 'Partiellement Nuageux': 2, 
#                 'Nuageux': 3,
#                 'Très Nuageux': 4,
#                 'Couvert': 5,
#                 'Brouillard': 6,
#                 'Pluie Légère': 7,
#                 'Pluie': 8,
#                 'Forte Pluie': 9,
#                 'Orage': 10
#             }
            
#             df['nebulosite_num'] = df['nebulositeLibelleCourt'].map(
#                 lambda x: nebul_mapping.get(x, 5) if pd.notna(x) else 5
#             )
        
#         # 6. Traitement de l'âge et du poids
#         if 'age' in df.columns and 'poids' in df.columns:
#             df['poids_par_age'] = df['poids'] / df['age']
        
#         # 7. Distance normalisée par catégorie
#         if 'distance' in df.columns:
#             # Catégoriser les distances
#             df['distance_cat'] = pd.cut(
#                 df['distance'], 
#                 bins=[0, 1600, 2000, 2500, 3000, 10000],
#                 labels=['sprint', 'mile', 'intermediate', 'long', 'marathon']
#             )
        
#         # Compléter les valeurs manquantes
#         numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
#         for col in numeric_cols:
#             if df[col].isna().any():
#                 df[col].fillna(df[col].median(), inplace=True)
        
#         return df
    
#     def encode_features_for_model(self, df, is_training=True):
#         """Encode les features pour le ML, avec support pour l'inférence"""
#         self.logger.info("Encoding features for modeling")
        
#         # Colonnes catégorielles à encoder
#         categorical_cols = ['sexe', 'type_course', 'lieu', 'jockey_nom', 'corde', 'distance_cat']
#         categorical_cols = [col for col in categorical_cols if col in df.columns]
        
#         # Label Encoding pour les colonnes avec haute cardinalité
#         high_cardinality = ['lieu', 'jockey_nom']
#         high_cardinality = [col for col in high_cardinality if col in df.columns]
        
#         for col in high_cardinality:
#             if is_training or col not in self.label_encoders:
#                 self.label_encoders[col] = LabelEncoder()
#                 df[f"{col}_encoded"] = self.label_encoders[col].fit_transform(df[col])
#             else:
#                 # Gérer les nouvelles catégories en inférence
#                 unseen_categories = set(df[col]) - set(self.label_encoders[col].classes_)
#                 if unseen_categories:
#                     # Assigner une valeur spéciale pour les catégories inconnues
#                     df[f"{col}_encoded"] = df[col].apply(
#                         lambda x: self.label_encoders[col].transform([x])[0] if x in self.label_encoders[col].classes_ else -1
#                     )
#                 else:
#                     df[f"{col}_encoded"] = self.label_encoders[col].transform(df[col])
        
#         # One-Hot Encoding pour les colonnes à faible cardinalité
#         low_cardinality = [col for col in categorical_cols if col not in high_cardinality]
        
#         for col in low_cardinality:
#             if is_training or col not in self.one_hot_encoders:
#                 self.one_hot_encoders[col] = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
#                 encoded = self.one_hot_encoders[col].fit_transform(df[[col]])
                
#                 # Créer des colonnes pour chaque catégorie
#                 categories = self.one_hot_encoders[col].categories_[0]
#                 for i, category in enumerate(categories):
#                     df[f"{col}_{category}"] = encoded[:, i]
#             else:
#                 encoded = self.one_hot_encoders[col].transform(df[[col]])
#                 categories = self.one_hot_encoders[col].categories_[0]
#                 for i, category in enumerate(categories):
#                     df[f"{col}_{category}"] = encoded[:, i]
        
#         # Normalisation des features numériques
#         numeric_features = [
#             'age', 'poids', 'cote_final', 'normalized_odds', 'nb_courses_total',
#             'win_rate', 'place_rate', 'perf_mean', 'perf_trend', 'recent_form', 
#             'trend', 'jockey_win_rate', 'jockey_place_rate',
#             'same_venue_perf', 'similar_races_perf', 'team_win_rate'
#         ]
        
#         # Ne garder que les colonnes qui existent
#         numeric_features = [col for col in numeric_features if col in df.columns]
        
#         if numeric_features:
#             if is_training:
#                 normalized_features = self.scaler.fit_transform(df[numeric_features])
#             else:
#                 normalized_features = self.scaler.transform(df[numeric_features])
            
#             # Remplacer les colonnes par les versions normalisées
#             for i, col in enumerate(numeric_features):
#                 df[f"{col}_norm"] = normalized_features[:, i]
        
#         # Si en mode entraînement, sauvegarder les encodeurs
#         if is_training:
#             self.save_encoders()
        
#         return df
    
#     def prepare_data_for_simulation(self, course_id, selected_horses, simulation_params=None):
#         """Prépare les données pour la simulation avec des chevaux sélectionnés par l'utilisateur
        
#         Args:
#             course_id: ID de la course
#             selected_horses: liste d'IDs de chevaux sélectionnés
#             simulation_params: dictionnaire de paramètres à modifier pour la simulation
#                 ex: {'jockey_id': 10, 'poids': 500, 'meteo': 'pluie'}
#         """
#         self.logger.info(f"Preparing simulation data for course {course_id} with {len(selected_horses)} horses")
        
#         # Récupérer les données de la course
#         course_query = f"""
#         SELECT * FROM courses WHERE id = {course_id}
#         """
#         course_data = pd.read_sql_query(course_query, self.engine)
        
#         if course_data.empty:
#             self.logger.error(f"Course with ID {course_id} not found")
#             return None
        
#         # Récupérer les participants habituels de la course
#         participants_query = f"""
#         SELECT p.*, c.nom AS cheval_nom, c.age, c.sexe, j.nom AS jockey_nom 
#         FROM participations p
#         JOIN chevaux c ON p.id_cheval = c.id
#         JOIN jockeys j ON p.id_jockey = j.id
#         WHERE p.id_course = {course_id}
#         """
#         participants = pd.read_sql_query(participants_query, self.engine)
        
#         if participants.empty:
#             self.logger.error(f"No participants found for course {course_id}")
#             return None
        
#         # Filtrer pour ne garder que les chevaux sélectionnés
#         selected_participants = participants[participants['id_cheval'].isin(selected_horses)].copy()
        
#         if selected_participants.empty:
#             self.logger.error("None of the selected horses are participating in this course")
#             return None
        
#         # Appliquer les modifications de simulation si fournies
#         if simulation_params:
#             if 'jockey_id' in simulation_params:
#                 # Rechercher les informations du nouveau jockey
#                 jockey_query = f"""
#                 SELECT * FROM jockeys WHERE id = {simulation_params['jockey_id']}
#                 """
#                 jockey_data = pd.read_sql_query(jockey_query, self.engine)
                
#                 if not jockey_data.empty:
#                     # Mettre à jour les informations du jockey pour tous les chevaux sélectionnés
#                     selected_participants['id_jockey'] = simulation_params['jockey_id']
#                     selected_participants['jockey_nom'] = jockey_data.iloc[0]['nom']
            
#             if 'poids' in simulation_params:
#                 selected_participants['poids'] = simulation_params['poids']
            
#             if 'meteo' in simulation_params:
#                 # Mettre à jour les informations météo (simulées)
#                 selected_participants['nebulositeLibelleCourt'] = simulation_params['meteo']
        
#         # Créer des features avancées
#         enhanced_data = self.create_advanced_features(selected_participants)
        
#         # Encoder pour le modèle (en mode inférence)
#         prepared_data = self.encode_features_for_model(enhanced_data, is_training=False)
        
#         return prepared_data


# 2. MODÈLES DE PRÉDICTION
# ------------------------------

# model/dual_prediction_model.py
import pandas as pd
import numpy as np
import logging
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, RandomForestRegressor
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, mean_squared_error
from xgboost import XGBClassifier, XGBRanker, XGBRegressor
from lightgbm import LGBMClassifier, LGBMRanker
import joblib
import os
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
import json
from sqlalchemy import text

class DualPredictionModel:
    """Classe pour la gestion des deux types de modèles: inférence standard et simulation"""
    
    def __init__(self, base_path='model/trained_models'):
        """Initialise les deux types de modèles."""
        self.logger = logging.getLogger(__name__)
        self.base_path = base_path
        
        # Modèle pour les prédictions standard
        self.standard_model = None
        self.standard_model_type = 'xgboost'
        self.current_groups = None
        
        # Modèle pour les simulations personnalisées
        self.simulation_model = None
        self.simulation_model_type = 'xgboost_ranking'
        
        # Caractéristiques importantes
        self.feature_importances = {}
        
        # Créer le répertoire si nécessaire
        os.makedirs(base_path, exist_ok=True)
    
    def load_standard_model(self, model_path=None):
        """Charge le modèle pour les prédictions standard"""
        if model_path is None:
            model_path = f"{self.base_path}/standard_latest.pkl"
        
        try:
            self.standard_model = joblib.load(model_path)
            self.logger.info(f"Standard model loaded from {model_path}")
            
            # Charger aussi les importances de features si disponibles
            importance_path = model_path.replace('.pkl', '_importance.json')
            if os.path.exists(importance_path):
                with open(importance_path, 'r') as f:
                    self.feature_importances['standard'] = json.load(f)
            
            return True
        except Exception as e:
            self.logger.error(f"Error loading standard model: {str(e)}")
            return False
    
    def load_simulation_model(self, model_path=None):
        """Charge le modèle pour les simulations personnalisées"""
        if model_path is None:
            model_path = f"{self.base_path}/simulation_latest.pkl"
        
        try:
            self.simulation_model = joblib.load(model_path)
            self.logger.info(f"Simulation model loaded from {model_path}")
            
            # Charger aussi les importances de features si disponibles
            importance_path = model_path.replace('.pkl', '_importance.json')
            if os.path.exists(importance_path):
                with open(importance_path, 'r') as f:
                    self.feature_importances['simulation'] = json.load(f)
            
            return True
        except Exception as e:
            self.logger.error(f"Error loading simulation model: {str(e)}")
            return False
    
    def initialize_standard_model(self, model_type='xgboost'):
        """Initialise le modèle pour les prédictions standard"""
        self.standard_model_type = model_type
        
        if model_type == 'xgboost':
            self.standard_model = XGBClassifier(
                n_estimators=1500,
                max_depth=7,
                learning_rate=0.03,
                subsample=0.85,
                colsample_bytree=0.75,
                objective='binary:logistic',
                scale_pos_weight=4,
                gamma=0.5,
                min_child_weight=3,

            )

        elif model_type == 'lightgbm':
            self.standard_model = LGBMClassifier(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
                class_weight='balanced'
            )
        elif model_type == 'random_forest':
            self.standard_model = RandomForestClassifier(
                n_estimators=100,
                max_depth=None,
                min_samples_split=2,
                min_samples_leaf=1,
                n_jobs=-1,
                random_state=42,
                class_weight='balanced'
            )
        else:
            raise ValueError(f"Model type '{model_type}' not supported for standard prediction")
        
        self.logger.info(f"Initialized standard model with type {model_type}")
        return self.standard_model
    
    def initialize_simulation_model(self, model_type='xgboost_ranking'):
        """Initialise le modèle pour les simulations personnalisées"""
        self.simulation_model_type = model_type
        
        if model_type == 'xgboost_ranking':
            self.simulation_model = XGBRanker(
                n_estimators=1500,
                max_depth=9,
                learning_rate=0.03,
                subsample=0.85,
                colsample_bytree=0.75,
                objective='rank:ndcg',
                gamma=1.0,
                min_child_weight=2,
                max_delta_step=1,

            )
        elif model_type == 'xgboost_regression':
            self.simulation_model = XGBRegressor(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                subsample=0.8,
                colsample_bytree=0.8,
                objective='reg:squarederror',
                random_state=42
            )
        elif model_type == 'lightgbm_ranking':
            self.simulation_model = LGBMRanker(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42
            )
        elif model_type == 'random_forest_regression':
            self.simulation_model = RandomForestRegressor(
                n_estimators=100,
                max_depth=None,
                min_samples_split=2,
                min_samples_leaf=1,
                n_jobs=-1,
                random_state=42
            )
        else:
            raise ValueError(f"Model type '{model_type}' not supported for simulation")
        
        self.logger.info(f"Initialized simulation model with type {model_type}")
        return self.simulation_model
    
    def create_target_variables(self, df):
        """Crée différentes variables cibles pour différents objectifs de modélisation"""
        if 'position' not in df.columns:
            self.logger.error("position column not found in dataframe")
            return df
        
        # CORRECTION : Vérifier et résoudre les index dupliqués
        if df.index.duplicated().sum() > 0:
            self.logger.warning(f"Duplicated indexes found in dataframe: {df.index.duplicated().sum()}")
            df = df.reset_index(drop=True)
        
        # Pour la classification binaire (dans le top 3 ou non)
        df['target_place'] = df['position'].apply(lambda x: 1 if x <= 3 else 0)
        
        # Pour la classification binaire (gagnant ou non)
        df['target_win'] = df['position'].apply(lambda x: 1 if x == 1 else 0)
        
        # Pour le classement
        df['target_rank'] = df['position']
        
        # Pour la régression (position inversée et normalisée)
        max_position = df.groupby('id_course')['position'].transform('max')
        df['target_position_score'] = (max_position - df['position'] + 1) / max_position
        
        self.logger.info("Created multiple target variables for different modeling approaches")
        return df
    
    def calcul_top_k_accuracy(self, y_true, y_pred, k=7):
        """
        Calcule la précision des prédictions dans le top k.
        
        Args:
            y_true: Positions réelles
            y_pred: Scores prédits par le modèle
            k: Nombre de positions à considérer
            
        Returns:
            Pourcentage de chevaux correctement prédits dans le top k
        """
        # Grouper par course
        unique_groups = np.unique(self.current_groups)
        
        correct = 0
        total = 0
        
        for group in unique_groups:
            # Filtrer les données pour cette course
            mask = self.current_groups == group
            y_true_group = y_true[mask]
            y_pred_group = y_pred[mask]
            
            # Trouver les indices des k meilleurs selon la prédiction
            top_k_pred_indices = np.argsort(y_pred_group)[:k]
            
            # Trouver les indices des k meilleurs selon la vérité terrain
            top_k_true_indices = np.argsort(y_true_group)[:k]
            
            # Compter combien de chevaux sont correctement dans le top k
            correct_in_top_k = len(set(top_k_pred_indices) & set(top_k_true_indices))
            
            correct += correct_in_top_k
            total += min(k, len(top_k_true_indices))
        
        return correct / total if total > 0 else 0
    
    # def select_features(self, df, target_col, exclude_cols=None):
    #     """Sélectionne les features pertinentes pour la modélisation"""
    #     if exclude_cols is None:
    #         exclude_cols = []
            
    #     # Colonnes à exclure par défaut
    #     default_exclude = [
    #         'id', 'id_course', 'id_cheval', 'id_jockey', 'cheval_nom', 'jockey_nom',
    #         'position', 'date_heure', 'lieu', 'type_course', 'statut', 'est_forfait',
    #         'target_place', 'target_win', 'target_rank', 'target_position_score',
    #         'musique', 'musique_parsed', 'commentaire', 'dernierRapportDirect', 'dernierRapportReference'
    #     ]
        
    #     # Ne pas exclure la colonne cible
    #     exclude_cols = list(set(exclude_cols + default_exclude) - {target_col})
        
    #     # Inclure seulement les colonnes encodées et normalisées
    #     feature_cols = [col for col in df.columns if 
    #                    (col.endswith('_encoded') or 
    #                     col.endswith('_norm') or 
    #                     col.startswith('sexe_') or 
    #                     col.startswith('type_course_') or
    #                     col.startswith('corde_') or
    #                     col.startswith('distance_cat_') or
    #                     col.startswith('perf_') and col != 'perf_mean') and 
    #                    col not in exclude_cols]
        
    #     self.logger.info(f"Selected {len(feature_cols)} features for modeling")
    #     self.logger.debug("Liste exacte des features sélectionnées :")
    #     for col in sorted(feature_cols):
    #         self.logger.debug(f"- {col}")
    #     return feature_cols
    
    def train_standard_model(self, df, test_size=0.2):
        """Entraîne le modèle pour les prédictions standard (classification: dans le top 3 ou non)"""
        if self.standard_model is None:
            self.initialize_standard_model()
        
        if 'target_place' not in df.columns:
            df = self.create_target_variables(df)
        
        # CORRECTION : Réinitialiser l'index pour éviter les problèmes de duplicate labels
        df = df.reset_index(drop=True)
        
        # Sélectionner les features
        feature_cols = self.select_features(df, 'target_place')
        
        # Séparer les features et la cible
        X = df[feature_cols]
        y = df['target_place']
        X = X.fillna(X.median())



        for col in X.columns:
            if X[col].isna().any():
                median_value = X[col].median()
                if pd.isna(median_value):  # Si la médiane est aussi NaN
                    X[col] = X[col].fillna(0)
                else:
                    X[col] = X[col].fillna(median_value)

        X = X.reset_index(drop=True)
        y = y.reset_index(drop=True)
        # Diviser en ensembles d'entraînement et de test
        from sklearn.model_selection import train_test_split
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=42)
        
        # Entraîner le modèle
        self.logger.info(f"Training standard model on {len(X_train)} samples")
        self.standard_model.fit(X_train, y_train)
        
        # Évaluer le modèle
        from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
        y_pred = self.standard_model.predict(X_test)
        
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred)
        recall = recall_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred)
        
        self.logger.info(f"Standard model performance:")
        self.logger.info(f"Accuracy: {accuracy:.4f}, Precision: {precision:.4f}")
        self.logger.info(f"Recall: {recall:.4f}, F1 Score: {f1:.4f}")
        
        # Sauvegarder les importances de features
        if hasattr(self.standard_model, 'feature_importances_'):
            feature_importances = {
                feature: float(importance)
                for feature, importance in zip(feature_cols, self.standard_model.feature_importances_)
            }
            
            self.feature_importances['standard'] = feature_importances
            
            # Afficher les 10 features les plus importantes
            top_features = sorted(feature_importances.items(), key=lambda x: x[1], reverse=True)[:10]
            self.logger.info("Top 10 important features:")
            for feature, importance in top_features:
                self.logger.info(f"{feature}: {importance:.4f}")
        
        # Sauvegarder le modèle
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        model_path = f"{self.base_path}/standard_{self.standard_model_type}_{timestamp}.pkl"
        joblib.dump(self.standard_model, model_path)
        
        # Sauvegarder aussi comme "latest" pour un accès facile
        latest_path = f"{self.base_path}/standard_latest.pkl"
        joblib.dump(self.standard_model, latest_path)
        
        # Sauvegarder les importances de features si disponibles
        if 'standard' in self.feature_importances:
            importance_path = model_path.replace('.pkl', '_importance.json')
            with open(importance_path, 'w') as f:
                json.dump(self.feature_importances['standard'], f, indent=4)
            
            # Sauvegarder aussi pour "latest"
            latest_importance_path = latest_path.replace('.pkl', '_importance.json')
            with open(latest_importance_path, 'w') as f:
                json.dump(self.feature_importances['standard'], f, indent=4)
        
        # Sauvegarder les informations de performance
        model_info = {
            'model_type': self.standard_model_type,
            'accuracy': float(accuracy),
            'precision': float(precision),
            'recall': float(recall),
            'f1_score': float(f1),
            'training_size': len(X_train),
            'test_size': len(X_test),
            'timestamp': timestamp,
            'feature_count': len(feature_cols),
            'balanced': 'class_weight' in self.standard_model.get_params()
        }
        
        info_path = model_path.replace('.pkl', '_info.json')
        with open(info_path, 'w') as f:
            json.dump(model_info, f, indent=4)
        
        self.logger.info(f"Standard model saved to {model_path}")
        
        # Enregistrer dans la base de données (table model_versions)
        self._save_model_to_db('standard', model_path, model_info)
        
        return accuracy, model_path
    
    def train_simulation_model(self, df, test_size=0.2):
        """Entraîne le modèle pour les simulations personnalisées (classement des chevaux)"""
        if self.simulation_model is None:
            self.initialize_simulation_model()
        

        # Créer les variables cibles si elles n'existent pas
        if 'target_position_score' not in df.columns:
            df = self.create_target_variables(df)
        
        # CORRECTION : Réinitialiser l'index pour éviter les problèmes de duplicate labels
        df = df.reset_index(drop=True)
        
        # Sélectionner les features
        feature_cols = self.select_features(df, 'target_position_score')
        
        # Séparer les features et la cible
        X = df[feature_cols]
        
        # Remplir les valeurs manquantes
        for col in X.columns:
            if X[col].isna().any():
                X[col] = X[col].fillna(X[col].median() if not pd.isna(X[col].median()) else 0)
                
        # Réinitialiser les index pour éviter les problèmes de reindexation
        X = X.reset_index(drop=True)
        
        # Selon le type de modèle, nous utiliserons une cible différente
        if 'ranking' in self.simulation_model_type:
            # Pour les modèles de ranking, nous avons besoin des groupes (courses)
            groups = df['id_course']
            y = df['position']  # Position finale (plus petite = meilleure)
            
            # Diviser en ensembles d'entraînement et de test en préservant les groupes
            from sklearn.model_selection import GroupShuffleSplit
            gss = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=42)
            train_idx, test_idx = next(gss.split(X, y, groups))
            
            X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
            y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
            groups_train = groups.iloc[train_idx]
            groups_array = np.array([sum(groups_train == g) for g in np.unique(groups_train)])
            
            # Entraîner le modèle
            self.logger.info(f"Training simulation ranking model on {len(X_train)} samples")
            #self.simulation_model.fit(X_train, y_train, group=groups_train)
            self.simulation_model.fit(X_train, y_train, group=groups_array)
            
            # Évaluer avec des métriques spécifiques au ranking
            from sklearn.metrics import ndcg_score
            
            # Prédire sur l'ensemble de test
            test_groups = groups.iloc[test_idx]
            unique_test_groups = test_groups.unique()
            
            ndcg_scores = []
            for group in unique_test_groups:
                group_mask = test_groups == group
                X_group = X_test[group_mask]
                y_group = y_test[group_mask]
                
                if len(X_group) > 1:  # Besoin d'au moins 2 échantillons pour le ranking
                    y_pred = self.simulation_model.predict(X_group)
                    
                    # Pour ndcg_score, nous avons besoin de coder les positions en ordre inverse
                    # (plus petite position = meilleur rang = score plus élevé)
                    max_pos = y_group.max()
                    y_true_ndcg = max_pos - y_group + 1
                    
                    # Calculer le score NDCG pour ce groupe
                    try:
                        score = ndcg_score([y_true_ndcg], [y_pred])
                        ndcg_scores.append(score)
                    except:
                        pass
            
            avg_ndcg = np.mean(ndcg_scores) if ndcg_scores else 0
            self.logger.info(f"Simulation model performance (NDCG): {avg_ndcg:.4f}")
            
            # Mesure supplémentaire: Pourcentage de gagnants correctement prédits
            winners_correct = 0
            total_races = 0
            
            for group in unique_test_groups:
                group_mask = test_groups == group
                X_group = X_test[group_mask]
                y_group = y_test[group_mask]
                
                if len(X_group) > 1:
                    y_pred = self.simulation_model.predict(X_group)
                    
                    # Trouver le cheval avec le meilleur score prédit
                    best_pred_idx = np.argmin(y_pred)
                    
                    # Vérifier si c'était le gagnant réel
                    if y_group.iloc[best_pred_idx] == 1:  # Position 1 = gagnant
                        winners_correct += 1
                    
                    total_races += 1
            
            winner_accuracy = winners_correct / total_races if total_races > 0 else 0
            self.logger.info(f"Winner prediction accuracy: {winner_accuracy:.4f}")
            
            # Métriques pour l'évaluation
            metrics = {
                'ndcg_score': float(avg_ndcg),
                'winner_accuracy': float(winner_accuracy)
            }

            # Ajouter l'évaluation du top 7
            self.current_groups = groups.iloc[test_idx]  # Stocker les groupes pour l'évaluation
            top_7_accuracy = self.calcul_top_k_accuracy(y_test, y_pred, k=7)
            
            self.logger.info(f"Top-7 accuracy: {top_7_accuracy:.4f}")
            
            # Ajouter aux métriques existantes
            metrics['top_7_accuracy'] = float(top_7_accuracy)
        else:
            # Pour les modèles de régression, nous utilisons un score inversé (1.0 pour le gagnant, 0.0 pour le dernier)
            y = df['target_position_score']
            
            # Diviser en ensembles d'entraînement et de test
            from sklearn.model_selection import train_test_split
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=42)
            
            # Entraîner le modèle
            self.logger.info(f"Training simulation regression model on {len(X_train)} samples")
            self.simulation_model.fit(X_train, y_train)
            
            # Évaluer le modèle avec des métriques de régression
            from sklearn.metrics import mean_squared_error, r2_score
            y_pred = self.simulation_model.predict(X_test)
            
            mse = mean_squared_error(y_test, y_pred)
            rmse = np.sqrt(mse)
            r2 = r2_score(y_test, y_pred)
            
            self.logger.info(f"Simulation model performance:")
            self.logger.info(f"RMSE: {rmse:.4f}, R²: {r2:.4f}")
            
            # Métriques pour l'évaluation
            metrics = {
                'rmse': float(rmse),
                'r2_score': float(r2)
            }
        
        # Sauvegarder les importances de features
        if hasattr(self.simulation_model, 'feature_importances_'):
            feature_importances = {
                feature: float(importance)
                for feature, importance in zip(feature_cols, self.simulation_model.feature_importances_)
            }
            
            self.feature_importances['simulation'] = feature_importances
            
            # Afficher les 10 features les plus importantes
            top_features = sorted(feature_importances.items(), key=lambda x: x[1], reverse=True)[:10]
            self.logger.info("Top 10 important features for simulation:")
            for feature, importance in top_features:
                self.logger.info(f"{feature}: {importance:.4f}")
        
        # Sauvegarder le modèle
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        model_path = f"{self.base_path}/simulation_{self.simulation_model_type}_{timestamp}.pkl"
        joblib.dump(self.simulation_model, model_path)
        
        # Sauvegarder aussi comme "latest" pour un accès facile
        latest_path = f"{self.base_path}/simulation_latest.pkl"
        joblib.dump(self.simulation_model, latest_path)
        
        # Sauvegarder les importances de features si disponibles
        if 'simulation' in self.feature_importances:
            importance_path = model_path.replace('.pkl', '_importance.json')
            with open(importance_path, 'w') as f:
                json.dump(self.feature_importances['simulation'], f, indent=4)
            
            # Sauvegarder aussi pour "latest"
            latest_importance_path = latest_path.replace('.pkl', '_importance.json')
            with open(latest_importance_path, 'w') as f:
                json.dump(self.feature_importances['simulation'], f, indent=4)
        
        # Sauvegarder les informations de performance
        model_info = {
            'model_type': self.simulation_model_type,
            'metrics': metrics,
            'training_size': len(X_train),
            'test_size': len(X_test),
            'timestamp': timestamp,
            'feature_count': len(feature_cols)
        }
        
        info_path = model_path.replace('.pkl', '_info.json')
        with open(info_path, 'w') as f:
            json.dump(model_info, f, indent=4)
        
        self.logger.info(f"Simulation model saved to {model_path}")
        
        # Enregistrer dans la base de données (table model_versions)
        self._save_model_to_db('simulation', model_path, model_info)
        
        return metrics, model_path
    
    def _save_model_to_db(self, model_category, model_path, model_info):
        """Sauvegarde les informations du modèle dans la table model_versions"""
        try:
            from sqlalchemy.orm import sessionmaker
            from database.setup_database import engine
            import json
            
            Session = sessionmaker(bind=engine)
            session = Session()
            
            # Créer un dictionnaire pour la requête d'insertion
            query = """
            INSERT INTO model_versions (
                model_type, hyperparameters, training_date, training_duration,
                accuracy, precision_score, recall_score, f1_score, log_loss,
                file_path, training_data_range, feature_count, sample_count,
                validation_method, notes, is_active
            ) VALUES (
                :model_type, :hyperparameters, :training_date, :training_duration,
                :accuracy, :precision_score, :recall_score, :f1_score, :log_loss,
                :file_path, :training_data_range, :feature_count, :sample_count,
                :validation_method, :notes, :is_active
            )
            """
            
            # Préparer les paramètres selon le type de modèle
            params = {
                'model_type': f"{model_category}_{model_info['model_type']}",
                'hyperparameters': json.dumps(self.simulation_model.get_params() if model_category == 'simulation' else self.standard_model.get_params()),
                'training_date': datetime.now(),
                'training_duration': None,  # À calculer dans le futur
                'file_path': model_path,
                'feature_count': model_info['feature_count'],
                'sample_count': model_info['training_size'],
                'validation_method': 'train_test_split',
                'notes': f"Model trained with {model_info['feature_count']} features on {model_info['training_size']} samples.",
                'is_active': True
            }
            
            # Ajouter les métriques spécifiques à chaque type de modèle
            if model_category == 'standard':
                params.update({
                    'accuracy': model_info['accuracy'],
                    'precision_score': model_info['precision'],
                    'recall_score': model_info['recall'],
                    'f1_score': model_info['f1_score'],
                    'log_loss': None  # À calculer dans le futur
                })
            else:
                # Pour le modèle de simulation, nous stockons les métriques dans le champ 'notes'
                metrics_str = ", ".join([f"{k}: {v:.4f}" for k, v in model_info['metrics'].items()])
                params['notes'] += f" Performance metrics: {metrics_str}"
                
                # Valeurs par défaut pour les champs obligatoires
                params.update({
                    'accuracy': model_info['metrics'].get('winner_accuracy', None),
                    'precision_score': None,
                    'recall_score': None,
                    'f1_score': None,
                    'log_loss': None
                })
            
            # Désactiver tous les modèles existants de la même catégorie
            update_query = """
            UPDATE model_versions
            SET is_active = 0
            WHERE model_type LIKE :model_type_pattern
            """
            
            session.execute(update_query, {'model_type_pattern': f"{model_category}_%"})
            
            # Insérer le nouveau modèle
            session.execute(query, params)
            session.commit()
            
            self.logger.info(f"Model information saved to database for {model_category} model")
            
        except Exception as e:
            self.logger.error(f"Error saving model information to database: {str(e)}")
    
    def predict_standard(self, data, return_probabilities=True):
        """Effectue une prédiction avec le modèle standard (dans top 3 ou non)"""
        if self.standard_model is None:
            self.logger.error("Standard model not loaded")
            return None
        
        # Vérifier si les features nécessaires sont disponibles
        feature_cols = self.select_features(data, 'target_place')
        missing_features = [col for col in feature_cols if col not in data.columns]
        
        if missing_features:
            self.logger.error(f"Missing features for prediction: {missing_features}")
            return None
        
        # Prédire
        X = data[feature_cols]
        
        if return_probabilities:
            # Retourner les probabilités d'être dans le top 3
            predictions = self.standard_model.predict_proba(X)[:, 1]
        else:
            # Retourner la classe prédite (0 = pas dans top 3, 1 = dans top 3)
            predictions = self.standard_model.predict(X)
        
        # Créer un DataFrame avec les résultats
        results = pd.DataFrame({
            'id_cheval': data['id_cheval'],
            'cheval_nom': data['cheval_nom'] if 'cheval_nom' in data.columns else data['id_cheval'],
            'top3_probability': predictions if return_probabilities else None,
            'in_top3_prediction': predictions if not return_probabilities else (predictions >= 0.5).astype(int)
        })
        
        # Trier par probabilité décroissante
        results = results.sort_values('top3_probability' if return_probabilities else 'in_top3_prediction', 
                                      ascending=False).reset_index(drop=True)
        
        # Calculer le rang prédit
        results['predicted_rank'] = results.index + 1
        
        return results
    
    def predict_simulation(self, data):
        """Effectue une prédiction avec le modèle de simulation (classement complet)"""
        if self.simulation_model is None:
            self.logger.error("Simulation model not loaded")
            return None
        
        # Sélectionner les features pertinentes
        if 'ranking' in self.simulation_model_type:
            target = 'target_rank'
        else:
            target = 'target_position_score'
        
        feature_cols = self.select_features(data, target)
        missing_features = [col for col in feature_cols if col not in data.columns]
        
        if missing_features:
            self.logger.error(f"Missing features for simulation: {missing_features}")
            return None
        
        # Prédire
        X = data[feature_cols]
        predictions = self.simulation_model.predict(X)
        
        # Créer un DataFrame avec les résultats
        results = pd.DataFrame({
            'id_cheval': data['id_cheval'],
            'cheval_nom': data['cheval_nom'] if 'cheval_nom' in data.columns else data['id_cheval'],
            'predicted_score': predictions
        })
        
        # Pour les modèles de classement, une valeur plus basse est meilleure
        if 'ranking' in self.simulation_model_type:
            results = results.sort_values('predicted_score').reset_index(drop=True)
        else:
            # Pour les modèles de régression, une valeur plus haute est meilleure
            results = results.sort_values('predicted_score', ascending=False).reset_index(drop=True)
        
        # Calculer le rang prédit
        results['simulated_rank'] = results.index + 1
        
        # Ajouter les informations originales si disponibles
        for col in ['jockey_nom', 'poids', 'cote_finale', 'age']:
            if col in data.columns:
                results[col] = data.set_index('id_cheval').loc[results['id_cheval']][col].values
        
        return results
    



    def initialize_top7_simulation_model(self):
        """Initialise un modèle de simulation optimisé pour le Top 7."""
        self.simulation_model_type = 'xgboost_ranking'
        
        self.simulation_model = XGBRanker(
            n_estimators=1500,
            max_depth=7,
            learning_rate=0.03,
            subsample=0.85,
            colsample_bytree=0.75,
            objective='rank:ndcg',  # Optimisation pour le ranking
            gamma=1.0,
            min_child_weight=2,
            max_delta_step=1,
            reg_lambda=1.5,  # Utilisez reg_lambda au lieu de lambda_
            random_state=42
            # Supprimez ndcg_at s'il n'est pas supporté
        )
        
        self.logger.info(f"Initialized Top-7 simulation model with XGBoost Ranking")
        return self.simulation_model

    def train_top7_simulation_model(self, df, test_size=0.2, top_n_features=30, data_prep=None):
        """
        Entraîne le modèle de simulation optimisé pour le Top 7 avec features améliorées.
        """
        if self.simulation_model is None:
            self.initialize_top7_simulation_model()
        
        # Créer la variable cible si elle n'existe pas
        if 'position' not in df.columns:
            self.logger.error("Position column required for training simulation model")
            return None, None
        
        # Vérifier si les données sont déjà encodées
        encoded_columns = [col for col in df.columns if col.endswith('_encoded') or col.endswith('_norm')]
        if not encoded_columns and data_prep:
            self.logger.info("Encodage des données pour le modèle de simulation")
            df = data_prep.encode_features_for_model(df, is_training=False)
        
        # Utiliser la sélection améliorée de features
        feature_cols = self.select_features_enhanced(df, target_col='position')
        
        # Limiter aux top_n_features si nécessaire
        if len(feature_cols) > top_n_features:
            feature_cols = feature_cols[:top_n_features]
        
        self.logger.info(f"Training simulation model with {len(feature_cols)} features")
        
        # Séparer les features et la cible
        X = df[feature_cols]
        y = df['position']  # Position réelle (plus petite = meilleure)
        
        # Récupérer les groupes (courses)
        groups = df['id_course']
        
        # Gérer les valeurs manquantes
        for col in X.columns:
            if X[col].isna().any():
                X[col] = X[col].fillna(X[col].median() if not pd.isna(X[col].median()) else 0)
        
        # Diviser en ensembles d'entraînement et de test en préservant les groupes
        from sklearn.model_selection import GroupShuffleSplit
        gss = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=42)
        train_idx, test_idx = next(gss.split(X, y, groups))
        
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
        groups_train = groups.iloc[train_idx]
        groups_test = groups.iloc[test_idx]
        
        # Transformer les groupes en array pour XGBoost
        groups_array = np.array([sum(groups_train == g) for g in np.unique(groups_train)])
        
        # Entraîner le modèle
        self.logger.info(f"Training Top-7 simulation model on {len(X_train)} samples")
        self.simulation_model.fit(X_train, y_train, group=groups_array)
        
        # Évaluer le modèle avec des métriques pour le Top-7
        unique_test_groups = groups_test.unique()
        
        # Métriques d'évaluation
        metrics = self.evaluate_top7_performance(X_test, y_test, groups_test, unique_test_groups)
        
        # Sauvegarder les importances de features
        if hasattr(self.simulation_model, 'feature_importances_'):
            feature_importances = {
                feature: float(importance)
                for feature, importance in zip(feature_cols, self.simulation_model.feature_importances_)
            }
            
            self.feature_importances['simulation_top7'] = feature_importances
            
            # Afficher les 10 features les plus importantes
            top_features = sorted(feature_importances.items(), key=lambda x: x[1], reverse=True)[:10]
            self.logger.info("Top 10 important features for Top-7 simulation:")
            for feature, importance in top_features:
                self.logger.info(f"{feature}: {importance:.4f}")
        
        # Sauvegarder le modèle
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        model_path = f"{self.base_path}/simulation_top7_{self.simulation_model_type}_{timestamp}.pkl"
        joblib.dump(self.simulation_model, model_path)
        
        # Sauvegarder les importances de features
        if 'simulation_top7' in self.feature_importances:
            importance_path = model_path.replace('.pkl', '_importance.json')
            with open(importance_path, 'w') as f:
                json.dump(self.feature_importances['simulation_top7'], f, indent=4)
        
        # Sauvegarder les informations de performance
        model_info = {
            'model_type': self.simulation_model_type,
            'metrics': metrics,
            'training_size': len(X_train),
            'test_size': len(X_test),
            'timestamp': timestamp,
            'feature_count': len(feature_cols),
            'top7_optimized': True
        }
        
        info_path = model_path.replace('.pkl', '_info.json')
        with open(info_path, 'w') as f:
            json.dump(model_info, f, indent=4)
        
        self.logger.info(f"Top-7 simulation model saved to {model_path}")
        
        return metrics, model_path


    def evaluate_top7_performance(self, X_test, y_test, groups_test, unique_test_groups):
        """Évalue la performance du modèle pour le Top 7."""
        try:
            from sklearn.metrics import ndcg_score
            
            ndcg_scores = []
            winners_correct = 0
            top3_correct = 0
            top5_correct = 0
            top7_correct = 0
            quinte_exact_count = 0    # Cette variable était manquante
            quinte_desordre_count = 0 # Cette variable était manquante
            total_races = 0
            
            for group in unique_test_groups:
                # Filtrer pour cette course
                group_mask = groups_test == group
                X_group = X_test[group_mask].copy()
                y_group = y_test[group_mask].copy()
                
                if len(X_group) > 4:  # Besoin d'au moins 5 chevaux
                    # Prédire les positions
                    y_pred = self.simulation_model.predict(X_group)
                    
                    # Convertir en indices pour le tri
                    y_pred_with_idx = [(i, pred) for i, pred in enumerate(y_pred)]
                    y_true_with_idx = [(i, true) for i, true in enumerate(y_group)]
                    
                    # Trier par score prédit (plus petit = meilleur)
                    y_pred_sorted = sorted(y_pred_with_idx, key=lambda x: x[1])
                    y_pred_sorted_idx = [idx for idx, _ in y_pred_sorted]
                    
                    # Trier par position réelle (plus petit = meilleur)
                    y_true_sorted = sorted(y_true_with_idx, key=lambda x: x[1])
                    y_true_sorted_idx = [idx for idx, _ in y_true_sorted]
                    
                    # NDCG score pour cette course
                    try:
                        # Pour ndcg_score, inverser les positions (plus petit = meilleur)
                        max_pos = y_group.max()
                        y_true_ndcg = max_pos - y_group.values + 1  # Assurez-vous d'avoir des valeurs
                        score = ndcg_score([y_true_ndcg.tolist()], [y_pred.tolist()])
                        ndcg_scores.append(score)
                    except Exception as ndcg_error:
                        self.logger.debug(f"Erreur calcul NDCG: {ndcg_error}")
                        # Continue même si le calcul NDCG échoue
                    
                    # Vérifier si le gagnant est correctement prédit
                    if len(y_true_sorted_idx) > 0 and len(y_pred_sorted_idx) > 0:
                        if y_true_sorted_idx[0] == y_pred_sorted_idx[0]:
                            winners_correct += 1
                    
                    # Vérifier le Top 3
                    if len(y_true_sorted_idx) >= 3 and len(y_pred_sorted_idx) >= 3:
                        pred_top3 = set(y_pred_sorted_idx[:3])
                        true_top3 = set(y_true_sorted_idx[:3])
                        if len(pred_top3.intersection(true_top3)) >= 2:  # Au moins 2 sur 3 corrects
                            top3_correct += 1
                    
                    # Vérifier le Top 5 (Quinté)
                    if len(y_true_sorted_idx) >= 5 and len(y_pred_sorted_idx) >= 5:
                        pred_top5 = set(y_pred_sorted_idx[:5])
                        true_top5 = set(y_true_sorted_idx[:5])
                        if len(pred_top5.intersection(true_top5)) >= 3:  # Au moins 3 sur 5 corrects
                            top5_correct += 1
                            
                            # Quinté dans le désordre (tous les 5 chevaux sans ordre)
                            if len(pred_top5.intersection(true_top5)) == 5:
                                quinte_desordre_count += 1
                                
                                # Quinté exact (5 dans l'ordre)
                                if all(y_pred_sorted_idx[i] == y_true_sorted_idx[i] for i in range(5)):
                                    quinte_exact_count += 1
                    
                    # Vérifier le Top 7
                    if len(y_true_sorted_idx) >= 7 and len(y_pred_sorted_idx) >= 7:
                        pred_top7 = set(y_pred_sorted_idx[:7])
                        true_top7 = set(y_true_sorted_idx[:7])
                        if len(pred_top7.intersection(true_top7)) >= 4:  # Au moins 4 sur 7 corrects
                            top7_correct += 1
                    
                    total_races += 1
        
            # S'assurer que total_races n'est pas zéro pour éviter la division par zéro
            if total_races == 0:
                self.logger.warning("Aucune course valide pour l'évaluation")
                return {
                    'ndcg_score': 0.0,
                    'winner_accuracy': 0.0,
                    'top3_accuracy': 0.0,
                    'top5_accuracy': 0.0,
                    'top7_accuracy': 0.0,
                    'quinte_exact_rate': 0.0,
                    'quinte_desordre_rate': 0.0,
                    'total_races_evaluated': 0
                }
            
            # Calculer les métriques finales
            metrics = {
                'ndcg_score': float(np.mean(ndcg_scores)) if ndcg_scores else 0.0,
                'winner_accuracy': float(winners_correct / total_races),
                'top3_accuracy': float(top3_correct / total_races),
                'top5_accuracy': float(top5_correct / total_races),
                'top7_accuracy': float(top7_correct / total_races),
                'quinte_exact_rate': float(quinte_exact_count / total_races),
                'quinte_desordre_rate': float(quinte_desordre_count / total_races),
                'total_races_evaluated': total_races
            }
            
            # Afficher les métriques dans les logs
            self.logger.info(f"Résultats d'évaluation Top-7:")
            for metric, value in metrics.items():
                if isinstance(value, float):
                    self.logger.info(f"{metric}: {value:.4f}")
                else:
                    self.logger.info(f"{metric}: {value}")
            
            return metrics
        
        except Exception as e:
            self.logger.error(f"Erreur dans l'évaluation: {str(e)}")
            # Retourner des métriques par défaut en cas d'erreur
            return {
                'ndcg_score': 0.0,
                'winner_accuracy': 0.0,
                'top3_accuracy': 0.0,
                'top5_accuracy': 0.0,
                'top7_accuracy': 0.0,
                'quinte_exact_rate': 0.0,
                'quinte_desordre_rate': 0.0,
                'error': str(e),
                'total_races_evaluated': 0
            }
        
    def predict_top7(self, data):
        """
        Effectue une prédiction du Top 7 pour une course donnée.
        """
        if self.simulation_model is None:
            self.logger.error("Top-7 simulation model not loaded")
            return None
        
        # Vérifier si les features nécessaires sont disponibles
        feature_cols = set(self.feature_importances.get('simulation_top7', {}).keys())
        missing_features = [col for col in feature_cols if col not in data.columns]
        
        if missing_features and len(missing_features) > len(feature_cols) / 3:  # Si plus d'un tiers des features manquent
            self.logger.error(f"Too many missing features for Top-7 prediction: {missing_features[:10]}...")
            return None
        
        # Utiliser toutes les features disponibles
        available_features = [col for col in feature_cols if col in data.columns]
        X = data[available_features]
        
        # Remplir les valeurs manquantes
        for col in X.columns:
            if X[col].isna().any():
                X[col] = X[col].fillna(X[col].median() if not pd.isna(X[col].median()) else 0)
        
        # Prédire
        predictions = self.simulation_model.predict(X)
        
        # Créer un DataFrame avec les résultats
        results = pd.DataFrame({
            'id_cheval': data['id_cheval'],
            'cheval_nom': data['cheval_nom'] if 'cheval_nom' in data.columns else data['id_cheval'],
            'predicted_rank_score': predictions
        })
        
        # Trier par score prédit (plus petit = meilleur rang)
        results = results.sort_values('predicted_rank_score').reset_index(drop=True)
        
        # Ajouter le rang prédit (1 à n)
        results['predicted_rank'] = results.index + 1
        
        # Calculer les probabilités de finir dans le top-k
        # (Estimation basée sur un modèle de scoring)
        results['in_top1_prob'] = np.exp(-0.5 * results['predicted_rank_score'])
        results['in_top3_prob'] = np.exp(-0.2 * results['predicted_rank_score'])
        results['in_top5_prob'] = np.exp(-0.1 * results['predicted_rank_score'])
        results['in_top7_prob'] = np.exp(-0.05 * results['predicted_rank_score'])
        
        # Normaliser les probabilités
        for prob_col in ['in_top1_prob', 'in_top3_prob', 'in_top5_prob', 'in_top7_prob']:
            results[prob_col] = results[prob_col] / results[prob_col].sum()
        
        # Ajouter les informations originales si disponibles
        for col in ['jockey_nom', 'poids', 'cote_finale', 'age', 'sexe', 'musique']:
            if col in data.columns:
                results[col] = data.set_index('id_cheval').loc[results['id_cheval']][col].values
        
        # Marquer les picks pour différents types de paris
        results['tierce_pick'] = (results['predicted_rank'] <= 3).astype(int)
        results['quarte_pick'] = (results['predicted_rank'] <= 4).astype(int)
        results['quinte_pick'] = (results['predicted_rank'] <= 5).astype(int)
        results['top7_pick'] = (results['predicted_rank'] <= 7).astype(int)
        
        return results

    def train_with_enhanced_features(self, df, target_col='target_place', test_size=0.2, top_n_features=30, data_prep=None):

        """
        Entraîne le modèle avec la sélection améliorée de features.
        
        Args:
            df: DataFrame avec les données préparées
            target_col: Colonne cible (par défaut 'target_place')
            test_size: Proportion des données pour le test (par défaut 0.2)
            top_n_features: Nombre de features importantes à sélectionner (par défaut 30)
            
        Returns:
            tuple: (accuracy, model_path) pour le modèle standard
        """

        if self.standard_model is None:
            self.initialize_standard_model()
        
        # Vérifier que la variable cible existe
        if target_col not in df.columns:
            self.logger.error(f"La colonne cible {target_col} n'existe pas dans les données")
            return None, None
        
        # Vérifier si les données sont déjà encodées
        encoded_columns = [col for col in df.columns if col.endswith('_encoded') or col.endswith('_norm')]
        if not encoded_columns:
            self.logger.info("Les données ne sont pas encore encodées, application de l'encodage")
            # Vous devez avoir accès à data_prep ou implémenter l'encodage ici
            # Par exemple: df = self.data_prep.encode_features_for_model(df)
            # Si vous n'avez pas accès à data_prep, vous pouvez utiliser une approche de secours

        if data_prep and not encoded_columns:
            self.logger.info("Encodage des données avec data_prep")
            df = data_prep.encode_features_for_model(df)
        
        # Méthode de sélection de features modifiée pour s'assurer qu'elle trouve toujours quelque chose
        feature_cols = self.select_features_enhanced(df, target_col)
        
        if not feature_cols:
            self.logger.warning("Aucune feature trouvée avec la méthode habituelle, utilisation d'une méthode de secours")
            # Sélectionner toutes les colonnes numériques sauf les exclusions
            exclude_cols = ['id', 'id_course', 'id_cheval', 'id_jockey', 'position', 
                            'target_place', 'target_win', 'target_rank', 'target_position_score']
            feature_cols = [col for col in df.columns 
                            if pd.api.types.is_numeric_dtype(df[col]) and col not in exclude_cols]
        
        self.logger.info(f"Entraînement avec {len(feature_cols)} features")
        
        # Limiter aux top_n_features si nécessaire
        if len(feature_cols) > top_n_features:
            # Utiliser les top_n_features les plus importantes si disponibles
            if hasattr(self, 'feature_importances') and 'standard' in self.feature_importances:
                # Trier les features par importance
                sorted_features = sorted(
                    self.feature_importances['standard'].items(), 
                    key=lambda x: x[1], 
                    reverse=True
                )
                # Prendre les top_n_features
                feature_cols = [f for f, _ in sorted_features[:top_n_features] if f in feature_cols]
            else:
                # Sinon juste prendre les premières
                feature_cols = feature_cols[:top_n_features]
        
        # Séparer les features et la cible
        X = df[feature_cols]
        y = df[target_col]
        
        # Gérer les valeurs manquantes
        for col in X.columns:
            if X[col].isna().any():
                median_value = X[col].median()
                if pd.isna(median_value):  # Si la médiane est aussi NaN
                    X[col] = X[col].fillna(0)
                else:
                    X[col] = X[col].fillna(median_value)
        
        # Diviser en ensembles d'entraînement et de test
        from sklearn.model_selection import train_test_split
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=42)
        
        # Entraîner le modèle
        self.logger.info(f"Training enhanced model on {len(X_train)} samples with {len(feature_cols)} features")
        self.standard_model.fit(X_train, y_train)
        
        # Évaluer le modèle
        from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
        y_pred = self.standard_model.predict(X_test)
        
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred)
        recall = recall_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred)
        
        self.logger.info(f"Enhanced model performance:")
        self.logger.info(f"Accuracy: {accuracy:.4f}, Precision: {precision:.4f}")
        self.logger.info(f"Recall: {recall:.4f}, F1 Score: {f1:.4f}")
        
        # Sauvegarder les importances de features
        if hasattr(self.standard_model, 'feature_importances_'):
            feature_importances = {
                feature: float(importance)
                for feature, importance in zip(feature_cols, self.standard_model.feature_importances_)
            }
            
            self.feature_importances['enhanced'] = feature_importances
            
            # Afficher les 10 features les plus importantes
            top_features = sorted(feature_importances.items(), key=lambda x: x[1], reverse=True)[:10]
            self.logger.info("Top 10 important features with enhanced selection:")
            for feature, importance in top_features:
                self.logger.info(f"{feature}: {importance:.4f}")
        
        # Sauvegarder le modèle
        import os
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        model_path = f"{self.base_path}/enhanced_{self.standard_model_type}_{timestamp}.pkl"
        
        # Créer le répertoire si nécessaire
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        
        # Sauvegarder le modèle
        import joblib
        joblib.dump(self.standard_model, model_path)
        
        # Sauvegarder les importances de features si disponibles
        if 'enhanced' in self.feature_importances:
            import json
            importance_path = model_path.replace('.pkl', '_importance.json')
            with open(importance_path, 'w') as f:
                json.dump(self.feature_importances['enhanced'], f, indent=4)
        
        # Sauvegarder les informations de performance
        model_info = {
            'model_type': self.standard_model_type,
            'accuracy': float(accuracy),
            'precision': float(precision),
            'recall': float(recall),
            'f1_score': float(f1),
            'training_size': len(X_train),
            'test_size': len(X_test),
            'timestamp': timestamp,
            'feature_count': len(feature_cols),
            'enhanced': True
        }
        
        info_path = model_path.replace('.pkl', '_info.json')
        with open(info_path, 'w') as f:
            json.dump(model_info, f, indent=4)
        
        self.logger.info(f"Enhanced model saved to {model_path}")
        
        return accuracy, model_path
    
    def select_features_enhanced(self, df, target_col='target_place', exclude_cols=None):
        """
        Version améliorée de select_features qui utilise toutes les colonnes numériques disponibles
        """
        if exclude_cols is None:
            exclude_cols = []
            
        # Colonnes à exclure par défaut
        default_exclude = [
            'id', 'id_course', 'id_cheval', 'id_jockey', 'cheval_nom', 'jockey_nom',
            'position', 'date_heure', 'lieu', 'type_course', 'statut', 'est_forfait',
            'target_place', 'target_win', 'target_rank', 'target_position_score',  # Toutes les variables cibles
            'musique', 'musique_parsed', 'commentaire', 'dernierRapportDirect', 'dernierRapportReference'
        ]
        
        # Ne pas exclure la colonne cible
        #exclude_cols = list(set(exclude_cols + default_exclude) - {target_col})
        exclude_cols = list(set(exclude_cols + default_exclude))
        
        # Sélectionner toutes les colonnes numériques qui ne sont pas dans la liste d'exclusion
        numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
        feature_cols = [col for col in numeric_cols if col not in exclude_cols]
        
        # Ajouter également les colonnes catégorielles encodées (si elles existent)
        encoded_cols = [col for col in df.columns if 
                    (col.endswith('_encoded') or 
                        col.startswith('sexe_') or 
                        col.startswith('type_course_') or
                        col.startswith('corde_') or
                        col.startswith('distance_cat_')) and
                    col not in exclude_cols]
        
        # Combiner les deux listes de colonnes
        feature_cols = list(set(feature_cols + encoded_cols))
        
        self.logger.info(f"Selected {len(feature_cols)} features for modeling")
        #self.logger.info(f"Types of features selected: numeric={len(numeric_cols & set(feature_cols))}, encoded={len(set(encoded_cols) & set(feature_cols))}")
        self.logger.info(f"Types of features selected: numeric={len(set(numeric_cols).intersection(set(feature_cols)))}, encoded={len(set(encoded_cols).intersection(set(feature_cols)))}")
        
        if len(feature_cols) > 0:
            sample_size = min(10, len(feature_cols))
            self.logger.info(f"Sample features: {sorted(feature_cols)[:sample_size]}...")
        
        return feature_cols

# 3. ORCHESTRATION DU SYSTÈME
# ------------------------------

# orchestrator/training_orchestrator.py
# import logging
# import argparse
# from datetime import datetime, timedelta
# from data_preparation.enhanced_data_prep import EnhancedDataPreparation
# from model.dual_prediction_model import DualPredictionModel

# def train_models(days_back=180, test_size=0.2, standard_model_type='xgboost', simulation_model_type='xgboost_ranking'):
#     """Entraîne les deux modèles avec les données des derniers jours"""
#     logger = logging.getLogger(__name__)
#     logger.info(f"Starting model training with {days_back} days of data")
    
#     # Préparer les données
#     data_prep = EnhancedDataPreparation()
    
#     # Définir la période d'entraînement
#     end_date = datetime.now()
#     start_date = end_date - timedelta(days=days_back)
    
#     logger.info(f"Getting training data from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    
#     # Récupérer les données
#     training_data = data_prep.get_training_data(
#         start_date=start_date.strftime("%Y-%m-%d"),
#         end_date=end_date.strftime("%Y-%m-%d")
#     )
    
#     if training_data.empty:
#         logger.error("No training data found")
#         return False
    
#     logger.info(f"Retrieved {len(training_data)} samples for training")
    
#     # Créer des features avancées
#     enhanced_data = data_prep.create_advanced_features(training_data)
    
#     # Encoder pour le modèle
#     prepared_data = data_prep.encode_features_for_model(enhanced_data, is_training=True)
    
#     # Initialiser les modèles
#     model = DualPredictionModel()
    
#     # Entraîner le modèle standard
#     logger.info(f"Training standard model with {standard_model_type}")
#     standard_accuracy, standard_path = model.train_standard_model(prepared_data, test_size=test_size)
    
#     # Entraîner le modèle de simulation
#     logger.info(f"Training simulation model with {simulation_model_type}")
#     simulation_metrics, simulation_path = model.train_simulation_model(prepared_data, test_size=test_size)
    
#     logger.info("Model training completed")
#     logger.info(f"Standard model accuracy: {standard_accuracy:.4f}")
#     logger.info(f"Simulation model metrics: {simulation_metrics}")
    
#     return {
#         'standard_model': {
#             'accuracy': standard_accuracy,
#             'path': standard_path
#         },
#         'simulation_model': {
#             'metrics': simulation_metrics,
#             'path': simulation_path
#         }
#     }

# if __name__ == "__main__":
#     # Configurer le logging
#     logging.basicConfig(
#         level=logging.INFO,
#         format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#         filename='logs/training.log'
#     )
    
#     # Créer le parser d'arguments
#     parser = argparse.ArgumentParser(description='Train PMU prediction models')
#     parser.add_argument('--days-back', type=int, default=180, help='Number of days to use for training')
#     parser.add_argument('--standard-model', type=str, default='xgboost', choices=['xgboost', 'lightgbm', 'random_forest'], help='Model type for standard predictions')
#     parser.add_argument('--simulation-model', type=str, default='xgboost_ranking', choices=['xgboost_ranking', 'xgboost_regression', 'lightgbm_ranking', 'random_forest_regression'], help='Model type for simulations')
#     parser.add_argument('--test-size', type=float, default=0.2, help='Proportion of data to use for testing (0.0-1.0)')
    
#     args = parser.parse_args()
    
#     # Exécuter l'entraînement
#     train_models(
#         days_back=args.days_back,
#         test_size=args.test_size,
#         standard_model_type=args.standard_model,
#         simulation_model_type=args.simulation_model
#     )


# # orchestrator/prediction_orchestrator.py
# import logging
# import pandas as pd
# import json
# from datetime import datetime
# from data_preparation.enhanced_data_prep import EnhancedDataPreparation
# from model.dual_prediction_model import DualPredictionModel
# from database.database import save_prediction

# class PredictionOrchestrator:
#     """Classe pour orchestrer les prédictions de courses"""
    
#     def __init__(self):
#         self.logger = logging.getLogger(__name__)
#         self.data_prep = EnhancedDataPreparation()
#         self.model = DualPredictionModel()
        
#         # Charger les encodeurs
#         self.data_prep.load_encoders()
        
#         # Charger les modèles
#         self.model.load_standard_model()
#         self.model.load_simulation_model()
    
#     def predict_upcoming_race(self, course_id):
#         """Prédit les résultats d'une course à venir"""
#         self.logger.info(f"Predicting results for course {course_id}")
        
#         # Préparer les données pour la prédiction
#         prediction_data = self.data_prep.get_participant_data(course_id=course_id)
        
#         if prediction_data.empty:
#             self.logger.error(f"No data found for course {course_id}")
#             return None
        
#         # Créer des features avancées
#         enhanced_data = self.data_prep.create_advanced_features(prediction_data)
        
#         # Encoder pour le modèle
#         prepared_data = self.data_prep.encode_features_for_model(enhanced_data, is_training=False)
        
#         # Faire la prédiction standard
#         standard_predictions = self.model.predict_standard(prepared_data)
        
#         if standard_predictions is None:
#             self.logger.error(f"Failed to make standard prediction for course {course_id}")
#             return None
        
#         # Fusionner les informations originales importantes
#         for col in ['jockey_nom', 'poids', 'cote_actuelle', 'age']:
#             if col in prediction_data.columns:
#                 standard_predictions[col] = prediction_data.set_index('id_cheval').loc[standard_predictions['id_cheval']][col].values
        
#         # Sauvegarder les prédictions dans la base de données
#         self._save_prediction_to_db(course_id, standard_predictions)
        
#         return standard_predictions
    
#     def simulate_race(self, course_id, selected_horses, simulation_params=None):
#         """Simule une course avec des paramètres personnalisés"""
#         self.logger.info(f"Simulating race {course_id} with {len(selected_horses)} horses")
        
#         # Préparer les données pour la simulation
#         simulation_data = self.data_prep.prepare_data_for_simulation(
#             course_id, selected_horses, simulation_params
#         )
        
#         if simulation_data is None:
#             self.logger.error(f"Failed to prepare simulation data for course {course_id}")
#             return None
        
#         # Faire la prédiction de simulation
#         simulation_results = self.model.predict_simulation(simulation_data)
        
#         if simulation_results is None:
#             self.logger.error(f"Failed to simulate race {course_id}")
#             return None
        
#         # Ajouter des métadonnées de simulation
#         simulation_results['simulation_params'] = str(simulation_params)
#         simulation_results['simulation_timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
#         # Sauvegarder dans la base de données (table simulations)
#         self._save_simulation_to_db(course_id, simulation_results, selected_horses, simulation_params)
        
#         return simulation_results
    
#     def _save_prediction_to_db(self, course_id, predictions):
#         """Sauvegarde les prédictions dans la base de données"""
#         try:
#             # Convertir en format JSON
#             predictions_json = predictions.to_json(orient='records')
            
#             # Calculer un score de confiance (moyenne des probabilités top3)
#             confidence = predictions['top3_probability'].mean()
            
#             # Sauvegarder dans la base de données
#             save_prediction(course_id, predictions_json, confidence)
            
#             self.logger.info(f"Prediction saved to database for course {course_id}")
            
#         except Exception as e:
#             self.logger.error(f"Error saving prediction to database: {str(e)}")
    
#     def _save_simulation_to_db(self, course_id, results, selected_horses, simulation_params):
#         """Sauvegarde les résultats de simulation dans la base de données"""
#         try:
#             from sqlalchemy.orm import sessionmaker
#             from database.setup_database import engine, Simulation
            
#             Session = sessionmaker(bind=engine)
#             session = Session()
            
#             # Convertir les résultats en JSON
#             results_json = results.to_json(orient='records')
            
#             # Créer un nouvel enregistrement de simulation
#             simulation = Simulation(
#                 utilisateur_id=1,  # À remplacer par l'ID utilisateur réel
#                 date_simulation=datetime.now(),
#                 id_course=course_id,
#                 chevaux_selectionnes=json.dumps(selected_horses),
#                 resultat_simule=results_json
#             )
            
#             session.add(simulation)
#             session.commit()
            
#             self.logger.info(f"Simulation saved to database for course {course_id}")
            
#         except Exception as e:
#             self.logger.error(f"Error saving simulation to database: {str(e)}")




# # 5. API DE PRÉDICTION
# # ------------------------------

# # api/prediction_api.py
# from flask import Flask, request, jsonify
# import logging
# from orchestrator.prediction_orchestrator import PredictionOrchestrator

# app = Flask(__name__)

# # Configurer le logging
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#     handlers=[
#         logging.FileHandler('logs/api.log'),
#         logging.StreamHandler()
#     ]
# )

# logger = logging.getLogger(__name__)

# # Initialiser l'orchestrateur de prédictions
# orchestrator = PredictionOrchestrator()

# @app.route('/predict/<int:course_id>', methods=['GET'])
# def predict_race(course_id):
#     """Endpoint pour prédire une course"""
#     logger.info(f"Prediction request for course {course_id}")
    
#     try:
#         predictions = orchestrator.predict_upcoming_race(course_id)
        
#         if predictions is None:
#             return jsonify({'error': 'Failed to make prediction'}), 500
        
#         # Convertir le DataFrame en dictionnaire
#         predictions_dict = predictions.to_dict(orient='records')
        
#         return jsonify({
#             'course_id': course_id,
#             'predictions': predictions_dict,
#             'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
#         })
    
#     except Exception as e:
#         logger.error(f"Error in prediction: {str(e)}")
#         return jsonify({'error': str(e)}), 500

# @app.route('/simulate/<int:course_id>', methods=['POST'])
# def simulate_race(course_id):
#     """Endpoint pour simuler une course avec des paramètres personnalisés"""
#     logger.info(f"Simulation request for course {course_id}")
    
#     try:
#         # Récupérer les paramètres de la requête
#         data = request.json
#         selected_horses = data.get('selected_horses', [])
#         simulation_params = data.get('simulation_params', {})
        
#         if not selected_horses:
#             return jsonify({'error': 'No horses selected for simulation'}), 400
        
#         # Lancer la simulation
#         simulation_results = orchestrator.simulate_race(
#             course_id, selected_horses, simulation_params
#         )
        
#         if simulation_results is None:
#             return jsonify({'error': 'Failed to simulate race'}), 500
        
#         # Convertir le DataFrame en dictionnaire
#         results_dict = simulation_results.to_dict(orient='records')
        
#         return jsonify({
#             'course_id': course_id,
#             'selected_horses': selected_horses,
#             'simulation_params': simulation_params,
#             'results': results_dict,
#             'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
#         })
    
#     except Exception as e:
#         logger.error(f"Error in simulation: {str(e)}")
#         return jsonify({'error': str(e)}), 500

# if __name__ == '__main__':
#     logger.info("Starting prediction API")
#     app.run(debug=True)