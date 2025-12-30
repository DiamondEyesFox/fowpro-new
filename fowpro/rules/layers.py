"""
Continuous Effect Layer System for Force of Will.

Implements the layer system per CR 909.1 for applying continuous effects
in the correct order.

References:
- CR 909: Continuous Effects
- CR 909.1a-h: Layers (characteristics in specific order)
- CR 909.2: Within layers, effects apply in timestamp order
- CR 909.3: Dependency handling
"""

from dataclasses import dataclass, field
from enum import IntEnum
from typing import TYPE_CHECKING, List, Optional, Dict, Set, Callable, Any

if TYPE_CHECKING:
    from ..engine import GameEngine
    from ..models import Card

from .types import EffectDuration, KeywordAbility
from .targeting import TargetFilter
from .conditions import Condition


class Layer(IntEnum):
    """
    Layers for continuous effect application.

    CR 909.1: Effects that change characteristics are applied in layers.
    Lower numbers are applied first.
    """
    # Layer 1: Copy effects (CR 909.1a)
    COPY = 1

    # Layer 2: Control-changing effects (CR 909.1b)
    CONTROL = 2

    # Layer 3: Text-changing effects (CR 909.1c)
    TEXT = 3

    # Layer 4: Type-changing effects (CR 909.1d)
    TYPE = 4

    # Layer 5: Attribute/color-changing effects (CR 909.1e)
    ATTRIBUTE = 5

    # Layer 6: Ability-adding/removing effects (CR 909.1f)
    ABILITY = 6

    # Layer 7a: ATK/DEF from characteristic-defining abilities
    STAT_CDA = 70

    # Layer 7b: ATK/DEF setting effects
    STAT_SET = 71

    # Layer 7c: ATK/DEF modifying effects
    STAT_MODIFY = 72

    # Layer 7d: Counter-based ATK/DEF
    STAT_COUNTER = 73

    # Layer 8: All other effects
    OTHER = 8


@dataclass
class LayeredEffect:
    """
    A continuous effect that applies in the layer system.

    CR 909: Continuous effects apply as long as they are active.
    """
    # Unique ID for this effect
    effect_id: str = ""

    # Source card UID
    source_id: str = ""

    # Display name
    name: str = ""

    # Which layer this applies in
    layer: Layer = Layer.STAT_MODIFY

    # How long this lasts
    duration: EffectDuration = EffectDuration.WHILE_ON_FIELD

    # Turn/timestamp for ordering (CR 909.2)
    timestamp: int = 0

    # What this effect does - depends on layer
    # Layer 1 (Copy): copy_source = card to copy
    copy_source: Optional[str] = None

    # Layer 2 (Control): new_controller = player index
    new_controller: Optional[int] = None

    # Layer 4 (Type): types to add/set
    add_types: List[str] = field(default_factory=list)
    set_type: Optional[str] = None

    # Layer 5 (Attribute): attributes to add/set
    add_attributes: List[str] = field(default_factory=list)
    set_attribute: Optional[str] = None

    # Layer 6 (Ability): keywords/abilities to add/remove
    grant_keywords: KeywordAbility = KeywordAbility.NONE
    remove_keywords: KeywordAbility = KeywordAbility.NONE
    grant_abilities: List[str] = field(default_factory=list)
    remove_abilities: List[str] = field(default_factory=list)

    # Layer 7 (Stats): ATK/DEF modifications
    set_atk: Optional[int] = None
    set_def: Optional[int] = None
    modify_atk: int = 0
    modify_def: int = 0

    # Filter for which cards this affects
    affected_filter: Optional[TargetFilter] = None

    # Only affects self
    affects_self_only: bool = False

    # Condition for this effect to be active
    condition: Optional[Condition] = None

    # Custom application function
    apply_func: Optional[Callable] = None

    # Dependencies (effect IDs that must be applied before this)
    dependencies: Set[str] = field(default_factory=set)

    def applies_to(self, card: 'Card', game: 'GameEngine') -> bool:
        """Check if this effect applies to a given card."""
        # Check if source still exists
        source = game.get_card(self.source_id)
        if not source:
            return False

        # Check duration
        if self.duration == EffectDuration.WHILE_ON_FIELD:
            from ..models import Zone
            if source.zone != Zone.FIELD:
                return False

        # Self-only check
        if self.affects_self_only:
            return card.uid == self.source_id

        # Filter check
        if self.affected_filter:
            return self.affected_filter.matches(
                card, card.controller, source.controller
            )

        return True

    def is_active(self, game: 'GameEngine') -> bool:
        """Check if this effect is currently active."""
        source = game.get_card(self.source_id)
        if not source:
            return False

        # Check condition
        if self.condition:
            return self.condition.check(game, source, source.controller)

        # Check duration
        if self.duration == EffectDuration.WHILE_ON_FIELD:
            from ..models import Zone
            return source.zone == Zone.FIELD

        return True


class LayerManager:
    """
    Manages the layer system for continuous effects.

    CR 909.1: Effects are applied in layer order.
    CR 909.2: Within a layer, effects are applied in timestamp order.
    CR 909.3: Dependency handling.
    """

    def __init__(self, game: 'GameEngine'):
        self.game = game

        # All registered effects
        self.effects: Dict[str, LayeredEffect] = {}

        # Effect counter for unique IDs
        self._effect_counter = 0

        # Current timestamp
        self._timestamp = 0

    def register_effect(self, effect: LayeredEffect) -> str:
        """
        Register a new continuous effect.

        Returns the effect ID.
        """
        self._effect_counter += 1
        effect_id = f"effect_{self._effect_counter:06d}"
        effect.effect_id = effect_id

        self._timestamp += 1
        effect.timestamp = self._timestamp

        self.effects[effect_id] = effect
        return effect_id

    def unregister_effect(self, effect_id: str):
        """Remove a continuous effect."""
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

    def remove_duration_effects(self, duration: EffectDuration):
        """Remove all effects with a specific duration."""
        to_remove = [
            eid for eid, e in self.effects.items()
            if e.duration == duration
        ]
        for eid in to_remove:
            del self.effects[eid]

    def clear_end_of_turn_effects(self):
        """Remove all until-end-of-turn effects."""
        self.remove_duration_effects(EffectDuration.UNTIL_END_OF_TURN)

    def get_effects_in_order(self) -> List[LayeredEffect]:
        """
        Get all active effects in application order.

        CR 909.1: Layer order
        CR 909.2: Timestamp order within layers
        CR 909.3: Dependency sorting
        """
        active = [e for e in self.effects.values() if e.is_active(self.game)]

        # Sort by layer, then timestamp
        active.sort(key=lambda e: (e.layer.value, e.timestamp))

        # Handle dependencies
        return self._topological_sort(active)

    def _topological_sort(self, effects: List[LayeredEffect]) -> List[LayeredEffect]:
        """
        Sort effects respecting dependencies.

        CR 909.3: An effect is dependent on another if:
        - They affect the same cards
        - One could change whether the other applies
        - They're in the same layer
        """
        # Build dependency graph
        effect_map = {e.effect_id: e for e in effects}
        in_degree = {e.effect_id: 0 for e in effects}
        dependents = {e.effect_id: [] for e in effects}

        for e in effects:
            for dep_id in e.dependencies:
                if dep_id in effect_map:
                    in_degree[e.effect_id] += 1
                    dependents[dep_id].append(e.effect_id)

        # Kahn's algorithm
        result = []
        queue = [eid for eid, deg in in_degree.items() if deg == 0]

        while queue:
            # Sort queue by layer then timestamp for deterministic order
            queue.sort(key=lambda eid: (
                effect_map[eid].layer.value,
                effect_map[eid].timestamp
            ))

            eid = queue.pop(0)
            result.append(effect_map[eid])

            for dep_eid in dependents[eid]:
                in_degree[dep_eid] -= 1
                if in_degree[dep_eid] == 0:
                    queue.append(dep_eid)

        return result

    def apply_all_effects(self):
        """
        Apply all continuous effects to all cards.

        This recalculates derived stats and abilities.
        """
        # Reset all cards to base values first
        for card in self._get_all_field_cards():
            self._reset_card_to_base(card)

        # Apply effects in order
        effects = self.get_effects_in_order()

        for effect in effects:
            for card in self._get_all_field_cards():
                if effect.applies_to(card, self.game):
                    self._apply_effect_to_card(effect, card)

    def _get_all_field_cards(self) -> List['Card']:
        """Get all cards on the field."""
        cards = []
        for p in self.game.players:
            cards.extend(p.field)
        return cards

    def _reset_card_to_base(self, card: 'Card'):
        """Reset a card's derived values to base."""
        if card.data:
            card.current_atk = card.data.atk
            card.current_def = card.data.defense
        else:
            card.current_atk = 0
            card.current_def = 0

        card.granted_keywords = KeywordAbility.NONE
        card.granted_abilities = []

    def _apply_effect_to_card(self, effect: LayeredEffect, card: 'Card'):
        """Apply a single effect to a card."""
        layer = effect.layer

        # Layer 1: Copy
        if layer == Layer.COPY and effect.copy_source:
            source_card = self.game.get_card(effect.copy_source)
            if source_card and source_card.data:
                # Copy characteristics
                card.copied_from = source_card.data

        # Layer 2: Control
        elif layer == Layer.CONTROL and effect.new_controller is not None:
            old_controller = card.controller
            new_controller = effect.new_controller

            if old_controller != new_controller:
                # Move between players
                if card in self.game.players[old_controller].field:
                    self.game.players[old_controller].field.remove(card)
                self.game.players[new_controller].field.append(card)
                card.controller = new_controller

        # Layer 4: Type
        elif layer == Layer.TYPE:
            if effect.set_type:
                card.current_type = effect.set_type
            for t in effect.add_types:
                if not hasattr(card, 'additional_types'):
                    card.additional_types = []
                card.additional_types.append(t)

        # Layer 5: Attribute
        elif layer == Layer.ATTRIBUTE:
            if effect.set_attribute:
                card.current_attribute = effect.set_attribute
            for a in effect.add_attributes:
                if not hasattr(card, 'additional_attributes'):
                    card.additional_attributes = []
                card.additional_attributes.append(a)

        # Layer 6: Abilities
        elif layer == Layer.ABILITY:
            if effect.grant_keywords:
                card.granted_keywords |= effect.grant_keywords
            if effect.remove_keywords:
                card.granted_keywords &= ~effect.remove_keywords
            for ability in effect.grant_abilities:
                if ability not in card.granted_abilities:
                    card.granted_abilities.append(ability)
            for ability in effect.remove_abilities:
                if ability in card.granted_abilities:
                    card.granted_abilities.remove(ability)

        # Layer 7a: CDA stats
        elif layer == Layer.STAT_CDA:
            # Characteristic-defining abilities set base stats
            pass  # Handled by card data

        # Layer 7b: Set stats
        elif layer == Layer.STAT_SET:
            if effect.set_atk is not None:
                card.current_atk = effect.set_atk
            if effect.set_def is not None:
                card.current_def = effect.set_def

        # Layer 7c: Modify stats
        elif layer == Layer.STAT_MODIFY:
            if effect.modify_atk:
                card.current_atk = (card.current_atk or 0) + effect.modify_atk
            if effect.modify_def:
                card.current_def = (card.current_def or 0) + effect.modify_def

        # Layer 7d: Counter-based stats
        elif layer == Layer.STAT_COUNTER:
            # +100/+100 counters, etc.
            for counter_type, count in card.counters.items():
                if counter_type.startswith('+'):
                    # Parse +X/+Y format
                    try:
                        parts = counter_type.split('/')
                        atk_mod = int(parts[0])
                        def_mod = int(parts[1]) if len(parts) > 1 else 0
                        card.current_atk = (card.current_atk or 0) + (atk_mod * count)
                        card.current_def = (card.current_def or 0) + (def_mod * count)
                    except (ValueError, IndexError):
                        pass

        # Custom application function
        if effect.apply_func:
            effect.apply_func(card, self.game, effect)


# Convenience functions for creating common effects
class LayeredEffectBuilder:
    """Builder for creating common layered effects."""

    @staticmethod
    def buff(source_id: str, atk: int = 0, def_: int = 0,
             filter_: TargetFilter = None,
             duration: EffectDuration = EffectDuration.WHILE_ON_FIELD) -> LayeredEffect:
        """Create a stat buff effect."""
        return LayeredEffect(
            source_id=source_id,
            name=f"+{atk}/+{def_}",
            layer=Layer.STAT_MODIFY,
            duration=duration,
            modify_atk=atk,
            modify_def=def_,
            affected_filter=filter_,
        )

    @staticmethod
    def buff_self(source_id: str, atk: int = 0, def_: int = 0,
                  duration: EffectDuration = EffectDuration.WHILE_ON_FIELD) -> LayeredEffect:
        """Create a self-buff effect."""
        return LayeredEffect(
            source_id=source_id,
            name=f"Self +{atk}/+{def_}",
            layer=Layer.STAT_MODIFY,
            duration=duration,
            modify_atk=atk,
            modify_def=def_,
            affects_self_only=True,
        )

    @staticmethod
    def grant_keyword(source_id: str, keyword: KeywordAbility,
                      filter_: TargetFilter = None,
                      duration: EffectDuration = EffectDuration.WHILE_ON_FIELD) -> LayeredEffect:
        """Create a keyword-granting effect."""
        return LayeredEffect(
            source_id=source_id,
            name=f"Grant {keyword.name}",
            layer=Layer.ABILITY,
            duration=duration,
            grant_keywords=keyword,
            affected_filter=filter_,
        )

    @staticmethod
    def grant_keyword_self(source_id: str, keyword: KeywordAbility,
                           duration: EffectDuration = EffectDuration.UNTIL_END_OF_TURN) -> LayeredEffect:
        """Create a self keyword-granting effect."""
        return LayeredEffect(
            source_id=source_id,
            name=f"Self gains {keyword.name}",
            layer=Layer.ABILITY,
            duration=duration,
            grant_keywords=keyword,
            affects_self_only=True,
        )

    @staticmethod
    def set_stats(source_id: str, atk: int, def_: int,
                  filter_: TargetFilter = None) -> LayeredEffect:
        """Create a stat-setting effect (becomes X/Y)."""
        return LayeredEffect(
            source_id=source_id,
            name=f"Set to {atk}/{def_}",
            layer=Layer.STAT_SET,
            set_atk=atk,
            set_def=def_,
            affected_filter=filter_,
        )

    @staticmethod
    def control(source_id: str, new_controller: int,
                filter_: TargetFilter = None) -> LayeredEffect:
        """Create a control-changing effect."""
        return LayeredEffect(
            source_id=source_id,
            name=f"Control change to P{new_controller}",
            layer=Layer.CONTROL,
            new_controller=new_controller,
            affected_filter=filter_,
        )

    @staticmethod
    def race_buff(source_id: str, race: str, atk: int = 0, def_: int = 0) -> LayeredEffect:
        """Create a buff for all cards of a specific race."""
        from .targeting import TargetController

        race_filter = TargetFilter(
            races=[race],
            controllers=[TargetController.YOU],
        )

        return LayeredEffect(
            source_id=source_id,
            name=f"Each {race} gets +{atk}/+{def_}",
            layer=Layer.STAT_MODIFY,
            duration=EffectDuration.WHILE_ON_FIELD,
            modify_atk=atk,
            modify_def=def_,
            affected_filter=race_filter,
        )
