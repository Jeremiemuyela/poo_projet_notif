"""
Service de traduction simple avec fallback manuel.
Utilise SQLite pour les traductions manuelles.
"""
from typing import Optional
from db import fetch_one

try:
    from deep_translator import GoogleTranslator  # type: ignore
except ImportError:  # pragma: no cover
    GoogleTranslator = None


SUPPORTED_LANGUAGES = {"fr", "en"}


class TranslationService:
    """Service centralisé de traduction."""

    def __init__(self):
        pass  # Plus besoin de charger depuis JSON

    def _find_manual_translation(self, texte: str, target_lang: str) -> Optional[str]:
        """Recherche une traduction dans la base de données."""
        if not texte:
            return None

        key = texte.strip()
        
        # Recherche exacte
        result = fetch_one(
            f"SELECT {target_lang} FROM translations WHERE key_text = ?",
            (key,)
        )
        if result and result.get(target_lang):
            return result[target_lang]

        # Recherche insensible à la casse
        result = fetch_one(
            f"SELECT {target_lang} FROM translations WHERE LOWER(key_text) = LOWER(?)",
            (key,)
        )
        if result and result.get(target_lang):
            return result[target_lang]
        
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
                print(f"[TRANSLATION] Traduction reussie via deep-translator: '{texte}' -> '{translated}'")
                return translated
            except Exception as exc:  # pragma: no cover
                print(f"[TRANSLATION] Erreur via API deep-translator: {exc}")

        # Fallback: retourner le texte original avec un avertissement
        print(f"[TRANSLATION] ATTENTION: Traduction non disponible pour '{texte}' (fr -> {target_lang}), texte original retourne")
        return texte


# Instance globale
translation_service = TranslationService()

