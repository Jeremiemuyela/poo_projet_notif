"""
Module d'administration - Interface de configuration système
"""
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from typing import Dict, Any, Optional
import projetnotif as notif
from metrics import metrics_manager
from auth import (
    authenticate_user, require_auth, require_role, require_permission,
    load_users, create_user, ROLES
)
from queue_manager import queue_manager
from students import students_manager, FACULTIES

# Créer un Blueprint pour l'administration
admin_bp = Blueprint('admin', __name__, url_prefix='/admin', template_folder='templates')


# ==================== FONCTIONS UTILITAIRES ====================

def get_retry_config() -> Dict[str, Any]:
    """Récupère la configuration actuelle du retry."""
    config = notif.RetryConfig
    return {
        "attempts": config.get_option("attempts", 3),
        "delay": config.get_option("delay", 1),
        "backoff": config.get_option("backoff", 2),
        "defaults": config.defaults
    }


def get_circuit_breaker_config() -> Dict[str, Any]:
    """Récupère la configuration actuelle du circuit breaker."""
    config = notif.CircuitBreakerConfig
    return {
        "threshold": config.get_option("threshold", 3),
        "cooldown": config.get_option("cooldown", 5),
        "defaults": config.defaults
    }


def get_system_status() -> Dict[str, Any]:
    """Récupère le statut général du système."""
    registry = notif.REGISTRY
    configs = registry.get("configs", {})
    channels = registry.get("channels", {})
    templates = registry.get("templates", {})
    notificateurs = registry.get("notificateurs", [])
    
    return {
        "configs_actives": list(configs.keys()),
        "canaux_disponibles": list(channels.keys()),
        "templates_disponibles": list(templates.keys()),
        "notificateurs_enregistres": len(notificateurs),
        "types_notifications": [cls.__name__ for cls in registry.get("notification_types", [])]
    }


def format_timestamp(timestamp: Optional[float]) -> Optional[str]:
    if timestamp is None:
        return None
    return datetime.fromtimestamp(timestamp).isoformat(timespec='seconds')


def get_metrics_summary() -> Dict[str, Any]:
    summary = metrics_manager.get_summary()

    global_data = summary.get("global", {})
    global_data["last_notification_iso"] = format_timestamp(global_data.get("last_notification"))

    formatted_notifiers = {}
    for name, data in summary.get("notifiers", {}).items():
        formatted_notifiers[name] = {
            **data,
            "success_rate": (
                data["success"] / data["count"] if data.get("count") else None
            ),
            "last_timestamp_iso": format_timestamp(data.get("last_timestamp")),
        }

    return {
        "global": global_data,
        "notifiers": formatted_notifiers,
    }


# ==================== ROUTES PAGES HTML ====================

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Page de connexion."""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            return render_template('admin/login.html', error="Nom d'utilisateur et mot de passe requis")
        
        user = authenticate_user(username, password)
        if user:
            session['user'] = {
                'username': user['username'],
                'role': user['role']
            }
            return redirect(url_for('admin.index'))
        else:
            return render_template('admin/login.html', error="Nom d'utilisateur ou mot de passe incorrect")
    
    # Si déjà connecté, rediriger vers le tableau de bord
    if 'user' in session:
        return redirect(url_for('admin.index'))
    
    return render_template('admin/login.html')


@admin_bp.route('/logout')
def logout():
    """Déconnexion."""
    session.pop('user', None)
    return redirect(url_for('admin.login'))


@admin_bp.route('/')
@require_auth
def index():
    """Page d'accueil de l'interface d'administration."""
    return render_template('admin/index.html')


@admin_bp.route('/config/retry')
@require_auth
@require_role('admin', 'operator')
def config_retry_page():
    """Page de configuration du retry."""
    return render_template('admin/config_retry.html')


@admin_bp.route('/config/circuit-breaker')
@require_auth
@require_role('admin', 'operator')
def config_circuit_breaker_page():
    """Page de configuration du circuit breaker."""
    return render_template('admin/config_circuit_breaker.html')


@admin_bp.route('/status')
@require_auth
def status_page():
    """Page de statut du système."""
    return render_template('admin/status.html')


@admin_bp.route('/queue')
@require_auth
def queue_page():
    """Page de gestion des files d'attente."""
    return render_template('admin/queue.html')


@admin_bp.route('/send')
@require_auth
@require_role('admin', 'operator')
def send_notification_page():
    """Page d'envoi de notification depuis l'interface."""
    return render_template('admin/send_notification.html')


# ==================== ENDPOINTS API ====================

@admin_bp.route('/api/config/retry', methods=['GET'])
@require_auth
def get_retry_config_api():
    """API: Récupère la configuration du retry."""
    try:
        config = get_retry_config()
        return jsonify({
            "success": True,
            "config": config
        }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@admin_bp.route('/api/config/retry', methods=['POST'])
@require_auth
@require_role('admin', 'operator')
def update_retry_config_api():
    """API: Met à jour la configuration du retry."""
    try:
        if not request.is_json:
            return jsonify({
                "success": False,
                "error": "Le contenu doit être au format JSON"
            }), 400
        
        data = request.get_json()
        config = notif.RetryConfig
        
        # Validation et mise à jour
        if "attempts" in data:
            attempts = int(data["attempts"])
            if attempts < 1:
                return jsonify({
                    "success": False,
                    "error": "Le nombre de tentatives doit être >= 1"
                }), 400
            config.set_option("attempts", attempts)
        
        if "delay" in data:
            delay = float(data["delay"])
            if delay < 0:
                return jsonify({
                    "success": False,
                    "error": "Le délai doit être >= 0"
                }), 400
            config.set_option("delay", delay)
        
        if "backoff" in data:
            backoff = float(data["backoff"])
            if backoff < 1:
                return jsonify({
                    "success": False,
                    "error": "Le facteur de backoff doit être >= 1"
                }), 400
            config.set_option("backoff", backoff)
        
        return jsonify({
            "success": True,
            "message": "Configuration retry mise à jour avec succès",
            "config": get_retry_config()
        }), 200
        
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": f"Valeur invalide: {str(e)}"
        }), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@admin_bp.route('/api/config/retry/reset', methods=['POST'])
@require_auth
@require_role('admin')
def reset_retry_config_api():
    """API: Réinitialise la configuration du retry aux valeurs par défaut."""
    try:
        config = notif.RetryConfig
        
        # Réinitialiser aux valeurs par défaut
        for key, default_value in config.defaults.items():
            config.set_option(key, default_value)
        
        return jsonify({
            "success": True,
            "message": "Configuration retry réinitialisée aux valeurs par défaut",
            "config": get_retry_config()
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@admin_bp.route('/api/config/circuit-breaker', methods=['GET'])
@require_auth
def get_circuit_breaker_config_api():
    """API: Récupère la configuration du circuit breaker."""
    try:
        config = get_circuit_breaker_config()
        return jsonify({
            "success": True,
            "config": config
        }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@admin_bp.route('/api/config/circuit-breaker', methods=['POST'])
@require_auth
@require_role('admin', 'operator')
def update_circuit_breaker_config_api():
    """API: Met à jour la configuration du circuit breaker."""
    try:
        if not request.is_json:
            return jsonify({
                "success": False,
                "error": "Le contenu doit être au format JSON"
            }), 400
        
        data = request.get_json()
        config = notif.CircuitBreakerConfig
        
        # Validation et mise à jour
        if "threshold" in data:
            threshold = int(data["threshold"])
            if threshold < 1:
                return jsonify({
                    "success": False,
                    "error": "Le seuil doit être >= 1"
                }), 400
            config.set_option("threshold", threshold)
        
        if "cooldown" in data:
            cooldown = float(data["cooldown"])
            if cooldown < 0:
                return jsonify({
                    "success": False,
                    "error": "Le temps de cooldown doit être >= 0"
                }), 400
            config.set_option("cooldown", cooldown)
        
        return jsonify({
            "success": True,
            "message": "Configuration circuit breaker mise à jour avec succès",
            "config": get_circuit_breaker_config()
        }), 200
        
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": f"Valeur invalide: {str(e)}"
        }), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@admin_bp.route('/api/config/circuit-breaker/reset', methods=['POST'])
@require_auth
@require_role('admin')
def reset_circuit_breaker_config_api():
    """API: Réinitialise la configuration du circuit breaker aux valeurs par défaut."""
    try:
        config = notif.CircuitBreakerConfig
        
        # Réinitialiser aux valeurs par défaut
        for key, default_value in config.defaults.items():
            config.set_option(key, default_value)
        
        return jsonify({
            "success": True,
            "message": "Configuration circuit breaker réinitialisée aux valeurs par défaut",
            "config": get_circuit_breaker_config()
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@admin_bp.route('/api/status', methods=['GET'])
@require_auth
def get_system_status_api():
    """API: Récupère le statut général du système."""
    try:
        status = get_system_status()
        retry_config = get_retry_config()
        cb_config = get_circuit_breaker_config()
        metrics_summary = get_metrics_summary()

        return jsonify({
            "success": True,
            "status": status,
            "retry_config": retry_config,
            "circuit_breaker_config": cb_config,
            "metrics": metrics_summary
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@admin_bp.route('/api/metrics', methods=['GET'])
@require_auth
def get_metrics_api():
    """API: Récupère les métriques de performance."""
    try:
        metrics_summary = get_metrics_summary()
        return jsonify({
            "success": True,
            "metrics": metrics_summary
        }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ==================== GESTION DES UTILISATEURS ====================

@admin_bp.route('/api/users', methods=['GET'])
@require_auth
@require_role('admin')
def list_users_api():
    """API: Liste tous les utilisateurs (admin uniquement)."""
    try:
        users = load_users()
        # Ne pas exposer les mots de passe
        safe_users = {}
        for username, user in users.items():
            safe_users[username] = {
                "username": user.get("username"),
                "role": user.get("role"),
                "active": user.get("active", True),
                "has_api_key": bool(user.get("api_key"))
            }
        
        return jsonify({
            "success": True,
            "users": safe_users,
            "roles": {role: data["description"] for role, data in ROLES.items()}
        }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@admin_bp.route('/api/users', methods=['POST'])
@require_auth
@require_role('admin')
def create_user_api():
    """API: Crée un nouvel utilisateur (admin uniquement)."""
    try:
        if not request.is_json:
            return jsonify({
                "success": False,
                "error": "Le contenu doit être au format JSON"
            }), 400
        
        data = request.get_json()
        username = data.get("username")
        password = data.get("password")
        role = data.get("role", "viewer")
        
        if not username or not password:
            return jsonify({
                "success": False,
                "error": "Le nom d'utilisateur et le mot de passe sont requis"
            }), 400
        
        user = create_user(username, password, role)
        
        return jsonify({
            "success": True,
            "message": f"Utilisateur '{username}' créé avec succès",
            "user": {
                "username": user["username"],
                "role": user["role"],
                "api_key": user["api_key"]
            }
        }), 201
        
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ==================== ENDPOINTS FILES D'ATTENTE ====================

@admin_bp.route('/api/queue/tasks', methods=['GET'])
@require_auth
def list_queue_tasks_api():
    """API: Liste les tâches en file d'attente."""
    try:
        limit = request.args.get('limit', 100, type=int)
        tasks = queue_manager.get_all_tasks(limit=limit)
        return jsonify({
            "success": True,
            "tasks": tasks
        }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@admin_bp.route('/api/queue/stats', methods=['GET'])
@require_auth
def get_queue_stats_api():
    """API: Récupère les statistiques de la file d'attente."""
    try:
        stats = queue_manager.get_stats()
        return jsonify({
            "success": True,
            "stats": stats
        }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@admin_bp.route('/api/queue/clear', methods=['POST'])
@require_auth
@require_role('admin')
def clear_completed_tasks_api():
    """API: Nettoie les tâches complétées anciennes (admin uniquement)."""
    try:
        hours = request.json.get('hours', 24) if request.is_json else 24
        removed = queue_manager.clear_completed(older_than_hours=hours)
        return jsonify({
            "success": True,
            "message": f"{removed} tâches supprimées",
            "removed": removed
        }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ==================== ENVOI DE NOTIFICATIONS DEPUIS L'ADMIN ====================

@admin_bp.route('/api/send-notification', methods=['POST'])
@require_auth
@require_role('admin', 'operator')
def send_notification_from_admin():
    """API: Envoie une notification depuis l'interface admin."""
    try:
        if not request.is_json:
            return jsonify({
                "success": False,
                "error": "Le contenu doit être au format JSON"
            }), 400
        
        data = request.get_json()
        notification_type = data.get("type")
        
        if notification_type not in ["meteo", "securite", "sante", "infra"]:
            return jsonify({
                "success": False,
                "error": f"Type de notification invalide: {notification_type}"
            }), 400
        
        # Récupérer les destinataires par filtrage
        facultes = data.get("facultes", [])
        promotions = data.get("promotions", [])
        
        # Filtrer selon les facultés et promotions
        # Si aucune sélection, prendre tous les étudiants actifs
        filtered_students = students_manager.filter_students(
            facultes=facultes if facultes else None,
            promotions=promotions if promotions else None,
            actif_only=True
        )
        
        # Convertir les étudiants en format utilisateur
        # Charger le store de préférences pour récupérer les préférences de langue
        # (maintenant un singleton, donc partagé avec app.py)
        prefs_store = notif.PreferencesStore()
        
        utilisateurs_data = []
        for student in filtered_students:
            # Charger les préférences depuis PreferencesStore si elles existent
            prefs = prefs_store.obtenir(student.id)
            
            # Déterminer la langue (préférence > profil étudiant)
            langue = student.langue
            if prefs and prefs.langue:
                langue = prefs.langue.value if isinstance(prefs.langue, notif.Langue) else str(prefs.langue)
            
            # Déterminer le canal préféré (préférence > profil étudiant)
            canal_prefere = student.canal_prefere
            if prefs and prefs.canal_prefere:
                canal_prefere = prefs.canal_prefere
            
            # Déterminer le statut actif (préférence > profil étudiant)
            actif = student.actif
            if prefs is not None:
                actif = prefs.actif
            
            utilisateurs_data.append({
                "id": student.id,
                "nom": student.nom,
                "email": student.email,
                "telephone": student.telephone,
                "langue": langue,
                "preferences": {
                    "langue": langue,
                    "canal_prefere": canal_prefere,
                    "actif": actif
                }
            })
        
        if not utilisateurs_data:
            return jsonify({
                "success": False,
                "error": "Aucun destinataire trouvé avec les critères sélectionnés"
            }), 400
        
        # Mettre à jour les données avec les utilisateurs filtrés
        data["utilisateurs"] = utilisateurs_data
        
        # Ajouter à la file d'attente
        task_id = queue_manager.enqueue(notification_type, data)
        
        return jsonify({
            "success": True,
            "message": f"Notification {notification_type} mise en file d'attente pour {len(utilisateurs_data)} destinataire(s)",
            "task_id": task_id,
            "status": "pending",
            "destinataires_count": len(utilisateurs_data)
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


@admin_bp.route('/api/students/faculties', methods=['GET'])
@require_auth
def get_faculties_api():
    """API: Récupère la liste des facultés."""
    return jsonify({
        "success": True,
        "faculties": students_manager.get_faculties(),
        "faculties_details": FACULTIES
    }), 200


@admin_bp.route('/api/students/stats', methods=['GET'])
@require_auth
def get_students_stats_api():
    """API: Récupère les statistiques des étudiants."""
    stats = students_manager.get_statistics()
    return jsonify({
        "success": True,
        "stats": stats
    }), 200

