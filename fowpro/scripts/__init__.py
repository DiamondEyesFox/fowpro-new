"""
FoWPro scripts package (CR-only).
"""

from __future__ import annotations

import logging
from typing import Optional

from .rules_bridge import RulesCardScript

logger = logging.getLogger(__name__)


class ScriptRegistry:
    """
    Registry mapping card codes to CR-based RulesCardScript classes.
    """
    _scripts: dict[str, type[RulesCardScript]] = {}
    _instances: dict[str, RulesCardScript] = {}

    @classmethod
    def register(cls, card_code: str):
        """Decorator to register a script class for a card code."""
        def decorator(script_class: type[RulesCardScript]):
            cls._scripts[card_code] = script_class
            return script_class
        return decorator

    @classmethod
    def get(cls, card_code: str, fresh: bool = False) -> RulesCardScript:
        """Get a script instance for a card code."""
        cls._ensure_generated_loaded()
        if not fresh and card_code in cls._instances:
            return cls._instances[card_code]

        if card_code in cls._scripts:
            instance = cls._scripts[card_code](card_code)
        else:
            raise RuntimeError(f"No script registered for card code {card_code}")

        if not fresh:
            cls._instances[card_code] = instance
        return instance

    @classmethod
    def has_script(cls, card_code: str) -> bool:
        """Check if a custom script exists for this card."""
        cls._ensure_generated_loaded()
        return card_code in cls._scripts

    @classmethod
    def clear_cache(cls):
        """Clear the instance cache (useful for testing)."""
        cls._instances.clear()

    @classmethod
    def _ensure_generated_loaded(cls):
        """Load generated scripts once to populate the registry."""
        if getattr(cls, "_generated_loaded", False):
            return
        try:
            from . import generated  # noqa: F401
            cls._generated_loaded = True
        except Exception:
            cls._generated_loaded = True

__all__ = [
    "ScriptRegistry",
    "RulesCardScript",
]
