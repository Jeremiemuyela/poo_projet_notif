# Guide de Test de l'API RESTful

## 🚀 Méthode 1 : Script Python (Recommandé)

### Installation
```bash
pip install -r requirements.txt
```

### Exécution
```bash
python test_api.py
```

Le script teste automatiquement tous les endpoints et affiche les résultats.

---

## 🪟 Méthode 2 : PowerShell (Windows)

PowerShell a un alias `curl` qui pointe vers `Invoke-WebRequest`. Voici comment faire :

### Option A : Utiliser Invoke-WebRequest (Syntaxe PowerShell)

```powershell
# Health check
Invoke-WebRequest -Uri "http://localhost:5000/api/health" -Method GET

# Notification météo
$body = @{
    titre = "alerte_meteo"
    message = "Tempête prévue ce soir"
    priorite = "HAUTE"
    utilisateurs = @(
        @{
            id = "etudiant1"
            nom = "Jean Dupont"
            email = "jean@univ.fr"
            langue = "fr"
            telephone = "+33123456789"
            preferences = @{
                canal_prefere = "email"
                actif = $true
            }
        }
    )
} | ConvertTo-Json -Depth 10

Invoke-WebRequest -Uri "http://localhost:5000/api/notifications/meteo" -Method POST -Body $body -ContentType "application/json"
```

### Option B : Utiliser curl.exe (Version Windows)

Si vous avez curl installé sur Windows, utilisez `curl.exe` au lieu de `curl` :

```powershell
curl.exe -X POST http://localhost:5000/api/notifications/meteo `
  -H "Content-Type: application/json" `
  -d '{\"titre\":\"alerte_meteo\",\"message\":\"Test\",\"utilisateurs\":[{\"id\":\"1\",\"nom\":\"Test\",\"email\":\"test@test.fr\"}]}'
```

---

## 🌐 Méthode 3 : Utiliser un Client HTTP (Postman, Insomnia, etc.)

### Configuration
- **URL** : `http://localhost:5000/api/notifications/meteo`
- **Method** : `POST`
- **Headers** : `Content-Type: application/json`
- **Body** (raw JSON) :
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

---

## 📝 Exemples de Requêtes PowerShell Complètes

### 1. Health Check
```powershell
Invoke-RestMethod -Uri "http://localhost:5000/api/health" -Method GET
```

### 2. Liste des Types
```powershell
Invoke-RestMethod -Uri "http://localhost:5000/api/notifications/types" -Method GET
```

### 3. Notification Météo
```powershell
$json = @'
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
'@

Invoke-RestMethod -Uri "http://localhost:5000/api/notifications/meteo" -Method POST -Body $json -ContentType "application/json"
```

### 4. Notification Sécurité
```powershell
$json = @'
{
  "titre": "alerte_securite",
  "message": "ÉVACUATION IMMÉDIATE",
  "priorite": "CRITIQUE",
  "utilisateurs": [
    {
      "id": "etudiant1",
      "nom": "Jean Dupont",
      "email": "jean@univ.fr",
      "langue": "fr",
      "telephone": "+33123456789",
      "preferences": {
        "canal_prefere": "sms",
        "actif": true
      }
    }
  ]
}
'@

Invoke-RestMethod -Uri "http://localhost:5000/api/notifications/securite" -Method POST -Body $json -ContentType "application/json"
```

---

## 🔧 Dépannage

### Erreur : "Impossible de se connecter"
- Vérifiez que le serveur Flask est démarré : `python app.py`
- Vérifiez que le port 5000 n'est pas utilisé par un autre processus

### Erreur : "curl : commande introuvable"
- Utilisez `Invoke-RestMethod` ou `Invoke-WebRequest` dans PowerShell
- Ou installez curl pour Windows et utilisez `curl.exe`

### Erreur : "400 Bad Request"
- Vérifiez que le JSON est valide
- Vérifiez que tous les champs requis sont présents
- Vérifiez le Content-Type header : `application/json`

---

## 💡 Astuce : Créer un Fichier de Test PowerShell

Créez un fichier `test.ps1` :

```powershell
# test.ps1
$baseUrl = "http://localhost:5000"

# Health check
Write-Host "Test Health Check..." -ForegroundColor Green
Invoke-RestMethod -Uri "$baseUrl/api/health" -Method GET

# Notification météo
Write-Host "`nTest Notification Météo..." -ForegroundColor Green
$json = Get-Content "exemples_requetes.json" -Raw | ConvertFrom-Json
$meteoJson = $json.exemple_meteo | ConvertTo-Json -Depth 10
Invoke-RestMethod -Uri "$baseUrl/api/notifications/meteo" -Method POST -Body $meteoJson -ContentType "application/json"
```

Puis exécutez : `.\test.ps1`

