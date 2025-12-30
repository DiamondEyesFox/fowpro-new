"""
Dual Magic Stone Scripts
========================

Magic stones that produce one of two colors.
"""

from typing import List, TYPE_CHECKING
from .. import CardScript, ScriptRegistry

if TYPE_CHECKING:
    from ...engine import GameEngine
    from ...models import Card, Attribute


class DualStoneScript(CardScript):
    """Base class for dual-color stones"""
    COLOR_A: 'Attribute' = None
    COLOR_B: 'Attribute' = None

    def get_will_colors(self, game: 'GameEngine', card: 'Card') -> List['Attribute']:
        colors = []
        if self.COLOR_A:
            colors.append(self.COLOR_A)
        if self.COLOR_B:
            colors.append(self.COLOR_B)
        return colors


# =============================================================================
# WIND + DARKNESS (Black Silence)
# =============================================================================

@ScriptRegistry.register("CMF-096")
class MagicStoneOfBlackSilence(CardScript):
    """Wind/Darkness dual stone"""
    def get_will_colors(self, game, card):
        from ...models import Attribute
        return [Attribute.WIND, Attribute.DARKNESS]


# =============================================================================
# WIND + FIRE (Blasting Waves)
# =============================================================================

@ScriptRegistry.register("TAT-094")
class MagicStoneOfBlastingWaves(CardScript):
    """Wind/Fire dual stone"""
    def get_will_colors(self, game, card):
        from ...models import Attribute
        return [Attribute.WIND, Attribute.FIRE]


# =============================================================================
# DARKNESS + WATER (Dark Depth)
# =============================================================================

@ScriptRegistry.register("TAT-095")
class MagicStoneOfDarkDepth(CardScript):
    """Darkness/Water dual stone"""
    def get_will_colors(self, game, card):
        from ...models import Attribute
        return [Attribute.DARKNESS, Attribute.WATER]


# =============================================================================
# WIND + WATER (Deep Wood)
# =============================================================================

@ScriptRegistry.register("CMF-097")
class MagicStoneOfDeepWood(CardScript):
    """Wind/Water dual stone"""
    def get_will_colors(self, game, card):
        from ...models import Attribute
        return [Attribute.WIND, Attribute.WATER]


# =============================================================================
# LIGHT + WIND (Gusting Skies)
# =============================================================================

@ScriptRegistry.register("TAT-096")
class MagicStoneOfGustingSkies(CardScript):
    """Light/Wind dual stone"""
    def get_will_colors(self, game, card):
        from ...models import Attribute
        return [Attribute.LIGHT, Attribute.WIND]


# =============================================================================
# FIRE + WATER (Hearth's Core)
# =============================================================================

@ScriptRegistry.register("CMF-098")
class MagicStoneOfHearthsCore(CardScript):
    """Fire/Water dual stone"""
    def get_will_colors(self, game, card):
        from ...models import Attribute
        return [Attribute.FIRE, Attribute.WATER]


# =============================================================================
# LIGHT + FIRE (Heat Ray)
# =============================================================================

@ScriptRegistry.register("CMF-099")
class MagicStoneOfHeatRay(CardScript):
    """Light/Fire dual stone"""
    def get_will_colors(self, game, card):
        from ...models import Attribute
        return [Attribute.LIGHT, Attribute.FIRE]


# =============================================================================
# LIGHT + DARKNESS (Heaven's Rift)
# =============================================================================

@ScriptRegistry.register("CMF-100")
class MagicStoneOfHeavensRift(CardScript):
    """Light/Darkness dual stone"""
    def get_will_colors(self, game, card):
        from ...models import Attribute
        return [Attribute.LIGHT, Attribute.DARKNESS]


# =============================================================================
# LIGHT + WATER (Light Vapors)
# =============================================================================

@ScriptRegistry.register("TAT-097")
class MagicStoneOfLightVapors(CardScript):
    """Light/Water dual stone"""
    def get_will_colors(self, game, card):
        from ...models import Attribute
        return [Attribute.LIGHT, Attribute.WATER]


# =============================================================================
# DARKNESS + FIRE (Scorched Bales)
# =============================================================================

@ScriptRegistry.register("TAT-098")
class MagicStoneOfScorchedBales(CardScript):
    """Darkness/Fire dual stone"""
    def get_will_colors(self, game, card):
        from ...models import Attribute
        return [Attribute.DARKNESS, Attribute.FIRE]
