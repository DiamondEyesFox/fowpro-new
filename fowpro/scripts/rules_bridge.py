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
    Effect as RulesEffect, ContinuousEffect, ReplacementEffect as ReplacementEffectCR, EffectBuilder,
    # Abilities
    Ability, ActivateAbility, AutomaticAbility, ContinuousAbility, WillAbility,
    JudgmentAbility, ModalAbility, IncarnationCost, AwakeningCost,
    AbilityFactory,
    CostPaymentModifier,
)

# Replacement system (CR 910)
from ..rules import ReplacementEventType, ReplacementEffectResult, ReplacementBuilder

if TYPE_CHECKING:
    from ..engine import GameEngine
    from ..models import Card, Attribute, WillCost


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

    def register_ability(self, ability: Ability):
        """
        Register a CR-compliant ability.

        This is the primary method for defining card behavior.
        CR abilities are handled by APNAPTriggerManager - NOT lifecycle hooks.
        """
        self._abilities.append(ability)
        # NOTE: We do NOT convert to old effects anymore to prevent double-firing.
        # CR abilities are handled by the engine's APNAPTriggerManager (rules/integration.py).

    def register_spell_effect(self, effects: List[RulesEffect]):
        """
        Register spell effects to run on resolution.

        Spells resolve via on_resolve(), which executes AutomaticAbility entries.
        """
        self._abilities.append(AutomaticAbility(
            name="Spell Effect",
            trigger_condition=TriggerCondition.SPELL_RESOLVES,
            effects=effects,
            is_mandatory=True,
        ))

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

    def get_replacement_effects(self, game: 'GameEngine', card: 'Card') -> List[ReplacementEffectCR]:
        """Override to provide CR replacement effects from this card."""
        return []

    def get_abilities(self) -> List[Ability]:
        """Get all registered CR-compliant abilities."""
        return self._abilities

    def get_activated_abilities(self, game: 'GameEngine', card: 'Card') -> List[Ability]:
        """
        Get activated abilities that can currently be used.

        Returns CR-compliant ActivateAbility objects.
        """
        abilities = []

        # Check CR-compliant abilities
        for ability in self._abilities:
            if not isinstance(ability, ActivateAbility):
                continue
            # Use the ability's own can_play() check
            if ability.can_play(game, card, card.controller):
                abilities.append(ability)

        return abilities

    # =========================================================================
    # LIFECYCLE HOOKS
    # =========================================================================

    def on_enter_field(self, game: 'GameEngine', card: 'Card'):
        """Called when card enters the field.

        NOTE: AutomaticAbility triggers are now handled by the engine's
        APNAPTriggerManager (CR 906). This hook is only for legacy effects.
        """
        pass

    def on_leave_field(self, game: 'GameEngine', card: 'Card'):
        """Called when card leaves the field.

        NOTE: AutomaticAbility triggers handled by APNAPTriggerManager.
        """
        pass

    def on_attack(self, game: 'GameEngine', card: 'Card'):
        """Called when card attacks.

        NOTE: AutomaticAbility triggers handled by APNAPTriggerManager.
        """
        pass  # Attack triggers handled by APNAPTriggerManager

    def on_recover(self, game: 'GameEngine', card: 'Card'):
        """Called when card recovers (untaps).

        NOTE: AutomaticAbility triggers handled by APNAPTriggerManager.
        """
        pass  # Recovery triggers handled by APNAPTriggerManager

    def on_rest(self, game: 'GameEngine', card: 'Card'):
        """Called when card rests (taps)."""
        pass

    def on_turn_start(self, game: 'GameEngine', card: 'Card'):
        """Called at start of controller's turn.

        Resets per-turn ability flags. Trigger firing handled by APNAPTriggerManager.
        """
        # Reset ability flags (triggers are reset by RulesEngine.triggers.reset_turn())
        for ability in self._abilities:
            if isinstance(ability, ActivateAbility):
                ability.used_this_turn = False

    def on_turn_end(self, game: 'GameEngine', card: 'Card'):
        """Called at end of turn.

        NOTE: AutomaticAbility triggers handled by APNAPTriggerManager.
        """
        pass  # End-of-turn triggers handled by APNAPTriggerManager

    # =========================================================================
    # MAGIC STONE SUPPORT
    # =========================================================================

    def get_will_colors(self, game: 'GameEngine', card: 'Card') -> List['Attribute']:
        """
        Get will colors this card can produce.

        Checks for WillAbility and ActivateAbility with produce_will effects.
        """
        from ..models import Attribute
        from ..rules.types import EffectAction

        colors = []
        for ability in self._abilities:
            if isinstance(ability, WillAbility):
                colors.extend(ability.will_colors)
            elif isinstance(ability, ActivateAbility):
                # Check if this activate ability produces will
                for effect in ability.effects:
                    if hasattr(effect, 'action') and effect.action == EffectAction.PRODUCE_WILL:
                        if effect.params.get('any_color'):
                            for attr in [Attribute.LIGHT, Attribute.FIRE, Attribute.WATER,
                                         Attribute.WIND, Attribute.DARKNESS]:
                                if attr not in colors:
                                    colors.append(attr)
                        else:
                            attr = effect.params.get('attribute')
                            if attr and attr not in colors:
                                colors.append(attr)

        return colors

    def produce_will(self, game: 'GameEngine', card: 'Card',
                     chosen_color: 'Attribute') -> bool:
        """
        Produce will of the chosen color.

        Finds matching WillAbility or ActivateAbility and executes it.
        """
        from ..rules.types import EffectAction

        # First check WillAbility (CR 907)
        for ability in self._abilities:
            if isinstance(ability, WillAbility):
                if chosen_color in ability.will_colors:
                    return ability.resolve(game, card, card.controller,
                                          choices={'color': chosen_color})

        # Also check ActivateAbility with produce_will effect (mana dorks)
        for ability in self._abilities:
            if isinstance(ability, ActivateAbility):
                for effect in ability.effects:
                    if hasattr(effect, 'action') and effect.action == EffectAction.PRODUCE_WILL:
                        if effect.params.get('any_color'):
                            if ability.can_play(game, card, card.controller):
                                return ability.resolve(game, card, card.controller,
                                                      choices={'color': chosen_color})
                        else:
                            attr = effect.params.get('attribute')
                            if attr == chosen_color:
                                # Execute this ability
                                if ability.can_play(game, card, card.controller):
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
                if ability.trigger_condition == TriggerCondition.SPELL_RESOLVES:
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
    'RulesEffect', 'ContinuousEffect', 'ReplacementEffectCR', 'ReplacementEventType',
    'ReplacementEffectResult', 'ReplacementBuilder', 'EffectBuilder',
    'Ability', 'ActivateAbility', 'AutomaticAbility', 'ContinuousAbility', 'WillAbility',
    'AbilityFactory',
    'CostPaymentModifier',

    # Convenience functions
    'create_stone_script', 'create_resonator_script',
]
