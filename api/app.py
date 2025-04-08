# app.py
# api/app.py
from api import create_app
from api.config import get_config

app = create_app(get_config())

@app.route('/health')
def health_check():
    """Route simple pour vérifier que l'API fonctionne"""
    return {'status': 'healthy', 'version': '1.0.0'}, 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)


# api/wsgi.py
from api.app import app

if __name__ == "__main__":
    app.run()



