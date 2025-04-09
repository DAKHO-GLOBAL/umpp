# __init__.py
# api/routes/__init__.py
def register_routes(app):
    """Enregistre toutes les routes de l'application"""
    
    # Import des blueprints
    from routes.auth_routes import auth_bp
    from routes.user_routes import user_bp
    from routes.prediction_routes import prediction_bp
    from routes.simulation_routes import simulation_bp
    from routes.course_routes import course_bp
    from routes.subscription_routes import subscription_bp
    from routes.admin_routes import admin_bp
    
    # Enregistrement des blueprints avec préfixes
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(user_bp, url_prefix='/api/users')
    app.register_blueprint(prediction_bp, url_prefix='/api/predictions')
    app.register_blueprint(simulation_bp, url_prefix='/api/simulations')
    app.register_blueprint(course_bp, url_prefix='/api/courses')
    app.register_blueprint(subscription_bp, url_prefix='/api/subscriptions')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    
    # Journal des routes enregistrées
    app.logger.info('Routes registered successfully')