import os

# Structure du projet
structure = {
    "api": [
        "__init__.py", "config.py", "app.py", "wsgi.py",
        {
            "routes": [
                "__init__.py",
                "auth_routes.py", "user_routes.py", "prediction_routes.py",
                "simulation_routes.py", "course_routes.py",
                "subscription_routes.py", "admin_routes.py"
            ]
        },
        {
            "services": [
                "__init__.py",
                "auth_service.py", "user_service.py", "prediction_service.py",
                "simulation_service.py", "notification_service.py", "subscription_service.py"
            ]
        },
        {
            "models": [
                "__init__.py",
                "user.py", "subscription.py", "prediction.py",
                "simulation.py", "course.py"
            ]
        },
        {
            "schemas": [
                "__init__.py",
                "user_schema.py", "prediction_schema.py", "simulation_schema.py"
            ]
        },
        {
            "middleware": [
                "__init__.py",
                "auth_middleware.py", "rate_limiter.py", "error_handler.py"
            ]
        },
        {
            "utils": [
                "__init__.py",
                "validators.py", "decorators.py", "firebase_client.py",
                "email_sender.py", "logger.py"
            ]
        },
        {
            "tasks": [
                "__init__.py",
                "training_scheduler.py", "data_updater.py", "notification_sender.py"
            ]
        },
        {
            "tests": [
                "__init__.py", "conftest.py", "test_auth.py",
                "test_predictions.py", "test_simulations.py"
            ]
        }
    ]
}

def create_structure(base_path, tree):
    for item in tree:
        if isinstance(item, dict):
            for folder, sub_items in item.items():
                folder_path = os.path.join(base_path, folder)
                os.makedirs(folder_path, exist_ok=True)
                create_structure(folder_path, sub_items)
        else:
            file_path = os.path.join(base_path, item)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"# {item}\n")

# Point de départ
if __name__ == "__main__":
    root = "api"
    os.makedirs(root, exist_ok=True)
    create_structure(root, structure["api"])  # <- on passe "api" comme base_path
    print("Structure du projet API Flask créée avec succès.")
