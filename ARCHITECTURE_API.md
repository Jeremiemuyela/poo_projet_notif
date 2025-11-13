# Architecture de l'API RESTful - Système de Notification d'Urgence

## 📋 Vue d'ensemble

L'API RESTful a été créée pour exposer les fonctionnalités du système de notification d'urgence via des endpoints HTTP. Elle transforme votre code Python monolithique en une application web accessible via des requêtes HTTP standard.

---

## 🏗️ Structure de l'Application

### Fichiers créés

1. **`app.py`** - Application Flask principale avec tous les endpoints
2. **`requirements.txt`** - Dépendances Python nécessaires
3. **`exemples_requetes.json`** - Exemples de requêtes JSON pour tester l'API

---

## 🔧 Architecture Détaillée

### 1. Initialisation Flask

```python
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False  # Support des caractères français
```

**Explication :**
- Crée l'instance Flask principale
- Configure le support UTF-8 pour les caractères français dans les réponses JSON

### 2. Initialisation des Services (Singleton Pattern)

```python
prefs_store = notif.PreferencesStore()
canaux = {
    "email": notif.Email(),
    "sms": notif.SMS(),
    "app": notif.App(),
}
notificateurs = {
    "meteo": notif.NotificationMeteorologique(canaux, prefs_store),
    "securite": notif.NotificationSecurite(canaux, prefs_store),
    "sante": notif.NotificationSante(canaux, prefs_store),
    "infra": notif.NotificationInfra(canaux, prefs_store),
}
```

**Explication :**
- **Singleton Pattern** : Les instances sont créées une seule fois au démarrage
- **Réutilisation** : Toutes les requêtes utilisent les mêmes instances (performances)
- **Séparation des responsabilités** : Chaque type de notification a son propre notificateur

### 3. Fonctions de Validation et Conversion

#### `valider_priorite(priorite_str: str) -> notif.Priorite`
- Convertit les chaînes JSON ("CRITIQUE", "HAUTE", "NORMALE") en énumérations Python
- Supporte plusieurs formats (majuscules, minuscules, nombres)
- Lève une exception si la valeur est invalide

#### `valider_langue(langue_str: str) -> notif.Langue`
- Convertit "fr"/"en" en énumération Langue
- Valeur par défaut : "fr" si non spécifiée

#### `creer_utilisateurs_depuis_json(users_data: List[Dict]) -> List[Utilisateur]`
- Transforme les données JSON en objets `Utilisateur` Python
- Valide les champs requis (id, nom, email)
- Gère les champs optionnels (langue, téléphone, préférences)
- Sauvegarde automatiquement les préférences dans le store

#### `creer_urgence_depuis_json(type_urgence, data: Dict) -> Urgence`
- Crée un objet `Urgence` depuis les données JSON
- Valide les champs requis (titre, message)
- Gère la priorité (défaut: NORMALE)

### 4. Gestion des Erreurs HTTP

```python
@app.errorhandler(400)  # Bad Request
@app.errorhandler(404)  # Not Found
@app.errorhandler(500)  # Internal Server Error
```

**Explication :**
- **400** : Requête mal formée (JSON invalide, champs manquants)
- **404** : Endpoint non trouvé
- **500** : Erreur serveur (exception non gérée)

Toutes les erreurs retournent un JSON standardisé :
```json
{
  "success": false,
  "error": "Type d'erreur",
  "message": "Détails de l'erreur"
}
```

---

## 🌐 Endpoints RESTful

### Endpoint 1: Health Check
```
GET /api/health
```

**Rôle :** Vérifier que l'API est opérationnelle

**Réponse :**
```json
{
  "status": "healthy",
  "service": "Système de notification d'urgence",
  "version": "1.0.0"
}
```

---

### Endpoint 2: Liste des Types
```
GET /api/notifications/types
```

**Rôle :** Lister tous les types de notifications disponibles

**Réponse :**
```json
{
  "success": true,
  "types": [
    {
      "type": "meteo",
      "endpoint": "/api/notifications/meteo",
      "description": "..."
    },
    ...
  ]
}
```

---

### Endpoint 3: Notification Météo
```
POST /api/notifications/meteo
```

**Rôle :** Envoyer une notification météorologique

**Body JSON :**
```json
{
  "titre": "alerte_meteo",
  "message": "Tempête prévue ce soir",
  "priorite": "HAUTE",
  "utilisateurs": [
    {
      "id": "etudiant1",
      "nom": "Jean Dupont",
      "email": "jean@univ.fr",
      "langue": "fr",
      "telephone": "+33123456789",
      "preferences": {
        "canal_prefere": "email",
        "actif": true
      }
    }
  ]
}
```

**Réponse succès (200) :**
```json
{
  "success": true,
  "message": "Notification météorologique envoyée avec succès",
  "type": "meteo",
  "utilisateurs_notifies": 2
}
```

**Fonctionnalités spécifiques :**
- Calcule automatiquement les zones à risque (via `calculer_zone_risque()`)
- Utilise le mécanisme de retry en cas d'échec
- Circuit breaker pour gérer les pannes

---

### Endpoint 4: Notification Sécurité
```
POST /api/notifications/securite
```

**Rôle :** Envoyer une notification de sécurité

**Body JSON :** Identique à météo, mais `priorite` est fortement recommandé (CRITIQUE pour urgences)

**Fonctionnalités spécifiques :**
- Si priorité CRITIQUE → déclenche `sortir_urgence()` automatiquement
- Requiert confirmation (via décorateur `@require_confirmation`)
- Circuit breaker et retry activés

---

### Endpoint 5: Notification Santé
```
POST /api/notifications/sante
```

**Rôle :** Envoyer une notification de santé

**Fonctionnalités spécifiques :**
- Requiert confirmation avant envoi
- Utilise le mixin `ConfirmableMixin`

---

### Endpoint 6: Notification Infrastructure
```
POST /api/notifications/infra
```

**Rôle :** Envoyer une notification d'infrastructure

**Fonctionnalités spécifiques :**
- Notification standard sans confirmation
- Logging automatique des communications

---

## 🔄 Flux de Traitement d'une Requête

1. **Réception HTTP** → Flask reçoit la requête POST
2. **Validation JSON** → Vérifie que le body est du JSON valide
3. **Validation des champs** → Vérifie les champs requis
4. **Conversion** → Transforme JSON → Objets Python (`Urgence`, `Utilisateur`)
5. **Traitement** → Appelle le notificateur approprié
6. **Envoi** → Le notificateur envoie via les canaux (email, SMS, app)
7. **Réponse** → Retourne un JSON de confirmation

---

## 📊 Format des Réponses

### Succès (200)
```json
{
  "success": true,
  "message": "Notification envoyée avec succès",
  "type": "meteo",
  "utilisateurs_notifies": 2
}
```

### Erreur de Validation (400)
```json
{
  "success": false,
  "error": "Erreur de validation",
  "message": "Le champ 'titre' est requis"
}
```

### Erreur Serveur (500)
```json
{
  "success": false,
  "error": "Erreur lors de l'envoi de la notification",
  "message": "Détails de l'exception"
}
```

---

## 🧪 Comment Tester l'API

### 1. Démarrer le serveur
```bash
python app.py
```

### 2. Tester avec curl
```bash
# Health check
curl http://localhost:5000/api/health

# Envoyer une notification météo
curl -X POST http://localhost:5000/api/notifications/meteo \
  -H "Content-Type: application/json" \
  -d @exemples_requetes.json
```

### 3. Tester avec Python requests
```python
import requests

response = requests.post(
    'http://localhost:5000/api/notifications/meteo',
    json={
        "titre": "alerte_meteo",
        "message": "Tempête prévue",
        "priorite": "HAUTE",
        "utilisateurs": [
            {
                "id": "etudiant1",
                "nom": "Jean Dupont",
                "email": "jean@univ.fr",
                "langue": "fr"
            }
        ]
    }
)
print(response.json())
```

---

## 🎯 Avantages de cette Architecture

1. **Séparation des responsabilités** : Chaque endpoint gère un type spécifique
2. **Réutilisabilité** : Les fonctions de validation sont partagées
3. **Maintenabilité** : Code organisé et commenté
4. **Extensibilité** : Facile d'ajouter de nouveaux endpoints
5. **Robustesse** : Gestion d'erreurs complète
6. **Standards REST** : Utilise les conventions HTTP (GET, POST, codes de statut)

---

## 🔮 Prochaines Étapes Possibles

- Authentification (JWT, API keys)
- Rate limiting (limiter les requêtes par IP)
- Logging structuré (fichiers de logs)
- Base de données (persistance des notifications)
- Documentation Swagger/OpenAPI
- Tests unitaires et d'intégration

