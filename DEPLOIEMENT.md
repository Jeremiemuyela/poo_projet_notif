# Guide de Déploiement - Système de Notification d'Urgence

> **Note** : Ce projet utilise Docker pour le déploiement. Consultez `DOCKER.md` pour les instructions détaillées sur Docker.

## 📚 Qu'est-ce que le déploiement ?

Le **déploiement** consiste à rendre votre application accessible sur Internet, au lieu de la faire tourner uniquement sur votre ordinateur local. C'est comme publier votre site web pour que d'autres personnes puissent y accéder.

### Différences entre développement local et production

- **Développement local** : Votre application tourne sur `localhost:5000` (accessible uniquement sur votre PC)
- **Production (déploiement)** : Votre application a une URL publique comme `https://votre-app.herokuapp.com` (accessible partout)

---

## 🎯 Options de Déploiement

### 1. **Railway** (Recommandé pour débutants) ⭐
- ✅ Gratuit pour commencer
- ✅ Très simple à utiliser
- ✅ Déploiement en quelques clics
- ✅ Supporte Python/Flask nativement
- 🔗 https://railway.app

### 2. **Render**
- ✅ Gratuit avec limitations
- ✅ Facile à configurer
- ✅ Bon pour les projets Flask
- 🔗 https://render.com

### 3. **Heroku**
- ⚠️ Plus complexe
- ⚠️ Nécessite une carte bancaire (même pour le gratuit)
- ✅ Très populaire et bien documenté
- 🔗 https://heroku.com

### 4. **PythonAnywhere**
- ✅ Gratuit pour débuter
- ✅ Spécialisé Python
- ✅ Interface simple
- 🔗 https://www.pythonanywhere.com

---

## 🚀 Déploiement sur Railway (Recommandé)

### Étape 1 : Préparer votre projet

Assurez-vous d'avoir tous les fichiers nécessaires (déjà fait ✅)

### Étape 2 : Créer un compte Railway

1. Allez sur https://railway.app
2. Cliquez sur "Start a New Project"
3. Connectez-vous avec GitHub (recommandé) ou email

### Étape 3 : Connecter votre projet

1. Dans Railway, cliquez sur "New Project"
2. Choisissez "Deploy from GitHub repo"
3. Sélectionnez votre repository (ou créez-en un sur GitHub d'abord)
4. Railway détectera automatiquement que c'est une app Python/Flask

### Étape 4 : Configurer les variables d'environnement

Dans Railway, allez dans "Variables" et ajoutez :
```
SECRET_KEY=votre-cle-secrete-tres-longue-et-aleatoire
FLASK_ENV=production
```

### Étape 5 : Déployer

Railway déploiera automatiquement votre application ! 🎉

### Étape 6 : Obtenir votre URL

Une fois déployé, Railway vous donnera une URL comme :
`https://votre-app-production.up.railway.app`

---

## 🔧 Déploiement sur Render

### Étape 1 : Créer un compte
Allez sur https://render.com et créez un compte

### Étape 2 : Créer un nouveau Web Service
1. Cliquez sur "New +" → "Web Service"
2. Connectez votre repository GitHub
3. Configurez :
   - **Name** : notification-system
   - **Environment** : Python 3
   - **Build Command** : `pip install -r requirements.txt`
   - **Start Command** : `gunicorn app:app`

### Étape 3 : Variables d'environnement
Ajoutez dans "Environment Variables" :
```
SECRET_KEY=votre-cle-secrete
FLASK_ENV=production
```

### Étape 4 : Déployer
Cliquez sur "Create Web Service" et attendez le déploiement

---

## 📝 Fichiers nécessaires pour le déploiement

### 1. `Procfile` (pour Heroku/Railway)
```
web: gunicorn app:app
```

### 2. `runtime.txt` (optionnel, pour spécifier Python)
```
python-3.11.0
```

### 3. `.env.example` (template pour les variables)
```
SECRET_KEY=changez-moi-en-production
FLASK_ENV=production
```

---

## ⚠️ Points importants avant le déploiement

### 1. Sécurité
- ✅ Changez `SECRET_KEY` dans `app.py` (ligne 16)
- ✅ Utilisez des variables d'environnement pour les secrets
- ✅ Ne commitez JAMAIS les fichiers sensibles (users.json, students.json)

### 2. Fichiers à ne PAS déployer
- `__pycache__/` (déjà dans .gitignore ✅)
- `notif/` (environnement virtuel local)
- Fichiers de données sensibles

### 3. Base de données
Votre application utilise des fichiers JSON locaux. Pour la production, vous devriez :
- Utiliser une vraie base de données (PostgreSQL, MySQL)
- Ou utiliser le stockage persistant de la plateforme

---

## 🔍 Vérifications avant déploiement

- [ ] `requirements.txt` est à jour
- [ ] `SECRET_KEY` est changé
- [ ] `.gitignore` exclut les fichiers sensibles
- [ ] L'application fonctionne en local
- [ ] Tous les tests passent

---

## 📞 Support

Si vous rencontrez des problèmes :
1. Vérifiez les logs de déploiement
2. Consultez la documentation de la plateforme choisie
3. Vérifiez que toutes les dépendances sont dans `requirements.txt`

---

## 🎉 Après le déploiement

Une fois déployé :
1. Testez votre application avec l'URL fournie
2. Vérifiez que les fonctionnalités marchent
3. Partagez l'URL avec vos utilisateurs !

