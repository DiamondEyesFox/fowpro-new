"""
Cost System for Force of Will.

Implements complete cost handling per CR 402 and CR 1002.

References:
- CR 402: Costs
- CR 402.1: Costs are what must be paid to play/use something
- CR 402.2: Total cost = base cost + additions - reductions
- CR 402.3: Restrictions on cost payment
- CR 402.4: Alternative costs replace base cost
- CR 1002: Cost actions (rest, banish, discard, etc.)
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import TYPE_CHECKING, List, Optional, Dict, Callable, Any, Tuple, Set

if TYPE_CHECKING:
    from ..engine import GameEngine
    from ..models import Card

from .types import KeywordAbility


class CostType(Enum):
    """
    Types of costs that can be paid.

    CR 402: Various cost types.
    """
    # Will/mana cost
    WILL = "will"

    # Life payment (CR 105.4a)
    LIFE = "life"

    # Rest cost (CR 1002.1)
    REST = "rest"

    # Banish cost (CR 1002.2)
    BANISH = "banish"

    # Discard cost
    DISCARD = "discard"

    # Remove from game
    REMOVE_FROM_GAME = "remove_from_game"

    # Put into graveyard
    PUT_INTO_GRAVEYARD = "put_into_graveyard"

    # Counter manipulation
    REMOVE_COUNTER = "remove_counter"
    ADD_COUNTER = "add_counter"

    # Reveal
    REVEAL = "reveal"

    # Pay X (variable)
    PAY_X = "pay_x"


class WillType(Enum):
    """
    Types of will (mana).

    CR 407: Will production and types.
    """
    LIGHT = "light"
    FIRE = "fire"
    WATER = "water"
    WIND = "wind"
    DARKNESS = "darkness"
    VOID = "void"       # Colorless/generic
    MOON = "moon"       # Special
    SPECIAL = "special"  # X or other special


@dataclass
class WillCost:
    """
    Represents will (mana) cost.

    CR 402.1: The total cost to play a card.
    """
    # Colored will requirements
    light: int = 0
    fire: int = 0
    water: int = 0
    wind: int = 0
    darkness: int = 0

    # Generic/void (can be paid with any color)
    void: int = 0

    # Moon will (special)
    moon: int = 0

    # X cost (variable)
    x_count: int = 0  # How many X's in the cost

    def total(self) -> int:
        """Get total will cost (converted will cost)."""
        return (self.light + self.fire + self.water + self.wind +
                self.darkness + self.void + self.moon)

    @classmethod
    def parse(cls, cost_string: str) -> 'WillCost':
        """
        Parse a cost string like '{2}{R}{R}' or '1RR' into WillCost.

        Supports formats:
        - {X} notation: {1}{R}{R}
        - Compact notation: 1RR
        - Mixed: {2}RR
        """
        cost = cls()

        if not cost_string:
            return cost

        # Normalize - remove braces
        s = cost_string.replace('{', '').replace('}', '')

        i = 0
        while i < len(s):
            c = s[i].upper()

            if c.isdigit():
                # Parse number
                num_str = c
                while i + 1 < len(s) and s[i + 1].isdigit():
                    i += 1
                    num_str += s[i]
                cost.void += int(num_str)
            elif c == 'W' or c == 'L':  # White/Light
                cost.light += 1
            elif c == 'R' or c == 'F':  # Red/Fire
                cost.fire += 1
            elif c == 'U' or c == 'B':  # Blue/Water
                cost.water += 1
            elif c == 'G':  # Green/Wind
                cost.wind += 1
            elif c == 'K' or c == 'D':  # Black/Darkness
                cost.darkness += 1
            elif c == 'M':  # Moon
                cost.moon += 1
            elif c == 'X':
                cost.x_count += 1
            elif c == 'V':  # Void explicit
                cost.void += 1

            i += 1

        return cost

    def can_pay(self, will_pool: Dict[str, int]) -> bool:
        """Check if this cost can be paid from a will pool."""
        # Calculate available colored will
        available = {
            'light': will_pool.get('light', 0),
            'fire': will_pool.get('fire', 0),
            'water': will_pool.get('water', 0),
            'wind': will_pool.get('wind', 0),
            'darkness': will_pool.get('darkness', 0),
            'moon': will_pool.get('moon', 0),
        }

        # Check colored requirements
        if available['light'] < self.light:
            return False
        if available['fire'] < self.fire:
            return False
        if available['water'] < self.water:
            return False
        if available['wind'] < self.wind:
            return False
        if available['darkness'] < self.darkness:
            return False
        if available['moon'] < self.moon:
            return False

        # Deduct colored costs
        remaining = (
            available['light'] - self.light +
            available['fire'] - self.fire +
            available['water'] - self.water +
            available['wind'] - self.wind +
            available['darkness'] - self.darkness +
            available['moon'] - self.moon
        )

        # Add void/colorless will from pool
        remaining += will_pool.get('void', 0)

        # Check void requirement
        return remaining >= self.void

    def __str__(self) -> str:
        """String representation of cost."""
        parts = []
        if self.void:
            parts.append(str(self.void))
        if self.light:
            parts.append('L' * self.light)
        if self.fire:
            parts.append('F' * self.fire)
        if self.water:
            parts.append('U' * self.water)
        if self.wind:
            parts.append('W' * self.wind)
        if self.darkness:
            parts.append('D' * self.darkness)
        if self.moon:
            parts.append('M' * self.moon)
        if self.x_count:
            parts.append('X' * self.x_count)
        return ''.join(parts) if parts else '0'


@dataclass
class AdditionalCost:
    """
    An additional cost beyond will.

    CR 402.1: Additional costs must be paid along with will cost.
    """
    cost_type: CostType

    # For REST, BANISH, DISCARD: how many/what kind
    count: int = 1

    # Filter for what can be used to pay
    filter_description: str = ""  # e.g., "a resonator you control"

    # Specific card types/races that qualify
    card_types: List[str] = field(default_factory=list)
    races: List[str] = field(default_factory=list)

    # For counter costs
    counter_type: str = ""

    # For life costs
    life_amount: int = 0

    # For reveal costs
    reveal_from_hand: bool = False
    reveal_attribute: str = ""

    # Custom validation function
    validator: Optional[Callable] = None


@dataclass
class AlternativeCost:
    """
    An alternative cost that replaces the base cost.

    CR 402.4: Alternative costs replace the entire base cost.
    CR 1111: Incarnation is an alternative cost.
    """
    name: str = ""  # e.g., "Incarnation", "Flashback"

    # What keyword enables this (if any)
    keyword: KeywordAbility = KeywordAbility.NONE

    # The alternative will cost (if any)
    will_cost: Optional[WillCost] = None

    # Additional costs required
    additional_costs: List[AdditionalCost] = field(default_factory=list)

    # Condition for this alternative to be available
    condition: Optional[Callable] = None

    # What happens when used (e.g., exile after for Remnant)
    on_use: Optional[Callable] = None


@dataclass
class CostReduction:
    """
    A cost reduction effect.

    CR 402.2: Total cost includes reductions.
    """
    effect_id: str = ""
    source_id: str = ""
    name: str = ""

    # Will reduction
    reduce_void: int = 0
    reduce_colored: Dict[str, int] = field(default_factory=dict)
    reduce_total: int = 0  # Reduces total, applied after colored

    # Condition for this reduction to apply
    condition: Optional[Callable] = None

    # What cards this applies to
    applies_to_filter: Optional[Callable] = None


@dataclass
class CostIncrease:
    """
    A cost increase effect.

    CR 402.2: Total cost includes additions.
    """
    effect_id: str = ""
    source_id: str = ""
    name: str = ""

    # Will increase
    increase_void: int = 0
    increase_colored: Dict[str, int] = field(default_factory=dict)

    # Additional costs added
    additional_costs: List[AdditionalCost] = field(default_factory=list)

    # Condition for this increase to apply
    condition: Optional[Callable] = None

    # What cards this applies to
    applies_to_filter: Optional[Callable] = None


@dataclass
class CostPaymentPlan:
    """
    A complete plan for how to pay a cost.

    This is generated when a player decides to play something,
    showing exactly what will be spent.
    """
    # Will to pay
    will_to_spend: Dict[str, int] = field(default_factory=dict)

    # Cards to rest
    cards_to_rest: List['Card'] = field(default_factory=list)

    # Cards to banish
    cards_to_banish: List['Card'] = field(default_factory=list)

    # Cards to discard
    cards_to_discard: List['Card'] = field(default_factory=list)

    # Cards to remove from game
    cards_to_remove: List['Card'] = field(default_factory=list)

    # Life to pay
    life_to_pay: int = 0

    # Counters to remove
    counters_to_remove: Dict[str, int] = field(default_factory=dict)

    # Cards to reveal
    cards_to_reveal: List['Card'] = field(default_factory=list)

    # X value chosen
    x_value: int = 0

    # Which alternative cost is being used (if any)
    alternative_used: Optional[str] = None

    # Which awakening was chosen (if any)
    awakening_used: bool = False


class CostManager:
    """
    Manages cost calculation and payment.

    CR 402: Complete cost management.
    """

    def __init__(self, game: 'GameEngine'):
        self.game = game

        # Registered cost modifiers
        self.reductions: Dict[str, CostReduction] = {}
        self.increases: Dict[str, CostIncrease] = {}

        # Effect counter for unique IDs
        self._effect_counter = 0

    def register_reduction(self, reduction: CostReduction) -> str:
        """Register a cost reduction effect."""
        self._effect_counter += 1
        effect_id = f"red_{self._effect_counter:06d}"
        reduction.effect_id = effect_id
        self.reductions[effect_id] = reduction
        return effect_id

    def register_increase(self, increase: CostIncrease) -> str:
        """Register a cost increase effect."""
        self._effect_counter += 1
        effect_id = f"inc_{self._effect_counter:06d}"
        increase.effect_id = effect_id
        self.increases[effect_id] = increase
        return effect_id

    def unregister_effect(self, effect_id: str):
        """Remove a cost modifier."""
        if effect_id in self.reductions:
            del self.reductions[effect_id]
        if effect_id in self.increases:
            del self.increases[effect_id]

    def unregister_from_source(self, source_id: str):
        """Remove all cost modifiers from a source."""
        to_remove = [
            eid for eid, e in self.reductions.items()
            if e.source_id == source_id
        ]
        for eid in to_remove:
            del self.reductions[eid]

        to_remove = [
            eid for eid, e in self.increases.items()
            if e.source_id == source_id
        ]
        for eid in to_remove:
            del self.increases[eid]

    def get_base_cost(self, card: 'Card') -> WillCost:
        """
        Get the base will cost for a card.

        CR 402.1: Base cost comes from card definition.
        """
        if card.data and card.data.cost:
            # Handle both string and WillCost types
            if isinstance(card.data.cost, str):
                return WillCost.parse(card.data.cost)
            elif hasattr(card.data.cost, 'total'):
                # Already a WillCost-like object, convert it
                cost = WillCost()
                if hasattr(card.data.cost, 'to_dict'):
                    cost_dict = card.data.cost.to_dict()
                    cost.light = cost_dict.get('light', 0)
                    cost.fire = cost_dict.get('fire', 0)
                    cost.water = cost_dict.get('water', 0)
                    cost.wind = cost_dict.get('wind', 0)
                    cost.darkness = cost_dict.get('darkness', 0)
                    cost.void = cost_dict.get('void', 0)
                return cost
        return WillCost()

    def get_total_cost(self, card: 'Card', player: int,
                       alternative: AlternativeCost = None) -> Tuple[WillCost, List[AdditionalCost]]:
        """
        Calculate the total cost to play a card.

        CR 402.2: Total cost = base + increases - reductions.

        Returns (will_cost, additional_costs).
        """
        # Start with base or alternative cost
        if alternative and alternative.will_cost:
            will_cost = alternative.will_cost
            additional = list(alternative.additional_costs)
        else:
            will_cost = self.get_base_cost(card)
            additional = self._get_base_additional_costs(card)

        # Apply increases
        for inc in self.increases.values():
            if self._modifier_applies(inc, card, player):
                will_cost.void += inc.increase_void
                for color, amount in inc.increase_colored.items():
                    setattr(will_cost, color, getattr(will_cost, color, 0) + amount)
                additional.extend(inc.additional_costs)

        # Apply reductions
        for red in self.reductions.values():
            if self._modifier_applies(red, card, player):
                will_cost.void = max(0, will_cost.void - red.reduce_void)
                for color, amount in red.reduce_colored.items():
                    current = getattr(will_cost, color, 0)
                    setattr(will_cost, color, max(0, current - amount))
                if red.reduce_total > 0:
                    # Reduce void first, then any color
                    remaining = red.reduce_total
                    if will_cost.void > 0:
                        reduce_void = min(will_cost.void, remaining)
                        will_cost.void -= reduce_void
                        remaining -= reduce_void
                    # Could reduce colored here if needed

        return will_cost, additional

    def _get_base_additional_costs(self, card: 'Card') -> List[AdditionalCost]:
        """Get any additional costs from the card definition."""
        additional = []

        # Parse from card text/data
        if card.data and card.data.ability_text:
            text = card.data.ability_text.lower()

            # Rest this card pattern
            if "[rest]" in text or "rest:" in text:
                additional.append(AdditionalCost(
                    cost_type=CostType.REST,
                    count=1,
                    filter_description="this card"
                ))

            # Banish patterns
            if "banish " in text and " as an additional cost" in text:
                additional.append(AdditionalCost(
                    cost_type=CostType.BANISH,
                    count=1,
                    filter_description="a resonator you control"
                ))

            # Discard patterns
            if "discard a card" in text:
                additional.append(AdditionalCost(
                    cost_type=CostType.DISCARD,
                    count=1
                ))

        return additional

    def _modifier_applies(self, modifier, card: 'Card', player: int) -> bool:
        """Check if a cost modifier applies to a card."""
        # Check source still exists
        source = self.game.get_card(modifier.source_id)
        if not source:
            return False

        # Check condition
        if hasattr(modifier, 'condition') and modifier.condition:
            if not modifier.condition(self.game, source, card, player):
                return False

        # Check filter
        if hasattr(modifier, 'applies_to_filter') and modifier.applies_to_filter:
            if not modifier.applies_to_filter(card, player):
                return False

        return True

    def get_available_alternatives(self, card: 'Card', player: int) -> List[AlternativeCost]:
        """
        Get available alternative costs for a card.

        CR 402.4: Check which alternative costs can be used.
        """
        alternatives = []

        # Check Incarnation (CR 1111)
        if card.data and KeywordAbility.INCARNATION in (card.data.keywords or KeywordAbility.NONE):
            incarnation = self._build_incarnation_cost(card)
            if incarnation and self._can_use_alternative(incarnation, card, player):
                alternatives.append(incarnation)

        # Check Remnant (CR 1115) - play from graveyard
        from ..models import Zone
        if card.zone == Zone.GRAVEYARD:
            if card.data and KeywordAbility.REMNANT in (card.data.keywords or KeywordAbility.NONE):
                remnant = AlternativeCost(
                    name="Remnant",
                    keyword=KeywordAbility.REMNANT,
                    will_cost=self.get_base_cost(card),
                    on_use=lambda g, c: g.remove_from_game(c)  # Exile after
                )
                if self._can_use_alternative(remnant, card, player):
                    alternatives.append(remnant)

        return alternatives

    def _build_incarnation_cost(self, card: 'Card') -> Optional[AlternativeCost]:
        """Build the Incarnation alternative cost from card text."""
        if not card.data or not card.data.ability_text:
            return None

        text = card.data.ability_text.lower()

        # Look for Incarnation specification
        if "incarnation:" not in text:
            return None

        # Parse the required race
        import re
        match = re.search(r'incarnation:\s*(\w+)', text)
        if match:
            race = match.group(1)
            return AlternativeCost(
                name=f"Incarnation ({race})",
                keyword=KeywordAbility.INCARNATION,
                will_cost=WillCost(),  # Free will cost
                additional_costs=[
                    AdditionalCost(
                        cost_type=CostType.BANISH,
                        count=1,
                        filter_description=f"a {race} resonator you control",
                        races=[race],
                    )
                ]
            )

        return None

    def _can_use_alternative(self, alt: AlternativeCost, card: 'Card', player: int) -> bool:
        """Check if an alternative cost can be used."""
        if alt.condition:
            source = self.game.get_card(card.uid)
            if not alt.condition(self.game, source, player):
                return False

        # Check if additional costs can be paid
        for add_cost in alt.additional_costs:
            if not self._can_pay_additional_cost(add_cost, player, card):
                return False

        return True

    def get_awakening_cost(self, card: 'Card') -> Optional[Tuple[WillCost, List[AdditionalCost]]]:
        """
        Get the awakening cost for a card with Awakening.

        CR 1110: Awakening is an additional cost for a bonus effect.
        """
        if not card.data or not card.data.ability_text:
            return None

        text = card.data.ability_text.lower()

        if "awakening" not in text:
            return None

        # Parse awakening cost from text
        import re
        match = re.search(r'awakening[:\s]+\{?([0-9WRUBGKDLFM]+)\}?', text, re.IGNORECASE)
        if match:
            awakening_will = WillCost.parse(match.group(1))
            return (awakening_will, [])

        return None

    def can_pay_cost(self, card: 'Card', player: int,
                     alternative: AlternativeCost = None,
                     awakening: bool = False) -> bool:
        """
        Check if a player can pay the cost for a card.

        CR 402.3: Check if cost can be paid.
        """
        will_cost, additional = self.get_total_cost(card, player, alternative)

        # Add awakening cost if requested
        if awakening:
            awk = self.get_awakening_cost(card)
            if awk:
                awk_will, awk_add = awk
                will_cost.void += awk_will.void
                will_cost.light += awk_will.light
                will_cost.fire += awk_will.fire
                will_cost.water += awk_will.water
                will_cost.wind += awk_will.wind
                will_cost.darkness += awk_will.darkness
                additional.extend(awk_add)

        # Check will
        will_pool = self.game.get_will_pool(player)
        if not will_cost.can_pay(will_pool):
            return False

        # Check additional costs
        for add_cost in additional:
            if not self._can_pay_additional_cost(add_cost, player, card):
                return False

        return True

    def _can_pay_additional_cost(self, cost: AdditionalCost, player: int,
                                  source_card: 'Card' = None) -> bool:
        """Check if an additional cost can be paid."""
        p = self.game.players[player]

        if cost.cost_type == CostType.LIFE:
            return p.life > cost.life_amount  # Must have more life than paying

        elif cost.cost_type == CostType.REST:
            # Find valid cards to rest
            valid = [c for c in p.field if not c.is_rested]
            if source_card and cost.filter_description == "this card":
                valid = [c for c in valid if c.uid == source_card.uid]
            return len(valid) >= cost.count

        elif cost.cost_type == CostType.BANISH:
            # Find valid cards to banish
            valid = self._get_valid_banish_targets(player, cost)
            return len(valid) >= cost.count

        elif cost.cost_type == CostType.DISCARD:
            return len(p.hand) >= cost.count

        elif cost.cost_type == CostType.REMOVE_COUNTER:
            # Check if source has enough counters
            if source_card:
                return source_card.counters.get(cost.counter_type, 0) >= cost.count
            return False

        elif cost.cost_type == CostType.REVEAL:
            # Check if hand has matching card
            if cost.reveal_attribute:
                matching = [c for c in p.hand
                            if c.data and cost.reveal_attribute in (c.data.attribute or '')]
                return len(matching) >= cost.count
            return len(p.hand) >= cost.count

        return True

    def _get_valid_banish_targets(self, player: int, cost: AdditionalCost) -> List['Card']:
        """Get cards that can be banished for a cost."""
        p = self.game.players[player]
        valid = list(p.field)

        # Filter by card types
        if cost.card_types:
            from ..models import CardType
            valid = [c for c in valid if c.data and
                     str(c.data.card_type.value) in cost.card_types]

        # Filter by races
        if cost.races:
            valid = [c for c in valid if c.data and
                     any(r.lower() in (c.data.race or '').lower() for r in cost.races)]

        # Custom validator
        if cost.validator:
            valid = [c for c in valid if cost.validator(c)]

        return valid

    def pay_cost(self, card: 'Card', player: int, plan: CostPaymentPlan) -> bool:
        """
        Execute a cost payment plan.

        CR 402.1: Pay the cost to play the card/ability.

        Returns True if successful, False if something failed.
        """
        p = self.game.players[player]

        try:
            # Pay will
            for will_type, amount in plan.will_to_spend.items():
                if not self.game.spend_will(player, will_type, amount):
                    return False

            # Pay life
            if plan.life_to_pay > 0:
                if p.life <= plan.life_to_pay:
                    return False
                p.life -= plan.life_to_pay

            # Rest cards
            for c in plan.cards_to_rest:
                if c.is_rested:
                    return False
                c.is_rested = True

            # Banish cards
            from ..models import Zone
            for c in plan.cards_to_banish:
                self.game.move_card(c, Zone.REMOVED)

            # Discard cards
            for c in plan.cards_to_discard:
                self.game.move_card(c, Zone.GRAVEYARD)

            # Remove from game
            for c in plan.cards_to_remove:
                self.game.move_card(c, Zone.REMOVED)

            # Remove counters
            for counter_type, count in plan.counters_to_remove.items():
                if card.counters.get(counter_type, 0) < count:
                    return False
                card.counters[counter_type] -= count

            # Handle alternative cost effects
            if plan.alternative_used:
                # Find and apply the alternative's on_use callback
                alts = self.get_available_alternatives(card, player)
                for alt in alts:
                    if alt.name == plan.alternative_used and alt.on_use:
                        alt.on_use(self.game, card)

            return True

        except Exception as e:
            print(f"[ERROR] Cost payment failed: {e}")
            return False

    def generate_payment_plan(self, card: 'Card', player: int,
                              alternative: AlternativeCost = None,
                              awakening: bool = False,
                              x_value: int = 0) -> Optional[CostPaymentPlan]:
        """
        Generate a payment plan for a cost.

        This is called by AI or can be used as a starting point for UI.
        """
        plan = CostPaymentPlan()
        plan.x_value = x_value

        if alternative:
            plan.alternative_used = alternative.name

        plan.awakening_used = awakening

        # Calculate total cost
        will_cost, additional = self.get_total_cost(card, player, alternative)

        if awakening:
            awk = self.get_awakening_cost(card)
            if awk:
                awk_will, _ = awk
                will_cost.void += awk_will.void
                will_cost.light += awk_will.light
                # ... etc

        # Add X cost
        if will_cost.x_count and x_value:
            will_cost.void += x_value * will_cost.x_count

        # Plan will payment
        will_pool = self.game.get_will_pool(player)

        # Pay colored first
        for color in ['light', 'fire', 'water', 'wind', 'darkness', 'moon']:
            needed = getattr(will_cost, color, 0)
            if needed > 0:
                available = will_pool.get(color, 0)
                if available < needed:
                    return None  # Can't pay
                plan.will_to_spend[color] = needed

        # Pay void with remaining will
        remaining_pool = dict(will_pool)
        for color, spent in plan.will_to_spend.items():
            remaining_pool[color] = remaining_pool.get(color, 0) - spent

        void_needed = will_cost.void

        # First use void/colorless will from pool for void costs
        void_available = remaining_pool.get('void', 0)
        if void_available > 0 and void_needed > 0:
            use = min(void_available, void_needed)
            plan.will_to_spend['void'] = plan.will_to_spend.get('void', 0) + use
            void_needed -= use

        # Then use remaining colored will for void costs
        for color in ['light', 'fire', 'water', 'wind', 'darkness', 'moon']:
            if void_needed <= 0:
                break
            available = remaining_pool.get(color, 0)
            if available > 0:
                use = min(available, void_needed)
                plan.will_to_spend[color] = plan.will_to_spend.get(color, 0) + use
                void_needed -= use

        if void_needed > 0:
            return None  # Can't pay void

        # Plan additional costs
        p = self.game.players[player]
        for add_cost in additional:
            if add_cost.cost_type == CostType.LIFE:
                plan.life_to_pay += add_cost.life_amount

            elif add_cost.cost_type == CostType.REST:
                if add_cost.filter_description == "this card":
                    plan.cards_to_rest.append(card)
                else:
                    # Find cards to rest
                    valid = [c for c in p.field if not c.is_rested
                             and c not in plan.cards_to_rest]
                    if len(valid) < add_cost.count:
                        return None
                    plan.cards_to_rest.extend(valid[:add_cost.count])

            elif add_cost.cost_type == CostType.BANISH:
                valid = self._get_valid_banish_targets(player, add_cost)
                valid = [c for c in valid if c not in plan.cards_to_banish]
                if len(valid) < add_cost.count:
                    return None
                plan.cards_to_banish.extend(valid[:add_cost.count])

            elif add_cost.cost_type == CostType.DISCARD:
                valid = [c for c in p.hand if c not in plan.cards_to_discard]
                if len(valid) < add_cost.count:
                    return None
                plan.cards_to_discard.extend(valid[:add_cost.count])

            elif add_cost.cost_type == CostType.REMOVE_COUNTER:
                plan.counters_to_remove[add_cost.counter_type] = add_cost.count

        return plan


# Builder helpers
class CostBuilder:
    """Helper for building common costs."""

    @staticmethod
    def will(cost_string: str) -> WillCost:
        """Parse a will cost string."""
        return WillCost.parse(cost_string)

    @staticmethod
    def tap_cost() -> AdditionalCost:
        """Create a tap/rest cost."""
        return AdditionalCost(
            cost_type=CostType.REST,
            count=1,
            filter_description="this card"
        )

    @staticmethod
    def banish_resonator(race: str = None) -> AdditionalCost:
        """Create a banish resonator cost."""
        cost = AdditionalCost(
            cost_type=CostType.BANISH,
            count=1,
            card_types=["resonator"],
        )
        if race:
            cost.races = [race]
            cost.filter_description = f"a {race} resonator you control"
        else:
            cost.filter_description = "a resonator you control"
        return cost

    @staticmethod
    def discard(count: int = 1) -> AdditionalCost:
        """Create a discard cost."""
        return AdditionalCost(
            cost_type=CostType.DISCARD,
            count=count
        )

    @staticmethod
    def pay_life(amount: int) -> AdditionalCost:
        """Create a life payment cost."""
        return AdditionalCost(
            cost_type=CostType.LIFE,
            life_amount=amount
        )

    @staticmethod
    def remove_counter(counter_type: str, count: int = 1) -> AdditionalCost:
        """Create a remove counter cost."""
        return AdditionalCost(
            cost_type=CostType.REMOVE_COUNTER,
            counter_type=counter_type,
            count=count
        )

    @staticmethod
    def reveal_attribute(attribute: str) -> AdditionalCost:
        """Create a reveal from hand cost."""
        return AdditionalCost(
            cost_type=CostType.REVEAL,
            reveal_from_hand=True,
            reveal_attribute=attribute
        )
