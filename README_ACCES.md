# 🌐 Guide d'Accès à l'Application

## 📍 URLs Disponibles

### Page d'Accueil (Racine)
```
http://localhost:5000/
```
ou après déploiement :
```
https://votre-url/
```

**Réponse** : Page d'accueil avec informations sur l'API, endpoints disponibles et liens vers les interfaces.

---

### Interface d'Administration
```
http://localhost:5000/admin/
```
ou après déploiement :
```
https://votre-url/admin/
```

**Accès** : Requiert une authentification (admin ou operator)

**Fonctionnalités** :
- Tableau de bord
- Envoi de notifications
- Gestion des utilisateurs
- Configuration du système
- Statistiques et métriques

---

### Interface Étudiant
```
http://localhost:5000/student/
```
ou après déploiement :
```
https://votre-url/student/
```

**Accès** : Requiert une authentification (étudiant)

**Fonctionnalités** :
- Consulter ses notifications
- Gérer ses préférences (langue, canal)
- Voir son profil

---

### API - Vérification de Santé
```
http://localhost:5000/api/health
```
ou après déploiement :
```
https://votre-url/api/health
```

**Réponse** :
```json
{
  "status": "healthy",
  "service": "Système de notification d'urgence",
  "version": "1.0.0"
}
```

---

### API - Liste des Types de Notifications
```
http://localhost:5000/api/notifications/types
```
ou après déploiement :
```
https://votre-url/api/notifications/types
```

**Réponse** : Liste de tous les types de notifications disponibles avec leurs endpoints.

---

## 🔐 Identifiants par Défaut

### Administrateur
- **Username** : `admin`
- **Password** : `admin123`

### Opérateur
- **Username** : `operator`
- **Password** : `operator123`

### Étudiant
- **Username** : `etudiant1`
- **Password** : `etudiant123`

---

## 📝 Notes Importantes

1. **La route racine (`/`) affiche maintenant une page d'accueil** au lieu d'une erreur 404
2. **Les interfaces admin et student nécessitent une authentification**
3. **L'API est accessible sans authentification** pour certains endpoints (comme `/api/health`)
4. **Après déploiement**, remplacez `localhost:5000` par votre URL de production

---

## 🐛 Dépannage

### Erreur 404 sur la racine
- Vérifiez que le conteneur Docker est bien démarré
- Vérifiez les logs : `docker-compose logs`

### Erreur d'authentification
- Vérifiez que vous utilisez les bons identifiants
- Vérifiez que la base de données est initialisée

### L'application ne répond pas
- Vérifiez que le port 5000 est bien exposé
- Vérifiez les logs Docker pour les erreurs

