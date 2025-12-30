"""
Triggered Ability System
=========================

Handles triggered abilities that fire on game events.
Similar to YGOPro's SetCategory/CATEGORY_* flags.
"""

from enum import Enum, auto, Flag
from dataclasses import dataclass, field
from typing import Callable, Optional, List, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ..engine import GameEngine
    from ..models import Card


class TriggerEvent(Flag):
    """Events that can trigger abilities"""
    NONE = 0

    # Turn events
    TURN_START = auto()
    TURN_END = auto()
    DRAW_PHASE = auto()
    MAIN_PHASE = auto()
    END_PHASE = auto()

    # Combat events
    ATTACK_DECLARED = auto()
    BLOCKER_DECLARED = auto()
    BEFORE_DAMAGE = auto()
    AFTER_DAMAGE = auto()
    COMBAT_END = auto()

    # Card events
    ENTER_FIELD = auto()
    LEAVE_FIELD = auto()
    DESTROYED = auto()
    BANISHED = auto()
    RETURNED_TO_HAND = auto()
    RECOVERED = auto()
    RESTED = auto()

    # Damage events
    DAMAGE_DEALT = auto()
    DAMAGE_RECEIVED = auto()
    PLAYER_DAMAGED = auto()

    # Card type specific
    SPELL_CAST = auto()
    ABILITY_ACTIVATED = auto()
    STONE_CALLED = auto()
    WILL_PRODUCED = auto()

    # Other
    LIFE_GAINED = auto()
    LIFE_LOST = auto()
    CARD_DRAWN = auto()
    CARD_DISCARDED = auto()


class TriggerTiming(Enum):
    """When the trigger resolves"""
    IMMEDIATE = auto()      # Resolves immediately (replacement effects)
    CHASE = auto()          # Goes on the chase
    STATE_BASED = auto()    # Checked during state-based actions


@dataclass
class TriggerCondition:
    """Conditions for a trigger to fire"""
    # Source requirements
    source_controller: Optional[int] = None  # Must be controlled by this player
    source_zone: Optional[str] = None        # Card must be in this zone

    # Target/event requirements
    target_type: Optional[str] = None        # Type of card involved ("resonator", "spell", etc.)
    target_attribute: Optional[str] = None   # Attribute filter
    target_controller: Optional[int] = None  # Controlled by specific player (0=you, 1=opponent)

    # Custom condition function
    custom: Optional[Callable[['GameEngine', 'Card', dict], bool]] = None


@dataclass
class TriggeredAbility:
    """A triggered ability definition"""
    name: str
    event: TriggerEvent
    timing: TriggerTiming = TriggerTiming.CHASE

    # Condition to check if trigger should fire
    condition: Optional[TriggerCondition] = None

    # The effect to execute
    operation: Optional[Callable[['GameEngine', 'Card', dict], None]] = None

    # Flags
    is_mandatory: bool = False
    once_per_turn: bool = False

    # Internal tracking
    _triggered_this_turn: bool = field(default=False, repr=False)


class TriggerManager:
    """Manages all triggered abilities in the game"""

    def __init__(self, game: 'GameEngine'):
        self.game = game
        self._registered_triggers: List[tuple['Card', TriggeredAbility]] = []
        self._pending_triggers: List[tuple['Card', TriggeredAbility, dict]] = []

    def register_trigger(self, card: 'Card', trigger: TriggeredAbility):
        """Register a triggered ability for a card"""
        self._registered_triggers.append((card, trigger))

    def unregister_card(self, card: 'Card'):
        """Remove all triggers for a card"""
        self._registered_triggers = [
            (c, t) for c, t in self._registered_triggers if c != card
        ]

    def check_triggers(self, event: TriggerEvent, event_data: dict = None):
        """Check all triggers for a specific event"""
        if event_data is None:
            event_data = {}

        for card, trigger in self._registered_triggers:
            if not (trigger.event & event):
                continue

            # Check once per turn
            if trigger.once_per_turn and trigger._triggered_this_turn:
                continue

            # Check condition
            if trigger.condition:
                if not self._check_condition(card, trigger.condition, event_data):
                    continue

            # Add to pending triggers
            self._pending_triggers.append((card, trigger, event_data.copy()))

    def _check_condition(self, card: 'Card', cond: TriggerCondition,
                         event_data: dict) -> bool:
        """Check if a trigger condition is met"""
        from ..models import Zone

        # Source controller check
        if cond.source_controller is not None:
            if card.controller != cond.source_controller:
                return False

        # Source zone check
        if cond.source_zone is not None:
            expected_zone = Zone[cond.source_zone.upper()]
            if card.zone != expected_zone:
                return False

        # Target type check
        if cond.target_type and 'target' in event_data:
            target = event_data['target']
            if hasattr(target, 'data'):
                type_check = {
                    'resonator': target.data.is_resonator(),
                    'spell': target.data.is_spell(),
                    'stone': target.data.is_stone(),
                    'addition': 'ADDITION' in target.data.card_type.name,
                }
                if cond.target_type in type_check:
                    if not type_check[cond.target_type]:
                        return False

        # Custom condition
        if cond.custom:
            if not cond.custom(self.game, card, event_data):
                return False

        return True

    def process_pending_triggers(self):
        """Process all pending triggers"""
        from ..models import ChaseItem
        import uuid

        while self._pending_triggers:
            card, trigger, event_data = self._pending_triggers.pop(0)

            # Mark as triggered this turn
            if trigger.once_per_turn:
                trigger._triggered_this_turn = True

            if trigger.timing == TriggerTiming.IMMEDIATE:
                # Execute immediately
                if trigger.operation:
                    trigger.operation(self.game, card, event_data)
            elif trigger.timing == TriggerTiming.CHASE:
                # Add to chase
                item = ChaseItem(
                    uid=str(uuid.uuid4()),
                    source=card,
                    item_type="TRIGGER",
                    controller=card.controller,
                    targets=[],
                    effect_data={
                        'trigger_name': trigger.name,
                        'event_data': event_data,
                        'operation': trigger.operation,
                    },
                )
                self.game.add_to_chase(item)

    def reset_turn_triggers(self):
        """Reset once-per-turn triggers at turn start"""
        for card, trigger in self._registered_triggers:
            trigger._triggered_this_turn = False


# =============================================================================
# COMMON TRIGGER BUILDERS
# =============================================================================

def when_enters_field(operation: Callable, condition: TriggerCondition = None,
                      mandatory: bool = True) -> TriggeredAbility:
    """Create an 'enters field' trigger"""
    return TriggeredAbility(
        name="When enters field",
        event=TriggerEvent.ENTER_FIELD,
        timing=TriggerTiming.CHASE,
        condition=condition,
        operation=operation,
        is_mandatory=mandatory,
    )


def when_leaves_field(operation: Callable, condition: TriggerCondition = None,
                      mandatory: bool = True) -> TriggeredAbility:
    """Create a 'leaves field' trigger"""
    return TriggeredAbility(
        name="When leaves field",
        event=TriggerEvent.LEAVE_FIELD,
        timing=TriggerTiming.CHASE,
        condition=condition,
        operation=operation,
        is_mandatory=mandatory,
    )


def when_attacks(operation: Callable, condition: TriggerCondition = None) -> TriggeredAbility:
    """Create an 'attacks' trigger"""
    return TriggeredAbility(
        name="When attacks",
        event=TriggerEvent.ATTACK_DECLARED,
        timing=TriggerTiming.CHASE,
        condition=condition,
        operation=operation,
    )


def when_deals_damage(operation: Callable, to_player: bool = False) -> TriggeredAbility:
    """Create a 'deals damage' trigger"""
    event = TriggerEvent.PLAYER_DAMAGED if to_player else TriggerEvent.DAMAGE_DEALT
    return TriggeredAbility(
        name="When deals damage",
        event=event,
        timing=TriggerTiming.CHASE,
        operation=operation,
    )


def when_destroyed(operation: Callable) -> TriggeredAbility:
    """Create a 'destroyed' trigger"""
    return TriggeredAbility(
        name="When destroyed",
        event=TriggerEvent.DESTROYED,
        timing=TriggerTiming.CHASE,
        operation=operation,
    )


def at_turn_start(operation: Callable, controller_only: bool = True) -> TriggeredAbility:
    """Create a 'beginning of turn' trigger"""
    cond = TriggerCondition(source_controller=0) if controller_only else None
    return TriggeredAbility(
        name="At beginning of turn",
        event=TriggerEvent.TURN_START,
        timing=TriggerTiming.CHASE,
        condition=cond,
        operation=operation,
    )


def at_turn_end(operation: Callable, controller_only: bool = True) -> TriggeredAbility:
    """Create an 'end of turn' trigger"""
    cond = TriggerCondition(source_controller=0) if controller_only else None
    return TriggeredAbility(
        name="At end of turn",
        event=TriggerEvent.TURN_END,
        timing=TriggerTiming.CHASE,
        condition=cond,
        operation=operation,
    )
