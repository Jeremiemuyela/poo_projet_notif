# 🎨 Guide : Logo et Couleur de l'Application

## 📋 Modifications Effectuées

### ✅ Couleur Dominante Changée

**Ancienne couleur** : Violet/Bleu (`#667eea` / `#764ba2`)  
**Nouvelle couleur** : Bleu Université (`#0088cc` / `#006699`)

**Couleur principale** : `#0088cc` (R:0, G:136, B:204)  
**Couleur foncée** : `#006699` (pour dégradés et effets hover)

### ✅ Logo Intégré

Le logo de l'Université Nouveaux Horizons est maintenant intégré dans :
- ✅ Interface Admin (menu latéral)
- ✅ Interface Admin (page de connexion)
- ✅ Interface Étudiant (navbar)
- ✅ Interface Étudiant (page de connexion)

---

## 📁 Ajouter le Logo

### Étape 1 : Placer le Fichier Logo

Placez votre logo dans le dossier :
```
static/images/logo-unh.png
```

**Formats acceptés** :
- PNG (recommandé, avec fond transparent)
- JPG
- SVG

**Nom du fichier** : `logo-unh.png` ou `logo-unh.jpg`

### Étape 2 : Vérifier le Logo

Une fois le logo placé, vérifiez qu'il s'affiche :
- Interface Admin : `http://localhost:5000/admin/`
- Interface Étudiant : `http://localhost:5000/student/`

**Note** : Si le logo n'est pas trouvé, une icône par défaut s'affichera automatiquement.

---

## 🎨 Où la Nouvelle Couleur Apparaît

### Interface Admin
- ✅ Sidebar (menu latéral) - dégradé bleu
- ✅ En-têtes de cartes (card-header)
- ✅ Boutons primaires
- ✅ Page de connexion
- ✅ Focus des champs de formulaire
- ✅ Valeurs des statistiques

### Interface Étudiant
- ✅ Navbar (barre de navigation)
- ✅ En-têtes de cartes
- ✅ Boutons primaires
- ✅ Page de connexion
- ✅ Fond de page (dégradé)

---

## 🔧 Personnalisation Supplémentaire

### Modifier la Couleur

Si vous souhaitez ajuster la couleur, modifiez dans les fichiers :

**`templates/admin/base.html`** et **`templates/student/base.html`** :
```css
:root {
    --primary-color: #0088cc;      /* Couleur principale */
    --primary-dark: #006699;       /* Couleur foncée */
    --primary-light: #00aaff;      /* Couleur claire (optionnel) */
}
```

### Modifier la Taille du Logo

Dans les templates, ajustez :
```css
.logo-container img {
    max-width: 150px;  /* Ajustez selon vos besoins */
    max-height: 150px;
}
```

---

## 📝 Fichiers Modifiés

1. ✅ `app.py` - Configuration static folder
2. ✅ `templates/admin/base.html` - Couleurs et logo
3. ✅ `templates/admin/index.html` - Couleurs
4. ✅ `templates/admin/login.html` - Couleurs et logo
5. ✅ `templates/student/base.html` - Couleurs et logo
6. ✅ `templates/student/login.html` - Couleurs et logo
7. ✅ `templates/student/dashboard.html` - Couleurs
8. ✅ `static/images/README.md` - Guide du logo

---

## 🚀 Déploiement

### En Local
Les modifications sont déjà actives après redémarrage du conteneur Docker.

### En Production
1. Placez le logo dans `static/images/logo-unh.png`
2. Poussez les modifications sur GitHub
3. Railway/Render déploiera automatiquement

---

## ✅ Checklist

- [x] Couleur changée vers #0088cc
- [x] Logo intégré dans templates admin
- [x] Logo intégré dans templates student
- [x] Dossier static/images créé
- [ ] Logo placé dans static/images/logo-unh.png (à faire par vous)
- [ ] Test local effectué
- [ ] Déploiement en production

---

## 🎯 Résultat Attendu

Après avoir placé le logo, vous devriez voir :
- Logo UNH dans le menu latéral admin
- Logo UNH dans la navbar étudiant
- Logo UNH sur les pages de connexion
- Toutes les couleurs en bleu #0088cc au lieu de violet

