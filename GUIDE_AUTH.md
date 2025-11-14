# Guide d'Authentification et d'Autorisation

## 📋 Vue d'ensemble

Le système d'authentification utilise un mécanisme simple avec :
- **Stockage** : Fichier JSON (`users.json`)
- **Authentification web** : Sessions Flask (nom d'utilisateur + mot de passe)
- **Authentification API** : Clés API dans l'en-tête HTTP
- **Rôles** : admin, operator, viewer

---

## 🔐 Rôles et Permissions

### Rôle `admin`
- **Permissions** : Toutes (`*`)
- **Accès** : Interface admin complète, configuration, gestion des utilisateurs

### Rôle `operator`
- **Permissions** : `read`, `send_notifications`
- **Accès** : Lecture des métriques, envoi de notifications, modification des configurations

### Rôle `viewer`
- **Permissions** : `read`
- **Accès** : Lecture seule (métriques, statut, configurations)

---

## 🚀 Utilisation

### 1. Utilisateur par Défaut

Au premier démarrage, un utilisateur admin est créé automatiquement :
- **Nom d'utilisateur** : `admin`
- **Mot de passe** : `admin123`
- **⚠️ IMPORTANT** : Changez ce mot de passe en production !

### 2. Connexion à l'Interface Web

1. Accéder à : `http://localhost:5000/admin/login`
2. Entrer le nom d'utilisateur et le mot de passe
3. Vous serez redirigé vers le tableau de bord

### 3. Utilisation de l'API avec Clé API

Toutes les requêtes API nécessitent une clé API dans l'en-tête :

```bash
# Avec curl
curl -X POST http://localhost:5000/api/notifications/meteo \
  -H "Content-Type: application/json" \
  -H "X-API-Key: VOTRE_CLE_API" \
  -d '{"titre":"alerte_meteo","message":"Test","utilisateurs":[...]}'
```

```python
# Avec Python requests
import requests

headers = {
    "Content-Type": "application/json",
    "X-API-Key": "VOTRE_CLE_API"
}

response = requests.post(
    'http://localhost:5000/api/notifications/meteo',
    headers=headers,
    json={...}
)
```

---

## 👥 Gestion des Utilisateurs

### Créer un Utilisateur (Admin uniquement)

**Via l'API :**
```bash
curl -X POST http://localhost:5000/admin/api/users \
  -H "Content-Type: application/json" \
  -H "X-API-Key: CLE_ADMIN" \
  -d '{
    "username": "operator1",
    "password": "motdepasse123",
    "role": "operator"
  }'
```

**Réponse :**
```json
{
  "success": true,
  "message": "Utilisateur 'operator1' créé avec succès",
  "user": {
    "username": "operator1",
    "role": "operator",
    "api_key": "abc123..."
  }
}
```

### Lister les Utilisateurs (Admin uniquement)

```bash
curl -X GET http://localhost:5000/admin/api/users \
  -H "X-API-Key: CLE_ADMIN"
```

### Modifier un Utilisateur

Éditez directement le fichier `users.json` :
```json
{
  "admin": {
    "username": "admin",
    "password_hash": "...",
    "role": "admin",
    "api_key": "...",
    "active": true
  }
}
```

**⚠️ Attention** : Ne modifiez jamais `password_hash` directement. Utilisez la fonction `create_user()` ou changez le mot de passe via l'interface.

---

## 🔑 Obtenir une Clé API

Chaque utilisateur a une clé API unique générée automatiquement lors de la création.

**Pour récupérer votre clé API :**
1. Consultez le fichier `users.json`
2. Ou utilisez l'endpoint `/admin/api/users` (admin uniquement)

---

## 📁 Structure du Fichier users.json

```json
{
  "admin": {
    "username": "admin",
    "password_hash": "sha256_hash_du_mot_de_passe",
    "role": "admin",
    "api_key": "token_aleatoire_securise",
    "active": true
  },
  "operator1": {
    "username": "operator1",
    "password_hash": "...",
    "role": "operator",
    "api_key": "...",
    "active": true
  }
}
```

---

## 🛡️ Protection des Endpoints

### Endpoints Publics (sans authentification)
- `GET /api/health` - Vérification de santé
- `GET /api/notifications/types` - Liste des types

### Endpoints Protégés (authentification requise)
- `POST /api/notifications/*` - Envoi de notifications
- `GET /admin/*` - Interface d'administration
- `GET /admin/api/*` - API d'administration

### Endpoints Admin Uniquement
- `POST /admin/api/config/*/reset` - Réinitialisation des configurations
- `GET /admin/api/users` - Liste des utilisateurs
- `POST /admin/api/users` - Création d'utilisateurs

---

## 🔒 Sécurité

### Recommandations

1. **Changez le mot de passe par défaut** en production
2. **Changez la SECRET_KEY** dans `app.py` en production
3. **Protégez le fichier `users.json`** (permissions de fichier)
4. **Utilisez HTTPS** en production
5. **Régénérez les clés API** régulièrement si compromises

### Hash des Mots de Passe

Les mots de passe sont hashés avec SHA-256. Pour une sécurité renforcée en production, considérez l'utilisation de `bcrypt` ou `argon2`.

---

## 🐛 Dépannage

### Erreur 401 "Authentification requise"
- Vérifiez que vous avez fourni une clé API valide
- Vérifiez que la session est active (pour l'interface web)
- Vérifiez que l'utilisateur est actif dans `users.json`

### Erreur 403 "Accès refusé"
- Vérifiez que votre rôle a les permissions nécessaires
- Certaines actions nécessitent le rôle `admin`

### Impossible de se connecter
- Vérifiez que le fichier `users.json` existe
- Vérifiez que l'utilisateur existe et est actif
- Vérifiez le mot de passe

---

## 📝 Exemples Complets

### Créer un Opérateur et Envoyer une Notification

```bash
# 1. Créer l'utilisateur (en tant qu'admin)
curl -X POST http://localhost:5000/admin/api/users \
  -H "Content-Type: application/json" \
  -H "X-API-Key: CLE_ADMIN" \
  -d '{
    "username": "operator1",
    "password": "secure123",
    "role": "operator"
  }'

# Réponse contient la clé API
# api_key: "abc123xyz..."

# 2. Utiliser la clé API pour envoyer une notification
curl -X POST http://localhost:5000/api/notifications/meteo \
  -H "Content-Type: application/json" \
  -H "X-API-Key: abc123xyz..." \
  -d '{
    "titre": "alerte_meteo",
    "message": "Tempête prévue",
    "utilisateurs": [
      {
        "id": "etudiant1",
        "nom": "Jean Dupont",
        "email": "jean@univ.fr"
      }
    ]
  }'
```

---

## 🔄 Migration vers une Base de Données

Pour migrer vers une base de données (SQLite, PostgreSQL, etc.) :

1. Remplacez les fonctions `load_users()` et `save_users()` dans `auth.py`
2. Adaptez le schéma de données
3. Migrez les données existantes depuis `users.json`

Le reste du code (décorateurs, authentification) reste identique.

