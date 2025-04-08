# validators.py
# validators.py
# api/utils/validators.py
import re
from datetime import datetime
import uuid

def is_valid_email(email):
    """
    Valide un format d'email.
    
    Args:
        email (str): Adresse email à valider
        
    Returns:
        bool: True si l'email est valide, False sinon
    """
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return bool(re.match(pattern, email))

def is_valid_password(password, min_length=8):
    """
    Vérifie si un mot de passe respecte les critères de sécurité.
    
    Args:
        password (str): Mot de passe à valider
        min_length (int): Longueur minimale
        
    Returns:
        tuple: (valid, message) - valid est un booléen, message est l'erreur si invalide
    """
    if len(password) < min_length:
        return False, f"Password must be at least {min_length} characters long"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one number"
    
    return True, ""

def is_valid_username(username):
    """
    Vérifie si un nom d'utilisateur est valide.
    
    Args:
        username (str): Nom d'utilisateur à valider
        
    Returns:
        bool: True si le nom d'utilisateur est valide, False sinon
    """
    # Lettres, chiffres et underscore uniquement, entre 3 et 30 caractères
    pattern = r'^[a-zA-Z0-9_]{3,30}$'
    return bool(re.match(pattern, username))

def is_valid_date(date_str, format='%Y-%m-%d'):
    """
    Vérifie si une chaîne est une date valide au format spécifié.
    
    Args:
        date_str (str): Chaîne de date à valider
        format (str): Format de date attendu
        
    Returns:
        bool: True si la date est valide, False sinon
    """
    try:
        datetime.strptime(date_str, format)
        return True
    except ValueError:
        return False

def is_valid_uuid(uuid_str):
    """
    Vérifie si une chaîne est un UUID valide.
    
    Args:
        uuid_str (str): Chaîne UUID à valider
        
    Returns:
        bool: True si l'UUID est valide, False sinon
    """
    try:
        uuid_obj = uuid.UUID(uuid_str)
        return str(uuid_obj) == uuid_str
    except (ValueError, AttributeError):
        return False

def is_valid_phone(phone_number):
    """
    Vérifie si un numéro de téléphone est valide.
    
    Args:
        phone_number (str): Numéro de téléphone à valider
        
    Returns:
        bool: True si le numéro est valide, False sinon
    """
    # Format international, avec ou sans le +
    pattern = r'^(\+\d{1,3})?[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}$'
    return bool(re.match(pattern, phone_number))

def is_valid_url(url):
    """
    Vérifie si une URL est valide.
    
    Args:
        url (str): URL à valider
        
    Returns:
        bool: True si l'URL est valide, False sinon
    """
    pattern = r'^(https?://)?(www\.)?[-a-zA-Z0-9@:%._+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_+.~#?&/=]*)$'
    return bool(re.match(pattern, url))

def is_valid_subscription_level(level):
    """
    Vérifie si un niveau d'abonnement est valide.
    
    Args:
        level (str): Niveau d'abonnement à valider
        
    Returns:
        bool: True si le niveau est valide, False sinon
    """
    valid_levels = ['free', 'standard', 'premium']
    return level in valid_levels

def is_valid_prediction_type(prediction_type):
    """
    Vérifie si un type de prédiction est valide.
    
    Args:
        prediction_type (str): Type de prédiction à valider
        
    Returns:
        bool: True si le type est valide, False sinon
    """
    valid_types = ['standard', 'top3', 'top7', 'realtime']
    return prediction_type in valid_types

def is_valid_simulation_type(simulation_type):
    """
    Vérifie si un type de simulation est valide.
    
    Args:
        simulation_type (str): Type de simulation à valider
        
    Returns:
        bool: True si le type est valide, False sinon
    """
    valid_types = ['basic', 'advanced', 'comparison']
    return simulation_type in valid_types

def is_valid_payment_method(payment_method):
    """
    Vérifie si une méthode de paiement est valide.
    
    Args:
        payment_method (str): Méthode de paiement à valider
        
    Returns:
        bool: True si la méthode est valide, False sinon
    """
    valid_methods = ['credit_card', 'paypal', 'bank_transfer', 'mobile_money', 'crypto', 'orange_money', 'free_trial']
    return payment_method in valid_methods

def sanitize_input(input_str):
    """
    Sanitize une chaîne d'entrée pour éviter les injections.
    
    Args:
        input_str (str): Chaîne à sanitizer
        
    Returns:
        str: Chaîne sanitizée
    """
    if input_str is None:
        return None
    
    # Supprimer les caractères HTML
    clean_str = re.sub(r'<[^>]*>', '', input_str)
    
    # Supprimer les séquences d'échappement SQL communes
    clean_str = clean_str.replace("'", "''")  # Échapper les apostrophes
    clean_str = clean_str.replace(";", "")  # Supprimer les points-virgules
    
    return clean_str

def validate_date_range(start_date, end_date, format='%Y-%m-%d'):
    """
    Vérifie si une plage de dates est valide.
    
    Args:
        start_date (str): Date de début
        end_date (str): Date de fin
        format (str): Format de date
        
    Returns:
        tuple: (valid, message) - valid est un booléen, message est l'erreur si invalide
    """
    if not is_valid_date(start_date, format):
        return False, f"Start date is not valid. Expected format: {format}"
    
    if not is_valid_date(end_date, format):
        return False, f"End date is not valid. Expected format: {format}"
    
    start = datetime.strptime(start_date, format)
    end = datetime.strptime(end_date, format)
    
    if start > end:
        return False, "Start date must be before end date"
    
    return True, ""