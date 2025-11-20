# 🔧 Résolution des Problèmes Docker

## Erreur de Connexion lors du Build

### Erreur rencontrée :
```
ERROR: failed to build: failed to solve: failed to compute cache key: 
failed to copy: httpReadSeeker: failed open: failed to do request: 
Get "https://docker-images-prod...": dial tcp 172.64.66.1:443: 
connectex: A connection attempt failed because the connected party 
did not properly respond after a period of time
```

### Cause
Problème de connexion réseau pour télécharger l'image Python depuis Docker Hub.

---

## ✅ Solutions

### Solution 1 : Vérifier la connexion Internet

```powershell
# Tester la connexion
ping google.com

# Tester l'accès à Docker Hub
ping registry-1.docker.io
```

### Solution 2 : Configurer Docker Desktop pour utiliser un proxy (si nécessaire)

Si vous êtes derrière un proxy d'entreprise :

1. Ouvrez Docker Desktop
2. Allez dans **Settings** → **Resources** → **Proxies**
3. Configurez votre proxy HTTP/HTTPS
4. Redémarrez Docker Desktop

### Solution 3 : Utiliser un mirror Docker (Chine/Mirror)

Si vous êtes dans une région avec accès limité à Docker Hub, utilisez un mirror :

1. Créez/modifiez le fichier `C:\Users\VotreNom\.docker\daemon.json` :
```json
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com"
  ]
}
```

2. Redémarrez Docker Desktop

### Solution 4 : Utiliser une image alternative

Modifiez le Dockerfile pour utiliser une image plus petite ou un registry alternatif :

```dockerfile
# Au lieu de python:3.11-slim
FROM python:3.11-alpine

# Ou utilisez une image locale si disponible
# FROM python:3.11
```

### Solution 5 : Télécharger l'image manuellement

```powershell
# Télécharger l'image Python d'abord
docker pull python:3.11-slim

# Puis construire votre image
docker build -t notification-system .
```

### Solution 6 : Vérifier le firewall/antivirus

- Vérifiez que votre firewall/autoroute ne bloque pas Docker
- Ajoutez Docker Desktop aux exceptions de votre antivirus
- Désactivez temporairement le VPN si vous en utilisez un

### Solution 7 : Réinitialiser Docker Desktop

Si rien ne fonctionne :

1. Ouvrez Docker Desktop
2. Allez dans **Troubleshoot** → **Reset to factory defaults**
3. Redémarrez Docker Desktop
4. Réessayez le build

---

## 🧪 Test de Connexion Docker

```powershell
# Tester si Docker fonctionne
docker --version

# Tester le téléchargement d'une petite image
docker pull hello-world

# Si ça fonctionne, essayez Python
docker pull python:3.11-slim
```

---

## 🔄 Alternative : Build sans cache

Si le problème persiste, essayez de construire sans cache :

```powershell
docker build --no-cache -t notification-system .
```

---

## 📞 Si le problème persiste

1. Vérifiez les logs Docker Desktop
2. Redémarrez votre ordinateur
3. Vérifiez que Docker Desktop est à jour
4. Consultez la documentation Docker pour votre région

