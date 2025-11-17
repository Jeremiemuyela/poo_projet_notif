"""
Script de test pour l'API RESTful de notification
Utilise la bibliothèque requests pour tester tous les endpoints
"""
import requests
import json
from typing import Dict, Any

BASE_URL = "http://localhost:5000"

# Clé API pour les tests (à obtenir depuis users.json ou créer un utilisateur)
API_KEY = None  # Sera récupérée automatiquement ou définie manuellement

def get_headers():
    """Retourne les en-têtes avec authentification si disponible."""
    headers = {"Content-Type": "application/json"}
    if API_KEY:
        headers["X-API-Key"] = API_KEY
    return headers


def print_response(response: requests.Response):
    """Affiche la réponse de manière lisible."""
    print(f"\n{'='*60}")
    print(f"Status Code: {response.status_code}")
    print(f"Response:")
    try:
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    except:
        print(response.text)
    print(f"{'='*60}\n")


def test_health_check():
    """Teste l'endpoint de health check."""
    print("🔍 Test: Health Check")
    response = requests.get(f"{BASE_URL}/api/health")
    print_response(response)


def test_list_types():
    """Teste l'endpoint de liste des types."""
    print("📋 Test: Liste des types de notifications")
    response = requests.get(f"{BASE_URL}/api/notifications/types")
    print_response(response)


def test_notification_meteo():
    """Teste l'endpoint de notification météorologique."""
    print("🌦️  Test: Notification Météo")
    
    data = {
        "titre": "alerte_meteo",
        "message": "Tempête prévue ce soir avec vents violents",
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
                    "actif": True
                }
            },
            {
                "id": "etudiant2",
                "nom": "Marie Martin",
                "email": "marie@univ.fr",
                "langue": "fr",
                "telephone": "+33698765432",
                "preferences": {
                    "canal_prefere": "sms",
                    "actif": True
                }
            }
        ]
    }
    
    response = requests.post(
        f"{BASE_URL}/api/notifications/meteo",
        json=data,
        headers=get_headers()
    )
    print_response(response)


def test_notification_securite():
    """Teste l'endpoint de notification de sécurité."""
    print("🚨 Test: Notification Sécurité")
    
    data = {
        "titre": "alerte_securite",
        "message": "ÉVACUATION IMMÉDIATE - Veuillez quitter le bâtiment",
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
                    "actif": True
                }
            },
            {
                "id": "etudiant3",
                "nom": "John Smith",
                "email": "john@univ.fr",
                "langue": "en",
                "telephone": "+447900123456",
                "preferences": {
                    "canal_prefere": "app",
                    "actif": True
                }
            }
        ]
    }
    
    response = requests.post(
        f"{BASE_URL}/api/notifications/securite",
        json=data,
        headers=get_headers()
    )
    print_response(response)


def test_notification_sante():
    """Teste l'endpoint de notification de santé."""
    print("🏥 Test: Notification Santé")
    
    data = {
        "titre": "alerte_sante",
        "message": "Campagne de vaccination disponible cette semaine. Rendez-vous sur le site web.",
        "priorite": "NORMALE",
        "utilisateurs": [
            {
                "id": "etudiant1",
                "nom": "Jean Dupont",
                "email": "jean@univ.fr",
                "langue": "fr",
                "preferences": {
                    "canal_prefere": "email",
                    "actif": True
                }
            }
        ]
    }
    
    response = requests.post(
        f"{BASE_URL}/api/notifications/sante",
        json=data,
        headers=get_headers()
    )
    print_response(response)


def test_notification_infra():
    """Teste l'endpoint de notification d'infrastructure."""
    print("🏗️  Test: Notification Infrastructure")
    
    data = {
        "titre": "alerte_infra",
        "message": "Coupure d'eau prévue demain de 8h à 12h sur le campus nord",
        "priorite": "HAUTE",
        "utilisateurs": [
            {
                "id": "etudiant2",
                "nom": "Marie Martin",
                "email": "marie@univ.fr",
                "langue": "fr",
                "telephone": "+33698765432",
                "preferences": {
                    "canal_prefere": "sms",
                    "actif": True
                }
            },
            {
                "id": "etudiant3",
                "nom": "John Smith",
                "email": "john@univ.fr",
                "langue": "en",
                "preferences": {
                    "canal_prefere": "app",
                    "actif": True
                }
            }
        ]
    }
    
    response = requests.post(
        f"{BASE_URL}/api/notifications/infra",
        json=data,
        headers=get_headers()
    )
    print_response(response)


def test_erreur_validation():
    """Teste la gestion d'erreur avec des données invalides."""
    print("❌ Test: Erreur de validation (champs manquants)")
    
    data = {
        "titre": "alerte_meteo",
        # "message" manquant intentionnellement
        "utilisateurs": []
    }
    
    response = requests.post(
        f"{BASE_URL}/api/notifications/meteo",
        json=data,
        headers=get_headers()
    )
    print_response(response)


def get_api_key_from_users():
    """Tente de récupérer la clé API depuis users.json."""
    global API_KEY
    try:
        import os
        if os.path.exists("users.json"):
            with open("users.json", 'r', encoding='utf-8') as f:
                users = json.load(f)
                # Prendre la première clé API disponible
                for username, user_data in users.items():
                    if user_data.get("api_key"):
                        API_KEY = user_data["api_key"]
                        print(f"✅ Clé API trouvée pour l'utilisateur: {username}")
                        return True
    except Exception as e:
        print(f"⚠️  Impossible de charger la clé API depuis users.json: {e}")
    return False


def main():
    """Exécute tous les tests."""
    print("=" * 60)
    print("TESTS DE L'API RESTful - Système de Notification")
    print("=" * 60)
    print("\n⚠️  Assurez-vous que le serveur Flask est démarré (python app.py)")
    
    # Essayer de récupérer la clé API
    if not get_api_key_from_users():
        print("\n⚠️  Aucune clé API trouvée.")
        print("   Les tests nécessitent une authentification.")
        print("   Vous pouvez :")
        print("   1. Créer un utilisateur via l'API admin")
        print("   2. Récupérer la clé API depuis users.json")
        print("   3. Modifier API_KEY dans ce fichier")
        api_key_input = input("\n   Entrez une clé API (ou appuyez sur Entrée pour continuer sans) : ")
        if api_key_input.strip():
            global API_KEY
            API_KEY = api_key_input.strip()
            print(f"✅ Clé API définie")
        else:
            print("⚠️  Les tests d'envoi de notifications échoueront sans clé API")
    
    print("\nAppuyez sur Entrée pour commencer les tests...")
    input()
    
    try:
        # Tests GET
        test_health_check()
        test_list_types()
        
        # Tests POST
        test_notification_meteo()
        test_notification_securite()
        test_notification_sante()
        test_notification_infra()
        
        # Test d'erreur
        test_erreur_validation()
        
        print("\n✅ Tous les tests sont terminés !")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ERREUR: Impossible de se connecter au serveur.")
        print("   Assurez-vous que le serveur Flask est démarré avec: python app.py")
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")


if __name__ == "__main__":
    main()

