"""
Application Flask - API RESTful pour le système de notification d'urgence
"""
from flask import Flask, request, jsonify
from typing import Dict, List, Any, Optional
import projetnotif as notif
from admin import admin_bp

# ==================== INITIALISATION FLASK ====================

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False  # Pour supporter les caractères français

# Enregistrer le Blueprint d'administration
app.register_blueprint(admin_bp)

# ==================== INITIALISATION DES SERVICES ====================

# Créer le store de préférences (singleton)
prefs_store = notif.PreferencesStore()

# Créer les canaux de notification
canaux = {
    "email": notif.Email(),
    "sms": notif.SMS(),
    "app": notif.App(),
}

# Créer les instances de notificateurs (une par type)
notificateurs = {
    "meteo": notif.NotificationMeteorologique(canaux, prefs_store),
    "securite": notif.NotificationSecurite(canaux, prefs_store),
    "sante": notif.NotificationSante(canaux, prefs_store),
    "infra": notif.NotificationInfra(canaux, prefs_store),
}


# ==================== VALIDATION ET UTILITAIRES ====================

def valider_priorite(priorite_str: str) -> notif.Priorite:
    """Convertit une chaîne de priorité en énumération Priorite."""
    mapping = {
        "CRITIQUE": notif.Priorite.CRITIQUE,
        "critique": notif.Priorite.CRITIQUE,
        "1": notif.Priorite.CRITIQUE,
        "HAUTE": notif.Priorite.HAUTE,
        "haute": notif.Priorite.HAUTE,
        "2": notif.Priorite.HAUTE,
        "NORMALE": notif.Priorite.NORMALE,
        "normale": notif.Priorite.NORMALE,
        "3": notif.Priorite.NORMALE,
    }
    if priorite_str in mapping:
        return mapping[priorite_str]
    raise ValueError(f"Priorité invalide: {priorite_str}. Valeurs acceptées: CRITIQUE, HAUTE, NORMALE")


def valider_langue(langue_str: str) -> notif.Langue:
    """Convertit une chaîne de langue en énumération Langue."""
    mapping = {
        "fr": notif.Langue.FR,
        "FR": notif.Langue.FR,
        "en": notif.Langue.EN,
        "EN": notif.Langue.EN,
    }
    if langue_str in mapping:
        return mapping[langue_str]
    raise ValueError(f"Langue invalide: {langue_str}. Valeurs acceptées: fr, en")


def creer_utilisateurs_depuis_json(users_data: List[Dict[str, Any]]) -> List[notif.Utilisateur]:
    """Crée une liste d'objets Utilisateur à partir de données JSON."""
    utilisateurs = []
    for user_data in users_data:
        # Validation des champs requis
        if "id" not in user_data or "nom" not in user_data or "email" not in user_data:
            raise ValueError("Chaque utilisateur doit avoir: id, nom, email")
        
        # Récupération des champs
        user_id = user_data["id"]
        nom = user_data["nom"]
        email = user_data["email"]
        
        # Langue (optionnel, défaut: FR)
        langue_str = user_data.get("langue", "fr")
        langue = valider_langue(langue_str)
        
        # Téléphone (optionnel)
        telephone = user_data.get("telephone", None)
        
        # Créer l'utilisateur
        utilisateur = notif.Utilisateur(
            id=user_id,
            nom=nom,
            email=email,
            langue=langue,
            telephone=telephone
        )
        utilisateurs.append(utilisateur)
        
        # Sauvegarder les préférences si fournies
        if "preferences" in user_data:
            prefs_data = user_data["preferences"]
            canal_prefere = prefs_data.get("canal_prefere", "email")
            actif = prefs_data.get("actif", True)
            prefs = notif.Preferences(canal_prefere=canal_prefere, actif=actif)
            prefs_store.sauvegarder(user_id, prefs)
    
    return utilisateurs


def creer_urgence_depuis_json(type_urgence: notif.TypeUrgence, data: Dict[str, Any]) -> notif.Urgence:
    """Crée un objet Urgence à partir de données JSON."""
    # Validation des champs requis
    if "titre" not in data:
        raise ValueError("Le champ 'titre' est requis")
    if "message" not in data:
        raise ValueError("Le champ 'message' est requis")
    
    titre = data["titre"]
    message = data["message"]
    
    # Priorité (optionnel, défaut: NORMALE)
    priorite_str = data.get("priorite", "NORMALE")
    priorite = valider_priorite(priorite_str)
    
    return notif.Urgence(
        type=type_urgence,
        titre=titre,
        message=message,
        priorite=priorite
    )


# ==================== GESTION DES ERREURS ====================

@app.errorhandler(400)
def bad_request(error):
    """Gère les erreurs 400 (Bad Request)."""
    return jsonify({
        "success": False,
        "error": "Requête invalide",
        "message": str(error.description) if hasattr(error, 'description') else str(error)
    }), 400


@app.errorhandler(404)
def not_found(error):
    """Gère les erreurs 404 (Not Found)."""
    return jsonify({
        "success": False,
        "error": "Endpoint non trouvé",
        "message": str(error.description) if hasattr(error, 'description') else str(error)
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Gère les erreurs 500 (Internal Server Error)."""
    return jsonify({
        "success": False,
        "error": "Erreur interne du serveur",
        "message": str(error)
    }), 500


# ==================== ENDPOINTS API RESTful ====================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Endpoint de vérification de santé de l'API."""
    return jsonify({
        "status": "healthy",
        "service": "Système de notification d'urgence",
        "version": "1.0.0"
    }), 200


@app.route('/api/notifications/meteo', methods=['POST'])
def envoyer_notification_meteo():
    """
    Endpoint pour envoyer une notification météorologique.
    
    Body JSON attendu:
    {
        "titre": "alerte_meteo",
        "message": "Tempête prévue ce soir",
        "priorite": "HAUTE",  // optionnel: CRITIQUE, HAUTE, NORMALE (défaut: NORMALE)
        "utilisateurs": [
            {
                "id": "etudiant1",
                "nom": "Jean Dupont",
                "email": "jean@univ.fr",
                "langue": "fr",  // optionnel: fr, en (défaut: fr)
                "telephone": "+33123456789",  // optionnel
                "preferences": {  // optionnel
                    "canal_prefere": "email",  // email, sms, app
                    "actif": true
                }
            }
        ]
    }
    """
    try:
        # Vérifier que la requête contient du JSON
        if not request.is_json:
            return jsonify({
                "success": False,
                "error": "Le contenu doit être au format JSON"
            }), 400
        
        data = request.get_json()
        
        # Validation des données
        if "utilisateurs" not in data or not isinstance(data["utilisateurs"], list):
            return jsonify({
                "success": False,
                "error": "Le champ 'utilisateurs' (liste) est requis"
            }), 400
        
        if not data["utilisateurs"]:
            return jsonify({
                "success": False,
                "error": "Au moins un utilisateur doit être fourni"
            }), 400
        
        # Créer les objets depuis JSON
        urgence = creer_urgence_depuis_json(notif.TypeUrgence.METEO, data)
        utilisateurs = creer_utilisateurs_depuis_json(data["utilisateurs"])
        
        # Envoyer la notification
        notificateur = notificateurs["meteo"]
        notificateur.envoyer(urgence, utilisateurs)
        
        return jsonify({
            "success": True,
            "message": "Notification météorologique envoyée avec succès",
            "type": "meteo",
            "utilisateurs_notifies": len(utilisateurs)
        }), 200
        
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": "Erreur de validation",
            "message": str(e)
        }), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "error": "Erreur lors de l'envoi de la notification",
            "message": str(e)
        }), 500


@app.route('/api/notifications/securite', methods=['POST'])
def envoyer_notification_securite():
    """
    Endpoint pour envoyer une notification de sécurité.
    
    Body JSON attendu:
    {
        "titre": "alerte_securite",
        "message": "ÉVACUATION IMMÉDIATE",
        "priorite": "CRITIQUE",  // requis pour sécurité
        "utilisateurs": [...]
    }
    """
    try:
        if not request.is_json:
            return jsonify({
                "success": False,
                "error": "Le contenu doit être au format JSON"
            }), 400
        
        data = request.get_json()
        
        if "utilisateurs" not in data or not isinstance(data["utilisateurs"], list):
            return jsonify({
                "success": False,
                "error": "Le champ 'utilisateurs' (liste) est requis"
            }), 400
        
        if not data["utilisateurs"]:
            return jsonify({
                "success": False,
                "error": "Au moins un utilisateur doit être fourni"
            }), 400
        
        urgence = creer_urgence_depuis_json(notif.TypeUrgence.SECURITE, data)
        utilisateurs = creer_utilisateurs_depuis_json(data["utilisateurs"])
        
        notificateur = notificateurs["securite"]
        notificateur.envoyer(urgence, utilisateurs)
        
        return jsonify({
            "success": True,
            "message": "Notification de sécurité envoyée avec succès",
            "type": "securite",
            "priorite": urgence.priorite.name,
            "utilisateurs_notifies": len(utilisateurs)
        }), 200
        
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": "Erreur de validation",
            "message": str(e)
        }), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "error": "Erreur lors de l'envoi de la notification",
            "message": str(e)
        }), 500


@app.route('/api/notifications/sante', methods=['POST'])
def envoyer_notification_sante():
    """
    Endpoint pour envoyer une notification de santé.
    
    Body JSON attendu:
    {
        "titre": "alerte_sante",
        "message": "Campagne de vaccination disponible",
        "priorite": "NORMALE",  // optionnel
        "utilisateurs": [...]
    }
    """
    try:
        if not request.is_json:
            return jsonify({
                "success": False,
                "error": "Le contenu doit être au format JSON"
            }), 400
        
        data = request.get_json()
        
        if "utilisateurs" not in data or not isinstance(data["utilisateurs"], list):
            return jsonify({
                "success": False,
                "error": "Le champ 'utilisateurs' (liste) est requis"
            }), 400
        
        if not data["utilisateurs"]:
            return jsonify({
                "success": False,
                "error": "Au moins un utilisateur doit être fourni"
            }), 400
        
        urgence = creer_urgence_depuis_json(notif.TypeUrgence.SANTE, data)
        utilisateurs = creer_utilisateurs_depuis_json(data["utilisateurs"])
        
        notificateur = notificateurs["sante"]
        notificateur.envoyer(urgence, utilisateurs)
        
        return jsonify({
            "success": True,
            "message": "Notification de santé envoyée avec succès",
            "type": "sante",
            "utilisateurs_notifies": len(utilisateurs)
        }), 200
        
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": "Erreur de validation",
            "message": str(e)
        }), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "error": "Erreur lors de l'envoi de la notification",
            "message": str(e)
        }), 500


@app.route('/api/notifications/infra', methods=['POST'])
def envoyer_notification_infra():
    """
    Endpoint pour envoyer une notification d'infrastructure.
    
    Body JSON attendu:
    {
        "titre": "alerte_infra",
        "message": "Coupure d'eau prévue demain",
        "priorite": "HAUTE",  // optionnel
        "utilisateurs": [...]
    }
    """
    try:
        if not request.is_json:
            return jsonify({
                "success": False,
                "error": "Le contenu doit être au format JSON"
            }), 400
        
        data = request.get_json()
        
        if "utilisateurs" not in data or not isinstance(data["utilisateurs"], list):
            return jsonify({
                "success": False,
                "error": "Le champ 'utilisateurs' (liste) est requis"
            }), 400
        
        if not data["utilisateurs"]:
            return jsonify({
                "success": False,
                "error": "Au moins un utilisateur doit être fourni"
            }), 400
        
        urgence = creer_urgence_depuis_json(notif.TypeUrgence.INFRA, data)
        utilisateurs = creer_utilisateurs_depuis_json(data["utilisateurs"])
        
        notificateur = notificateurs["infra"]
        notificateur.envoyer(urgence, utilisateurs)
        
        return jsonify({
            "success": True,
            "message": "Notification d'infrastructure envoyée avec succès",
            "type": "infra",
            "utilisateurs_notifies": len(utilisateurs)
        }), 200
        
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": "Erreur de validation",
            "message": str(e)
        }), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "error": "Erreur lors de l'envoi de la notification",
            "message": str(e)
        }), 500


@app.route('/api/notifications/types', methods=['GET'])
def lister_types_notifications():
    """Liste tous les types de notifications disponibles."""
    return jsonify({
        "success": True,
        "types": [
            {
                "type": "meteo",
                "endpoint": "/api/notifications/meteo",
                "description": "Notifications météorologiques avec calcul de zones à risque"
            },
            {
                "type": "securite",
                "endpoint": "/api/notifications/securite",
                "description": "Notifications de sécurité avec gestion des urgences critiques"
            },
            {
                "type": "sante",
                "endpoint": "/api/notifications/sante",
                "description": "Notifications de santé avec confirmation requise"
            },
            {
                "type": "infra",
                "endpoint": "/api/notifications/infra",
                "description": "Notifications d'infrastructure"
            }
        ]
    }), 200


# ==================== POINT D'ENTRÉE ====================

if __name__ == '__main__':
    print("=" * 60)
    print("API RESTful - Système de Notification d'Urgence")
    print("=" * 60)
    print("\nEndpoints API disponibles:")
    print("  GET  /api/health                    - Vérification de santé")
    print("  GET  /api/notifications/types       - Liste des types de notifications")
    print("  POST /api/notifications/meteo       - Envoyer notification météo")
    print("  POST /api/notifications/securite    - Envoyer notification sécurité")
    print("  POST /api/notifications/sante       - Envoyer notification santé")
    print("  POST /api/notifications/infra       - Envoyer notification infrastructure")
    print("\nInterface d'administration:")
    print("  GET  /admin/                        - Tableau de bord")
    print("  GET  /admin/config/retry            - Configuration Retry")
    print("  GET  /admin/config/circuit-breaker  - Configuration Circuit Breaker")
    print("  GET  /admin/status                  - Statut du système")
    print("\nDémarrage du serveur Flask...")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)

