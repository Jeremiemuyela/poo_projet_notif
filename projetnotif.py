"""
Système de notification d'urgence - Version simplifiée
Tout dans un seul fichier pour faciliter la compréhension
"""
from enum import IntEnum, Enum
import re
import time
from functools import wraps
from typing import Any, Dict, List, Optional

from metrics import metrics_manager
from translation_service import translation_service


REGISTRY: Dict[str, Any] = {}
CONFIG_SOURCE: Dict[str, Dict[str, Any]] = {}


# ==================== ÉNUMÉRATIONS ====================

class Priorite(IntEnum):
    """Niveaux de priorité des notifications."""
    CRITIQUE = 1
    HAUTE = 2
    NORMALE = 3


class Langue(Enum):
    """Langues supportées."""
    FR = "fr"
    EN = "en"


class TypeUrgence(Enum):
    """Types d'urgence."""
    METEO = "meteo"
    SECURITE = "securite"
    SANTE = "sante"
    INFRA = "infra"


# ==================== MODÈLES ====================

class Urgence:
    """Représente une urgence."""
    def __init__(self, type: TypeUrgence, titre: str, message: str, priorite: Priorite):
        self.type = type
        self.titre = titre
        self.message = message
        self.priorite = priorite


# ==================== DESCRIPTEURS ====================


class EmailDescriptor:
    """Valide le format des adresses email."""
    _pattern = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

    def __set_name__(self, owner, name):
        self._storage_name = f"_{name}"

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return getattr(instance, self._storage_name, None)

    def __set__(self, instance, value):
        if value is None:
            setattr(instance, self._storage_name, None)
            return
        if not isinstance(value, str):
            raise TypeError("L'email doit être une chaîne de caractères.")
        value = value.strip()
        if not self._pattern.fullmatch(value):
            raise ValueError(f"Format email invalide: {value}")
        setattr(instance, self._storage_name, value)


class PhoneDescriptor:
    """Valide les numéros de téléphone internationaux simples."""
    _pattern = re.compile(r"^\+?[0-9]{10,15}$")

    def __set_name__(self, owner, name):
        self._storage_name = f"_{name}"

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return getattr(instance, self._storage_name, None)

    def __set__(self, instance, value):
        if value is None:
            setattr(instance, self._storage_name, None)
            return
        if not isinstance(value, str):
            raise TypeError("Le numéro de téléphone doit être une chaîne de caractères.")
        value = value.strip().replace(" ", "")
        if not self._pattern.fullmatch(value):
            raise ValueError(f"Numéro de téléphone international invalide: {value}")
        setattr(instance, self._storage_name, value)


class StudentIdDescriptor:
    """Valide l'identifiant unique des étudiants."""
    _pattern = re.compile(r"^[a-z0-9_-]{5,20}$", re.IGNORECASE)

    def __set_name__(self, owner, name):
        self._storage_name = f"_{name}"

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return getattr(instance, self._storage_name, None)

    def __set__(self, instance, value):
        if not isinstance(value, str):
            raise TypeError("L'identifiant étudiant doit être une chaîne de caractères.")
        value = value.strip()
        if not self._pattern.fullmatch(value):
            raise ValueError("Identifiant étudiant invalide (lettres, chiffres, -, _ entre 5 et 20 caractères).")
        setattr(instance, self._storage_name, value)


class PreferredLanguageDescriptor:
    """Valide la langue préférée au format code ISO (ex: fr, en)."""
    _allowed = {"fr", "en", "es", "de", "it"}

    def __set_name__(self, owner, name):
        self._storage_name = f"_{name}"

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return getattr(instance, self._storage_name, None)

    def __set__(self, instance, value):
        if value is None:
            setattr(instance, self._storage_name, None)
            return
        if not isinstance(value, str):
            raise TypeError("La langue préférée doit être une chaîne de caractères.")
        value = value.strip().lower()
        if value not in self._allowed:
            raise ValueError(f"Langue préférée invalide: {value}. Valeurs autorisées: {', '.join(sorted(self._allowed))}")
        setattr(instance, self._storage_name, value)


# ==================== MÉTACLASSES ====================


class NotificationMeta(type):
    """Génère automatiquement des helpers pour les notificateurs."""
    def __new__(mcls, name, bases, attrs):
        required_fields = attrs.get("required_fields")
        if required_fields and "validate_required_fields" not in attrs:
            attrs["validate_required_fields"] = mcls._build_validator(required_fields)
        attrs.setdefault("description", f"Notification {name}")
        cls = super().__new__(mcls, name, bases, attrs)
        if name != "NotificationBase":
            REGISTRY.setdefault("notification_types", []).append(cls)
        return cls

    @staticmethod
    def _build_validator(required_fields):
        def validator(self, urgence: "Urgence"):
            manquants = [
                field for field in required_fields
                if getattr(urgence, field, None) in (None, "")
            ]
            if manquants:
                raise ValueError(f"Champs d'urgence requis manquants: {', '.join(manquants)}")
        return validator


class ChannelMeta(type):
    """Enregistre automatiquement les canaux disponibles."""
    def __new__(mcls, name, bases, attrs):
        attrs.setdefault("channel_type", name.lower())
        cls = super().__new__(mcls, name, bases, attrs)
        if name != "CanalBase":
            if "livrer" not in attrs:
                raise TypeError(f"Le canal {name} doit définir une méthode 'livrer'.")
            REGISTRY.setdefault("channels", {})[cls.channel_type] = cls
        return cls


class TemplateMeta(type):
    """Cadre pour centraliser les templates de messages."""
    def __new__(mcls, name, bases, attrs):
        template_key = attrs.get("template_key")
        if template_key is None:
            attrs["template_key"] = name.lower()
        required_fields = attrs.get("required_fields")
        if required_fields and "validate_context" not in attrs:
            attrs["validate_context"] = mcls._build_context_validator(required_fields)
        cls = super().__new__(mcls, name, bases, attrs)
        if name != "BaseTemplate":
            REGISTRY.setdefault("templates", {})[cls.template_key] = cls
        return cls

    @staticmethod
    def _build_context_validator(required_fields):
        def validator(self, context: Dict[str, Any]):
            manquants = [
                field for field in required_fields
                if field not in context or context[field] in (None, "")
            ]
            if manquants:
                raise ValueError(f"Champs de template manquants: {', '.join(manquants)}")
        return validator


class ConfigMeta(type):
    """Simplifie la gestion de configuration dynamique."""
    def __new__(mcls, name, bases, attrs):
        namespace = attrs.get("namespace", name.lower())
        attrs["namespace"] = namespace
        defaults = attrs.get("defaults", {})
        attrs["defaults"] = defaults
        cls = super().__new__(mcls, name, bases, attrs)
        REGISTRY.setdefault("configs", {})[namespace] = cls
        return cls

    def get_option(cls, key: str, default: Any = None) -> Any:
        return CONFIG_SOURCE.get(cls.namespace, {}).get(key, cls.defaults.get(key, default))

    def set_option(cls, key: str, value: Any):
        CONFIG_SOURCE.setdefault(cls.namespace, {})[key] = value


class RetryConfig(metaclass=ConfigMeta):
    """Configuration globale du mécanisme de retry."""
    namespace = "retry"
    defaults = {"attempts": 3, "delay": 1, "backoff": 2}


class CircuitBreakerConfig(metaclass=ConfigMeta):
    """Configuration du coupe-circuit automatique."""
    namespace = "circuit_breaker"
    defaults = {"threshold": 3, "cooldown": 5}


class Utilisateur:
    """Représente un utilisateur (étudiant)."""
    id = StudentIdDescriptor()
    email = EmailDescriptor()
    telephone = PhoneDescriptor()
    langue_preferee = PreferredLanguageDescriptor()

    def __init__(
        self,
        id: str,
        nom: str,
        email: str,
        langue: Langue = Langue.FR,
        telephone: Optional[str] = None,
        langue_preferee: Optional[str] = None,
    ):
        self.id = id
        self.nom = nom
        self.email = email
        self.langue = langue
        self.telephone = telephone
        self.langue_preferee = langue_preferee


class Preferences:
    """Préférences d'un utilisateur."""
    def __init__(
        self,
        langue: Optional[Langue] = None,
        canal_prefere: str = "email",
        actif: bool = True
    ):
        self.langue = langue
        self.canal_prefere = canal_prefere
        self.actif = actif


class Message:
    """Message à livrer."""
    def __init__(self, charge: Dict, priorite: Priorite, utilisateur: Utilisateur):
        self.charge = charge
        self.priorite = priorite
        self.utilisateur = utilisateur


# ==================== MIXINS ====================

class RetryMixin:
    """Mixin pour gérer les tentatives de retry."""
    def retry(self, func, attempts=3, delay=1, backoff=2, *args, **kwargs):
        """Exécute une fonction avec retry en cas d'échec."""
        configs = REGISTRY.get("configs")
        if isinstance(configs, dict):
            retry_config = configs.get("retry")
        else:
            retry_config = None
        if retry_config:
            attempts = retry_config.get_option("attempts", attempts)
            delay = retry_config.get_option("delay", delay)
            backoff = retry_config.get_option("backoff", backoff)

        last_exc = None
        for i in range(attempts):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exc = e
                if i < attempts - 1:
                    time.sleep(delay * (backoff ** i))
        raise last_exc


class ConfirmableMixin:
    """Mixin pour gérer les confirmations."""
    def __init__(self):
        self._confirmations = {}

    def attendre_confirmation(self, utilisateur: Utilisateur, message_id: str) -> bool:
        """Attend une confirmation."""
        return self._confirmations.get(message_id, False)


# ==================== DÉCORATEURS ====================

def log_action(func):
    """Décorateur pour logger les actions."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        print(f"[LOG] {func.__name__} appelé")
        return func(*args, **kwargs)
    return wrapper


def require_confirmation(func):
    """Décorateur pour exiger une confirmation."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        print(f"[CONFIRMATION] {func.__name__} nécessite une confirmation")
        return func(*args, **kwargs)
    return wrapper


def add_performance_tracking(cls):
    """Ajoute un suivi automatique du temps d'exécution."""
    original_envoyer = getattr(cls, "envoyer", None)
    if original_envoyer is None:
        return cls

    @wraps(original_envoyer)
    def wrapped_envoyer(self, *args, **kwargs):
        start_time = time.time()
        try:
            result = original_envoyer(self, *args, **kwargs)
            duration = time.time() - start_time
            metrics_manager.record_notification(
                cls.__name__, duration, success=True
            )
            print(f"[PERF] {cls.__name__}.envoyer exécuté en {duration:.3f}s")
            return result
        except Exception as exc:
            duration = time.time() - start_time
            metrics_manager.record_notification(
                cls.__name__, duration, success=False, error=str(exc)
            )
            print(f"[PERF] {cls.__name__}.envoyer a échoué en {duration:.3f}s")
            raise

    cls.envoyer = wrapped_envoyer
    return cls


def auto_configuration_validation(cls):
    """Valide la configuration de base au moment de l'instanciation."""
    original_init = getattr(cls, "__init__", None)
    if original_init is None:
        return cls

    @wraps(original_init)
    def wrapped_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        assert isinstance(self.canaux, dict), "canaux doit être un dictionnaire"
        assert self.canaux, "au moins un canal doit être fourni"
        assert "email" in self.canaux, "le canal 'email' est requis pour les notifications"

    cls.__init__ = wrapped_init
    return cls


def register_in_global_registry(cls):
    """Enregistre automatiquement la classe dans un registre global."""
    REGISTRY.setdefault("notificateurs", [])
    if cls not in REGISTRY["notificateurs"]:
        REGISTRY["notificateurs"].append(cls)
        print(f"[REGISTRY] {cls.__name__} enregistré dans le registre global")
    return cls


def add_circuit_breaker(cls):
    """Ajoute un coupe-circuit simple pour gérer les pannes répétées."""
    original_envoyer = getattr(cls, "envoyer", None)
    if original_envoyer is None:
        return cls
    threshold = getattr(cls, "circuit_breaker_threshold", None)
    cooldown = getattr(cls, "circuit_breaker_cooldown", None)
    configs = REGISTRY.get("configs")
    circuit_config = configs.get("circuit_breaker") if isinstance(configs, dict) else None
    if circuit_config:
        threshold = circuit_config.get_option("threshold", threshold)
        cooldown = circuit_config.get_option("cooldown", cooldown)
    if threshold is None:
        threshold = 3
    if cooldown is None:
        cooldown = 5

    @wraps(original_envoyer)
    def wrapped_envoyer(self, *args, **kwargs):
        state = getattr(self, "_circuit_breaker_state", {"failures": 0, "open": False, "last_failure": 0.0})
        if state.get("open"):
            elapsed = time.time() - state.get("last_failure", 0.0)
        else:
            elapsed = None
        if state.get("open") and elapsed is not None and elapsed < cooldown:
            print(f"[CB] {cls.__name__} circuit ouvert, en attente ({cooldown - elapsed:.1f}s restantes)")
            return False
        if state.get("open") and (elapsed is None or elapsed >= cooldown):
            print(f"[CB] {cls.__name__} circuit refermé après cooldown")
            state["open"] = False
            state["failures"] = 0

        try:
            result = original_envoyer(self, *args, **kwargs)
            state["failures"] = 0
            self._circuit_breaker_state = state
            return result
        except Exception as exc:
            state["failures"] = state.get("failures", 0) + 1
            state["last_failure"] = time.time()
            if state["failures"] >= threshold:
                state["open"] = True
                print(f"[CB] {cls.__name__} circuit ouvert après {state['failures']} échecs")
            self._circuit_breaker_state = state
            raise exc

    cls.envoyer = wrapped_envoyer
    return cls


# ==================== CANAUX ====================

class CanalBase(metaclass=ChannelMeta):
    """Classe de base pour les canaux."""
    channel_type = "base"
    def livrer(self, message: Message) -> bool:
        """Livre un message (à surcharger)."""
        raise NotImplementedError


class Email(CanalBase):
    """Canal email."""
    @log_action
    def livrer(self, message: Message) -> bool:
        """Livre un message par email (mode test)."""
        print(f"[EMAIL] [TEST] Envoi à {message.utilisateur.email}")
        print(f"       Sujet: {message.charge.get('titre', 'Sans titre')}")
        print(f"       Message: {message.charge.get('message', '')}")
        return True


class SMS(CanalBase):
    """Canal SMS."""
    @log_action
    def livrer(self, message: Message) -> bool:
        """Livre un message par SMS."""
        numero = getattr(message.utilisateur, "telephone", None)
        if numero:
            destinataire = f"{message.utilisateur.nom} ({numero})"
        else:
            destinataire = message.utilisateur.nom
        print(f"[SMS] Envoi à {destinataire}")
        print(f"      Message: {message.charge.get('message', '')}")
        return True


class App(CanalBase):
    """Canal notification application."""
    @log_action
    def livrer(self, message: Message) -> bool:
        """Livre un message via l'application mobile."""
        print(f"[APP] Notification pour {message.utilisateur.nom}")
        print(f"      Titre: {message.charge.get('titre', 'Sans titre')}")
        return True


# ==================== TEMPLATES ====================


class BaseTemplate(metaclass=TemplateMeta):
    """Template de base utilisant la traduction générique."""
    template_key = "default"
    required_fields = ["titre", "message"]

    def build_context(self, urgence: Urgence, translate, langue: Langue) -> Dict[str, str]:
        titre = translate(urgence.titre, langue)
        message = translate(urgence.message, langue)
        return {
            "titre": titre,
            "message": message,
        }


class DefaultTemplate(BaseTemplate):
    """Template par défaut utilisé en dernier recours."""
    template_key = "default"
    required_fields = ["titre", "message"]


class MeteoTemplate(BaseTemplate):
    """Template spécifique aux alertes météo."""
    template_key = TypeUrgence.METEO.value
    required_fields = ["titre", "message"]

    def build_context(self, urgence: Urgence, translate, langue: Langue) -> Dict[str, str]:
        context = super().build_context(urgence, translate, langue)
        message = f"{urgence.message} (zones ciblées à vérifier)"
        context["message"] = translate(message, langue)
        return context


class SecuriteTemplate(BaseTemplate):
    """Template spécifique aux alertes de sécurité."""
    template_key = TypeUrgence.SECURITE.value
    required_fields = ["titre", "message", "priorite"]

    def build_context(self, urgence: Urgence, translate, langue: Langue) -> Dict[str, Any]:
        context = super().build_context(urgence, translate, langue)
        context["priorite"] = urgence.priorite.name
        message = f"{urgence.message} (Priorité: {urgence.priorite.name})"
        context["message"] = translate(message, langue)
        return context


class SanteTemplate(BaseTemplate):
    """Template spécifique aux alertes santé."""
    template_key = TypeUrgence.SANTE.value
    required_fields = ["titre", "message"]

    def build_context(self, urgence: Urgence, translate, langue: Langue) -> Dict[str, str]:
        context = super().build_context(urgence, translate, langue)
        message = f"{urgence.message} Merci de suivre les instructions sanitaires."
        context["message"] = translate(message, langue)
        return context


class InfraTemplate(BaseTemplate):
    """Template spécifique aux alertes infrastructure."""
    template_key = TypeUrgence.INFRA.value
    required_fields = ["titre", "message"]

    def build_context(self, urgence: Urgence, translate, langue: Langue) -> Dict[str, str]:
        context = super().build_context(urgence, translate, langue)
        message = f"{urgence.message} Merci de planifier vos déplacements."
        context["message"] = translate(message, langue)
        return context


# ==================== NOTIFICATEURS ====================

class PreferencesStore:
    """Store des préférences utilisateur."""
    def __init__(self):
        self._prefs = {}

    def obtenir(self, user_id: str) -> Optional[Preferences]:
        """Obtient les préférences d'un utilisateur."""
        return self._prefs.get(user_id)

    def sauvegarder(self, user_id: str, prefs: Preferences):
        """Sauvegarde les préférences."""
        self._prefs[user_id] = prefs


class NotificationBase(metaclass=NotificationMeta):
    """Classe de base pour les notifications."""
    def __init__(self, canaux: Dict[str, CanalBase], prefs_store: PreferencesStore):
        self.canaux = canaux
        self.prefs_store = prefs_store

    def traduire(self, texte: str, langue: Langue, source_lang: str = "fr") -> str:
        """Traduit un texte en utilisant le service dédié."""
        if not texte:
            return texte
        try:
            target_lang = langue.value if isinstance(langue, Langue) else str(langue)
        except AttributeError:
            target_lang = str(langue)
        return translation_service.translate_text(
            texte,
            source_lang=source_lang,
            target_lang=target_lang
        )

    @log_action
    def envoyer(self, urgence: Urgence, utilisateurs: List[Utilisateur]):
        """Envoie une notification à des utilisateurs."""
        validator = getattr(self, "validate_required_fields", None)
        if callable(validator):
            validator(urgence)

        template_cls = None
        templates_registry = REGISTRY.get("templates")
        if isinstance(templates_registry, dict):
            template_cls = templates_registry.get(urgence.type.value) or templates_registry.get("default")

        for user in utilisateurs:
            prefs = self.prefs_store.obtenir(user.id)
            if prefs and not prefs.actif:
                continue

            # Déterminer la langue (préférence > profil > langue déclarée)
            langue_utilisateur = user.langue
            if prefs and prefs.langue:
                langue_utilisateur = prefs.langue
            elif user.langue_preferee:
                try:
                    langue_utilisateur = Langue(user.langue_preferee)
                except ValueError:
                    langue_utilisateur = user.langue

            # Préparer la charge utile
            if template_cls:
                template = template_cls()
                charge = template.build_context(urgence, self.traduire, langue_utilisateur)
                validate_context = getattr(template, "validate_context", None)
                if callable(validate_context):
                    validate_context(charge)
            else:
                titre = self.traduire(urgence.titre, langue_utilisateur)
                message_traduit = self.traduire(urgence.message, langue_utilisateur)
                charge = {
                    "titre": titre,
                    "message": message_traduit
                }

            # Créer le message
            message = Message(charge=charge, priorite=urgence.priorite, utilisateur=user)

            # Dispatcher directement vers le canal
            canal_nom = prefs.canal_prefere if prefs and prefs.canal_prefere else "email"
            canal = self.canaux.get(canal_nom, self.canaux["email"])
            canal.livrer(message)


@register_in_global_registry
@auto_configuration_validation
@add_circuit_breaker
@add_performance_tracking
class NotificationMeteorologique(RetryMixin, NotificationBase):
    """Notification météorologique avec retry."""
    required_fields = ["type", "titre", "message"]
    def calculer_zone_risque(self):
        """Calcule les zones à risque."""
        print("[METEO] Calcul des zones à risque")
        return ["Campus Principal"]

    def envoyer(self, urgence: Urgence, utilisateurs: List[Utilisateur]):
        """Envoie une notification météorologique."""
        # Utiliser retry pour le calcul
        zones = self.retry(self.calculer_zone_risque)
        print(f"[METEO] Zones à risque: {zones}")
        super().envoyer(urgence, utilisateurs)


@register_in_global_registry
@auto_configuration_validation
@add_circuit_breaker
@add_performance_tracking
class NotificationSecurite(RetryMixin, ConfirmableMixin, NotificationBase):
    """Notification de sécurité avec retry et confirmation."""
    required_fields = ["type", "titre", "message", "priorite"]
    def __init__(self, canaux: Dict[str, CanalBase], prefs_store: PreferencesStore):
        NotificationBase.__init__(self, canaux, prefs_store)
        ConfirmableMixin.__init__(self)

    @log_action
    @require_confirmation
    def sortir_urgence(self, urgence: Urgence, utilisateurs: List[Utilisateur]):
        """Gère une sortie d'urgence."""
        print("[SECURITE] Sortie d'urgence déclenchée")
        # Forcer priorité critique
        urgence.priorite = Priorite.CRITIQUE
        super().envoyer(urgence, utilisateurs)

    def envoyer(self, urgence: Urgence, utilisateurs: List[Utilisateur]):
        """Envoie une notification de sécurité."""
        if urgence.priorite == Priorite.CRITIQUE:
            self.sortir_urgence(urgence, utilisateurs)
        else:
            super().envoyer(urgence, utilisateurs)


@register_in_global_registry
@auto_configuration_validation
@add_circuit_breaker
@add_performance_tracking
class NotificationSante(ConfirmableMixin, NotificationBase):
    """Notification de santé demandant confirmation."""
    required_fields = ["type", "titre", "message"]
    def __init__(self, canaux: Dict[str, CanalBase], prefs_store: PreferencesStore):
        NotificationBase.__init__(self, canaux, prefs_store)
        ConfirmableMixin.__init__(self)

    @log_action
    @require_confirmation
    def envoyer(self, urgence: Urgence, utilisateurs: List[Utilisateur]):
        """Envoie une notification de santé avec confirmation."""
        return super().envoyer(urgence, utilisateurs)


@register_in_global_registry
@auto_configuration_validation
@add_circuit_breaker
@add_performance_tracking
class NotificationInfra(NotificationBase):
    """Notification liée aux infrastructures."""
    required_fields = ["type", "titre", "message"]
    @log_action
    def envoyer(self, urgence: Urgence, utilisateurs: List[Utilisateur]):
        """Envoie une notification d'infrastructure."""
        print("[INFRA] Communication aux étudiants impactés")
        return super().envoyer(urgence, utilisateurs)


# ==================== DÉMONSTRATION ====================

def main():
    """Fonction principale de démonstration."""
    print("=" * 60)
    print("SYSTÈME DE NOTIFICATION D'URGENCE - DÉMONSTRATION")
    print("=" * 60)

    # Créer les composants
    prefs_store = PreferencesStore()

    # Créer les canaux
    canaux = {
        "email": Email(),
        "sms": SMS(),
        "app": App(),
    }

    # Créer des utilisateurs
    user1 = Utilisateur("etudiant1", "Jean Dupont", "jean@univ.fr", Langue.FR, telephone="+33123456789", langue_preferee="fr")
    user2 = Utilisateur("etudiant2", "Marie Martin", "marie@univ.fr", Langue.FR, telephone="+33698765432", langue_preferee="fr")
    user3 = Utilisateur("etudiant3", "John Smith", "john@univ.fr", Langue.EN, telephone="+447900123456", langue_preferee="en")

    # Configurer les préférences
    prefs_store.sauvegarder(user1.id, Preferences(canal_prefere="email"))
    prefs_store.sauvegarder(user2.id, Preferences(canal_prefere="sms"))
    prefs_store.sauvegarder(user3.id, Preferences(canal_prefere="app"))

    # Scénario 1: Alerte météorologique
    print("\n--- Scénario 1: Alerte météorologique ---")
    urgence_meteo = Urgence(
        type=TypeUrgence.METEO,
        titre="alerte_meteo",
        message="Tempête prévue ce soir",
        priorite=Priorite.HAUTE,
    )
    notif_meteo = NotificationMeteorologique(canaux, prefs_store)
    notif_meteo.envoyer(urgence_meteo, [user1, user2])

    # Scénario 2: Alerte de sécurité
    print("\n--- Scénario 2: Alerte de sécurité ---")
    urgence_secu = Urgence(
        type=TypeUrgence.SECURITE,
        titre="alerte_securite",
        message="ÉVACUATION IMMÉDIATE",
        priorite=Priorite.CRITIQUE,
    )
    notif_secu = NotificationSecurite(canaux, prefs_store)
    notif_secu.envoyer(urgence_secu, [user1, user2, user3])

    # Scénario 3: Alerte de santé
    print("\n--- Scénario 3: Alerte de santé ---")
    urgence_sante = Urgence(
        type=TypeUrgence.SANTE,
        titre="alerte_sante",
        message="Campagne de vaccination disponible cette semaine.",
        priorite=Priorite.NORMALE,
    )
    notif_sante = NotificationSante(canaux, prefs_store)
    notif_sante.envoyer(urgence_sante, [user1, user3])

    # Scénario 4: Alerte d'infrastructure
    print("\n--- Scénario 4: Alerte d'infrastructure ---")
    urgence_infra = Urgence(
        type=TypeUrgence.INFRA,
        titre="alerte_infra",
        message="Coupure d'eau prévue demain de 8h à 12h sur le campus nord.",
        priorite=Priorite.HAUTE,
    )
    notif_infra = NotificationInfra(canaux, prefs_store)
    notif_infra.envoyer(urgence_infra, [user2, user3])

    print("\n" + "=" * 60)
    print("DÉMONSTRATION TERMINÉE")
    print("=" * 60)


if __name__ == "__main__":
    main()
