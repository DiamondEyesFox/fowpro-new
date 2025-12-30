"""
Rules Bridge - Connects CR-based rules module to CardScript system.

This module bridges the new Comprehensive Rules-based ability system
with the existing CardScript infrastructure, allowing cards to be
defined using CR-compliant ability types that automatically integrate
with the game engine.

References:
- CR 901-907: Ability types
- CR 903.2: Playing cards and abilities
- CR 909: Continuous effects
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Callable, TYPE_CHECKING
from abc import ABC

# Import CR-based rules module
from ..rules import (
    # Types
    AbilityType, EffectTiming, TriggerCondition, TriggerTiming,
    EffectAction, KeywordAbility, EffectDuration,
    # Targeting
    TargetRequirement, TargetFilter, TargetZone, TargetController, CommonFilters,
    # Conditions
    Condition, ConditionType, ConditionOperator, ConditionBuilder,
    # Modals
    ModalChoice, Mode, ModalPatterns,
    # Effects
    Effect as RulesEffect, ContinuousEffect, ReplacementEffect, EffectBuilder,
    # Abilities
    Ability, ActivateAbility, AutomaticAbility, ContinuousAbility, WillAbility,
    JudgmentAbility, ModalAbility, IncarnationCost, AwakeningCost,
    AbilityFactory,
)

# Import old system for compatibility
from . import Effect as OldEffect, EffectType as OldEffectType, EffectTiming as OldEffectTiming

if TYPE_CHECKING:
    from ..engine import GameEngine
    from ..models import Card, Attribute, WillCost


# =============================================================================
# ABILITY TYPE MAPPING
# =============================================================================

def map_ability_to_old_effect_type(ability: Ability) -> OldEffectType:
    """Map CR ability type to old EffectType for backward compatibility."""
    if isinstance(ability, ActivateAbility):
        return OldEffectType.ACTIVATED
    elif isinstance(ability, AutomaticAbility):
        # Map trigger condition to specific trigger type
        tc = ability.trigger_condition
        if tc == TriggerCondition.ENTER_FIELD:
            return OldEffectType.TRIGGER_ENTER
        elif tc == TriggerCondition.LEAVE_FIELD:
            return OldEffectType.TRIGGER_LEAVE
        elif tc == TriggerCondition.DECLARES_ATTACK:
            return OldEffectType.TRIGGER_ATTACK
        elif tc in (TriggerCondition.DEALS_DAMAGE, TriggerCondition.DEALS_BATTLE_DAMAGE):
            return OldEffectType.TRIGGER_DAMAGE
        else:
            return OldEffectType.TRIGGER_ENTER  # Default
    elif isinstance(ability, ContinuousAbility):
        return OldEffectType.CONTINUOUS
    elif isinstance(ability, WillAbility):
        return OldEffectType.ACTIVATED  # Will abilities act like activated
    else:
        return OldEffectType.STATIC


def map_timing_to_old(timing: EffectTiming) -> OldEffectTiming:
    """Map CR timing to old EffectTiming."""
    if timing == EffectTiming.MAIN_TIMING:
        return OldEffectTiming.SPELL_SPEED
    elif timing == EffectTiming.INSTANT:
        return OldEffectTiming.INSTANT_SPEED
    elif timing == EffectTiming.WILL_SPEED:
        return OldEffectTiming.WILL_SPEED
    else:
        return OldEffectTiming.INSTANT_SPEED


# =============================================================================
# RULES-BASED CARD SCRIPT
# =============================================================================

class RulesCardScript(ABC):
    """
    Card script base class using CR-based ability system.

    This replaces the old CardScript class with one that uses the
    Comprehensive Rules-based ability definitions.

    Cards define abilities using:
    - ActivateAbility (CR 905)
    - AutomaticAbility (CR 906)
    - ContinuousAbility (CR 904)
    - WillAbility (CR 907)
    """

    def __init__(self, card_code: str):
        self.card_code = card_code
        self._abilities: List[Ability] = []
        self._old_effects: List[OldEffect] = []  # For backward compatibility

    def register_ability(self, ability: Ability):
        """
        Register a CR-compliant ability.

        This is the primary method for defining card behavior.
        """
        self._abilities.append(ability)

        # Also create old-style Effect for backward compatibility with engine
        old_effect = self._convert_to_old_effect(ability)
        if old_effect:
            self._old_effects.append(old_effect)

    def _convert_to_old_effect(self, ability: Ability) -> Optional[OldEffect]:
        """Convert a CR ability to old Effect format for engine compatibility."""

        # Create operation function that executes the ability's effects
        def make_operation(ab: Ability):
            def operation(game: 'GameEngine', card: 'Card', event_data: dict = None):
                targets = event_data.get('targets', []) if event_data else []
                choices = event_data.get('choices', {}) if event_data else {}
                ab.resolve(game, card, card.controller, targets, choices)
            return operation

        # Create condition function
        def make_condition(ab: Ability):
            def condition(game: 'GameEngine', card: 'Card') -> bool:
                return ab.can_play(game, card, card.controller)
            return condition

        if isinstance(ability, ActivateAbility):
            return OldEffect(
                name=ability.name,
                effect_type=OldEffectType.ACTIVATED,
                timing=map_timing_to_old(ability.timing),
                will_cost=ability.will_cost,
                tap_cost=ability.tap_cost,
                condition=make_condition(ability),
                operation=make_operation(ability),
                uses_chase=True,  # Activate abilities use chase
                once_per_turn=ability.once_per_turn,
            )

        elif isinstance(ability, AutomaticAbility):
            return OldEffect(
                name=ability.name,
                effect_type=map_ability_to_old_effect_type(ability),
                timing=OldEffectTiming.INSTANT_SPEED,
                condition=make_condition(ability),
                operation=make_operation(ability),
                uses_chase=ability.trigger_timing == TriggerTiming.CHASE,
                is_mandatory=ability.is_mandatory,
                once_per_turn=ability.once_per_turn,
            )

        elif isinstance(ability, WillAbility):
            # Will abilities are special - they don't use the chase
            return OldEffect(
                name=ability.name,
                effect_type=OldEffectType.ACTIVATED,
                timing=OldEffectTiming.WILL_SPEED,
                tap_cost=ability.tap_cost,
                uses_chase=False,  # CR 907.3: Will abilities don't use chase
                operation=make_operation(ability),
            )

        elif isinstance(ability, ContinuousAbility):
            return OldEffect(
                name=ability.name,
                effect_type=OldEffectType.CONTINUOUS,
                value=ability.continuous_effect,
            )

        return None

    # =========================================================================
    # BACKWARD COMPATIBLE API
    # =========================================================================

    def initial_effect(self, game: 'GameEngine', card: 'Card'):
        """
        Called when card is created. Override to define abilities.

        Example:
            def initial_effect(self, game, card):
                # [Enter] >>> Draw a card
                self.register_ability(AbilityFactory.enter_ability(
                    name="Draw on Enter",
                    effects=[EffectBuilder.draw(1)]
                ))
        """
        pass

    def register_effect(self, effect: OldEffect):
        """Legacy method - register an old-style Effect directly."""
        self._old_effects.append(effect)

    def get_effects(self) -> List[OldEffect]:
        """Get all registered effects in old format (for engine compatibility)."""
        return self._old_effects

    def get_abilities(self) -> List[Ability]:
        """Get all registered CR-compliant abilities."""
        return self._abilities

    def get_activated_abilities(self, game: 'GameEngine', card: 'Card') -> List[OldEffect]:
        """
        Get activated abilities that can currently be used.

        Returns old-style Effects for backward compatibility with engine.
        """
        abilities = []
        for effect in self._old_effects:
            if effect.effect_type != OldEffectType.ACTIVATED:
                continue
            # Check condition
            if effect.condition and not effect.condition(game, card):
                continue
            # Check once per turn
            if effect.once_per_turn and effect._activated_this_turn:
                continue
            # Check tap cost
            if effect.tap_cost and card.is_rested:
                continue
            abilities.append(effect)
        return abilities

    # =========================================================================
    # LIFECYCLE HOOKS
    # =========================================================================

    def on_enter_field(self, game: 'GameEngine', card: 'Card'):
        """Called when card enters the field."""
        # Check for [Enter] abilities
        for ability in self._abilities:
            if isinstance(ability, AutomaticAbility):
                if ability.trigger_condition == TriggerCondition.ENTER_FIELD:
                    if ability.can_trigger(game, card, TriggerCondition.ENTER_FIELD, {}):
                        ability.trigger(game, card, {})
                        # If mandatory or immediate, execute now
                        if ability.is_mandatory or ability.trigger_timing == TriggerTiming.IMMEDIATE:
                            ability.resolve(game, card, card.controller)

        # Also run old-style triggers
        for effect in self._old_effects:
            if effect.effect_type == OldEffectType.TRIGGER_ENTER:
                if not effect.condition or effect.condition(game, card):
                    if effect.operation:
                        effect.operation(game, card)

    def on_leave_field(self, game: 'GameEngine', card: 'Card'):
        """Called when card leaves the field."""
        for ability in self._abilities:
            if isinstance(ability, AutomaticAbility):
                if ability.trigger_condition == TriggerCondition.LEAVE_FIELD:
                    if ability.can_trigger(game, card, TriggerCondition.LEAVE_FIELD, {}):
                        ability.trigger(game, card, {})
                        if ability.is_mandatory or ability.trigger_timing == TriggerTiming.IMMEDIATE:
                            ability.resolve(game, card, card.controller)

        for effect in self._old_effects:
            if effect.effect_type == OldEffectType.TRIGGER_LEAVE:
                if not effect.condition or effect.condition(game, card):
                    if effect.operation:
                        effect.operation(game, card)

    def on_attack(self, game: 'GameEngine', card: 'Card'):
        """Called when card attacks."""
        for ability in self._abilities:
            if isinstance(ability, AutomaticAbility):
                if ability.trigger_condition == TriggerCondition.DECLARES_ATTACK:
                    if ability.can_trigger(game, card, TriggerCondition.DECLARES_ATTACK, {}):
                        ability.trigger(game, card, {})
                        if ability.is_mandatory:
                            ability.resolve(game, card, card.controller)

    def on_recover(self, game: 'GameEngine', card: 'Card'):
        """Called when card recovers (untaps)."""
        for ability in self._abilities:
            if isinstance(ability, AutomaticAbility):
                if ability.trigger_condition == TriggerCondition.RECOVERED:
                    if ability.can_trigger(game, card, TriggerCondition.RECOVERED, {}):
                        ability.trigger(game, card, {})
                        if ability.is_mandatory:
                            ability.resolve(game, card, card.controller)

    def on_rest(self, game: 'GameEngine', card: 'Card'):
        """Called when card rests (taps)."""
        pass

    def on_turn_start(self, game: 'GameEngine', card: 'Card'):
        """Called at start of controller's turn."""
        # Reset once-per-turn flags
        for effect in self._old_effects:
            effect._activated_this_turn = False

        # Reset ability trigger counts
        for ability in self._abilities:
            if isinstance(ability, AutomaticAbility):
                ability.reset_turn()
            elif isinstance(ability, ActivateAbility):
                ability.used_this_turn = False

        # Check for turn start triggers
        for ability in self._abilities:
            if isinstance(ability, AutomaticAbility):
                if ability.trigger_condition == TriggerCondition.TURN_START:
                    if ability.can_trigger(game, card, TriggerCondition.TURN_START, {}):
                        ability.trigger(game, card, {})
                        if ability.is_mandatory:
                            ability.resolve(game, card, card.controller)

    def on_turn_end(self, game: 'GameEngine', card: 'Card'):
        """Called at end of turn."""
        for ability in self._abilities:
            if isinstance(ability, AutomaticAbility):
                if ability.trigger_condition == TriggerCondition.TURN_END:
                    if ability.can_trigger(game, card, TriggerCondition.TURN_END, {}):
                        ability.trigger(game, card, {})
                        if ability.is_mandatory:
                            ability.resolve(game, card, card.controller)

    # =========================================================================
    # MAGIC STONE SUPPORT
    # =========================================================================

    def get_will_colors(self, game: 'GameEngine', card: 'Card') -> List['Attribute']:
        """
        Get will colors this card can produce.

        Checks for WillAbility registered on the card.
        """
        from ..models import Attribute

        colors = []
        for ability in self._abilities:
            if isinstance(ability, WillAbility):
                colors.extend(ability.will_colors)

        return colors

    def produce_will(self, game: 'GameEngine', card: 'Card',
                     chosen_color: 'Attribute') -> bool:
        """
        Produce will of the chosen color.

        Finds matching WillAbility and executes it per CR 907.
        """
        for ability in self._abilities:
            if isinstance(ability, WillAbility):
                if chosen_color in ability.will_colors:
                    return ability.resolve(game, card, card.controller,
                                          choices={'color': chosen_color})
        return False

    # =========================================================================
    # CONTINUOUS EFFECTS
    # =========================================================================

    def get_continuous_effects(self, game: 'GameEngine', card: 'Card') -> List[ContinuousEffect]:
        """Get active continuous effects from this card."""
        effects = []
        for ability in self._abilities:
            if isinstance(ability, ContinuousAbility):
                if ability.is_active(game, card, card.controller):
                    if ability.continuous_effect:
                        ability.continuous_effect.source_id = card.uid
                        effects.append(ability.continuous_effect)
        return effects

    def get_atk_modifier(self, game: 'GameEngine', card: 'Card') -> int:
        """Get ATK modifier from continuous abilities."""
        mod = 0
        for ability in self._abilities:
            if isinstance(ability, ContinuousAbility):
                if ability.is_active(game, card, card.controller):
                    if ability.continuous_effect:
                        mod += ability.continuous_effect.atk_modifier
        return mod

    def get_def_modifier(self, game: 'GameEngine', card: 'Card') -> int:
        """Get DEF modifier from continuous abilities."""
        mod = 0
        for ability in self._abilities:
            if isinstance(ability, ContinuousAbility):
                if ability.is_active(game, card, card.controller):
                    if ability.continuous_effect:
                        mod += ability.continuous_effect.def_modifier
        return mod

    # =========================================================================
    # SPELL RESOLUTION
    # =========================================================================

    def on_resolve(self, game: 'GameEngine', card: 'Card'):
        """Called when spell resolves from chase."""
        # Execute all spell effects
        for ability in self._abilities:
            if isinstance(ability, AutomaticAbility):
                # Spells have implicit "on cast" trigger
                ability.resolve(game, card, card.controller)

    # =========================================================================
    # MODAL SUPPORT
    # =========================================================================

    def get_modal_choices(self, game: 'GameEngine', card: 'Card') -> Optional[ModalChoice]:
        """Get modal choices if this card/ability has them."""
        for ability in self._abilities:
            if ability.modal:
                return ability.modal
        return None

    def get_max_modes(self, game: 'GameEngine', card: 'Card') -> int:
        """Get maximum number of modes that can be chosen."""
        modal = self.get_modal_choices(game, card)
        if modal:
            return modal.choose_count
        return 1


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def create_stone_script(card_code: str, will_colors: List['Attribute'],
                       enter_effect: Callable = None) -> RulesCardScript:
    """
    Create a basic magic stone script.

    Args:
        card_code: Card code
        will_colors: List of Attribute colors this stone produces
        enter_effect: Optional enter effect function

    Example:
        script = create_stone_script("CMF-096", [Attribute.FIRE])
    """
    class StoneScript(RulesCardScript):
        def initial_effect(self, game, card):
            # Register will ability
            self.register_ability(AbilityFactory.will_ability(
                colors=will_colors,
                tap=True
            ))

            # Register enter effect if provided
            if enter_effect:
                self.register_ability(AutomaticAbility(
                    name="Enter Effect",
                    trigger_condition=TriggerCondition.ENTER_FIELD,
                    is_mandatory=True,
                    effects=[RulesEffect(
                        action=EffectAction.CUSTOM,
                        params={'operation': enter_effect}
                    )]
                ))

    return StoneScript(card_code)


def create_resonator_script(card_code: str, abilities: List[Ability] = None,
                           keywords: KeywordAbility = KeywordAbility.NONE) -> RulesCardScript:
    """
    Create a resonator script with given abilities.

    Args:
        card_code: Card code
        abilities: List of abilities to register
        keywords: Keyword flags

    Example:
        script = create_resonator_script("CMF-019", [
            AbilityFactory.enter_ability("Draw", [EffectBuilder.draw(1)])
        ])
    """
    class ResonatorScript(RulesCardScript):
        def initial_effect(self, game, card):
            for ability in (abilities or []):
                self.register_ability(ability)

            # Store keywords for has_keyword checks
            self._keywords = keywords

        def has_keyword(self, keyword: KeywordAbility) -> bool:
            return bool(self._keywords & keyword)

    return ResonatorScript(card_code)


# =============================================================================
# EXPORTS FOR RULES MODULE
# =============================================================================

__all__ = [
    # Main class
    'RulesCardScript',

    # Re-export rules module for convenience
    'AbilityType', 'EffectTiming', 'TriggerCondition', 'TriggerTiming',
    'EffectAction', 'KeywordAbility', 'EffectDuration',
    'TargetRequirement', 'TargetFilter', 'TargetZone', 'TargetController', 'CommonFilters',
    'Condition', 'ConditionType', 'ConditionOperator', 'ConditionBuilder',
    'ModalChoice', 'Mode', 'ModalPatterns',
    'RulesEffect', 'ContinuousEffect', 'ReplacementEffect', 'EffectBuilder',
    'Ability', 'ActivateAbility', 'AutomaticAbility', 'ContinuousAbility', 'WillAbility',
    'AbilityFactory',

    # Convenience functions
    'create_stone_script', 'create_resonator_script',
]
