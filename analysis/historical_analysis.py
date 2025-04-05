import pandas as pd
import numpy as np
from sqlalchemy import create_engine
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import logging
import os

class HistoricalAnalysis:
    """Classe pour analyser les performances historiques des chevaux, jockeys et entraîneurs."""
    
    def __init__(self, db_path='pmu_ia'):
        """Initialise la connexion à la base de données."""
        self.engine = create_engine(f'mysql://root:@localhost/{db_path}')
        self.logger = logging.getLogger(__name__)
    
    def get_horse_performance(self, horse_id=None, horse_name=None, start_date=None, end_date=None):
        """Récupère les performances historiques d'un cheval spécifique."""
        if horse_id is None and horse_name is None:
            self.logger.error("Either horse_id or horse_name must be provided")
            return None
            
        # Si on a le nom mais pas l'ID, on cherche l'ID
        if horse_id is None and horse_name is not None:
            query = f"""
            SELECT id FROM chevaux WHERE nom = '{horse_name}'
            """
            
            result = pd.read_sql_query(query, self.engine)
            
            if result.empty:
                self.logger.error(f"No horse found with name: {horse_name}")
                return None
                
            horse_id = result.iloc[0]['id']
        
        # Construire la requête
        query = f"""
        SELECT p.*, c.date_heure, c.lieu, c.type_course, c.distance, c.terrain,
               chev.nom AS cheval_nom, chev.age, chev.sexe,
               j.nom AS jockey_nom
        FROM participations p
        JOIN courses c ON p.id_course = c.id
        JOIN chevaux chev ON p.id_cheval = chev.id
        JOIN jockeys j ON p.id_jockey = j.id
        WHERE p.id_cheval = {horse_id}
        """
        
        if start_date:
            query += f" AND c.date_heure >= '{start_date}'"
        if end_date:
            query += f" AND c.date_heure <= '{end_date}'"
        
        query += " ORDER BY c.date_heure DESC"
        
        return pd.read_sql_query(query, self.engine)
    
    def get_jockey_performance(self, jockey_id=None, jockey_name=None, start_date=None, end_date=None, limit=100):
        """Récupère les performances historiques d'un jockey spécifique."""
        if jockey_id is None and jockey_name is None:
            self.logger.error("Either jockey_id or jockey_name must be provided")
            return None
            
        # Si on a le nom mais pas l'ID, on cherche l'ID
        if jockey_id is None and jockey_name is not None:
            query = f"""
            SELECT id FROM jockeys WHERE nom = '{jockey_name}'
            """
            
            result = pd.read_sql_query(query, self.engine)
            
            if result.empty:
                self.logger.error(f"No jockey found with name: {jockey_name}")
                return None
                
            jockey_id = result.iloc[0]['id']
        
        # Construire la requête
        query = f"""
        SELECT p.*, c.date_heure, c.lieu, c.type_course, c.distance, c.terrain,
               chev.nom AS cheval_nom, chev.age, chev.sexe,
               j.nom AS jockey_nom
        FROM participations p
        JOIN courses c ON p.id_course = c.id
        JOIN chevaux chev ON p.id_cheval = chev.id
        JOIN jockeys j ON p.id_jockey = j.id
        WHERE p.id_jockey = {jockey_id}
        """
        
        if start_date:
            query += f" AND c.date_heure >= '{start_date}'"
        if end_date:
            query += f" AND c.date_heure <= '{end_date}'"
        
        query += " ORDER BY c.date_heure DESC"
        
        if limit:
            query += f" LIMIT {limit}"
        
        return pd.read_sql_query(query, self.engine)
    
    def calculate_horse_metrics(self, horse_id=None, horse_name=None):
        """Calcule des métriques détaillées pour un cheval spécifique."""
        horse_data = self.get_horse_performance(horse_id, horse_name)
        
        if horse_data is None or horse_data.empty:
            if horse_name:
                self.logger.warning(f"No data found for horse '{horse_name}'")
            else:
                self.logger.warning(f"No data found for horse with id {horse_id}")
            return None
        
        # Récupérer le nom du cheval
        horse_name = horse_data['cheval_nom'].iloc[0]
        
        # Calculer les métriques principales
        total_races = len(horse_data)
        wins = len(horse_data[horse_data['position'] == 1])
        places = len(horse_data[horse_data['position'].between(2, 3)])
        
        win_rate = (wins / total_races) * 100 if total_races > 0 else 0
        place_rate = ((wins + places) / total_races) * 100 if total_races > 0 else 0
        
        # Performance par distance
        if 'distance' in horse_data.columns:
            perf_by_distance = horse_data.groupby('distance').agg(
                races=('id_course', 'count'),
                wins=('position', lambda x: (x == 1).sum()),
                places=('position', lambda x: ((x >= 2) & (x <= 3)).sum())
            ).reset_index()
            
            perf_by_distance['win_rate'] = (perf_by_distance['wins'] / perf_by_distance['races']) * 100
            perf_by_distance['place_rate'] = ((perf_by_distance['wins'] + perf_by_distance['places']) / perf_by_distance['races']) * 100
        else:
            perf_by_distance = None
        
        # Performance par hippodrome
        if 'lieu' in horse_data.columns:
            perf_by_hippodrome = horse_data.groupby('lieu').agg(
                races=('id_course', 'count'),
                wins=('position', lambda x: (x == 1).sum()),
                places=('position', lambda x: ((x >= 2) & (x <= 3)).sum())
            ).reset_index()
            
            perf_by_hippodrome['win_rate'] = (perf_by_hippodrome['wins'] / perf_by_hippodrome['races']) * 100
            perf_by_hippodrome['place_rate'] = ((perf_by_hippodrome['wins'] + perf_by_hippodrome['places']) / perf_by_hippodrome['races']) * 100
        else:
            perf_by_hippodrome = None
        
        # Évolution récente des performances
        if 'date_heure' in horse_data.columns:
            horse_data = horse_data.sort_values('date_heure')
            horse_data['date'] = pd.to_datetime(horse_data['date_heure']).dt.date
            
            recent_form = horse_data.tail(5)[['date', 'position', 'lieu', 'distance']]
        else:
            recent_form = None
        
        # Performance avec différents jockeys
        if 'jockey_nom' in horse_data.columns:
            perf_by_jockey = horse_data.groupby('jockey_nom').agg(
                races=('id_course', 'count'),
                wins=('position', lambda x: (x == 1).sum()),
                places=('position', lambda x: ((x >= 2) & (x <= 3)).sum()),
                avg_position=('position', 'mean')
            ).reset_index()
            
            perf_by_jockey['win_rate'] = (perf_by_jockey['wins'] / perf_by_jockey['races']) * 100
            perf_by_jockey['place_rate'] = ((perf_by_jockey['wins'] + perf_by_jockey['places']) / perf_by_jockey['races']) * 100
            perf_by_jockey = perf_by_jockey.sort_values('win_rate', ascending=False)
        else:
            perf_by_jockey = None
        
        # Analyse des cotes
        if 'cote_actuelle' in horse_data.columns:
            avg_odds = horse_data['cote_actuelle'].mean()
            min_odds = horse_data['cote_actuelle'].min()
            max_odds = horse_data['cote_actuelle'].max()
            
            # Analyse de la relation entre cote et position
            if len(horse_data) >= 5:  # Besoin d'assez de données
                corr = horse_data['cote_actuelle'].corr(horse_data['position'])
            else:
                corr = None
            
            odds_analysis = {
                'avg_odds': avg_odds,
                'min_odds': min_odds,
                'max_odds': max_odds,
                'odds_position_correlation': corr
            }
        else:
            odds_analysis = None
        
        # Résultats à retourner
        results = {
            'id': horse_id,
            'name': horse_name,
            'total_races': total_races,
            'wins': wins,
            'places': places,
            'win_rate': win_rate,
            'place_rate': place_rate,
            'perf_by_distance': perf_by_distance,
            'perf_by_hippodrome': perf_by_hippodrome,
            'perf_by_jockey': perf_by_jockey,
            'recent_form': recent_form,
            'odds_analysis': odds_analysis
        }
        
        return results
    
    def calculate_jockey_metrics(self, jockey_id=None, jockey_name=None):
        """Calcule des métriques détaillées pour un jockey spécifique."""
        jockey_data = self.get_jockey_performance(jockey_id, jockey_name)
        
        if jockey_data is None or jockey_data.empty:
            if jockey_name:
                self.logger.warning(f"No data found for jockey '{jockey_name}'")
            else:
                self.logger.warning(f"No data found for jockey with id {jockey_id}")
            return None
        
        # Récupérer le nom du jockey
        jockey_name = jockey_data['jockey_nom'].iloc[0]
        
        # Calculer les métriques principales
        total_races = len(jockey_data)
        wins = len(jockey_data[jockey_data['position'] == 1])
        places = len(jockey_data[jockey_data['position'].between(2, 3)])
        
        win_rate = (wins / total_races) * 100 if total_races > 0 else 0
        place_rate = ((wins + places) / total_races) * 100 if total_races > 0 else 0
        
        # Performance par cheval
        if 'cheval_nom' in jockey_data.columns:
            perf_by_horse = jockey_data.groupby('cheval_nom').agg(
                races=('id_course', 'count'),
                wins=('position', lambda x: (x == 1).sum()),
                places=('position', lambda x: ((x >= 2) & (x <= 3)).sum()),
                avg_position=('position', 'mean')
            ).reset_index()
            
            perf_by_horse['win_rate'] = (perf_by_horse['wins'] / perf_by_horse['races']) * 100
            perf_by_horse['place_rate'] = ((perf_by_horse['wins'] + perf_by_horse['places']) / perf_by_horse['races']) * 100
            perf_by_horse = perf_by_horse.sort_values('win_rate', ascending=False)
        else:
            perf_by_horse = None
        
        # Performance par hippodrome
        if 'lieu' in jockey_data.columns:
            perf_by_hippodrome = jockey_data.groupby('lieu').agg(
                races=('id_course', 'count'),
                wins=('position', lambda x: (x == 1).sum()),
                places=('position', lambda x: ((x >= 2) & (x <= 3)).sum()),
                avg_position=('position', 'mean')
            ).reset_index()
            
            perf_by_hippodrome['win_rate'] = (perf_by_hippodrome['wins'] / perf_by_hippodrome['races']) * 100
            perf_by_hippodrome['place_rate'] = ((perf_by_hippodrome['wins'] + perf_by_hippodrome['places']) / perf_by_hippodrome['races']) * 100
            perf_by_hippodrome = perf_by_hippodrome.sort_values('win_rate', ascending=False)
        else:
            perf_by_hippodrome = None
        
        # Tendance récente (derniers 30 jours vs 30 jours précédents)
        if 'date_heure' in jockey_data.columns:
            jockey_data['date_heure'] = pd.to_datetime(jockey_data['date_heure'])
            
            today = datetime.now()
            last_30_days = today - timedelta(days=30)
            previous_30_days = last_30_days - timedelta(days=30)
            
            recent_data = jockey_data[jockey_data['date_heure'] >= last_30_days]
            previous_data = jockey_data[(jockey_data['date_heure'] < last_30_days) & (jockey_data['date_heure'] >= previous_30_days)]
            
            recent_win_rate = (len(recent_data[recent_data['position'] == 1]) / len(recent_data)) * 100 if len(recent_data) > 0 else 0
            previous_win_rate = (len(previous_data[previous_data['position'] == 1]) / len(previous_data)) * 100 if len(previous_data) > 0 else 0
            
            trend = recent_win_rate - previous_win_rate
        else:
            recent_win_rate = None
            previous_win_rate = None
            trend = None
        
        # Performance par distance
        if 'distance' in jockey_data.columns:
            # Créer des catégories de distance
            jockey_data['distance_cat'] = pd.cut(
                jockey_data['distance'], 
                bins=[0, 1600, 2000, 2500, 3000, 10000],
                labels=['sprint', 'mile', 'intermediate', 'long', 'marathon']
            )
            
            perf_by_distance_cat = jockey_data.groupby('distance_cat').agg(
                races=('id_course', 'count'),
                wins=('position', lambda x: (x == 1).sum()),
                places=('position', lambda x: ((x >= 2) & (x <= 3)).sum()),
                avg_position=('position', 'mean')
            ).reset_index()
            
            perf_by_distance_cat['win_rate'] = (perf_by_distance_cat['wins'] / perf_by_distance_cat['races']) * 100
            perf_by_distance_cat['place_rate'] = ((perf_by_distance_cat['wins'] + perf_by_distance_cat['places']) / perf_by_distance_cat['races']) * 100
        else:
            perf_by_distance_cat = None
        
        # Résultats à retourner
        results = {
            'id': jockey_id,
            'name': jockey_name,
            'total_races': total_races,
            'wins': wins,
            'places': places,
            'win_rate': win_rate,
            'place_rate': place_rate,
            'perf_by_horse': perf_by_horse,
            'perf_by_hippodrome': perf_by_hippodrome,
            'perf_by_distance_cat': perf_by_distance_cat,
            'recent_win_rate': recent_win_rate,
            'previous_win_rate': previous_win_rate,
            'trend': trend
        }
        
        return results
    
    def analyze_course(self, course_id):
        """Analyse une course spécifique avec tous ses participants."""
        query = f"""
        SELECT c.*
        FROM courses c
        WHERE c.id = {course_id}
        """
        
        course_data = pd.read_sql_query(query, self.engine)
        
        if course_data.empty:
            self.logger.warning(f"No data found for course ID {course_id}")
            return None, None
        
        # Récupérer les participants
        query = f"""
        SELECT p.*, 
               chev.nom AS cheval_nom, chev.age, chev.sexe,
               j.nom AS jockey_nom
        FROM participations p
        JOIN chevaux chev ON p.id_cheval = chev.id
        JOIN jockeys j ON p.id_jockey = j.id
        WHERE p.id_course = {course_id}
        """
        
        participants = pd.read_sql_query(query, self.engine)
        
        if participants.empty:
            self.logger.warning(f"No participants found for course ID {course_id}")
            return course_data, None
        
        # Analyser chaque participant
        participant_analysis = []
        
        for _, participant in participants.iterrows():
            cheval_id = participant['id_cheval']
            horse_metrics = self.calculate_horse_metrics(horse_id=cheval_id)
            
            if horse_metrics:
                # Ajouter des informations spécifiques à cette course
                horse_metrics['numPmu'] = participant.get('id_cheval')  # On utilise l'ID du cheval comme numéro PMU
                if 'cote_actuelle' in participant:
                    horse_metrics['cote'] = participant['cote_actuelle']
                
                participant_analysis.append(horse_metrics)
        
        return course_data.iloc[0].to_dict(), participant_analysis
    
    def plot_horse_performance(self, horse_id=None, horse_name=None, output_path=None):
        """Génère des graphiques d'analyse pour un cheval spécifique."""
        horse_data = self.get_horse_performance(horse_id, horse_name)
        
        if horse_data is None or horse_data.empty:
            if horse_name:
                self.logger.warning(f"No data found for horse '{horse_name}'")
            else:
                self.logger.warning(f"No data found for horse with id {horse_id}")
            return None
        
        # Récupérer le nom du cheval
        horse_name = horse_data['cheval_nom'].iloc[0]
        
        # Convertir date_heure en datetime si nécessaire
        if 'date_heure' in horse_data.columns:
            horse_data['date_heure'] = pd.to_datetime(horse_data['date_heure'])
            horse_data = horse_data.sort_values('date_heure')
        
        # Créer la figure avec plusieurs sous-graphiques
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        
        # 1. Évolution des positions au fil du temps
        if 'date_heure' in horse_data.columns and 'position' in horse_data.columns:
            ax = axes[0, 0]
            ax.plot(horse_data['date_heure'], horse_data['position'], 'o-', color='blue')
            ax.set_title(f"Évolution des positions de {horse_name}")
            ax.set_xlabel("Date")
            ax.set_ylabel("Position (1 = premier)")
            ax.grid(True)
            ax.invert_yaxis()  # Pour que 1 soit en haut
        
        # 2. Performance par distance
        if 'distance' in horse_data.columns and 'position' in horse_data.columns:
            ax = axes[0, 1]
            perf_by_distance = horse_data.groupby('distance')['position'].mean().reset_index()
            perf_by_distance = perf_by_distance.sort_values('distance')
            
            ax.bar(perf_by_distance['distance'].astype(str), perf_by_distance['position'], color='green')
            ax.set_title("Position moyenne par distance")
            ax.set_xlabel("Distance (m)")
            ax.set_ylabel("Position moyenne")
            ax.grid(True, axis='y')
            ax.invert_yaxis()  # Pour que les meilleures performances soient plus hautes
        
        # 3. Performance par hippodrome
        if 'lieu' in horse_data.columns and 'position' in horse_data.columns:
            ax = axes[1, 0]
            perf_by_hippodrome = horse_data.groupby('lieu')['position'].mean().reset_index()
            perf_by_hippodrome = perf_by_hippodrome.sort_values('position')
            
            ax.barh(perf_by_hippodrome['lieu'], perf_by_hippodrome['position'], color='orange')
            ax.set_title("Position moyenne par hippodrome")
            ax.set_xlabel("Position moyenne")
            ax.set_ylabel("Hippodrome")
            ax.grid(True, axis='x')
            ax.invert_xaxis()  # Pour que les meilleures performances soient plus à droite
        
        # 4. Distribution des positions
        if 'position' in horse_data.columns:
            ax = axes[1, 1]
            positions = horse_data['position'].value_counts().sort_index()
            
            ax.bar(positions.index.astype(str), positions.values, color='purple')
            ax.set_title("Distribution des positions")
            ax.set_xlabel("Position")
            ax.set_ylabel("Nombre de courses")
            ax.grid(True, axis='y')
        
        plt.tight_layout()
        
        # Sauvegarder l'image si un chemin est fourni
        if output_path:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            plt.savefig(output_path)
            plt.close()
            return output_path
        else:
            # Sinon, générer un nom de fichier basé sur le nom du cheval
            output_file = f"{horse_name.replace(' ', '_')}_performance.png"
            plt.savefig(output_file)
            plt.close()
            return output_file
    
    def plot_jockey_performance(self, jockey_id=None, jockey_name=None, output_path=None):
        """Génère des graphiques d'analyse pour un jockey spécifique."""
        jockey_data = self.get_jockey_performance(jockey_id, jockey_name)
        
        if jockey_data is None or jockey_data.empty:
            if jockey_name:
                self.logger.warning(f"No data found for jockey '{jockey_name}'")
            else:
                self.logger.warning(f"No data found for jockey with id {jockey_id}")
            return None
        
        # Récupérer le nom du jockey
        jockey_name = jockey_data['jockey_nom'].iloc[0]
        
        # Convertir date_heure en datetime si nécessaire
        if 'date_heure' in jockey_data.columns:
            jockey_data['date_heure'] = pd.to_datetime(jockey_data['date_heure'])
            jockey_data = jockey_data.sort_values('date_heure')
        
        # Créer la figure avec plusieurs sous-graphiques
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        
        # 1. Taux de victoire sur les dernières courses (fenêtre mobile)
        if 'date_heure' in jockey_data.columns and 'position' in jockey_data.columns:
            ax = axes[0, 0]
            
            # Trier par date
            jockey_data = jockey_data.sort_values('date_heure')
            
            # Créer une colonne indiquant si c'est une victoire
            jockey_data['is_win'] = (jockey_data['position'] == 1).astype(int)
            
            # Calculer une moyenne mobile sur les 10 dernières courses
            window_size = min(10, len(jockey_data))
            if window_size > 1:
                jockey_data['win_rate_moving'] = jockey_data['is_win'].rolling(window=window_size, min_periods=1).mean() * 100
                
                ax.plot(jockey_data['date_heure'], jockey_data['win_rate_moving'], '-', color='blue')
                ax.set_title(f"Évolution du taux de victoire de {jockey_name}")
                ax.set_xlabel("Date")
                ax.set_ylabel("Taux de victoire (%)")
                ax.grid(True)
        
        # 2. Performance par hippodrome
        if 'lieu' in jockey_data.columns and 'position' in jockey_data.columns:
            ax = axes[0, 1]
            
            # Grouper par hippodrome et calculer le taux de victoire
            hippo_stats = jockey_data.groupby('lieu').agg(
                races=('id_course', 'count'),
                wins=('is_win', 'sum')
            ).reset_index()
            
            hippo_stats['win_rate'] = (hippo_stats['wins'] / hippo_stats['races']) * 100
            
            # Ne garder que les hippodromes avec au moins 3 courses
            hippo_stats = hippo_stats[hippo_stats['races'] >= 3]
            hippo_stats = hippo_stats.sort_values('win_rate', ascending=False)
            
            # Limiter à 10 hippodromes pour la lisibilité
            hippo_stats = hippo_stats.head(10)
            
            ax.barh(hippo_stats['lieu'], hippo_stats['win_rate'], color='orange')
            ax.set_title("Taux de victoire par hippodrome")
            ax.set_xlabel("Taux de victoire (%)")
            ax.set_ylabel("Hippodrome")
            ax.grid(True, axis='x')
        
        # 3. Performance par cheval (top chevaux)
        if 'cheval_nom' in jockey_data.columns and 'position' in jockey_data.columns:
            ax = axes[1, 0]
            
            # Grouper par cheval et calculer le taux de victoire
            cheval_stats = jockey_data.groupby('cheval_nom').agg(
                races=('id_course', 'count'),
                wins=('is_win', 'sum')
            ).reset_index()
            
            cheval_stats['win_rate'] = (cheval_stats['wins'] / cheval_stats['races']) * 100
            
            # Ne garder que les chevaux avec au moins 2 courses
            cheval_stats = cheval_stats[cheval_stats['races'] >= 2]
            cheval_stats = cheval_stats.sort_values('win_rate', ascending=False)
            
            # Limiter à 10 chevaux pour la lisibilité
            cheval_stats = cheval_stats.head(10)
            
            ax.barh(cheval_stats['cheval_nom'], cheval_stats['win_rate'], color='green')
            ax.set_title("Taux de victoire par cheval")
            ax.set_xlabel("Taux de victoire (%)")
            ax.set_ylabel("Cheval")
            ax.grid(True, axis='x')
        
        # 4. Distribution des positions
        if 'position' in jockey_data.columns:
            ax = axes[1, 1]
            positions = jockey_data['position'].value_counts().sort_index()
            
            ax.bar(positions.index.astype(str), positions.values, color='purple')
            ax.set_title("Distribution des positions")
            ax.set_xlabel("Position")
            ax.set_ylabel("Nombre de courses")
            ax.grid(True, axis='y')
        
        plt.tight_layout()
        
        # Sauvegarder l'image si un chemin est fourni
        if output_path:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            plt.savefig(output_path)
            plt.close()
            return output_path
        else:
            # Sinon, générer un nom de fichier basé sur le nom du jockey
            output_file = f"{jockey_name.replace(' ', '_')}_performance.png"
            plt.savefig(output_file)
            plt.close()
            return output_file
    
    def get_course_stats(self, lieu=None, distance=None, limit=100):
        """Récupère des statistiques sur les courses par lieu et/ou distance."""
        conditions = []
        
        if lieu:
            conditions.append(f"c.lieu = '{lieu}'")
        if distance:
            # On prend une fourchette de ±100m
            conditions.append(f"c.distance BETWEEN {distance-100} AND {distance+100}")
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        query = f"""
        SELECT c.lieu, c.distance, c.type_course, c.terrain,
               p.id_cheval, p.id_jockey, p.position, p.cote_actuelle,
               chev.nom AS cheval_nom, j.nom AS jockey_nom
        FROM courses c
        JOIN participations p ON c.id = p.id_course
        JOIN chevaux chev ON p.id_cheval = chev.id
        JOIN jockeys j ON p.id_jockey = j.id
        WHERE {where_clause}
        ORDER BY c.date_heure DESC
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        data = pd.read_sql_query(query, self.engine)
        
        if data.empty:
            self.logger.warning(f"No data found for lieu='{lieu}', distance={distance}")
            return None
        
        # Statistiques sur les favoris
        if 'cote_actuelle' in data.columns:
            # Pour chaque course, marquer le favori (cote la plus basse)
            data['course_id'] = data.index  # Temporaire pour le groupby
            data['favori_rank'] = data.groupby('course_id')['cote_actuelle'].rank()
            
            # Calculer le taux de victoire des favoris
            favoris = data[data['favori_rank'] == 1]
            favoris_win_rate = (favoris['position'] == 1).mean() * 100 if not favoris.empty else 0
            
            # Calculer le taux de places (top 3) des favoris
            favoris_place_rate = (favoris['position'] <= 3).mean() * 100 if not favoris.empty else 0
            
            # Odds moyens du gagnant
            winners = data[data['position'] == 1]
            avg_winner_odds = winners['cote_actuelle'].mean() if not winners.empty else None
        else:
            favoris_win_rate = None
            favoris_place_rate = None
            avg_winner_odds = None
        
        # Analyse des jockeys les plus performants
        jockey_stats = data.groupby('jockey_nom').agg(
            races=('course_id', 'count'),
            wins=('position', lambda x: (x == 1).sum()),
            places=('position', lambda x: ((x >= 2) & (x <= 3)).sum())
        ).reset_index()
        
        jockey_stats['win_rate'] = (jockey_stats['wins'] / jockey_stats['races']) * 100
        jockey_stats['place_rate'] = ((jockey_stats['wins'] + jockey_stats['places']) / jockey_stats['races']) * 100
        
        # Ne garder que les jockeys avec au moins 3 courses
        jockey_stats = jockey_stats[jockey_stats['races'] >= 3]
        top_jockeys = jockey_stats.sort_values('win_rate', ascending=False).head(5)
        
        # Résultats à retourner
        results = {
            'total_races': len(data['course_id'].unique()),
            'lieu': lieu,
            'distance': distance,
            'favoris_win_rate': favoris_win_rate,
            'favoris_place_rate': favoris_place_rate,
            'avg_winner_odds': avg_winner_odds,
            'top_jockeys': top_jockeys
        }
        
        return results
    
    def get_predictions_history(self, days_back=30):
        """Récupère l'historique des prédictions pour évaluer leur précision."""
        # Récupérer les prédictions des x derniers jours
        today = datetime.now()
        start_date = today - timedelta(days=days_back)
        
        query = f"""
        SELECT p.id, p.id_course, p.horodatage, p.prediction, p.note_confiance,
               c.date_heure, c.lieu, c.type_course, c.distance
        FROM predictions p
        JOIN courses c ON p.id_course = c.id
        WHERE p.horodatage >= '{start_date.strftime("%Y-%m-%d")}'
        ORDER BY p.horodatage DESC
        """
        
        predictions = pd.read_sql_query(query, self.engine)
        
        if predictions.empty:
            self.logger.warning(f"No predictions found for the last {days_back} days")
            return None
        
        # Pour chaque prédiction, récupérer les résultats réels
        results = []
        
        for idx, pred in predictions.iterrows():
            course_id = pred['id_course']
            
            # Récupérer les résultats réels de la course
            real_results_query = f"""
            SELECT p.id_cheval, p.position, chev.nom AS cheval_nom
            FROM participations p
            JOIN chevaux chev ON p.id_cheval = chev.id
            WHERE p.id_course = {course_id}
            ORDER BY p.position
            """
            
            real_results = pd.read_sql_query(real_results_query, self.engine)
            
            if real_results.empty:
                continue
            
            # Analyser la prédiction (format JSON)
            try:
                prediction = pd.read_json(pred['prediction'])
                
                # Top prédiction
                top_prediction = prediction.iloc[0] if not prediction.empty else None
                
                if top_prediction is not None:
                    # Vérifier si la prédiction était correcte
                    winner_id = real_results.iloc[0]['id_cheval'] if not real_results.empty else None
                    correct = top_prediction['id_cheval'] == winner_id
                    
                    # Vérifier si le gagnant était dans le top 3 des prédictions
                    top3_ids = prediction.head(3)['id_cheval'].tolist() if len(prediction) >= 3 else prediction['id_cheval'].tolist()
                    in_top3 = winner_id in top3_ids
                    
                    # Position réelle du cheval prédit comme gagnant
                    top_cheval_result = real_results[real_results['id_cheval'] == top_prediction['id_cheval']]
                    predicted_winner_position = top_cheval_result.iloc[0]['position'] if not top_cheval_result.empty else None
                    
                    # Ajouter aux résultats
                    results.append({
                        'prediction_id': pred['id'],
                        'course_id': course_id,
                        'date_prediction': pred['horodatage'],
                        'date_course': pred['date_heure'],
                        'lieu': pred['lieu'],
                        'distance': pred['distance'],
                        'predicted_winner': top_prediction['cheval_nom'] if 'cheval_nom' in top_prediction else top_prediction['id_cheval'],
                        'real_winner': real_results.iloc[0]['cheval_nom'] if not real_results.empty else None,
                        'correct': correct,
                        'in_top3': in_top3,
                        'predicted_winner_position': predicted_winner_position,
                        'confidence': pred['note_confiance']
                    })
            except Exception as e:
                self.logger.error(f"Error analyzing prediction {pred['id']}: {str(e)}")
        
        if not results:
            self.logger.warning("No predictions could be analyzed")
            return None
        
        # Convertir en DataFrame
        results_df = pd.DataFrame(results)
        
        # Calculer des métriques globales
        accuracy = results_df['correct'].mean() * 100
        top3_accuracy = results_df['in_top3'].mean() * 100
        
        # Métriques par hippodrome
        hippo_metrics = results_df.groupby('lieu').agg(
            predictions=('prediction_id', 'count'),
            accuracy=('correct', 'mean'),
            top3_accuracy=('in_top3', 'mean')
        ).reset_index()
        
        hippo_metrics['accuracy'] = hippo_metrics['accuracy'] * 100
        hippo_metrics['top3_accuracy'] = hippo_metrics['top3_accuracy'] * 100
        
        return {
            'all_predictions': results_df,
            'total_predictions': len(results_df),
            'overall_accuracy': accuracy,
            'overall_top3_accuracy': top3_accuracy,
            'hippodrome_metrics': hippo_metrics
        }