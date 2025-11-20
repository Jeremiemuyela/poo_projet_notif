# 🐳 Déploiement Rapide avec Docker

## Démarrage Rapide (3 étapes)

### 1. Construire l'image Docker

**Si vous avez des problèmes de connexion réseau**, consultez `TROUBLESHOOTING_DOCKER.md`

**Pour PowerShell (Windows)** :
```powershell
docker build -t notification-system .
```

**Alternative** (si problème de connexion) :
```powershell
docker build -f Dockerfile.alternative -t notification-system .
```

### 2. Lancer avec docker-compose
```powershell
docker-compose up -d
```

### 3. Accéder à l'application
Ouvrez votre navigateur : http://localhost:5000

---

## Configuration

### Variables d'environnement

Créez un fichier `.env` à la racine du projet :
```env
SECRET_KEY=votre-cle-secrete-tres-longue-et-aleatoire
FLASK_ENV=production
PORT=5000
```

Ou modifiez directement `docker-compose.yml`.

---

## Commandes Utiles

```bash
# Voir les logs
docker-compose logs -f

# Arrêter
docker-compose down

# Redémarrer
docker-compose restart

# Reconstruire après modification du code
docker-compose up -d --build
```

---

## Déploiement sur Cloud

### Railway
1. Poussez votre code sur GitHub
2. Allez sur https://railway.app
3. Créez un nouveau projet depuis GitHub
4. Railway détectera automatiquement le Dockerfile
5. Ajoutez les variables d'environnement
6. Déployez !

### Render
1. Poussez votre code sur GitHub
2. Allez sur https://render.com
3. Créez un nouveau "Web Service"
4. Connectez votre repository
5. Render détectera le Dockerfile automatiquement
6. Configurez les variables d'environnement
7. Déployez !

---

Pour plus de détails, consultez `DOCKER.md`


