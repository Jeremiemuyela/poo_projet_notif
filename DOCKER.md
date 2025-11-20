# Guide de Déploiement avec Docker 🐳

## 📚 Qu'est-ce que Docker ?

**Docker** est un système de conteneurisation qui permet d'empaqueter votre application avec toutes ses dépendances dans un "conteneur". C'est comme une boîte qui contient tout ce dont votre application a besoin pour fonctionner, peu importe où elle est déployée.

### Avantages de Docker :
- ✅ **Portabilité** : Fonctionne de la même manière sur Windows, Mac, Linux
- ✅ **Isolation** : Votre application ne perturbe pas le système hôte
- ✅ **Reproductibilité** : Même environnement partout
- ✅ **Facilité de déploiement** : Un seul fichier (`Dockerfile`) décrit tout

---

## 🚀 Déploiement Local avec Docker

### Prérequis
- Docker Desktop installé (https://www.docker.com/products/docker-desktop)
- Ou Docker Engine sur Linux

### Étape 1 : Construire l'image Docker

```bash
docker build -t notification-system .
```

Cette commande :
- Lit le `Dockerfile`
- Télécharge Python 3.11
- Installe toutes les dépendances
- Copie votre code
- Crée une image Docker nommée `notification-system`

### Étape 2 : Lancer le conteneur

**Pour PowerShell (Windows)** - Utilisez docker-compose (recommandé) :
```powershell
docker-compose up -d
```

**Pour PowerShell (Windows)** - Si vous voulez utiliser docker run directement :
```powershell
docker run -d -p 5000:5000 -e SECRET_KEY="votre-cle-secrete-tres-longue" -e FLASK_ENV=production --name notification-app notification-system
```

**Pour Linux/Mac/Bash** - Avec retours à la ligne :
```bash
docker run -d \
  -p 5000:5000 \
  -e SECRET_KEY="votre-cle-secrete-tres-longue" \
  -e FLASK_ENV=production \
  --name notification-app \
  notification-system
```

> **Note** : PowerShell utilise le backtick `` ` `` pour les lignes de continuation, pas le backslash `\`. Mais docker-compose est plus simple !

### Étape 3 : Vérifier que ça fonctionne

Ouvrez votre navigateur : http://localhost:5000/api/health

### Commandes utiles

```bash
# Voir les logs
docker logs notification-app

# Arrêter le conteneur
docker stop notification-app

# Redémarrer
docker start notification-app

# Supprimer le conteneur
docker rm notification-app

# Voir les conteneurs en cours d'exécution
docker ps
```

---

## 🌐 Déploiement sur un Serveur avec Docker

### Option 1 : Déployer sur un VPS (DigitalOcean, AWS EC2, etc.)

#### Sur votre serveur Linux :

1. **Installer Docker** :
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
```

2. **Cloner votre projet** :
```bash
git clone https://github.com/votre-username/votre-repo.git
cd votre-repo
```

3. **Créer un fichier `.env`** :
```bash
nano .env
```
Contenu :
```
SECRET_KEY=votre-cle-secrete-tres-longue-et-aleatoire
FLASK_ENV=production
PORT=5000
```

4. **Construire et lancer** :
```bash
docker-compose up -d --build
```

5. **Configurer un reverse proxy (Nginx)** pour avoir un nom de domaine :
```nginx
server {
    listen 80;
    server_name votre-domaine.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## ☁️ Déploiement sur Plateformes Cloud avec Docker

### Option 1 : Railway (Recommandé) ⭐

1. Allez sur https://railway.app
2. Créez un nouveau projet
3. Choisissez "Deploy from GitHub"
4. Railway détectera automatiquement le Dockerfile
5. Ajoutez les variables d'environnement dans l'interface
6. Déployez !

### Option 2 : Render

1. Allez sur https://render.com
2. Créez un nouveau "Web Service"
3. Connectez votre repository GitHub
4. Render détectera le Dockerfile automatiquement
5. Configurez les variables d'environnement
6. Déployez !

### Option 3 : AWS ECS / Google Cloud Run / Azure Container Instances

Ces plateformes supportent Docker nativement. Consultez leur documentation pour les détails spécifiques.

---

## 🔧 Configuration Avancée

### Variables d'environnement

Créez un fichier `.env` :
```env
SECRET_KEY=votre-cle-secrete-tres-longue-et-aleatoire
FLASK_ENV=production
PORT=5000
```

Puis utilisez :
```bash
docker-compose --env-file .env up -d
```

### Persistance des données

Les fichiers JSON sont montés dans `./data` via docker-compose.yml pour persister les données même si le conteneur est supprimé.

### Logs

```bash
# Voir les logs en temps réel
docker-compose logs -f

# Voir les logs d'un service spécifique
docker-compose logs web
```

### Redémarrer après modification du code

```bash
# Reconstruire et redémarrer
docker-compose up -d --build
```

---

## 🐛 Dépannage

### Le conteneur ne démarre pas

```bash
# Voir les logs d'erreur
docker logs notification-app

# Vérifier que le port n'est pas déjà utilisé
netstat -an | grep 5000
```

### Modifier le Dockerfile

Après modification, reconstruisez :
```bash
docker build -t notification-system .
```

### Accéder au shell du conteneur

```bash
docker exec -it notification-app /bin/bash
```

---

## 📝 Checklist avant déploiement

- [ ] Dockerfile créé ✅
- [ ] .dockerignore configuré ✅
- [ ] docker-compose.yml créé ✅
- [ ] SECRET_KEY changé dans les variables d'environnement
- [ ] Testé localement avec `docker-compose up`
- [ ] Vérifié que l'application fonctionne sur http://localhost:5000

---

## 🎉 C'est prêt !

Votre application est maintenant prête à être déployée avec Docker. Choisissez votre plateforme et suivez les instructions ci-dessus !


