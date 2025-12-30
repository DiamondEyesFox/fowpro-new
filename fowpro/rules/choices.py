"""
Choice System for Force of Will - UI Integration.

Handles all player choices during gameplay:
- Modal choices ("Choose one", "Choose two")
- Target selection (with validation)
- X value determination
- Optional effects ("You may")
- Distribution choices ("Divide X damage among...")
- Order choices ("Put in any order")

References:
- CR 903.2g: Modal choices
- CR 903.2h-k: Target selection
- CR 903.2j-1: X value determination
- CR 903.2j-2: Distribution
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import TYPE_CHECKING, List, Optional, Dict, Callable, Any, Union, Tuple

if TYPE_CHECKING:
    from ..engine import GameEngine
    from ..models import Card

from .targeting import TargetRequirement, TargetFilter
from .modals import ModalChoice, Mode


class ChoiceType(Enum):
    """Types of choices players can make."""
    MODAL = "modal"                  # Choose one or more modes
    TARGET = "target"                # Select targets
    X_VALUE = "x_value"              # Choose X value
    YES_NO = "yes_no"                # "You may" decision
    DISTRIBUTION = "distribution"    # Divide among targets
    ORDER = "order"                  # Arrange cards/effects
    CARD_FROM_LIST = "card_from_list"  # Select from revealed cards
    NUMBER = "number"                # Choose a number
    ATTRIBUTE = "attribute"          # Choose an attribute
    CARD_TYPE = "card_type"          # Choose a card type


class ChoiceState(Enum):
    """State of a pending choice."""
    PENDING = "pending"      # Waiting for player input
    RESOLVED = "resolved"    # Player made choice
    CANCELLED = "cancelled"  # Choice was cancelled (ability countered, etc.)
    TIMED_OUT = "timed_out"  # Time limit reached (in timed games)


@dataclass
class Choice:
    """
    A pending choice for a player to make.

    CR 903.2: Choices made during play process.
    """
    # Unique ID
    choice_id: str = ""

    # What type of choice
    choice_type: ChoiceType = ChoiceType.YES_NO

    # Player who must choose
    player: int = 0

    # Source card/ability that caused this choice
    source_id: str = ""
    source_name: str = ""

    # Prompt to display
    prompt: str = ""

    # Current state
    state: ChoiceState = ChoiceState.PENDING

    # The result once resolved
    result: Any = None

    # ====== Type-specific data ======

    # For MODAL choices
    modal_choice: Optional[ModalChoice] = None

    # For TARGET choices
    target_requirements: List[TargetRequirement] = field(default_factory=list)
    valid_targets: List['Card'] = field(default_factory=list)
    min_targets: int = 1
    max_targets: int = 1

    # For X_VALUE choices
    min_x: int = 0
    max_x: int = 99  # Practical maximum
    x_description: str = ""

    # For DISTRIBUTION choices
    total_to_distribute: int = 0
    distribute_targets: List['Card'] = field(default_factory=list)
    min_per_target: int = 0
    max_per_target: int = 99

    # For ORDER choices
    items_to_order: List[Any] = field(default_factory=list)

    # For CARD_FROM_LIST choices
    card_list: List['Card'] = field(default_factory=list)
    select_count: int = 1
    select_up_to: bool = False

    # For NUMBER choices
    min_number: int = 0
    max_number: int = 99
    number_description: str = ""

    # For ATTRIBUTE choices
    attribute_options: List[str] = field(default_factory=list)

    # For CARD_TYPE choices
    type_options: List[str] = field(default_factory=list)

    # Callback when choice is made
    on_choice: Optional[Callable] = None

    # Whether this choice is mandatory
    is_mandatory: bool = True

    def resolve(self, result: Any) -> bool:
        """
        Resolve this choice with the given result.

        Returns True if valid, False if rejected.
        """
        if self.state != ChoiceState.PENDING:
            return False

        # Validate based on type
        if not self._validate_result(result):
            return False

        self.result = result
        self.state = ChoiceState.RESOLVED

        if self.on_choice:
            self.on_choice(result)

        return True

    def _validate_result(self, result: Any) -> bool:
        """Validate the result for this choice type."""
        if self.choice_type == ChoiceType.YES_NO:
            return isinstance(result, bool)

        elif self.choice_type == ChoiceType.MODAL:
            if not isinstance(result, list):
                return False
            # Validation is handled by ModalChoice.validate_choices

        elif self.choice_type == ChoiceType.TARGET:
            if not isinstance(result, list):
                return False
            count = len(result)
            return self.min_targets <= count <= self.max_targets

        elif self.choice_type == ChoiceType.X_VALUE:
            if not isinstance(result, int):
                return False
            return self.min_x <= result <= self.max_x

        elif self.choice_type == ChoiceType.DISTRIBUTION:
            if not isinstance(result, dict):
                return False
            total = sum(result.values())
            if total != self.total_to_distribute:
                return False
            for target_id, amount in result.items():
                if amount < self.min_per_target or amount > self.max_per_target:
                    return False

        elif self.choice_type == ChoiceType.ORDER:
            if not isinstance(result, list):
                return False
            return len(result) == len(self.items_to_order)

        elif self.choice_type == ChoiceType.CARD_FROM_LIST:
            if not isinstance(result, list):
                return False
            count = len(result)
            if self.select_up_to:
                return count <= self.select_count
            return count == self.select_count

        elif self.choice_type == ChoiceType.NUMBER:
            if not isinstance(result, int):
                return False
            return self.min_number <= result <= self.max_number

        elif self.choice_type == ChoiceType.ATTRIBUTE:
            return result in self.attribute_options

        elif self.choice_type == ChoiceType.CARD_TYPE:
            return result in self.type_options

        return True

    def cancel(self):
        """Cancel this choice (e.g., source was countered)."""
        self.state = ChoiceState.CANCELLED


class ChoiceManager:
    """
    Manages player choices and UI integration.

    This is the bridge between game rules and the UI.
    """

    def __init__(self, game: 'GameEngine'):
        self.game = game

        # All pending choices
        self.pending_choices: Dict[str, Choice] = {}

        # Choice counter for unique IDs
        self._choice_counter = 0

        # UI callback for presenting choices
        self._ui_callback: Optional[Callable] = None

    def set_ui_callback(self, callback: Callable[[Choice], Any]):
        """
        Set the callback for presenting choices to the UI.

        The callback receives a Choice and should return the player's selection.
        For async UIs, this might return a future/promise.
        """
        self._ui_callback = callback

    def create_choice(self, choice_type: ChoiceType, player: int,
                      source: 'Card' = None, **kwargs) -> Choice:
        """Create a new choice for a player."""
        self._choice_counter += 1
        choice_id = f"choice_{self._choice_counter:06d}"

        choice = Choice(
            choice_id=choice_id,
            choice_type=choice_type,
            player=player,
            source_id=source.uid if source else "",
            source_name=source.data.name if source and source.data else "",
            **kwargs
        )

        self.pending_choices[choice_id] = choice
        return choice

    def request_choice(self, choice: Choice) -> Any:
        """
        Request a choice from the player.

        For AI, this uses the AI decision system.
        For human, this triggers the UI.

        Returns the result once available.
        """
        if self.game.is_ai_player(choice.player):
            # AI makes choice automatically
            result = self._ai_make_choice(choice)
            choice.resolve(result)
            return result
        else:
            # Human choice through UI
            if self._ui_callback:
                result = self._ui_callback(choice)
                if result is not None:
                    choice.resolve(result)
                return choice.result
            else:
                # No UI - default to first valid option
                result = self._get_default_choice(choice)
                choice.resolve(result)
                return result

    def _ai_make_choice(self, choice: Choice) -> Any:
        """Let AI make a choice."""
        # Simple AI: choose first valid option
        return self._get_default_choice(choice)

    def _get_default_choice(self, choice: Choice) -> Any:
        """Get the default/first valid choice."""
        if choice.choice_type == ChoiceType.YES_NO:
            return True if choice.is_mandatory else False

        elif choice.choice_type == ChoiceType.MODAL:
            if choice.modal_choice:
                available = choice.modal_choice.get_available_modes(
                    self.game, self.game.get_card(choice.source_id), choice.player
                )
                if available:
                    return [choice.modal_choice.modes.index(available[0])]
            return [0]

        elif choice.choice_type == ChoiceType.TARGET:
            if choice.valid_targets:
                return choice.valid_targets[:choice.min_targets]
            return []

        elif choice.choice_type == ChoiceType.X_VALUE:
            return choice.min_x

        elif choice.choice_type == ChoiceType.DISTRIBUTION:
            if choice.distribute_targets:
                # Distribute evenly, then remainder to first
                count = len(choice.distribute_targets)
                per_target = choice.total_to_distribute // count
                remainder = choice.total_to_distribute % count
                result = {}
                for i, target in enumerate(choice.distribute_targets):
                    amount = per_target + (1 if i < remainder else 0)
                    result[target.uid] = amount
                return result
            return {}

        elif choice.choice_type == ChoiceType.ORDER:
            return list(choice.items_to_order)  # Keep original order

        elif choice.choice_type == ChoiceType.CARD_FROM_LIST:
            if choice.card_list:
                return choice.card_list[:choice.select_count]
            return []

        elif choice.choice_type == ChoiceType.NUMBER:
            return choice.min_number

        elif choice.choice_type == ChoiceType.ATTRIBUTE:
            if choice.attribute_options:
                return choice.attribute_options[0]
            return ""

        elif choice.choice_type == ChoiceType.CARD_TYPE:
            if choice.type_options:
                return choice.type_options[0]
            return ""

        return None

    def cleanup_choice(self, choice_id: str):
        """Remove a resolved or cancelled choice."""
        if choice_id in self.pending_choices:
            del self.pending_choices[choice_id]

    def cancel_choices_from_source(self, source_id: str):
        """Cancel all pending choices from a source (e.g., countered spell)."""
        for choice in self.pending_choices.values():
            if choice.source_id == source_id:
                choice.cancel()

    # ====== High-level choice helpers ======

    def request_modal_choice(self, player: int, source: 'Card',
                             modal: ModalChoice) -> List[int]:
        """
        Request a modal choice from the player.

        Returns list of chosen mode indices.
        """
        choice = self.create_choice(
            ChoiceType.MODAL,
            player,
            source,
            prompt=modal.prompt,
            modal_choice=modal,
        )

        result = self.request_choice(choice)
        self.cleanup_choice(choice.choice_id)
        return result or []

    def request_targets(self, player: int, source: 'Card',
                        requirements: List[TargetRequirement],
                        prompt: str = "Choose targets") -> List['Card']:
        """
        Request target selection from the player.

        Returns list of selected targets.
        """
        # Get all valid targets
        valid = []
        for req in requirements:
            if req.filter:
                for p in self.game.players:
                    for card in p.field:
                        if req.filter.matches(card, card.controller, player):
                            if card not in valid:
                                valid.append(card)

        # Calculate min/max
        min_targets = sum(r.count for r in requirements if not r.up_to)
        max_targets = sum(r.count for r in requirements)

        choice = self.create_choice(
            ChoiceType.TARGET,
            player,
            source,
            prompt=prompt,
            target_requirements=requirements,
            valid_targets=valid,
            min_targets=min_targets,
            max_targets=max_targets,
        )

        result = self.request_choice(choice)
        self.cleanup_choice(choice.choice_id)
        return result or []

    def request_yes_no(self, player: int, source: 'Card',
                       prompt: str, mandatory: bool = False) -> bool:
        """
        Request a yes/no choice from the player.

        For "You may" effects.
        """
        choice = self.create_choice(
            ChoiceType.YES_NO,
            player,
            source,
            prompt=prompt,
            is_mandatory=mandatory,
        )

        result = self.request_choice(choice)
        self.cleanup_choice(choice.choice_id)
        return result or False

    def request_x_value(self, player: int, source: 'Card',
                        min_x: int = 0, max_x: int = None,
                        description: str = "Choose X") -> int:
        """
        Request an X value from the player.

        max_x defaults to available will if not specified.
        """
        if max_x is None:
            # Calculate based on available will
            will_pool = self.game.get_will_pool(player)
            max_x = sum(will_pool.values())

        choice = self.create_choice(
            ChoiceType.X_VALUE,
            player,
            source,
            prompt=description,
            min_x=min_x,
            max_x=max_x,
            x_description=description,
        )

        result = self.request_choice(choice)
        self.cleanup_choice(choice.choice_id)
        return result or 0

    def request_distribution(self, player: int, source: 'Card',
                             total: int, targets: List['Card'],
                             description: str = "Distribute",
                             min_per: int = 0) -> Dict[str, int]:
        """
        Request a distribution among targets.

        For effects like "Divide 5 damage among up to 3 targets".
        """
        choice = self.create_choice(
            ChoiceType.DISTRIBUTION,
            player,
            source,
            prompt=description,
            total_to_distribute=total,
            distribute_targets=targets,
            min_per_target=min_per,
            max_per_target=total,
        )

        result = self.request_choice(choice)
        self.cleanup_choice(choice.choice_id)
        return result or {}

    def request_card_from_list(self, player: int, source: 'Card',
                               cards: List['Card'], count: int = 1,
                               up_to: bool = False,
                               prompt: str = "Choose a card") -> List['Card']:
        """
        Request selection of cards from a list.

        For search effects, revealed cards, etc.
        """
        choice = self.create_choice(
            ChoiceType.CARD_FROM_LIST,
            player,
            source,
            prompt=prompt,
            card_list=cards,
            select_count=count,
            select_up_to=up_to,
        )

        result = self.request_choice(choice)
        self.cleanup_choice(choice.choice_id)
        return result or []

    def request_order(self, player: int, source: 'Card',
                      items: List[Any],
                      prompt: str = "Choose order") -> List[Any]:
        """
        Request ordering of items.

        For effects that let you arrange cards on top of deck, etc.
        """
        choice = self.create_choice(
            ChoiceType.ORDER,
            player,
            source,
            prompt=prompt,
            items_to_order=items,
        )

        result = self.request_choice(choice)
        self.cleanup_choice(choice.choice_id)
        return result or items

    def request_attribute(self, player: int, source: 'Card',
                          options: List[str] = None,
                          prompt: str = "Choose an attribute") -> str:
        """
        Request an attribute choice.

        For effects like "Choose Light or Darkness".
        """
        if options is None:
            options = ['Light', 'Fire', 'Water', 'Wind', 'Darkness']

        choice = self.create_choice(
            ChoiceType.ATTRIBUTE,
            player,
            source,
            prompt=prompt,
            attribute_options=options,
        )

        result = self.request_choice(choice)
        self.cleanup_choice(choice.choice_id)
        return result or options[0]

    def request_card_type(self, player: int, source: 'Card',
                          options: List[str],
                          prompt: str = "Choose a card type") -> str:
        """
        Request a card type choice.

        For effects like "Choose resonator or addition".
        """
        choice = self.create_choice(
            ChoiceType.CARD_TYPE,
            player,
            source,
            prompt=prompt,
            type_options=options,
        )

        result = self.request_choice(choice)
        self.cleanup_choice(choice.choice_id)
        return result or options[0]


# UI Message structures for integration
@dataclass
class ChoiceUIMessage:
    """
    Message to send to UI for choice presentation.

    Can be serialized to JSON for network/IPC.
    """
    choice_id: str
    choice_type: str
    player: int
    source_name: str
    prompt: str

    # Options for the choice
    options: List[Dict[str, Any]] = field(default_factory=list)

    # Constraints
    min_selections: int = 1
    max_selections: int = 1
    is_mandatory: bool = True

    @classmethod
    def from_choice(cls, choice: Choice) -> 'ChoiceUIMessage':
        """Create a UI message from a Choice."""
        options = []

        if choice.choice_type == ChoiceType.MODAL and choice.modal_choice:
            for i, mode in enumerate(choice.modal_choice.modes):
                options.append({
                    'id': i,
                    'name': mode.name,
                    'description': mode.description,
                })

        elif choice.choice_type == ChoiceType.TARGET:
            for card in choice.valid_targets:
                options.append({
                    'id': card.uid,
                    'name': card.data.name if card.data else "Unknown",
                    'zone': str(card.zone),
                    'controller': card.controller,
                })

        elif choice.choice_type == ChoiceType.CARD_FROM_LIST:
            for card in choice.card_list:
                options.append({
                    'id': card.uid,
                    'name': card.data.name if card.data else "Unknown",
                })

        elif choice.choice_type == ChoiceType.ATTRIBUTE:
            for attr in choice.attribute_options:
                options.append({
                    'id': attr,
                    'name': attr,
                })

        elif choice.choice_type == ChoiceType.CARD_TYPE:
            for ct in choice.type_options:
                options.append({
                    'id': ct,
                    'name': ct,
                })

        elif choice.choice_type == ChoiceType.YES_NO:
            options = [
                {'id': True, 'name': 'Yes'},
                {'id': False, 'name': 'No'},
            ]

        return cls(
            choice_id=choice.choice_id,
            choice_type=choice.choice_type.value,
            player=choice.player,
            source_name=choice.source_name,
            prompt=choice.prompt,
            options=options,
            min_selections=choice.min_targets if choice.choice_type == ChoiceType.TARGET else 1,
            max_selections=choice.max_targets if choice.choice_type == ChoiceType.TARGET else 1,
            is_mandatory=choice.is_mandatory,
        )
