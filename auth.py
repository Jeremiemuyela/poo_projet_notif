"""
Module d'authentification et d'autorisation simple
Stockage des utilisateurs dans un fichier JSON
"""
import json
import os
import secrets
import hashlib
from typing import Dict, List, Optional, Set
from functools import wraps
from flask import request, jsonify, session, redirect, url_for

# Fichier de stockage des utilisateurs
USERS_FILE = "users.json"

# Rôles disponibles
ROLES = {
    "admin": {"description": "Administrateur complet", "permissions": ["*"]},
    "operator": {"description": "Opérateur", "permissions": ["read", "send_notifications"]},
    "viewer": {"description": "Lecteur", "permissions": ["read"]}
}


def load_users() -> Dict[str, Dict]:
    """Charge les utilisateurs depuis le fichier JSON."""
    if not os.path.exists(USERS_FILE):
        return {}
    try:
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def save_users(users: Dict[str, Dict]):
    """Sauvegarde les utilisateurs dans le fichier JSON."""
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=2, ensure_ascii=False)


def hash_password(password: str) -> str:
    """Hash un mot de passe avec SHA-256 (simple, pour développement)."""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    """Vérifie un mot de passe contre son hash."""
    return hash_password(password) == hashed


def generate_api_key() -> str:
    """Génère une clé API aléatoire."""
    return secrets.token_urlsafe(32)


def create_user(username: str, password: str, role: str = "viewer", api_key: Optional[str] = None) -> Dict:
    """Crée un nouvel utilisateur."""
    if role not in ROLES:
        raise ValueError(f"Rôle invalide: {role}. Rôles disponibles: {', '.join(ROLES.keys())}")
    
    users = load_users()
    if username in users:
        raise ValueError(f"L'utilisateur '{username}' existe déjà")
    
    if api_key is None:
        api_key = generate_api_key()
    
    user = {
        "username": username,
        "password_hash": hash_password(password),
        "role": role,
        "api_key": api_key,
        "active": True
    }
    
    users[username] = user
    save_users(users)
    return user


def authenticate_user(username: str, password: str) -> Optional[Dict]:
    """Authentifie un utilisateur avec nom d'utilisateur et mot de passe."""
    users = load_users()
    user = users.get(username)
    
    if not user:
        return None
    
    if not user.get("active", True):
        return None
    
    if not verify_password(password, user.get("password_hash", "")):
        return None
    
    return user


def authenticate_api_key(api_key: str) -> Optional[Dict]:
    """Authentifie un utilisateur avec une clé API."""
    users = load_users()
    
    for username, user in users.items():
        if user.get("api_key") == api_key and user.get("active", True):
            return user
    
    return None


def get_user_permissions(role: str) -> Set[str]:
    """Récupère les permissions d'un rôle."""
    role_data = ROLES.get(role, {})
    permissions = set(role_data.get("permissions", []))
    
    # "*" signifie toutes les permissions
    if "*" in permissions:
        return {"*"}
    
    return permissions


def has_permission(user: Dict, permission: str) -> bool:
    """Vérifie si un utilisateur a une permission spécifique."""
    role = user.get("role", "viewer")
    permissions = get_user_permissions(role)
    
    return "*" in permissions or permission in permissions


# ==================== DÉCORATEURS ====================

def require_auth(f):
    """Décorateur pour exiger une authentification (session ou API key)."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Vérifier la session (pour l'interface web)
        if 'user' in session:
            return f(*args, **kwargs)
        
        # Vérifier la clé API (pour les requêtes API)
        api_key = request.headers.get('X-API-Key') or request.headers.get('Authorization', '').replace('Bearer ', '')
        if api_key:
            user = authenticate_api_key(api_key)
            if user:
                request.current_user = user
                return f(*args, **kwargs)
        
        # Pas d'authentification valide
        if request.path.startswith('/admin'):
            return redirect(url_for('admin.login'))
        else:
            return jsonify({
                "success": False,
                "error": "Authentification requise",
                "message": "Veuillez fournir une clé API valide dans l'en-tête X-API-Key ou vous connecter"
            }), 401
    
    return decorated_function


def require_role(*allowed_roles):
    """Décorateur pour exiger un rôle spécifique."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = None
            
            # Récupérer l'utilisateur depuis la session ou la requête
            if 'user' in session:
                user = session['user']
            elif hasattr(request, 'current_user'):
                user = request.current_user
            else:
                if request.path.startswith('/admin'):
                    return redirect(url_for('admin.login'))
                else:
                    return jsonify({
                        "success": False,
                        "error": "Authentification requise"
                    }), 401
            
            user_role = user.get('role', 'viewer')
            if user_role not in allowed_roles:
                return jsonify({
                    "success": False,
                    "error": "Accès refusé",
                    "message": f"Rôle requis: {', '.join(allowed_roles)}. Votre rôle: {user_role}"
                }), 403
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def require_permission(permission: str):
    """Décorateur pour exiger une permission spécifique."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = None
            
            if 'user' in session:
                user = session['user']
            elif hasattr(request, 'current_user'):
                user = request.current_user
            else:
                if request.path.startswith('/admin'):
                    return redirect(url_for('admin.login'))
                else:
                    return jsonify({
                        "success": False,
                        "error": "Authentification requise"
                    }), 401
            
            if not has_permission(user, permission):
                return jsonify({
                    "success": False,
                    "error": "Permission refusée",
                    "message": f"Permission requise: {permission}"
                }), 403
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


# ==================== INITIALISATION ====================

def init_default_users():
    """Initialise les utilisateurs par défaut si le fichier n'existe pas."""
    if os.path.exists(USERS_FILE):
        return
    
    # Créer un admin par défaut
    try:
        create_user(
            username="admin",
            password="admin123",  # À changer en production !
            role="admin"
        )
        print(f"[AUTH] Utilisateur admin créé (mot de passe: admin123)")
        print(f"[AUTH] ⚠️  Changez le mot de passe en production !")
    except Exception as e:
        print(f"[AUTH] Erreur lors de la création de l'utilisateur par défaut: {e}")

