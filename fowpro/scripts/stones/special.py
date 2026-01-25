"""
Special Magic Stone Scripts
===========================

Complex magic stones with unique abilities.
"""

import logging
from typing import List, Set, TYPE_CHECKING
from .. import CardScript, ScriptRegistry, Effect, EffectType, EffectTiming, EffectCategory

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from ...engine import GameEngine
    from ...models import Card, Attribute


# =============================================================================
# MOON LIGHT - Produce any color another stone could produce
# =============================================================================

@ScriptRegistry.register("MPR-099")
class MagicStoneOfMoonLight(CardScript):
    """
    [Activate] : Produce VOID.
    [Activate] : Produce one will of any attribute that a magic stone you control could produce.
    """

    def get_will_colors(self, game: 'GameEngine', card: 'Card') -> List['Attribute']:
        from ...models import Attribute, CardType, Zone

        # Collect colors from all other magic stones we control
        colors: Set[Attribute] = set()
        player = game.players[card.owner]

        for stone in player.field:
            # Skip self and non-stones
            if stone.uid == card.uid:
                continue
            if stone.data.card_type != CardType.MAGIC_STONE:
                continue

            # Get that stone's script and colors
            other_script = ScriptRegistry.get(stone.data.code)
            for color in other_script.get_will_colors(game, stone):
                colors.add(color)

        # Always can produce void as fallback
        if not colors:
            colors.add(Attribute.VOID)

        return list(colors)


# =============================================================================
# MOON SHADE - Pay 200 life to produce any of 4 colors
# =============================================================================

@ScriptRegistry.register("MPR-100")
class MagicStoneOfMoonShade(CardScript):
    """
    [Activate] : Produce VOID.
    [Activate] , pay 200 life: Produce LIGHT, FIRE, WATER, or WIND.
    """

    def __init__(self, card_code: str):
        super().__init__(card_code)
        self._pay_life_mode = False

    def get_will_colors(self, game: 'GameEngine', card: 'Card') -> List['Attribute']:
        from ...models import Attribute

        # Base production is void
        colors = [Attribute.VOID]

        # If player has 200+ life, can also produce colored will (costs life)
        player = game.players[card.owner]
        if player.life >= 200:
            colors.extend([
                Attribute.LIGHT,
                Attribute.FIRE,
                Attribute.WATER,
                Attribute.WIND,
            ])

        return colors

    def produce_will(self, game: 'GameEngine', card: 'Card',
                     chosen_color: 'Attribute') -> bool:
        from ...models import Attribute

        player = game.players[card.owner]

        # Void is free
        if chosen_color == Attribute.VOID:
            player.will_pool.add(chosen_color, 1)
            return True

        # Colored will costs 200 life
        if chosen_color in [Attribute.LIGHT, Attribute.FIRE, Attribute.WATER, Attribute.WIND]:
            if player.life >= 200:
                player.life -= 200
                player.will_pool.add(chosen_color, 1)
                game.emit_simple(f"Paid 200 life for {chosen_color.name} will")
                return True

        return False


# =============================================================================
# LITTLE RED - Choose attribute on entry
# =============================================================================

@ScriptRegistry.register("MPR-098")
class LittleRedThePureStone(CardScript):
    """
    As this card comes into a magic stone area, choose an attribute.
    [Activate] : Produce one will of the chosen attribute.
    """

    def __init__(self, card_code: str):
        super().__init__(card_code)
        # Track chosen attribute per card instance
        self._chosen_attribute: dict[int, 'Attribute'] = {}

    def on_enter_field(self, game: 'GameEngine', card: 'Card'):
        """When entering field, player chooses an attribute"""
        logger.debug(f"Little Red on_enter_field START: card.uid={card.uid}")
        try:
            from ...models import Attribute

            logger.debug(f"Little Red: checking _chosen_attribute dict")
            # For now, default to the first available - GUI should prompt
            # Store choice keyed by card UID
            if card.uid not in self._chosen_attribute:
                # Prefer UI prompt via rules engine if available
                chosen = None
                if hasattr(game, "_rules_engine") and game._rules_engine:
                    try:
                        attr_name = game._rules_engine.request_attribute(
                            card.controller,
                            card,
                            options=["Light", "Fire", "Water", "Wind", "Darkness"],
                            prompt="Choose an attribute for Little Red"
                        )
                        if attr_name:
                            chosen = Attribute[attr_name.upper()]
                    except Exception:
                        chosen = None

                # If no choice was made (no UI), leave unchosen so first tap can decide
                if chosen is not None:
                    self._chosen_attribute[card.uid] = chosen
                    logger.debug(f"Little Red on_enter_field: set attribute to {self._chosen_attribute[card.uid]}")
                else:
                    logger.debug("Little Red on_enter_field: no choice made; leaving unchosen")
        except Exception as e:
            logger.debug(f"Little Red on_enter_field CRASH: {e}")
            import traceback
            traceback.print_exc()

    def set_chosen_attribute(self, card: 'Card', attr: 'Attribute'):
        """Set the chosen attribute for this card instance"""
        self._chosen_attribute[card.uid] = attr

    def get_will_colors(self, game: 'GameEngine', card: 'Card') -> List['Attribute']:
        from ...models import Attribute

        # Return the chosen attribute, or all if not yet chosen
        if card.uid in self._chosen_attribute:
            return [self._chosen_attribute[card.uid]]

        # If not chosen yet, show all options
        return [
            Attribute.LIGHT,
            Attribute.FIRE,
            Attribute.WATER,
            Attribute.WIND,
            Attribute.DARKNESS,
        ]

    def produce_will(self, game: 'GameEngine', card: 'Card',
                     chosen_color: 'Attribute') -> bool:
        """Lock in the chosen attribute on first use, then produce will."""
        if card.uid not in self._chosen_attribute:
            self._chosen_attribute[card.uid] = chosen_color
        return super().produce_will(game, card, chosen_color)


# =============================================================================
# TRUE MAGIC STONES - Have additional activated abilities
# =============================================================================

@ScriptRegistry.register("TAT-091")
class AlmeriusTheLevitatingStone(CardScript):
    """
    [Activate] : Produce LIGHT.
    [Activate] : Target J/resonator gains [Flying] until end of turn.
    """

    def get_will_colors(self, game, card):
        from ...models import Attribute
        return [Attribute.LIGHT]

    def get_activated_abilities(self, game: 'GameEngine', card: 'Card') -> List:
        """Return list of activated abilities."""
        from .. import ActivatedAbility

        return [
            ActivatedAbility(
                name="Grant Flying",
                cost_text="{Rest}",
                effect_text="Target J/resonator gains [Flying] until end of turn.",
                requires_rest=True,
                requires_target=True,
                target_filter="j_resonator",
                operation=self._grant_flying,
            )
        ]

    def _grant_flying(self, game: 'GameEngine', card: 'Card', targets: list = None):
        """Grant Flying to target until end of turn."""
        from ...models import Keyword

        if not targets:
            return False

        target = targets[0]
        target.granted_keywords |= Keyword.FLYING
        # Register for cleanup at end of turn
        game.continuous_manager.register_until_eot_keyword(target, Keyword.FLYING)
        return True


@ScriptRegistry.register("TAT-092")
class FeethsingTheHolyWindStone(CardScript):
    """
    [Activate] : Produce WIND.
    [Activate] : Target J/resonator cannot be targeted by normal spells
                 your opponents control until end of turn.
    """

    def get_will_colors(self, game, card):
        from ...models import Attribute
        return [Attribute.WIND]

    def get_activated_abilities(self, game: 'GameEngine', card: 'Card') -> List:
        from .. import ActivatedAbility
        return [
            ActivatedAbility(
                name="Grant Barrier",
                cost_text="{Rest}",
                effect_text="Target J/resonator cannot be targeted by spells opponents control until end of turn.",
                requires_rest=True,
                requires_target=True,
                target_filter="j_resonator",
                operation=self._grant_barrier,
            )
        ]

    def _grant_barrier(self, game: 'GameEngine', card: 'Card', targets: list = None):
        from ...models import Keyword
        if not targets:
            return False
        target = targets[0]
        target.granted_keywords |= Keyword.BARRIER
        game.continuous_manager.register_until_eot_keyword(target, Keyword.BARRIER)
        return True


@ScriptRegistry.register("TAT-093")
class GrubalestaTheSealingStone(CardScript):
    """
    [Activate] : Produce WATER.
    [Activate] : Target J/resonator gains [+0/-200] until end of turn.
    """

    def get_will_colors(self, game, card):
        from ...models import Attribute
        return [Attribute.WATER]

    def get_activated_abilities(self, game: 'GameEngine', card: 'Card') -> List:
        from .. import ActivatedAbility
        return [
            ActivatedAbility(
                name="Weaken",
                cost_text="{Rest}",
                effect_text="Target J/resonator gets -200 DEF until end of turn.",
                requires_rest=True,
                requires_target=True,
                target_filter="j_resonator",
                operation=self._weaken,
            )
        ]

    def _weaken(self, game: 'GameEngine', card: 'Card', targets: list = None):
        if not targets:
            return False
        target = targets[0]
        target.current_def = (target.current_def or target.data.defense) - 200
        game.continuous_manager.register_until_eot_stat_mod(target, 0, -200)
        return True


@ScriptRegistry.register("TAT-099")
class MilestTheGhostlyFlameStone(CardScript):
    """
    [Activate] : Produce FIRE.
    [Activate] : This turn, if target J/resonator would deal damage,
                 it deals that much +200 instead.
    """

    def get_will_colors(self, game, card):
        from ...models import Attribute
        return [Attribute.FIRE]

    def get_activated_abilities(self, game: 'GameEngine', card: 'Card') -> List:
        from .. import ActivatedAbility
        return [
            ActivatedAbility(
                name="Empower",
                cost_text="{Rest}",
                effect_text="Target J/resonator deals +200 damage this turn.",
                requires_rest=True,
                requires_target=True,
                target_filter="j_resonator",
                operation=self._empower,
            )
        ]

    def _empower(self, game: 'GameEngine', card: 'Card', targets: list = None):
        if not targets:
            return False
        target = targets[0]
        # Mark for +200 damage this turn (checked in damage dealing)
        target.damage_bonus = getattr(target, 'damage_bonus', 0) + 200
        return True


@ScriptRegistry.register("TAT-100")
class MoojdartTheFantasyStone(CardScript):
    """
    [Activate] : Produce DARKNESS.
    [Activate] : Target J/resonator loses all races and gains a race
                 of your choice until end of turn.
    """

    def get_will_colors(self, game, card):
        from ...models import Attribute
        return [Attribute.DARKNESS]

    def get_activated_abilities(self, game: 'GameEngine', card: 'Card') -> List:
        from .. import ActivatedAbility
        return [
            ActivatedAbility(
                name="Change Race",
                cost_text="{Rest}",
                effect_text="Target J/resonator loses all races and gains a race of your choice until end of turn.",
                requires_rest=True,
                requires_target=True,
                target_filter="j_resonator",
                requires_choice=True,
                choice_type="race",
                operation=self._change_race,
            )
        ]

    def _change_race(self, game: 'GameEngine', card: 'Card', targets: list = None, choice: str = None):
        if not targets:
            return False
        target = targets[0]
        # Store original races for EOT cleanup
        target._original_races = target.data.races if target.data else []
        # Clear and set new race
        target.granted_races = [choice] if choice else ["Human"]  # Default to Human
        return True


# =============================================================================
# SPECIAL RESONATOR THAT ACTS LIKE A STONE
# =============================================================================

@ScriptRegistry.register("MOA-045")
class GrubalestaTheKeeperOfMagicStones(CardScript):
    """
    Not a magic stone, but a resonator with knowledge counter mechanics.
    """

    def get_will_colors(self, game, card):
        # Not a stone - doesn't produce will
        return []
