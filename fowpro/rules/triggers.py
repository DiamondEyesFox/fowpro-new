"""
Trigger System for Force of Will - APNAP Ordering Implementation.

Implements triggered abilities per CR 906 with proper ordering.

References:
- CR 906: Automatic Abilities
- CR 906.4: Trigger condition checking
- CR 906.5: APNAP ordering (Active Player Non-Active Player)
- CR 906.6: Playing triggered abilities
- CR 906.9: State triggers (intervening-if)
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import TYPE_CHECKING, List, Optional, Dict, Callable, Any, Tuple

if TYPE_CHECKING:
    from ..engine import GameEngine
    from ..models import Card

from .types import TriggerCondition, TriggerTiming
from .conditions import Condition
from .targeting import TargetRequirement


class TriggerType(Enum):
    """
    Types of triggered abilities.

    CR 906: Different trigger patterns.
    """
    # Standard trigger: "When X happens, Y"
    STANDARD = "standard"

    # Intervening-if: "When X happens, if Y, Z"
    # Condition checked on trigger AND on resolution
    INTERVENING_IF = "intervening_if"

    # State trigger: "When X is true" (checks continuously)
    STATE = "state"

    # Delayed trigger: "At end of turn, X"
    DELAYED = "delayed"

    # Reflexive trigger: "When you do, X" (within resolution of another ability)
    REFLEXIVE = "reflexive"


@dataclass
class TriggerInstance:
    """
    A specific instance of a trigger waiting to be put on the chase.

    CR 906.4: Each trigger creates a separate trigger instance.
    """
    # The triggered ability this is an instance of
    ability: 'TriggeredAbility'

    # Source card
    source: 'Card'

    # Controller who will control this triggered ability
    controller: int

    # Event data that caused the trigger
    event_data: Dict[str, Any] = field(default_factory=dict)

    # Turn when this was created (for ordering)
    trigger_turn: int = 0

    # Timestamp within turn (for same-time triggers)
    timestamp: int = 0

    # Whether this has been checked by intervening-if
    intervening_checked: bool = False


@dataclass
class TriggeredAbility:
    """
    A triggered ability per CR 906.

    CR 906.1: "When/Whenever X happens, Y" are automatic abilities.
    """
    # Display name
    name: str = ""

    # What triggers this
    trigger_condition: TriggerCondition = TriggerCondition.ENTER_FIELD

    # Type of trigger
    trigger_type: TriggerType = TriggerType.STANDARD

    # Additional condition beyond the trigger
    condition: Optional[Condition] = None

    # Target requirements
    targets: List[TargetRequirement] = field(default_factory=list)

    # The operation to perform
    operation: Optional[Callable] = None

    # Whether this is mandatory
    is_mandatory: bool = True

    # "You may" - controller can decline
    is_optional: bool = False

    # Once per turn restriction
    once_per_turn: bool = False

    # Has been used this turn
    used_this_turn: bool = False

    # When this goes on the chase
    timing: TriggerTiming = TriggerTiming.CHASE

    # For delayed triggers - when to trigger
    delayed_until: Optional[str] = None  # "end_of_turn", "next_upkeep", etc.

    def can_trigger(self, game: 'GameEngine', source: 'Card',
                    event_type: TriggerCondition, event_data: Dict) -> bool:
        """
        Check if this ability should trigger from an event.

        CR 906.4: Check if trigger condition is met.
        """
        # Check trigger type
        if event_type != self.trigger_condition:
            return False

        # Check once per turn
        if self.once_per_turn and self.used_this_turn:
            return False

        # Check condition (for standard triggers, only checked here)
        if self.condition and self.trigger_type == TriggerType.STANDARD:
            if not self.condition.check(game, source, source.controller):
                return False

        # For intervening-if, check condition now and again on resolution
        if self.trigger_type == TriggerType.INTERVENING_IF:
            if self.condition and not self.condition.check(game, source, source.controller):
                return False

        return True

    def check_on_resolution(self, game: 'GameEngine', source: 'Card') -> bool:
        """
        Check conditions on resolution (for intervening-if).

        CR 906.9: State triggers check condition on trigger AND resolution.
        """
        if self.trigger_type == TriggerType.INTERVENING_IF:
            if self.condition:
                return self.condition.check(game, source, source.controller)
        return True

    def reset_turn(self):
        """Reset per-turn state."""
        self.used_this_turn = False


class APNAPTriggerManager:
    """
    Manages triggered abilities with APNAP ordering.

    CR 906.5: During priority sequence, turn player's triggers go on
    the chase first, then non-active player's triggers.

    This means they RESOLVE in reverse order: non-active player's
    triggers resolve first.
    """

    def __init__(self, game: 'GameEngine'):
        self.game = game

        # Registered triggers per card
        self.triggers: Dict[str, List[TriggeredAbility]] = {}

        # Pending trigger instances waiting to go on chase
        self.pending: List[TriggerInstance] = []

        # Delayed triggers waiting for their time
        self.delayed: List[TriggerInstance] = []

        # Timestamp counter for ordering same-time triggers
        self._timestamp = 0

    def register_trigger(self, card: 'Card', ability: TriggeredAbility):
        """Register a triggered ability for a card."""
        if card.uid not in self.triggers:
            self.triggers[card.uid] = []
        self.triggers[card.uid].append(ability)

    def unregister_triggers(self, card: 'Card'):
        """Unregister all triggers for a card."""
        if card.uid in self.triggers:
            del self.triggers[card.uid]

    def check_triggers(self, event_type: TriggerCondition,
                       event_data: Dict[str, Any]):
        """
        Check for triggered abilities from an event.

        CR 906.4: When a trigger condition is met, create trigger instances.
        """
        self._timestamp += 1

        # Check all registered triggers
        for card_uid, abilities in self.triggers.items():
            card = self.game.get_card(card_uid)
            if not card:
                continue

            for ability in abilities:
                if ability.can_trigger(self.game, card, event_type, event_data):
                    instance = TriggerInstance(
                        ability=ability,
                        source=card,
                        controller=card.controller,
                        event_data=dict(event_data),
                        trigger_turn=self.game.turn_number,
                        timestamp=self._timestamp,
                    )
                    self.pending.append(instance)

    def order_pending_triggers(self) -> List[TriggerInstance]:
        """
        Order pending triggers according to APNAP rule.

        CR 906.5: Active player's triggers go on chase first.
        Since chase resolves LIFO, they resolve LAST.
        """
        if not self.pending:
            return []

        active_player = self.game.turn_player
        non_active = 1 - active_player

        # Separate by controller
        active_triggers = [t for t in self.pending if t.controller == active_player]
        non_active_triggers = [t for t in self.pending if t.controller == non_active]

        # Within each player, order by timestamp (older first)
        active_triggers.sort(key=lambda t: t.timestamp)
        non_active_triggers.sort(key=lambda t: t.timestamp)

        # If player controls multiple, they choose order
        # For AI, we use timestamp order
        active_triggers = self._player_orders_triggers(active_player, active_triggers)
        non_active_triggers = self._player_orders_triggers(non_active, non_active_triggers)

        # APNAP: Active player's go on first (resolve last)
        ordered = active_triggers + non_active_triggers

        return ordered

    def _player_orders_triggers(self, player: int,
                                triggers: List[TriggerInstance]
                                ) -> List[TriggerInstance]:
        """
        Let player order their simultaneous triggers.

        CR 906.5: Player chooses order for their own triggers.

        For AI, we use timestamp order. For human, this should
        trigger a UI prompt if there are multiple.
        """
        if len(triggers) <= 1:
            return triggers

        # TODO: Integrate with UI for human players
        # For now, keep timestamp order
        return triggers

    def add_triggers_to_chase(self):
        """
        Add all pending triggers to the chase in APNAP order.

        Called after events settle during priority sequence.
        """
        if not self.pending:
            return

        ordered = self.order_pending_triggers()
        self.pending = []

        from ..models import ChaseItem

        for instance in ordered:
            # For intervening-if, mark that we need to check condition again
            if instance.ability.trigger_type == TriggerType.INTERVENING_IF:
                instance.intervening_checked = False

            item = ChaseItem(
                source=instance.source,
                controller=instance.controller,
                item_type="TRIGGER",
                effect_data={
                    'ability': instance.ability,
                    'event_data': instance.event_data,
                    'trigger_name': instance.ability.name,
                    'operation': instance.ability.operation,
                    'intervening_checked': instance.intervening_checked,
                },
            )
            self.game.add_to_chase(item)

    def resolve_trigger(self, item) -> bool:
        """
        Resolve a triggered ability.

        CR 906.9: For intervening-if, check condition again.

        Returns True if resolved, False if fizzled.
        """
        ability = item.effect_data.get('ability')
        event_data = item.effect_data.get('event_data', {})
        source = item.source

        if not ability:
            return False

        # Check intervening-if condition
        if ability.trigger_type == TriggerType.INTERVENING_IF:
            if not ability.check_on_resolution(self.game, source):
                # Condition no longer true - fizzle
                return False

        # Check targets are still valid
        # TODO: Implement target validation

        # Execute the operation
        if ability.operation:
            try:
                ability.operation(self.game, source, event_data)
            except Exception as e:
                print(f"[ERROR] Trigger resolution failed: {e}")
                return False

        # Mark as used for once-per-turn
        if ability.once_per_turn:
            ability.used_this_turn = True

        return True

    def reset_turn(self):
        """Reset per-turn trigger state."""
        for abilities in self.triggers.values():
            for ability in abilities:
                ability.reset_turn()

    def add_delayed_trigger(self, ability: TriggeredAbility, source: 'Card',
                            until: str, event_data: Dict = None):
        """
        Add a delayed trigger that fires at a specific time.

        CR 906: Delayed triggers wait for their condition.
        """
        instance = TriggerInstance(
            ability=ability,
            source=source,
            controller=source.controller,
            event_data=event_data or {},
            trigger_turn=self.game.turn_number,
            timestamp=self._timestamp,
        )
        ability.delayed_until = until
        self.delayed.append(instance)

    def check_delayed_triggers(self, event: str):
        """
        Check if any delayed triggers should fire.

        Called at specific times (end of turn, upkeep, etc.)
        """
        to_trigger = []
        remaining = []

        for instance in self.delayed:
            if instance.ability.delayed_until == event:
                to_trigger.append(instance)
            else:
                remaining.append(instance)

        self.delayed = remaining

        # Add triggered ones to pending
        self.pending.extend(to_trigger)

    def on_end_of_turn(self):
        """Handle end of turn for delayed triggers."""
        self.check_delayed_triggers('end_of_turn')

    def on_upkeep(self):
        """Handle upkeep for delayed triggers."""
        self.check_delayed_triggers('upkeep')


# Convenience builders
class TriggerBuilder:
    """Builder for creating common triggered abilities."""

    @staticmethod
    def enter_field(name: str, operation: Callable,
                    condition: Condition = None) -> TriggeredAbility:
        """Create an [Enter] trigger."""
        return TriggeredAbility(
            name=name,
            trigger_condition=TriggerCondition.ENTER_FIELD,
            operation=operation,
            condition=condition,
            is_mandatory=True,
        )

    @staticmethod
    def leave_field(name: str, operation: Callable,
                    condition: Condition = None) -> TriggeredAbility:
        """Create a leave-field trigger."""
        return TriggeredAbility(
            name=name,
            trigger_condition=TriggerCondition.LEAVE_FIELD,
            operation=operation,
            condition=condition,
            is_mandatory=True,
        )

    @staticmethod
    def on_attack(name: str, operation: Callable,
                  condition: Condition = None) -> TriggeredAbility:
        """Create an attack trigger."""
        return TriggeredAbility(
            name=name,
            trigger_condition=TriggerCondition.DECLARES_ATTACK,
            operation=operation,
            condition=condition,
            is_mandatory=True,
        )

    @staticmethod
    def on_damage(name: str, operation: Callable,
                  battle_only: bool = False) -> TriggeredAbility:
        """Create a damage trigger."""
        return TriggeredAbility(
            name=name,
            trigger_condition=(TriggerCondition.DEALS_BATTLE_DAMAGE if battle_only
                               else TriggerCondition.DEALS_DAMAGE),
            operation=operation,
            is_mandatory=True,
        )

    @staticmethod
    def may_trigger(name: str, trigger_condition: TriggerCondition,
                    operation: Callable) -> TriggeredAbility:
        """Create an optional ("You may") trigger."""
        return TriggeredAbility(
            name=name,
            trigger_condition=trigger_condition,
            operation=operation,
            is_mandatory=False,
            is_optional=True,
        )

    @staticmethod
    def intervening_if(name: str, trigger_condition: TriggerCondition,
                       condition: Condition, operation: Callable) -> TriggeredAbility:
        """Create an intervening-if trigger (checks condition twice)."""
        return TriggeredAbility(
            name=name,
            trigger_condition=trigger_condition,
            trigger_type=TriggerType.INTERVENING_IF,
            condition=condition,
            operation=operation,
            is_mandatory=True,
        )

    @staticmethod
    def delayed_eot(name: str, operation: Callable) -> TriggeredAbility:
        """Create a delayed trigger for end of turn."""
        return TriggeredAbility(
            name=name,
            trigger_condition=TriggerCondition.END_OF_TURN,
            trigger_type=TriggerType.DELAYED,
            delayed_until='end_of_turn',
            operation=operation,
        )
