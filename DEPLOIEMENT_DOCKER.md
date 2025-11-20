# 🚀 Guide de Déploiement Docker - Étape par Étape

## 📋 Checklist Avant Déploiement

- [x] Dockerfile créé ✅
- [x] docker-compose.yml configuré ✅
- [x] Base de données SQLite intégrée ✅
- [x] Variables d'environnement configurées ✅
- [ ] Test local réussi
- [ ] Code pushé sur GitHub
- [ ] Déployé sur plateforme cloud

---

## 🧪 Étape 1 : Test Local

### 1.1 Vérifier que Docker fonctionne

```powershell
docker --version
docker-compose --version
```

### 1.2 Construire l'image Docker

```powershell
docker build -t notification-system .
```

**Si vous avez des problèmes de connexion**, utilisez :
```powershell
docker build -f Dockerfile.alternative -t notification-system .
```

### 1.3 Lancer l'application

```powershell
docker-compose up -d
```

### 1.4 Vérifier les logs

```powershell
docker-compose logs -f
```

Vous devriez voir :
- `[DB] Initialisation de la base de données...`
- `[APP] Application démarrée`
- `Running on http://0.0.0.0:5000`

### 1.5 Tester l'application

Ouvrez votre navigateur : http://localhost:5000/api/health

Vous devriez voir :
```json
{
  "status": "ok",
  "message": "API opérationnelle"
}
```

### 1.6 Arrêter l'application (après test)

```powershell
docker-compose down
```

---

## 📤 Étape 2 : Préparer le Code pour GitHub

### 2.1 Vérifier les fichiers à commiter

```powershell
git status
```

### 2.2 Ajouter vos fichiers Docker

```powershell
git add Dockerfile docker-compose.yml .dockerignore
git add Procfile runtime.txt wsgi.py
git add DOCKER.md README_DOCKER.md TROUBLESHOOTING_DOCKER.md
git add COMMANDES_POWERSHELL.md DEPLOIEMENT.md DOCKER_BDD.md
git add GIT_SYNC.md MIGRATION_DATABASE.md
```

### 2.3 Commit vos modifications

```powershell
git commit -m "Ajout configuration Docker et documentation déploiement"
```

### 2.4 Push sur GitHub

```powershell
git push new-origin main
```

---

## ☁️ Étape 3 : Déploiement sur Railway (Recommandé)

### 3.1 Créer un compte Railway

1. Allez sur https://railway.app
2. Cliquez sur "Start a New Project"
3. Connectez-vous avec GitHub

### 3.2 Créer un nouveau projet

1. Cliquez sur "New Project"
2. Choisissez "Deploy from GitHub repo"
3. Sélectionnez votre repository : `poo_projet_notif`

### 3.3 Railway détecte automatiquement Docker

Railway va :
- ✅ Détecter le Dockerfile
- ✅ Construire l'image automatiquement
- ✅ Déployer l'application

### 3.4 Configurer les variables d'environnement

Dans Railway, allez dans votre projet → **Variables** :

1. Cliquez sur "New Variable"
2. Ajoutez :
   - **Name** : `SECRET_KEY`
   - **Value** : `votre-cle-secrete-tres-longue-et-aleatoire`

Pour générer une SECRET_KEY sécurisée :
```python
import secrets
print(secrets.token_hex(32))
```

3. Ajoutez aussi :
   - **Name** : `FLASK_ENV`
   - **Value** : `production`

### 3.5 Déployer

Railway déploie automatiquement ! Attendez quelques minutes.

### 3.6 Obtenir votre URL

Une fois déployé :
1. Cliquez sur votre service
2. Allez dans **Settings** → **Networking**
3. Cliquez sur **Generate Domain**
4. Vous obtiendrez une URL comme : `https://votre-app-production.up.railway.app`

### 3.7 Tester votre application déployée

Ouvrez l'URL dans votre navigateur :
```
https://votre-app-production.up.railway.app/api/health
```

---

## 🌐 Étape 4 : Déploiement sur Render (Alternative)

### 4.1 Créer un compte Render

1. Allez sur https://render.com
2. Créez un compte (gratuit)

### 4.2 Créer un nouveau Web Service

1. Cliquez sur "New +" → "Web Service"
2. Connectez votre repository GitHub
3. Sélectionnez `poo_projet_notif`

### 4.3 Configuration

- **Name** : `notification-system`
- **Environment** : `Docker`
- **Region** : Choisissez le plus proche
- **Branch** : `main`

### 4.4 Variables d'environnement

Dans **Environment Variables** :
```
SECRET_KEY=votre-cle-secrete-tres-longue-et-aleatoire
FLASK_ENV=production
```

### 4.5 Déployer

1. Cliquez sur "Create Web Service"
2. Render va construire et déployer automatiquement
3. Attendez la fin du déploiement

### 4.6 Obtenir votre URL

Render vous donnera une URL automatiquement :
```
https://notification-system.onrender.com
```

---

## 🔧 Étape 5 : Configuration Post-Déploiement

### 5.1 Persistance de la Base de Données

**Important** : Sur Railway/Render, la base de données SQLite sera dans le système de fichiers éphémère du conteneur.

**Pour la production**, vous devriez :
- Utiliser un volume persistant (Railway/Render le gèrent automatiquement)
- Ou migrer vers PostgreSQL (voir `MIGRATION_DATABASE.md`)

### 5.2 Vérifier que tout fonctionne

1. Testez l'API : `https://votre-url/api/health`
2. Testez l'interface admin : `https://votre-url/admin/`
3. Testez l'interface étudiant : `https://votre-url/student/`

### 5.3 Surveiller les logs

**Railway** :
- Allez dans votre projet → **Deployments** → Cliquez sur le déploiement → **Logs**

**Render** :
- Allez dans votre service → **Logs**

---

## 🐛 Dépannage Post-Déploiement

### L'application ne démarre pas

1. Vérifiez les logs de déploiement
2. Vérifiez que `SECRET_KEY` est bien configuré
3. Vérifiez que le port est correct (Railway/Render le gèrent automatiquement)

### Erreur de base de données

1. Vérifiez que le fichier `migrations/001_initial_schema.sql` est présent
2. Vérifiez les logs pour voir si l'initialisation a réussi

### Erreur 502 Bad Gateway

1. Attendez quelques minutes (l'application démarre)
2. Vérifiez les logs pour voir les erreurs
3. Vérifiez que gunicorn démarre correctement

---

## ✅ Checklist Post-Déploiement

- [ ] Application accessible via l'URL publique
- [ ] API `/api/health` répond correctement
- [ ] Interface admin accessible
- [ ] Interface étudiant accessible
- [ ] Base de données initialisée
- [ ] Variables d'environnement configurées
- [ ] Logs sans erreurs critiques

---

## 🎉 Félicitations !

Votre application est maintenant déployée et accessible sur Internet ! 🚀

---

## 📞 Support

Si vous rencontrez des problèmes :
1. Consultez `TROUBLESHOOTING_DOCKER.md`
2. Vérifiez les logs de déploiement
3. Consultez la documentation de Railway/Render

