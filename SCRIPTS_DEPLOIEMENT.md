# 🚀 Scripts et Fichiers de Déploiement

## 📍 Emplacement des Fichiers de Déploiement

Les fichiers de déploiement se trouvent à la **racine du projet** :

```
projetnotif - Copie/
├── Dockerfile              # Configuration Docker
├── Dockerfile.alternative   # Alternative Docker (Alpine)
├── docker-compose.yml      # Orchestration Docker
├── Procfile                # Configuration pour Railway/Heroku
├── wsgi.py                 # Point d'entrée WSGI
├── requirements.txt        # Dépendances Python
├── runtime.txt             # Version Python pour Heroku
└── .dockerignore          # Fichiers ignorés par Docker
```

---

## 📄 Fichiers de Déploiement

### 1. **Dockerfile** (Ligne 1-37)

**Emplacement** : `./Dockerfile`

**Rôle** : Définit l'image Docker de l'application

**Contenu principal** :
```dockerfile
FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y gcc curl
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p /app/data /app/migrations
EXPOSE 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120", "app:app"]
```

**Utilisation** :
```bash
docker build -t notification-system .
```

---

### 2. **docker-compose.yml** (Ligne 1-26)

**Emplacement** : `./docker-compose.yml`

**Rôle** : Orchestration Docker avec volumes et health checks

**Contenu principal** :
```yaml
services:
  web:
    build: .
    container_name: notification-system
    ports:
      - "5000:5000"
    environment:
      - SECRET_KEY=${SECRET_KEY:-changez-moi-en-production}
      - FLASK_ENV=production
    volumes:
      - ./notifications.db:/app/notifications.db:rw
      - ./data:/app/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/api/health"]
```

**Utilisation** :
```bash
docker-compose up -d
```

---

### 3. **Procfile** (Pour Railway/Heroku)

**Emplacement** : `./Procfile`

**Rôle** : Commande de démarrage pour plateformes cloud

**Contenu** :
```
web: gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 app:app
```

**Utilisation** : Automatique sur Railway/Heroku

---

### 4. **wsgi.py** (Point d'entrée WSGI)

**Emplacement** : `./wsgi.py`

**Rôle** : Point d'entrée pour serveurs WSGI (gunicorn, uwsgi)

**Contenu** :
```python
from app import app

if __name__ == "__main__":
    app.run()
```

**Utilisation** : Référencé par gunicorn dans Dockerfile et Procfile

---

## 🛠️ Commandes de Déploiement

### Déploiement Local avec Docker

#### 1. Construire l'image
```powershell
docker build -t notification-system .
```

#### 2. Lancer avec docker-compose
```powershell
docker-compose up -d
```

#### 3. Vérifier les logs
```powershell
docker-compose logs -f
```

#### 4. Arrêter
```powershell
docker-compose down
```

---

### Déploiement sur Railway

#### 1. Préparer le code
```powershell
git add .
git commit -m "Prêt pour déploiement"
git push origin main
```

#### 2. Sur Railway.app
1. Créer un nouveau projet
2. Connecter le repository GitHub
3. Railway détecte automatiquement le Dockerfile
4. Configurer les variables d'environnement :
   - `SECRET_KEY` : Votre clé secrète
   - `FLASK_ENV` : `production`

#### 3. Déploiement automatique
Railway utilise automatiquement :
- `Dockerfile` pour construire l'image
- `Procfile` pour démarrer l'application
- Variables d'environnement configurées

---

### Déploiement sur Render

#### 1. Préparer le code
```powershell
git push origin main
```

#### 2. Sur Render.com
1. Créer un nouveau Web Service
2. Connecter le repository GitHub
3. Configuration :
   - **Environment** : `Docker`
   - **Build Command** : (automatique)
   - **Start Command** : (automatique depuis Dockerfile)

#### 3. Variables d'environnement
Dans Render → Environment Variables :
- `SECRET_KEY` : Votre clé secrète
- `FLASK_ENV` : `production`

---

## 📝 Scripts de Déploiement Personnalisés

Si vous souhaitez créer des scripts de déploiement automatisés :

### Script PowerShell : `deploy.ps1`

```powershell
# deploy.ps1
# Script de déploiement pour Windows PowerShell

Write-Host "🚀 Déploiement de l'application..." -ForegroundColor Green

# Vérifier que Docker est installé
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Docker n'est pas installé!" -ForegroundColor Red
    exit 1
}

# Arrêter les conteneurs existants
Write-Host "⏹️  Arrêt des conteneurs existants..." -ForegroundColor Yellow
docker-compose down

# Construire l'image
Write-Host "🔨 Construction de l'image Docker..." -ForegroundColor Yellow
docker-compose build

# Démarrer les conteneurs
Write-Host "▶️  Démarrage des conteneurs..." -ForegroundColor Yellow
docker-compose up -d

# Attendre que l'application démarre
Write-Host "⏳ Attente du démarrage..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Vérifier la santé
Write-Host "🏥 Vérification de la santé..." -ForegroundColor Yellow
$response = Invoke-WebRequest -Uri "http://localhost:5000/api/health" -UseBasicParsing
if ($response.StatusCode -eq 200) {
    Write-Host "✅ Application déployée avec succès!" -ForegroundColor Green
    Write-Host "🌐 Application disponible sur: http://localhost:5000" -ForegroundColor Cyan
} else {
    Write-Host "❌ Erreur lors du déploiement" -ForegroundColor Red
    docker-compose logs
}
```

**Utilisation** :
```powershell
.\deploy.ps1
```

---

### Script Bash : `deploy.sh` (Pour Linux/Mac)

```bash
#!/bin/bash
# deploy.sh
# Script de déploiement pour Linux/Mac

echo "🚀 Déploiement de l'application..."

# Vérifier Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker n'est pas installé!"
    exit 1
fi

# Arrêter les conteneurs
echo "⏹️  Arrêt des conteneurs..."
docker-compose down

# Construire l'image
echo "🔨 Construction de l'image..."
docker-compose build

# Démarrer
echo "▶️  Démarrage..."
docker-compose up -d

# Attendre
echo "⏳ Attente du démarrage..."
sleep 10

# Vérifier
echo "🏥 Vérification..."
if curl -f http://localhost:5000/api/health > /dev/null 2>&1; then
    echo "✅ Application déployée avec succès!"
    echo "🌐 Disponible sur: http://localhost:5000"
else
    echo "❌ Erreur lors du déploiement"
    docker-compose logs
fi
```

**Utilisation** :
```bash
chmod +x deploy.sh
./deploy.sh
```

---

## 🔧 Configuration des Variables d'Environnement

### Fichier `.env` (Optionnel)

Créez un fichier `.env` à la racine :

```env
SECRET_KEY=votre-cle-secrete-tres-longue-et-aleatoire
FLASK_ENV=production
PORT=5000
```

**Note** : Le fichier `.env` est dans `.gitignore` pour ne pas être commité.

---

## 📊 Résumé des Fichiers de Déploiement

| Fichier | Rôle | Utilisé par |
|---------|------|-------------|
| `Dockerfile` | Image Docker | Docker, Railway, Render |
| `docker-compose.yml` | Orchestration | Docker Compose (local) |
| `Procfile` | Commande démarrage | Railway, Heroku |
| `wsgi.py` | Point d'entrée WSGI | Gunicorn |
| `requirements.txt` | Dépendances | pip, Docker |
| `runtime.txt` | Version Python | Heroku |

---

## 🎯 Workflow de Déploiement Recommandé

### 1. Développement Local
```powershell
# Tester localement
docker-compose up -d
```

### 2. Préparation
```powershell
# Vérifier que tout fonctionne
docker-compose logs
curl http://localhost:5000/api/health
```

### 3. Commit et Push
```powershell
git add .
git commit -m "Prêt pour déploiement"
git push origin main
```

### 4. Déploiement Cloud
- Railway : Déploiement automatique après push
- Render : Déploiement automatique après push

---

## 🐛 Dépannage

### L'application ne démarre pas
```powershell
# Vérifier les logs
docker-compose logs

# Vérifier les conteneurs
docker ps -a

# Redémarrer
docker-compose restart
```

### Erreur de build
```powershell
# Reconstruire sans cache
docker-compose build --no-cache
```

### Port déjà utilisé
```powershell
# Modifier le port dans docker-compose.yml
ports:
  - "5001:5000"  # Au lieu de 5000:5000
```

---

## ✅ Checklist de Déploiement

- [ ] `Dockerfile` présent et valide
- [ ] `docker-compose.yml` configuré
- [ ] `requirements.txt` à jour
- [ ] Variables d'environnement configurées
- [ ] Base de données initialisée
- [ ] Tests locaux réussis
- [ ] Code pushé sur GitHub
- [ ] Déploiement cloud configuré
- [ ] Health check fonctionne
- [ ] Documentation Swagger accessible

---

## 📚 Ressources

- **Docker** : https://docs.docker.com/
- **Railway** : https://docs.railway.app/
- **Render** : https://render.com/docs
- **Gunicorn** : https://gunicorn.org/

