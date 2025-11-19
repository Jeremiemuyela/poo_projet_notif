"""
Service de traduction simple avec fallback manuel.
"""
import json
import os
from typing import Dict, Optional

try:
    from deep_translator import GoogleTranslator  # type: ignore
except ImportError:  # pragma: no cover
    GoogleTranslator = None


MANUAL_TRANSLATIONS_FILE = "translations_manual.json"
SUPPORTED_LANGUAGES = {"fr", "en"}


class TranslationService:
    """Service centralisé de traduction."""

    def __init__(self):
        self.manual_translations: Dict[str, Dict[str, str]] = {}
        self._load_manual_translations()

    def _load_manual_translations(self):
        """Charge les traductions manuelles depuis un fichier JSON."""
        if not os.path.exists(MANUAL_TRANSLATIONS_FILE):
            self.manual_translations = {}
            return

        try:
            with open(MANUAL_TRANSLATIONS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    self.manual_translations = data
        except (json.JSONDecodeError, IOError) as exc:  # pragma: no cover
            print(f"[TRANSLATION] Erreur de chargement des traductions: {exc}")
            self.manual_translations = {}

    def _find_manual_translation(self, texte: str, target_lang: str) -> Optional[str]:
        """Recherche une traduction dans le dictionnaire manuel."""
        if not texte:
            return None

        key = texte.strip()
        entry = self.manual_translations.get(key)
        if entry:
            return entry.get(target_lang)

        # Essayer avec une clé insensible à la casse
        lower_key = key.lower()
        for original, translations in self.manual_translations.items():
            if original.lower() == lower_key:
                return translations.get(target_lang)
        return None

    def translate_text(
        self,
        texte: str,
        target_lang: str = "fr",
        source_lang: str = "fr"
    ) -> str:
        """Traduit un texte vers la langue cible."""
        if not texte or not isinstance(texte, str):
            return texte

        target_lang = (target_lang or "fr").lower()
        source_lang = (source_lang or "fr").lower()

        if target_lang not in SUPPORTED_LANGUAGES:
            return texte
        if target_lang == source_lang:
            return texte

        # Essayer le dictionnaire manuel
        manual = self._find_manual_translation(texte, target_lang)
        if manual:
            return manual

        # Essayer deep-translator si disponible
        if GoogleTranslator:
            try:
                translator = GoogleTranslator(source=source_lang, target=target_lang)
                translated = translator.translate(texte)
                print(f"[TRANSLATION] ✓ Traduction réussie via deep-translator: '{texte}' -> '{translated}'")
                return translated
            except Exception as exc:  # pragma: no cover
                print(f"[TRANSLATION] ✗ Erreur via API deep-translator: {exc}")

        # Fallback: retourner le texte original avec un avertissement
        print(f"[TRANSLATION] ⚠ ATTENTION: Traduction non disponible pour '{texte}' (fr -> {target_lang}), texte original retourné")
        return texte


# Instance globale
translation_service = TranslationService()

