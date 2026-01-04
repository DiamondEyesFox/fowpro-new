"""
Effect system for Force of Will.

Defines effects that abilities and spells can produce.

References:
- CR 908: One Time Effects
- CR 909: Continuous Effects
- CR 910: Replacement Effects
- CR 1000+: Action by Rules
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Callable, Union, TYPE_CHECKING
from enum import Enum

from .types import EffectAction, EffectDuration, KeywordAbility
from .targeting import TargetRequirement, TargetFilter
from .conditions import Condition
from .modals import ModalChoice

if TYPE_CHECKING:
    from ..engine import GameEngine
    from ..models import Card


@dataclass
class Effect:
    """
    An effect that can be produced by an ability or spell.

    CR 901.3: An effect is a part of the game procedure produced by a
    resolved ability, or produced by a rule or a replacement effect.
    """
    # What action this effect performs
    action: EffectAction

    # Parameters for the action
    params: Dict[str, Any] = field(default_factory=dict)

    # Target requirements (if any)
    target: Optional[TargetRequirement] = None

    # Condition that must be met (if any)
    condition: Optional[Condition] = None

    # For modal effects
    modal: Optional[ModalChoice] = None

    # Duration (for continuous effects)
    duration: EffectDuration = EffectDuration.INSTANT

    # Source card (set at runtime)
    source: Optional['Card'] = None

    # Resolved targets (set at runtime)
    resolved_targets: List['Card'] = field(default_factory=list)

    # For effects that reference "it" or "that card"
    reference_target: Optional['Card'] = None

    def execute(self, game: 'GameEngine', source: 'Card',
                targets: List['Card'] = None, player: int = None) -> bool:
        """
        Execute this effect.

        Args:
            game: The game engine
            source: The source card
            targets: Target cards (if applicable)
            player: The player executing the effect

        Returns:
            True if effect was executed successfully
        """
        if player is None:
            player = source.controller

        # Check condition
        if self.condition and not self.condition.check(game, source, player):
            return False

        # Store for reference
        self.source = source
        self.resolved_targets = targets or []

        # Execute based on action type
        return self._execute_action(game, source, targets, player)

    def _execute_action(self, game: 'GameEngine', source: 'Card',
                        targets: List['Card'], player: int) -> bool:
        """Execute the specific action."""
        action = self.action
        params = self.params

        # Damage effects (CR 1007)
        if action == EffectAction.DEAL_DAMAGE:
            amount = params.get('amount', 0)
            for target in targets:
                if hasattr(target, 'damage'):
                    target.damage += amount
                elif hasattr(target, 'life'):
                    target.life -= amount
            return True

        # Zone movement effects
        if action == EffectAction.DESTROY:
            for target in targets:
                game._destroy_card(target)
            return True

        if action == EffectAction.BANISH:
            for target in targets:
                game.move_card(target, target.controller, game.Zone.GRAVEYARD)
            return True

        if action == EffectAction.RETURN_TO_HAND:
            for target in targets:
                game.move_card(target, target.owner, game.Zone.HAND)
            return True

        if action == EffectAction.REMOVE_FROM_GAME:
            for target in targets:
                game.move_card(target, target.owner, game.Zone.REMOVED)
            return True

        # Card draw (CR 1009)
        if action == EffectAction.DRAW:
            count = params.get('count', 1)
            target_player = params.get('player', player)
            for _ in range(count):
                game.draw_card(target_player)
            return True

        # Discard (CR 1019)
        if action == EffectAction.DISCARD:
            count = params.get('count', 1)
            target_player = params.get('player', player)
            # Discard is handled by UI for random/choice
            return True

        # Life effects
        if action == EffectAction.GAIN_LIFE:
            amount = params.get('amount', 0)
            target_player = params.get('player', player)
            game.players[target_player].life += amount
            return True

        if action == EffectAction.LOSE_LIFE:
            amount = params.get('amount', 0)
            target_player = params.get('player', player)
            game.players[target_player].life -= amount
            return True

        # Will production (CR 907)
        if action == EffectAction.PRODUCE_WILL:
            from ..models import Attribute
            attr = params.get('attribute', Attribute.VOID)
            count = params.get('count', 1)
            game.players[player].will_pool.add(attr, count)
            return True

        # Rest/Recover (CR 1013)
        if action == EffectAction.REST:
            for target in targets:
                target.is_rested = True
            return True

        if action == EffectAction.RECOVER:
            for target in targets:
                target.is_rested = False
            return True

        # Counters (CR 1022)
        if action == EffectAction.ADD_COUNTER:
            counter_type = params.get('counter_type', 'generic')
            count = params.get('count', 1)
            for target in targets:
                target.counters[counter_type] = target.counters.get(counter_type, 0) + count
            return True

        if action == EffectAction.REMOVE_COUNTER:
            counter_type = params.get('counter_type', 'generic')
            count = params.get('count', 1)
            for target in targets:
                current = target.counters.get(counter_type, 0)
                target.counters[counter_type] = max(0, current - count)
            return True

        # Stat modification
        if action == EffectAction.MODIFY_ATK:
            amount = params.get('amount', 0)
            for target in targets:
                target.current_atk = (target.current_atk or 0) + amount
            return True

        if action == EffectAction.MODIFY_DEF:
            amount = params.get('amount', 0)
            for target in targets:
                target.current_def = (target.current_def or 0) + amount
            return True

        # Keyword granting
        if action == EffectAction.GRANT_KEYWORD:
            keyword = params.get('keyword')
            if keyword:
                for target in targets:
                    target.granted_keywords |= keyword
            return True

        if action == EffectAction.REMOVE_KEYWORD:
            keyword = params.get('keyword')
            if keyword:
                for target in targets:
                    target.granted_keywords &= ~keyword
            return True

        # Cancel (CR 1012)
        if action == EffectAction.CANCEL:
            for target in targets:
                if target in game.chase:
                    game.chase.remove(target)
            return True

        # Put into field (CR 1006)
        if action == EffectAction.PUT_INTO_FIELD:
            from_zone = params.get('from_zone', 'hand')
            x_variable = params.get('x_variable', False)

            # Get X value if needed
            x_value = params.get('x_value', 0)

            # For now, move target cards to field
            for target in targets:
                # Check cost restriction for X variable
                if x_variable and hasattr(target, 'data') and target.data:
                    if target.data.total_cost > x_value:
                        continue
                game.move_card(target, player, game.Zone.FIELD)
            return True

        # Search (CR 1014)
        if action == EffectAction.SEARCH:
            destination = params.get('destination', 'hand')
            filter_type = params.get('filter_type')
            filter_name = params.get('filter_name')
            filter_race = params.get('filter_race')

            # Find matching cards in deck
            deck = game.players[player].deck
            matching = []
            for card in deck:
                if not card.data:
                    continue
                if filter_type and filter_type.lower() not in str(card.data.card_type).lower():
                    continue
                if filter_name and filter_name.lower() not in card.data.name.lower():
                    continue
                if filter_race and filter_race.lower() not in (card.data.race or '').lower():
                    continue
                matching.append(card)

            # For now, take first match (UI should prompt choice)
            if matching:
                chosen = matching[0]
                deck.remove(chosen)
                if destination == 'hand':
                    game.players[player].hand.append(chosen)
                elif destination == 'field':
                    game.move_card(chosen, player, game.Zone.FIELD)
                # Shuffle deck
                import random
                random.shuffle(deck)
            return True

        # Prevent damage (CR 1018)
        if action == EffectAction.PREVENT_DAMAGE:
            # Set up damage prevention shield
            amount = params.get('amount', 0)
            prevent_all = params.get('all', False)
            for target in targets:
                if prevent_all:
                    target.damage_prevention = float('inf')
                else:
                    target.damage_prevention = (getattr(target, 'damage_prevention', 0) or 0) + amount
            return True

        # Gain control (CR 105.3)
        if action == EffectAction.GAIN_CONTROL:
            for target in targets:
                # Change controller
                old_controller = target.controller
                target.controller = player
                # Move between fields
                if target in game.players[old_controller].field:
                    game.players[old_controller].field.remove(target)
                    game.players[player].field.append(target)
            return True

        # Put on top of deck
        if action == EffectAction.PUT_ON_TOP_OF_DECK:
            for target in targets:
                owner = target.owner if hasattr(target, 'owner') else target.controller
                # Remove from current zone
                game.move_card(target, game.Zone.REMOVED)  # Temp removal
                # Put on top of deck
                game.players[owner].deck.insert(0, target)
                target.zone = game.Zone.DECK
            return True

        # Put on bottom of deck
        if action == EffectAction.PUT_ON_BOTTOM_OF_DECK:
            for target in targets:
                owner = target.owner if hasattr(target, 'owner') else target.controller
                game.move_card(target, game.Zone.REMOVED)  # Temp removal
                game.players[owner].deck.append(target)
                target.zone = game.Zone.DECK
            return True

        # Put into graveyard
        if action == EffectAction.PUT_INTO_GRAVEYARD:
            for target in targets:
                game.move_card(target, game.Zone.GRAVEYARD)
            return True

        # Shuffle into deck
        if action == EffectAction.SHUFFLE_INTO_DECK:
            import random
            for target in targets:
                owner = target.owner if hasattr(target, 'owner') else target.controller
                game.move_card(target, game.Zone.REMOVED)  # Temp removal
                game.players[owner].deck.append(target)
                target.zone = game.Zone.DECK
            # Shuffle each affected player's deck
            owners = set(t.owner if hasattr(t, 'owner') else t.controller for t in targets)
            for owner in owners:
                random.shuffle(game.players[owner].deck)
            return True

        # Reveal cards
        if action == EffectAction.REVEAL:
            # Mark cards as revealed (for UI purposes)
            for target in targets:
                target.is_revealed = True
            return True

        # Look at cards (private reveal)
        if action == EffectAction.LOOK:
            # Similar to reveal but only controller sees
            # In practice this is mostly UI handling
            return True

        # Set ATK
        if action == EffectAction.SET_ATK:
            value = params.get('value', 0)
            for target in targets:
                target.current_atk = value
            return True

        # Set DEF
        if action == EffectAction.SET_DEF:
            value = params.get('value', 0)
            for target in targets:
                target.current_def = value
            return True

        # Set life
        if action == EffectAction.SET_LIFE:
            value = params.get('value', 0)
            game.players[player].life = value
            return True

        # Grant ability
        if action == EffectAction.GRANT_ABILITY:
            ability_text = params.get('ability', '')
            for target in targets:
                if not hasattr(target, 'granted_abilities'):
                    target.granted_abilities = []
                target.granted_abilities.append(ability_text)
            return True

        # Remove ability
        if action == EffectAction.REMOVE_ABILITY:
            remove_all = params.get('all', False)
            for target in targets:
                if remove_all:
                    target.abilities_removed = True
            return True

        # Copy card
        if action == EffectAction.COPY:
            # Create a copy of target card's characteristics
            for target in targets:
                if targets and source:
                    # Source becomes a copy of target
                    source.copy_from = target.uid
            return True

        # Summon token
        if action == EffectAction.SUMMON:
            from ..models import CardData, CardType, Attribute, Card
            token_data = params.get('token_data', {})
            count = params.get('count', 1)

            # Create token CardData
            token_card_data = CardData(
                code=f"TOKEN-{id(token_data)}",
                name=token_data.get('name', 'Token'),
                card_type=CardType.RESONATOR,
                attribute=token_data.get('attribute', Attribute.NONE),
                cost=token_data.get('cost', None) or __import__('fowpro.models', fromlist=['WillCost']).WillCost(),
                atk=token_data.get('atk', 0),
                defense=token_data.get('def', 0),
                races=token_data.get('races', []),
            )

            # Create token instances
            for _ in range(count):
                import uuid
                token = Card(
                    uid=str(uuid.uuid4()),
                    data=token_card_data,
                    owner=player,
                    controller=player,
                    zone=game.Zone.FIELD,
                )
                token.is_token = True
                game.players[player].field.append(token)
            return True

        # Remove damage (healing)
        if action == EffectAction.REMOVE_DAMAGE:
            amount = params.get('amount', 0)
            remove_all = params.get('all', False)
            for target in targets:
                if remove_all:
                    target.damage = 0
                else:
                    target.damage = max(0, target.damage - amount)
            return True

        # Grant attribute
        if action == EffectAction.GRANT_ATTRIBUTE:
            from ..models import Attribute
            attr = params.get('attribute', Attribute.NONE)
            for target in targets:
                if not hasattr(target, 'granted_attributes'):
                    target.granted_attributes = Attribute.NONE
                target.granted_attributes |= attr
            return True

        # Remove attribute
        if action == EffectAction.REMOVE_ATTRIBUTE:
            from ..models import Attribute
            attr = params.get('attribute', Attribute.NONE)
            for target in targets:
                if hasattr(target, 'granted_attributes'):
                    target.granted_attributes &= ~attr
            return True

        # Set attribute (replace all)
        if action == EffectAction.SET_ATTRIBUTE:
            from ..models import Attribute
            attr = params.get('attribute', Attribute.NONE)
            for target in targets:
                target.base_attribute_override = attr
            return True

        # Grant race
        if action == EffectAction.GRANT_RACE:
            race = params.get('race', '')
            for target in targets:
                if not hasattr(target, 'granted_races'):
                    target.granted_races = []
                if race and race not in target.granted_races:
                    target.granted_races.append(race)
            return True

        # Set type
        if action == EffectAction.SET_TYPE:
            from ..models import CardType
            card_type = params.get('type', CardType.RESONATOR)
            for target in targets:
                target.type_override = card_type
            return True

        # Become copy (different from COPY - the card becomes a copy itself)
        if action == EffectAction.BECOME_COPY:
            # Source becomes a copy of target, copying all printed values
            for target in targets:
                if source:
                    # Store original values if not already stored
                    if not hasattr(source, 'original_data'):
                        source.original_data = source.data
                    # Copy target's data
                    source.copy_of = target.uid
                    source.current_atk = target.data.atk
                    source.current_def = target.data.defense
                    # Copy abilities would be handled by the ability system
            return True

        print(f"[WARN] Effect action {action} not fully implemented")
        return True


class EffectLayer:
    """
    Effect layers per CR 909.1.
    Effects are applied in layer order; within layers, by timestamp (CR 909.3b).
    """
    # Layer 1: Copy effects (CR 909.1a)
    COPY = 1

    # Layer 2: Control-changing effects (CR 909.1b)
    CONTROL = 2

    # Layer 3: Text-changing effects (CR 909.1c)
    TEXT = 3

    # Layer 4: Type-changing effects (CR 909.1d)
    TYPE = 4

    # Layer 5: Attribute-changing effects (CR 909.1e)
    ATTRIBUTE = 5

    # Layer 6: ATK/DEF modification (CR 909.1f)
    # Sublayer 6a: Set to specific value
    STATS_SET = 6
    # Sublayer 6b: Modify (add/subtract)
    STATS_MODIFY = 7

    # Layer 7: Keyword-granting effects (CR 909.1g)
    KEYWORDS = 8

    # Layer 8: Ability-granting effects (CR 909.1h)
    ABILITIES = 9


@dataclass
class ContinuousEffect:
    """
    A continuous effect that applies over time.

    CR 909: Continuous effects apply as long as they are active.
    """
    # Unique ID for this effect instance
    effect_id: str = ""

    # Source card UID
    source_id: int = 0

    # Name for debugging
    name: str = "Continuous Effect"

    # How long this lasts
    duration: EffectDuration = EffectDuration.WHILE_ON_FIELD

    # What layer this applies in (CR 909.1a-h)
    # Uses EffectLayer constants
    layer: int = EffectLayer.STATS_MODIFY

    # Filter for affected cards
    affected_filter: Optional[TargetFilter] = None

    # Only affects self
    affects_self_only: bool = False

    # Stat modifications (layer 6-7)
    atk_modifier: int = 0
    def_modifier: int = 0
    set_atk: Optional[int] = None  # For layer 6a (set to value)
    set_def: Optional[int] = None  # For layer 6a (set to value)

    # Keywords to grant/remove (layer 8)
    grant_keywords: KeywordAbility = KeywordAbility.NONE
    remove_keywords: KeywordAbility = KeywordAbility.NONE

    # Abilities to grant (layer 9)
    grant_abilities: List[str] = field(default_factory=list)

    # Attribute changes (layer 5)
    grant_attributes: int = 0  # Attribute flags
    remove_attributes: int = 0
    set_attributes: Optional[int] = None

    # Type changes (layer 4)
    set_type: Optional[str] = None
    grant_races: List[str] = field(default_factory=list)

    # Copy (layer 1)
    copy_of: Optional[str] = None  # UID of card to copy

    # Control (layer 2)
    new_controller: Optional[int] = None

    # Custom application function
    apply_func: Optional[Callable] = None

    # Condition for this effect to be active
    condition: Optional[Condition] = None

    # Turn/timestamp for ordering (CR 909.3b)
    timestamp: int = 0

    def get_layer(self) -> int:
        """Determine which layer this effect applies in."""
        if self.copy_of is not None:
            return EffectLayer.COPY
        if self.new_controller is not None:
            return EffectLayer.CONTROL
        if self.set_type or self.grant_races:
            return EffectLayer.TYPE
        if self.grant_attributes or self.remove_attributes or self.set_attributes is not None:
            return EffectLayer.ATTRIBUTE
        if self.set_atk is not None or self.set_def is not None:
            return EffectLayer.STATS_SET
        if self.atk_modifier or self.def_modifier:
            return EffectLayer.STATS_MODIFY
        if self.grant_keywords or self.remove_keywords:
            return EffectLayer.KEYWORDS
        if self.grant_abilities:
            return EffectLayer.ABILITIES
        return self.layer

    def applies_to(self, card: 'Card', game: 'GameEngine') -> bool:
        """Check if this effect applies to a card."""
        if self.affects_self_only:
            return card.uid == self.source_id

        if self.affected_filter:
            source = game.get_card_by_uid(self.source_id)
            if source:
                return self.affected_filter.matches(card, card.controller, source.controller)

        return True

    def apply(self, card: 'Card', game: 'GameEngine'):
        """Apply this continuous effect to a card."""
        # Check condition
        if self.condition:
            source = game.get_card_by_uid(self.source_id)
            if source and not self.condition.check(game, source, source.controller):
                return

        layer = self.get_layer()

        # Layer 1: Copy effects
        if layer == EffectLayer.COPY and self.copy_of:
            original = game.get_card_by_uid(self.copy_of)
            if original:
                # Copy base stats and characteristics
                card.current_atk = original.data.atk
                card.current_def = original.data.defense
                card.copy_of = self.copy_of

        # Layer 2: Control
        if layer == EffectLayer.CONTROL and self.new_controller is not None:
            card.controller = self.new_controller

        # Layer 4: Type changes
        if layer == EffectLayer.TYPE:
            if self.set_type:
                card.type_override = self.set_type
            for race in self.grant_races:
                if not hasattr(card, 'granted_races'):
                    card.granted_races = []
                if race not in card.granted_races:
                    card.granted_races.append(race)

        # Layer 5: Attribute changes
        if layer == EffectLayer.ATTRIBUTE:
            if self.set_attributes is not None:
                card.base_attribute_override = self.set_attributes
            if self.grant_attributes:
                if not hasattr(card, 'granted_attributes'):
                    card.granted_attributes = 0
                card.granted_attributes |= self.grant_attributes
            if self.remove_attributes:
                if hasattr(card, 'granted_attributes'):
                    card.granted_attributes &= ~self.remove_attributes

        # Layer 6a: Set stats
        if layer == EffectLayer.STATS_SET:
            if self.set_atk is not None:
                card.current_atk = self.set_atk
            if self.set_def is not None:
                card.current_def = self.set_def

        # Layer 6b: Modify stats
        if layer == EffectLayer.STATS_MODIFY:
            if self.atk_modifier:
                card.current_atk = (card.current_atk or 0) + self.atk_modifier
            if self.def_modifier:
                card.current_def = (card.current_def or 0) + self.def_modifier

        # Layer 7: Keywords
        if layer == EffectLayer.KEYWORDS:
            if self.grant_keywords:
                card.granted_keywords |= self.grant_keywords
            if self.remove_keywords:
                card.granted_keywords &= ~self.remove_keywords

        # Layer 8: Abilities
        if layer == EffectLayer.ABILITIES:
            if not hasattr(card, 'granted_abilities'):
                card.granted_abilities = []
            for ability in self.grant_abilities:
                if ability not in card.granted_abilities:
                    card.granted_abilities.append(ability)

        # Custom function (runs at specified layer)
        if self.apply_func:
            self.apply_func(card, game)


class ContinuousEffectManager:
    """
    Manages continuous effects and applies them in correct layer order.

    CR 909.3: Multiple continuous effects are applied in layer order,
    then by timestamp within each layer.
    """

    def __init__(self):
        self.effects: List[ContinuousEffect] = []
        self.timestamp_counter: int = 0

    def add_effect(self, effect: ContinuousEffect) -> None:
        """Add a continuous effect with timestamp."""
        effect.timestamp = self.timestamp_counter
        self.timestamp_counter += 1
        self.effects.append(effect)

    def remove_effect(self, effect_id: str) -> bool:
        """Remove an effect by ID."""
        for i, effect in enumerate(self.effects):
            if effect.effect_id == effect_id:
                self.effects.pop(i)
                return True
        return False

    def remove_effects_from_source(self, source_id) -> int:
        """Remove all effects from a source card. Returns count removed."""
        original_len = len(self.effects)
        self.effects = [e for e in self.effects if e.source_id != source_id]
        return original_len - len(self.effects)

    def get_effects_by_layer(self) -> Dict[int, List[ContinuousEffect]]:
        """Group effects by layer, sorted by timestamp within each layer."""
        by_layer: Dict[int, List[ContinuousEffect]] = {}
        for effect in self.effects:
            layer = effect.get_layer()
            if layer not in by_layer:
                by_layer[layer] = []
            by_layer[layer].append(effect)

        # Sort each layer by timestamp
        for layer in by_layer:
            by_layer[layer].sort(key=lambda e: e.timestamp)

        return by_layer

    def apply_to_card(self, card: 'Card', game: 'GameEngine') -> None:
        """Apply all relevant continuous effects to a card in layer order."""
        # Reset card to base values
        card.current_atk = card.data.atk if card.data else 0
        card.current_def = card.data.defense if card.data else 0

        # Get effects grouped by layer
        by_layer = self.get_effects_by_layer()

        # Apply in layer order (1-9)
        for layer in sorted(by_layer.keys()):
            for effect in by_layer[layer]:
                if effect.applies_to(card, game):
                    effect.apply(card, game)

    def apply_to_all_cards(self, game: 'GameEngine') -> None:
        """Apply all continuous effects to all cards in the game."""
        # Apply to all cards on field
        for player in game.players:
            for card in player.field:
                self.apply_to_card(card, game)
            # Also apply to J-Ruler if present
            if player.j_ruler:
                self.apply_to_card(player.j_ruler, game)

    def cleanup_expired_effects(self, game: 'GameEngine') -> int:
        """Remove effects that have expired. Returns count removed."""
        original_len = len(self.effects)
        active_effects = []

        for effect in self.effects:
            keep = True

            if effect.duration == EffectDuration.WHILE_ON_FIELD:
                # Check if source is still on field
                source = game.get_card_by_uid(effect.source_id)
                if not source or source.zone != game.Zone.FIELD:
                    keep = False

            # Other duration types are handled by the game's phase system
            # (UNTIL_END_OF_TURN effects cleaned up at end phase)

            if keep:
                active_effects.append(effect)

        self.effects = active_effects
        return original_len - len(self.effects)


@dataclass
class ReplacementEffect:
    """
    A replacement effect that modifies game events.

    CR 910: Replacement effects change what happens.
    """
    # What event this replaces
    replaces: str  # "destroy", "damage", "draw", etc.

    # Condition for replacement
    condition: Optional[Condition] = None

    # What happens instead
    replacement: Callable[['GameEngine', 'Card', dict], Any] = None

    # Source card UID
    source_id: int = 0

    # Whether this has been applied this instance
    applied: bool = False

    def can_replace(self, event_type: str, game: 'GameEngine',
                    card: 'Card', event_data: dict) -> bool:
        """Check if this replacement can apply."""
        if self.replaces != event_type:
            return False

        if self.condition:
            source = game.get_card_by_uid(self.source_id)
            if source:
                return self.condition.check(game, source, source.controller)

        return True

    def apply_replacement(self, game: 'GameEngine', card: 'Card',
                          event_data: dict) -> Any:
        """Apply this replacement effect."""
        if self.replacement:
            return self.replacement(game, card, event_data)
        return None


class ReplacementType:
    """
    Standard replacement effect types per CR 910.
    """
    DAMAGE = "damage"          # "If X would deal damage"
    DESTROY = "destroy"        # "If X would be destroyed"
    DRAW = "draw"              # "If X would draw a card"
    DISCARD = "discard"        # "If X would discard"
    ENTER_FIELD = "enter_field"  # "If X would enter the field"
    LEAVE_FIELD = "leave_field"  # "If X would leave the field"
    LOSE_LIFE = "lose_life"    # "If X would lose life"
    GAIN_LIFE = "gain_life"    # "If X would gain life"
    REST = "rest"              # "If X would rest"
    PUT_INTO_GRAVEYARD = "put_into_graveyard"  # "If X would be put into graveyard"


@dataclass
class ReplacementResult:
    """Result of applying a replacement effect."""
    was_replaced: bool = False
    replacement_applied: Optional[ReplacementEffect] = None
    new_event_data: Dict[str, Any] = field(default_factory=dict)
    prevent_original: bool = False


class ReplacementEffectManager:
    """
    Manages replacement effects.

    CR 910: If one event is applicable to multiple replacement effects,
    the controller of the affected card chooses which to apply.
    CR 910.2: Each replacement can only apply once per event.
    """

    def __init__(self):
        self.effects: List[ReplacementEffect] = []

    def add_effect(self, effect: ReplacementEffect) -> None:
        """Register a replacement effect."""
        self.effects.append(effect)

    def remove_effect(self, source_id) -> int:
        """Remove all replacement effects from a source."""
        original_len = len(self.effects)
        self.effects = [e for e in self.effects if e.source_id != source_id]
        return original_len - len(self.effects)

    def check_replacement(self, event_type: str, game: 'GameEngine',
                          affected_card: 'Card', event_data: dict) -> ReplacementResult:
        """
        Check if any replacement effect applies to an event.

        CR 910: If multiple replacements apply, affected card's controller chooses.
        For now, we apply the first matching replacement.
        """
        result = ReplacementResult()
        result.new_event_data = event_data.copy()

        # Find applicable replacements
        applicable = []
        for effect in self.effects:
            if effect.can_replace(event_type, game, affected_card, event_data):
                applicable.append(effect)

        if not applicable:
            return result

        # Apply first applicable replacement (CR 910 - controller would choose)
        chosen = applicable[0]
        replacement_result = chosen.apply_replacement(game, affected_card, event_data)

        result.was_replaced = True
        result.replacement_applied = chosen
        result.prevent_original = True

        if isinstance(replacement_result, dict):
            result.new_event_data.update(replacement_result)

        return result

    def apply_damage_replacement(self, game: 'GameEngine', target: 'Card',
                                  amount: int, source: 'Card') -> int:
        """
        Apply replacement effects to damage.
        Returns the actual damage amount after replacements.
        """
        event_data = {
            'amount': amount,
            'source': source,
            'target': target,
        }

        result = self.check_replacement(ReplacementType.DAMAGE, game, target, event_data)

        if result.was_replaced:
            # If prevented, return 0
            if result.new_event_data.get('prevent', False):
                return 0
            # If modified, return new amount
            return result.new_event_data.get('amount', amount)

        return amount

    def apply_destroy_replacement(self, game: 'GameEngine', target: 'Card',
                                   source: 'Card' = None) -> bool:
        """
        Apply replacement effects to destruction.
        Returns True if destruction should proceed, False if replaced/prevented.
        """
        event_data = {
            'source': source,
            'target': target,
        }

        result = self.check_replacement(ReplacementType.DESTROY, game, target, event_data)

        if result.was_replaced and result.prevent_original:
            return False

        return True


class EffectBuilder:
    """Builder for creating effects."""

    @staticmethod
    def deal_damage(amount: int, to_player: bool = False) -> Effect:
        """Deal damage to target(s)."""
        return Effect(
            action=EffectAction.DEAL_DAMAGE,
            params={'amount': amount, 'to_player': to_player}
        )

    @staticmethod
    def destroy() -> Effect:
        """Destroy target(s)."""
        return Effect(action=EffectAction.DESTROY)

    @staticmethod
    def return_to_hand() -> Effect:
        """Return target(s) to owner's hand."""
        return Effect(action=EffectAction.RETURN_TO_HAND)

    @staticmethod
    def draw(count: int = 1, player: str = 'you') -> Effect:
        """Draw cards."""
        return Effect(
            action=EffectAction.DRAW,
            params={'count': count, 'player': player}
        )

    @staticmethod
    def discard(count: int = 1, random: bool = False) -> Effect:
        """Discard cards."""
        return Effect(
            action=EffectAction.DISCARD,
            params={'count': count, 'random': random}
        )

    @staticmethod
    def gain_life(amount: int) -> Effect:
        """Gain life."""
        return Effect(
            action=EffectAction.GAIN_LIFE,
            params={'amount': amount}
        )

    @staticmethod
    def lose_life(amount: int) -> Effect:
        """Lose life."""
        return Effect(
            action=EffectAction.LOSE_LIFE,
            params={'amount': amount}
        )

    @staticmethod
    def produce_will(attribute, count: int = 1) -> Effect:
        """Produce will."""
        return Effect(
            action=EffectAction.PRODUCE_WILL,
            params={'attribute': attribute, 'count': count}
        )

    @staticmethod
    def rest() -> Effect:
        """Rest target(s)."""
        return Effect(action=EffectAction.REST)

    @staticmethod
    def recover() -> Effect:
        """Recover target(s)."""
        return Effect(action=EffectAction.RECOVER)

    @staticmethod
    def add_counter(counter_type: str, count: int = 1) -> Effect:
        """Add counters."""
        return Effect(
            action=EffectAction.ADD_COUNTER,
            params={'counter_type': counter_type, 'count': count}
        )

    @staticmethod
    def buff(atk: int = 0, def_: int = 0, duration: EffectDuration = EffectDuration.UNTIL_END_OF_TURN) -> Effect:
        """Buff ATK/DEF."""
        effects = []
        if atk:
            effects.append(Effect(
                action=EffectAction.MODIFY_ATK,
                params={'amount': atk},
                duration=duration
            ))
        if def_:
            effects.append(Effect(
                action=EffectAction.MODIFY_DEF,
                params={'amount': def_},
                duration=duration
            ))
        # Return first effect or create compound
        return effects[0] if len(effects) == 1 else effects

    @staticmethod
    def grant_keyword(keyword: KeywordAbility,
                      duration: EffectDuration = EffectDuration.UNTIL_END_OF_TURN) -> Effect:
        """Grant a keyword."""
        return Effect(
            action=EffectAction.GRANT_KEYWORD,
            params={'keyword': keyword},
            duration=duration
        )

    @staticmethod
    def cancel() -> Effect:
        """Cancel target spell/ability."""
        return Effect(action=EffectAction.CANCEL)

    @staticmethod
    def remove_from_game() -> Effect:
        """Remove from game."""
        return Effect(action=EffectAction.REMOVE_FROM_GAME)

    @staticmethod
    def put_into_field(from_zone: str = 'hand') -> Effect:
        """Put a card into the field from a zone."""
        return Effect(
            action=EffectAction.PUT_INTO_FIELD,
            params={'from_zone': from_zone}
        )

    @staticmethod
    def put_into_field_x_cost() -> Effect:
        """Put a card with cost X or less into the field."""
        return Effect(
            action=EffectAction.PUT_INTO_FIELD,
            params={'from_zone': 'hand', 'x_variable': True}
        )

    @staticmethod
    def search(destination: str = 'hand', filter_type: str = None,
               filter_name: str = None, filter_race: str = None) -> Effect:
        """Search deck for a card."""
        return Effect(
            action=EffectAction.SEARCH,
            params={
                'destination': destination,
                'filter_type': filter_type,
                'filter_name': filter_name,
                'filter_race': filter_race,
            }
        )

    @staticmethod
    def banish() -> Effect:
        """Banish target(s) - put into graveyard from field."""
        return Effect(action=EffectAction.BANISH)

    @staticmethod
    def prevent_damage(amount: int = 0, all_damage: bool = False) -> Effect:
        """Prevent damage."""
        return Effect(
            action=EffectAction.PREVENT_DAMAGE,
            params={'amount': amount, 'all': all_damage}
        )

    @staticmethod
    def gain_control() -> Effect:
        """Gain control of target."""
        return Effect(action=EffectAction.GAIN_CONTROL)

    @staticmethod
    def put_on_top_of_deck() -> Effect:
        """Put target on top of owner's deck."""
        return Effect(action=EffectAction.PUT_ON_TOP_OF_DECK)

    @staticmethod
    def put_on_bottom_of_deck() -> Effect:
        """Put target on bottom of owner's deck."""
        return Effect(action=EffectAction.PUT_ON_BOTTOM_OF_DECK)

    @staticmethod
    def put_into_graveyard() -> Effect:
        """Put target into graveyard."""
        return Effect(action=EffectAction.PUT_INTO_GRAVEYARD)

    @staticmethod
    def shuffle_into_deck() -> Effect:
        """Shuffle target into owner's deck."""
        return Effect(action=EffectAction.SHUFFLE_INTO_DECK)

    @staticmethod
    def reveal() -> Effect:
        """Reveal target card(s)."""
        return Effect(action=EffectAction.REVEAL)

    @staticmethod
    def look_at(count: int = 1) -> Effect:
        """Look at top N cards of deck."""
        return Effect(
            action=EffectAction.LOOK,
            params={'count': count}
        )

    @staticmethod
    def set_atk(value: int) -> Effect:
        """Set ATK to a specific value."""
        return Effect(
            action=EffectAction.SET_ATK,
            params={'value': value}
        )

    @staticmethod
    def set_def(value: int) -> Effect:
        """Set DEF to a specific value."""
        return Effect(
            action=EffectAction.SET_DEF,
            params={'value': value}
        )

    @staticmethod
    def set_life(value: int) -> Effect:
        """Set player's life to a specific value."""
        return Effect(
            action=EffectAction.SET_LIFE,
            params={'value': value}
        )

    @staticmethod
    def grant_ability(ability_text: str) -> Effect:
        """Grant an ability to target."""
        return Effect(
            action=EffectAction.GRANT_ABILITY,
            params={'ability': ability_text}
        )

    @staticmethod
    def remove_all_abilities() -> Effect:
        """Remove all abilities from target."""
        return Effect(
            action=EffectAction.REMOVE_ABILITY,
            params={'all': True}
        )

    @staticmethod
    def copy_card() -> Effect:
        """Copy target card's characteristics."""
        return Effect(action=EffectAction.COPY)

    @staticmethod
    def summon_token(name: str, atk: int, def_: int, **kwargs) -> Effect:
        """Summon a token creature."""
        return Effect(
            action=EffectAction.SUMMON,
            params={
                'token_data': {
                    'name': name,
                    'atk': atk,
                    'def': def_,
                    **kwargs
                }
            }
        )

    @staticmethod
    def remove_counter(counter_type: str, count: int = 1) -> Effect:
        """Remove counters from target."""
        return Effect(
            action=EffectAction.REMOVE_COUNTER,
            params={'counter_type': counter_type, 'count': count}
        )

    @staticmethod
    def remove_damage(amount: int = 0, remove_all: bool = False) -> Effect:
        """Remove damage from target (healing)."""
        return Effect(
            action=EffectAction.REMOVE_DAMAGE,
            params={'amount': amount, 'all': remove_all}
        )

    @staticmethod
    def grant_attribute(attribute) -> Effect:
        """Grant an attribute to target."""
        return Effect(
            action=EffectAction.GRANT_ATTRIBUTE,
            params={'attribute': attribute}
        )

    @staticmethod
    def remove_attribute(attribute) -> Effect:
        """Remove an attribute from target."""
        return Effect(
            action=EffectAction.REMOVE_ATTRIBUTE,
            params={'attribute': attribute}
        )

    @staticmethod
    def set_attribute(attribute) -> Effect:
        """Set target's attribute (replacing all others)."""
        return Effect(
            action=EffectAction.SET_ATTRIBUTE,
            params={'attribute': attribute}
        )

    @staticmethod
    def grant_race(race: str) -> Effect:
        """Grant a race/trait to target."""
        return Effect(
            action=EffectAction.GRANT_RACE,
            params={'race': race}
        )

    @staticmethod
    def set_type(card_type) -> Effect:
        """Set target's card type."""
        return Effect(
            action=EffectAction.SET_TYPE,
            params={'type': card_type}
        )

    @staticmethod
    def become_copy() -> Effect:
        """Make source become a copy of target."""
        return Effect(action=EffectAction.BECOME_COPY)

    # =========================================================================
    # Extended effect methods for CR-compliant script generation
    # =========================================================================

    @staticmethod
    def draw_variable() -> Effect:
        """Draw cards equal to a variable amount (from game state)."""
        return Effect(
            action=EffectAction.DRAW,
            params={'variable': True}
        )

    @staticmethod
    def deal_damage_x() -> Effect:
        """Deal X damage where X is from paid cost."""
        return Effect(
            action=EffectAction.DEAL_DAMAGE,
            params={'x_variable': True}
        )

    @staticmethod
    def deal_damage_equal_to_atk() -> Effect:
        """Deal damage equal to source's ATK."""
        return Effect(
            action=EffectAction.DEAL_DAMAGE,
            params={'equal_to_atk': True}
        )

    @staticmethod
    def deal_damage_variable() -> Effect:
        """Deal damage equal to a game state variable."""
        return Effect(
            action=EffectAction.DEAL_DAMAGE,
            params={'variable': True}
        )

    @staticmethod
    def deal_damage_mutual() -> Effect:
        """Source and target deal damage to each other."""
        return Effect(
            action=EffectAction.DEAL_DAMAGE,
            params={'mutual': True}
        )

    @staticmethod
    def return_from_graveyard() -> Effect:
        """Return target from graveyard to hand."""
        return Effect(
            action=EffectAction.RETURN_TO_HAND,
            params={'from_zone': 'graveyard'}
        )

    @staticmethod
    def gain_life_equal_to_damage() -> Effect:
        """Gain life equal to damage dealt."""
        return Effect(
            action=EffectAction.GAIN_LIFE,
            params={'equal_to_damage': True}
        )

    @staticmethod
    def produce_will_any() -> Effect:
        """Produce will of any attribute."""
        return Effect(
            action=EffectAction.PRODUCE_WILL,
            params={'any_color': True}
        )

    @staticmethod
    def rest_x_targets() -> Effect:
        """Rest X target resonators where X is from paid cost."""
        return Effect(
            action=EffectAction.REST,
            params={'x_variable': True}
        )

    @staticmethod
    def scaling_buff(atk_per: int, def_per: int) -> Effect:
        """Buff that scales with game state (e.g., +X/+X for each card)."""
        return Effect(
            action=EffectAction.MODIFY_ATK,
            params={'atk_per': atk_per, 'def_per': def_per, 'scaling': True}
        )

    @staticmethod
    def dynamic_stats() -> Effect:
        """ATK/DEF calculated dynamically from game state."""
        return Effect(
            action=EffectAction.SET_ATK,
            params={'dynamic': True}
        )

    @staticmethod
    def double_damage() -> Effect:
        """Source deals double damage."""
        return Effect(
            action=EffectAction.MODIFY_ATK,
            params={'double_damage': True}
        )

    @staticmethod
    def swap_stats() -> Effect:
        """Swap ATK and DEF of target."""
        return Effect(
            action=EffectAction.MODIFY_ATK,
            params={'swap_stats': True}
        )

    @staticmethod
    def damage_replacement() -> Effect:
        """Replace damage with an alternative effect."""
        return Effect(
            action=EffectAction.PREVENT_DAMAGE,
            params={'replacement': True}
        )

    @staticmethod
    def force_attack() -> Effect:
        """Target must attack if able."""
        return Effect(
            action=EffectAction.GRANT_ABILITY,
            params={'force_attack': True}
        )

    @staticmethod
    def force_block() -> Effect:
        """Target must block if able."""
        return Effect(
            action=EffectAction.GRANT_ABILITY,
            params={'force_block': True}
        )

    @staticmethod
    def redirect_target() -> Effect:
        """Change the target of a spell/ability."""
        return Effect(
            action=EffectAction.GRANT_ABILITY,
            params={'redirect': True}
        )

    @staticmethod
    def grant_to_others() -> Effect:
        """Grant an ability to other permanents you control."""
        return Effect(
            action=EffectAction.GRANT_ABILITY,
            params={'to_others': True}
        )

    @staticmethod
    def end_of_turn_trigger() -> Effect:
        """Create an end-of-turn trigger effect."""
        return Effect(
            action=EffectAction.GRANT_ABILITY,
            params={'end_of_turn_trigger': True}
        )

    @staticmethod
    def on_targeted_trigger() -> Effect:
        """Trigger when this becomes targeted."""
        return Effect(
            action=EffectAction.GRANT_ABILITY,
            params={'on_targeted': True}
        )

    @staticmethod
    def play_restriction() -> Effect:
        """Restrict what can be played/summoned."""
        return Effect(
            action=EffectAction.REMOVE_ABILITY,
            params={'restriction': True}
        )

    @staticmethod
    def move_addition() -> Effect:
        """Move an Addition from one target to another."""
        return Effect(
            action=EffectAction.GRANT_ABILITY,
            params={'move': True}
        )

    @staticmethod
    def put_on_added_death() -> Effect:
        """Put added resonator into field when it dies."""
        return Effect(
            action=EffectAction.PUT_INTO_FIELD,
            params={'on_added_death': True}
        )

    @staticmethod
    def search_on_death(destination: str = 'hand') -> Effect:
        """Search when target goes to graveyard."""
        return Effect(
            action=EffectAction.SEARCH,
            params={'destination': destination, 'on_death': True}
        )

    @staticmethod
    def banish_self_conditional() -> Effect:
        """Banish this card if condition is met."""
        return Effect(
            action=EffectAction.BANISH,
            params={'self': True, 'conditional': True}
        )

    @staticmethod
    def opponent_banishes() -> Effect:
        """Opponent banishes a card."""
        return Effect(
            action=EffectAction.BANISH,
            params={'controller': 'opponent'}
        )

    @staticmethod
    def discard_all() -> Effect:
        """Discard all cards in hand."""
        return Effect(
            action=EffectAction.DISCARD,
            params={'all': True}
        )

    @staticmethod
    def remove_ability() -> Effect:
        """Remove a specific ability from target."""
        return Effect(action=EffectAction.REMOVE_ABILITY)

    @staticmethod
    def add_restriction() -> Effect:
        """Add a play/summon restriction."""
        return Effect(
            action=EffectAction.REMOVE_ABILITY,
            params={'restriction': True}
        )

    @staticmethod
    def prevent_recovery() -> Effect:
        """Prevent target from recovering during recovery phase."""
        return Effect(
            action=EffectAction.REMOVE_ABILITY,
            params={'prevent_recovery': True}
        )

    @staticmethod
    def reveal_top() -> Effect:
        """Reveal the top card of deck."""
        return Effect(
            action=EffectAction.REVEAL,
            params={'from_top': True}
        )

    @staticmethod
    def secret_choice() -> Effect:
        """Make a secret choice (e.g., choose a number)."""
        return Effect(
            action=EffectAction.REVEAL,
            params={'secret_choice': True}
        )

    @staticmethod
    def redirect_damage() -> Effect:
        """Redirect damage from one target to another."""
        return Effect(
            action=EffectAction.PREVENT_DAMAGE,
            params={'redirect': True}
        )

    @staticmethod
    def prevent_next_damage() -> Effect:
        """Prevent the next damage that would be dealt."""
        return Effect(
            action=EffectAction.PREVENT_DAMAGE,
            params={'next_only': True}
        )

    @staticmethod
    def prevent_all_battle_damage() -> Effect:
        """Prevent all battle damage."""
        return Effect(
            action=EffectAction.PREVENT_DAMAGE,
            params={'all': True, 'battle_only': True}
        )

    @staticmethod
    def prevent_all_damage() -> Effect:
        """Prevent all damage."""
        return Effect(
            action=EffectAction.PREVENT_DAMAGE,
            params={'all': True}
        )

    # =========================================================================
    # Additional CR-compliant methods added for comprehensive effect coverage
    # =========================================================================

    @staticmethod
    def remove_all_damage() -> Effect:
        """Remove all damage from target (full heal)."""
        return Effect(
            action=EffectAction.REMOVE_DAMAGE,
            params={'all': True}
        )

    @staticmethod
    def summon() -> Effect:
        """Summon a resonator (put on chase as spell, CR 1006)."""
        return Effect(action=EffectAction.SUMMON)

    @staticmethod
    def copy_spell() -> Effect:
        """Copy target spell or ability (CR 1017.3)."""
        return Effect(
            action=EffectAction.COPY,
            params={'type': 'spell'}
        )

    @staticmethod
    def copy_entity() -> Effect:
        """Copy target entity, creating a token (CR 1017.2)."""
        return Effect(
            action=EffectAction.COPY,
            params={'type': 'entity'}
        )

    @staticmethod
    def foresee(count: int) -> Effect:
        """Foresee X - look at top X, put any on top/bottom (CR 1034)."""
        return Effect(
            action=EffectAction.LOOK,
            params={'count': count, 'foresee': True}
        )

    @staticmethod
    def look(count: int) -> Effect:
        """Look at top N cards of deck (CR 1014)."""
        return Effect(
            action=EffectAction.LOOK,
            params={'count': count}
        )

    @staticmethod
    def set_stats(atk: int, def_: int) -> Effect:
        """Set both ATK and DEF to specific values."""
        return Effect(
            action=EffectAction.SET_ATK,
            params={'atk': atk, 'def': def_}
        )

    @staticmethod
    def set_race(race: str) -> Effect:
        """Set target's race (replacing existing)."""
        return Effect(
            action=EffectAction.GRANT_RACE,
            params={'race': race, 'replace': True}
        )

    @staticmethod
    def call_magic_stone() -> Effect:
        """Call a magic stone (CR 1016)."""
        return Effect(
            action=EffectAction.GRANT_ABILITY,
            params={'call_stone': True}
        )

    @staticmethod
    def remove_keyword(keyword) -> Effect:
        """Remove a keyword ability from target."""
        return Effect(
            action=EffectAction.REMOVE_KEYWORD,
            params={'keyword': keyword}
        )
