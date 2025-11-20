# Dockerfile pour le système de notification d'urgence
# Utilise Python 3.11 comme image de base
# Si vous avez des problèmes de connexion, essayez python:3.11-alpine à la place
FROM python:3.11-slim

# Définir le répertoire de travail
WORKDIR /app

# Installer les dépendances système si nécessaire
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copier le fichier requirements.txt
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copier tout le code de l'application
COPY . .

# Créer les répertoires nécessaires
RUN mkdir -p /app/data /app/migrations

# Exposer le port 5000 (peut être surchargé avec la variable d'environnement PORT)
EXPOSE 5000

# Variables d'environnement par défaut
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PORT=5000

# Commande pour démarrer l'application avec gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120", "app:app"]

