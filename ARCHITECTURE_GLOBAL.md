 # Guide d’Architecture Global (Mise à jour 2025-11-17)

 Ce document synthétise l’architecture complète du système de notifications, incluant l’API RESTful, l’interface d’administration, l’authentification, la gestion des étudiants par faculté/promotion et le traitement asynchrone via files d’attente.

 ---

 ## 1. Vue d’ensemble

 - **Framework principal** : Flask 3
 - **Domain core** : `projetnotif.py` (metaclasses, descripteurs, mixins)
 - **Traitement** : File d’attente (`queue_manager.py`)
 - **Interface admin** : Blueprint `admin.py` + templates Jinja2
 - **Authentification/Autorisation** : `auth.py` (API Key + sessions + rôles)
 - **Gestion étudiants** : `students.py` + `students.json`
 - **Métriques & supervision** : `metrics.py`
 - **Notifications** : Emails (mode test), SMS, App (mode test)

 ---

 ## 2. Diagramme des modules principaux

 ```mermaid
 graph TD
     A[app.py] -->|registre| B[projetnotif.py]
     A --> C[queue_manager.py]
     A --> D[auth.py]
     A --> E[students.py]
     A --> F[metrics.py]
     A --> G[admin.py Blueprint]
     B --> F
     G --> D
     G --> E
     G --> C
     C --> B
 ```

 ---

 ## 3. Domain Notification (projetnotif.py)

 ```mermaid
 classDiagram
     class Utilisateur{
         +EmailDescriptor email
         +PhoneDescriptor telephone
         +StudentIdDescriptor student_id
         +PreferredLanguageDescriptor langue
     }
     class CanalBase{
         +livrer(message)
     }
     class Email
     class SMS
     class App
     class NotificationBase{
         +envoyer(urgence, utilisateurs)
     }
     class NotificationMeteorologique
     class NotificationSecurite
     class NotificationSante
     class NotificationInfra
     class PreferencesStore{
         +obtenir(id)
         +sauvegarder(id, prefs)
     }
     Utilisateur --> PreferencesStore
     NotificationBase --> CanalBase
     NotificationMeteorologique --> NotificationBase
     NotificationSecurite --> NotificationBase
     NotificationSante --> NotificationBase
     NotificationInfra --> NotificationBase
     Email --> CanalBase
     SMS --> CanalBase
     App --> CanalBase
 ```

 ### Points clefs
 - **Metaclasses** (`NotificationMeta`, `ChannelMeta`, `TemplateMeta`, `ConfigMeta`) auto-enregistrent les composants.
 - **Descripteurs** *(Email, Phone, StudentId, PreferredLanguage)* garantissent la validité des données utilisateur.
 - **Décorateurs** *(log_action, add_performance_tracking, add_circuit_breaker, require_confirmation)* injectent des comportements transverses.

 ---

 ## 4. File d’attente asynchrone (`queue_manager.py`)

 ```mermaid
 classDiagram
     class QueueManager{
         -Queue task_queue
         -Dict tasks
         +set_processor(func)
         +enqueue(type, data)
         +get_task(id)
         +get_stats()
     }
     class NotificationTask{
         +id
         +type
         +data
         +status
         +result
         +timestamp
     }
     QueueManager --> NotificationTask
 ```

 - **Workflow** : `app.py` reçoit la requête → valide → `queue_manager.enqueue()` → worker appelle `process_notification_task()` → notificateur adapté envoie la notification.
 - **Endpoints queue** : `/api/queue/tasks/<id>`, `/api/queue/stats`.

 ---

 ## 5. Authentification & Autorisation (`auth.py`)

 - **Stockage** : `users.json` (hash SHA-256, rôle, API key)
 - **API** :
   - `@require_auth` (API Key ou session)
   - `@require_role('admin'|'operator'|'viewer')`
 - **Flux** : API protégées par `X-API-Key`, interface admin par session (`/admin/login` → formulaire → session Flask).

 ---

 ## 6. Gestion des étudiants (`students.py`)

 ```mermaid
 classDiagram
     class StudentsManager{
         -Dict students
         +filter_students(facultes, promotions, actif_only)
         +get_faculties()
         +get_promotions_for_faculty()
         +get_statistics()
     }
     class Student{
         +id
         +nom
         +email
         +telephone
         +langue
         +faculté
         +promotion
         +canal_prefere
         +actif
     }
     StudentsManager --> Student
 ```

 - **Facultés supportées** :
   - Informatique (L1→L4, M1, M2)
   - ESAU (Prépa, L1→L3, M1, M2)
   - Droit, SAE, SIC (L1→L3, M1, M2)
   - Science Technologique (Prépa, L1→L3, M1, M2)
   - Médecine (L1→L3, M1, M2, D1→D3)
 - **Utilisation** : `/admin/api/send-notification` filtre automatiquement les destinataires suivant les facultés/promotions sélectionnées dans l’interface.

 ---

 ## 7. Interface d’administration (Blueprint `admin.py`)

 ### Pages & fonctionnalités

 | Page | Description |
 |------|-------------|
 | `/admin/` | Dashboard (métriques globales + notificateurs + configs) |
 | `/admin/config/retry` | Configuration du mécanisme de retry |
 | `/admin/config/circuit-breaker` | Configuration du circuit breaker |
 | `/admin/status` | Statut système détaillé |
 | `/admin/queue` | Suivi des tâches en file d’attente |
 | `/admin/send` | Envoi de notifications (filtrage facultés/promotion) |
 | `/admin/login` | Authentification par formulaire |

 ### API internes
 - Config Retry : `GET/POST /admin/api/config/retry`, `POST /admin/api/config/retry/reset`
 - Config Circuit breaker : `GET/POST /admin/api/config/circuit-breaker`, `POST /admin/api/config/circuit-breaker/reset`
 - Statut & métriques : `GET /admin/api/status`, `GET /admin/api/metrics`
 - File d’attente : `GET /admin/api/queue/tasks`, `GET /admin/api/queue/stats`, `POST /admin/api/queue/clear`
 - Envoi notifications : `POST /admin/api/send-notification`
 - Référentiel étudiants : `GET /admin/api/students/faculties`, `GET /admin/api/students/stats`

 ---

 ## 8. Flux global d’envoi d’une notification (depuis l’admin)

 1. Administrateur se connecte (`/admin/login`)
 2. Page `/admin/send` → sélection des facultés/promotions → formulaire POST
 3. `/admin/api/send-notification`
    - vérifie l’authentification et le rôle
    - filtre les étudiants via `StudentsManager`
    - ajoute la tâche à la file via `queue_manager.enqueue`
 4. Worker → `process_notification_task` → notificateur adéquat (`projetnotif.py`)
 5. Décorateurs `@add_performance_tracking` + `metrics_manager.record_notification`
 6. Résultats visibles dans `/admin/queue` et le dashboard (`/admin/`)

 ---

 ## 9. Sécurité & conformité

 - **Authentification** : API Key pour endpoints REST, session pour l’admin
 - **Rôles** :
   - `admin` : accès complet (config, envoi, queue, users)
   - `operator` : envoi + suivi queue
   - `viewer` : consultation dashboard uniquement
 - **Protection CSRF** : non implémentée (à prévoir si ouverture publique)
 - **Sensibles ignorés par Git** : `users.json`, `students.json`

 ---

 ## 10. Améliorations futures

 1. Persistance BDD (PostgreSQL ou MongoDB) pour utilisateurs, étudiants, logs
 2. Intégration réelle des canaux (SMTP, SMS provider, push mobile)
 3. WebSockets pour l’actualisation temps réel du dashboard/queue
 4. Interface de gestion des étudiants (CRUD)
 5. Génération automatique de rapports (PDF / Excel)
 6. Observabilité : traces structurées + dashboard Grafana




