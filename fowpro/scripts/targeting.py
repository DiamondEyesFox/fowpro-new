"""
Targeting System
================

Handles target selection for spells and abilities.
Integrates with UI through callbacks for player selection.
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Callable, Optional, List, Set, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ..engine import GameEngine
    from ..models import Card, Player


class TargetZone(Enum):
    """Zones where targets can be selected"""
    FIELD = auto()
    HAND = auto()
    GRAVEYARD = auto()
    STONE_DECK = auto()
    MAIN_DECK = auto()
    REMOVED = auto()
    CHASE = auto()
    ANY = auto()


class TargetController(Enum):
    """Who controls valid targets"""
    YOU = auto()
    OPPONENT = auto()
    ANY = auto()


@dataclass
class TargetFilter:
    """Filter for valid targets"""
    zones: Set[TargetZone] = field(default_factory=lambda: {TargetZone.FIELD})
    controller: TargetController = TargetController.ANY

    # Card property filters
    is_resonator: Optional[bool] = None
    is_j_resonator: Optional[bool] = None
    is_spell: Optional[bool] = None
    is_stone: Optional[bool] = None
    is_addition: Optional[bool] = None
    is_ruler: Optional[bool] = None

    # Attribute filter
    attributes: Optional[Set[str]] = None

    # Stat filters
    min_atk: Optional[int] = None
    max_atk: Optional[int] = None
    min_def: Optional[int] = None
    max_def: Optional[int] = None

    # Cost filter
    max_total_cost: Optional[int] = None

    # Name filter
    name_contains: Optional[str] = None
    name_exact: Optional[str] = None

    # Keyword filter
    has_keyword: Optional[str] = None
    lacks_keyword: Optional[str] = None

    # State filters
    is_rested: Optional[bool] = None
    is_recovered: Optional[bool] = None

    # Custom filter
    custom: Optional[Callable[['Card'], bool]] = None

    def matches(self, card: 'Card', game: 'GameEngine',
                source_controller: int) -> bool:
        """Check if card matches all filters"""
        from ..models import Zone

        # Zone check
        if self.zones and TargetZone.ANY not in self.zones:
            zone_match = False
            for tz in self.zones:
                if tz == TargetZone.FIELD and card.zone == Zone.FIELD:
                    zone_match = True
                elif tz == TargetZone.HAND and card.zone == Zone.HAND:
                    zone_match = True
                elif tz == TargetZone.GRAVEYARD and card.zone == Zone.GRAVEYARD:
                    zone_match = True
                elif tz == TargetZone.REMOVED and card.zone == Zone.REMOVED:
                    zone_match = True
            if not zone_match:
                return False

        # Controller check
        if self.controller == TargetController.YOU:
            if card.controller != source_controller:
                return False
        elif self.controller == TargetController.OPPONENT:
            if card.controller == source_controller:
                return False

        # Card type checks
        if card.data:
            if self.is_resonator is not None:
                if card.data.is_resonator() != self.is_resonator:
                    return False

            if self.is_j_resonator is not None:
                is_j = 'J_RULER' in card.data.card_type.name or 'J_RESONATOR' in card.data.card_type.name
                if is_j != self.is_j_resonator:
                    return False

            if self.is_spell is not None:
                if card.data.is_spell() != self.is_spell:
                    return False

            if self.is_stone is not None:
                if card.data.is_stone() != self.is_stone:
                    return False

            if self.is_addition is not None:
                is_add = 'ADDITION' in card.data.card_type.name
                if is_add != self.is_addition:
                    return False

            # Attribute check
            if self.attributes:
                if not card.data.attribute:
                    return False
                if card.data.attribute.name.upper() not in {a.upper() for a in self.attributes}:
                    return False

            # Stat checks
            if self.min_atk is not None:
                if (card.current_atk or 0) < self.min_atk:
                    return False

            if self.max_atk is not None:
                if (card.current_atk or 0) > self.max_atk:
                    return False

            if self.min_def is not None:
                if (card.current_def or 0) < self.min_def:
                    return False

            if self.max_def is not None:
                if (card.current_def or 0) > self.max_def:
                    return False

            # Cost check
            if self.max_total_cost is not None:
                total = card.data.get_total_cost()
                if total > self.max_total_cost:
                    return False

            # Name checks
            if self.name_contains:
                if self.name_contains.lower() not in card.data.name.lower():
                    return False

            if self.name_exact:
                if card.data.name.lower() != self.name_exact.lower():
                    return False

        # State checks
        if self.is_rested is not None:
            if card.is_rested != self.is_rested:
                return False

        if self.is_recovered is not None:
            if card.is_rested == self.is_recovered:
                return False

        # Keyword check
        if self.has_keyword:
            if not hasattr(card, 'keyword_state'):
                return False
            from .keywords import TEXT_TO_KEYWORD
            kw = TEXT_TO_KEYWORD.get(self.has_keyword.lower())
            if kw and not card.keyword_state.has(kw):
                return False

        if self.lacks_keyword:
            if hasattr(card, 'keyword_state'):
                from .keywords import TEXT_TO_KEYWORD
                kw = TEXT_TO_KEYWORD.get(self.lacks_keyword.lower())
                if kw and card.keyword_state.has(kw):
                    return False

        # Custom filter
        if self.custom:
            if not self.custom(card):
                return False

        return True


@dataclass
class TargetRequirement:
    """Requirement for targeting"""
    filter: TargetFilter
    min_targets: int = 1
    max_targets: int = 1
    optional: bool = False          # If True, can choose 0 targets
    prompt: str = "Select a target"

    @property
    def is_single_target(self) -> bool:
        return self.min_targets == 1 and self.max_targets == 1


@dataclass
class TargetSelection:
    """Result of target selection"""
    targets: List['Card'] = field(default_factory=list)
    cancelled: bool = False         # Player cancelled targeting

    @property
    def target(self) -> Optional['Card']:
        """Get single target (for single-target effects)"""
        return self.targets[0] if self.targets else None


class TargetingManager:
    """Manages target selection for spells and abilities"""

    def __init__(self, game: 'GameEngine'):
        self.game = game
        self._pending_request: Optional[TargetRequest] = None
        self._ui_callback: Optional[Callable] = None

    def set_ui_callback(self, callback: Callable):
        """Set the UI callback for target selection"""
        self._ui_callback = callback

    def get_valid_targets(self, requirement: TargetRequirement,
                         source: 'Card') -> List['Card']:
        """Get all valid targets for a requirement"""
        valid = []
        source_controller = source.controller if source else 0

        for player in self.game.players:
            for card in player.get_all_cards():
                # Skip the source card
                if source and card.uid == source.uid:
                    continue

                # Check Barrier keyword
                from .keywords import KeywordProcessor
                kp = KeywordProcessor(self.game)
                if not kp.can_be_targeted(card, source_controller):
                    continue

                # Check filter
                if requirement.filter.matches(card, self.game, source_controller):
                    valid.append(card)

        return valid

    def has_valid_targets(self, requirement: TargetRequirement,
                         source: 'Card') -> bool:
        """Check if there are enough valid targets"""
        if requirement.optional:
            return True

        valid = self.get_valid_targets(requirement, source)
        return len(valid) >= requirement.min_targets

    def request_targets(self, requirement: TargetRequirement,
                       source: 'Card',
                       callback: Callable[[TargetSelection], None]):
        """Request target selection from UI"""
        valid = self.get_valid_targets(requirement, source)

        if len(valid) < requirement.min_targets and not requirement.optional:
            # Not enough valid targets
            callback(TargetSelection(cancelled=True))
            return

        if len(valid) == 1 and requirement.is_single_target and not requirement.optional:
            # Auto-select single valid target
            callback(TargetSelection(targets=[valid[0]]))
            return

        # Request from UI
        if self._ui_callback:
            self._pending_request = TargetRequest(
                requirement=requirement,
                valid_targets=valid,
                callback=callback,
            )
            self._ui_callback(self._pending_request)
        else:
            # No UI - auto-select first valid targets
            selected = valid[:requirement.min_targets]
            callback(TargetSelection(targets=selected))

    def submit_selection(self, target_ids: List[str]):
        """Called by UI when player selects targets"""
        if not self._pending_request:
            return

        req = self._pending_request
        self._pending_request = None

        # Find cards by ID
        targets = []
        for tid in target_ids:
            for card in req.valid_targets:
                if card.uid == tid:
                    targets.append(card)
                    break

        # Validate selection
        if len(targets) < req.requirement.min_targets:
            if req.requirement.optional:
                req.callback(TargetSelection(targets=[]))
            else:
                req.callback(TargetSelection(cancelled=True))
        else:
            req.callback(TargetSelection(targets=targets[:req.requirement.max_targets]))

    def cancel_selection(self):
        """Called by UI when player cancels targeting"""
        if self._pending_request:
            req = self._pending_request
            self._pending_request = None
            req.callback(TargetSelection(cancelled=True))


@dataclass
class TargetRequest:
    """Request for UI to show target selection"""
    requirement: TargetRequirement
    valid_targets: List['Card']
    callback: Callable[[TargetSelection], None]


# =============================================================================
# COMMON TARGET FILTERS
# =============================================================================

def target_resonator() -> TargetFilter:
    """Target any resonator on the field"""
    return TargetFilter(
        zones={TargetZone.FIELD},
        is_resonator=True,
    )


def target_j_resonator() -> TargetFilter:
    """Target any J-Resonator on the field"""
    return TargetFilter(
        zones={TargetZone.FIELD},
        is_j_resonator=True,
    )


def target_opponent_resonator() -> TargetFilter:
    """Target opponent's resonator"""
    return TargetFilter(
        zones={TargetZone.FIELD},
        controller=TargetController.OPPONENT,
        is_resonator=True,
    )


def target_your_resonator() -> TargetFilter:
    """Target your own resonator"""
    return TargetFilter(
        zones={TargetZone.FIELD},
        controller=TargetController.YOU,
        is_resonator=True,
    )


def target_spell_on_chase() -> TargetFilter:
    """Target spell on the chase"""
    return TargetFilter(
        zones={TargetZone.CHASE},
        is_spell=True,
    )


def target_stone() -> TargetFilter:
    """Target any magic stone"""
    return TargetFilter(
        zones={TargetZone.FIELD},
        is_stone=True,
    )


def target_addition() -> TargetFilter:
    """Target any addition"""
    return TargetFilter(
        zones={TargetZone.FIELD},
        is_addition=True,
    )


def target_card_in_graveyard(controller: TargetController = TargetController.ANY) -> TargetFilter:
    """Target card in graveyard"""
    return TargetFilter(
        zones={TargetZone.GRAVEYARD},
        controller=controller,
    )


def target_rested_resonator() -> TargetFilter:
    """Target rested resonator"""
    return TargetFilter(
        zones={TargetZone.FIELD},
        is_resonator=True,
        is_rested=True,
    )


def target_attribute_resonator(attribute: str) -> TargetFilter:
    """Target resonator with specific attribute"""
    return TargetFilter(
        zones={TargetZone.FIELD},
        is_resonator=True,
        attributes={attribute.upper()},
    )


def target_with_max_def(max_def: int) -> TargetFilter:
    """Target resonator with DEF <= X"""
    return TargetFilter(
        zones={TargetZone.FIELD},
        is_resonator=True,
        max_def=max_def,
    )


# =============================================================================
# TARGET REQUIREMENT BUILDERS
# =============================================================================

def single_target(filter: TargetFilter, prompt: str = "Select a target") -> TargetRequirement:
    """Create single-target requirement"""
    return TargetRequirement(
        filter=filter,
        min_targets=1,
        max_targets=1,
        prompt=prompt,
    )


def multiple_targets(filter: TargetFilter, count: int,
                    prompt: str = "Select targets") -> TargetRequirement:
    """Create multi-target requirement"""
    return TargetRequirement(
        filter=filter,
        min_targets=count,
        max_targets=count,
        prompt=prompt,
    )


def up_to_targets(filter: TargetFilter, max_count: int,
                 prompt: str = "Select up to X targets") -> TargetRequirement:
    """Create 'up to X' target requirement"""
    return TargetRequirement(
        filter=filter,
        min_targets=0,
        max_targets=max_count,
        optional=True,
        prompt=prompt,
    )


def optional_target(filter: TargetFilter,
                   prompt: str = "Select a target (optional)") -> TargetRequirement:
    """Create optional single-target requirement"""
    return TargetRequirement(
        filter=filter,
        min_targets=0,
        max_targets=1,
        optional=True,
        prompt=prompt,
    )
