import pandas as pd
import numpy as np
import logging
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split, GroupKFold, cross_val_score
from sklearn.metrics import accuracy_score, log_loss, f1_score, precision_score, recall_score
from xgboost import XGBClassifier
import lightgbm as lgb
from datetime import datetime
import joblib
import matplotlib.pyplot as plt
import seaborn as sns

class PredictionModel:
    def __init__(self, model_type='xgboost'):
        """Initialise le modèle prédictif."""
        self.logger = logging.getLogger(__name__)
        self.model_type = model_type
        self.model = None
        self.feature_importances = None
        
    def initialize_model(self):
        """Initialise le modèle en fonction du type spécifié."""
        if self.model_type == 'random_forest':
            self.model = RandomForestClassifier(
                n_estimators=100,
                max_depth=None,
                min_samples_split=2,
                min_samples_leaf=1,
                n_jobs=-1,
                random_state=42,
                class_weight='balanced'
            )
        elif self.model_type == 'xgboost':
            self.model = XGBClassifier(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                subsample=0.8,
                colsample_bytree=0.8,
                objective='binary:logistic',
                eval_metric='logloss',
                random_state=42
            )
        elif self.model_type == 'gradient_boosting':
            self.model = GradientBoostingClassifier(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                subsample=0.8,
                random_state=42
            )
        elif self.model_type == 'lightgbm':
            self.model = lgb.LGBMClassifier(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42
            )
        else:
            raise ValueError(f"Model type '{self.model_type}' not supported")
            
        self.logger.info(f"Initialized {self.model_type} model")
        return self.model
    
    def create_target_variable(self, df, type_target='place'):
        """Crée la variable cible en fonction de la position d'arrivée."""
        if 'position' not in df.columns:
            self.logger.error("Column 'position' not found in dataframe")
            return None
            
        if type_target == 'win':
            # Gagnant (1ère place)
            df['target'] = df['position'].apply(lambda x: 1 if x == 1 else 0)
        elif type_target == 'place':
            # Dans les 3 premiers
            df['target'] = df['position'].apply(lambda x: 1 if x <= 3 else 0)
        elif type_target == 'show':
            # Dans les 5 premiers
            df['target'] = df['position'].apply(lambda x: 1 if x <= 5 else 0)
        else:
            # Place exacte (multi-classe)
            df['target'] = df['position']
            
        self.logger.info(f"Created target variable '{type_target}'. Positive class ratio: {df['target'].mean():.2f}")
        return df
    
    def enhance_features(self, df):
        """Améliore les features avec des calculées avancées."""
        self.logger.info("Enhancing features with advanced calculations")
        
        # Ajouter des ratios et des features interactives
        if 'poids' in df.columns and 'age' in df.columns:
            df['poids_par_age'] = df['poids'] / df['age']
            
        if 'distance' in df.columns:
            # Catégoriser les distances
            df['distance_cat'] = pd.cut(
                df['distance'], 
                bins=[0, 1600, 2000, 2500, 3000, 10000],
                labels=['sprint', 'mile', 'intermediate', 'long', 'marathon']
            )
            
        # Features par course
        if 'id_course' in df.columns and 'cote_actuelle' in df.columns:
            # Classement par cote dans chaque course
            df['cote_rank'] = df.groupby('id_course')['cote_actuelle'].rank(ascending=True)
            
            # Ratio de cote par rapport à la cote moyenne dans la course
            df['cote_ratio'] = df['cote_actuelle'] / df.groupby('id_course')['cote_actuelle'].transform('mean')
        
        # Performances passées sur le même hippodrome (déjà calculé dans DataPreparation)
        # Performances passées sur la même distance (déjà calculé dans DataPreparation)
        
        # Tendance de la cote
        if 'cote_initiale' in df.columns and 'cote_actuelle' in df.columns:
            df['cote_trend'] = df['cote_actuelle'] - df['cote_initiale']
            df['cote_trend_pct'] = (df['cote_actuelle'] - df['cote_initiale']) / df['cote_initiale'] * 100
        
        # Interaction entre caractéristiques
        if 'win_rate' in df.columns and 'jockey_win_rate' in df.columns:
            df['combined_win_rate'] = df['win_rate'] * df['jockey_win_rate'] / 100  # Normaliser en pourcentage
        
        if 'cote_actuelle' in df.columns and 'win_rate' in df.columns:
            df['value_bet_indicator'] = df['win_rate'] / df['cote_actuelle']  # Plus c'est élevé, meilleur est le rapport qualité/prix
        
        # Combler les valeurs manquantes des nouvelles colonnes
        for col in df.columns:
            if df[col].isna().any():
                # Pour les colonnes numériques, utiliser la médiane ou 0
                if pd.api.types.is_numeric_dtype(df[col]):
                    df[col].fillna(df[col].median() if df[col].median() else 0, inplace=True)
                else:
                    df[col].fillna('Unknown', inplace=True)
                    
        return df
    
    def select_features(self, df, target_col='target', exclude_cols=None):
        """Sélectionne les features pertinentes pour la modélisation."""
        if exclude_cols is None:
            exclude_cols = []
            
        # Colonnes à exclure par défaut
        default_exclude = [
            'id', 'id_course', 'id_cheval', 'id_jockey', 'cheval_nom', 'jockey_nom',
            'target', 'position', 'date_heure', 'statut', 'est_forfait'
        ]
        exclude_cols = list(set(exclude_cols + default_exclude + [target_col]))
        
        # Sélectionner seulement les colonnes numériques et les catégorielles encodées
        numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
        encoded_cols = [col for col in df.columns if col.endswith('_encoded')]
        
        feature_cols = list(set(numeric_cols.tolist() + encoded_cols) - set(exclude_cols))
        
        self.logger.info(f"Selected {len(feature_cols)} features for modeling")
        return feature_cols
    
    def train(self, df, target_col='target', test_size=0.2, group_col=None):
        """Entraîne le modèle sur les données fournies."""
        if self.model is None:
            self.initialize_model()
            
        # Sélectionner les features
        feature_cols = self.select_features(df, target_col)
        
        X = df[feature_cols]
        y = df[target_col]
        
        # Vérifier qu'il n'y a pas de valeurs manquantes
        if X.isna().any().any():
            self.logger.warning("NaN values found in features. Filling with median values.")
            X = X.fillna(X.median())
            
        # Utiliser GroupKFold si un groupe est spécifié
        if group_col and group_col in df.columns:
            groups = df[group_col]
            gkf = GroupKFold(n_splits=5)
            
            self.logger.info(f"Training with GroupKFold on {group_col}")
            
            scores = []
            for train_idx, test_idx in gkf.split(X, y, groups):
                X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
                y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
                
                self.model.fit(X_train, y_train)
                y_pred = self.model.predict(X_test)
                
                score = accuracy_score(y_test, y_pred)
                scores.append(score)
                
            self.logger.info(f"Cross-validation scores: {scores}")
            self.logger.info(f"Mean CV score: {np.mean(scores):.4f}")
            
            # Ré-entraîner sur l'ensemble des données
            self.model.fit(X, y)
            
        else:
            # Diviser les données en ensembles d'entraînement et de test
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=42
            )
            
            self.logger.info(f"Training on {len(X_train)} samples, testing on {len(X_test)} samples")
            
            # Entraîner le modèle
            self.model.fit(X_train, y_train)
            
            # Évaluer les performances
            y_pred = self.model.predict(X_test)
            y_pred_proba = self.model.predict_proba(X_test)[:, 1]
            
            acc = accuracy_score(y_test, y_pred)
            logloss = log_loss(y_test, y_pred_proba)
            f1 = f1_score(y_test, y_pred)
            precision = precision_score(y_test, y_pred)
            recall = recall_score(y_test, y_pred)
            
            self.logger.info(f"Performance metrics:")
            self.logger.info(f"Accuracy: {acc:.4f}")
            self.logger.info(f"Log Loss: {logloss:.4f}")
            self.logger.info(f"F1 Score: {f1:.4f}")
            self.logger.info(f"Precision: {precision:.4f}")
            self.logger.info(f"Recall: {recall:.4f}")
            
        # Stocker les importances des features
        if hasattr(self.model, 'feature_importances_'):
            self.feature_importances = pd.DataFrame({
                'feature': feature_cols,
                'importance': self.model.feature_importances_
            }).sort_values('importance', ascending=False)
            
            self.logger.info(f"Top 10 important features:")
            for i, row in self.feature_importances.head(10).iterrows():
                self.logger.info(f"{row['feature']}: {row['importance']:.4f}")
                
        return self.model
    
    def predict(self, X):
        """Effectue une prédiction avec le modèle entraîné."""
        if self.model is None:
            self.logger.error("Model not trained yet. Call train() first.")
            return None
            
        # Vérifier qu'il n'y a pas de valeurs manquantes
        if X.isna().any().any():
            self.logger.warning("NaN values found in features. Filling with median values.")
            X = X.fillna(X.median())
            
        # Prédire les classes et les probabilités
        y_pred = self.model.predict(X)
        y_pred_proba = self.model.predict_proba(X)
        
        return y_pred, y_pred_proba
    
    def predict_ranking(self, df, course_id=None):
        """Prédit le classement complet des chevaux dans une course."""
        if self.model is None:
            self.logger.error("Model not trained yet. Call train() first.")
            return None
            
        # Filtrer pour cette course si un ID est fourni
        if course_id is not None:
            df = df[df['id_course'] == course_id].copy()
            
        if df.empty:
            self.logger.error("No data available for this course")
            return None
            
        # Sélectionner les features
        feature_cols = self.select_features(df)
        X = df[feature_cols]
        
        # Prédire les probabilités de victoire
        y_pred_proba = self.model.predict_proba(X)[:, 1]
        
        # Créer un DataFrame de résultats
        results = pd.DataFrame({
            'id_cheval': df['id_cheval'],
            'cheval_nom': df['cheval_nom'] if 'cheval_nom' in df.columns else df['id_cheval'],
            'id_jockey': df['id_jockey'],
            'jockey_nom': df['jockey_nom'] if 'jockey_nom' in df.columns else df['id_jockey'],
            'win_probability': y_pred_proba
        })
        
        # Trier par probabilité décroissante
        results = results.sort_values('win_probability', ascending=False).reset_index(drop=True)
        
        # Ajouter le rang prédit
        results['predicted_rank'] = results.index + 1
        
        # Ajouter les cotes si disponibles
        if 'cote_actuelle' in df.columns:
            results = pd.merge(
                results,
                df[['id_cheval', 'cote_actuelle']],
                on='id_cheval',
                how='left'
            )
        
        return results
    
    def save_model(self, filename):
        """Sauvegarde le modèle entraîné."""
        if self.model is None:
            self.logger.error("No model to save. Train first.")
            return
            
        # Créer le répertoire si nécessaire
        import os
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        # Sauvegarder le modèle
        joblib.dump(self.model, filename)
        self.logger.info(f"Model saved to {filename}")
        
        # Sauvegarder les importances si disponibles
        if self.feature_importances is not None:
            importances_filename = filename.replace('.pkl', '_importance.csv')
            self.feature_importances.to_csv(importances_filename, index=False)
            self.logger.info(f"Feature importances saved to {importances_filename}")
            
        return filename
    
    def load_model(self, filename):
        """Charge un modèle entraîné."""
        try:
            self.model = joblib.load(filename)
            self.logger.info(f"Model loaded from {filename}")
            return self.model
        except Exception as e:
            self.logger.error(f"Error loading model: {str(e)}")
            return None
    
    def save_predictions_to_db(self, predictions_df, course_id):
        """Sauvegarde les prédictions dans la base de données."""
        from sqlalchemy import create_engine
        
        engine = create_engine('mysql://root:@localhost/pmu_ia')
        
        # Convertir le DataFrame en format JSON
        prediction_json = predictions_df.to_json(orient='records')
        
        # Créer un DataFrame pour la table predictions
        prediction_record = pd.DataFrame({
            'id_course': [course_id],
            'horodatage': [datetime.now()],
            'prediction': [prediction_json],
            'note_confiance': [predictions_df['win_probability'].mean()]
        })
        
        # Sauvegarder dans la table predictions
        try:
            prediction_record.to_sql('predictions', engine, if_exists='append', index=False)
            self.logger.info(f"Predictions saved to database for course_id {course_id}")
            return True
        except Exception as e:
            self.logger.error(f"Error saving predictions to database: {str(e)}")
            return False