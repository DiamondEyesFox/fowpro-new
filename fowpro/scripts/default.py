"""
Default Card Script
===================

Fallback script for cards without custom scripts.
Attempts to parse behavior from card data and ability text.
"""

import re
from typing import List, TYPE_CHECKING

from . import CardScript, ScriptRegistry, Effect, EffectType, EffectTiming, EffectCategory

if TYPE_CHECKING:
    from ..engine import GameEngine
    from ..models import Card, Attribute


@ScriptRegistry.register_default
class DefaultCardScript(CardScript):
    """
    Default script that attempts to derive behavior from card data.

    For magic stones, parses ability text to determine will colors.
    """

    def __init__(self, card_code: str):
        super().__init__(card_code)
        self._parsed_colors: List['Attribute'] = None

    def get_will_colors(self, game: 'GameEngine', card: 'Card') -> List['Attribute']:
        """Parse will colors from card's ability text"""
        from ..models import Attribute, CardType

        # Only for magic stones
        if card.data.card_type != CardType.MAGIC_STONE:
            return []

        # Use cached result if available
        if self._parsed_colors is not None:
            return self._parsed_colors

        # Parse from ability text
        self._parsed_colors = self._parse_will_colors(card)
        return self._parsed_colors

    def _parse_will_colors(self, card: 'Card') -> List['Attribute']:
        """Parse will colors from ability text"""
        from ..models import Attribute

        color_map = {
            'light': Attribute.LIGHT,
            'fire': Attribute.FIRE,
            'water': Attribute.WATER,
            'wind': Attribute.WIND,
            'dark': Attribute.DARKNESS,
            'darkness': Attribute.DARKNESS,
        }

        ability = card.data.ability_text.lower() if card.data.ability_text else ""
        name = card.data.name.lower()
        colors = []

        # Pattern 1: "Treat this card as X magic stone and Y magic stone"
        treat_match = re.search(
            r'treat this card as (\w+) magic stone and (\w+) magic stone',
            ability
        )
        if treat_match:
            for color_name in treat_match.groups():
                if color_name in color_map:
                    colors.append(color_map[color_name])
            if colors:
                return colors

        # Pattern 2: Look for "Produce X" in ability text
        # Handle both symbol-based and text-based references
        produce_section = ability.split('[activate]')[-1] if '[activate]' in ability else ability

        for color_name, attr in color_map.items():
            # Check for "produce X" or just color name in produce section
            if f'{color_name}' in produce_section:
                if attr not in colors:
                    colors.append(attr)

        if colors:
            return colors

        # Pattern 3: Check card name for basic stones
        for color_name, attr in color_map.items():
            if f'of {color_name}' in name or f'{color_name} stone' in name:
                return [attr]

        # Special case: "of flame" = fire
        if 'of flame' in name:
            return [Attribute.FIRE]

        # Default to card's attribute if nothing else works
        if card.data.attribute:
            return [card.data.attribute]

        return []

    def produce_will(self, game: 'GameEngine', card: 'Card',
                     chosen_color: 'Attribute') -> bool:
        """Produce will - validates color is allowed"""
        colors = self.get_will_colors(game, card)
        if chosen_color in colors:
            game.players[card.owner].will_pool.add(chosen_color, 1)
            return True
        return False
