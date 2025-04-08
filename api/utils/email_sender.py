# email_sender.py
# email_sender.py
# api/utils/email_sender.py
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app, render_template

logger = logging.getLogger(__name__)

def send_email(recipient, subject, body, template_name=None, data=None, html=True):
    """
    Envoie un email à un destinataire.
    
    Args:
        recipient (str): L'adresse email du destinataire
        subject (str): Le sujet de l'email
        body (str): Le corps du message (utilisé si template_name est None)
        template_name (str, optional): Nom du template à utiliser
        data (dict, optional): Données à passer au template
        html (bool, optional): Si True, l'email sera au format HTML
    
    Returns:
        bool: True si l'email a été envoyé avec succès, False sinon
    """
    try:
        # Récupérer les paramètres de configuration
        mail_server = current_app.config.get('MAIL_SERVER')
        mail_port = current_app.config.get('MAIL_PORT')
        mail_use_tls = current_app.config.get('MAIL_USE_TLS')
        mail_username = current_app.config.get('MAIL_USERNAME')
        mail_password = current_app.config.get('MAIL_PASSWORD')
        mail_default_sender = current_app.config.get('MAIL_DEFAULT_SENDER')
        
        if not mail_server or not mail_username or not mail_password:
            logger.error("Missing email configuration")
            return False
        
        # Créer le message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = mail_default_sender
        msg['To'] = recipient
        
        # Utiliser un template si spécifié
        if template_name:
            try:
                # Utiliser le template spécifié
                if html:
                    html_content = render_template(f'emails/{template_name}.html', **data)
                    msg.attach(MIMEText(html_content, 'html'))
                    
                    # Ajouter également une version texte
                    text_content = render_template(f'emails/{template_name}.txt', **data)
                    msg.attach(MIMEText(text_content, 'plain'))
                else:
                    text_content = render_template(f'emails/{template_name}.txt', **data)
                    msg.attach(MIMEText(text_content, 'plain'))
            except Exception as template_error:
                logger.error(f"Error rendering email template: {str(template_error)}")
                # Fallback to plain text
                msg.attach(MIMEText(body, 'plain'))
        else:
            # Utiliser le corps fourni directement
            msg.attach(MIMEText(body, 'html' if html else 'plain'))
        
        # Se connecter au serveur SMTP et envoyer l'email
        with smtplib.SMTP(mail_server, mail_port) as server:
            if mail_use_tls:
                server.starttls()
            server.login(mail_username, mail_password)
            server.sendmail(mail_default_sender, recipient, msg.as_string())
        
        logger.info(f"Email sent successfully to {recipient}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        return False


def send_welcome_email(user_email, user_name):
    """Envoie un email de bienvenue à un nouvel utilisateur"""
    subject = "Bienvenue sur notre plateforme de prédiction PMU !"
    
    data = {
        'user_name': user_name,
        'app_name': current_app.config.get('APP_NAME', 'Notre plateforme PMU'),
        'support_email': current_app.config.get('SUPPORT_EMAIL', 'support@example.com')
    }
    
    return send_email(
        recipient=user_email,
        subject=subject,
        body="",  # Le contenu sera fourni par le template
        template_name='welcome',
        data=data,
        html=True
    )


def send_reset_password_email(user_email, reset_token, expiration_minutes=60):
    """Envoie un email de réinitialisation de mot de passe"""
    subject = "Réinitialisation de votre mot de passe"
    
    frontend_url = current_app.config.get('FRONTEND_URL', 'http://localhost:3000')
    reset_url = f"{frontend_url}/reset-password?token={reset_token}"
    
    data = {
        'reset_url': reset_url,
        'expiration_minutes': expiration_minutes,
        'app_name': current_app.config.get('APP_NAME', 'Notre plateforme PMU'),
        'support_email': current_app.config.get('SUPPORT_EMAIL', 'support@example.com')
    }
    
    return send_email(
        recipient=user_email,
        subject=subject,
        body="",  # Le contenu sera fourni par le template
        template_name='reset_password',
        data=data,
        html=True
    )


def send_prediction_notification_email(user_email, course_data, prediction_data):
    """Envoie un email de notification de prédiction"""
    subject = f"Prédiction disponible pour {course_data['lieu']}"
    
    data = {
        'course': course_data,
        'prediction': prediction_data,
        'app_name': current_app.config.get('APP_NAME', 'Notre plateforme PMU'),
        'frontend_url': current_app.config.get('FRONTEND_URL', 'http://localhost:3000')
    }
    
    return send_email(
        recipient=user_email,
        subject=subject,
        body="",  # Le contenu sera fourni par le template
        template_name='prediction_notification',
        data=data,
        html=True
    )


def send_odds_change_notification_email(user_email, course_data, changed_horses):
    """Envoie un email de notification de changement de cotes"""
    subject = f"Mouvements de cotes pour {course_data['lieu']}"
    
    data = {
        'course': course_data,
        'changed_horses': changed_horses,
        'app_name': current_app.config.get('APP_NAME', 'Notre plateforme PMU'),
        'frontend_url': current_app.config.get('FRONTEND_URL', 'http://localhost:3000')
    }
    
    return send_email(
        recipient=user_email,
        subject=subject,
        body="",  # Le contenu sera fourni par le template
        template_name='odds_change_notification',
        data=data,
        html=True
    )


def send_upcoming_race_notification_email(user_email, course_data, time_before_start):
    """Envoie un email de notification de course à venir"""
    hours = time_before_start // 60
    minutes = time_before_start % 60
    
    if hours > 0:
        time_text = f"{hours}h {minutes}min" if minutes > 0 else f"{hours}h"
    else:
        time_text = f"{minutes}min"
    
    subject = f"Course dans {time_text} à {course_data['lieu']}"
    
    data = {
        'course': course_data,
        'time_before_start': time_before_start,
        'time_text': time_text,
        'app_name': current_app.config.get('APP_NAME', 'Notre plateforme PMU'),
        'frontend_url': current_app.config.get('FRONTEND_URL', 'http://localhost:3000')
    }
    
    return send_email(
        recipient=user_email,
        subject=subject,
        body="",  # Le contenu sera fourni par le template
        template_name='upcoming_race_notification',
        data=data,
        html=True
    )