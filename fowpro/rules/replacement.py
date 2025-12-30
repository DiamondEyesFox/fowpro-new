"""
Replacement Effect System for Force of Will.

Implements replacement effects per CR 910.

References:
- CR 910: Replacement Effects
- CR 910.1: "If X would Y, Z instead"
- CR 910.2: A replacement effect changes what event happens
- CR 910.3: Player chooses order when multiple apply
- CR 910.4: Self-replacement limitation
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import TYPE_CHECKING, List, Optional, Dict, Callable, Any, Tuple

if TYPE_CHECKING:
    from ..engine import GameEngine
    from ..models import Card

from .conditions import Condition


class ReplacementEventType(Enum):
    """
    Types of events that can be replaced.

    CR 910: Replacement effects watch for specific events.
    """
    # Damage events
    WOULD_DEAL_DAMAGE = "would_deal_damage"
    WOULD_TAKE_DAMAGE = "would_take_damage"

    # Zone change events
    WOULD_BE_DESTROYED = "would_be_destroyed"
    WOULD_ENTER_GRAVEYARD = "would_enter_graveyard"
    WOULD_ENTER_FIELD = "would_enter_field"
    WOULD_LEAVE_FIELD = "would_leave_field"
    WOULD_BE_REMOVED = "would_be_removed"

    # Life events
    WOULD_GAIN_LIFE = "would_gain_life"
    WOULD_LOSE_LIFE = "would_lose_life"

    # Draw events
    WOULD_DRAW = "would_draw"

    # Counter events
    WOULD_ADD_COUNTER = "would_add_counter"
    WOULD_REMOVE_COUNTER = "would_remove_counter"

    # State change events
    WOULD_REST = "would_rest"
    WOULD_RECOVER = "would_recover"


@dataclass
class ReplacementEffectResult:
    """
    Result of a replacement effect.

    Describes what happened instead of the original event.
    """
    # Whether the event was replaced
    was_replaced: bool = False

    # New event data (what happens instead)
    new_event_data: Dict[str, Any] = field(default_factory=dict)

    # Whether to continue with remaining replacements
    continue_chain: bool = True

    # Message for UI/logging
    message: str = ""


@dataclass
class ReplacementEffect:
    """
    A replacement effect per CR 910.

    CR 910.1: Replacement effects are described as "If X would Y, Z instead."
    """
    # Unique ID
    effect_id: str = ""

    # Source card UID
    source_id: str = ""

    # Display name
    name: str = ""

    # What event this replaces
    replaces: ReplacementEventType = ReplacementEventType.WOULD_BE_DESTROYED

    # Condition for this replacement to apply
    condition: Optional[Condition] = None

    # Which cards this can affect (None = any)
    affects_self_only: bool = False
    affects_source_controller_only: bool = False

    # The replacement function
    # Args: (game, original_card, event_data) -> ReplacementEffectResult
    replacement: Optional[Callable] = None

    # CR 910.4: Self-replacement can only apply once per event
    is_self_replacement: bool = False

    # Has this been applied to current event?
    applied_this_event: bool = False

    def can_replace(self, game: 'GameEngine', card: 'Card',
                    event_data: Dict[str, Any]) -> bool:
        """Check if this replacement can apply to an event."""
        # Get source
        source = game.get_card(self.source_id)
        if not source:
            return False

        # Check self-replacement limit
        if self.is_self_replacement and self.applied_this_event:
            return False

        # Check affects restrictions
        if self.affects_self_only:
            if card.uid != self.source_id:
                return False

        if self.affects_source_controller_only:
            if card.controller != source.controller:
                return False

        # Check condition
        if self.condition:
            return self.condition.check(game, source, source.controller)

        return True

    def apply(self, game: 'GameEngine', card: 'Card',
              event_data: Dict[str, Any]) -> ReplacementEffectResult:
        """Apply this replacement effect."""
        if not self.replacement:
            return ReplacementEffectResult(was_replaced=False)

        result = self.replacement(game, card, event_data)

        # Mark as applied for self-replacement limit
        if self.is_self_replacement:
            self.applied_this_event = True

        return result

    def reset(self):
        """Reset per-event state."""
        self.applied_this_event = False


class ReplacementManager:
    """
    Manages replacement effects according to CR 910.

    CR 910.2: When an event would happen, check for replacement effects.
    CR 910.3: If multiple apply, affected player chooses order.
    """

    def __init__(self, game: 'GameEngine'):
        self.game = game

        # All registered replacement effects
        self.effects: Dict[str, ReplacementEffect] = {}

        # Effect counter for unique IDs
        self._effect_counter = 0

        # Pending player choice for multiple replacements
        self._pending_choice: Optional[Dict] = None

    def register_effect(self, effect: ReplacementEffect) -> str:
        """Register a new replacement effect."""
        self._effect_counter += 1
        effect_id = f"repl_{self._effect_counter:06d}"
        effect.effect_id = effect_id
        self.effects[effect_id] = effect
        return effect_id

    def unregister_effect(self, effect_id: str):
        """Remove a replacement effect."""
        if effect_id in self.effects:
            del self.effects[effect_id]

    def unregister_effects_from_source(self, source_id: str):
        """Remove all effects from a specific source."""
        to_remove = [
            eid for eid, e in self.effects.items()
            if e.source_id == source_id
        ]
        for eid in to_remove:
            del self.effects[eid]

    def check_replacements(self, event_type: ReplacementEventType,
                           card: 'Card', event_data: Dict[str, Any]
                           ) -> Tuple[bool, Dict[str, Any]]:
        """
        Check and apply replacement effects to an event.

        CR 910.2: Check if any replacement effects want to modify this event.

        Returns (was_replaced, final_event_data)
        """
        # Reset all effects for this event
        for effect in self.effects.values():
            effect.reset()

        current_data = dict(event_data)
        any_replaced = False

        while True:
            # Find applicable replacements
            applicable = self._get_applicable_replacements(
                event_type, card, current_data
            )

            if not applicable:
                break

            # If multiple apply, affected player chooses (CR 910.3)
            if len(applicable) > 1:
                affected_player = card.controller
                effect = self._choose_replacement(affected_player, applicable)
            else:
                effect = applicable[0]

            # Apply the replacement
            result = effect.apply(self.game, card, current_data)

            if result.was_replaced:
                any_replaced = True
                current_data.update(result.new_event_data)

                if not result.continue_chain:
                    break

        return any_replaced, current_data

    def _get_applicable_replacements(self, event_type: ReplacementEventType,
                                      card: 'Card', event_data: Dict[str, Any]
                                      ) -> List[ReplacementEffect]:
        """Get all replacement effects that can apply to this event."""
        applicable = []

        for effect in self.effects.values():
            if effect.replaces != event_type:
                continue

            if effect.can_replace(self.game, card, event_data):
                applicable.append(effect)

        return applicable

    def _choose_replacement(self, player: int,
                            effects: List[ReplacementEffect]) -> ReplacementEffect:
        """
        Let player choose which replacement to apply first.

        CR 910.3: Affected player chooses the order.

        For AI, just pick the first one. For human, this should
        trigger a UI prompt.
        """
        # TODO: Integrate with UI for human players
        # For now, just return the first effect
        return effects[0]

    def would_destroy(self, card: 'Card', cause: str = "") -> Tuple[bool, str]:
        """
        Check if destruction should happen.

        Returns (should_destroy, reason/replacement_name)
        """
        event_data = {'cause': cause, 'source': card.uid}

        replaced, new_data = self.check_replacements(
            ReplacementEventType.WOULD_BE_DESTROYED,
            card,
            event_data
        )

        if replaced:
            return False, new_data.get('replacement_name', 'replaced')

        return True, cause

    def would_enter_graveyard(self, card: 'Card', from_zone) -> Tuple[bool, Any]:
        """
        Check if entering graveyard should happen.

        Returns (should_enter_graveyard, new_zone_or_None)
        """
        event_data = {'from_zone': from_zone}

        replaced, new_data = self.check_replacements(
            ReplacementEventType.WOULD_ENTER_GRAVEYARD,
            card,
            event_data
        )

        if replaced:
            new_zone = new_data.get('new_zone')
            return False, new_zone

        return True, None

    def would_deal_damage(self, source: 'Card', target, amount: int,
                          is_combat: bool = False) -> Tuple[int, bool]:
        """
        Check if damage should be dealt and how much.

        Returns (final_amount, was_prevented)
        """
        event_data = {
            'source': source.uid if source else None,
            'target': target,
            'amount': amount,
            'is_combat': is_combat,
        }

        replaced, new_data = self.check_replacements(
            ReplacementEventType.WOULD_DEAL_DAMAGE,
            source,
            event_data
        )

        if replaced:
            final_amount = new_data.get('amount', 0)
            return final_amount, amount != final_amount

        return amount, False

    def would_gain_life(self, player: int, amount: int) -> int:
        """
        Check life gain and return final amount.

        Some effects may modify or prevent life gain.
        """
        event_data = {'player': player, 'amount': amount}

        # Create a dummy card for the player (life gain doesn't always have a card)
        # This is a limitation we may need to address
        replaced, new_data = self.check_replacements(
            ReplacementEventType.WOULD_GAIN_LIFE,
            None,  # No specific card
            event_data
        )

        if replaced:
            return new_data.get('amount', amount)

        return amount

    def would_draw(self, player: int, count: int) -> int:
        """
        Check draw and return final count.

        Some effects may modify or prevent draws.
        """
        event_data = {'player': player, 'count': count}

        replaced, new_data = self.check_replacements(
            ReplacementEventType.WOULD_DRAW,
            None,
            event_data
        )

        if replaced:
            return new_data.get('count', count)

        return count


# Common replacement effect builders
class ReplacementBuilder:
    """Builder for creating common replacement effects."""

    @staticmethod
    def prevent_destruction(source_id: str, name: str = "Indestructible",
                            condition: Condition = None) -> ReplacementEffect:
        """Create an effect that prevents destruction."""
        def replacement(game, card, event_data):
            return ReplacementEffectResult(
                was_replaced=True,
                new_event_data={'prevented': True, 'replacement_name': name},
                continue_chain=False,
            )

        return ReplacementEffect(
            source_id=source_id,
            name=name,
            replaces=ReplacementEventType.WOULD_BE_DESTROYED,
            affects_self_only=True,
            condition=condition,
            replacement=replacement,
        )

    @staticmethod
    def return_to_hand_instead(source_id: str, name: str = "Return to Hand",
                               condition: Condition = None) -> ReplacementEffect:
        """Create an effect that returns to hand instead of graveyard."""
        def replacement(game, card, event_data):
            from ..models import Zone
            return ReplacementEffectResult(
                was_replaced=True,
                new_event_data={'new_zone': Zone.HAND, 'replacement_name': name},
                continue_chain=False,
            )

        return ReplacementEffect(
            source_id=source_id,
            name=name,
            replaces=ReplacementEventType.WOULD_ENTER_GRAVEYARD,
            affects_self_only=True,
            condition=condition,
            replacement=replacement,
        )

    @staticmethod
    def prevent_damage(source_id: str, amount: Optional[int] = None,
                       name: str = "Prevent Damage") -> ReplacementEffect:
        """Create an effect that prevents damage."""
        def replacement(game, card, event_data):
            original = event_data.get('amount', 0)
            if amount is None:
                # Prevent all damage
                new_amount = 0
            else:
                # Prevent up to amount
                new_amount = max(0, original - amount)

            return ReplacementEffectResult(
                was_replaced=True,
                new_event_data={'amount': new_amount, 'prevented': original - new_amount},
                continue_chain=True,  # Allow other prevention effects
            )

        return ReplacementEffect(
            source_id=source_id,
            name=name,
            replaces=ReplacementEventType.WOULD_DEAL_DAMAGE,
            replacement=replacement,
        )

    @staticmethod
    def damage_to_life(source_id: str, name: str = "Damage becomes life gain"
                       ) -> ReplacementEffect:
        """Create an effect that converts damage to life gain."""
        def replacement(game, card, event_data):
            amount = event_data.get('amount', 0)
            # Instead of taking damage, gain that much life
            # (This needs to trigger life gain instead)
            return ReplacementEffectResult(
                was_replaced=True,
                new_event_data={'amount': 0, 'gain_life': amount},
                continue_chain=False,
            )

        return ReplacementEffect(
            source_id=source_id,
            name=name,
            replaces=ReplacementEventType.WOULD_DEAL_DAMAGE,
            replacement=replacement,
        )

    @staticmethod
    def modify_life_gain(source_id: str, multiplier: float = 1.0,
                         addition: int = 0, name: str = "Modify Life Gain"
                         ) -> ReplacementEffect:
        """Create an effect that modifies life gain."""
        def replacement(game, card, event_data):
            original = event_data.get('amount', 0)
            new_amount = int(original * multiplier) + addition

            return ReplacementEffectResult(
                was_replaced=True,
                new_event_data={'amount': new_amount},
                continue_chain=True,
            )

        return ReplacementEffect(
            source_id=source_id,
            name=name,
            replaces=ReplacementEventType.WOULD_GAIN_LIFE,
            replacement=replacement,
        )
