# 📊 Guide de Migration vers une Base de Données

## ✅ Déploiement Actuel (Sans Base de Données)

**Oui, vous pouvez déployer maintenant sans base de données !**

Votre application utilise actuellement des fichiers JSON pour stocker les données :
- `users.json` - Utilisateurs/admin
- `students.json` - Étudiants
- `notifications_log.json` - Historique des notifications

### ✅ Avantages du système actuel
- Simple à déployer
- Pas de configuration de base de données nécessaire
- Fonctionne immédiatement
- Parfait pour les tests et petits projets

### ⚠️ Limitations
- Les données sont stockées localement dans le conteneur
- Perte de données si le conteneur est supprimé (sauf si vous utilisez des volumes)
- Pas de sauvegarde automatique
- Performance limitée pour de grandes quantités de données
- Pas de transactions ACID
- Pas de relations entre données

---

## 🚀 Déploiement Actuel avec Docker

Votre `docker-compose.yml` inclut déjà un volume pour persister les données :

```yaml
volumes:
  - ./data:/app/data
```

Cela signifie que même si le conteneur est supprimé, les données JSON seront conservées dans le dossier `./data` sur votre machine hôte.

### Pour déployer maintenant :

1. **Testez localement** :
```bash
docker-compose up -d
```

2. **Déployez sur Railway/Render** :
   - Les plateformes cloud gèrent automatiquement les volumes
   - Les données seront persistées dans le système de fichiers du conteneur

---

## 📈 Quand Ajouter une Base de Données ?

Ajoutez une base de données quand :
- ✅ Vous avez beaucoup d'utilisateurs (>1000)
- ✅ Vous avez besoin de recherches complexes
- ✅ Vous avez besoin de relations entre données
- ✅ Vous avez besoin de transactions
- ✅ Vous avez besoin de sauvegardes automatiques
- ✅ Vous avez besoin de meilleures performances

---

## 🗄️ Options de Base de Données pour Plus Tard

### 1. **PostgreSQL** (Recommandé) ⭐
- ✅ Gratuit et open-source
- ✅ Très performant
- ✅ Supporte les relations complexes
- ✅ Excellent pour Flask avec SQLAlchemy
- ✅ Disponible sur toutes les plateformes cloud

### 2. **SQLite** (Simple)
- ✅ Pas de serveur nécessaire
- ✅ Fichier unique
- ✅ Parfait pour petits projets
- ⚠️ Limité pour la production à grande échelle

### 3. **MySQL/MariaDB**
- ✅ Très populaire
- ✅ Bonne performance
- ✅ Supporté partout

### 4. **MongoDB** (NoSQL)
- ✅ Flexible (documents JSON)
- ✅ Facile à migrer depuis JSON
- ✅ Bon pour données non structurées

---

## 🔄 Plan de Migration Future

### Étape 1 : Préparer la Structure

Créez un nouveau fichier `models.py` avec SQLAlchemy :

```python
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Student(db.Model):
    id = db.Column(db.String(50), primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    telephone = db.Column(db.String(20))
    langue = db.Column(db.String(2), default='fr')
    faculté = db.Column(db.String(100))
    promotion = db.Column(db.String(10))
    canal_prefere = db.Column(db.String(20), default='email')
    actif = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class User(db.Model):
    id = db.Column(db.String(50), primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    api_key = db.Column(db.String(255), unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class NotificationLog(db.Model):
    id = db.Column(db.String(50), primary_key=True)
    student_id = db.Column(db.String(50), db.ForeignKey('student.id'), nullable=False)
    type = db.Column(db.String(20), nullable=False)
    titre = db.Column(db.Text, nullable=False)
    message = db.Column(db.Text, nullable=False)
    priorite = db.Column(db.String(20), nullable=False)
    canal = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default='unread')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    read_at = db.Column(db.DateTime, nullable=True)
```

### Étape 2 : Script de Migration

Créez un script `migrate_to_db.py` pour migrer les données JSON vers la base de données :

```python
import json
from app import app, db
from models import Student, User, NotificationLog

def migrate_students():
    with open('students.json', 'r', encoding='utf-8') as f:
        students_data = json.load(f)
    
    for student_id, student_data in students_data.items():
        student = Student(
            id=student_id,
            nom=student_data['nom'],
            email=student_data['email'],
            telephone=student_data.get('telephone'),
            langue=student_data.get('langue', 'fr'),
            faculté=student_data.get('faculté', ''),
            promotion=student_data.get('promotion', ''),
            canal_prefere=student_data.get('canal_prefere', 'email'),
            actif=student_data.get('actif', True)
        )
        db.session.add(student)
    
    db.session.commit()
    print(f"✅ {len(students_data)} étudiants migrés")

# Faire de même pour users.json et notifications_log.json
```

### Étape 3 : Mettre à Jour le Code

Modifier `students.py`, `auth.py`, et `notifications_log.py` pour utiliser la base de données au lieu des fichiers JSON.

---

## 🐳 Docker avec Base de Données (Pour Plus Tard)

Quand vous serez prêt, voici un exemple de `docker-compose.yml` avec PostgreSQL :

```yaml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    container_name: notification-db
    environment:
      POSTGRES_USER: notification_user
      POSTGRES_PASSWORD: notification_password
      POSTGRES_DB: notification_db
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  web:
    build: .
    container_name: notification-system
    ports:
      - "5000:5000"
    environment:
      - SECRET_KEY=${SECRET_KEY}
      - FLASK_ENV=production
      - DATABASE_URL=postgresql://notification_user:notification_password@db:5432/notification_db
    depends_on:
      - db
    volumes:
      - ./data:/app/data
    restart: unless-stopped

volumes:
  postgres_data:
```

---

## ✅ Conclusion

**Vous pouvez déployer maintenant sans base de données !**

1. ✅ Déployez avec Docker maintenant (fichiers JSON)
2. ✅ Testez votre application
3. ✅ Ajoutez une base de données plus tard quand nécessaire
4. ✅ Migrez les données avec un script de migration

Votre application fonctionnera parfaitement avec les fichiers JSON pour commencer. La migration vers une base de données peut se faire progressivement sans interruption de service.


