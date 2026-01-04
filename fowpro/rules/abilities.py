"""
Ability system for Force of Will.

Defines the different types of abilities per CR 901-907.

References:
- CR 901: Ability and Effect
- CR 904: Continuous Ability
- CR 905: Activate Ability
- CR 906: Automatic Abilities
- CR 907: Will Abilities
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Callable, TYPE_CHECKING
from abc import ABC, abstractmethod

from .types import (
    AbilityType, EffectTiming, TriggerCondition, TriggerTiming,
    EffectDuration, KeywordAbility
)
from .targeting import TargetRequirement
from .conditions import Condition
from .effects import Effect, ContinuousEffect
from .modals import ModalChoice

if TYPE_CHECKING:
    from ..engine import GameEngine
    from ..models import Card, WillCost


@dataclass
class Ability(ABC):
    """
    Base class for all abilities.

    CR 901.1: An ability is a text written on a card that makes effects
    of the game.
    """
    # Name for display/debugging
    name: str = "Ability"

    # The ability type
    ability_type: AbilityType = AbilityType.ACTIVATE

    # Effects this ability produces
    effects: List[Effect] = field(default_factory=list)

    # Condition to play this ability
    condition: Optional[Condition] = None

    # Modal choices (if any)
    modal: Optional[ModalChoice] = None

    # Whether this ability is mandatory
    is_mandatory: bool = False

    # Source card (set at runtime)
    source: Optional['Card'] = None

    @abstractmethod
    def can_play(self, game: 'GameEngine', card: 'Card', player: int) -> bool:
        """Check if this ability can be played."""
        pass

    @abstractmethod
    def resolve(self, game: 'GameEngine', card: 'Card', player: int,
                targets: List['Card'] = None, choices: dict = None) -> bool:
        """Resolve this ability."""
        pass


@dataclass
class ActivateAbility(Ability):
    """
    An activate ability per CR 905.

    CR 905.1: Activated abilities are abilities that the controller of
    them may play them at any time they can play it.
    """
    ability_type: AbilityType = AbilityType.ACTIVATE

    # Cost to activate
    will_cost: Optional['WillCost'] = None

    # Whether this requires tapping (rest)
    tap_cost: bool = False

    # Additional costs (e.g., "discard a card", "pay 500 life")
    additional_costs: List[Dict[str, Any]] = field(default_factory=list)

    # When this can be played
    timing: EffectTiming = EffectTiming.INSTANT

    # Target requirements
    targets: List[TargetRequirement] = field(default_factory=list)

    # Whether this needs swiftness to use on entry turn
    # CR 905.3: Activate abilities with [rest] need swiftness
    needs_swiftness_for_tap: bool = True

    # Once per turn restriction
    once_per_turn: bool = False

    # Track if used this turn
    used_this_turn: bool = False

    def can_play(self, game: 'GameEngine', card: 'Card', player: int) -> bool:
        """
        Check if this ability can be played.

        CR 905.2: Activated abilities are played following CR 903.2.
        """
        # Check if card is controlled by player
        if card.controller != player:
            return False

        # Check once per turn
        if self.once_per_turn and self.used_this_turn:
            return False

        # Check timing
        if self.timing == EffectTiming.MAIN_TIMING:
            # CR 701.2: main timing requirements
            if game.turn_player != player:
                return False
            from ..engine import Phase
            if game.current_phase != Phase.MAIN:
                return False
            if game.in_battle:
                return False
            if game.chase:
                return False

        # Check tap cost + swiftness
        if self.tap_cost:
            if card.is_rested:
                return False
            # CR 905.3: Need swiftness if card just entered this turn
            if self.needs_swiftness_for_tap and card.entered_turn == game.turn_number:
                if not card.has_keyword(KeywordAbility.SWIFTNESS):
                    return False

        # Check will cost
        if self.will_cost:
            if not game.players[player].will_pool.can_pay(self.will_cost):
                return False

        # Check condition
        if self.condition and not self.condition.check(game, card, player):
            return False

        # Check targets exist
        for target_req in self.targets:
            # Find at least one valid target
            valid_targets = self._find_valid_targets(game, card, player, target_req)
            min_needed = 0 if target_req.up_to or target_req.optional else target_req.count
            if len(valid_targets) < min_needed:
                return False

        return True

    def _find_valid_targets(self, game: 'GameEngine', card: 'Card',
                            player: int, target_req: TargetRequirement) -> List['Card']:
        """Find all valid targets for a requirement."""
        valid = []
        from .targeting import TargetZone

        for zone in target_req.filter.zones:
            if zone == TargetZone.FIELD:
                for p in game.players:
                    for c in p.field:
                        if target_req.filter.matches(c, c.controller, player):
                            valid.append(c)
            elif zone == TargetZone.GRAVEYARD:
                for p in game.players:
                    for c in p.graveyard:
                        if target_req.filter.matches(c, p.index, player):
                            valid.append(c)
            # Add other zones as needed

        return valid

    def resolve(self, game: 'GameEngine', card: 'Card', player: int,
                targets: List['Card'] = None, choices: dict = None) -> bool:
        """
        Resolve this ability.

        CR 707.3: When an ability in the chase area resolves, apply the
        effect of the ability, then remove it from the chase area.
        """
        targets = targets or []
        choices = choices or {}

        # Pay costs
        if self.tap_cost:
            card.is_rested = True

        if self.will_cost:
            game.players[player].will_pool.pay(self.will_cost)

        # Mark used
        if self.once_per_turn:
            self.used_this_turn = True

        # Execute effects
        for effect in self.effects:
            effect.execute(game, card, targets, player)

        return True


@dataclass
class AutomaticAbility(Ability):
    """
    An automatic (triggered) ability per CR 906.

    CR 906.1: Abilities described as "{Trigger condition} >>> (Effect)"
    are automatic abilities. An automatic ability watches the game
    situation, and if its trigger condition is met, it's automatically
    played in the priority sequence.
    """
    ability_type: AbilityType = AbilityType.AUTOMATIC

    # What triggers this ability
    trigger_condition: TriggerCondition = TriggerCondition.ENTER_FIELD

    # When this goes on the chase
    trigger_timing: TriggerTiming = TriggerTiming.CHASE

    # Additional condition beyond the trigger
    extra_condition: Optional[Condition] = None

    # Target requirements
    targets: List[TargetRequirement] = field(default_factory=list)

    # Whether controller can choose not to play (CR 906.6b - hidden zones)
    is_optional: bool = False

    # Once per turn
    once_per_turn: bool = False

    # Tracks trigger count (CR 906.4)
    trigger_count: int = 0

    def can_trigger(self, game: 'GameEngine', card: 'Card',
                    trigger: TriggerCondition, event_data: dict) -> bool:
        """
        Check if this ability should trigger.

        CR 906.4: If a condition on the automatic object is met, the
        number of times the automatic object triggered is increased by one.
        """
        if trigger != self.trigger_condition:
            return False

        if self.once_per_turn and self.trigger_count > 0:
            return False

        if self.extra_condition:
            if not self.extra_condition.check(game, card, card.controller):
                return False

        return True

    def trigger(self, game: 'GameEngine', card: 'Card', event_data: dict):
        """
        Mark this ability as triggered.

        CR 906.4: Increase trigger count.
        """
        self.trigger_count += 1

    def can_play(self, game: 'GameEngine', card: 'Card', player: int) -> bool:
        """
        Check if this triggered ability can be played.

        CR 906.6: Triggered automatic objects have to be played unless
        prohibited by rules or effects.
        """
        if self.trigger_count <= 0:
            return False

        if self.condition and not self.condition.check(game, card, player):
            return False

        # Check targets exist (if required)
        for target_req in self.targets:
            if not target_req.optional:
                valid = self._find_valid_targets(game, card, player, target_req)
                if len(valid) < target_req.count:
                    return False

        return True

    def _find_valid_targets(self, game: 'GameEngine', card: 'Card',
                            player: int, target_req: TargetRequirement) -> List['Card']:
        """Find valid targets."""
        valid = []
        from .targeting import TargetZone

        for zone in target_req.filter.zones:
            if zone == TargetZone.FIELD:
                for p in game.players:
                    for c in p.field:
                        if target_req.filter.matches(c, c.controller, player):
                            valid.append(c)

        return valid

    def resolve(self, game: 'GameEngine', card: 'Card', player: int,
                targets: List['Card'] = None, choices: dict = None) -> bool:
        """
        Resolve this triggered ability.
        """
        targets = targets or []
        choices = choices or {}

        # Decrease trigger count
        self.trigger_count -= 1

        # Execute effects
        for effect in self.effects:
            effect.execute(game, card, targets, player)

        return True

    def reset_turn(self):
        """Reset per-turn state."""
        if self.once_per_turn:
            self.trigger_count = 0


@dataclass
class ContinuousAbility(Ability):
    """
    A continuous ability per CR 904.

    CR 904.1: Continuous abilities are abilities that apply their effects
    as long as they are active. Effects of continuous abilities are
    considered continuous effects.
    """
    ability_type: AbilityType = AbilityType.CONTINUOUS

    # The continuous effect this produces
    continuous_effect: Optional[ContinuousEffect] = None

    # Condition for this to be active
    active_condition: Optional[Condition] = None

    def can_play(self, game: 'GameEngine', card: 'Card', player: int) -> bool:
        """Continuous abilities are always 'active', not 'played'."""
        return False  # Can't be played

    def is_active(self, game: 'GameEngine', card: 'Card', player: int) -> bool:
        """Check if this continuous ability is currently active."""
        if self.active_condition:
            return self.active_condition.check(game, card, player)
        return True

    def resolve(self, game: 'GameEngine', card: 'Card', player: int,
                targets: List['Card'] = None, choices: dict = None) -> bool:
        """Continuous abilities don't resolve - they just apply."""
        return True


@dataclass
class WillAbility(Ability):
    """
    A will ability per CR 907.

    CR 907.1: Some abilities that produce wills are considered "Will
    abilities".

    CR 907.3: Will abilities don't use the chase area and are resolved
    just after they are played.
    """
    ability_type: AbilityType = AbilityType.WILL

    # Cost (usually just tap)
    tap_cost: bool = True

    # Will colors this can produce
    will_colors: List[Any] = field(default_factory=list)  # List of Attribute

    # For dual stones - choice of colors
    choose_color: bool = False

    def can_play(self, game: 'GameEngine', card: 'Card', player: int) -> bool:
        """
        Check if this will ability can be played.

        CR 907.2: A player can play will abilities while they have
        priority, but not in the midst of performing an action.
        """
        if card.controller != player:
            return False

        if self.tap_cost and card.is_rested:
            return False

        # Will abilities can be played during cost payment
        # No timing restrictions like activate abilities

        return True

    def resolve(self, game: 'GameEngine', card: 'Card', player: int,
                targets: List['Card'] = None, choices: dict = None) -> bool:
        """
        Resolve this will ability immediately.

        CR 907.3: Will abilities don't use the chase area and are
        resolved just after they are played.
        """
        choices = choices or {}

        # Pay tap cost
        if self.tap_cost:
            card.is_rested = True

        # Determine which color to produce
        if self.choose_color and 'color' in choices:
            color = choices['color']
        elif self.will_colors:
            color = self.will_colors[0]
        else:
            from ..models import Attribute
            color = Attribute.VOID

        # Add will
        game.players[player].will_pool.add(color, 1)

        return True


@dataclass
class JudgmentAbility(Ability):
    """
    Judgment ability that flips a Ruler to its J-Ruler side.

    CR 702: Judgment is a special action that transforms a Ruler
    into its J-Ruler form by paying the Judgment cost.

    Judgment can only be done:
    - During main timing
    - Once per game (unless the J-Ruler returns to ruler zone)
    """
    ability_type: AbilityType = AbilityType.ACTIVATE

    # Cost to perform Judgment
    will_cost: Optional['WillCost'] = None

    # The J-Ruler code to flip to (e.g., "CMF-013J")
    j_ruler_code: str = ""

    # Tracks if Judgment has been used this game
    used_this_game: bool = False

    def can_play(self, game: 'GameEngine', card: 'Card', player: int) -> bool:
        """
        Check if Judgment can be performed.

        CR 702.1: A player can play the Judgment of a face-up Ruler
        they control during their main timing, if they haven't performed
        Judgment this game.
        """
        if card.controller != player:
            return False

        # Must be turn player
        if game.turn_player != player:
            return False

        # Must be main timing
        from ..engine import Phase
        if game.current_phase != Phase.MAIN:
            return False

        # Can't be in chase or battle
        if game.chase or game.in_battle:
            return False

        # Check if already used (unless J-Ruler returned to ruler zone)
        if self.used_this_game:
            return False

        # Check will cost
        if self.will_cost:
            if not game.players[player].will_pool.can_pay(self.will_cost):
                return False

        return True

    def resolve(self, game: 'GameEngine', card: 'Card', player: int,
                targets: List['Card'] = None, choices: dict = None) -> bool:
        """
        Perform Judgment - flip Ruler to J-Ruler.

        CR 702.2: When Judgment is performed, the Ruler is flipped to
        its J-Ruler side and enters the field as a J-Ruler.
        """
        # Pay cost
        if self.will_cost:
            game.players[player].will_pool.pay(self.will_cost)

        # Mark as used
        self.used_this_game = True

        # Flip to J-Ruler
        return self._perform_judgment(game, card, player)

    def _perform_judgment(self, game: 'GameEngine', card: 'Card', player: int) -> bool:
        """Actually flip the card to J-Ruler side."""
        from ..database import CardDatabase
        from ..models import Zone

        db = CardDatabase()

        # Find J-Ruler data
        j_ruler_data = db.get_card(self.j_ruler_code)
        if not j_ruler_data:
            print(f"[WARN] J-Ruler {self.j_ruler_code} not found")
            return False

        # Update card data to J-Ruler
        card.data = j_ruler_data

        # Move from ruler zone to field
        if hasattr(game.players[player], 'ruler') and game.players[player].ruler == card:
            game.players[player].ruler = None

        # Enter field as J-Ruler
        game.move_card(card, player, Zone.FIELD)

        # Trigger enter effects
        from .types import TriggerCondition
        game._check_triggers(TriggerCondition.ENTER_FIELD, card.controller, card)

        return True


# Helper to create common ability patterns
class AbilityFactory:
    """Factory for creating common ability patterns."""

    @staticmethod
    def enter_ability(name: str, effects: List[Effect],
                      condition: Condition = None,
                      targets: List[TargetRequirement] = None) -> AutomaticAbility:
        """Create an [Enter] ability."""
        return AutomaticAbility(
            name=name,
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=effects,
            extra_condition=condition,
            targets=targets or [],
            is_mandatory=True
        )

    @staticmethod
    def leave_ability(name: str, effects: List[Effect]) -> AutomaticAbility:
        """Create a leave field ability."""
        return AutomaticAbility(
            name=name,
            trigger_condition=TriggerCondition.LEAVE_FIELD,
            effects=effects,
            is_mandatory=True
        )

    @staticmethod
    def attack_ability(name: str, effects: List[Effect]) -> AutomaticAbility:
        """Create a 'when attacks' ability."""
        return AutomaticAbility(
            name=name,
            trigger_condition=TriggerCondition.DECLARES_ATTACK,
            effects=effects,
            is_mandatory=True
        )

    @staticmethod
    def damage_ability(name: str, effects: List[Effect],
                       battle_only: bool = False) -> AutomaticAbility:
        """Create a 'when deals damage' ability."""
        return AutomaticAbility(
            name=name,
            trigger_condition=(TriggerCondition.DEALS_BATTLE_DAMAGE if battle_only
                               else TriggerCondition.DEALS_DAMAGE),
            effects=effects,
            is_mandatory=True
        )

    @staticmethod
    def tap_ability(name: str, effects: List[Effect],
                    will_cost: 'WillCost' = None) -> ActivateAbility:
        """Create a tap ability."""
        return ActivateAbility(
            name=name,
            tap_cost=True,
            will_cost=will_cost,
            effects=effects
        )

    @staticmethod
    def will_ability(colors: List[Any], tap: bool = True) -> WillAbility:
        """Create a will production ability."""
        return WillAbility(
            name="Produce Will",
            tap_cost=tap,
            will_colors=colors,
            choose_color=len(colors) > 1
        )

    @staticmethod
    def continuous_buff(atk: int = 0, def_: int = 0,
                        filter_=None, name: str = "") -> ContinuousAbility:
        """Create a continuous buff ability."""
        from .effects import ContinuousEffect

        return ContinuousAbility(
            name=name or f"+{atk}/+{def_}",
            continuous_effect=ContinuousEffect(
                name=name,
                atk_modifier=atk,
                def_modifier=def_,
                affected_filter=filter_,
                duration=EffectDuration.WHILE_ON_FIELD
            )
        )


# =============================================================================
# MODAL ABILITIES (CR 903.2)
# =============================================================================

@dataclass
class ModalAbility(ActivateAbility):
    """
    A modal ability that lets the player choose from options.

    CR 903.2a: If a spell/ability says "choose one", "choose two", etc.,
    the player makes those choices as it's played.
    """
    # List of (name, effect) tuples for choices
    choices: List[tuple] = field(default_factory=list)

    # How many choices to make
    choose_count: int = 1

    # Whether "up to" is allowed
    up_to: bool = False

    # Upgrade condition (e.g., "If you control X, choose up to 3 instead")
    upgrade_condition: Optional[Condition] = None
    upgrade_count: int = 0

    def can_play(self, game: 'GameEngine', card: 'Card', player: int) -> bool:
        """Check if modal ability can be played."""
        # Base checks
        if not super().can_play(game, card, player):
            return False

        # Must have at least choose_count valid choices
        min_choices = 1 if self.up_to else self.choose_count
        if len(self.choices) < min_choices:
            return False

        return True

    def get_choose_count(self, game: 'GameEngine', card: 'Card', player: int) -> int:
        """Get how many choices the player can make (may be upgraded)."""
        if self.upgrade_condition and self.upgrade_condition.check(game, card, player):
            return self.upgrade_count
        return self.choose_count

    def resolve(self, game: 'GameEngine', card: 'Card', player: int,
                targets: List['Card'] = None, choices: dict = None) -> bool:
        """Resolve modal ability with chosen effects."""
        choices = choices or {}
        selected_indices = choices.get('modal_choices', [])

        if not selected_indices:
            # If no choices provided, this shouldn't happen in normal play
            return False

        # Execute selected effects
        for idx in selected_indices:
            if 0 <= idx < len(self.choices):
                name, effect = self.choices[idx]
                if effect:
                    effect.execute(game, card, targets or [], player)

        return True


# =============================================================================
# ALTERNATIVE COSTS
# =============================================================================

@dataclass
class IncarnationCost:
    """
    Incarnation alternative cost.

    CR 1105: Incarnation is a static ability that allows paying an
    alternative cost by banishing resonators of specified attributes.
    """
    # Required attributes of resonators to banish
    required_attributes: List[Any] = field(default_factory=list)  # List of Attribute

    # How many resonators to banish
    banish_count: int = 1

    def can_pay(self, game: 'GameEngine', player: int) -> bool:
        """Check if player can pay this incarnation cost."""
        # Count available resonators with required attributes
        available = 0
        for card in game.players[player].field:
            if card.data and card.data.is_resonator():
                card_attr = card.data.attribute
                if card_attr in self.required_attributes:
                    available += 1

        return available >= self.banish_count

    def pay(self, game: 'GameEngine', player: int, chosen_cards: List['Card']) -> bool:
        """Pay the incarnation cost by banishing chosen cards."""
        if len(chosen_cards) < self.banish_count:
            return False

        for card in chosen_cards[:self.banish_count]:
            game.banish_card(card)

        return True


@dataclass
class AwakeningCost:
    """
    Awakening enhanced cost.

    CR 1102: Awakening is a static ability that allows paying an
    extra cost for an enhanced effect.
    """
    # Extra will to pay for awakening
    light: int = 0
    fire: int = 0
    water: int = 0
    wind: int = 0
    darkness: int = 0
    generic: int = 0

    # Whether awakening uses X
    x_cost: bool = False

    def get_total_will(self) -> Dict[str, int]:
        """Get the extra will cost as a dict."""
        return {
            'LIGHT': self.light,
            'FIRE': self.fire,
            'WATER': self.water,
            'WIND': self.wind,
            'DARKNESS': self.darkness,
            'GENERIC': self.generic,
        }

    def can_pay(self, game: 'GameEngine', player: int, x_value: int = 0) -> bool:
        """Check if player can pay this awakening cost."""
        will_pool = game.players[player].will_pool

        # Calculate total needed
        total_needed = self.generic
        if self.x_cost:
            total_needed += x_value

        for attr, count in self.get_total_will().items():
            if attr == 'GENERIC':
                continue
            # Check specific attribute will
            attr_available = will_pool.get(attr, 0)
            if attr_available < count:
                total_needed += (count - attr_available)

        return will_pool.total() >= total_needed

    def pay(self, game: 'GameEngine', player: int, x_value: int = 0) -> bool:
        """Pay the awakening cost."""
        will_pool = game.players[player].will_pool

        for attr, count in self.get_total_will().items():
            if attr == 'GENERIC':
                continue
            if count > 0:
                will_pool.pay_specific(attr, count)

        generic_total = self.generic
        if self.x_cost:
            generic_total += x_value

        if generic_total > 0:
            will_pool.pay_generic(generic_total)

        return True
