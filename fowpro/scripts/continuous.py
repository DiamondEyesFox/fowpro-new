"""
Continuous Effects System
=========================

Handles continuous/static effects that persist while a card is on the field.
Uses a layer system similar to MTG for effect ordering.

Effect layers (applied in order):
1. Control-changing effects
2. Type-changing effects
3. Attribute-changing effects
4. Ability-modifying effects (grant/remove keywords)
5. ATK/DEF modifying effects
6. ATK/DEF setting effects
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Callable, Optional, List, Set, Dict, Any, TYPE_CHECKING
from .keywords import Keyword, KeywordState

if TYPE_CHECKING:
    from ..engine import GameEngine
    from ..models import Card


class EffectLayer(Enum):
    """Layers for continuous effect application order"""
    CONTROL = 1         # Control-changing effects
    TYPE = 2            # Type-changing effects (add/remove types)
    ATTRIBUTE = 3       # Attribute-changing effects
    ABILITY = 4         # Ability granting/removing
    STAT_MODIFY = 5     # ATK/DEF +X/+X or -X/-X
    STAT_SET = 6        # ATK/DEF = X (applied last)


class EffectDuration(Enum):
    """How long an effect lasts"""
    WHILE_ON_FIELD = auto()     # While source is on field
    UNTIL_END_OF_TURN = auto()  # Until end of current turn
    PERMANENT = auto()          # Permanent modification (counters)


@dataclass
class AffectedCardFilter:
    """Filter for what cards a continuous effect affects"""
    controller: Optional[int] = None      # 0=you, 1=opponent, None=any
    zone: Optional[str] = None            # Zone the card must be in
    card_types: Optional[Set[str]] = None # Card types to match
    attributes: Optional[Set[str]] = None # Attributes to match
    has_keywords: Optional[Keyword] = None # Must have these keywords
    name_contains: Optional[str] = None   # Name filter
    custom: Optional[Callable[['Card'], bool]] = None  # Custom filter

    def matches(self, card: 'Card', source_controller: int) -> bool:
        """Check if a card matches this filter"""
        # Controller check (relative to source)
        if self.controller is not None:
            expected_controller = source_controller if self.controller == 0 else 1 - source_controller
            if card.controller != expected_controller:
                return False

        # Zone check
        if self.zone is not None:
            from ..models import Zone
            expected_zone = Zone[self.zone.upper()]
            if card.zone != expected_zone:
                return False

        # Card type check
        if self.card_types:
            if card.data:
                card_type = card.data.card_type.name.lower()
                if not any(t.lower() in card_type for t in self.card_types):
                    return False

        # Attribute check
        if self.attributes:
            if card.data and card.data.attribute:
                if card.data.attribute.name.upper() not in {a.upper() for a in self.attributes}:
                    return False

        # Keyword check
        if self.has_keywords:
            if not hasattr(card, 'keyword_state'):
                return False
            if not (card.keyword_state.effective_keywords & self.has_keywords):
                return False

        # Name check
        if self.name_contains:
            if not card.data or self.name_contains.lower() not in card.data.name.lower():
                return False

        # Custom check
        if self.custom:
            if not self.custom(card):
                return False

        return True


@dataclass
class ContinuousEffect:
    """A continuous effect definition"""
    source_id: str                          # Card UID that creates this effect
    name: str                               # Effect name for debugging
    layer: EffectLayer                      # When to apply this effect
    duration: EffectDuration = EffectDuration.WHILE_ON_FIELD

    # What cards are affected
    affected_filter: AffectedCardFilter = field(default_factory=AffectedCardFilter)
    affects_self: bool = False              # If true, also affects the source

    # Effect values (depending on layer)
    # CONTROL: new_controller (int)
    # TYPE: add_types (set), remove_types (set)
    # ATTRIBUTE: new_attribute (str)
    # ABILITY: grant_keywords (Keyword), remove_keywords (Keyword)
    # STAT_MODIFY: atk_mod (int), def_mod (int)
    # STAT_SET: atk_set (int), def_set (int)
    effect_values: Dict[str, Any] = field(default_factory=dict)

    # Timestamp for dependency ordering
    timestamp: int = 0

    # Condition for effect to be active
    condition: Optional[Callable[['GameEngine', 'Card'], bool]] = None


class ContinuousEffectManager:
    """Manages all continuous effects in the game"""

    def __init__(self, game: 'GameEngine'):
        self.game = game
        self._effects: List[ContinuousEffect] = []
        self._timestamp_counter = 0

    def register_effect(self, effect: ContinuousEffect):
        """Register a new continuous effect"""
        effect.timestamp = self._timestamp_counter
        self._timestamp_counter += 1
        self._effects.append(effect)

    def unregister_source(self, source_id: str):
        """Remove all effects from a source"""
        self._effects = [e for e in self._effects if e.source_id != source_id]

    def remove_end_of_turn_effects(self):
        """Remove effects that expire at end of turn"""
        self._effects = [
            e for e in self._effects
            if e.duration != EffectDuration.UNTIL_END_OF_TURN
        ]

    def apply_all_effects(self):
        """Apply all continuous effects (called during state-based actions)"""
        # Reset all cards to base state first
        self._reset_all_cards()

        # Get all effects sorted by layer, then timestamp
        sorted_effects = sorted(
            self._effects,
            key=lambda e: (e.layer.value, e.timestamp)
        )

        # Apply effects in layer order
        for effect in sorted_effects:
            self._apply_effect(effect)

    def _reset_all_cards(self):
        """Reset all cards to their base state"""
        for player in self.game.players:
            for card in player.get_all_cards():
                # Reset stats to base
                if card.data:
                    card.current_atk = card.data.atk or 0
                    card.current_def = card.data.defense or 0

                # Reset keyword state (keep base, clear granted/removed)
                if hasattr(card, 'keyword_state'):
                    card.keyword_state.granted_keywords = Keyword.NONE
                    card.keyword_state.removed_keywords = Keyword.NONE

    def _apply_effect(self, effect: ContinuousEffect):
        """Apply a single continuous effect"""
        # Find source card
        source = self._find_card_by_id(effect.source_id)

        # Check if source is still valid
        if effect.duration == EffectDuration.WHILE_ON_FIELD:
            from ..models import Zone
            if not source or source.zone != Zone.FIELD:
                return

        # Check condition
        if effect.condition and source:
            if not effect.condition(self.game, source):
                return

        # Find affected cards
        affected_cards = self._get_affected_cards(effect, source)

        # Apply effect to each card
        for card in affected_cards:
            self._apply_effect_to_card(effect, card)

    def _get_affected_cards(self, effect: ContinuousEffect,
                           source: Optional['Card']) -> List['Card']:
        """Get all cards affected by an effect"""
        affected = []
        source_controller = source.controller if source else 0

        for player in self.game.players:
            for card in player.get_all_cards():
                # Skip source unless affects_self
                if source and card.uid == source.uid:
                    if effect.affects_self:
                        affected.append(card)
                    continue

                # Check filter
                if effect.affected_filter.matches(card, source_controller):
                    affected.append(card)

        return affected

    def _apply_effect_to_card(self, effect: ContinuousEffect, card: 'Card'):
        """Apply effect values to a specific card"""
        values = effect.effect_values

        if effect.layer == EffectLayer.CONTROL:
            new_controller = values.get('new_controller')
            if new_controller is not None:
                card.controller = new_controller

        elif effect.layer == EffectLayer.ABILITY:
            # Initialize keyword state if needed
            if not hasattr(card, 'keyword_state'):
                card.keyword_state = KeywordState()

            grant = values.get('grant_keywords', Keyword.NONE)
            remove = values.get('remove_keywords', Keyword.NONE)

            if grant:
                card.keyword_state.grant(grant)
            if remove:
                card.keyword_state.remove(remove)

        elif effect.layer == EffectLayer.STAT_MODIFY:
            atk_mod = values.get('atk_mod', 0)
            def_mod = values.get('def_mod', 0)
            card.current_atk += atk_mod
            card.current_def += def_mod

        elif effect.layer == EffectLayer.STAT_SET:
            atk_set = values.get('atk_set')
            def_set = values.get('def_set')
            if atk_set is not None:
                card.current_atk = atk_set
            if def_set is not None:
                card.current_def = def_set

    def _find_card_by_id(self, card_id: str) -> Optional['Card']:
        """Find a card by its UID"""
        for player in self.game.players:
            for card in player.get_all_cards():
                if card.uid == card_id:
                    return card
        return None


# =============================================================================
# CONTINUOUS EFFECT BUILDERS
# =============================================================================

def all_resonators_get_buff(source: 'Card', atk: int, def_: int,
                            your_side_only: bool = True) -> ContinuousEffect:
    """Create 'All resonators you control get +X/+X' effect"""
    return ContinuousEffect(
        source_id=source.uid,
        name=f"All resonators get +{atk}/+{def_}",
        layer=EffectLayer.STAT_MODIFY,
        affected_filter=AffectedCardFilter(
            controller=0 if your_side_only else None,
            zone='FIELD',
            card_types={'resonator'},
        ),
        effect_values={'atk_mod': atk, 'def_mod': def_},
    )


def resonators_with_keyword_get_buff(source: 'Card', keyword: Keyword,
                                     atk: int, def_: int) -> ContinuousEffect:
    """Create 'Resonators with X get +A/+D' effect"""
    return ContinuousEffect(
        source_id=source.uid,
        name=f"Resonators with {keyword.name} get +{atk}/+{def_}",
        layer=EffectLayer.STAT_MODIFY,
        affected_filter=AffectedCardFilter(
            zone='FIELD',
            card_types={'resonator'},
            has_keywords=keyword,
        ),
        effect_values={'atk_mod': atk, 'def_mod': def_},
    )


def all_resonators_gain_keyword(source: 'Card', keyword: Keyword,
                                your_side_only: bool = True) -> ContinuousEffect:
    """Create 'All resonators you control gain X' effect"""
    return ContinuousEffect(
        source_id=source.uid,
        name=f"All resonators gain {keyword.name}",
        layer=EffectLayer.ABILITY,
        affected_filter=AffectedCardFilter(
            controller=0 if your_side_only else None,
            zone='FIELD',
            card_types={'resonator'},
        ),
        effect_values={'grant_keywords': keyword},
    )


def opponent_resonators_lose_keyword(source: 'Card', keyword: Keyword) -> ContinuousEffect:
    """Create 'Resonators your opponent controls lose X' effect"""
    return ContinuousEffect(
        source_id=source.uid,
        name=f"Opponent resonators lose {keyword.name}",
        layer=EffectLayer.ABILITY,
        affected_filter=AffectedCardFilter(
            controller=1,  # Opponent
            zone='FIELD',
            card_types={'resonator'},
        ),
        effect_values={'remove_keywords': keyword},
    )


def attribute_resonators_get_buff(source: 'Card', attribute: str,
                                  atk: int, def_: int) -> ContinuousEffect:
    """Create 'X attribute resonators you control get +A/+D' effect"""
    return ContinuousEffect(
        source_id=source.uid,
        name=f"{attribute} resonators get +{atk}/+{def_}",
        layer=EffectLayer.STAT_MODIFY,
        affected_filter=AffectedCardFilter(
            controller=0,
            zone='FIELD',
            card_types={'resonator'},
            attributes={attribute.upper()},
        ),
        effect_values={'atk_mod': atk, 'def_mod': def_},
    )


def named_resonators_get_buff(source: 'Card', name_contains: str,
                              atk: int, def_: int) -> ContinuousEffect:
    """Create 'Resonators with "X" in their name get +A/+D' effect"""
    return ContinuousEffect(
        source_id=source.uid,
        name=f'"{name_contains}" resonators get +{atk}/+{def_}',
        layer=EffectLayer.STAT_MODIFY,
        affected_filter=AffectedCardFilter(
            controller=0,
            zone='FIELD',
            card_types={'resonator'},
            name_contains=name_contains,
        ),
        effect_values={'atk_mod': atk, 'def_mod': def_},
    )


def self_buff_while_condition(source: 'Card', atk: int, def_: int,
                              condition: Callable[['GameEngine', 'Card'], bool]) -> ContinuousEffect:
    """Create conditional self-buff effect"""
    return ContinuousEffect(
        source_id=source.uid,
        name=f"Conditional self +{atk}/+{def_}",
        layer=EffectLayer.STAT_MODIFY,
        affected_filter=AffectedCardFilter(),
        affects_self=True,
        effect_values={'atk_mod': atk, 'def_mod': def_},
        condition=condition,
    )
