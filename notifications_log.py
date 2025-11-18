"""
Gestion du log des notifications envoyées aux étudiants
"""
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum

NOTIFICATIONS_LOG_FILE = "notifications_log.json"


class NotificationStatus(Enum):
    """Statut d'une notification."""
    UNREAD = "unread"
    READ = "read"


@dataclass
class NotificationLog:
    """Représente une notification dans le log."""
    id: str
    student_id: str
    type: str  # meteo, securite, sante, infra
    titre: str
    message: str
    priorite: str  # CRITIQUE, HAUTE, NORMALE
    canal: str  # email, sms, app
    status: str = NotificationStatus.UNREAD.value
    created_at: str = None
    read_at: Optional[str] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit la notification en dictionnaire."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NotificationLog':
        """Crée une notification depuis un dictionnaire."""
        return cls(**data)


class NotificationsLogger:
    """Gestionnaire du log des notifications."""
    
    def __init__(self):
        self._notifications: List[NotificationLog] = []
        self._load_notifications()
    
    def _load_notifications(self):
        """Charge les notifications depuis le fichier JSON."""
        if not os.path.exists(NOTIFICATIONS_LOG_FILE):
            self._save_notifications()
            return
        
        try:
            with open(NOTIFICATIONS_LOG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._notifications = [
                    NotificationLog.from_dict(notif_data)
                    for notif_data in data
                ]
        except (json.JSONDecodeError, IOError, KeyError) as e:
            print(f"[NOTIFICATIONS_LOG] Erreur lors du chargement: {e}")
            self._notifications = []
    
    def _save_notifications(self):
        """Sauvegarde les notifications dans le fichier JSON."""
        data = [notif.to_dict() for notif in self._notifications]
        with open(NOTIFICATIONS_LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def log_notification(
        self,
        student_id: str,
        notification_type: str,
        titre: str,
        message: str,
        priorite: str,
        canal: str
    ) -> NotificationLog:
        """Enregistre une nouvelle notification."""
        import uuid
        notification_id = str(uuid.uuid4())
        
        notification = NotificationLog(
            id=notification_id,
            student_id=student_id,
            type=notification_type,
            titre=titre,
            message=message,
            priorite=priorite,
            canal=canal,
            status=NotificationStatus.UNREAD.value
        )
        
        self._notifications.append(notification)
        self._save_notifications()
        
        return notification
    
    def get_student_notifications(
        self,
        student_id: str,
        status: Optional[str] = None,
        notification_type: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[NotificationLog]:
        """Récupère les notifications d'un étudiant."""
        filtered = [
            notif for notif in self._notifications
            if notif.student_id == student_id
        ]
        
        if status:
            filtered = [n for n in filtered if n.status == status]
        
        if notification_type:
            filtered = [n for n in filtered if n.type == notification_type]
        
        # Trier par date (plus récentes en premier)
        filtered.sort(key=lambda x: x.created_at, reverse=True)
        
        if limit:
            filtered = filtered[:limit]
        
        return filtered
    
    def mark_as_read(self, notification_id: str, student_id: str) -> bool:
        """Marque une notification comme lue."""
        for notif in self._notifications:
            if notif.id == notification_id and notif.student_id == student_id:
                if notif.status == NotificationStatus.UNREAD.value:
                    notif.status = NotificationStatus.READ.value
                    notif.read_at = datetime.now().isoformat()
                    self._save_notifications()
                    return True
        return False
    
    def mark_all_as_read(self, student_id: str) -> int:
        """Marque toutes les notifications d'un étudiant comme lues."""
        count = 0
        for notif in self._notifications:
            if notif.student_id == student_id and notif.status == NotificationStatus.UNREAD.value:
                notif.status = NotificationStatus.READ.value
                notif.read_at = datetime.now().isoformat()
                count += 1
        
        if count > 0:
            self._save_notifications()
        
        return count
    
    def get_unread_count(self, student_id: str) -> int:
        """Retourne le nombre de notifications non lues pour un étudiant."""
        return len([
            n for n in self._notifications
            if n.student_id == student_id and n.status == NotificationStatus.UNREAD.value
        ])
    
    def delete_notification(self, notification_id: str, student_id: str) -> bool:
        """Supprime une notification."""
        initial_count = len(self._notifications)
        self._notifications = [
            n for n in self._notifications
            if not (n.id == notification_id and n.student_id == student_id)
        ]
        
        if len(self._notifications) < initial_count:
            self._save_notifications()
            return True
        return False


# Instance globale
notifications_logger = NotificationsLogger()



