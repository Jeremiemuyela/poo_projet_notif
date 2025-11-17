# Guide du Système de Files d'Attente

## 📋 Vue d'ensemble

Le système de files d'attente permet de traiter les notifications de manière asynchrone, améliorant les performances et la réactivité de l'API.

---

## 🔧 Architecture

### Composants

1. **QueueManager** : Gestionnaire principal des files d'attente
2. **Workers** : Threads qui traitent les tâches en arrière-plan
3. **NotificationTask** : Représente une tâche de notification

### Fonctionnement

1. **Envoi** : L'API reçoit une requête et ajoute la tâche à la file d'attente
2. **Traitement** : Un worker récupère la tâche et la traite
3. **Suivi** : Le statut de la tâche est mis à jour (pending → processing → completed/failed)

---

## 🚀 Utilisation

### Envoyer une Notification (Asynchrone)

Les endpoints de notification retournent maintenant un `task_id` et un statut HTTP 202 (Accepted) :

```bash
curl -X POST http://localhost:5000/api/notifications/meteo \
  -H "Content-Type: application/json" \
  -H "X-API-Key: VOTRE_CLE" \
  -d '{
    "titre": "alerte_meteo",
    "message": "Tempête prévue",
    "utilisateurs": [...]
  }'
```

**Réponse :**
```json
{
  "success": true,
  "message": "Notification météorologique mise en file d'attente",
  "type": "meteo",
  "task_id": "abc123-def456-...",
  "status": "pending"
}
```

### Vérifier le Statut d'une Tâche

```bash
curl -X GET http://localhost:5000/api/queue/tasks/abc123-def456-... \
  -H "X-API-Key: VOTRE_CLE"
```

**Réponse :**
```json
{
  "success": true,
  "task": {
    "id": "abc123-def456-...",
    "type": "meteo",
    "status": "completed",
    "created_at_iso": "2025-11-13T10:00:00",
    "started_at_iso": "2025-11-13T10:00:01",
    "completed_at_iso": "2025-11-13T10:00:02",
    "result": {
      "success": true,
      "type": "meteo",
      "utilisateurs_notifies": 2
    }
  }
}
```

### Consulter les Statistiques

```bash
curl -X GET http://localhost:5000/api/queue/stats \
  -H "X-API-Key: VOTRE_CLE"
```

**Réponse :**
```json
{
  "success": true,
  "stats": {
    "total_enqueued": 100,
    "total_processed": 95,
    "total_failed": 2,
    "current_queue_size": 3,
    "tasks_by_status": {
      "pending": 2,
      "processing": 1,
      "completed": 90,
      "failed": 2
    },
    "total_tasks": 95,
    "workers": 2,
    "running": true
  }
}
```

---

## 📊 Interface d'Administration

### Page Files d'Attente

Accédez à : `http://localhost:5000/admin/queue`

**Fonctionnalités :**
- Vue en temps réel des statistiques
- Liste des tâches avec filtres par statut
- Actualisation automatique toutes les 3 secondes
- Nettoyage des tâches anciennes (admin uniquement)

### Statistiques Affichées

- **En attente** : Tâches en file d'attente
- **En traitement** : Tâches actuellement traitées
- **Terminées** : Tâches complétées avec succès
- **Échouées** : Tâches ayant échoué

---

## ⚙️ Configuration

### Nombre de Workers

Par défaut, 2 workers traitent les tâches. Pour modifier :

```python
# Dans queue_manager.py
queue_manager = QueueManager(num_workers=4)  # Augmenter le nombre
```

### Nettoyage Automatique

Les tâches complétées sont conservées pendant 24h par défaut. Pour nettoyer :

```bash
curl -X POST http://localhost:5000/admin/api/queue/clear \
  -H "X-API-Key: CLE_ADMIN" \
  -H "Content-Type: application/json" \
  -d '{"hours": 24}'
```

---

## 🔍 Statuts des Tâches

### `pending`
- Tâche en file d'attente, en attente de traitement
- Aucun worker ne l'a encore prise en charge

### `processing`
- Tâche actuellement traitée par un worker
- Le traitement est en cours

### `completed`
- Tâche terminée avec succès
- Le résultat est disponible dans `task.result`

### `failed`
- Tâche échouée
- L'erreur est disponible dans `task.error`

---

## 📈 Avantages

### Performance
- **Réactivité** : L'API répond immédiatement (202 Accepted)
- **Parallélisme** : Plusieurs notifications traitées simultanément
- **Scalabilité** : Facile d'ajouter plus de workers

### Fiabilité
- **Suivi** : Chaque tâche peut être suivie individuellement
- **Retry** : Les échecs sont enregistrés pour analyse
- **Historique** : Conservation des tâches pour audit

### Expérience Utilisateur
- **Pas d'attente** : L'utilisateur n'attend pas la fin du traitement
- **Transparence** : Statut visible en temps réel
- **Traçabilité** : Chaque notification a un ID unique

---

## 🐛 Dépannage

### Les tâches restent en "pending"
- Vérifiez que les workers sont démarrés : `stats.running` doit être `true`
- Vérifiez les logs du serveur pour les erreurs
- Augmentez le nombre de workers si nécessaire

### Tâches en échec
- Consultez `task.error` pour le message d'erreur
- Vérifiez les logs du serveur
- Vérifiez la configuration des notificateurs

### Performance lente
- Augmentez le nombre de workers
- Vérifiez la charge du serveur
- Considérez l'optimisation des canaux de notification

---

## 🔮 Améliorations Futures

1. **Priorités** : Tâches prioritaires traitées en premier
2. **Retry automatique** : Réessayer les tâches échouées
3. **Webhooks** : Notifications quand une tâche est terminée
4. **Limites de taux** : Limiter le nombre de tâches par minute
5. **Persistance** : Sauvegarder les tâches dans une base de données
6. **Monitoring** : Alertes si trop de tâches échouent

---

## 📝 Notes Techniques

### Thread Safety
- Le `QueueManager` utilise des locks pour la thread-safety
- Les workers sont des threads daemon (s'arrêtent avec l'application)

### Mémoire
- Les tâches sont stockées en mémoire
- Le nettoyage automatique évite l'accumulation
- Pour de gros volumes, considérez une base de données

### Arrêt Propre
- Les workers s'arrêtent proprement à l'arrêt de l'application
- Les tâches en cours sont terminées avant l'arrêt


