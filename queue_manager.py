"""
Module de gestion des files d'attente pour le traitement asynchrone des notifications
"""
import queue
import threading
import time
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from enum import Enum
from dataclasses import dataclass, asdict


class TaskStatus(Enum):
    """Statut d'une tâche."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class NotificationTask:
    """Représente une tâche de notification en file d'attente."""
    id: str
    type: str  # meteo, securite, sante, infra
    data: Dict[str, Any]
    status: TaskStatus
    created_at: float
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    error: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit la tâche en dictionnaire pour JSON."""
        result = asdict(self)
        result['status'] = self.status.value
        result['created_at_iso'] = datetime.fromtimestamp(self.created_at).isoformat()
        if self.started_at:
            result['started_at_iso'] = datetime.fromtimestamp(self.started_at).isoformat()
        if self.completed_at:
            result['completed_at_iso'] = datetime.fromtimestamp(self.completed_at).isoformat()
        return result


class QueueManager:
    """Gestionnaire de files d'attente pour les notifications."""
    
    def __init__(self, num_workers: int = 2):
        """
        Initialise le gestionnaire de files d'attente.
        
        Args:
            num_workers: Nombre de workers pour traiter les tâches
        """
        self._queue = queue.Queue()
        self._tasks: Dict[str, NotificationTask] = {}
        self._tasks_lock = threading.Lock()
        self._num_workers = num_workers
        self._workers: List[threading.Thread] = []
        self._stop_event = threading.Event()
        self._processor: Optional[Callable] = None
        self._running = False
        
        # Statistiques
        self._stats = {
            "total_enqueued": 0,
            "total_processed": 0,
            "total_failed": 0,
            "current_queue_size": 0
        }
    
    def set_processor(self, processor: Callable):
        """
        Définit la fonction de traitement des notifications.
        
        Args:
            processor: Fonction qui prend (task_type, data) et retourne un résultat
        """
        self._processor = processor
    
    def start(self):
        """Démarre les workers pour traiter les tâches."""
        if self._running:
            return
        
        if not self._processor:
            raise ValueError("Un processeur doit être défini avant de démarrer")
        
        self._running = True
        self._stop_event.clear()
        
        for i in range(self._num_workers):
            worker = threading.Thread(
                target=self._worker_loop,
                name=f"QueueWorker-{i}",
                daemon=True
            )
            worker.start()
            self._workers.append(worker)
    
    def stop(self, timeout: float = 5.0):
        """Arrête les workers."""
        if not self._running:
            return
        
        self._running = False
        self._stop_event.set()
        
        for worker in self._workers:
            worker.join(timeout=timeout)
        
        self._workers.clear()
    
    def enqueue(self, task_type: str, data: Dict[str, Any]) -> str:
        """
        Ajoute une tâche à la file d'attente.
        
        Args:
            task_type: Type de notification (meteo, securite, etc.)
            data: Données de la notification
            
        Returns:
            ID de la tâche créée
        """
        task_id = str(uuid.uuid4())
        task = NotificationTask(
            id=task_id,
            type=task_type,
            data=data,
            status=TaskStatus.PENDING,
            created_at=time.time()
        )
        
        with self._tasks_lock:
            self._tasks[task_id] = task
            self._stats["total_enqueued"] += 1
            self._stats["current_queue_size"] += 1
        
        self._queue.put(task_id)
        return task_id
    
    def get_task(self, task_id: str) -> Optional[NotificationTask]:
        """Récupère une tâche par son ID."""
        with self._tasks_lock:
            return self._tasks.get(task_id)
    
    def get_all_tasks(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Récupère toutes les tâches (limité)."""
        with self._tasks_lock:
            tasks = list(self._tasks.values())
            # Trier par date de création (plus récentes en premier)
            tasks.sort(key=lambda t: t.created_at, reverse=True)
            return [task.to_dict() for task in tasks[:limit]]
    
    def get_stats(self) -> Dict[str, Any]:
        """Récupère les statistiques de la file d'attente."""
        with self._tasks_lock:
            pending = sum(1 for t in self._tasks.values() if t.status == TaskStatus.PENDING)
            processing = sum(1 for t in self._tasks.values() if t.status == TaskStatus.PROCESSING)
            completed = sum(1 for t in self._tasks.values() if t.status == TaskStatus.COMPLETED)
            failed = sum(1 for t in self._tasks.values() if t.status == TaskStatus.FAILED)
            
            return {
                **self._stats,
                "current_queue_size": self._queue.qsize(),
                "tasks_by_status": {
                    "pending": pending,
                    "processing": processing,
                    "completed": completed,
                    "failed": failed
                },
                "total_tasks": len(self._tasks),
                "workers": self._num_workers,
                "running": self._running
            }
    
    def clear_completed(self, older_than_hours: int = 24):
        """Supprime les tâches complétées plus anciennes que X heures."""
        cutoff_time = time.time() - (older_than_hours * 3600)
        
        with self._tasks_lock:
            to_remove = [
                task_id for task_id, task in self._tasks.items()
                if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED)
                and task.completed_at and task.completed_at < cutoff_time
            ]
            
            for task_id in to_remove:
                del self._tasks[task_id]
        
        return len(to_remove)
    
    def _worker_loop(self):
        """Boucle principale d'un worker."""
        while not self._stop_event.is_set():
            try:
                # Attendre une tâche avec timeout pour pouvoir vérifier stop_event
                try:
                    task_id = self._queue.get(timeout=1.0)
                except queue.Empty:
                    continue
                
                # Récupérer la tâche
                with self._tasks_lock:
                    task = self._tasks.get(task_id)
                    if not task:
                        continue
                    task.status = TaskStatus.PROCESSING
                    task.started_at = time.time()
                
                # Traiter la tâche
                try:
                    result = self._processor(task.type, task.data)
                    
                    with self._tasks_lock:
                        task.status = TaskStatus.COMPLETED
                        task.completed_at = time.time()
                        task.result = result
                        self._stats["total_processed"] += 1
                        self._stats["current_queue_size"] -= 1
                
                except Exception as e:
                    with self._tasks_lock:
                        task.status = TaskStatus.FAILED
                        task.completed_at = time.time()
                        task.error = str(e)
                        self._stats["total_failed"] += 1
                        self._stats["current_queue_size"] -= 1
                
                finally:
                    self._queue.task_done()
            
            except Exception as e:
                print(f"[QUEUE] Erreur dans le worker: {e}")


# Instance globale du gestionnaire de files d'attente
queue_manager = QueueManager(num_workers=2)


