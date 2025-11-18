"""
Interface étudiante - Gestion des préférences personnelles
"""
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from typing import Dict, Any, Optional
from students import students_manager
from notifications_log import notifications_logger
from translation_service import translation_service
import projetnotif as notif

# Créer un Blueprint pour l'interface étudiante
student_bp = Blueprint('student', __name__, url_prefix='/student', template_folder='templates')


def require_student_auth(f):
    """Décorateur pour vérifier qu'un étudiant est authentifié."""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'student_id' not in session:
            return redirect(url_for('student.login'))
        return f(*args, **kwargs)
    return decorated_function


# ==================== ROUTES PAGES HTML ====================

@student_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Page de connexion pour les étudiants."""
    if request.method == 'POST':
        student_id = request.form.get('student_id')
        
        if not student_id:
            return render_template('student/login.html', error="ID étudiant requis")
        
        # Vérifier que l'étudiant existe
        student = students_manager.get_student(student_id)
        if not student:
            return render_template('student/login.html', error="ID étudiant non trouvé")
        
        if not student.actif:
            return render_template('student/login.html', error="Compte étudiant désactivé")
        
        # Créer la session
        session['student_id'] = student.id
        session['student_nom'] = student.nom
        session['student_email'] = student.email
        
        return redirect(url_for('student.dashboard'))
    
    # Si déjà connecté, rediriger vers le dashboard
    if 'student_id' in session:
        return redirect(url_for('student.dashboard'))
    
    return render_template('student/login.html')


@student_bp.route('/logout')
def logout():
    """Déconnexion de l'étudiant."""
    session.clear()
    return redirect(url_for('student.login'))


@student_bp.route('/')
@require_student_auth
def dashboard():
    """Tableau de bord étudiant."""
    return render_template('student/dashboard.html')


@student_bp.route('/preferences')
@require_student_auth
def preferences():
    """Page de gestion des préférences."""
    return render_template('student/preferences.html')


@student_bp.route('/profile')
@require_student_auth
def profile():
    """Page de gestion du profil."""
    return render_template('student/profile.html')


@student_bp.route('/notifications')
@require_student_auth
def notifications():
    """Page des notifications de l'étudiant."""
    return render_template('student/notifications.html')


# ==================== ENDPOINTS API ====================

@student_bp.route('/api/profile', methods=['GET'])
@require_student_auth
def get_profile():
    """API: Récupère le profil de l'étudiant connecté."""
    try:
        student_id = session.get('student_id')
        if not student_id:
            return jsonify({
                "success": False,
                "error": "Non authentifié"
            }), 401
        
        student = students_manager.get_student(student_id)
        if not student:
            return jsonify({
                "success": False,
                "error": "Étudiant non trouvé"
            }), 404
        
        # Récupérer les préférences depuis PreferencesStore
        prefs_store = notif.PreferencesStore()
        prefs = prefs_store.obtenir(student_id)
        
        return jsonify({
            "success": True,
            "profile": {
                "id": student.id,
                "nom": student.nom,
                "email": student.email,
                "telephone": student.telephone,
                "faculté": student.faculté,
                "promotion": student.promotion,
                "langue": student.langue,
                "canal_prefere": student.canal_prefere,
                "actif": student.actif,
                "preferences": {
                    "langue": prefs.langue.value if prefs and prefs.langue else student.langue,
                    "canal_prefere": prefs.canal_prefere.value if prefs and prefs.canal_prefere else student.canal_prefere,
                    "actif": prefs.actif if prefs is not None else student.actif
                } if prefs else {
                    "langue": student.langue,
                    "canal_prefere": student.canal_prefere,
                    "actif": student.actif
                }
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@student_bp.route('/api/profile', methods=['POST'])
@require_student_auth
def update_profile():
    """API: Met à jour le profil de l'étudiant."""
    try:
        student_id = session.get('student_id')
        if not student_id:
            return jsonify({
                "success": False,
                "error": "Non authentifié"
            }), 401
        
        if not request.is_json:
            return jsonify({
                "success": False,
                "error": "Le contenu doit être au format JSON"
            }), 400
        
        data = request.get_json()
        student = students_manager.get_student(student_id)
        if not student:
            return jsonify({
                "success": False,
                "error": "Étudiant non trouvé"
            }), 404
        
        # Valider et mettre à jour les champs modifiables
        updates = {}
        
        if "nom" in data:
            nom = data["nom"].strip()
            if not nom:
                return jsonify({
                    "success": False,
                    "error": "Le nom ne peut pas être vide"
                }), 400
            updates["nom"] = nom
        
        if "email" in data:
            email = data["email"].strip()
            if not email:
                return jsonify({
                    "success": False,
                    "error": "L'email ne peut pas être vide"
                }), 400
            # Validation basique de l'email
            if "@" not in email:
                return jsonify({
                    "success": False,
                    "error": "Format d'email invalide"
                }), 400
            updates["email"] = email
        
        if "telephone" in data:
            telephone = data["telephone"].strip() if data["telephone"] else None
            updates["telephone"] = telephone
        
        # Mettre à jour l'étudiant
        if updates:
            updated_student = students_manager.update_student(student_id, **updates)
            
            # Mettre à jour la session si le nom a changé
            if "nom" in updates:
                session['student_nom'] = updated_student.nom
            if "email" in updates:
                session['student_email'] = updated_student.email
            
            return jsonify({
                "success": True,
                "message": "Profil mis à jour avec succès",
                "profile": {
                    "id": updated_student.id,
                    "nom": updated_student.nom,
                    "email": updated_student.email,
                    "telephone": updated_student.telephone,
                    "faculté": updated_student.faculté,
                    "promotion": updated_student.promotion
                }
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": "Aucune modification à effectuer"
            }), 400
        
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": f"Erreur de validation: {str(e)}"
        }), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@student_bp.route('/api/preferences', methods=['GET'])
@require_student_auth
def get_preferences():
    """API: Récupère les préférences de l'étudiant."""
    try:
        student_id = session.get('student_id')
        if not student_id:
            return jsonify({
                "success": False,
                "error": "Non authentifié"
            }), 401
        
        student = students_manager.get_student(student_id)
        if not student:
            return jsonify({
                "success": False,
                "error": "Étudiant non trouvé"
            }), 404
        
        # Récupérer les préférences depuis PreferencesStore
        prefs_store = notif.PreferencesStore()
        prefs = prefs_store.obtenir(student_id)
        
        # Si pas de préférences, utiliser les valeurs par défaut de l'étudiant
        if not prefs:
            return jsonify({
                "success": True,
                "preferences": {
                    "langue": student.langue,
                    "canal_prefere": student.canal_prefere,
                    "actif": student.actif
                }
            }), 200
        
        return jsonify({
            "success": True,
            "preferences": {
                "langue": prefs.langue.value,
                "canal_prefere": prefs.canal_prefere.value,
                "actif": prefs.actif
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@student_bp.route('/api/preferences', methods=['POST'])
@require_student_auth
def update_preferences():
    """API: Met à jour les préférences de l'étudiant."""
    try:
        student_id = session.get('student_id')
        if not student_id:
            return jsonify({
                "success": False,
                "error": "Non authentifié"
            }), 401
        
        if not request.is_json:
            return jsonify({
                "success": False,
                "error": "Le contenu doit être au format JSON"
            }), 400
        
        data = request.get_json()
        student = students_manager.get_student(student_id)
        if not student:
            return jsonify({
                "success": False,
                "error": "Étudiant non trouvé"
            }), 404
        
        # Valider les données
        langue = data.get("langue", student.langue)
        canal_prefere = data.get("canal_prefere", student.canal_prefere)
        actif = data.get("actif", student.actif)
        
        # Valider la langue
        if langue not in ["fr", "en"]:
            return jsonify({
                "success": False,
                "error": f"Langue invalide: {langue}. Valeurs autorisées: fr, en"
            }), 400
        
        # Valider le canal
        if canal_prefere not in ["email", "sms", "app"]:
            return jsonify({
                "success": False,
                "error": f"Canal invalide: {canal_prefere}. Valeurs autorisées: email, sms, app"
            }), 400
        
        # Valider actif
        if not isinstance(actif, bool):
            return jsonify({
                "success": False,
                "error": "Le champ 'actif' doit être un booléen"
            }), 400
        
        # Créer ou mettre à jour les préférences
        prefs_store = notif.PreferencesStore()
        langue_enum = notif.Langue(langue)
        prefs = notif.Preferences(
            langue=langue_enum,
            canal_prefere=canal_prefere,
            actif=actif
        )
        prefs_store.sauvegarder(student_id, prefs)
        
        # Mettre à jour aussi dans students.json pour cohérence
        students_manager.update_student(
            student_id,
            langue=langue,
            canal_prefere=canal_prefere,
            actif=actif
        )
        
        return jsonify({
            "success": True,
            "message": "Préférences mises à jour avec succès",
            "preferences": {
                "langue": langue,
                "canal_prefere": canal_prefere,
                "actif": actif
            }
        }), 200
        
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": f"Erreur de validation: {str(e)}"
        }), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@student_bp.route('/api/notifications', methods=['GET'])
@require_student_auth
def get_notifications():
    """API: Récupère les notifications de l'étudiant."""
    try:
        student_id = session.get('student_id')
        if not student_id:
            return jsonify({
                "success": False,
                "error": "Non authentifié"
            }), 401

        student = students_manager.get_student(student_id)
        if not student:
            return jsonify({
                "success": False,
                "error": "Étudiant non trouvé"
            }), 404
        
        status = request.args.get('status')
        notification_type = request.args.get('type')
        limit = request.args.get('limit', type=int)
        
        notifications_list = notifications_logger.get_student_notifications(
            student_id=student_id,
            status=status,
            notification_type=notification_type,
            limit=limit
        )

        target_lang = (student.langue or "fr").lower()
        translated_notifications = []
        for notif_entry in notifications_list:
            notif_dict = notif_entry.to_dict()
            notif_dict["titre"] = translation_service.translate_text(
                notif_dict.get("titre", ""),
                source_lang="fr",
                target_lang=target_lang
            )
            notif_dict["message"] = translation_service.translate_text(
                notif_dict.get("message", ""),
                source_lang="fr",
                target_lang=target_lang
            )
            translated_notifications.append(notif_dict)
        
        return jsonify({
            "success": True,
            "notifications": translated_notifications,
            "unread_count": notifications_logger.get_unread_count(student_id)
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@student_bp.route('/api/notifications/<notification_id>/read', methods=['POST'])
@require_student_auth
def mark_notification_read(notification_id):
    """API: Marque une notification comme lue."""
    try:
        student_id = session.get('student_id')
        if not student_id:
            return jsonify({
                "success": False,
                "error": "Non authentifié"
            }), 401
        
        success = notifications_logger.mark_as_read(notification_id, student_id)
        
        if success:
            return jsonify({
                "success": True,
                "message": "Notification marquée comme lue",
                "unread_count": notifications_logger.get_unread_count(student_id)
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": "Notification non trouvée ou déjà lue"
            }), 404
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@student_bp.route('/api/notifications/read-all', methods=['POST'])
@require_student_auth
def mark_all_notifications_read():
    """API: Marque toutes les notifications comme lues."""
    try:
        student_id = session.get('student_id')
        if not student_id:
            return jsonify({
                "success": False,
                "error": "Non authentifié"
            }), 401
        
        count = notifications_logger.mark_all_as_read(student_id)
        
        return jsonify({
            "success": True,
            "message": f"{count} notification(s) marquée(s) comme lue(s)",
            "marked_count": count
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@student_bp.route('/api/notifications/<notification_id>', methods=['DELETE'])
@require_student_auth
def delete_notification(notification_id):
    """API: Supprime une notification."""
    try:
        student_id = session.get('student_id')
        if not student_id:
            return jsonify({
                "success": False,
                "error": "Non authentifié"
            }), 401
        
        success = notifications_logger.delete_notification(notification_id, student_id)
        
        if success:
            return jsonify({
                "success": True,
                "message": "Notification supprimée"
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": "Notification non trouvée"
            }), 404
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

