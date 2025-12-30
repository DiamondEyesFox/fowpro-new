"""
Targeting system based on Force of Will Comprehensive Rules.

References:
- CR 903.2i: Targeting requirements
- CR 1014: Choose/Look/Search
- CR 1120: [Barrier] - targeting restrictions
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Optional, Set, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from ..models import Card, Attribute, CardType


class TargetZone(Enum):
    """Zones that can be targeted."""
    FIELD = "field"
    HAND = "hand"
    GRAVEYARD = "graveyard"
    DECK = "deck"
    MAGIC_STONE_DECK = "magic_stone_deck"
    REMOVED = "removed"
    CHASE = "chase"
    RULER_AREA = "ruler_area"
    STANDBY = "standby"
    ANY = "any"


class TargetController(Enum):
    """Who controls the target."""
    YOU = "you"
    OPPONENT = "opponent"
    ANY = "any"
    OWNER = "owner"  # For cards that refer to owner vs controller


@dataclass
class TargetFilter:
    """
    Filter for what can be targeted.

    CR 903.2i: The player chooses appropriate targets for the card or ability.
    """
    # Zone restrictions
    zones: List[TargetZone] = field(default_factory=lambda: [TargetZone.FIELD])

    # Controller restrictions
    controllers: List[TargetController] = field(default_factory=lambda: [TargetController.ANY])

    # Card type restrictions (J/resonator, spell, magic stone, etc.)
    card_types: Optional[List[str]] = None

    # Attribute restrictions
    attributes: Optional[List[str]] = None
    exclude_attributes: Optional[List[str]] = None

    # Race/trait restrictions
    races: Optional[List[str]] = None

    # Keyword restrictions
    has_keywords: Optional[List[str]] = None
    lacks_keywords: Optional[List[str]] = None

    # Stat restrictions
    min_atk: Optional[int] = None
    max_atk: Optional[int] = None
    min_def: Optional[int] = None
    max_def: Optional[int] = None
    min_total_cost: Optional[int] = None
    max_total_cost: Optional[int] = None

    # State restrictions
    is_rested: Optional[bool] = None
    is_recovered: Optional[bool] = None
    has_damage: Optional[bool] = None

    # Name restrictions
    name_contains: Optional[str] = None
    name_exact: Optional[str] = None
    name_not: Optional[str] = None

    # Special restrictions
    is_token: Optional[bool] = None
    is_addition: Optional[bool] = None
    can_be_targeted: bool = True  # For barrier checking

    # Custom filter function for complex conditions
    custom_filter: Optional[Callable] = None

    def matches(self, card: 'Card', controller: int, source_controller: int) -> bool:
        """
        Check if a card matches this filter.

        Args:
            card: The card to check
            controller: The controller of the card being checked
            source_controller: The controller of the targeting ability

        Returns:
            True if the card matches all filter criteria
        """
        # Check zone (handled externally, but validate if needed)

        # Check controller
        if self.controllers and TargetController.ANY not in self.controllers:
            if TargetController.YOU in self.controllers and controller != source_controller:
                return False
            if TargetController.OPPONENT in self.controllers and controller == source_controller:
                return False

        # Check card type
        if self.card_types:
            card_type_str = card.data.card_type.value if card.data else None
            if card_type_str not in self.card_types:
                # Check for J/resonator
                if "j_resonator" in self.card_types:
                    if card_type_str not in ("resonator", "j_ruler"):
                        return False
                else:
                    return False

        # Check attributes
        if self.attributes:
            card_attr = card.data.attribute if card.data else None
            if card_attr:
                attr_name = card_attr.name.lower()
                if attr_name not in [a.lower() for a in self.attributes]:
                    return False
            else:
                return False

        if self.exclude_attributes:
            card_attr = card.data.attribute if card.data else None
            if card_attr:
                attr_name = card_attr.name.lower()
                if attr_name in [a.lower() for a in self.exclude_attributes]:
                    return False

        # Check races
        if self.races:
            card_races = card.data.race.split('/') if card.data and card.data.race else []
            card_races = [r.strip().lower() for r in card_races]
            if not any(r.lower() in card_races for r in self.races):
                return False

        # Check keywords
        if self.has_keywords:
            for kw in self.has_keywords:
                if not card.has_keyword_by_name(kw):
                    return False

        if self.lacks_keywords:
            for kw in self.lacks_keywords:
                if card.has_keyword_by_name(kw):
                    return False

        # Check stats
        if self.min_atk is not None and card.effective_atk < self.min_atk:
            return False
        if self.max_atk is not None and card.effective_atk > self.max_atk:
            return False
        if self.min_def is not None and card.effective_def < self.min_def:
            return False
        if self.max_def is not None and card.effective_def > self.max_def:
            return False

        # Check total cost
        if card.data and card.data.cost:
            total_cost = card.data.cost.total()
            if self.min_total_cost is not None and total_cost < self.min_total_cost:
                return False
            if self.max_total_cost is not None and total_cost > self.max_total_cost:
                return False

        # Check state
        if self.is_rested is not None and card.is_rested != self.is_rested:
            return False
        if self.is_recovered is not None and card.is_rested == self.is_recovered:
            return False

        # Check damage
        if self.has_damage is not None:
            has_dmg = card.damage > 0
            if has_dmg != self.has_damage:
                return False

        # Check name
        if self.name_contains and card.data:
            if self.name_contains.lower() not in card.data.name.lower():
                return False

        if self.name_exact and card.data:
            if card.data.name.lower() != self.name_exact.lower():
                return False

        if self.name_not and card.data:
            if card.data.name.lower() == self.name_not.lower():
                return False

        # Check special flags
        if self.is_token is not None and card.is_token != self.is_token:
            return False

        if self.is_addition is not None:
            is_add = card.data and card.data.card_type.value == "addition"
            if is_add != self.is_addition:
                return False

        # Check barrier (CR 1120)
        if self.can_be_targeted:
            if card.has_keyword_by_name("barrier"):
                if controller != source_controller:
                    return False

        # Custom filter
        if self.custom_filter:
            if not self.custom_filter(card, controller, source_controller):
                return False

        return True


@dataclass
class TargetRequirement:
    """
    Requirements for targeting per CR 903.2i.

    CR 903.2i: If that card or ability requires you to choose one or more
    targets, the player chooses appropriate targets for the card or ability
    at this time.
    """
    # How many targets
    count: int = 1

    # "up to X" vs "exactly X"
    up_to: bool = False

    # "any number" - no limit
    any_number: bool = False

    # The filter for valid targets
    filter: TargetFilter = field(default_factory=TargetFilter)

    # Whether this target is optional
    optional: bool = False

    # Label for UI
    label: str = "target"

    def validate_count(self, actual_count: int) -> bool:
        """Check if the number of targets is valid."""
        if self.any_number:
            return True
        if self.up_to:
            return 0 <= actual_count <= self.count
        if self.optional:
            return actual_count == 0 or actual_count == self.count
        return actual_count == self.count


# Common target filters for convenience
class CommonFilters:
    """Pre-built target filters for common patterns."""

    @staticmethod
    def j_resonator(controller: TargetController = TargetController.ANY) -> TargetFilter:
        """Target J/resonator."""
        return TargetFilter(
            card_types=["resonator", "j_ruler"],
            controllers=[controller]
        )

    @staticmethod
    def resonator(controller: TargetController = TargetController.ANY) -> TargetFilter:
        """Target resonator (not J-ruler)."""
        return TargetFilter(
            card_types=["resonator"],
            controllers=[controller]
        )

    @staticmethod
    def opponent_j_resonator() -> TargetFilter:
        """Target J/resonator opponent controls."""
        return TargetFilter(
            card_types=["resonator", "j_ruler"],
            controllers=[TargetController.OPPONENT]
        )

    @staticmethod
    def your_j_resonator() -> TargetFilter:
        """Target J/resonator you control."""
        return TargetFilter(
            card_types=["resonator", "j_ruler"],
            controllers=[TargetController.YOU]
        )

    @staticmethod
    def magic_stone(controller: TargetController = TargetController.ANY) -> TargetFilter:
        """Target magic stone."""
        return TargetFilter(
            card_types=["magic_stone"],
            controllers=[controller]
        )

    @staticmethod
    def addition(controller: TargetController = TargetController.ANY) -> TargetFilter:
        """Target addition."""
        return TargetFilter(
            card_types=["addition"],
            controllers=[controller]
        )

    @staticmethod
    def spell_on_chase() -> TargetFilter:
        """Target spell on the chase."""
        return TargetFilter(
            zones=[TargetZone.CHASE],
            card_types=["chant", "resonator", "addition", "regalia"]
        )

    @staticmethod
    def player() -> TargetFilter:
        """Target player (handled specially)."""
        return TargetFilter(controllers=[TargetController.ANY])

    @staticmethod
    def by_race(race: str, controller: TargetController = TargetController.ANY) -> TargetFilter:
        """Target by race."""
        return TargetFilter(
            card_types=["resonator", "j_ruler"],
            races=[race],
            controllers=[controller]
        )

    @staticmethod
    def by_attribute(attribute: str, controller: TargetController = TargetController.ANY) -> TargetFilter:
        """Target by attribute."""
        return TargetFilter(
            attributes=[attribute],
            controllers=[controller]
        )

    @staticmethod
    def by_total_cost(max_cost: int, controller: TargetController = TargetController.ANY) -> TargetFilter:
        """Target by total cost."""
        return TargetFilter(
            max_total_cost=max_cost,
            controllers=[controller]
        )
