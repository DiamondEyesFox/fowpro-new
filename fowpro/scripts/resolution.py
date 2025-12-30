"""
Effect Resolution System
========================

Handles complex effect resolution including:
- Modal effects (choose one/two)
- X costs
- For each effects
- Replacement effects
- Prevention effects
- Conditional effects
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Callable, Optional, List, Dict, Any, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from ..engine import GameEngine
    from ..models import Card, Player


class ChoiceType(Enum):
    """Types of choices in modal effects"""
    ONE = auto()        # Choose one
    TWO = auto()        # Choose two
    ANY = auto()        # Choose any number
    ALL = auto()        # Do all (no choice)


@dataclass
class EffectMode:
    """A mode for modal effects"""
    name: str
    description: str
    operation: Callable[['GameEngine', 'Card', Dict], None]
    condition: Optional[Callable[['GameEngine', 'Card'], bool]] = None


@dataclass
class ModalEffect:
    """A modal 'choose X' effect"""
    modes: List[EffectMode]
    choice_type: ChoiceType = ChoiceType.ONE
    prompt: str = "Choose"


class EffectResolver:
    """Handles complex effect resolution"""

    def __init__(self, game: 'GameEngine'):
        self.game = game
        self._ui_callback: Optional[Callable] = None
        self._pending_choice: Optional['ChoiceRequest'] = None

    def set_ui_callback(self, callback: Callable):
        """Set UI callback for choices"""
        self._ui_callback = callback

    # =========================================================================
    # MODAL EFFECTS
    # =========================================================================

    def resolve_modal(self, source: 'Card', modal: ModalEffect,
                     effect_data: Dict,
                     callback: Callable[[], None]):
        """Resolve a modal effect with player choice"""
        # Filter available modes by conditions
        available = []
        for mode in modal.modes:
            if mode.condition is None or mode.condition(self.game, source):
                available.append(mode)

        if not available:
            callback()
            return

        # Determine how many to choose
        if modal.choice_type == ChoiceType.ONE:
            min_choose, max_choose = 1, 1
        elif modal.choice_type == ChoiceType.TWO:
            min_choose, max_choose = 2, min(2, len(available))
        elif modal.choice_type == ChoiceType.ANY:
            min_choose, max_choose = 0, len(available)
        else:  # ALL
            # Execute all modes
            for mode in available:
                mode.operation(self.game, source, effect_data)
            callback()
            return

        def on_chosen(mode_indices: List[int]):
            for idx in mode_indices:
                if 0 <= idx < len(available):
                    available[idx].operation(self.game, source, effect_data)
            callback()

        self._request_mode_choice(
            source, available, min_choose, max_choose,
            modal.prompt, on_chosen
        )

    def _request_mode_choice(self, source: 'Card',
                            modes: List[EffectMode],
                            min_choose: int, max_choose: int,
                            prompt: str,
                            callback: Callable[[List[int]], None]):
        """Request mode choice from UI"""
        if self._ui_callback:
            self._pending_choice = ChoiceRequest(
                type='mode',
                options=[m.description for m in modes],
                min_select=min_choose,
                max_select=max_choose,
                prompt=prompt,
                callback=callback,
            )
            self._ui_callback(self._pending_choice)
        else:
            # Auto: choose first N
            callback(list(range(min_choose)))

    # =========================================================================
    # X COSTS
    # =========================================================================

    def resolve_x_cost(self, source: 'Card', player: 'Player',
                      max_x: Optional[int],
                      callback: Callable[[int], None]):
        """Resolve an X value for cost or effect"""
        total_will = sum(player.will_pool.values())

        if max_x is not None:
            max_value = min(max_x, total_will)
        else:
            max_value = total_will

        if max_value == 0:
            callback(0)
            return

        def on_chosen(values: List[int]):
            x = values[0] if values else 0
            callback(x)

        self._request_number_choice(
            min_value=0,
            max_value=max_value,
            prompt=f"Choose value for X (0-{max_value})",
            callback=on_chosen,
        )

    def _request_number_choice(self, min_value: int, max_value: int,
                              prompt: str,
                              callback: Callable[[List[int]], None]):
        """Request number choice from UI"""
        if self._ui_callback:
            self._pending_choice = ChoiceRequest(
                type='number',
                min_value=min_value,
                max_value=max_value,
                prompt=prompt,
                callback=callback,
            )
            self._ui_callback(self._pending_choice)
        else:
            # Auto: choose max
            callback([max_value])

    # =========================================================================
    # FOR EACH EFFECTS
    # =========================================================================

    def for_each_resonator(self, player: 'Player',
                          operation: Callable[['Card'], None],
                          filter_fn: Optional[Callable[['Card'], bool]] = None):
        """Execute operation for each resonator"""
        for card in list(player.field):
            if not card.data or not card.data.is_resonator():
                continue
            if filter_fn and not filter_fn(card):
                continue
            operation(card)

    def for_each_card_in_graveyard(self, player: 'Player',
                                  operation: Callable[['Card'], None],
                                  filter_fn: Optional[Callable[['Card'], bool]] = None):
        """Execute operation for each card in graveyard"""
        for card in list(player.graveyard):
            if filter_fn and not filter_fn(card):
                continue
            operation(card)

    def count_cards(self, zone_getter: Callable[[], List['Card']],
                   filter_fn: Optional[Callable[['Card'], bool]] = None) -> int:
        """Count cards matching filter in a zone"""
        cards = zone_getter()
        if filter_fn:
            cards = [c for c in cards if filter_fn(c)]
        return len(cards)

    def for_each_count(self, count: int,
                      operation: Callable[[int], None]):
        """Execute operation N times"""
        for i in range(count):
            operation(i)

    # =========================================================================
    # REPLACEMENT EFFECTS
    # =========================================================================

    def apply_replacement(self, event_type: str, event_data: Dict,
                         replacement_fn: Callable[[Dict], Dict]) -> Dict:
        """Apply a replacement effect to an event"""
        # Check for applicable replacement effects
        replaced_data = replacement_fn(event_data.copy())
        return replaced_data

    def replace_damage(self, source: 'Card', target: Union['Card', 'Player'],
                      amount: int,
                      replacement_fn: Callable[[int], int]) -> int:
        """Replace damage amount"""
        return replacement_fn(amount)

    def prevent_damage(self, target: Union['Card', 'Player'],
                      amount: int, prevention_amount: int) -> int:
        """Prevent up to N damage"""
        prevented = min(amount, prevention_amount)
        return amount - prevented

    def redirect_damage(self, original_target: Union['Card', 'Player'],
                       new_target: Union['Card', 'Player'],
                       amount: int) -> tuple:
        """Redirect damage to a different target"""
        return (new_target, amount)

    # =========================================================================
    # CONDITIONAL EFFECTS
    # =========================================================================

    def if_then_else(self, condition: bool,
                    if_operation: Callable[[], None],
                    else_operation: Optional[Callable[[], None]] = None):
        """Execute conditional effect"""
        if condition:
            if_operation()
        elif else_operation:
            else_operation()

    def check_threshold(self, value: int, threshold: int,
                       comparison: str = '>=') -> bool:
        """Check a threshold condition"""
        if comparison == '>=':
            return value >= threshold
        elif comparison == '>':
            return value > threshold
        elif comparison == '<=':
            return value <= threshold
        elif comparison == '<':
            return value < threshold
        elif comparison == '==':
            return value == threshold
        return False

    # =========================================================================
    # RANDOM EFFECTS
    # =========================================================================

    def random_choice(self, options: List[Any]) -> Any:
        """Make a random choice"""
        import random
        if not options:
            return None
        return random.choice(options)

    def coin_flip(self, callback: Callable[[bool], None]):
        """Flip a coin (returns True for heads)"""
        import random
        result = random.choice([True, False])

        self.game.emit_event('coin_flip', {
            'result': 'heads' if result else 'tails',
        })

        callback(result)

    def die_roll(self, sides: int = 6) -> int:
        """Roll a die"""
        import random
        result = random.randint(1, sides)

        self.game.emit_event('die_roll', {
            'sides': sides,
            'result': result,
        })

        return result

    # =========================================================================
    # UI INTERACTION
    # =========================================================================

    def submit_choice(self, values: List[Any]):
        """Called by UI when player makes a choice"""
        if not self._pending_choice:
            return

        req = self._pending_choice
        self._pending_choice = None
        req.callback(values)


@dataclass
class ChoiceRequest:
    """Request for UI to present a choice"""
    type: str  # 'mode', 'number', 'card'
    callback: Callable[[List[Any]], None]
    prompt: str = "Choose"

    # For mode choices
    options: List[str] = field(default_factory=list)
    min_select: int = 1
    max_select: int = 1

    # For number choices
    min_value: int = 0
    max_value: int = 0


# =============================================================================
# MODAL EFFECT BUILDERS
# =============================================================================

def choose_one(*modes: tuple) -> ModalEffect:
    """Create a 'choose one' modal effect"""
    effect_modes = [
        EffectMode(name=name, description=desc, operation=op)
        for name, desc, op in modes
    ]
    return ModalEffect(modes=effect_modes, choice_type=ChoiceType.ONE)


def choose_two(*modes: tuple) -> ModalEffect:
    """Create a 'choose two' modal effect"""
    effect_modes = [
        EffectMode(name=name, description=desc, operation=op)
        for name, desc, op in modes
    ]
    return ModalEffect(modes=effect_modes, choice_type=ChoiceType.TWO)


def do_both(*operations: Callable) -> Callable:
    """Create operation that does multiple things"""
    def combined(game, source, data):
        for op in operations:
            op(game, source, data)
    return combined


# =============================================================================
# COMMON CONDITIONS
# =============================================================================

def if_you_control_resonator(game: 'GameEngine', source: 'Card') -> bool:
    """Check if controller has any resonator"""
    player = game.players[source.controller]
    return any(c.data and c.data.is_resonator() for c in player.field)


def if_opponent_controls_resonator(game: 'GameEngine', source: 'Card') -> bool:
    """Check if opponent has any resonator"""
    opponent = game.players[1 - source.controller]
    return any(c.data and c.data.is_resonator() for c in opponent.field)


def if_graveyard_has_cards(count: int) -> Callable:
    """Check if graveyard has at least N cards"""
    def check(game: 'GameEngine', source: 'Card') -> bool:
        player = game.players[source.controller]
        return len(player.graveyard) >= count
    return check


def if_life_at_or_below(threshold: int) -> Callable:
    """Check if life is at or below threshold"""
    def check(game: 'GameEngine', source: 'Card') -> bool:
        player = game.players[source.controller]
        return player.life <= threshold
    return check


def if_hand_has_cards(count: int) -> Callable:
    """Check if hand has at least N cards"""
    def check(game: 'GameEngine', source: 'Card') -> bool:
        player = game.players[source.controller]
        return len(player.hand) >= count
    return check
