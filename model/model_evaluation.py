import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, log_loss
from sklearn.metrics import confusion_matrix, roc_curve, auc, precision_recall_curve
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV, learning_curve
import joblib
import logging
import time
from datetime import datetime

# Import des modules personnalisés
from model.prediction_model import PredictionModel
from data_preparation.data_preparation import DataPreparation

class ModelEvaluation:
    """Classe pour l'évaluation et l'optimisation des modèles de prédiction."""
    
    def __init__(self, model_path=None):
        """Initialise l'évaluateur de modèle."""
        self.logger = logging.getLogger(__name__)
        self.model = None
        
        if model_path:
            try:
                self.model = joblib.load(model_path)
                self.logger.info(f"Modèle chargé depuis {model_path}")
            except Exception as e:
                self.logger.error(f"Erreur lors du chargement du modèle: {e}")
    
    def evaluate_model(self, X_test, y_test, detailed=True):
        """Évalue les performances d'un modèle sur des données de test."""
        if self.model is None:
            self.logger.error("Aucun modèle chargé pour l'évaluation")
            return None
        
        start_time = time.time()
        
        # Prédictions
        y_pred = self.model.predict(X_test)
        y_pred_proba = self.model.predict_proba(X_test)[:, 1]
        
        # Métriques de base
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred)
        recall = recall_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred)
        logloss = log_loss(y_test, y_pred_proba)
        
        self.logger.info(f"Évaluation terminée en {time.time() - start_time:.2f} secondes")
        self.logger.info(f"Accuracy: {accuracy:.4f}, Precision: {precision:.4f}, Recall: {recall:.4f}, F1: {f1:.4f}, Log Loss: {logloss:.4f}")
        
        # Résultat de base
        results = {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'log_loss': logloss
        }
        
        if detailed:
            # Matrice de confusion
            cm = confusion_matrix(y_test, y_pred)
            
            # Courbe ROC
            fpr, tpr, _ = roc_curve(y_test, y_pred_proba)
            roc_auc = auc(fpr, tpr)
            
            # Courbe Précision-Rappel
            precision_curve, recall_curve, _ = precision_recall_curve(y_test, y_pred_proba)
            pr_auc = auc(recall_curve, precision_curve)
            
            # Top-K Accuracy pour différentes valeurs de K
            k_values = [3, 5, 10]
            top_k_accuracy = {}
            
            for k in k_values:
                if hasattr(self.model, 'classes_'):
                    n_classes = len(self.model.classes_)
                else:
                    n_classes = 2  # Binaire par défaut
                
                if n_classes > 1:
                    # Pour la classification multi-classe, on prend les K meilleures prédictions
                    top_k_indices = np.argsort(self.model.predict_proba(X_test), axis=1)[:, -k:]
                    top_k_accuracy[k] = np.mean([y_test.iloc[i] in self.model.classes_[top_k_indices[i]] for i in range(len(y_test))])
                else:
                    # Pour la classification binaire
                    top_k_accuracy[k] = accuracy  # Toujours le même en binaire
            
            # Ajouter les résultats détaillés
            results.update({
                'confusion_matrix': cm,
                'roc_curve': {
                    'fpr': fpr,
                    'tpr': tpr,
                    'auc': roc_auc
                },
                'pr_curve': {
                    'precision': precision_curve,
                    'recall': recall_curve,
                    'auc': pr_auc
                },
                'top_k_accuracy': top_k_accuracy
            })
        
        return results
    
    def optimize_hyperparameters(self, model_type, X_train, y_train, param_grid=None, cv=5, n_iter=20, scoring='f1'):
        """Optimise les hyperparamètres d'un modèle avec GridSearchCV ou RandomizedSearchCV."""
        self.logger.info(f"Démarrage de l'optimisation des hyperparamètres pour {model_type}")
        
        # Créer un modèle de base
        model = PredictionModel(model_type=model_type)
        model.initialize_model()
        
        # Paramètres par défaut si non fournis
        if param_grid is None:
            if model_type == 'random_forest':
                param_grid = {
                    'n_estimators': [50, 100, 200],
                    'max_depth': [None, 10, 20, 30],
                    'min_samples_split': [2, 5, 10],
                    'min_samples_leaf': [1, 2, 4],
                    'class_weight': ['balanced', None]
                }
            elif model_type == 'xgboost':
                param_grid = {
                    'n_estimators': [50, 100, 200],
                    'max_depth': [3, 5, 7],
                    'learning_rate': [0.01, 0.1, 0.2],
                    'subsample': [0.6, 0.8, 1.0],
                    'colsample_bytree': [0.6, 0.8, 1.0]
                }
            elif model_type == 'gradient_boosting':
                param_grid = {
                    'n_estimators': [50, 100, 200],
                    'max_depth': [3, 5, 7],
                    'learning_rate': [0.01, 0.1, 0.2],
                    'subsample': [0.6, 0.8, 1.0],
                    'min_samples_split': [2, 5, 10]
                }
            elif model_type == 'lightgbm':
                param_grid = {
                    'n_estimators': [50, 100, 200],
                    'max_depth': [3, 5, 7],
                    'learning_rate': [0.01, 0.1, 0.2],
                    'subsample': [0.6, 0.8, 1.0],
                    'colsample_bytree': [0.6, 0.8, 1.0],
                    'reg_alpha': [0, 0.1, 0.5],
                    'reg_lambda': [0, 0.1, 0.5]
                }
            else:
                self.logger.error(f"Type de modèle non supporté: {model_type}")
                return None
        
        start_time = time.time()
        
        # Utiliser RandomizedSearchCV pour une recherche plus efficace
        search = RandomizedSearchCV(
            model.model,
            param_distributions=param_grid,
            n_iter=n_iter,
            cv=cv,
            scoring=scoring,
            random_state=42,
            n_jobs=-1,
            verbose=1
        )
        
        # Effectuer la recherche
        search.fit(X_train, y_train)
        
        elapsed_time = time.time() - start_time
        
        self.logger.info(f"Optimisation terminée en {elapsed_time:.2f} secondes")
        self.logger.info(f"Meilleurs paramètres: {search.best_params_}")
        self.logger.info(f"Meilleur score: {search.best_score_:.4f}")
        
        # Stocker le meilleur modèle
        self.model = search.best_estimator_
        
        # Retourner les résultats
        return {
            'best_model': search.best_estimator_,
            'best_params': search.best_params_,
            'best_score': search.best_score_,
            'all_results': search.cv_results_,
            'elapsed_time': elapsed_time
        }
    
    def learning_curve_analysis(self, X, y, cv=5, train_sizes=np.linspace(0.1, 1.0, 5)):
        """Analyse la courbe d'apprentissage pour évaluer le sur/sous-apprentissage."""
        if self.model is None:
            self.logger.error("Aucun modèle chargé pour l'analyse")
            return None
        
        self.logger.info("Analyse de la courbe d'apprentissage")
        
        start_time = time.time()
        
        # Calculer la courbe d'apprentissage
        train_sizes_abs, train_scores, test_scores = learning_curve(
            self.model,
            X, y,
            train_sizes=train_sizes,
            cv=cv,
            scoring='f1',
            n_jobs=-1
        )
        
        self.logger.info(f"Analyse terminée en {time.time() - start_time:.2f} secondes")
        
        # Calculer les moyennes et écarts-types
        train_mean = np.mean(train_scores, axis=1)
        train_std = np.std(train_scores, axis=1)
        test_mean = np.mean(test_scores, axis=1)
        test_std = np.std(test_scores, axis=1)
        
        return {
            'train_sizes_abs': train_sizes_abs,
            'train_mean': train_mean,
            'train_std': train_std,
            'test_mean': test_mean,
            'test_std': test_std
        }
    
    def feature_importance_analysis(self, feature_names=None):
        """Analyse l'importance des features pour le modèle."""
        if self.model is None:
            self.logger.error("Aucun modèle chargé pour l'analyse")
            return None
        
        self.logger.info("Analyse de l'importance des features")
        
        if not hasattr(self.model, 'feature_importances_'):
            self.logger.warning("Le modèle ne supporte pas l'analyse d'importance des features")
            return None
        
        # Récupérer les importances
        importances = self.model.feature_importances_
        
        # Si les noms des features ne sont pas fournis, utiliser des index
        if feature_names is None:
            feature_names = [f'feature_{i}' for i in range(len(importances))]
        
        # Créer un DataFrame pour les importances
        importance_df = pd.DataFrame({
            'feature': feature_names,
            'importance': importances
        })
        
        # Trier par importance décroissante
        importance_df = importance_df.sort_values('importance', ascending=False)
        
        self.logger.info(f"Top 10 features: {importance_df.head(10)['feature'].tolist()}")
        
        return importance_df
    
    def save_evaluation_report(self, results, output_dir='model/evaluation'):
        """Sauvegarde un rapport d'évaluation complet avec graphiques."""
        import os
        import matplotlib.pyplot as plt
        import json
        
        # Créer le répertoire si nécessaire
        os.makedirs(output_dir, exist_ok=True)
        
        # Timestamp pour le nom du fichier
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Sauvegarder les métriques de base dans un fichier JSON
        metrics = {
            'accuracy': results['accuracy'],
            'precision': results['precision'],
            'recall': results['recall'],
            'f1_score': results['f1_score'],
            'log_loss': results['log_loss'],
            'timestamp': timestamp
        }
        
        with open(f"{output_dir}/metrics_{timestamp}.json", 'w') as f:
            json.dump(metrics, f, indent=4)
        
        # Graphiques détaillés si disponibles
        if 'confusion_matrix' in results:
            # Matrice de confusion
            plt.figure(figsize=(8, 6))
            sns.heatmap(results['confusion_matrix'], annot=True, fmt='d', cmap='Blues')
            plt.title('Matrice de confusion')
            plt.ylabel('Vrai label')
            plt.xlabel('Prédit')
            plt.tight_layout()
            plt.savefig(f"{output_dir}/confusion_matrix_{timestamp}.png")
            plt.close()
        
        if 'roc_curve' in results:
            # Courbe ROC
            plt.figure(figsize=(8, 6))
            plt.plot(results['roc_curve']['fpr'], results['roc_curve']['tpr'], 
                    color='darkorange', lw=2,
                    label=f'ROC curve (area = {results["roc_curve"]["auc"]:.2f})')
            plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
            plt.xlim([0.0, 1.0])
            plt.ylim([0.0, 1.05])
            plt.xlabel('Taux de faux positifs')
            plt.ylabel('Taux de vrais positifs')
            plt.title('Courbe ROC')
            plt.legend(loc="lower right")
            plt.savefig(f"{output_dir}/roc_curve_{timestamp}.png")
            plt.close()
        
        if 'pr_curve' in results:
            # Courbe Précision-Rappel
            plt.figure(figsize=(8, 6))
            plt.plot(results['pr_curve']['recall'], results['pr_curve']['precision'], 
                    color='blue', lw=2,
                    label=f'PR curve (area = {results["pr_curve"]["auc"]:.2f})')
            plt.xlabel('Recall')
            plt.ylabel('Precision')
            plt.title('Courbe Précision-Rappel')
            plt.legend(loc="lower left")
            plt.savefig(f"{output_dir}/pr_curve_{timestamp}.png")
            plt.close()
        
        self.logger.info(f"Rapport d'évaluation sauvegardé dans {output_dir}")
        
        return f"{output_dir}/metrics_{timestamp}.json"
    
    def save_model(self, output_path='model/trained_models/optimized_model.pkl'):
        """Sauvegarde le modèle optimisé."""
        if self.model is None:
            self.logger.error("Aucun modèle à sauvegarder")
            return None
        
        # Créer le répertoire si nécessaire
        import os
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Sauvegarder le modèle
        joblib.dump(self.model, output_path)
        self.logger.info(f"Modèle sauvegardé dans {output_path}")
        
        return output_path