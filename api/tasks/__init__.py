# __init__.py
# __init__.py
# api/tasks/__init__.py
import logging
import threading
import time
import uuid
from datetime import datetime, timedelta
from flask import current_app

logger = logging.getLogger(__name__)

# Dictionnaire pour suivre les tâches en cours d'exécution
running_tasks = {}

class TaskManager:
    """Gestionnaire pour exécuter les tâches planifiées"""
    
    def __init__(self):
        self.tasks = {
            'scraping': self.run_scraping,
            'prediction_generation': self.run_prediction_generation,
            'model_training': self.run_model_training,
            'model_evaluation': self.run_model_evaluation,
            'notification_sending': self.run_notification_sending,
            'data_cleanup': self.run_data_cleanup
        }
    
    def run_task(self, task_name, params=None):
        """
        Exécute une tâche dans un thread séparé.
        
        Args:
            task_name (str): Nom de la tâche à exécuter
            params (dict): Paramètres à passer à la tâche
            
        Returns:
            str: ID de la tâche ou None si la tâche n'existe pas
        """
        if task_name not in self.tasks:
            logger.error(f"Task {task_name} not found")
            return None
        
        # Créer un ID unique pour la tâche
        task_id = str(uuid.uuid4())
        
        # Créer un thread pour exécuter la tâche
        thread = threading.Thread(
            target=self._run_task_with_logging,
            args=(task_id, task_name, self.tasks[task_name], params)
        )
        thread.daemon = True
        
        # Enregistrer la tâche
        running_tasks[task_id] = {
            'task_name': task_name,
            'params': params,
            'start_time': datetime.now(),
            'status': 'running',
            'thread': thread
        }
        
        # Démarrer le thread
        thread.start()
        
        logger.info(f"Task {task_name} started with ID {task_id}")
        return task_id
    
    def _run_task_with_logging(self, task_id, task_name, task_func, params):
        """
        Exécute une tâche avec journalisation des erreurs.
        
        Args:
            task_id (str): ID de la tâche
            task_name (str): Nom de la tâche
            task_func (callable): Fonction à exécuter
            params (dict): Paramètres à passer à la fonction
        """
        try:
            logger.info(f"Running task {task_name} with ID {task_id}")
            
            # Exécuter la tâche
            if params:
                result = task_func(**params)
            else:
                result = task_func()
            
            # Mettre à jour le statut de la tâche
            running_tasks[task_id]['status'] = 'completed'
            running_tasks[task_id]['end_time'] = datetime.now()
            running_tasks[task_id]['result'] = result
            
            logger.info(f"Task {task_name} completed successfully")
            
        except Exception as e:
            # Journaliser l'erreur
            logger.error(f"Error in task {task_name}: {str(e)}", exc_info=True)
            
            # Mettre à jour le statut de la tâche
            running_tasks[task_id]['status'] = 'failed'
            running_tasks[task_id]['end_time'] = datetime.now()
            running_tasks[task_id]['error'] = str(e)
    
    def get_task_status(self, task_id):
        """
        Récupère le statut d'une tâche.
        
        Args:
            task_id (str): ID de la tâche
            
        Returns:
            dict: Statut de la tâche ou None si la tâche n'existe pas
        """
        if task_id not in running_tasks:
            return None
        
        task = running_tasks[task_id].copy()
        
        # Ne pas exposer l'objet thread
        if 'thread' in task:
            del task['thread']
        
        return task
    
    def get_running_tasks(self):
        """
        Récupère la liste des tâches en cours d'exécution.
        
        Returns:
            list: Liste des tâches en cours d'exécution
        """
        tasks = []
        
        for task_id, task in running_tasks.items():
            if task['status'] == 'running':
                task_copy = task.copy()
                
                # Ne pas exposer l'objet thread
                if 'thread' in task_copy:
                    del task_copy['thread']
                
                # Ajouter l'ID de la tâche
                task_copy['id'] = task_id
                
                tasks.append(task_copy)
        
        return tasks
    
    def run_scraping(self, days_back=None, specific_date=None):
        """
        Exécute le scraping des données de courses.
        
        Args:
            days_back (int): Nombre de jours à remonter pour le scraping
            specific_date (str): Date spécifique pour le scraping (format: YYYY-MM-DD)
            
        Returns:
            dict: Résultat du scraping
        """
        from tasks.data_updater import run_scraping
        
        # Lire la configuration
        if days_back is None:
            # Récupérer depuis la configuration
            from config import get_config
            config = get_config()
            days_back = config.SCRAPING_DAYS_BACK
        
        # Exécuter le scraping
        result = run_scraping(days_back, specific_date)
        
        return result
    
    def run_prediction_generation(self, days_ahead=None):
        """
        Génère des prédictions pour les courses à venir.
        
        Args:
            days_ahead (int): Nombre de jours à l'avance pour générer les prédictions
            
        Returns:
            dict: Résultat de la génération de prédictions
        """
        from tasks.data_updater import generate_predictions
        
        # Lire la configuration
        if days_ahead is None:
            # Récupérer depuis la configuration
            from config import get_config
            config = get_config()
            days_ahead = config.PREDICTION_DAYS_AHEAD
        
        # Générer les prédictions
        result = generate_predictions(days_ahead)
        
        return result
    
    def run_model_training(self, days_back=None, model_type=None):
        """
        Entraîne les modèles de prédiction.
        
        Args:
            days_back (int): Nombre de jours de données à utiliser pour l'entraînement
            model_type (str): Type de modèle à entraîner
            
        Returns:
            dict: Résultat de l'entraînement
        """
        from tasks.training_scheduler import train_models
        
        # Lire la configuration
        if days_back is None or model_type is None:
            # Récupérer depuis la configuration
            from config import get_config
            config = get_config()
            days_back = days_back or config.TRAINING_DAYS_BACK
            model_type = model_type or config.TRAINING_MODEL_TYPE
        
        # Entraîner les modèles
        result = train_models(days_back, model_type)
        
        return result
    
    def run_model_evaluation(self, days_back=None):
        """
        Évalue les performances des modèles de prédiction.
        
        Args:
            days_back (int): Nombre de jours de données à utiliser pour l'évaluation
            
        Returns:
            dict: Résultat de l'évaluation
        """
        from tasks.training_scheduler import evaluate_models
        
        # Lire la configuration
        if days_back is None:
            # Récupérer depuis la configuration
            from config import get_config
            config = get_config()
            days_back = config.EVALUATION_DAYS_BACK
        
        # Évaluer les modèles
        result = evaluate_models(days_back)
        
        return result
    
    def run_notification_sending(self, notification_type=None):
        """
        Envoie des notifications aux utilisateurs.
        
        Args:
            notification_type (str): Type de notification à envoyer
            
        Returns:
            dict: Résultat de l'envoi de notifications
        """
        from tasks.notification_sender import send_notifications
        
        # Envoyer les notifications
        result = send_notifications(notification_type)
        
        return result
    
    def run_data_cleanup(self, days_to_keep=60):
        """
        Nettoie les anciennes données.
        
        Args:
            days_to_keep (int): Nombre de jours de données à conserver
            
        Returns:
            dict: Résultat du nettoyage
        """
        from tasks.data_updater import cleanup_old_data
        
        # Nettoyer les données
        result = cleanup_old_data(days_to_keep)
        
        return result

# Créer une instance du gestionnaire de tâches
task_manager = TaskManager()