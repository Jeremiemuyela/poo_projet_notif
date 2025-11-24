"""
Application Flask - API RESTful pour le système de notification d'urgence
"""
import os
from flask import Flask, request, jsonify, session
from typing import Dict, List, Any, Optional
import projetnotif as notif
from admin import admin_bp
from student import student_bp
from auth import init_default_users, require_auth
from queue_manager import queue_manager
from flasgger import Swagger

# ==================== INITIALISATION FLASK ====================

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.config['JSON_AS_ASCII'] = False  # Pour supporter les caractères français

# Charger SECRET_KEY depuis les variables d'environnement ou utiliser une valeur par défaut
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Initialiser la base de données si elle n'existe pas
from db import init_db, db_exists
if not db_exists():
    print("[APP] Initialisation de la base de données...")
    init_db()

# Initialiser les utilisateurs par défaut
init_default_users()

# Enregistrer les Blueprints
app.register_blueprint(admin_bp)
app.register_blueprint(student_bp)

# Initialiser Swagger pour la documentation automatique de l'API
swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": "apispec",
            "route": "/api/apispec.json",
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/api/docs"
}

swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "API - Système de Notification d'Urgence",
        "description": "API RESTful pour la gestion des notifications d'urgence pour les étudiants",
        "version": "1.0.0",
        "contact": {
            "name": "Support API",
            "email": "support@example.com"
        }
    },
    "host": "localhost:5000",
    "basePath": "/api",
    "schemes": ["http", "https"],
    "securityDefinitions": {
        "ApiKeyAuth": {
            "type": "apiKey",
            "name": "X-API-Key",
            "in": "header",
            "description": "Clé API pour l'authentification. Obtenez votre clé API via l'interface admin."
        }
    },
    "tags": [
        {
            "name": "Health",
            "description": "Endpoints de vérification de santé"
        },
        {
            "name": "Notifications",
            "description": "Envoi et gestion des notifications d'urgence"
        },
        {
            "name": "Queue",
            "description": "Gestion de la file d'attente des notifications"
        }
    ]
}

swagger = Swagger(app, config=swagger_config, template=swagger_template)

# Schéma réutilisable pour les notifications
NOTIFICATION_SCHEMA = {
    "type": "object",
    "required": ["titre", "message", "utilisateurs"],
    "properties": {
        "titre": {
            "type": "string",
            "description": "Titre de la notification",
            "example": "Alerte"
        },
        "message": {
            "type": "string",
            "description": "Message de la notification",
            "example": "Message d'alerte"
        },
        "priorite": {
            "type": "string",
            "enum": ["CRITIQUE", "HAUTE", "NORMALE"],
            "default": "NORMALE",
            "description": "Priorité de la notification"
        },
        "utilisateurs": {
            "type": "array",
            "description": "Liste des étudiants à notifier",
            "items": {
                "type": "object",
                "required": ["id", "nom", "email"],
                "properties": {
                    "id": {"type": "string", "example": "etudiant1"},
                    "nom": {"type": "string", "example": "Jean Dupont"},
                    "email": {"type": "string", "format": "email", "example": "jean@univ.fr"},
                    "langue": {"type": "string", "enum": ["fr", "en"], "default": "fr"},
                    "telephone": {"type": "string", "example": "+33123456789"},
                    "preferences": {
                        "type": "object",
                        "properties": {
                            "canal_prefere": {"type": "string", "enum": ["email", "sms", "app"], "default": "email"},
                            "actif": {"type": "boolean", "default": True}
                        }
                    }
                }
            }
        }
    }
}

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
        
        # Charger les préférences depuis PreferencesStore en premier
        prefs_existantes = prefs_store.obtenir(user_id)
        print(f"[DEBUG] creer_utilisateurs_depuis_json - User {user_id}: préférences existantes = {prefs_existantes}")
        
        # Déterminer la langue pour les préférences (préférence existante > JSON > langue utilisateur)
        langue_pref = None
        if prefs_existantes and prefs_existantes.langue:
            langue_pref = prefs_existantes.langue
            print(f"[DEBUG] Langue depuis préférences existantes: {langue_pref.value if hasattr(langue_pref, 'value') else langue_pref}")
        elif "preferences" in user_data and "langue" in user_data["preferences"]:
            langue_pref = valider_langue(user_data["preferences"]["langue"])
            print(f"[DEBUG] Langue depuis JSON: {langue_pref.value if hasattr(langue_pref, 'value') else langue_pref}")
        else:
            langue_pref = langue
            print(f"[DEBUG] Langue depuis utilisateur: {langue_pref.value if hasattr(langue_pref, 'value') else langue_pref}")
        
        # Déterminer le canal préféré (préférence existante > JSON > défaut)
        canal_prefere = "email"
        if prefs_existantes and prefs_existantes.canal_prefere:
            canal_prefere = prefs_existantes.canal_prefere
        elif "preferences" in user_data and "canal_prefere" in user_data["preferences"]:
            canal_prefere = user_data["preferences"]["canal_prefere"]
        
        # Déterminer le statut actif (préférence existante > JSON > défaut)
        actif = True
        if prefs_existantes is not None:
            actif = prefs_existantes.actif
        elif "preferences" in user_data and "actif" in user_data["preferences"]:
            actif = user_data["preferences"]["actif"]
        
        # Créer ou mettre à jour les préférences avec la langue
        prefs = notif.Preferences(
            langue=langue_pref,
            canal_prefere=canal_prefere,
            actif=actif
        )
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


# ==================== PROCESSOR POUR LES FILES D'ATTENTE ====================

def process_notification_task(task_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Traite une tâche de notification.
    Cette fonction est appelée par les workers de la file d'attente.
    """
    try:
        # Créer les objets depuis les données
        type_mapping = {
            "meteo": notif.TypeUrgence.METEO,
            "securite": notif.TypeUrgence.SECURITE,
            "sante": notif.TypeUrgence.SANTE,
            "infra": notif.TypeUrgence.INFRA
        }
        
        type_urgence = type_mapping.get(task_type)
        if not type_urgence:
            raise ValueError(f"Type de notification inconnu: {task_type}")
        
        urgence = creer_urgence_depuis_json(type_urgence, data)
        utilisateurs = creer_utilisateurs_depuis_json(data["utilisateurs"])
        
        # Envoyer la notification
        notificateur = notificateurs[task_type]
        notificateur.envoyer(urgence, utilisateurs)
        
        return {
            "success": True,
            "type": task_type,
            "utilisateurs_notifies": len(utilisateurs)
        }
    except Exception as e:
        raise Exception(f"Erreur lors du traitement: {str(e)}")


# Configurer et démarrer le gestionnaire de files d'attente
queue_manager.set_processor(process_notification_task)
queue_manager.start()


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


# ==================== ROUTE RACINE ====================

@app.route('/', methods=['GET'])
def index():
    """Page d'accueil avec informations sur l'API et liens vers les interfaces."""
    return jsonify({
        "success": True,
        "service": "Système de notification d'urgence",
        "version": "1.0.0",
        "description": "API RESTful pour la gestion des notifications d'urgence",
        "endpoints": {
            "health": "/api/health",
            "types": "/api/notifications/types",
            "meteo": "/api/notifications/meteo",
            "securite": "/api/notifications/securite",
            "sante": "/api/notifications/sante",
            "infra": "/api/notifications/infra"
        },
        "interfaces": {
            "admin": "/admin/",
            "student": "/student/"
        },
        "documentation": {
            "swagger_ui": "/api/docs",
            "api_spec": "/api/apispec.json",
            "description": "Documentation interactive Swagger/OpenAPI disponible à /api/docs"
        }
    }), 200


# ==================== ENDPOINTS API RESTful ====================

@app.route('/api/health', methods=['GET'])
def health_check():
    """
    Vérification de santé de l'API
    ---
    tags:
      - Health
    summary: Vérifie que l'API est opérationnelle
    description: Retourne le statut de santé de l'API et sa version
    responses:
      200:
        description: API opérationnelle
        schema:
          type: object
          properties:
            status:
              type: string
              example: healthy
            service:
              type: string
              example: Système de notification d'urgence
            version:
              type: string
              example: 1.0.0
    """
    return jsonify({
        "status": "healthy",
        "service": "Système de notification d'urgence",
        "version": "1.0.0"
    }), 200


@app.route('/api/notifications/meteo', methods=['POST'])
def envoyer_notification_meteo():
    """
    Envoyer une notification météorologique
    ---
    tags:
      - Notifications
    summary: Envoie une notification météorologique aux étudiants
    description: |
      Envoie une notification météorologique avec calcul automatique des zones à risque.
      La notification est mise en file d'attente pour traitement asynchrone.
      Les notifications sont automatiquement traduites selon les préférences de langue de chaque étudiant.
    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - in: body
        name: body
        description: Données de la notification météorologique
        required: true
        schema:
          type: object
          required:
            - titre
            - message
            - utilisateurs
          properties:
            titre:
              type: string
              description: Titre de la notification
              example: "Alerte météorologique"
            message:
              type: string
              description: Message de la notification
              example: "Tempête prévue ce soir, vents forts attendus"
            priorite:
              type: string
              enum: [CRITIQUE, HAUTE, NORMALE]
              default: NORMALE
              description: Priorité de la notification
            utilisateurs:
              type: array
              description: Liste des étudiants à notifier
              items:
                type: object
                required:
                  - id
                  - nom
                  - email
                properties:
                  id:
                    type: string
                    example: "etudiant1"
                  nom:
                    type: string
                    example: "Jean Dupont"
                  email:
                    type: string
                    format: email
                    example: "jean@univ.fr"
                  langue:
                    type: string
                    enum: [fr, en]
                    default: fr
                    description: Langue préférée de l'étudiant
                  telephone:
                    type: string
                    example: "+33123456789"
                    description: Numéro de téléphone (optionnel)
                  preferences:
                    type: object
                    properties:
                      canal_prefere:
                        type: string
                        enum: [email, sms, app]
                        default: email
                      actif:
                        type: boolean
                        default: true
    responses:
      202:
        description: Notification mise en file d'attente avec succès
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "Notification météorologique mise en file d'attente"
            type:
              type: string
              example: "meteo"
            task_id:
              type: string
              example: "task_123456"
            status:
              type: string
              example: "pending"
      400:
        description: Erreur de validation des données
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "Le champ 'utilisateurs' (liste) est requis"
      500:
        description: Erreur serveur
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "Erreur lors de l'envoi de la notification"
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
        
        # Ajouter à la file d'attente pour traitement asynchrone
        task_id = queue_manager.enqueue("meteo", data)
        
        return jsonify({
            "success": True,
            "message": "Notification météorologique mise en file d'attente",
            "type": "meteo",
            "task_id": task_id,
            "status": "pending"
        }), 202  # 202 Accepted pour traitement asynchrone
        
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
@require_auth
def envoyer_notification_securite():
    """
    Envoyer une notification de sécurité
    ---
    tags:
      - Notifications
    summary: Envoie une notification de sécurité (authentification requise)
    description: |
      Envoie une notification de sécurité avec gestion des urgences critiques.
      **Authentification requise** : Ajoutez l'en-tête `X-API-Key: VOTRE_CLE_API`
    security:
      - ApiKeyAuth: []
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - titre
            - message
            - utilisateurs
          properties:
            titre:
              type: string
              example: "Alerte sécurité"
            message:
              type: string
              example: "ÉVACUATION IMMÉDIATE"
            priorite:
              type: string
              enum: [CRITIQUE, HAUTE, NORMALE]
              default: CRITIQUE
            utilisateurs:
              type: array
              items:
                type: object
                required: [id, nom, email]
                properties:
                  id: {type: string, example: "etudiant1"}
                  nom: {type: string, example: "Jean Dupont"}
                  email: {type: string, format: email, example: "jean@univ.fr"}
                  langue: {type: string, enum: [fr, en], default: fr}
                  telephone: {type: string, example: "+33123456789"}
                  preferences:
                    type: object
                    properties:
                      canal_prefere: {type: string, enum: [email, sms, app], default: email}
                      actif: {type: boolean, default: true}
    responses:
      202:
        description: Notification mise en file d'attente
        schema:
          type: object
          properties:
            success: {type: boolean, example: true}
            message: {type: string, example: "Notification de sécurité mise en file d'attente"}
            type: {type: string, example: "securite"}
            task_id: {type: string, example: "task_123456"}
            status: {type: string, example: "pending"}
      400:
        description: Erreur de validation
      401:
        description: Authentification requise
      500:
        description: Erreur serveur
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
        
        # Ajouter à la file d'attente pour traitement asynchrone
        task_id = queue_manager.enqueue("securite", data)
        
        return jsonify({
            "success": True,
            "message": "Notification de sécurité mise en file d'attente",
            "type": "securite",
            "task_id": task_id,
            "status": "pending"
        }), 202
        
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
@require_auth
def envoyer_notification_sante():
    """
    Envoyer une notification de santé
    ---
    tags:
      - Notifications
    summary: Envoie une notification de santé (authentification requise)
    description: |
      Envoie une notification de santé avec confirmation requise.
      **Authentification requise** : Ajoutez l'en-tête `X-API-Key: VOTRE_CLE_API`
    security:
      - ApiKeyAuth: []
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [titre, message, utilisateurs]
          properties:
            titre: {type: string, example: "Alerte santé"}
            message: {type: string, example: "Campagne de vaccination disponible"}
            priorite: {type: string, enum: [CRITIQUE, HAUTE, NORMALE], default: NORMALE}
            utilisateurs:
              type: array
              items:
                type: object
                required: [id, nom, email]
                properties:
                  id: {type: string, example: "etudiant1"}
                  nom: {type: string, example: "Jean Dupont"}
                  email: {type: string, format: email, example: "jean@univ.fr"}
                  langue: {type: string, enum: [fr, en], default: fr}
                  telephone: {type: string, example: "+33123456789"}
                  preferences:
                    type: object
                    properties:
                      canal_prefere: {type: string, enum: [email, sms, app], default: email}
                      actif: {type: boolean, default: true}
    responses:
      202:
        description: Notification mise en file d'attente
        schema:
          type: object
          properties:
            success: {type: boolean, example: true}
            message: {type: string, example: "Notification de santé mise en file d'attente"}
            type: {type: string, example: "sante"}
            task_id: {type: string, example: "task_123456"}
            status: {type: string, example: "pending"}
      400:
        description: Erreur de validation
      401:
        description: Authentification requise
      500:
        description: Erreur serveur
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
        
        # Ajouter à la file d'attente pour traitement asynchrone
        task_id = queue_manager.enqueue("sante", data)
        
        return jsonify({
            "success": True,
            "message": "Notification de santé mise en file d'attente",
            "type": "sante",
            "task_id": task_id,
            "status": "pending"
        }), 202
        
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
@require_auth
def envoyer_notification_infra():
    """
    Envoyer une notification d'infrastructure
    ---
    tags:
      - Notifications
    summary: Envoie une notification d'infrastructure (authentification requise)
    description: |
      Envoie une notification concernant l'infrastructure (coupures, maintenance, etc.).
      **Authentification requise** : Ajoutez l'en-tête `X-API-Key: VOTRE_CLE_API`
    security:
      - ApiKeyAuth: []
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [titre, message, utilisateurs]
          properties:
            titre: {type: string, example: "Alerte infrastructure"}
            message: {type: string, example: "Coupure d'eau prévue demain"}
            priorite: {type: string, enum: [CRITIQUE, HAUTE, NORMALE], default: NORMALE}
            utilisateurs:
              type: array
              items:
                type: object
                required: [id, nom, email]
                properties:
                  id: {type: string, example: "etudiant1"}
                  nom: {type: string, example: "Jean Dupont"}
                  email: {type: string, format: email, example: "jean@univ.fr"}
                  langue: {type: string, enum: [fr, en], default: fr}
                  telephone: {type: string, example: "+33123456789"}
                  preferences:
                    type: object
                    properties:
                      canal_prefere: {type: string, enum: [email, sms, app], default: email}
                      actif: {type: boolean, default: true}
    responses:
      202:
        description: Notification mise en file d'attente
        schema:
          type: object
          properties:
            success: {type: boolean, example: true}
            message: {type: string, example: "Notification d'infrastructure mise en file d'attente"}
            type: {type: string, example: "infra"}
            task_id: {type: string, example: "task_123456"}
            status: {type: string, example: "pending"}
      400:
        description: Erreur de validation
      401:
        description: Authentification requise
      500:
        description: Erreur serveur
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
        
        # Ajouter à la file d'attente pour traitement asynchrone
        task_id = queue_manager.enqueue("infra", data)
        
        return jsonify({
            "success": True,
            "message": "Notification d'infrastructure mise en file d'attente",
            "type": "infra",
            "task_id": task_id,
            "status": "pending"
        }), 202
        
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


@app.route('/api/queue/tasks/<task_id>', methods=['GET'])
@require_auth
def get_task_status(task_id: str):
    """
    Récupérer le statut d'une tâche
    ---
    tags:
      - Queue
    summary: Récupère le statut d'une tâche de notification (authentification requise)
    security:
      - ApiKeyAuth: []
    parameters:
      - name: task_id
        in: path
        type: string
        required: true
        description: ID de la tâche
        example: "task_123456"
    responses:
      200:
        description: Statut de la tâche
        schema:
          type: object
          properties:
            success: {type: boolean, example: true}
            task:
              type: object
              properties:
                id: {type: string, example: "task_123456"}
                type: {type: string, example: "meteo"}
                status: {type: string, example: "completed"}
                created_at: {type: string, example: "2025-11-20T10:00:00"}
      401:
        description: Authentification requise
      404:
        description: Tâche non trouvée
    """
    task = queue_manager.get_task(task_id)
    if not task:
        return jsonify({
            "success": False,
            "error": "Tâche non trouvée"
        }), 404
    
    return jsonify({
        "success": True,
        "task": task.to_dict()
    }), 200


@app.route('/api/queue/stats', methods=['GET'])
@require_auth
def get_queue_stats():
    """
    Récupérer les statistiques de la file d'attente
    ---
    tags:
      - Queue
    summary: Récupère les statistiques de la file d'attente (authentification requise)
    security:
      - ApiKeyAuth: []
    responses:
      200:
        description: Statistiques de la file d'attente
        schema:
          type: object
          properties:
            success: {type: boolean, example: true}
            stats:
              type: object
              properties:
                total: {type: integer, example: 10}
                pending: {type: integer, example: 2}
                completed: {type: integer, example: 7}
                failed: {type: integer, example: 1}
      401:
        description: Authentification requise
    """
    stats = queue_manager.get_stats()
    return jsonify({
        "success": True,
        "stats": stats
    }), 200


@app.route('/api/notifications/types', methods=['GET'])
def lister_types_notifications():
    """
    Lister les types de notifications disponibles
    ---
    tags:
      - Notifications
    summary: Liste tous les types de notifications disponibles
    description: Retourne la liste de tous les types de notifications avec leurs endpoints et descriptions
    produces:
      - application/json
    responses:
      200:
        description: Liste des types de notifications
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            types:
              type: array
              items:
                type: object
                properties:
                  type:
                    type: string
                    example: "meteo"
                  endpoint:
                    type: string
                    example: "/api/notifications/meteo"
                  description:
                    type: string
                    example: "Notifications météorologiques avec calcul de zones à risque"
    """
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
    # En développement, utiliser le serveur Flask intégré
    # En production, utiliser gunicorn (voir Procfile)
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') != 'production'
    app.run(debug=debug, host='0.0.0.0', port=port)

