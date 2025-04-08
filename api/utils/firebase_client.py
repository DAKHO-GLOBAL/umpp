# firebase_client.py
# firebase_client.py
# api/utils/firebase_client.py
import logging
import json
import requests
from flask import current_app
from google.oauth2 import service_account
import google.auth.transport.requests
import firebase_admin
from firebase_admin import credentials, messaging, auth

logger = logging.getLogger(__name__)

# Initialisation de l'app Firebase
firebase_app = None

def initialize_firebase():
    """Initialise l'application Firebase avec les credentials depuis la configuration"""
    global firebase_app
    
    if firebase_app:
        return firebase_app
    
    try:
        # Vérifier si les credentials sont disponibles
        firebase_credentials = current_app.config.get('FIREBASE_CREDENTIALS')
        
        if not firebase_credentials:
            # Essayer de charger depuis un fichier
            cred_path = current_app.config.get('FIREBASE_CREDENTIALS_PATH')
            
            if not cred_path:
                logger.error("Firebase credentials not provided")
                return None
            
            cred = credentials.Certificate(cred_path)
        else:
            # Utiliser les credentials fournis dans la configuration
            cred = credentials.Certificate(json.loads(firebase_credentials))
        
        # Initialiser l'application Firebase
        firebase_app = firebase_admin.initialize_app(cred)
        logger.info("Firebase initialized successfully")
        
        return firebase_app
        
    except Exception as e:
        logger.error(f"Error initializing Firebase: {str(e)}")
        return None


def verify_firebase_token(id_token):
    """Vérifie la validité d'un token ID Firebase"""
    try:
        # S'assurer que Firebase est initialisé
        if not firebase_app:
            initialize_firebase()
        
        # Vérifier le token
        decoded_token = auth.verify_id_token(id_token)
        
        return decoded_token
        
    except Exception as e:
        logger.error(f"Error verifying Firebase token: {str(e)}")
        return None


def send_push_notification(token, title, body, data=None):
    """
    Envoie une notification push à un appareil spécifique.
    
    Args:
        token (str): Le token FCM de l'appareil
        title (str): Le titre de la notification
        body (str): Le corps de la notification
        data (dict, optional): Données supplémentaires à envoyer avec la notification
    
    Returns:
        bool: True si la notification a été envoyée avec succès, False sinon
    """
    try:
        # S'assurer que Firebase est initialisé
        if not firebase_app:
            initialize_firebase()
        
        # Créer le message
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body
            ),
            data=data if data else {},
            token=token
        )
        
        # Envoyer le message
        response = messaging.send(message)
        
        logger.info(f"Push notification sent successfully: {response}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending push notification: {str(e)}")
        return False


def send_push_notification_to_multiple_devices(tokens, title, body, data=None):
    """
    Envoie une notification push à plusieurs appareils.
    
    Args:
        tokens (list): Liste des tokens FCM des appareils
        title (str): Le titre de la notification
        body (str): Le corps de la notification
        data (dict, optional): Données supplémentaires à envoyer avec la notification
    
    Returns:
        dict: Résultat de l'envoi des notifications
    """
    try:
        # S'assurer que Firebase est initialisé
        if not firebase_app:
            initialize_firebase()
        
        # Vérifier qu'il y a des tokens
        if not tokens:
            logger.warning("No FCM tokens provided for multicast")
            return {"success": 0, "failure": 0, "tokens": []}
        
        # Créer le message multicast
        message = messaging.MulticastMessage(
            notification=messaging.Notification(
                title=title,
                body=body
            ),
            data=data if data else {},
            tokens=tokens
        )
        
        # Envoyer le message
        response = messaging.send_multicast(message)
        
        logger.info(f"Multicast push notification sent: {response.success_count} successful, {response.failure_count} failed")
        
        # Collecter les résultats détaillés
        results = []
        for idx, resp in enumerate(response.responses):
            results.append({
                "token": tokens[idx],
                "success": resp.success,
                "error": str(resp.exception) if not resp.success else None
            })
        
        return {
            "success": response.success_count,
            "failure": response.failure_count,
            "tokens": results
        }
        
    except Exception as e:
        logger.error(f"Error sending multicast push notification: {str(e)}")
        return {"success": 0, "failure": len(tokens), "error": str(e), "tokens": []}


def send_topic_notification(topic, title, body, data=None):
    """
    Envoie une notification push à tous les appareils abonnés à un sujet.
    
    Args:
        topic (str): Le sujet auquel envoyer la notification
        title (str): Le titre de la notification
        body (str): Le corps de la notification
        data (dict, optional): Données supplémentaires à envoyer avec la notification
    
    Returns:
        bool: True si la notification a été envoyée avec succès, False sinon
    """
    try:
        # S'assurer que Firebase est initialisé
        if not firebase_app:
            initialize_firebase()
        
        # Créer le message
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body
            ),
            data=data if data else {},
            topic=topic
        )
        
        # Envoyer le message
        response = messaging.send(message)
        
        logger.info(f"Topic notification sent successfully: {response}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending topic notification: {str(e)}")
        return False


def subscribe_to_topic(tokens, topic):
    """
    Abonne des appareils à un sujet pour recevoir des notifications.
    
    Args:
        tokens (list): Liste des tokens FCM des appareils
        topic (str): Le sujet auquel s'abonner
    
    Returns:
        dict: Résultat de l'abonnement
    """
    try:
        # S'assurer que Firebase est initialisé
        if not firebase_app:
            initialize_firebase()
        
        # Vérifier qu'il y a des tokens
        if not tokens:
            logger.warning("No FCM tokens provided for topic subscription")
            return {"success": 0, "failure": 0, "tokens": []}
        
        # Abonner les appareils au sujet
        response = messaging.subscribe_to_topic(tokens, topic)
        
        logger.info(f"Topic subscription: {response.success_count} successful, {response.failure_count} failed")
        
        # Collecter les résultats détaillés
        results = []
        for idx, error in enumerate(response.errors):
            token = tokens[idx]
            results.append({
                "token": token,
                "success": error.code == messaging.TopicManagementErrorCode.NOT_FOUND,
                "error": str(error.message) if error.code != messaging.TopicManagementErrorCode.NOT_FOUND else None
            })
        
        return {
            "success": response.success_count,
            "failure": response.failure_count,
            "tokens": results
        }
        
    except Exception as e:
        logger.error(f"Error subscribing to topic: {str(e)}")
        return {"success": 0, "failure": len(tokens), "error": str(e), "tokens": []}
    

def unsubscribe_from_topic(tokens, topic):
    """
    Désabonne des appareils d'un sujet.
    
    Args:
        tokens (list): Liste des tokens FCM des appareils
        topic (str): Le sujet dont se désabonner
    
    Returns:
        dict: Résultat du désabonnement
    """
    try:
        # S'assurer que Firebase est initialisé
        if not firebase_app:
            initialize_firebase()
        
        # Vérifier qu'il y a des tokens
        if not tokens:
            logger.warning("No FCM tokens provided for topic unsubscription")
            return {"success": 0, "failure": 0, "tokens": []}
        
        # Désabonner les appareils du sujet
        response = messaging.unsubscribe_from_topic(tokens, topic)
        
        logger.info(f"Topic unsubscription: {response.success_count} successful, {response.failure_count} failed")
        
        # Collecter les résultats détaillés
        results = []
        for idx, error in enumerate(response.errors):
            token = tokens[idx]
            results.append({
                "token": token,
                "success": error.code == messaging.TopicManagementErrorCode.NOT_FOUND,
                "error": str(error.message) if error.code != messaging.TopicManagementErrorCode.NOT_FOUND else None
            })
        
        return {
            "success": response.success_count,
            "failure": response.failure_count,
            "tokens": results
        }
        
    except Exception as e:
        logger.error(f"Error unsubscribing from topic: {str(e)}")
        return {"success": 0, "failure": len(tokens), "error": str(e), "tokens": []}


def validate_fcm_token(token):
    """
    Vérifie la validité formelle d'un token FCM.
    
    Args:
        token (str): Le token FCM à valider
    
    Returns:
        bool: True si le token a un format valide, False sinon
    """
    # Vérifier les caractéristiques basiques d'un token FCM
    if not token or not isinstance(token, str):
        return False
    
    # Les tokens FCM ont une longueur minimale
    if len(token) < 100:
        return False
    
    # Les tokens FCM commencent généralement par certaines séquences
    valid_prefixes = ['f', 'd', 'e', 'c']
    if token[0].lower() not in valid_prefixes:
        return False
    
    # Vérifier la présence de caractères invalides
    import re
    if re.search(r'[^a-zA-Z0-9:_-]', token):
        return False
    
    return True