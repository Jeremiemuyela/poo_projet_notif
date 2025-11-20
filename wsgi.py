"""
Point d'entrée WSGI pour le déploiement en production.
Ce fichier est utilisé par gunicorn et autres serveurs WSGI.
"""
from app import app

if __name__ == "__main__":
    app.run()


