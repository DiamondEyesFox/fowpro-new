"""
Basic Magic Stone Scripts
=========================

Single-color magic stones that produce one attribute of will.
"""

from typing import List, TYPE_CHECKING
from .. import CardScript, ScriptRegistry

if TYPE_CHECKING:
    from ...engine import GameEngine
    from ...models import Card, Attribute


class BasicStoneScript(CardScript):
    """Base class for basic single-color stones"""
    PRODUCES: 'Attribute' = None  # Override in subclasses

    def get_will_colors(self, game: 'GameEngine', card: 'Card') -> List['Attribute']:
        if self.PRODUCES:
            return [self.PRODUCES]
        return []


# =============================================================================
# LIGHT STONES
# =============================================================================

@ScriptRegistry.register("CMF-103")
@ScriptRegistry.register("TAT-101")
@ScriptRegistry.register("MPR-103")
class MagicStoneOfLight(BasicStoneScript):
    def get_will_colors(self, game, card):
        from ...models import Attribute
        return [Attribute.LIGHT]


# =============================================================================
# FIRE STONES
# =============================================================================

@ScriptRegistry.register("CMF-102")
@ScriptRegistry.register("TAT-102")
@ScriptRegistry.register("MPR-102")
class MagicStoneOfFlame(BasicStoneScript):
    def get_will_colors(self, game, card):
        from ...models import Attribute
        return [Attribute.FIRE]


# =============================================================================
# WATER STONES
# =============================================================================

@ScriptRegistry.register("CMF-104")
@ScriptRegistry.register("TAT-103")
@ScriptRegistry.register("MPR-104")
class MagicStoneOfWater(BasicStoneScript):
    def get_will_colors(self, game, card):
        from ...models import Attribute
        return [Attribute.WATER]


# =============================================================================
# WIND STONES
# =============================================================================

@ScriptRegistry.register("CMF-105")
@ScriptRegistry.register("TAT-104")
@ScriptRegistry.register("MPR-105")
class MagicStoneOfWind(BasicStoneScript):
    def get_will_colors(self, game, card):
        from ...models import Attribute
        return [Attribute.WIND]


# =============================================================================
# DARKNESS STONES
# =============================================================================

@ScriptRegistry.register("CMF-101")
@ScriptRegistry.register("TAT-105")
@ScriptRegistry.register("MPR-101")
class MagicStoneOfDarkness(BasicStoneScript):
    def get_will_colors(self, game, card):
        from ...models import Attribute
        return [Attribute.DARKNESS]
