"""
Modal effects system for Force of Will.

Handles "choose one", "choose up to X", and similar modal effects.

References:
- CR 903.2g: Modal choices
- CR 903.2j: Determining modes and values
"""

from dataclasses import dataclass, field
from typing import List, Optional, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from ..engine import GameEngine
    from ..models import Card


@dataclass
class Mode:
    """
    A single mode option in a modal effect.

    CR 903.2g: If the card or ability has modes, the player chooses
    the mode(s) to perform at this time.
    """
    # Display name for the mode
    name: str

    # Description of what this mode does
    description: str

    # The effect operation to execute
    operation: Callable[['GameEngine', 'Card', dict], None]

    # Condition that must be met to choose this mode (optional)
    condition: Optional[Callable[['GameEngine', 'Card', int], bool]] = None

    # Whether this mode requires a target
    requires_target: bool = False

    # Target requirements if needed
    target_params: Optional[dict] = None

    def can_choose(self, game: 'GameEngine', card: 'Card', player: int) -> bool:
        """Check if this mode can be chosen."""
        if self.condition:
            return self.condition(game, card, player)
        return True


@dataclass
class ModalChoice:
    """
    A modal choice structure for effects with multiple options.

    CR 903.2g: The player chooses the mode(s) to perform.
    CR 903.2j-1: If any value is to be chosen, it is chosen at this time.
    """
    # Available modes
    modes: List[Mode] = field(default_factory=list)

    # How many modes to choose (1 = "choose one", 2 = "choose two", etc.)
    choose_count: int = 1

    # Whether to choose "up to" or "exactly"
    up_to: bool = False

    # Whether the same mode can be chosen multiple times
    allow_same: bool = False

    # Description for UI
    prompt: str = "Choose a mode"

    def get_available_modes(self, game: 'GameEngine', card: 'Card', player: int) -> List[Mode]:
        """Get all modes that can be chosen."""
        return [m for m in self.modes if m.can_choose(game, card, player)]

    def validate_choices(self, chosen_indices: List[int], game: 'GameEngine',
                         card: 'Card', player: int) -> bool:
        """
        Validate that the chosen modes are legal.

        CR 903.2g: Modes must be chosen legally.
        """
        # Check count
        if self.up_to:
            if len(chosen_indices) > self.choose_count:
                return False
        else:
            if len(chosen_indices) != self.choose_count:
                return False

        # Check for duplicates if not allowed
        if not self.allow_same:
            if len(chosen_indices) != len(set(chosen_indices)):
                return False

        # Check each mode is valid
        available = self.get_available_modes(game, card, player)
        available_indices = [self.modes.index(m) for m in available]

        for idx in chosen_indices:
            if idx not in available_indices:
                return False

        return True


# Common modal patterns
class ModalPatterns:
    """Pre-built modal patterns for common card effects."""

    @staticmethod
    def choose_one(*mode_configs) -> ModalChoice:
        """
        Create a "choose one" modal.

        Args:
            mode_configs: Tuples of (name, description, operation)
        """
        modes = [
            Mode(name=name, description=desc, operation=op)
            for name, desc, op in mode_configs
        ]
        return ModalChoice(
            modes=modes,
            choose_count=1,
            prompt="Choose one"
        )

    @staticmethod
    def choose_two(*mode_configs) -> ModalChoice:
        """Create a "choose two" modal."""
        modes = [
            Mode(name=name, description=desc, operation=op)
            for name, desc, op in mode_configs
        ]
        return ModalChoice(
            modes=modes,
            choose_count=2,
            prompt="Choose two"
        )

    @staticmethod
    def choose_up_to(count: int, *mode_configs) -> ModalChoice:
        """Create a "choose up to X" modal."""
        modes = [
            Mode(name=name, description=desc, operation=op)
            for name, desc, op in mode_configs
        ]
        return ModalChoice(
            modes=modes,
            choose_count=count,
            up_to=True,
            prompt=f"Choose up to {count}"
        )

    @staticmethod
    def choose_one_that_hasnt_been_chosen(*mode_configs) -> ModalChoice:
        """
        Create a modal where each mode can only be chosen once per game.
        Used for cards like Primogenitor abilities.
        """
        modes = [
            Mode(name=name, description=desc, operation=op)
            for name, desc, op in mode_configs
        ]
        return ModalChoice(
            modes=modes,
            choose_count=1,
            allow_same=False,
            prompt="Choose one that hasn't been chosen"
        )
