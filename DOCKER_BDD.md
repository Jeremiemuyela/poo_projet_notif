# 🐳 Docker avec Base de Données SQLite

## ✅ Configuration Actuelle

Votre application utilise maintenant **SQLite** au lieu des fichiers JSON. La configuration Docker a été adaptée pour :

1. ✅ Persister la base de données `notifications.db`
2. ✅ Initialiser automatiquement la base au démarrage
3. ✅ Sauvegarder les données même si le conteneur est supprimé

---

## 📁 Structure des Volumes Docker

```yaml
volumes:
  - ./notifications.db:/app/notifications.db:rw  # Base de données principale
  - ./data:/app/data                              # Données supplémentaires
```

### Fichiers SQLite créés automatiquement

SQLite en mode WAL crée automatiquement :
- `notifications.db` - Base de données principale
- `notifications.db-wal` - Write-Ahead Log (temporaire)
- `notifications.db-shm` - Shared Memory (temporaire)

Ces fichiers sont automatiquement gérés par SQLite.

---

## 🚀 Démarrage avec Docker

### 1. Construire l'image

```powershell
docker build -t notification-system .
```

### 2. Lancer avec docker-compose

```powershell
docker-compose up -d
```

### 3. Vérifier les logs

```powershell
docker-compose logs -f
```

Vous devriez voir :
```
[DB] Initialisation de la base de données...
[DB] Base de donnees initialisee: notifications.db
[AUTH] Utilisateur admin cree (mot de passe: admin123)
```

---

## 🔍 Vérification de la Base de Données

### Vérifier que la base existe

```powershell
# Dans le conteneur
docker exec -it notification-system ls -la /app/notifications.db

# Sur votre machine
ls -la notifications.db
```

### Accéder à la base de données

```powershell
# Entrer dans le conteneur
docker exec -it notification-system /bin/bash

# Utiliser sqlite3
sqlite3 notifications.db
.tables
.quit
```

---

## 📊 Migration des Données

Si vous avez des données dans les anciens fichiers JSON, votre collègue a probablement déjà créé un script de migration. Vérifiez dans `migrations/001_initial_schema.sql`.

---

## ⚠️ Points Importants

### 1. Persistance des Données

La base de données `notifications.db` est montée comme volume, donc :
- ✅ Les données sont sauvegardées sur votre machine hôte
- ✅ Si vous supprimez le conteneur, les données restent
- ✅ Si vous recréez le conteneur, les données sont toujours là

### 2. Sauvegarde

Pour sauvegarder la base de données :

```powershell
# Copier la base de données
cp notifications.db notifications.db.backup

# Ou depuis le conteneur
docker cp notification-system:/app/notifications.db ./notifications.db.backup
```

### 3. Initialisation Automatique

L'application initialise automatiquement la base de données au démarrage si elle n'existe pas :
- Vérifie si `notifications.db` existe
- Si non, exécute `migrations/001_initial_schema.sql`
- Crée les tables nécessaires
- Initialise les utilisateurs par défaut

---

## 🔧 Dépannage

### La base de données n'est pas créée

Vérifiez les logs :
```powershell
docker-compose logs web
```

### Erreur de permissions

Si vous avez des erreurs de permissions sur `notifications.db` :

```powershell
# Donner les permissions
chmod 666 notifications.db
```

### Réinitialiser la base de données

```powershell
# Supprimer la base de données
rm notifications.db

# Redémarrer le conteneur (il recréera la base)
docker-compose restart
```

---

## 📝 Comparaison : Avant vs Après

### Avant (Fichiers JSON)
- `users.json` - Utilisateurs
- `students.json` - Étudiants  
- `notifications_log.json` - Logs

### Après (SQLite)
- `notifications.db` - Tout dans une seule base de données
- Tables : `users`, `students`, `notifications_log`, `translations`, etc.

---

## ✅ Votre Configuration est Prête !

Votre `docker-compose.yml` est maintenant configuré pour :
- ✅ Persister la base de données SQLite
- ✅ Initialiser automatiquement la base au démarrage
- ✅ Fonctionner avec la nouvelle architecture de base de données

Vous pouvez maintenant déployer avec Docker ! 🎉

