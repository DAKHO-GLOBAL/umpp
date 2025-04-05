import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from sklearn.preprocessing import LabelEncoder, StandardScaler
from datetime import datetime, timedelta
import logging

class DataPreparation:
    def __init__(self, db_path='pmu_ia'):
        """Initialise la connexion à la base de données et les encodeurs."""
        self.engine = create_engine(f'mysql://root:@localhost/{db_path}')
        self.label_encoders = {}
        self.logger = logging.getLogger(__name__)
        
    def get_course_data(self, start_date=None, end_date=None, limit=None):
        """Récupère les données de courses depuis la BD avec une plage de dates optionnelle."""
        query = """
        SELECT c.*, h.lieu AS hippodrome_nom 
        FROM courses c
        """
        
        conditions = []
        if start_date:
            conditions.append(f"c.date_heure >= '{start_date}'")
        if end_date:
            conditions.append(f"c.date_heure <= '{end_date}'")
            
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
            
        query += " ORDER BY c.date_heure DESC"
        
        if limit:
            query += f" LIMIT {limit}"
            
        return pd.read_sql_query(query, self.engine)
    
    def get_participant_data(self, course_id=None):
        """Récupère les données des participants pour une course spécifique."""
        if not course_id:
            return pd.DataFrame()
            
        query = """
        SELECT p.*, c.nom AS cheval_nom, j.nom AS jockey_nom 
        FROM participations p
        JOIN chevaux c ON p.id_cheval = c.id
        JOIN jockeys j ON p.id_jockey = j.id
        WHERE p.id_course = %s
        """
        
        return pd.read_sql_query(query, self.engine, params=[course_id])
    
    def clean_data(self, df):
        """Nettoie les données en gérant les valeurs manquantes et convertissant les types."""
        self.logger.info(f"Cleaning data with shape {df.shape}")
        
        # Convertir les dates si elles sont en format string
        if 'date_heure' in df.columns and df['date_heure'].dtype == 'object':
            df['date_heure'] = pd.to_datetime(df['date_heure'])
        
        # Traiter les valeurs manquantes numériques
        numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
        for col in numeric_cols:
            df[col].fillna(df[col].median(), inplace=True)
        
        # Traiter les valeurs manquantes catégorielles
        categorical_cols = df.select_dtypes(include=['object']).columns
        for col in categorical_cols:
            df[col].fillna('Unknown', inplace=True)
            
        self.logger.info(f"Data cleaned. New shape {df.shape}")
        return df
    
    def encode_categorical_features(self, df, columns_to_encode=None):
        """Encode les features catégorielles avec LabelEncoder."""
        if columns_to_encode is None:
            columns_to_encode = df.select_dtypes(include=['object']).columns
        
        self.logger.info(f"Encoding categorical features: {columns_to_encode}")
        
        for col in columns_to_encode:
            if col not in self.label_encoders:
                self.label_encoders[col] = LabelEncoder()
                df[f"{col}_encoded"] = self.label_encoders[col].fit_transform(df[col])
            else:
                # Gérer les nouvelles catégories
                le = self.label_encoders[col]
                # Stockage des classes avant mise à jour
                old_classes = set(le.classes_)
                # Nouvelles classes dans les données actuelles
                new_classes = set(df[col].unique())
                # Classes qui n'ont pas été vues avant
                unseen_classes = new_classes - old_classes
                
                if unseen_classes:
                    # Créer un nouvel encodeur avec toutes les classes
                    new_le = LabelEncoder()
                    new_le.fit(list(old_classes) + list(unseen_classes))
                    self.label_encoders[col] = new_le
                
                # Transformer avec le nouvel encodeur ou l'ancien si pas de nouvelles classes
                df[f"{col}_encoded"] = self.label_encoders[col].transform(df[col])
                
        return df
    
    def normalize_numeric_features(self, df, columns_to_normalize=None):
        """Normalise les features numériques."""
        if columns_to_normalize is None:
            columns_to_normalize = df.select_dtypes(include=['float64', 'int64']).columns
        
        self.logger.info(f"Normalizing numeric features: {columns_to_normalize}")
        
        scaler = StandardScaler()
        df[columns_to_normalize] = scaler.fit_transform(df[columns_to_normalize])
        
        return df
    
    def create_time_features(self, df, date_column='date_heure'):
        """Crée des features temporelles à partir d'une colonne de date."""
        if date_column in df.columns and pd.api.types.is_datetime64_any_dtype(df[date_column]):
            self.logger.info(f"Creating time features from {date_column}")
            
            df['hour_of_day'] = df[date_column].dt.hour
            df['day_of_week'] = df[date_column].dt.dayofweek
            df['month'] = df[date_column].dt.month
            df['weekend'] = df[date_column].dt.dayofweek >= 5
            
            # Si c'est pour la prédiction, calculer le temps restant avant la course
            now = datetime.now()
            df['time_to_race'] = (df[date_column] - pd.Timestamp(now)).dt.total_seconds() / 3600  # en heures
            
        return df
    
    def create_participant_features(self, participants_df, course_data=None):
        """Crée des features avancées pour les participants."""
        self.logger.info("Creating participant features")
        
        if participants_df.empty:
            return participants_df
        
        # Si nous avons des données de course, fusionnons-les
        if course_data is not None and not course_data.empty:
            # La colonne de jointure est id_course dans participants et id dans course_data
            course_info = course_data[['id', 'date_heure', 'lieu', 'type_course', 'distance', 'terrain']].copy()
            course_info.rename(columns={'id': 'id_course'}, inplace=True)
            
            # Fusionner les données de course avec les participants
            participants_df = pd.merge(
                participants_df,
                course_info,
                on='id_course',
                how='left'
            )
        
        # Calculer le pourcentage de courses gagnées
        # Pour cela, nous avons besoin de l'historique des participations pour chaque cheval
        for index, participant in participants_df.iterrows():
            cheval_id = participant['id_cheval']
            
            # Récupérer l'historique des participations pour ce cheval
            historique_query = f"""
            SELECT p.position
            FROM participations p
            JOIN courses c ON p.id_course = c.id
            WHERE p.id_cheval = {cheval_id}
            """
            
            historique = pd.read_sql_query(historique_query, self.engine)
            
            if not historique.empty:
                # Calculer le taux de victoire
                victoires = len(historique[historique['position'] == 1])
                total_courses = len(historique)
                win_rate = (victoires / total_courses) * 100 if total_courses > 0 else 0
                
                # Ajouter à notre dataframe de participants
                participants_df.at[index, 'win_rate'] = win_rate
                
                # Calculer le taux de podium (top 3)
                podiums = len(historique[historique['position'] <= 3])
                place_rate = (podiums / total_courses) * 100 if total_courses > 0 else 0
                
                participants_df.at[index, 'place_rate'] = place_rate
                
                # Nombre de courses
                participants_df.at[index, 'nb_courses'] = total_courses
                
                # Calculer la moyenne des positions
                avg_position = historique['position'].mean()
                participants_df.at[index, 'avg_position'] = avg_position
                
                # Calculer les performances récentes (5 dernières courses)
                recent_query = f"""
                SELECT p.position
                FROM participations p
                JOIN courses c ON p.id_course = c.id
                WHERE p.id_cheval = {cheval_id}
                ORDER BY c.date_heure DESC
                LIMIT 5
                """
                
                recent = pd.read_sql_query(recent_query, self.engine)
                
                if not recent.empty:
                    recent_avg = recent['position'].mean()
                    participants_df.at[index, 'recent_avg_position'] = recent_avg
                else:
                    participants_df.at[index, 'recent_avg_position'] = np.nan
            
            else:
                # Pas d'historique, on met des valeurs par défaut
                participants_df.at[index, 'win_rate'] = 0
                participants_df.at[index, 'place_rate'] = 0
                participants_df.at[index, 'nb_courses'] = 0
                participants_df.at[index, 'avg_position'] = np.nan
                participants_df.at[index, 'recent_avg_position'] = np.nan
        
        # Performance des jockeys
        for index, participant in participants_df.iterrows():
            jockey_id = participant['id_jockey']
            
            # Récupérer l'historique des participations pour ce jockey
            jockey_query = f"""
            SELECT p.position
            FROM participations p
            JOIN courses c ON p.id_course = c.id
            WHERE p.id_jockey = {jockey_id}
            """
            
            jockey_hist = pd.read_sql_query(jockey_query, self.engine)
            
            if not jockey_hist.empty:
                # Calculer le taux de victoire du jockey
                jockey_wins = len(jockey_hist[jockey_hist['position'] == 1])
                jockey_races = len(jockey_hist)
                jockey_win_rate = (jockey_wins / jockey_races) * 100 if jockey_races > 0 else 0
                
                participants_df.at[index, 'jockey_win_rate'] = jockey_win_rate
                
                # Calculer le taux de podium du jockey
                jockey_podiums = len(jockey_hist[jockey_hist['position'] <= 3])
                jockey_place_rate = (jockey_podiums / jockey_races) * 100 if jockey_races > 0 else 0
                
                participants_df.at[index, 'jockey_place_rate'] = jockey_place_rate
            else:
                participants_df.at[index, 'jockey_win_rate'] = 0
                participants_df.at[index, 'jockey_place_rate'] = 0
        
        # Performances combinées cheval-jockey
        for index, participant in participants_df.iterrows():
            cheval_id = participant['id_cheval']
            jockey_id = participant['id_jockey']
            
            # Récupérer l'historique des participations pour ce couple cheval-jockey
            team_query = f"""
            SELECT p.position
            FROM participations p
            JOIN courses c ON p.id_course = c.id
            WHERE p.id_cheval = {cheval_id} AND p.id_jockey = {jockey_id}
            """
            
            team_hist = pd.read_sql_query(team_query, self.engine)
            
            if not team_hist.empty:
                # Calculer le taux de victoire de l'équipe
                team_wins = len(team_hist[team_hist['position'] == 1])
                team_races = len(team_hist)
                team_win_rate = (team_wins / team_races) * 100 if team_races > 0 else 0
                
                participants_df.at[index, 'team_win_rate'] = team_win_rate
                participants_df.at[index, 'team_races'] = team_races
            else:
                participants_df.at[index, 'team_win_rate'] = 0
                participants_df.at[index, 'team_races'] = 0
        
        # Récupérer l'âge et le sexe des chevaux
        cheval_info = pd.read_sql_query("""
            SELECT id, age, sexe 
            FROM chevaux
        """, self.engine)
        
        # Fusionner avec notre dataframe de participants
        participants_df = pd.merge(
            participants_df,
            cheval_info.rename(columns={'id': 'id_cheval'}),
            on='id_cheval',
            how='left'
        )
        
        # Facteur poids/âge (si les deux sont disponibles)
        if 'poids' in participants_df.columns and 'age' in participants_df.columns:
            participants_df['poids_age_ratio'] = participants_df['poids'] / participants_df['age']
        
        # Si nous avons des cotes, calculer des métriques basées sur les cotes
        if 'cote_actuelle' in participants_df.columns:
            # Pour chaque course, classer les chevaux par cote (rang des favoris)
            participants_df['favori_rank'] = participants_df.groupby('id_course')['cote_actuelle'].rank(method='min')
            
            # Normaliser les cotes par rapport à la moyenne de la course
            participants_df['cote_normalized'] = participants_df.groupby('id_course')['cote_actuelle'].transform(
                lambda x: x / x.mean() if x.mean() > 0 else 0
            )
        
        # Performances sur le même lieu/hippodrome
        if 'lieu' in participants_df.columns:
            for index, participant in participants_df.iterrows():
                cheval_id = participant['id_cheval']
                lieu = participant['lieu']
                
                lieu_query = f"""
                SELECT p.position
                FROM participations p
                JOIN courses c ON p.id_course = c.id
                WHERE p.id_cheval = {cheval_id} AND c.lieu = '{lieu}'
                """
                
                lieu_hist = pd.read_sql_query(lieu_query, self.engine)
                
                if not lieu_hist.empty:
                    lieu_avg = lieu_hist['position'].mean()
                    lieu_races = len(lieu_hist)
                    
                    participants_df.at[index, 'hippodrome_avg_position'] = lieu_avg
                    participants_df.at[index, 'hippodrome_races'] = lieu_races
                else:
                    participants_df.at[index, 'hippodrome_avg_position'] = np.nan
                    participants_df.at[index, 'hippodrome_races'] = 0
        
        # Performances sur distance similaire
        if 'distance' in participants_df.columns:
            for index, participant in participants_df.iterrows():
                cheval_id = participant['id_cheval']
                distance = participant['distance']
                
                # On considère une marge de ±200m comme "similaire"
                distance_min = distance - 200
                distance_max = distance + 200
                
                distance_query = f"""
                SELECT p.position
                FROM participations p
                JOIN courses c ON p.id_course = c.id
                WHERE p.id_cheval = {cheval_id} 
                AND c.distance BETWEEN {distance_min} AND {distance_max}
                """
                
                distance_hist = pd.read_sql_query(distance_query, self.engine)
                
                if not distance_hist.empty:
                    distance_avg = distance_hist['position'].mean()
                    distance_races = len(distance_hist)
                    
                    participants_df.at[index, 'distance_avg_position'] = distance_avg
                    participants_df.at[index, 'distance_races'] = distance_races
                else:
                    participants_df.at[index, 'distance_avg_position'] = np.nan
                    participants_df.at[index, 'distance_races'] = 0
        
        # Performances sur le même type de terrain
        if 'terrain' in participants_df.columns:
            for index, participant in participants_df.iterrows():
                cheval_id = participant['id_cheval']
                terrain = participant['terrain']
                
                if pd.isna(terrain) or terrain == "":
                    participants_df.at[index, 'terrain_avg_position'] = np.nan
                    participants_df.at[index, 'terrain_races'] = 0
                    continue
                
                terrain_query = f"""
                SELECT p.position
                FROM participations p
                JOIN courses c ON p.id_course = c.id
                WHERE p.id_cheval = {cheval_id} AND c.terrain = '{terrain}'
                """
                
                terrain_hist = pd.read_sql_query(terrain_query, self.engine)
                
                if not terrain_hist.empty:
                    terrain_avg = terrain_hist['position'].mean()
                    terrain_races = len(terrain_hist)
                    
                    participants_df.at[index, 'terrain_avg_position'] = terrain_avg
                    participants_df.at[index, 'terrain_races'] = terrain_races
                else:
                    participants_df.at[index, 'terrain_avg_position'] = np.nan
                    participants_df.at[index, 'terrain_races'] = 0
        
        # Remplir les valeurs manquantes
        numeric_cols = participants_df.select_dtypes(include=['float64', 'int64']).columns
        for col in numeric_cols:
            if participants_df[col].isna().any():
                participants_df[col].fillna(participants_df[col].median(), inplace=True)
        
        self.logger.info(f"Created {participants_df.shape[1]} features for participants")
        return participants_df
    
    def prepare_data_for_prediction(self, course_id=None):
        """Prépare les données pour la prédiction d'une course spécifique."""
        if not course_id:
            self.logger.error("Course ID is required for prediction")
            return None
        
        # Récupérer les informations de la course
        course_query = f"""
        SELECT * 
        FROM courses 
        WHERE id = {course_id}
        """
        
        course_data = pd.read_sql_query(course_query, self.engine)
        
        if course_data.empty:
            self.logger.error(f"No course data found for id={course_id}")
            return None
        
        # Récupérer les participants pour cette course
        participants = self.get_participant_data(course_id)
        
        if participants.empty:
            self.logger.error(f"No participants found for course id={course_id}")
            return None
        
        # Nettoyer les données
        participants = self.clean_data(participants)
        
        # Créer des features avancées
        participants = self.create_participant_features(participants, course_data)
        
        # Créer des features temporelles
        if 'date_heure' in participants.columns:
            participants = self.create_time_features(participants, 'date_heure')
        
        # Encoder les features catégorielles
        categorical_cols = [
            'cheval_nom', 'jockey_nom', 'sexe', 'statut', 
            'lieu', 'type_course', 'terrain'
        ]
        # Filtrer pour ne garder que les colonnes qui existent réellement
        categorical_cols = [col for col in categorical_cols if col in participants.columns]
        participants = self.encode_categorical_features(participants, categorical_cols)
        
        # Normaliser les features numériques
        numeric_cols = [
            'age', 'poids', 'cote_initiale', 'cote_actuelle',
            'win_rate', 'place_rate', 'nb_courses', 'avg_position',
            'recent_avg_position', 'jockey_win_rate', 'jockey_place_rate',
            'team_win_rate', 'team_races', 'distance'
        ]
        # Filtrer pour ne garder que les colonnes qui existent réellement
        numeric_cols = [col for col in numeric_cols if col in participants.columns]
        if numeric_cols:
            participants = self.normalize_numeric_features(participants, numeric_cols)
        
        self.logger.info(f"Prepared data for prediction with {participants.shape[1]} features")
        return participants
    
    def get_historical_data(self, cheval_id=None, jockey_id=None, limit=50):
        """Récupère les données historiques pour un cheval ou un jockey."""
        if cheval_id is None and jockey_id is None:
            self.logger.error("Either cheval_id or jockey_id must be provided")
            return None
        
        conditions = []
        if cheval_id is not None:
            conditions.append(f"p.id_cheval = {cheval_id}")
        if jockey_id is not None:
            conditions.append(f"p.id_jockey = {jockey_id}")
        
        where_clause = " AND ".join(conditions)
        
        query = f"""
        SELECT p.*, c.date_heure, c.lieu, c.type_course, c.distance, c.terrain,
               chev.nom AS cheval_nom, chev.age, chev.sexe,
               j.nom AS jockey_nom
        FROM participations p
        JOIN courses c ON p.id_course = c.id
        JOIN chevaux chev ON p.id_cheval = chev.id
        JOIN jockeys j ON p.id_jockey = j.id
        WHERE {where_clause}
        ORDER BY c.date_heure DESC
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        return pd.read_sql_query(query, self.engine)