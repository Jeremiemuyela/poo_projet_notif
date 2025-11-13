# Guide d'Utilisation - Interface d'Administration

## 🚀 Démarrage Rapide

### 1. Installer les dépendances
```bash
pip install -r requirements.txt
```

### 2. Démarrer le serveur
```bash
python app.py
```

### 3. Accéder à l'interface
Ouvrez votre navigateur et allez à :
```
http://localhost:5000/admin/
```

---

## 📱 Pages Disponibles

### Tableau de Bord (`/admin/`)
- Vue d'ensemble du système (notificateurs, canaux, templates, configurations)
- Métriques de performance en temps réel (totaux, taux de succès, durées)
- Tableau détaillé par notificateur avec dernières exécutions
- Accès rapide aux configurations

### Configuration Retry (`/admin/config/retry`)
- Modifier le nombre de tentatives
- Ajuster le délai initial
- Configurer le facteur de backoff
- Réinitialiser aux valeurs par défaut

### Configuration Circuit Breaker (`/admin/config/circuit-breaker`)
- Définir le seuil d'échecs
- Configurer le temps de cooldown
- Réinitialiser aux valeurs par défaut

### Statut Système (`/admin/status`)
- Voir tous les composants actifs
- Liste des canaux disponibles
- Liste des templates
- Types de notifications enregistrés

---

## 📈 Métriques de Performance

### Métriques globales
- **Notifications envoyées** : total cumulé depuis le démarrage
- **Taux de succès** : succès / total (actualisé toutes les 5 secondes)
- **Durée moyenne** : moyenne des temps d'exécution (affichée en millisecondes)
- **Dernière notification** : date/heure locale de la dernière exécution

### Tableau par notificateur
- Nombre total d'exécutions, succès et échecs
- Taux de succès individuel
- Durée moyenne, minimale et maximale
- Timestamp de la dernière exécution
- Mise en avant des échecs (nouvelle valeur `last_error` disponible via l'API)

### Astuces
- Surveillez les hausses de durée moyenne pour détecter les lenteurs
- Les échecs successifs peuvent indiquer l'ouverture du circuit breaker
- Utilisez la section Statut pour vérifier les canaux/templates disponibles

---

## ⚙️ Configuration Retry

### Paramètres

#### Nombre de Tentatives
- **Description** : Nombre de fois que le système réessayera en cas d'échec
- **Valeur minimale** : 1
- **Valeur par défaut** : 3
- **Exemple** : Si une notification échoue, le système réessayera 3 fois

#### Délai Initial
- **Description** : Temps d'attente (en secondes) avant la première nouvelle tentative
- **Valeur minimale** : 0
- **Valeur par défaut** : 1 seconde
- **Exemple** : Après un échec, attendre 1 seconde avant de réessayer

#### Facteur de Backoff
- **Description** : Facteur multiplicateur pour augmenter le délai entre chaque tentative
- **Valeur minimale** : 1
- **Valeur par défaut** : 2
- **Exemple** : Avec delay=1s et backoff=2, les tentatives auront lieu après 1s, 2s, 4s

### Exemple de Configuration

**Configuration recommandée pour production :**
- Tentatives : 5
- Délai : 2 secondes
- Backoff : 2

**Résultat :** Les tentatives auront lieu après 2s, 4s, 8s, 16s, 32s

---

## ⚡ Configuration Circuit Breaker

### Paramètres

#### Seuil d'Échecs
- **Description** : Nombre d'échecs consécutifs avant d'ouvrir le circuit
- **Valeur minimale** : 1
- **Valeur par défaut** : 3
- **Exemple** : Après 3 échecs consécutifs, le circuit s'ouvre

#### Temps de Cooldown
- **Description** : Temps d'attente (en secondes) avant de réessayer après l'ouverture du circuit
- **Valeur minimale** : 0
- **Valeur par défaut** : 5 secondes
- **Exemple** : Après ouverture, attendre 5 secondes avant de réessayer

### Fonctionnement

1. **Circuit Fermé** : Les notifications sont envoyées normalement
2. **Échecs** : Si le seuil d'échecs est atteint, le circuit s'ouvre
3. **Circuit Ouvert** : Toutes les nouvelles tentatives sont bloquées
4. **Cooldown** : Après le temps de cooldown, le circuit se referme
5. **Nouvelle tentative** : Le système réessaye avec le circuit fermé

### Exemple de Configuration

**Configuration recommandée pour production :**
- Seuil : 5 échecs
- Cooldown : 10 secondes

**Résultat :** Après 5 échecs, le système attend 10 secondes avant de réessayer

---

## 🔍 Statut Système

### Informations Affichées

#### Statistiques
- **Notificateurs** : Nombre de types de notificateurs enregistrés
- **Canaux** : Nombre de canaux de notification disponibles
- **Templates** : Nombre de templates de messages disponibles
- **Configurations** : Nombre de configurations actives

#### Composants
- **Types de Notifications** : Liste de tous les types enregistrés
- **Canaux Disponibles** : Liste des canaux (email, sms, app)
- **Templates Disponibles** : Liste des templates de messages

---

## 💡 Conseils d'Utilisation

### Pour les Notifications Critiques
- Augmenter le nombre de tentatives (5-10)
- Réduire le délai initial (0.5-1s)
- Augmenter le backoff (2-3)

### Pour les Notifications Normales
- Garder les valeurs par défaut
- Augmenter le cooldown du circuit breaker (10-30s)

### Pour les Tests
- Réduire le nombre de tentatives (1-2)
- Réduire les délais (0.1-0.5s)
- Faciliter le déclenchement du circuit breaker (seuil: 2)

---

## 🐛 Dépannage

### L'interface ne se charge pas
- Vérifiez que le serveur Flask est démarré
- Vérifiez l'URL : `http://localhost:5000/admin/`
- Vérifiez la console du serveur pour les erreurs

### Les modifications ne sont pas sauvegardées
- Vérifiez la console du navigateur (F12) pour les erreurs JavaScript
- Vérifiez que les valeurs sont valides (min, type)
- Actualisez la page après modification

### Les valeurs ne se chargent pas
- Vérifiez la connexion réseau
- Vérifiez que l'API répond : `http://localhost:5000/admin/api/status`
- Vérifiez la console du serveur pour les erreurs

---

## 📚 API Endpoints

### Configuration Retry
- `GET /admin/api/config/retry` - Récupérer la configuration
- `POST /admin/api/config/retry` - Mettre à jour la configuration
- `POST /admin/api/config/retry/reset` - Réinitialiser

### Configuration Circuit Breaker
- `GET /admin/api/config/circuit-breaker` - Récupérer la configuration
- `POST /admin/api/config/circuit-breaker` - Mettre à jour la configuration
- `POST /admin/api/config/circuit-breaker/reset` - Réinitialiser

### Statut
- `GET /admin/api/status` - Récupérer le statut complet (configurations + métriques)

### Métriques
- `GET /admin/api/metrics` - Récupérer uniquement les métriques globales et par notificateur

---

## 🎨 Personnalisation

### Modifier les Couleurs
Éditez `templates/admin/base.html` et modifiez les variables CSS :
```css
:root {
    --primary-color: #0d6efd;
    --secondary-color: #6c757d;
    ...
}
```

### Ajouter des Pages
1. Créer un nouveau template dans `templates/admin/`
2. Ajouter une route dans `admin.py`
3. Ajouter un lien dans la sidebar de `base.html`

---

## ✅ Checklist de Configuration

- [ ] Accéder à l'interface d'administration
- [ ] Vérifier le statut du système
- [ ] Configurer le retry selon vos besoins
- [ ] Configurer le circuit breaker selon vos besoins
- [ ] Tester les modifications
- [ ] Vérifier que les configurations sont appliquées

---

## 📞 Support

Pour toute question ou problème :
1. Vérifiez la documentation dans `ARCHITECTURE_ADMIN.md`
2. Consultez les logs du serveur Flask
3. Vérifiez la console du navigateur (F12)

