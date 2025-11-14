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

