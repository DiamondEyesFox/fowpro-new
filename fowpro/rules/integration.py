"""
Rules Integration Module for Force of Will.

Integrates all CR-compliant rules systems into the GameEngine.
This module provides a RulesEngine wrapper that enhances the base
GameEngine with proper rules handling.

Usage:
    from fowpro.rules.integration import RulesEngine
    engine = RulesEngine(db)
    # Use like normal GameEngine, but with CR-compliant behavior
"""

from typing import TYPE_CHECKING, Optional, List, Dict, Any

if TYPE_CHECKING:
    from ..engine import GameEngine
    from ..models import Card

# Import all rule systems
from .priority import PriorityManager, ActionType, PriorityState
from .costs import CostManager, WillCost, CostPaymentPlan
from .layers import LayerManager, Layer, LayeredEffect
from .keywords import KeywordManager, Keyword
from .replacement import ReplacementManager, ReplacementEventType
from .triggers import APNAPTriggerManager, TriggerCondition
from .choices import ChoiceManager, ChoiceType
from .types import TriggerCondition as TriggerCond, KeywordAbility


class RulesEngine:
    """
    CR-compliant rules wrapper for GameEngine.

    Adds proper handling of:
    - Priority with APNAP ordering
    - Cost calculation and payment
    - Continuous effect layers
    - Keyword abilities
    - Replacement effects
    - Triggered abilities with APNAP
    - Player choices (targeting, modals, etc.)
    """

    def __init__(self, game: 'GameEngine'):
        """
        Initialize rules engine wrapper.

        Args:
            game: The base GameEngine to enhance
        """
        self.game = game

        # Initialize CR-compliant managers
        self.priority = PriorityManager(game)
        self.costs = CostManager(game)
        self.layers = LayerManager(game)
        self.keywords = KeywordManager(game)
        self.replacement = ReplacementManager(game)
        self.triggers = APNAPTriggerManager(game)
        self.choices = ChoiceManager(game)

        # Hook into game events
        self._setup_event_hooks()

    def _setup_event_hooks(self):
        """Set up event handlers to integrate rules systems."""
        original_emit = self.game.emit

        def enhanced_emit(event_type, player=-1, card=None, target=None, **data):
            # Call original emit
            original_emit(event_type, player, card, target, **data)

            # Check for triggered abilities with new system
            self._check_triggers_enhanced(event_type, player, card, target, data)

        self.game.emit = enhanced_emit

    def _check_triggers_enhanced(self, event_type, player, card, target, data):
        """Check triggers using APNAP-aware trigger manager."""
        from ..engine import EventType

        # Map EventType to TriggerCondition
        event_map = {
            EventType.ENTERS_FIELD: TriggerCond.ENTER_FIELD,
            EventType.LEAVES_FIELD: TriggerCond.LEAVE_FIELD,
            EventType.CARD_DESTROYED: TriggerCond.DESTROYED,
            EventType.ATTACK_DECLARED: TriggerCond.DECLARES_ATTACK,
            EventType.BLOCKER_DECLARED: TriggerCond.DECLARES_BLOCK,
            EventType.DAMAGE_DEALT: TriggerCond.DEALS_DAMAGE,
            EventType.TURN_START: TriggerCond.BEGINNING_OF_TURN,
            EventType.TURN_END: TriggerCond.END_OF_TURN,
        }

        trigger_cond = event_map.get(event_type)
        if not trigger_cond:
            return

        # Build event data
        event_data = dict(data)
        if card:
            event_data['source'] = card
            event_data['card'] = card
        if target:
            event_data['target'] = target
        event_data['player'] = player

        # Check triggers
        self.triggers.check_triggers(trigger_cond, event_data)

    # =========================================================================
    # ENHANCED PRIORITY SYSTEM
    # =========================================================================

    def pass_priority(self, player: int) -> bool:
        """
        Pass priority with CR-compliant behavior.

        CR 604-605: Priority passing and response windows.
        """
        return self.priority.pass_priority(player)

    def can_act(self, player: int) -> bool:
        """Check if a player can currently act."""
        return self.priority.has_priority(player)

    def is_main_timing(self, player: int) -> bool:
        """
        Check if it's main timing for a player.

        CR 701.2: Main timing requirements.
        """
        return self.priority.is_main_timing(player)

    # =========================================================================
    # ENHANCED COST SYSTEM
    # =========================================================================

    def can_pay_cost(self, card: 'Card', player: int) -> bool:
        """
        Check if a player can pay a card's cost.

        CR 402: Complete cost calculation.
        """
        return self.costs.can_pay_cost(card, player)

    def get_total_cost(self, card: 'Card', player: int):
        """Get the total cost for playing a card."""
        return self.costs.get_total_cost(card, player)

    def pay_cost(self, card: 'Card', player: int, plan: CostPaymentPlan) -> bool:
        """Execute a cost payment plan."""
        return self.costs.pay_cost(card, player, plan)

    def get_alternative_costs(self, card: 'Card', player: int):
        """Get available alternative costs (Incarnation, Remnant, etc.)."""
        return self.costs.get_available_alternatives(card, player)

    # =========================================================================
    # ENHANCED CONTINUOUS EFFECTS
    # =========================================================================

    def apply_continuous_effects(self):
        """
        Apply all continuous effects in layer order.

        CR 909: Layer system for continuous effects.
        """
        self.layers.apply_all_effects()

    def register_continuous_effect(self, effect: LayeredEffect) -> str:
        """Register a new continuous effect."""
        return self.layers.register_effect(effect)

    def unregister_continuous_effect(self, effect_id: str):
        """Remove a continuous effect."""
        self.layers.unregister_effect(effect_id)

    # =========================================================================
    # ENHANCED KEYWORD HANDLING
    # =========================================================================

    def card_has_keyword(self, card: 'Card', keyword: Keyword) -> bool:
        """
        Check if a card has a keyword ability.

        CR 1100+: Keyword ability checks.
        """
        return self.keywords.card_has_keyword(card, keyword)

    def check_blocking_allowed(self, attacker: 'Card', blocker: 'Card') -> bool:
        """
        Check if blocking is allowed by keywords.

        CR 1107: Flying restriction, etc.
        """
        return self.keywords.check_blocking(attacker, blocker)

    def check_targeting_allowed(self, source: 'Card', target: 'Card',
                                 source_controller: int) -> bool:
        """
        Check if targeting is allowed by keywords.

        CR 1120: Barrier restriction.
        """
        return self.keywords.check_targeting(source, target, source_controller)

    def on_deals_damage(self, source: 'Card', target: 'Card',
                        damage: int, is_battle: bool) -> int:
        """Process keyword effects when damage is dealt."""
        return self.keywords.on_deals_damage(source, target, damage, is_battle)

    # =========================================================================
    # ENHANCED REPLACEMENT EFFECTS
    # =========================================================================

    def would_destroy(self, card: 'Card', cause: str = ""):
        """
        Check replacement effects for destruction.

        CR 910: "If this would be destroyed, instead..."
        """
        return self.replacement.would_destroy(card, cause)

    def would_deal_damage(self, source: 'Card', target, amount: int,
                          is_combat: bool = False):
        """Check replacement effects for damage."""
        return self.replacement.would_deal_damage(source, target, amount, is_combat)

    def would_enter_graveyard(self, card: 'Card', from_zone):
        """Check replacement effects for graveyard entry."""
        return self.replacement.would_enter_graveyard(card, from_zone)

    # =========================================================================
    # ENHANCED TRIGGER SYSTEM
    # =========================================================================

    def add_triggers_to_chase(self):
        """
        Add pending triggers to chase in APNAP order.

        CR 906.5: Active player's triggers go on first.
        """
        self.triggers.add_triggers_to_chase()

    def resolve_trigger(self, item) -> bool:
        """Resolve a triggered ability."""
        return self.triggers.resolve_trigger(item)

    # =========================================================================
    # CHOICE SYSTEM
    # =========================================================================

    def request_targets(self, player: int, source: 'Card',
                        requirements, prompt: str = "Choose targets"):
        """Request target selection from player."""
        return self.choices.request_targets(player, source, requirements, prompt)

    def request_modal_choice(self, player: int, source: 'Card', modal):
        """Request modal choice from player."""
        return self.choices.request_modal_choice(player, source, modal)

    def request_yes_no(self, player: int, source: 'Card',
                       prompt: str, mandatory: bool = False):
        """Request yes/no choice from player."""
        return self.choices.request_yes_no(player, source, prompt, mandatory)

    def request_x_value(self, player: int, source: 'Card',
                        min_x: int = 0, max_x: int = None):
        """Request X value choice from player."""
        return self.choices.request_x_value(player, source, min_x, max_x)

    def set_ui_callback(self, callback):
        """Set the UI callback for player choices."""
        self.choices.set_ui_callback(callback)

    # =========================================================================
    # ENHANCED GAME ACTIONS
    # =========================================================================

    def play_card_enhanced(self, player: int, card: 'Card',
                           targets: List['Card'] = None,
                           alternative: str = None,
                           awakening: bool = False,
                           x_value: int = 0) -> bool:
        """
        Play a card with full CR-compliant behavior.

        Handles:
        - Alternative costs (Incarnation, Remnant)
        - Awakening
        - X costs
        - Target selection
        - Modal choices
        """
        from ..models import Zone, CardType

        # Check card is in hand (or graveyard for Remnant)
        if card.zone != Zone.HAND:
            if card.zone == Zone.GRAVEYARD:
                # Check Remnant
                if not self.card_has_keyword(card, Keyword.REMNANT):
                    return False
            else:
                return False

        # Check timing
        if not self._can_play_timing(player, card):
            return False

        # Get cost (with alternatives)
        alt_cost = None
        if alternative:
            alts = self.get_alternative_costs(card, player)
            for alt in alts:
                if alt.name == alternative:
                    alt_cost = alt
                    break

        # Generate payment plan
        plan = self.costs.generate_payment_plan(
            card, player, alt_cost, awakening, x_value
        )
        if not plan:
            return False

        # Request targets if needed
        script = self.game.get_script(card)
        if script and hasattr(script, 'get_target_requirements'):
            requirements = script.get_target_requirements(self.game, card)
            if requirements:
                targets = self.request_targets(
                    player, card, requirements,
                    f"Choose targets for {card.data.name}"
                )
                if not targets and requirements:
                    return False  # Required targets not selected

        # Pay cost
        if not self.pay_cost(card, player, plan):
            return False

        # Handle based on card type
        if card.data.is_resonator():
            self.game._play_resonator(player, card)
        elif card.data.is_spell():
            self.game._play_spell(player, card, targets)
        elif card.data.card_type in [CardType.ADDITION_FIELD, CardType.REGALIA]:
            self.game._play_addition(player, card, targets)

        self.game.emit(self.game.EventType.CARD_PLAYED, player, card)
        return True

    def _can_play_timing(self, player: int, card: 'Card') -> bool:
        """Check if timing allows playing this card."""
        # Quickcast/instant can be played anytime with priority
        if self.card_has_keyword(card, Keyword.QUICKCAST):
            return self.can_act(player)

        if card.data.is_instant():
            return self.can_act(player)

        # Other cards require main timing
        return self.is_main_timing(player)

    def destroy_card_enhanced(self, card: 'Card', cause: str = "") -> bool:
        """
        Destroy a card with replacement effect checking.

        CR 910: Check "If this would be destroyed" effects.
        """
        # Check replacement effects
        should_destroy, reason = self.would_destroy(card, cause)

        if not should_destroy:
            # Destruction was replaced
            return False

        # Check keyword replacements (Imperishable)
        if self.keywords.check_destroy_replacement(card):
            return False

        # Actually destroy
        self.game._destroy_card(card)
        return True

    def deal_damage_enhanced(self, source: 'Card', target, amount: int,
                             is_combat: bool = False) -> int:
        """
        Deal damage with replacement effect checking.

        CR 910: Check damage prevention/modification effects.
        """
        # Check replacement effects
        final_amount, was_prevented = self.would_deal_damage(
            source, target, amount, is_combat
        )

        if final_amount <= 0:
            return 0

        # Apply damage
        from ..models import Card
        if isinstance(target, Card):
            target.damage += final_amount
            self.game.emit(
                self.game.EventType.DAMAGE_DEALT,
                source.controller,
                source,
                target=target,
                amount=final_amount
            )

            # Handle keyword effects
            self.on_deals_damage(source, target, final_amount, is_combat)
        else:
            # Player damage
            player_idx = target
            self.game.players[player_idx].life -= final_amount
            self.game.emit(
                self.game.EventType.PLAYER_DAMAGED,
                player_idx,
                source,
                amount=final_amount
            )

        return final_amount

    # =========================================================================
    # STATE-BASED ACTIONS
    # =========================================================================

    def run_state_based_actions_enhanced(self) -> bool:
        """
        Run state-based actions with full rules integration.

        CR 704: State-based actions.
        """
        # Apply continuous effects in layer order
        self.apply_continuous_effects()

        changed = True
        iterations = 0

        while changed and iterations < 100:
            changed = False
            iterations += 1

            for p_idx, p in enumerate(self.game.players):
                # Destroy creatures with lethal damage
                for card in list(p.field):
                    if card.data.is_resonator() or card.data.card_type.name == 'J_RULER':
                        if card.damage >= card.effective_def:
                            # Check for indestructible
                            if not self.card_has_keyword(card, Keyword.IMPERISHABLE):
                                if self.destroy_card_enhanced(card, "lethal damage"):
                                    changed = True

                # Check for player loss
                if p.life <= 0 and not p.has_lost:
                    self.game._player_loses(p_idx, "life reached 0")
                    changed = True

            # Re-apply continuous effects if state changed
            if changed:
                self.apply_continuous_effects()

        # Add pending triggers to chase in APNAP order
        self.add_triggers_to_chase()

        return iterations > 1

    # =========================================================================
    # TURN STRUCTURE
    # =========================================================================

    def end_turn_enhanced(self):
        """
        End turn with proper cleanup.

        CR 505: End phase rules.
        """
        # Clear until-end-of-turn effects
        self.layers.clear_end_of_turn_effects()

        # Check delayed triggers
        self.triggers.on_end_of_turn()

        # Reset per-turn trigger state
        self.triggers.reset_turn()

        # Clear will pools (CR 505.5c)
        for p in self.game.players:
            p.will_pool.clear()

        # Call original end_turn
        self.game.end_turn()


def enhance_engine(game: 'GameEngine') -> RulesEngine:
    """
    Enhance a GameEngine with CR-compliant rules.

    Usage:
        engine = GameEngine(db)
        rules = enhance_engine(engine)
        # Now use rules.xxx for CR-compliant behavior
    """
    return RulesEngine(game)
