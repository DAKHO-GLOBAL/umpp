# api/wsgi.py
import os
import sys

# Ajouter le répertoire racine au chemin de recherche
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, root_dir)

from api.app import create_app
from api.config import get_config

app = create_app(get_config())

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)