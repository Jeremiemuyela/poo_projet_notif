# 📚 Documentation Automatique de l'API avec Swagger

## 🎯 Vue d'ensemble

L'application utilise **Swagger/OpenAPI** pour générer automatiquement une documentation interactive de l'API. Cette documentation est accessible via une interface web moderne et permet de tester les endpoints directement depuis le navigateur.

---

## 🌐 Accès à la Documentation

### En Local
```
http://localhost:5000/api/docs
```

### Après Déploiement
```
https://votre-url/api/docs
```

---

## ✨ Fonctionnalités

### 1. Interface Interactive Swagger UI

- **Visualisation** de tous les endpoints disponibles
- **Description** détaillée de chaque endpoint
- **Schémas** de requête et de réponse
- **Test en direct** des endpoints depuis le navigateur
- **Authentification** intégrée pour les endpoints protégés

### 2. Endpoints Documentés

#### Health Check
- `GET /api/health` - Vérification de santé de l'API

#### Notifications
- `POST /api/notifications/meteo` - Envoyer une notification météorologique
- `POST /api/notifications/securite` - Envoyer une notification de sécurité (authentification requise)
- `POST /api/notifications/sante` - Envoyer une notification de santé (authentification requise)
- `POST /api/notifications/infra` - Envoyer une notification d'infrastructure (authentification requise)
- `GET /api/notifications/types` - Lister les types de notifications disponibles

#### Queue
- `GET /api/queue/tasks/<task_id>` - Récupérer le statut d'une tâche (authentification requise)
- `GET /api/queue/stats` - Récupérer les statistiques de la file d'attente (authentification requise)

---

## 🔐 Authentification dans Swagger

### Pour les Endpoints Protégés

1. Cliquez sur le bouton **"Authorize"** en haut de la page Swagger
2. Entrez votre clé API dans le champ `X-API-Key`
3. Cliquez sur **"Authorize"**
4. Toutes les requêtes suivantes incluront automatiquement votre clé API

### Obtenir une Clé API

- Via l'interface admin : `/admin/`
- Via l'API : `POST /admin/api/users` (en tant qu'admin)

---

## 📝 Utilisation

### 1. Explorer les Endpoints

1. Ouvrez `/api/docs` dans votre navigateur
2. Parcourez les différentes sections (Health, Notifications, Queue)
3. Cliquez sur un endpoint pour voir ses détails

### 2. Tester un Endpoint

1. Cliquez sur un endpoint pour l'étendre
2. Cliquez sur **"Try it out"**
3. Remplissez les paramètres si nécessaire
4. Cliquez sur **"Execute"**
5. Consultez la réponse dans la section "Responses"

### 3. Exemple : Envoyer une Notification Météo

1. Allez dans la section **"Notifications"**
2. Cliquez sur `POST /api/notifications/meteo`
3. Cliquez sur **"Try it out"**
4. Modifiez le JSON dans le champ "Request body" :
```json
{
  "titre": "Alerte météorologique",
  "message": "Tempête prévue ce soir",
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
```
5. Cliquez sur **"Execute"**
6. Consultez la réponse (code 202 avec task_id)

---

## 🔧 Configuration

### Fichier de Configuration

Le fichier `swagger_config.yaml` contient la configuration de base de Swagger. Il peut être personnalisé pour ajouter :
- Des tags supplémentaires
- Des schémas réutilisables
- Des exemples personnalisés
- Des descriptions détaillées

### Ajouter un Nouvel Endpoint à la Documentation

Pour documenter un nouvel endpoint, ajoutez une docstring Swagger dans votre fonction Flask :

```python
@app.route('/api/mon-endpoint', methods=['POST'])
def mon_endpoint():
    """
    Description de mon endpoint
    ---
    tags:
      - MaSection
    summary: Résumé de l'endpoint
    description: Description détaillée
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            champ1:
              type: string
              example: "valeur"
    responses:
      200:
        description: Succès
        schema:
          type: object
          properties:
            success: {type: boolean, example: true}
    """
    # Votre code ici
    pass
```

---

## 📊 Spécification OpenAPI

La spécification OpenAPI complète est disponible au format JSON :

```
http://localhost:5000/api/apispec.json
```

Cette spécification peut être utilisée avec :
- **Postman** : Importez la spécification pour générer une collection
- **Insomnia** : Importez pour créer des requêtes
- **Autres outils** : Tous les outils compatibles OpenAPI

---

## 🐛 Dépannage

### La page Swagger ne s'affiche pas

1. Vérifiez que `flasgger` est installé : `pip install flasgger`
2. Vérifiez les logs de l'application pour les erreurs
3. Vérifiez que le port 5000 est accessible

### Les endpoints ne s'affichent pas

1. Vérifiez que les docstrings Swagger sont correctement formatées
2. Vérifiez que les routes sont bien enregistrées dans Flask
3. Consultez `/api/apispec.json` pour voir la spécification générée

### Erreur d'authentification dans Swagger

1. Vérifiez que vous avez entré votre clé API correctement
2. Vérifiez que la clé API est valide dans la base de données
3. Vérifiez que l'endpoint nécessite bien une authentification

---

## 📚 Ressources

- **Documentation Flasgger** : https://github.com/flasgger/flasgger
- **Spécification OpenAPI** : https://swagger.io/specification/
- **Swagger UI** : https://swagger.io/tools/swagger-ui/

---

## ✅ Avantages

1. **Documentation toujours à jour** : Générée automatiquement depuis le code
2. **Test interactif** : Testez les endpoints sans outils externes
3. **Standard OpenAPI** : Compatible avec tous les outils modernes
4. **Interface intuitive** : Facile à utiliser pour les développeurs et les testeurs
5. **Schémas de validation** : Aide à comprendre la structure des données

---

## 🎉 Conclusion

La documentation Swagger rend votre API facilement explorable et testable. C'est un outil essentiel pour :
- Les développeurs qui intègrent votre API
- Les testeurs qui vérifient le fonctionnement
- La documentation technique du projet

