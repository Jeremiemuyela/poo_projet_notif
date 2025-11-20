# 🚀 Guide Complet de Déploiement Docker

## ✅ État Actuel

Votre application Docker fonctionne déjà localement ! 🎉

---

## 📋 Étape par Étape

### Étape 1 : Vérifier que tout fonctionne localement ✅

Votre conteneur est déjà en cours d'exécution. Vérifions :

```powershell
# Voir les logs
docker-compose logs -f

# Tester l'API
# Ouvrez http://localhost:5000/api/health dans votre navigateur
```

---

### Étape 2 : Préparer le Code pour GitHub

#### 2.1 Ajouter tous vos fichiers Docker

```powershell
# Ajouter les fichiers Docker
git add Dockerfile docker-compose.yml .dockerignore
git add Procfile runtime.txt wsgi.py

# Ajouter la documentation
git add DOCKER.md README_DOCKER.md TROUBLESHOOTING_DOCKER.md
git add COMMANDES_POWERSHELL.md DEPLOIEMENT.md DOCKER_BDD.md
git add DEPLOIEMENT_DOCKER.md GIT_SYNC.md MIGRATION_DATABASE.md

# Ajouter les modifications de code
git add app.py requirements.txt .gitignore
```

#### 2.2 Commit

```powershell
git commit -m "Configuration Docker complète avec support base de données SQLite"
```

#### 2.3 Push sur GitHub

```powershell
git push new-origin main
```

---

### Étape 3 : Déployer sur Railway (Recommandé) ⭐

#### 3.1 Créer un compte Railway

1. Allez sur **https://railway.app**
2. Cliquez sur **"Start a New Project"**
3. Connectez-vous avec **GitHub**

#### 3.2 Créer un nouveau projet

1. Cliquez sur **"New Project"**
2. Choisissez **"Deploy from GitHub repo"**
3. Sélectionnez votre repository : **`poo_projet_notif`**

Railway va automatiquement :
- ✅ Détecter le Dockerfile
- ✅ Construire l'image
- ✅ Déployer l'application

#### 3.3 Configurer les variables d'environnement

Dans Railway, allez dans votre projet → **Variables** :

**Ajoutez ces variables** :

1. **SECRET_KEY**
   - Pour générer une clé sécurisée :
   ```powershell
   python -c "import secrets; print(secrets.token_hex(32))"
   ```
   - Copiez le résultat et collez-le dans Railway

2. **FLASK_ENV**
   - Valeur : `production`

#### 3.4 Attendre le déploiement

Railway va :
1. Cloner votre repository
2. Construire l'image Docker
3. Démarrer le conteneur
4. Vous donner une URL publique

**Temps estimé** : 2-5 minutes

#### 3.5 Obtenir votre URL

1. Cliquez sur votre service
2. Allez dans **Settings** → **Networking**
3. Cliquez sur **"Generate Domain"**
4. Vous obtiendrez une URL comme :
   ```
   https://votre-app-production.up.railway.app
   ```

#### 3.6 Tester votre application déployée

Ouvrez l'URL dans votre navigateur :
```
https://votre-url/api/health
```

Vous devriez voir :
```json
{
  "status": "ok",
  "message": "API opérationnelle"
}
```

---

### Étape 4 : Déploiement sur Render (Alternative)

Si Railway ne fonctionne pas, utilisez Render :

#### 4.1 Créer un compte Render

1. Allez sur **https://render.com**
2. Créez un compte gratuit

#### 4.2 Créer un Web Service

1. Cliquez sur **"New +"** → **"Web Service"**
2. Connectez votre repository GitHub
3. Sélectionnez **`poo_projet_notif`**

#### 4.3 Configuration

- **Name** : `notification-system`
- **Environment** : `Docker`
- **Region** : Choisissez le plus proche
- **Branch** : `main`
- **Root Directory** : (laissez vide)

#### 4.4 Variables d'environnement

Dans **Environment Variables** :
```
SECRET_KEY=votre-cle-secrete-tres-longue-et-aleatoire
FLASK_ENV=production
```

#### 4.5 Déployer

1. Cliquez sur **"Create Web Service"**
2. Render va construire et déployer automatiquement
3. Attendez 5-10 minutes

#### 4.6 Obtenir votre URL

Render vous donnera automatiquement une URL :
```
https://notification-system.onrender.com
```

---

## 🔍 Vérifications Post-Déploiement

### 1. Test de l'API

```bash
curl https://votre-url/api/health
```

### 2. Test de l'interface admin

Ouvrez : `https://votre-url/admin/`

### 3. Test de l'interface étudiant

Ouvrez : `https://votre-url/student/`

### 4. Vérifier les logs

**Railway** :
- Projet → Deployments → Cliquez sur le déploiement → Logs

**Render** :
- Service → Logs

---

## 🐛 Dépannage

### L'application ne démarre pas

1. **Vérifiez les logs** de déploiement
2. **Vérifiez SECRET_KEY** est bien configuré
3. **Vérifiez** que le Dockerfile est correct

### Erreur 502 Bad Gateway

1. Attendez quelques minutes (démarrage)
2. Vérifiez les logs pour les erreurs
3. Vérifiez que gunicorn démarre

### Base de données non initialisée

1. Vérifiez que `migrations/001_initial_schema.sql` est présent
2. Vérifiez les logs pour voir l'initialisation

---

## 📊 Monitoring

### Railway

- **Logs en temps réel** : Projet → Deployments → Logs
- **Métriques** : Projet → Metrics
- **Variables** : Projet → Variables

### Render

- **Logs** : Service → Logs
- **Métriques** : Service → Metrics
- **Variables** : Service → Environment

---

## ✅ Checklist Finale

- [ ] Application testée localement
- [ ] Code pushé sur GitHub
- [ ] Déployé sur Railway/Render
- [ ] Variables d'environnement configurées
- [ ] URL publique obtenue
- [ ] API testée et fonctionnelle
- [ ] Interfaces admin/étudiant accessibles
- [ ] Logs vérifiés (pas d'erreurs)

---

## 🎉 Félicitations !

Votre application est maintenant déployée et accessible sur Internet ! 🚀

---

## 📞 Support

- Guide Docker : `DOCKER.md`
- Dépannage : `TROUBLESHOOTING_DOCKER.md`
- Commandes PowerShell : `COMMANDES_POWERSHELL.md`

