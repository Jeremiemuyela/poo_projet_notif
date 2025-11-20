# 💻 Commandes Docker pour PowerShell (Windows)

## ⚠️ Important : Différences PowerShell vs Bash

PowerShell utilise le **backtick** `` ` `` pour les lignes de continuation, **PAS** le backslash `\`.

**❌ Ne fonctionne PAS dans PowerShell** :
```powershell
docker run -d \
  -p 5000:5000 \
  notification-system
```

**✅ Fonctionne dans PowerShell** (une seule ligne) :
```powershell
docker run -d -p 5000:5000 notification-system
```

**✅ Ou avec docker-compose** (recommandé) :
```powershell
docker-compose up -d
```

---

## 🚀 Commandes Essentielles

### Construire l'image
```powershell
docker build -t notification-system .
```

### Lancer avec docker-compose (RECOMMANDÉ)
```powershell
docker-compose up -d
```

### Voir les logs
```powershell
docker-compose logs -f
```

### Arrêter
```powershell
docker-compose down
```

### Redémarrer
```powershell
docker-compose restart
```

### Reconstruire après modification
```powershell
docker-compose up -d --build
```

---

## 🔧 Commandes Docker Directes (si nécessaire)

### Lancer un conteneur (une seule ligne)
```powershell
docker run -d -p 5000:5000 -e SECRET_KEY="votre-cle" -e FLASK_ENV=production --name notification-app notification-system
```

### Voir les conteneurs
```powershell
docker ps
```

### Voir tous les conteneurs (y compris arrêtés)
```powershell
docker ps -a
```

### Arrêter un conteneur
```powershell
docker stop notification-app
```

### Démarrer un conteneur
```powershell
docker start notification-app
```

### Supprimer un conteneur
```powershell
docker rm notification-app
```

### Voir les logs d'un conteneur
```powershell
docker logs notification-app
```

### Suivre les logs en temps réel
```powershell
docker logs -f notification-app
```

### Entrer dans le conteneur (shell)
```powershell
docker exec -it notification-app /bin/bash
```

---

## 📝 Astuces PowerShell

### Multi-lignes avec backtick (si vraiment nécessaire)
```powershell
docker run -d `
  -p 5000:5000 `
  -e SECRET_KEY="votre-cle" `
  notification-system
```

**Mais docker-compose est beaucoup plus simple !**

### Variables d'environnement PowerShell
```powershell
$env:SECRET_KEY = "votre-cle-secrete"
docker-compose up -d
```

---

## ✅ Recommandation

**Utilisez toujours `docker-compose`** - C'est plus simple et fonctionne de la même manière sur Windows, Mac et Linux !

```powershell
# C'est tout ce dont vous avez besoin !
docker-compose up -d
```

