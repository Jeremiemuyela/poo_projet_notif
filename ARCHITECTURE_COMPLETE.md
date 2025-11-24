# 🏗️ Architecture Complète de l'Application

## 📋 Table des Matières

1. [Vue d'ensemble](#vue-densemble)
2. [Architecture en Couches](#architecture-en-couches)
3. [Composants Principaux](#composants-principaux)
4. [Flux de Données](#flux-de-données)
5. [Base de Données](#base-de-données)
6. [Sécurité et Authentification](#sécurité-et-authentification)
7. [Patterns de Conception](#patterns-de-conception)
8. [Déploiement](#déploiement)

---

## 🎯 Vue d'ensemble

L'application est un **système de notification d'urgence** pour les étudiants, construit avec **Flask** (Python) et utilisant une architecture modulaire en couches.

### Caractéristiques Principales

- ✅ **API RESTful** pour l'envoi de notifications
- ✅ **Interfaces Web** (Admin et Étudiant)
- ✅ **Traitement asynchrone** via file d'attente
- ✅ **Traduction automatique** (FR/EN) selon préférences
- ✅ **Base de données SQLite** pour persistance
- ✅ **Documentation Swagger** automatique
- ✅ **Métriques de performance** intégrées
- ✅ **Déploiement Docker** prêt

---

## 🏛️ Architecture en Couches

```
┌─────────────────────────────────────────────────────────────┐
│                    COUCHE PRÉSENTATION                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Admin UI   │  │  Student UI  │  │  Swagger UI  │     │
│  │  (Templates) │  │  (Templates) │  │  (API Docs)  │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                    COUCHE APPLICATION                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   app.py     │  │   admin.py    │  │  student.py  │     │
│  │  (Routes API)│  │  (Blueprint)  │  │  (Blueprint) │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Flask Application (app)                   │  │
│  │  - Blueprints: admin_bp, student_bp                   │  │
│  │  - Swagger Documentation                               │  │
│  │  - Error Handlers                                      │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                    COUCHE MÉTIER                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ projetnotif  │  │ queue_manager │  │ translation  │     │
│  │   (Domain)   │  │  (Async)      │  │  (Service)   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   metrics    │  │ notifications │  │    auth       │     │
│  │  (Tracking)  │  │     _log     │  │ (Security)   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                    COUCHE DONNÉES                           │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              db.py (SQLite)                          │  │
│  │  - get_db_connection()                               │  │
│  │  - execute_query()                                   │  │
│  │  - fetch_one() / fetch_all()                         │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         notifications.db (SQLite Database)            │  │
│  │  - users, students, notifications_log                │  │
│  │  - translations, queue_tasks, metrics                 │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 🧩 Composants Principaux

### 1. **app.py** - Application Flask Principale

**Responsabilités :**
- Initialisation de l'application Flask
- Configuration des Blueprints (admin, student)
- Routes API RESTful principales
- Gestion des erreurs HTTP (400, 404, 500)
- Configuration Swagger pour documentation API
- Initialisation de la base de données

**Routes Principales :**
```python
GET  /                    # Page d'accueil avec infos API
GET  /api/health          # Health check
GET  /api/notifications/types  # Liste des types
POST /api/notifications/meteo  # Notification météo
POST /api/notifications/securite  # Notification sécurité (auth)
POST /api/notifications/sante     # Notification santé (auth)
POST /api/notifications/infra     # Notification infrastructure (auth)
GET  /api/queue/tasks/<id>  # Statut d'une tâche (auth)
GET  /api/queue/stats       # Statistiques queue (auth)
```

**Initialisation :**
```python
1. Création de l'app Flask
2. Configuration SECRET_KEY (env)
3. Initialisation DB si nécessaire
4. Création utilisateurs par défaut
5. Enregistrement Blueprints
6. Configuration Swagger
7. Création des services (canaux, notificateurs)
8. Démarrage queue_manager
```

---

### 2. **projetnotif.py** - Domaine Métier

**Responsabilités :**
- Définition des modèles de domaine (Urgence, Utilisateur, Message)
- Énumérations (Priorite, Langue, TypeUrgence)
- Canaux de notification (Email, SMS, App)
- Notificateurs spécialisés (Météo, Sécurité, Santé, Infra)
- Gestion des préférences utilisateur (singleton)
- Patterns de résilience (Retry, Circuit Breaker)

**Classes Principales :**

#### Modèles
- `Urgence` : Représente une urgence (type, titre, message, priorité)
- `Utilisateur` : Représente un étudiant (id, nom, email, langue, téléphone)
- `Message` : Message formaté pour un canal spécifique
- `Preferences` : Préférences utilisateur (langue, canal, actif)

#### Canaux de Notification
- `Email` : Envoi par email (simulé)
- `SMS` : Envoi par SMS (simulé)
- `App` : Notification dans l'application (simulé)

#### Notificateurs Spécialisés
- `NotificationMeteorologique` : Calcul zones à risque
- `NotificationSecurite` : Gestion urgences critiques
- `NotificationSante` : Confirmation requise
- `NotificationInfra` : Notifications infrastructure

#### Patterns de Résilience
- `RetryConfig` : Configuration retry (attempts, delay, backoff)
- `CircuitBreakerConfig` : Configuration circuit breaker (threshold, cooldown)

---

### 3. **queue_manager.py** - Traitement Asynchrone

**Responsabilités :**
- Gestion de la file d'attente des notifications
- Traitement asynchrone avec workers threads
- Suivi du statut des tâches
- Statistiques de la queue

**Architecture :**
```python
QueueManager
├── Queue (threading.Queue)
├── Workers (2 threads par défaut)
├── Tasks Registry (Dict[str, NotificationTask])
└── Statistics Tracking
```

**Flux de Traitement :**
```
1. Enqueue (app.py) → Création NotificationTask
2. Worker récupère la tâche
3. Appel du processor (process_notification_task)
4. Traitement de la notification
5. Mise à jour statut (completed/failed)
6. Enregistrement résultat
```

**Statuts des Tâches :**
- `PENDING` : En attente de traitement
- `PROCESSING` : En cours de traitement
- `COMPLETED` : Traitement réussi
- `FAILED` : Échec du traitement

---

### 4. **admin.py** - Interface d'Administration

**Responsabilités :**
- Interface web pour administrateurs
- Gestion des utilisateurs
- Configuration système (Retry, Circuit Breaker)
- Envoi de notifications via interface
- Visualisation des métriques et statistiques
- Gestion de la file d'attente

**Routes Principales :**
```python
GET  /admin/                    # Dashboard
GET  /admin/login               # Page de connexion
GET  /admin/config/retry        # Configuration Retry
GET  /admin/config/circuit-breaker  # Configuration Circuit Breaker
GET  /admin/status              # Statut système
GET  /admin/queue               # Gestion queue
GET  /admin/send                # Envoi notification
GET  /admin/api/users           # API: Liste utilisateurs
POST /admin/api/users           # API: Créer utilisateur
POST /admin/api/send-notification  # API: Envoyer notification
```

**Authentification :**
- Session Flask pour interface web
- Clé API (`X-API-Key`) pour API
- Rôles : `admin`, `operator`, `viewer`

---

### 5. **student.py** - Interface Étudiante

**Responsabilités :**
- Interface web pour étudiants
- Consultation des notifications
- Gestion des préférences (langue, canal)
- Visualisation du profil

**Routes Principales :**
```python
GET  /student/                  # Dashboard étudiant
GET  /student/login            # Page de connexion
GET  /student/notifications    # Liste notifications
GET  /student/preferences      # Gestion préférences
GET  /student/profile          # Profil étudiant
GET  /student/api/profile      # API: Profil
GET  /student/api/preferences  # API: Préférences
GET  /student/api/notifications  # API: Notifications
POST /student/api/preferences  # API: Mettre à jour préférences
```

**Authentification :**
- Session Flask basée sur `student_id`
- Vérification existence étudiant dans DB

---

### 6. **auth.py** - Authentification et Autorisation

**Responsabilités :**
- Authentification utilisateurs (username/password)
- Authentification API (clé API)
- Gestion des rôles et permissions
- Hash des mots de passe (SHA-256)
- Génération de clés API

**Fonctions Principales :**
```python
authenticate_user(username, password) → Dict | None
authenticate_api_key(api_key) → Dict | None
create_user(username, password, role) → Dict
get_user_permissions(role) → Set[str]
require_auth(f) → Decorator
require_role(*roles) → Decorator
require_permission(permission) → Decorator
```

**Rôles et Permissions :**
- `admin` : Toutes permissions (`*`)
- `operator` : `read`, `send_notifications`
- `viewer` : `read` uniquement

---

### 7. **db.py** - Accès aux Données

**Responsabilités :**
- Gestion des connexions SQLite
- Exécution de requêtes SQL
- Mode WAL pour meilleure concurrence
- Context managers pour transactions

**Fonctions Principales :**
```python
get_db_connection() → Context Manager
execute_query(query, params) → None
execute_many(query, params_list) → None
fetch_one(query, params) → Dict | None
fetch_all(query, params) → List[Dict]
execute_script(sql_script) → None
init_db() → None
db_exists() → bool
```

**Configuration SQLite :**
- Mode WAL (Write-Ahead Logging)
- Synchronous = NORMAL
- Foreign Keys activés

---

### 8. **translation_service.py** - Service de Traduction

**Responsabilités :**
- Traduction automatique des notifications
- Support FR/EN
- Fallback manuel (base de données)
- Intégration deep-translator (optionnel)

**Stratégie de Traduction :**
```
1. Recherche dans DB (translations table)
2. Si non trouvé → deep-translator (GoogleTranslator)
3. Si échec → retour texte original
```

**Utilisation :**
```python
translation_service.translate_text(
    texte="Alerte météo",
    target_lang="en",
    source_lang="fr"
) → "Weather Alert"
```

---

### 9. **notifications_log.py** - Journal des Notifications

**Responsabilités :**
- Enregistrement des notifications envoyées
- Suivi du statut (unread/read)
- Persistance dans base de données SQLite

**Fonctions Principales :**
```python
log_notification(student_id, type, titre, message, ...) → NotificationLog
get_notifications(student_id) → List[NotificationLog]
mark_as_read(notification_id) → None
get_unread_count(student_id) → int
```

**Structure :**
- Stockage dans table `notifications_log`
- Statut : `unread` / `read`
- Timestamps : `created_at`, `read_at`

---

### 10. **metrics.py** - Métriques de Performance

**Responsabilités :**
- Collecte des métriques de performance
- Suivi des durées d'exécution
- Statistiques par notificateur
- Métriques globales

**Métriques Collectées :**
- Nombre total de notifications
- Taux de succès/échec
- Durée moyenne/min/max
- Dernière notification
- Métriques par notificateur

**Utilisation :**
```python
metrics_manager.record_notification(
    notifier_name="NotificationMeteorologique",
    duration=2.5,
    success=True
)
```

---

### 11. **students.py** - Gestion des Étudiants

**Responsabilités :**
- Gestion de la liste des étudiants
- Chargement depuis base de données
- Recherche et filtrage

**Fonctions Principales :**
```python
get_student(student_id) → Student | None
get_all_students() → List[Student]
search_students(query) → List[Student]
filter_by_faculty(faculty) → List[Student]
```

---

## 🔄 Flux de Données

### Flux 1 : Envoi d'une Notification (API)

```
1. Client → POST /api/notifications/meteo
   └─ Body JSON: {titre, message, priorite, utilisateurs}

2. app.py → Validation des données
   └─ Vérification JSON valide
   └─ Vérification champs requis

3. app.py → queue_manager.enqueue("meteo", data)
   └─ Création NotificationTask
   └─ Ajout à la queue
   └─ Retour task_id

4. Réponse immédiate → 202 Accepted
   └─ {success: true, task_id: "...", status: "pending"}

5. Worker (thread) → Traitement asynchrone
   └─ Récupération tâche de la queue
   └─ Appel process_notification_task()

6. process_notification_task() → Création objets métier
   └─ creer_urgence_depuis_json()
   └─ creer_utilisateurs_depuis_json()

7. Notificateur → Envoi notifications
   └─ Pour chaque utilisateur:
      ├─ Récupération préférences (langue, canal)
      ├─ Traduction du message
      ├─ Sélection du canal (email/sms/app)
      ├─ Envoi via canal
      └─ Enregistrement dans notifications_log

8. Mise à jour statut tâche → COMPLETED
```

### Flux 2 : Consultation des Notifications (Étudiant)

```
1. Étudiant → GET /student/notifications
   └─ Vérification session (require_student_auth)

2. student.py → notifications_logger.get_notifications(student_id)
   └─ Requête DB: SELECT * FROM notifications_log WHERE student_id = ?

3. Récupération préférences langue étudiant
   └─ Préférences > Profil > Défaut (fr)

4. Affichage notifications (déjà traduites lors de l'envoi)
   └─ Format JSON pour API
   └─ Template HTML pour interface web

5. Réponse → Liste des notifications
```

### Flux 3 : Traduction d'une Notification

```
1. Notification créée avec texte FR

2. Pour chaque utilisateur:
   └─ Récupération langue préférée
      ├─ Préférence utilisateur (priorité 1)
      ├─ Langue profil (priorité 2)
      └─ Défaut FR (priorité 3)

3. translation_service.translate_text()
   └─ Si langue cible = langue source → Pas de traduction
   └─ Sinon:
      ├─ Recherche DB (translations table)
      ├─ Si trouvé → Retour traduction
      ├─ Sinon → deep-translator (GoogleTranslator)
      └─ Si échec → Texte original

4. Message traduit envoyé via canal préféré
```

---

## 💾 Base de Données

### Schéma SQLite

#### Table: `users`
```sql
- id (INTEGER PRIMARY KEY)
- username (VARCHAR UNIQUE)
- password_hash (VARCHAR)
- role (VARCHAR) -- admin, operator, viewer
- api_key (VARCHAR UNIQUE)
- active (BOOLEAN)
- created_at (TIMESTAMP)
- last_login (TIMESTAMP)
```

#### Table: `students`
```sql
- id (VARCHAR PRIMARY KEY)
- nom (VARCHAR)
- email (VARCHAR)
- telephone (VARCHAR)
- langue (VARCHAR) -- fr, en
- faculty (VARCHAR)
- actif (BOOLEAN)
- created_at (TIMESTAMP)
```

#### Table: `notifications_log`
```sql
- id (INTEGER PRIMARY KEY)
- student_id (VARCHAR)
- notification_type (VARCHAR)
- titre (VARCHAR)
- message (TEXT)
- priorite (VARCHAR)
- canal (VARCHAR)
- status (VARCHAR) -- unread, read
- created_at (TIMESTAMP)
- read_at (TIMESTAMP)
```

#### Table: `translations`
```sql
- id (INTEGER PRIMARY KEY)
- key_text (VARCHAR UNIQUE)
- fr (TEXT)
- en (TEXT)
```

#### Table: `queue_tasks`
```sql
- id (VARCHAR PRIMARY KEY)
- type (VARCHAR)
- data (TEXT) -- JSON
- status (VARCHAR) -- pending, processing, completed, failed
- created_at (TIMESTAMP)
- started_at (TIMESTAMP)
- completed_at (TIMESTAMP)
- error (TEXT)
- result (TEXT) -- JSON
```

#### Table: `metrics`
```sql
- id (INTEGER PRIMARY KEY)
- notifier_name (VARCHAR)
- duration (REAL)
- success (BOOLEAN)
- error_message (TEXT)
- timestamp (TIMESTAMP)
```

---

## 🔒 Sécurité et Authentification

### Mécanismes d'Authentification

#### 1. Interface Web (Sessions Flask)
```python
# Connexion
session['user'] = user_dict  # Admin
session['student_id'] = student_id  # Étudiant

# Vérification
@require_auth  # Vérifie session['user']
@require_student_auth  # Vérifie session['student_id']
```

#### 2. API REST (Clés API)
```python
# En-tête requis
X-API-Key: votre_cle_api

# Vérification
authenticate_api_key(api_key) → User | None
```

### Hash des Mots de Passe
- Algorithme : SHA-256
- Note : Pour production, utiliser bcrypt ou argon2

### Rôles et Permissions
- **admin** : Accès complet (`*`)
- **operator** : Lecture + Envoi notifications
- **viewer** : Lecture seule

---

## 🎨 Patterns de Conception

### 1. Singleton Pattern
```python
# PreferencesStore - Une seule instance partagée
class PreferencesStore:
    _instance = None
    _prefs_shared = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
```

### 2. Factory Pattern
```python
# Création de notificateurs selon le type
notificateurs = {
    "meteo": NotificationMeteorologique(...),
    "securite": NotificationSecurite(...),
    "sante": NotificationSante(...),
    "infra": NotificationInfra(...)
}
```

### 3. Strategy Pattern
```python
# Canaux de notification interchangeables
canaux = {
    "email": Email(),
    "sms": SMS(),
    "app": App()
}
```

### 4. Decorator Pattern
```python
# Décorateurs pour authentification/autorisation
@require_auth
@require_role('admin', 'operator')
def ma_fonction():
    pass
```

### 5. Observer Pattern
```python
# Métriques enregistrées automatiquement
@log_action  # Décorateur qui enregistre les métriques
def envoyer(self, urgence, utilisateurs):
    pass
```

### 6. Template Method Pattern
```python
# NotificationBase définit le flux, sous-classes implémentent les détails
class NotificationBase:
    def envoyer(self, urgence, utilisateurs):
        # Flux commun
        for user in utilisateurs:
            charge = self.build_context(...)  # Méthode abstraite
            canal.livrer(message)
```

---

## 🚀 Déploiement

### Architecture Docker

```
┌─────────────────────────────────────┐
│         Docker Container            │
│  ┌───────────────────────────────┐ │
│  │    Flask Application          │ │
│  │    - Gunicorn (WSGI Server)   │ │
│  │    - 2 Workers                │ │
│  └───────────────────────────────┘ │
│                                     │
│  ┌───────────────────────────────┐ │
│  │    SQLite Database            │ │
│  │    - notifications.db          │ │
│  │    - Volume persistant        │ │
│  └───────────────────────────────┘ │
│                                     │
│  ┌───────────────────────────────┐ │
│  │    Queue Workers              │ │
│  │    - 2 Threads                │ │
│  └───────────────────────────────┘ │
└─────────────────────────────────────┘
```

### Configuration Docker

**Dockerfile :**
- Base : `python:3.11-slim`
- Installation dépendances système (gcc, curl)
- Installation dépendances Python (`requirements.txt`)
- Copie code application
- Port exposé : 5000
- Commande : `gunicorn --bind 0.0.0.0:5000 --workers 2 app:app`

**docker-compose.yml :**
- Service `web` : Application Flask
- Volumes : Persistance DB et données
- Health check : `/api/health`
- Variables d'environnement : `SECRET_KEY`, `FLASK_ENV`

---

## 📊 Diagramme de Séquence : Envoi Notification

```
Client          app.py        QueueManager    Worker      Notificateur    Translation    DB
  │               │                │            │            │              │          │
  │ POST /api/    │                │            │            │              │          │
  │ notifications │                │            │            │              │          │
  ├──────────────>│                │            │            │              │          │
  │               │ enqueue()      │            │            │              │          │
  │               ├───────────────>│            │            │              │          │
  │               │                │ Task créée │            │              │          │
  │               │<───────────────┤            │            │              │          │
  │               │ task_id        │            │            │              │          │
  │ 202 Accepted  │                │            │            │              │          │
  │<──────────────┤                │            │            │              │          │
  │               │                │            │            │              │          │
  │               │                │            │ Récupère   │              │          │
  │               │                │            │<───────────┤            │          │
  │               │                │            │            │              │          │
  │               │                │            │ processor() │              │          │
  │               │                │            ├────────────>│              │          │
  │               │                │            │            │              │          │
  │               │                │            │            │ Pour chaque  │          │
  │               │                │            │            │ utilisateur:  │          │
  │               │                │            │            │              │          │
  │               │                │            │            │ traduire()    │          │
  │               │                │            │            ├──────────────>│          │
  │               │                │            │            │              │          │
  │               │                │            │            │              │ DB query │
  │               │                │            │            │              ├─────────>│
  │               │                │            │            │              │<─────────┤
  │               │                │            │            │<──────────────┤          │
  │               │                │            │            │ Texte traduit │          │
  │               │                │            │            │              │          │
  │               │                │            │            │ livrer()      │          │
  │               │                │            │            ├───────────────┐          │
  │               │                │            │            │              │          │
  │               │                │            │            │ log_notification│        │
  │               │                │            │            ├──────────────────────────>│
  │               │                │            │            │              │          │
  │               │                │            │<───────────┤              │          │
  │               │                │            │ Completed  │              │          │
  │               │                │            │            │              │          │
```

---

## 🔍 Points Clés de l'Architecture

### ✅ Forces

1. **Modularité** : Séparation claire des responsabilités
2. **Extensibilité** : Facile d'ajouter nouveaux types de notifications
3. **Performance** : Traitement asynchrone avec queue
4. **Maintenabilité** : Code organisé et documenté
5. **Testabilité** : Composants isolés et testables
6. **Scalabilité** : Architecture prête pour scaling horizontal

### ⚠️ Points d'Attention

1. **SQLite** : Limité pour haute concurrence (considérer PostgreSQL en production)
2. **SHA-256** : Pour production, utiliser bcrypt/argon2
3. **Simulation Canaux** : Les canaux (email/sms/app) sont simulés
4. **Thread Safety** : Queue manager utilise locks pour thread safety

---

## 📚 Technologies Utilisées

- **Flask** : Framework web Python
- **SQLite** : Base de données relationnelle
- **Gunicorn** : Serveur WSGI pour production
- **Flasgger** : Documentation Swagger automatique
- **deep-translator** : Service de traduction
- **Docker** : Conteneurisation
- **Threading** : Traitement asynchrone

---

## 🎓 Conclusion

Cette architecture suit les **bonnes pratiques** de développement :
- Séparation des responsabilités
- Patterns de conception appropriés
- Traitement asynchrone pour performance
- Documentation automatique
- Prête pour déploiement production

L'application est **modulaire**, **maintenable** et **extensible**.

