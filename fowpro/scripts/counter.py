"""
Counter/Cancel System
=====================

Handles spell/ability countering and the chase.
FoW uses a "chase" system similar to MTG's stack.
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Callable, Optional, List, Dict, Any, TYPE_CHECKING
import uuid

if TYPE_CHECKING:
    from ..engine import GameEngine
    from ..models import Card, Player


class ChaseItemType(Enum):
    """Types of items on the chase"""
    SPELL = auto()
    ABILITY = auto()
    TRIGGER = auto()


@dataclass
class ChaseItem:
    """An item on the chase (FoW's stack)"""
    uid: str
    source: 'Card'
    item_type: ChaseItemType
    controller: int

    # For spells
    spell_card: Optional['Card'] = None

    # Targets and effect data
    targets: List['Card'] = field(default_factory=list)
    effect_data: Dict[str, Any] = field(default_factory=dict)

    # Tracking
    is_cancelled: bool = False


class ChaseManager:
    """Manages the chase (FoW's stack)"""

    def __init__(self, game: 'GameEngine'):
        self.game = game
        self._chase: List[ChaseItem] = []
        self._ui_callback: Optional[Callable] = None

    def set_ui_callback(self, callback: Callable):
        """Set UI callback for priority decisions"""
        self._ui_callback = callback

    @property
    def is_empty(self) -> bool:
        return len(self._chase) == 0

    @property
    def top(self) -> Optional[ChaseItem]:
        return self._chase[-1] if self._chase else None

    def add_spell(self, card: 'Card', controller: int,
                 targets: List['Card'] = None) -> ChaseItem:
        """Add a spell to the chase"""
        item = ChaseItem(
            uid=str(uuid.uuid4()),
            source=card,
            item_type=ChaseItemType.SPELL,
            controller=controller,
            spell_card=card,
            targets=targets or [],
        )

        self._chase.append(item)
        self.game.emit_event('added_to_chase', {
            'item': item,
            'chase_size': len(self._chase),
        })

        return item

    def add_ability(self, source: 'Card', controller: int,
                   effect_data: Dict = None,
                   targets: List['Card'] = None) -> ChaseItem:
        """Add an activated ability to the chase"""
        item = ChaseItem(
            uid=str(uuid.uuid4()),
            source=source,
            item_type=ChaseItemType.ABILITY,
            controller=controller,
            targets=targets or [],
            effect_data=effect_data or {},
        )

        self._chase.append(item)
        self.game.emit_event('added_to_chase', {'item': item})

        return item

    def add_trigger(self, source: 'Card', controller: int,
                   trigger_data: Dict) -> ChaseItem:
        """Add a triggered ability to the chase"""
        item = ChaseItem(
            uid=str(uuid.uuid4()),
            source=source,
            item_type=ChaseItemType.TRIGGER,
            controller=controller,
            effect_data=trigger_data,
        )

        self._chase.append(item)
        self.game.emit_event('added_to_chase', {'item': item})

        return item

    def cancel_item(self, item: ChaseItem):
        """Cancel an item on the chase"""
        if item in self._chase:
            item.is_cancelled = True
            self.game.emit_event('chase_item_cancelled', {'item': item})

    def counter_spell(self, target_item: ChaseItem):
        """Counter a spell on the chase"""
        if target_item.item_type != ChaseItemType.SPELL:
            return False

        if target_item not in self._chase:
            return False

        self.cancel_item(target_item)

        # Move spell to graveyard
        if target_item.spell_card:
            from ..models import Zone
            self.game.move_card(target_item.spell_card, Zone.GRAVEYARD)

        return True

    def negate_ability(self, target_item: ChaseItem):
        """Negate an ability on the chase"""
        if target_item.item_type == ChaseItemType.SPELL:
            return False

        if target_item not in self._chase:
            return False

        self.cancel_item(target_item)
        return True

    def resolve_top(self):
        """Resolve the top item of the chase"""
        if not self._chase:
            return

        item = self._chase.pop()

        if item.is_cancelled:
            self.game.emit_event('cancelled_item_removed', {'item': item})
            return

        self.game.emit_event('resolving_chase_item', {'item': item})

        if item.item_type == ChaseItemType.SPELL:
            self._resolve_spell(item)
        elif item.item_type == ChaseItemType.ABILITY:
            self._resolve_ability(item)
        elif item.item_type == ChaseItemType.TRIGGER:
            self._resolve_trigger(item)

    def _resolve_spell(self, item: ChaseItem):
        """Resolve a spell from the chase"""
        from ..models import Zone

        card = item.spell_card
        if not card:
            return

        # Execute spell effect from script
        script = self.game.get_script_for_card(card)
        if script and hasattr(script, 'resolve'):
            script.resolve(self.game, card, item.targets)

        # Move to graveyard after resolution
        self.game.move_card(card, Zone.GRAVEYARD)

        self.game.emit_event('spell_resolved', {
            'card': card,
            'targets': item.targets,
        })

    def _resolve_ability(self, item: ChaseItem):
        """Resolve an activated ability"""
        # Get operation from effect data
        operation = item.effect_data.get('operation')
        if operation and callable(operation):
            operation(self.game, item.source, item.effect_data)

        self.game.emit_event('ability_resolved', {
            'source': item.source,
            'effect_data': item.effect_data,
        })

    def _resolve_trigger(self, item: ChaseItem):
        """Resolve a triggered ability"""
        operation = item.effect_data.get('operation')
        event_data = item.effect_data.get('event_data', {})

        if operation and callable(operation):
            operation(self.game, item.source, event_data)

        self.game.emit_event('trigger_resolved', {
            'source': item.source,
            'trigger_name': item.effect_data.get('trigger_name'),
        })

    def resolve_all(self):
        """Resolve the entire chase (when both players pass)"""
        while self._chase:
            self.resolve_top()

    def get_spells_on_chase(self) -> List[ChaseItem]:
        """Get all spell items on the chase"""
        return [i for i in self._chase if i.item_type == ChaseItemType.SPELL]

    def get_abilities_on_chase(self) -> List[ChaseItem]:
        """Get all ability items on the chase"""
        return [i for i in self._chase
                if i.item_type in (ChaseItemType.ABILITY, ChaseItemType.TRIGGER)]

    def find_item(self, item_id: str) -> Optional[ChaseItem]:
        """Find chase item by UID"""
        for item in self._chase:
            if item.uid == item_id:
                return item
        return None


# =============================================================================
# COUNTER SPELL EFFECTS
# =============================================================================

def counter_target_spell(game: 'GameEngine', source: 'Card',
                        target_item: ChaseItem) -> bool:
    """Counter a target spell on the chase"""
    return game.chase_manager.counter_spell(target_item)


def counter_target_ability(game: 'GameEngine', source: 'Card',
                          target_item: ChaseItem) -> bool:
    """Negate a target ability on the chase"""
    return game.chase_manager.negate_ability(target_item)


def counter_unless_pay(game: 'GameEngine', source: 'Card',
                      target_item: ChaseItem,
                      cost_amount: int,
                      callback: Callable[[bool], None]):
    """Counter unless controller pays X will"""
    controller = game.players[target_item.controller]
    total_will = sum(controller.will_pool.values())

    if total_will < cost_amount:
        # Can't pay, auto-counter
        game.chase_manager.counter_spell(target_item)
        callback(True)
        return

    # Ask if they want to pay
    def on_decision(pay: bool):
        if pay:
            # Deduct will (simplified - takes from any)
            remaining = cost_amount
            for attr in list(controller.will_pool.keys()):
                available = controller.will_pool[attr]
                take = min(available, remaining)
                controller.will_pool[attr] -= take
                remaining -= take
                if remaining <= 0:
                    break
            callback(False)  # Not countered
        else:
            game.chase_manager.counter_spell(target_item)
            callback(True)  # Countered

    game.emit_event('counter_unless_pay', {
        'target': target_item,
        'amount': cost_amount,
        'callback': on_decision,
    })


# =============================================================================
# CARD COUNTERS (not chase-related)
# =============================================================================

class CounterManager:
    """Manages counters on cards (+1/+1, -1/-1, custom counters)"""

    def __init__(self, game: 'GameEngine'):
        self.game = game

    def add_counters(self, card: 'Card', counter_type: str, count: int = 1):
        """Add counters to a card"""
        if not hasattr(card, 'counters'):
            card.counters = {}

        current = card.counters.get(counter_type, 0)
        card.counters[counter_type] = current + count

        # Apply stat changes for +1/+1 and -1/-1 counters
        if counter_type == '+1/+1':
            card.current_atk += 100 * count
            card.current_def += 100 * count
        elif counter_type == '-1/-1':
            card.current_atk -= 100 * count
            card.current_def -= 100 * count

        self.game.emit_event('counters_added', {
            'card': card,
            'type': counter_type,
            'count': count,
        })

    def remove_counters(self, card: 'Card', counter_type: str, count: int = 1) -> int:
        """Remove counters from a card, returns actual removed"""
        if not hasattr(card, 'counters'):
            return 0

        current = card.counters.get(counter_type, 0)
        removed = min(current, count)
        card.counters[counter_type] = current - removed

        # Apply stat changes
        if counter_type == '+1/+1':
            card.current_atk -= 100 * removed
            card.current_def -= 100 * removed
        elif counter_type == '-1/-1':
            card.current_atk += 100 * removed
            card.current_def += 100 * removed

        self.game.emit_event('counters_removed', {
            'card': card,
            'type': counter_type,
            'count': removed,
        })

        return removed

    def get_counters(self, card: 'Card', counter_type: str) -> int:
        """Get counter count on a card"""
        if not hasattr(card, 'counters'):
            return 0
        return card.counters.get(counter_type, 0)

    def has_counters(self, card: 'Card', counter_type: str, minimum: int = 1) -> bool:
        """Check if card has at least N counters"""
        return self.get_counters(card, counter_type) >= minimum

    def move_counters(self, from_card: 'Card', to_card: 'Card',
                     counter_type: str, count: int = 1) -> int:
        """Move counters from one card to another"""
        removed = self.remove_counters(from_card, counter_type, count)
        if removed > 0:
            self.add_counters(to_card, counter_type, removed)
        return removed


# =============================================================================
# COMMON COUNTER OPERATIONS
# =============================================================================

def add_plus_counter(game: 'GameEngine', card: 'Card', count: int = 1):
    """Add +1/+1 counter(s)"""
    game.counter_manager.add_counters(card, '+1/+1', count)


def add_minus_counter(game: 'GameEngine', card: 'Card', count: int = 1):
    """Add -1/-1 counter(s)"""
    game.counter_manager.add_counters(card, '-1/-1', count)


def remove_plus_counter(game: 'GameEngine', card: 'Card', count: int = 1) -> int:
    """Remove +1/+1 counter(s)"""
    return game.counter_manager.remove_counters(card, '+1/+1', count)


def remove_minus_counter(game: 'GameEngine', card: 'Card', count: int = 1) -> int:
    """Remove -1/-1 counter(s)"""
    return game.counter_manager.remove_counters(card, '-1/-1', count)
