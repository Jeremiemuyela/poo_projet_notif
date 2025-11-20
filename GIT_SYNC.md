# 🔄 Synchroniser avec GitHub sans perdre vos modifications

## 📋 Situation
Votre collègue a pushé des modifications (notamment la base de données) sur GitHub, et vous avez des modifications locales non pushées que vous voulez garder.

---

## ✅ Solution : Utiliser Git Stash

### Étape 1 : Vérifier vos modifications locales

```powershell
git status
```

Cela vous montre quels fichiers ont été modifiés.

### Étape 2 : Sauvegarder temporairement vos modifications

```powershell
git stash push -m "Mes modifications avant pull"
```

Cela met de côté vos modifications sans les perdre.

### Étape 3 : Récupérer les modifications de GitHub

```powershell
git pull origin main
```

(Remplacez `main` par le nom de votre branche si différent : `master`, `develop`, etc.)

### Étape 4 : Récupérer vos modifications

```powershell
git stash pop
```

Cela réapplique vos modifications par-dessus les nouvelles modifications de GitHub.

### Étape 5 : Résoudre les conflits (si nécessaire)

Si Git vous signale des conflits :
1. Ouvrez les fichiers en conflit
2. Cherchez les marqueurs `<<<<<<<`, `=======`, `>>>>>>>`
3. Gardez les parties que vous voulez
4. Supprimez les marqueurs
5. Sauvegardez les fichiers

Puis :
```powershell
git add .
git commit -m "Résolution des conflits"
```

---

## 🔍 Vérifier vos modifications sauvegardées

Pour voir ce qui est dans le stash :
```powershell
git stash list
```

Pour voir le contenu d'un stash :
```powershell
git stash show -p
```

---

## 📝 Alternative : Commit puis Merge

Si vous préférez commit vos modifications d'abord :

### Étape 1 : Commit vos modifications locales

```powershell
git add .
git commit -m "Mes modifications locales avant pull"
```

### Étape 2 : Pull les modifications de GitHub

```powershell
git pull origin main
```

Git va automatiquement créer un merge commit si nécessaire.

### Étape 3 : Résoudre les conflits si nécessaire

Même processus que ci-dessus.

---

## 🎯 Méthode Recommandée : Stash

**Pourquoi stash est mieux** :
- ✅ Vos modifications ne sont pas commitées (vous pouvez les modifier avant)
- ✅ Plus propre si vous n'êtes pas sûr de vouloir commit
- ✅ Facile à annuler si quelque chose ne va pas

---

## ⚠️ En cas de problème

### Annuler le stash pop
```powershell
git stash
```

### Voir ce qui a changé avant de stash
```powershell
git diff
```

### Voir ce qui va changer après pull
```powershell
git fetch
git diff HEAD origin/main
```

---

## 📦 Après avoir synchronisé

Une fois que tout est synchronisé :

```powershell
# Vérifier que tout est OK
git status

# Tester votre application
docker-compose up -d

# Si tout fonctionne, vous pouvez push vos modifications
git add .
git commit -m "Description de vos modifications"
git push origin main
```

---

## 🔄 Workflow Complet Recommandé

```powershell
# 1. Vérifier l'état
git status

# 2. Sauvegarder vos modifications
git stash push -m "Modifications avant pull"

# 3. Récupérer les modifications de GitHub
git pull origin main

# 4. Récupérer vos modifications
git stash pop

# 5. Résoudre les conflits si nécessaire
# (éditer les fichiers, puis)
git add .
git commit -m "Résolution conflits"

# 6. Tester
docker-compose up -d

# 7. Push si tout fonctionne
git push origin main
```

