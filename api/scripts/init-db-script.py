#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script pour insérer des utilisateurs dans une base de données MySQL existante.
Adapté pour fonctionner avec la configuration MySQL de votre application.
"""

import sys
import os
import json
from datetime import datetime, timedelta
import pymysql
from werkzeug.security import generate_password_hash

# Configuration de la base de données MySQL
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "pmu_ia",
    "port": 3306,
    "charset": "utf8mb4"
}

def create_test_users():
    """
    Insère des utilisateurs de test dans la base de données MySQL
    """
    print("Tentative de connexion à la base de données MySQL...")
    print(f"Host: {DB_CONFIG['host']}, Database: {DB_CONFIG['database']}")
    
    try:
        # Connexion à la base de données MySQL
        conn = pymysql.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database=DB_CONFIG['database'],
            port=DB_CONFIG['port'],
            charset=DB_CONFIG['charset'],
            cursorclass=pymysql.cursors.DictCursor
        )
        
        cursor = conn.cursor()
        print("Connexion à la base de données MySQL réussie")
        
        # Vérifier si la table users existe
        cursor.execute("SHOW TABLES LIKE 'users'")
        if not cursor.fetchone():
            print("La table 'users' n'existe pas. Création des tables...")
            create_tables(cursor)
        
        # Créer l'administrateur
        cursor.execute("SELECT id FROM users WHERE email = %s", ('admin@pmu-ia.com',))
        admin_exists = cursor.fetchone()
        
        if not admin_exists:
            # Date actuelle et date d'expiration
            now = datetime.now()
            expiry = now + timedelta(days=365)
            
            # Insérer l'administrateur
            cursor.execute("""
                INSERT INTO users 
                (email, username, password_hash, first_name, last_name, is_active, is_admin, is_verified, 
                subscription_level, subscription_start, subscription_expiry, created_at, updated_at) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                'admin@pmu-ia.com', 'admin', generate_password_hash('AdminPass123'),
                'Admin', 'Système', True, True, True, 'premium', now, expiry, now, now
            ))
            
            admin_id = cursor.lastrowid
            
            # Vérifier si la table notification_settings existe
            cursor.execute("SHOW TABLES LIKE 'notification_settings'")
            if cursor.fetchone():
                # Insérer les paramètres de notification
                cursor.execute("""
                    INSERT INTO notification_settings 
                    (user_id, email_notifications, push_notifications, notify_predictions, 
                    notify_odds_changes, notify_upcoming_races, min_minutes_before_race, created_at, updated_at) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    admin_id, True, True, True, True, True, 60, now, now
                ))
            
            # Vérifier si la table user_subscriptions existe
            cursor.execute("SHOW TABLES LIKE 'user_subscriptions'")
            if cursor.fetchone():
                # Insérer l'abonnement
                cursor.execute("""
                    INSERT INTO user_subscriptions 
                    (user_id, plan, start_date, end_date, price, payment_method, status, auto_renew, created_at, updated_at) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    admin_id, 'premium', now, expiry, 199.99, 'manual', 'active', True, now, now
                ))
            
            print("Administrateur créé avec succès!")
        else:
            print("L'administrateur existe déjà.")
        
        # Créer l'utilisateur premium
        cursor.execute("SELECT id FROM users WHERE email = %s", ('premium@pmu-ia.com',))
        premium_exists = cursor.fetchone()
        
        if not premium_exists:
            # Date actuelle et date d'expiration
            now = datetime.now()
            expiry = now + timedelta(days=90)
            
            # Insérer l'utilisateur premium
            cursor.execute("""
                INSERT INTO users 
                (email, username, password_hash, first_name, last_name, is_active, is_admin, is_verified, 
                subscription_level, subscription_start, subscription_expiry, created_at, updated_at) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                'premium@pmu-ia.com', 'premium_user', generate_password_hash('PremiumPass123'),
                'Pierre', 'Dupont', True, False, True, 'premium', now, expiry, now, now
            ))
            
            premium_id = cursor.lastrowid
            
            # Vérifier si la table notification_settings existe
            cursor.execute("SHOW TABLES LIKE 'notification_settings'")
            if cursor.fetchone():
                # Insérer les paramètres de notification
                cursor.execute("""
                    INSERT INTO notification_settings 
                    (user_id, email_notifications, push_notifications, notify_predictions, 
                    notify_odds_changes, notify_upcoming_races, min_minutes_before_race, created_at, updated_at) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    premium_id, True, True, True, True, True, 30, now, now
                ))
            
            # Vérifier si la table user_subscriptions existe
            cursor.execute("SHOW TABLES LIKE 'user_subscriptions'")
            if cursor.fetchone():
                # Insérer l'abonnement
                cursor.execute("""
                    INSERT INTO user_subscriptions 
                    (user_id, plan, start_date, end_date, price, payment_method, status, auto_renew, created_at, updated_at) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    premium_id, 'premium', now, expiry, 19.99, 'credit_card', 'active', True, now, now
                ))
            
            print("Utilisateur premium créé avec succès!")
        else:
            print("L'utilisateur premium existe déjà.")
        
        # Créer l'utilisateur gratuit
        cursor.execute("SELECT id FROM users WHERE email = %s", ('free@pmu-ia.com',))
        free_exists = cursor.fetchone()
        
        if not free_exists:
            # Date actuelle
            now = datetime.now()
            
            # Insérer l'utilisateur gratuit
            cursor.execute("""
                INSERT INTO users 
                (email, username, password_hash, first_name, last_name, is_active, is_admin, is_verified, 
                subscription_level, created_at, updated_at) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                'free@pmu-ia.com', 'free_user', generate_password_hash('FreePass123'),
                'Marie', 'Martin', True, False, True, 'free', now, now
            ))
            
            free_id = cursor.lastrowid
            
            # Vérifier si la table notification_settings existe
            cursor.execute("SHOW TABLES LIKE 'notification_settings'")
            if cursor.fetchone():
                # Insérer les paramètres de notification
                cursor.execute("""
                    INSERT INTO notification_settings 
                    (user_id, email_notifications, push_notifications, notify_predictions, 
                    notify_odds_changes, notify_upcoming_races, min_minutes_before_race, created_at, updated_at) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    free_id, True, False, True, False, False, 60, now, now
                ))
            
            print("Utilisateur gratuit créé avec succès!")
        else:
            print("L'utilisateur gratuit existe déjà.")
        
        # Valider les changements
        conn.commit()
        print("Tous les utilisateurs ont été insérés avec succès!")
        return True
    
    except pymysql.Error as e:
        print(f"Erreur MySQL ({e.args[0]}): {e.args[1]}")
        if conn:
            conn.rollback()
        return False
    
    except Exception as e:
        print(f"Erreur inattendue: {e}")
        if 'conn' in locals() and conn:
            conn.rollback()
        return False
    
    finally:
        if 'conn' in locals() and conn:
            conn.close()
            print("Connexion à la base de données fermée")

def create_tables(cursor):
    """Crée les tables nécessaires si elles n'existent pas"""
    try:
        # Table users
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                email VARCHAR(120) NOT NULL UNIQUE,
                username VARCHAR(80) NOT NULL UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                first_name VARCHAR(50),
                last_name VARCHAR(50),
                profile_picture VARCHAR(255),
                bio TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                is_admin BOOLEAN DEFAULT FALSE,
                is_verified BOOLEAN DEFAULT FALSE,
                verification_token VARCHAR(100),
                subscription_level VARCHAR(20) DEFAULT 'free',
                subscription_start DATETIME,
                subscription_expiry DATETIME,
                billing_address TEXT,
                payment_info TEXT,
                login_count INT DEFAULT 0,
                last_login DATETIME,
                prediction_count INT DEFAULT 0,
                success_rate FLOAT DEFAULT 0.0,
                preferences TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                INDEX (email),
                INDEX (username)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        
        # Table notification_settings
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notification_settings (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL UNIQUE,
                email_notifications BOOLEAN DEFAULT TRUE,
                push_notifications BOOLEAN DEFAULT TRUE,
                notify_predictions BOOLEAN DEFAULT TRUE,
                notify_odds_changes BOOLEAN DEFAULT TRUE,
                notify_upcoming_races BOOLEAN DEFAULT TRUE,
                min_minutes_before_race INT DEFAULT 60,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                INDEX (user_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        
        # Table user_subscriptions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_subscriptions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                plan VARCHAR(20) NOT NULL,
                start_date DATETIME NOT NULL,
                end_date DATETIME,
                price FLOAT,
                payment_method VARCHAR(50),
                payment_reference VARCHAR(100),
                status VARCHAR(20) DEFAULT 'active',
                auto_renew BOOLEAN DEFAULT FALSE,
                cancelled_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                INDEX (user_id),
                INDEX (plan),
                INDEX (status)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        
        # Table subscription_plans
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS subscription_plans (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(50) NOT NULL UNIQUE,
                display_name VARCHAR(100) NOT NULL,
                description TEXT,
                price_monthly FLOAT NOT NULL,
                price_quarterly FLOAT,
                price_yearly FLOAT,
                features JSON NOT NULL,
                limits JSON NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                INDEX (name),
                INDEX (is_active)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        
        # Insertion des plans d'abonnement
        # Vérifier si des plans existent déjà
        cursor.execute("SELECT COUNT(*) as count FROM subscription_plans")
        result = cursor.fetchone()
        plan_count = result['count']
        
        if plan_count == 0:
            now = datetime.now()
            
            # Plan gratuit
            cursor.execute("""
                INSERT INTO subscription_plans
                (name, display_name, description, price_monthly, price_quarterly, price_yearly, features, limits, is_active, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                'free',
                'Gratuit',
                'Accès de base aux prédictions et simulations',
                0.0,
                0.0,
                0.0,
                json.dumps(['basic_predictions']),
                json.dumps({'predictions_per_day': 5, 'simulations_per_day': 2}),
                True,
                now,
                now
            ))
            
            # Plan standard
            cursor.execute("""
                INSERT INTO subscription_plans
                (name, display_name, description, price_monthly, price_quarterly, price_yearly, features, limits, is_active, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                'standard',
                'Standard',
                'Accès avancé aux prédictions et simulations de base',
                9.99,
                24.99,
                99.99,
                json.dumps(['basic_predictions', 'top3_predictions', 'basic_simulations']),
                json.dumps({'predictions_per_day': 30, 'simulations_per_day': 15}),
                True,
                now,
                now
            ))
            
            # Plan premium
            cursor.execute("""
                INSERT INTO subscription_plans
                (name, display_name, description, price_monthly, price_quarterly, price_yearly, features, limits, is_active, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                'premium',
                'Premium',
                'Accès illimité à toutes les fonctionnalités',
                19.99,
                49.99,
                199.99,
                json.dumps(['basic_predictions', 'top3_predictions', 'top7_predictions', 'basic_simulations', 'advanced_simulations', 'notifications']),
                json.dumps({'predictions_per_day': -1, 'simulations_per_day': -1}),
                True,
                now,
                now
            ))
            
            print("Plans d'abonnement créés avec succès")
        
        print("Tables créées avec succès")
        return True
    
    except pymysql.Error as e:
        print(f"Erreur lors de la création des tables: {e}")
        return False

if __name__ == "__main__":
    # Vérifier que pymysql est installé
    try:
        import pymysql
        print("Module pymysql trouvé, version:", pymysql.__version__)
    except ImportError:
        print("Le module pymysql n'est pas installé. Installation en cours...")
        import subprocess
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pymysql"])
            print("Module pymysql installé avec succès!")
            import pymysql
        except Exception as e:
            print(f"Impossible d'installer pymysql: {e}")
            print("Veuillez l'installer manuellement avec: pip install pymysql")
            sys.exit(1)
    
    create_test_users()