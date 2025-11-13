from __future__ import annotations

import threading
import time
from typing import Dict, Any, Optional


class PerformanceMetrics:
    """Collecteur centralisé des métriques de performance des notifications."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._metrics: Dict[str, Dict[str, Any]] = {}
        self._global: Dict[str, Any] = {
            "total_notifications": 0,
            "total_success": 0,
            "total_failure": 0,
            "total_duration": 0.0,
            "avg_duration": 0.0,
            "last_notification": None,
        }

    def reset(self) -> None:
        with self._lock:
            self._metrics.clear()
            self._global.update(
                total_notifications=0,
                total_success=0,
                total_failure=0,
                total_duration=0.0,
                avg_duration=0.0,
                last_notification=None,
            )

    def record_notification(
        self,
        notifier_name: str,
        duration: float,
        success: bool,
        error: Optional[str] = None,
    ) -> None:
        """Enregistre l'exécution d'un notificateur."""
        timestamp = time.time()
        with self._lock:
            # Mise à jour globale
            self._global["total_notifications"] += 1
            self._global["total_duration"] += duration
            if success:
                self._global["total_success"] += 1
            else:
                self._global["total_failure"] += 1
            if self._global["total_notifications"] > 0:
                self._global["avg_duration"] = (
                    self._global["total_duration"] / self._global["total_notifications"]
                )
            self._global["last_notification"] = timestamp

            # Mise à jour spécifique au notificateur
            metrics = self._metrics.setdefault(
                notifier_name,
                {
                    "count": 0,
                    "success": 0,
                    "failure": 0,
                    "total_duration": 0.0,
                    "avg_duration": 0.0,
                    "min_duration": None,
                    "max_duration": None,
                    "last_duration": None,
                    "last_timestamp": None,
                    "last_error": None,
                },
            )

            metrics["count"] += 1
            metrics["total_duration"] += duration
            metrics["last_duration"] = duration
            metrics["last_timestamp"] = timestamp

            if success:
                metrics["success"] += 1
            else:
                metrics["failure"] += 1
                metrics["last_error"] = error

            if metrics["min_duration"] is None or duration < metrics["min_duration"]:
                metrics["min_duration"] = duration
            if metrics["max_duration"] is None or duration > metrics["max_duration"]:
                metrics["max_duration"] = duration

            metrics["avg_duration"] = metrics["total_duration"] / metrics["count"]

    def get_metrics(self) -> Dict[str, Any]:
        with self._lock:
            # Retourner une copie pour éviter les modifications externes
            return {
                "global": dict(self._global),
                "notifiers": {name: dict(values) for name, values in self._metrics.items()},
            }

    def get_summary(self) -> Dict[str, Any]:
        data = self.get_metrics()
        global_data = data["global"]
        notifiers = data["notifiers"]

        success_rate = None
        total = global_data["total_notifications"]
        if total > 0:
            success_rate = global_data["total_success"] / total

        return {
            "global": {
                **global_data,
                "success_rate": success_rate,
            },
            "notifiers": notifiers,
        }


metrics_manager = PerformanceMetrics()
