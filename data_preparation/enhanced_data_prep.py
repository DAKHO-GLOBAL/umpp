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
        """Récupère un ensemble de données pour l'entraînement avec résultats connus et données enrichies"""
        # Récupérer les courses terminées qui ont un lien avec pmu_courses
        courses_query = """
        SELECT 
            c.*, 
            h.libelleLong AS hippodrome_nom, 
            pc.ordreArrivee as pmu_ordreArrivee,
            pc.id as pmu_course_id
        FROM courses c
        LEFT JOIN pmu_hippodromes h ON c.lieu = h.libelleLong
        INNER JOIN pmu_courses pc ON c.pmu_course_id = pc.id
        WHERE pc.ordreArrivee IS NOT NULL
        """
        
        # Ajouter les conditions de date si spécifiées
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
        
        # Vérifier si nous avons trouvé des courses
        if courses_df.empty:
            self.logger.warning("Aucune course trouvée avec les critères spécifiés")
            return pd.DataFrame()
        
        # Récupérer les participants pour ces courses avec les données enrichies
        # Récupérer les participants pour ces courses avec les données enrichies
        all_participants = []
        
        for _, course in courses_df.iterrows():
            # Requête pour récupérer les données de participations
            participants_query = f"""
            SELECT 
                p.*,
                c.nom AS cheval_nom, 
                c.age, 
                c.sexe, 
                j.nom AS jockey_nom
            FROM participations p
            JOIN chevaux c ON p.id_cheval = c.id
            JOIN jockeys j ON p.id_jockey = j.id
            WHERE p.id_course = {course['id']}
            """
            
            participants = pd.read_sql_query(participants_query, self.engine)
            
            # Si des participants ont été trouvés, récupérer les données complémentaires de pmu_participants
            if not participants.empty:
                # CORRECTION: S'assurer que l'index est réinitialisé avant d'ajouter des colonnes
                participants = participants.reset_index(drop=True)
                
                # Ajouter les infos de la course
                for col in course.index:
                    if col not in participants.columns:
                        # Utiliser une méthode plus sûre pour assigner des valeurs scalaires
                        participants[col] = [course[col]] * len(participants)
                
                
                # Pour chaque participant, récupérer les données de pmu_participants
                pmu_course_id = course['pmu_course_id'] if 'pmu_course_id' in course.index else None
                if pmu_course_id is not None:
                    # Vérifier que pmu_course_id est bien un entier ou une valeur simple
                    if isinstance(pmu_course_id, (int, float, str)) and not pd.isna(pmu_course_id):
                        # Convertir en entier si c'est une valeur numérique
                        pmu_course_id_value = int(pmu_course_id)
                        
                        for idx, participant in participants.iterrows():
                            if 'numPmu' in participant and not pd.isna(participant['numPmu']):
                                # Assurez-vous également que numPmu est un entier
                                numPmu_value = int(participant['numPmu'])
                                
                                pmu_participant_query = f"""
                                SELECT 
                                    musique,
                                    handicapPoids,
                                    incident,
                                    dernierRapportDirect,
                                    dernierRapportReference,
                                    entraineur
                                FROM pmu_participants
                                WHERE id_course = {pmu_course_id_value} AND numPmu = {numPmu_value}
                                LIMIT 1
                                """
                                
                                pmu_participant = pd.read_sql_query(pmu_participant_query, self.engine)
                                
                                if not pmu_participant.empty:
                                    for col in pmu_participant.columns:
                                        participants.at[idx, col] = pmu_participant.iloc[0][col]
                
                all_participants.append(participants)
        
        if not all_participants:
            return pd.DataFrame()
        
        # Combiner tous les participants
        training_data = pd.concat(all_participants, ignore_index=True)
        
        # CORRECTION: S'assurer que l'index est réinitialisé avant de retourner
        training_data = training_data.reset_index(drop=True)
        
        return training_data
    


    def _extract_rapport_from_json(self, json_str):
        """Extrait le rapport (cote) à partir d'une chaîne JSON"""
        if pd.isna(json_str) or not json_str:
            return None
        
        try:
            # Si c'est déjà un dictionnaire
            if isinstance(json_str, dict):
                data = json_str
            else:
                # Sinon, tenter de parser le JSON
                import json
                data = json.loads(json_str)
            
            # Extraire le rapport s'il existe
            if 'rapport' in data:
                return float(data['rapport'])
            
            return None
        except:
            return None

    def _calculate_trend(self, performances):
        """Calcule la tendance entre les performances récentes et anciennes"""
        if len(performances) < 3:
            return np.nan
        
        # Ne prendre que les valeurs valides (courses terminées)
        valid_perfs = [p for p in performances if p > 0]
        if len(valid_perfs) < 3:
            return np.nan
        
        # Diviser en performances récentes et anciennes
        mid_point = len(valid_perfs) // 2
        recent = valid_perfs[:mid_point]
        old = valid_perfs[mid_point:]
        
        if not recent or not old:
            return np.nan
        
        recent_avg = np.mean(recent)
        old_avg = np.mean(old)
        
        # Calculer la tendance (amélioration = positive, dégradation = négative)
        # Remarque: pour les positions, un chiffre plus bas est meilleur
        if old_avg > 0:
            return (old_avg - recent_avg) / old_avg
        
        return np.nan


    
    def create_enhanced_features(self, df):
        """
        Crée des features avancées en exploitant pleinement les données riches disponibles
        dans les tables PMU.
        """
        self.logger.info(f"Creating enhanced features for {len(df)} rows")
        
        # 1. Traitement de la musique (historique des performances)
        if 'musique' in df.columns:
            df['musique_parsed'] = df['musique'].apply(self._parse_musique)
            
            # Calculer des statistiques sur la musique
            df['musique_win_count'] = df['musique_parsed'].apply(
                lambda x: sum(1 for perf in x if perf == 1)
            )
            df['musique_place_count'] = df['musique_parsed'].apply(
                lambda x: sum(1 for perf in x if 1 <= perf <= 3)
            )
            df['musique_disqualified'] = df['musique_parsed'].apply(
                lambda x: 'a' in str(x).lower() or 'd' in str(x).lower()
            ).astype(int)
            
            # Extraire la tendance récente (3 dernières performances)
            df['recent_trend'] = df['musique_parsed'].apply(
                lambda x: sum(x[:3]) / len(x[:3]) if len(x) >= 3 and all(isinstance(p, int) and p > 0 for p in x[:3]) else None
            )
            
            # Régularité (écart-type des performances)
            df['performance_consistency'] = df['musique_parsed'].apply(
                lambda x: np.std([p for p in x if isinstance(p, int) and p > 0]) if len([p for p in x if isinstance(p, int) and p > 0]) >= 3 else None
            )
        
        # 2. Exploitation des données de lignée
        parent_stats = {}
        for index, row in df.iterrows():
            if 'nomPere' in df.columns and pd.notna(row['nomPere']):
                # Statistiques du père
                pere = row['nomPere']
                if pere not in parent_stats:
                    # Rechercher les performances des progénitures du père
                    query = f"""
                    SELECT p.position
                    FROM participations p
                    JOIN chevaux c ON p.id_cheval = c.id
                    WHERE c.nomPere = '{pere}'
                    """
                    pere_stats = pd.read_sql_query(query, self.engine)
                    if not pere_stats.empty:
                        parent_stats[pere] = {
                            'win_rate': (pere_stats['position'] == 1).mean() * 100,
                            'place_rate': (pere_stats['position'] <= 3).mean() * 100,
                            'avg_position': pere_stats['position'].mean(),
                            'count': len(pere_stats)
                        }
                    else:
                        parent_stats[pere] = {'win_rate': None, 'place_rate': None, 'avg_position': None, 'count': 0}
                
                # Ajouter les stats du père
                if parent_stats[pere]['count'] > 5:  # Seuil minimum pour la fiabilité
                    df.at[index, 'pere_win_rate'] = parent_stats[pere]['win_rate']
                    df.at[index, 'pere_place_rate'] = parent_stats[pere]['place_rate']
                    df.at[index, 'pere_avg_position'] = parent_stats[pere]['avg_position']
                
        # 3. Utilisation des données d'incidents
        if 'incident' in df.columns:
            # Convertir en variable binaire
            df['had_incident'] = df['incident'].notna() & (df['incident'] != '')
            df['had_incident'] = df['had_incident'].astype(int)
            
            # Catégoriser les types d'incidents
            incident_types = ['disqualifie', 'arrete', 'tombe', 'refuse', 'gene']
            for inc_type in incident_types:
                df[f'incident_{inc_type}'] = df['incident'].str.contains(
                    inc_type, case=False, na=False
                ).astype(int)
                
            # Historique d'incidents
            for index, row in df.iterrows():
                if 'id_cheval' in df.columns:
                    # Calculer le nombre d'incidents passés pour ce cheval
                    query = f"""
                    SELECT COUNT(*) as incident_count
                    FROM pmu_participants
                    WHERE id_cheval = {row['id_cheval']} AND incident IS NOT NULL AND incident != ''
                    """
                    incident_history = pd.read_sql_query(query, self.engine)
                    if not incident_history.empty:
                        df.at[index, 'past_incidents_count'] = incident_history.iloc[0]['incident_count']
                    else:
                        df.at[index, 'past_incidents_count'] = 0
        
        # 4. Exploitation des données météorologiques
        if 'id_course' in df.columns:
            for index, row in df.iterrows():
                # Récupérer les données météo de la réunion
                query = f"""
                SELECT r.temperature, r.forceVent, r.directionVent, r.nebulositeLibelleCourt
                FROM pmu_reunions r
                JOIN pmu_courses pc ON r.id = pc.reunion_id
                WHERE pc.id = {row['id_course']}
                """
                meteo_data = pd.read_sql_query(query, self.engine)
                
                if not meteo_data.empty:
                    df.at[index, 'temperature'] = meteo_data.iloc[0]['temperature']
                    df.at[index, 'force_vent'] = meteo_data.iloc[0]['forceVent']
                    df.at[index, 'meteo_code'] = self._encode_meteo(meteo_data.iloc[0]['nebulositeLibelleCourt'])
                    
                    # Performance historique dans des conditions similaires
                    if 'id_cheval' in df.columns:
                        meteo_condition = meteo_data.iloc[0]['nebulositeLibelleCourt']
                        query_similar_meteo = f"""
                        SELECT p.position
                        FROM participations p
                        JOIN courses c ON p.id_course = c.id
                        JOIN pmu_courses pc ON c.pmu_course_id = pc.id
                        JOIN pmu_reunions r ON pc.reunion_id = r.id
                        WHERE p.id_cheval = {row['id_cheval']}
                        AND r.nebulositeLibelleCourt = '{meteo_condition}'
                        AND p.id_course != {row['id_course']}
                        """
                        similar_meteo_perf = pd.read_sql_query(query_similar_meteo, self.engine)
                        if not similar_meteo_perf.empty:
                            df.at[index, 'similar_weather_perf'] = similar_meteo_perf['position'].mean()
                            df.at[index, 'similar_weather_count'] = len(similar_meteo_perf)
        
        # 5. Statistiques des entraîneurs
        if 'entraineur' in df.columns:
            entraineur_stats = {}
            for index, row in df.iterrows():
                entraineur = row['entraineur']
                if pd.notna(entraineur) and entraineur not in entraineur_stats:
                    query = f"""
                    SELECT p.position
                    FROM pmu_participants p
                    WHERE p.entraineur = '{entraineur}'
                    """
                    trainer_results = pd.read_sql_query(query, self.engine)
                    if not trainer_results.empty:
                        entraineur_stats[entraineur] = {
                            'win_rate': (trainer_results['position'] == 1).mean() * 100,
                            'place_rate': (trainer_results['position'] <= 3).mean() * 100,
                            'avg_position': trainer_results['position'].mean(),
                            'count': len(trainer_results)
                        }
                    else:
                        entraineur_stats[entraineur] = {'win_rate': None, 'place_rate': None, 'avg_position': None, 'count': 0}
                
                # Ajouter les stats de l'entraîneur
                if pd.notna(entraineur) and entraineur_stats[entraineur]['count'] > 0:
                    df.at[index, 'entraineur_win_rate'] = entraineur_stats[entraineur]['win_rate']
                    df.at[index, 'entraineur_place_rate'] = entraineur_stats[entraineur]['place_rate']
                    df.at[index, 'entraineur_avg_position'] = entraineur_stats[entraineur]['avg_position']
        
        # 6. Exploitation des données de propriétaires
        if 'proprietaire' in df.columns:
            proprietaire_stats = {}
            for index, row in df.iterrows():
                proprietaire = row['proprietaire']
                if pd.notna(proprietaire) and proprietaire not in proprietaire_stats:
                    query = f"""
                    SELECT p.position
                    FROM participations p
                    JOIN chevaux c ON p.id_cheval = c.id
                    WHERE c.proprietaire = '{proprietaire}'
                    """
                    owner_results = pd.read_sql_query(query, self.engine)
                    if not owner_results.empty:
                        proprietaire_stats[proprietaire] = {
                            'win_rate': (owner_results['position'] == 1).mean() * 100,
                            'place_rate': (owner_results['position'] <= 3).mean() * 100,
                            'count': len(owner_results)
                        }
                    else:
                        proprietaire_stats[proprietaire] = {'win_rate': None, 'place_rate': None, 'count': 0}
                
                # Ajouter les stats du propriétaire
                if pd.notna(proprietaire) and proprietaire_stats[proprietaire]['count'] > 0:
                    df.at[index, 'proprietaire_win_rate'] = proprietaire_stats[proprietaire]['win_rate']
                    df.at[index, 'proprietaire_place_rate'] = proprietaire_stats[proprietaire]['place_rate']
        
        # 7. Analyse détaillée des cotes et leur évolution
        if 'dernierRapportDirect' in df.columns and 'dernierRapportReference' in df.columns:
            # Extraire les cotes des données JSON
            df['cote_finale'] = df['dernierRapportDirect'].apply(self._extract_cote)
            df['cote_initiale'] = df['dernierRapportReference'].apply(self._extract_cote)
            
            # Calculer la variation des cotes
            df['cote_variation_pct'] = df.apply(
                lambda row: ((row['cote_finale'] - row['cote_initiale']) / row['cote_initiale'] * 100) 
                if pd.notna(row['cote_finale']) and pd.notna(row['cote_initiale']) and row['cote_initiale'] > 0 
                else 0,
                axis=1
            )
            
            # Identifier les chevaux dont la cote a significativement baissé (soutenus par le marché)
            df['market_support'] = (df['cote_variation_pct'] < -10).astype(int)
            
            # Normaliser les cotes par rapport à la course
            df['cote_finale_normalized'] = df.groupby('id_course')['cote_finale'].transform(
                lambda x: x / x.mean() if x.mean() > 0 else 1
            )
            
            # Rang de favoris basé sur les cotes finales
            df['favorite_rank'] = df.groupby('id_course')['cote_finale'].rank(method='min')
        
        # 8. Exploitation des données de handicap/poids
        if 'handicapPoids' in df.columns:
            # Normalisation du poids dans chaque course
            df['poids_norm_course'] = df.groupby('id_course')['handicapPoids'].transform(
                lambda x: (x - x.mean()) / x.std() if x.std() > 0 else 0
            )
            
            # Ratio poids/âge
            if 'age' in df.columns:
                df['poids_age_ratio'] = df['handicapPoids'] / df['age']
        
        # 9. Utilisation des temps/vitesses antérieurs
        if 'id_cheval' in df.columns:
            for index, row in df.iterrows():
                # Récupérer les temps précédents
                query = f"""
                SELECT tempsObtenu, reductionKilometrique, p.distance
                FROM pmu_participants pp
                JOIN pmu_courses p ON pp.id_course = p.id
                WHERE pp.cheval_id = {row['id_cheval']}
                AND pp.tempsObtenu IS NOT NULL
                """
                temps_data = pd.read_sql_query(query, self.engine)
                
                if not temps_data.empty:
                    # Vitesse moyenne (m/s)
                    temps_data['vitesse'] = temps_data.apply(
                        lambda x: x['distance'] / (x['tempsObtenu']/1000) if pd.notna(x['tempsObtenu']) and x['tempsObtenu'] > 0 else None,
                        axis=1
                    )
                    
                    df.at[index, 'avg_speed'] = temps_data['vitesse'].mean()
                    df.at[index, 'max_speed'] = temps_data['vitesse'].max()
                    
                    # Réduction kilométrique moyenne
                    if 'reductionKilometrique' in temps_data.columns:
                        df.at[index, 'avg_reduction_km'] = temps_data['reductionKilometrique'].mean()
        
        # 10. Caractéristiques spécifiques des courses
        if 'id_course' in df.columns:
            for index, row in df.iterrows():
                # Récupérer les détails de la course
                query = f"""
                SELECT specialite AS type_course, montantPrix, categorieParticularite
                FROM pmu_courses
                WHERE id = {row['id_course']}
                """
                course_details = pd.read_sql_query(query, self.engine)
                if not course_details.empty:
                    # Catégoriser le niveau de prix
                    if 'montantPrix' in course_details.columns:
                        prix = course_details.iloc[0]['montantPrix']
                        if pd.notna(prix):
                            df.at[index, 'prize_category'] = self._categorize_prize(prix)
                    
                    # Performance dans des courses similaires
                    if 'type_course' in course_details.columns and 'id_cheval' in df.columns:
                        course_type = course_details.iloc[0]['type_course']
                        if pd.notna(course_type):
                            query_similar_type = f"""
                            SELECT p.position
                            FROM participations p
                            JOIN courses c ON p.id_course = c.id
                            WHERE p.id_cheval = {row['id_cheval']}
                            AND c.type_course = '{course_type}'
                            AND p.id_course != {row['id_course']}
                            """
                            similar_course_perf = pd.read_sql_query(query_similar_type, self.engine)
                            if not similar_course_perf.empty:
                                df.at[index, 'similar_course_type_perf'] = similar_course_perf['position'].mean()
                                df.at[index, 'similar_course_type_count'] = len(similar_course_perf)
        # 11. Combinaison jockey-cheval (compatibilité)
        if 'id_cheval' in df.columns and 'id_jockey' in df.columns:
            for index, row in df.iterrows():
                # Récupérer l'historique des performances avec ce jockey
                query = f"""
                SELECT p.position
                FROM participations p
                WHERE p.id_cheval = {row['id_cheval']}
                AND p.id_jockey = {row['id_jockey']}
                AND p.id_course != {row['id_course']}
                """
                jockey_cheval_perf = pd.read_sql_query(query, self.engine)
                
                if not jockey_cheval_perf.empty:
                    df.at[index, 'jockey_cheval_win_rate'] = (jockey_cheval_perf['position'] == 1).mean() * 100
                    df.at[index, 'jockey_cheval_place_rate'] = (jockey_cheval_perf['position'] <= 3).mean() * 100
                    df.at[index, 'jockey_cheval_avg_position'] = jockey_cheval_perf['position'].mean()
                    df.at[index, 'jockey_cheval_count'] = len(jockey_cheval_perf)
        
        # 12. Analyse des commentaires de course (si disponibles)
        if 'id_course' in df.columns:
            for index, row in df.iterrows():
                # Vérifier s'il y a des commentaires pour des courses précédentes avec ce cheval
                if 'id_cheval' in df.columns:
                    query = f"""
                    SELECT cc.texte
                    FROM commentaires_course cc
                    JOIN pmu_courses pc ON cc.id_course = pc.id
                    JOIN participations p ON p.id_course = pc.id
                    WHERE p.id_cheval = {row['id_cheval']}
                    AND cc.id_course != {row['id_course']}
                    ORDER BY pc.heureDepart DESC
                    LIMIT 5
                    """
                    commentaires = pd.read_sql_query(query, self.engine)
                    
                    if not commentaires.empty:
                        # Analyse de sentiment simple des commentaires
                        positive_keywords = ['bien', 'facilité', 'puissance', 'vite', 'énergie', 'fort', 'dominant']
                        negative_keywords = ['fatigue', 'difficulté', 'lent', 'effort', 'peine', 'déception']
                        
                        positive_score = 0
                        negative_score = 0
                        
                        for _, comment_row in commentaires.iterrows():
                            comment = comment_row['texte']
                            if pd.notna(comment):
                                for keyword in positive_keywords:
                                    if keyword.lower() in comment.lower():
                                        positive_score += 1
                                for keyword in negative_keywords:
                                    if keyword.lower() in comment.lower():
                                        negative_score += 1
                        
                        df.at[index, 'comment_sentiment'] = positive_score - negative_score
        
        # 13. Performance sur la distance
        if 'id_cheval' in df.columns and 'distance' in df.columns:
            for index, row in df.iterrows():
                current_distance = row['distance']
                # Trouver des courses similaires en distance (± 200m)
                query = f"""
                SELECT p.position
                FROM participations p
                JOIN courses c ON p.id_course = c.id
                WHERE p.id_cheval = {row['id_cheval']}
                AND c.distance BETWEEN {current_distance - 200} AND {current_distance + 200}
                AND p.id_course != {row['id_course']}
                """
                similar_distance_perf = pd.read_sql_query(query, self.engine)
                
                if not similar_distance_perf.empty:
                    df.at[index, 'distance_win_rate'] = (similar_distance_perf['position'] == 1).mean() * 100
                    df.at[index, 'distance_place_rate'] = (similar_distance_perf['position'] <= 3).mean() * 100
                    df.at[index, 'distance_avg_position'] = similar_distance_perf['position'].mean()
                    df.at[index, 'distance_perf_count'] = len(similar_distance_perf)
        
        # Compléter les valeurs manquantes pour les colonnes numériques
        numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
        for col in numeric_cols:
            if df[col].isna().any():
                df[col].fillna(df[col].median(), inplace=True)
        
        self.logger.info(f"Created {len(df.columns)} features for {len(df)} rows")
        return df

    def _parse_musique(self, musique_str):
        """
        Parse avancé de la chaîne 'musique' (historique des performances).
        Convertit en liste de valeurs numériques où:
        - Chiffres = position réelle
        - 'A'/'a' (arrêté) = 0
        - 'D'/'d' (disqualifié) = 0
        - 'T'/'t' (tombé) = 0
        - Autres lettres = 0
        """
        if pd.isna(musique_str) or not musique_str:
            return []
        
        # Expression régulière pour extraire les performances
        import re
        
        # Séparation par les parenthèses pour gérer l'année
        parts = re.split(r'[\(\)]', musique_str)
        performances_str = ''.join(parts)
        
        # Extraire toutes les performances (chiffres suivis potentiellement de lettres)
        performances = re.findall(r'(\d+[a-zA-Z]*|[a-zA-Z]+)', performances_str)
        
        # Convertir en valeurs numériques
        numeric_values = []
        for perf in performances:
            if perf[0].isdigit():
                # Extraire la position numérique
                position = int(''.join(filter(str.isdigit, perf)))
                numeric_values.append(position)
            else:
                # Pour les non-finishes (disqualifié, arrêté, etc.)
                numeric_values.append(0)
        
        return numeric_values

    def _extract_cote(self, cote_json):
        """
        Extrait la cote (rapport) d'une chaîne JSON.
        """
        if pd.isna(cote_json) or not cote_json:
            return None
        
        try:
            import json
            
            # Si c'est une chaîne, convertir en dictionnaire
            if isinstance(cote_json, str):
                cote_dict = json.loads(cote_json)
            else:
                cote_dict = cote_json
            
            # Extraire le rapport s'il existe
            if 'rapport' in cote_dict:
                return float(cote_dict['rapport'])
            
            return None
        except:
            return None

    def _encode_meteo(self, meteo_str):
        """
        Encode la condition météo en valeur numérique.
        """
        if pd.isna(meteo_str):
            return 0
            
        meteo_mapping = {  
            'Soleil': 0,  
            'Peu Nuageux': 1,  
            'Variable avec Averses': 2,  
            'Couvert': 3,  
            'Très Nuageux': 4,  
            'Brouillard': 5,  
            'Pluie faible': 6,  
            'Pluies': 7,  
            'Orages Isolés': 8,  
            'Ondées Orageuses': 9,  
            'Risque d\'Averses': 10,  
            'Pluie et Averses de Neige': 11,  
            'Neige': 12,  
            'Pluie et Neige': 13  
            #'NULL': 14  
        }  
        
        return meteo_mapping.get(meteo_str, 5)  # Valeur par défaut si non trouvé

    def _categorize_prize(self, prize_amount):
        """
        Catégorise le montant du prix.
        """
        if prize_amount < 10000:
            return 1  # Petite course
        elif prize_amount < 25000:
            return 2  # Course moyenne
        elif prize_amount < 50000:
            return 3  # Course importante
        elif prize_amount < 100000:
            return 4  # Course majeure
        else:
            return 5  # Course prestigieuse


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

        df = df.reset_index(drop=True)
        
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
        
        # S'assurer que l'index est propre avant de retourner
        prepared_data = prepared_data.reset_index(drop=True)
        
        return prepared_data

    def select_enhanced_features(self, df, target_col='target', exclude_cols=None, top_n=25):
        """
        Sélectionne les features les plus pertinentes pour la modélisation
        en utilisant une combinaison de filtrage et d'importance.
        
        Args:
            df: DataFrame avec les features
            target_col: Colonne cible
            exclude_cols: Colonnes à exclure explicitement
            top_n: Nombre de features à sélectionner
            
        Returns:
            Liste des colonnes sélectionnées
        """
        if exclude_cols is None:
            exclude_cols = []
        
        # Colonnes à exclure par défaut
        default_exclude = [
            'id', 'id_course', 'id_cheval', 'id_jockey', 'cheval_nom', 'jockey_nom',
            'position', 'date_heure', 'lieu', 'type_course', 'statut', 'est_forfait',
            'target_place', 'target_win', 'target_rank', 'target_position_score',
            'musique', 'musique_parsed', 'commentaire', 'dernierRapportDirect', 
            'dernierRapportReference', 'entraineur', 'driver', 'proprietaire',
            'tempsObtenu', 'reductionKilometrique', 'incident'
        ]
        
        # Ne pas exclure la colonne cible
        exclude_cols = list(set(exclude_cols + default_exclude) - {target_col})
        
        # 1. Inclure les features numériques normalisées et encodées
        feature_patterns = [
            '_norm', '_encoded', '_win_rate', '_place_rate', 
            'sexe_', 'type_course_', 'favorite_rank', 'musique_',
            'cote_', 'poids_', 'entraineur_', 'proprietaire_',
            'similar_', 'jockey_cheval_', 'distance_', 'pere_'
        ]
        
        all_features = []
        for pattern in feature_patterns:
            features = [col for col in df.columns if pattern in col and col not in exclude_cols]
            all_features.extend(features)
        
        # Supprimer les doublons
        all_features = list(set(all_features))
        
        # 2. Si target_col existe, calculer l'importance statistique (corrélation)
        if target_col in df.columns:
            importance_dict = {}
            target = df[target_col]
            
            for feature in all_features:
                if feature in df.columns:
                    # Pour les features numériques, utiliser la corrélation
                    if pd.api.types.is_numeric_dtype(df[feature]):
                        correlation = abs(df[feature].corr(target))
                        importance_dict[feature] = correlation if not pd.isna(correlation) else 0
                    # Pour les features catégorielles, utiliser l'analyse de variance
                    else:
                        # Calculer l'association par groupe
                        group_means = df.groupby(feature)[target_col].mean()
                        overall_mean = df[target_col].mean()
                        group_counts = df.groupby(feature)[target_col].count()
                        
                        # Calcul simple de l'importance basé sur l'écart des moyennes pondéré par les effectifs
                        importance = sum(abs(group_mean - overall_mean) * count 
                                        for group_mean, count in zip(group_means, group_counts)) / len(df)
                        importance_dict[feature] = importance
            
            # Trier par importance décroissante et prendre les top_n
            sorted_features = sorted(importance_dict.items(), key=lambda x: x[1], reverse=True)
            self.logger.info(f"Top {min(10, len(sorted_features))} most important features:")
            for feature, importance in sorted_features[:10]:
                self.logger.info(f"{feature}: {importance:.4f}")
            
            # Sélectionner les features les plus importantes
            selected_features = [feature for feature, _ in sorted_features[:top_n]]
        else:
            # Si pas de target_col, prendre toutes les features identifiées
            selected_features = all_features[:top_n]
        
        self.logger.info(f"Selected {len(selected_features)} features for modeling")
        return selected_features



    # Intégrer cette sélection de features à la méthode train du modèle
    # def train_with_enhanced_features(self, df, target_col='target_place', test_size=0.2, top_n_features=25):
        """
        Entraîne le modèle avec la sélection améliorée de features.
        """
        if self.standard_model is None:
            self.initialize_standard_model()
        
        # Créer la variable cible si elle n'existe pas
        if target_col not in df.columns:
            df = self.create_target_variables(df)
        
        # Utiliser la sélection améliorée de features
        feature_cols = self.data_prep.select_enhanced_features(df, target_col=target_col, top_n=top_n_features)
        
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
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        model_path = f"{self.base_path}/enhanced_{self.standard_model_type}_{timestamp}.pkl"
        joblib.dump(self.standard_model, model_path)
        
        # Sauvegarder les importances de features si disponibles
        if 'enhanced' in self.feature_importances:
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