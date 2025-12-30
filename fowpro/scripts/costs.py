"""
Cost System
===========

Handles all types of costs in FoW:
- Will costs (colored and generic)
- Rest/Tap costs
- Life payment
- Sacrifice
- Discard
- Banish from graveyard
- Counter removal
- Additional costs (on cast effects)
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Callable, Optional, List, Dict, Any, TYPE_CHECKING
import re

if TYPE_CHECKING:
    from ..engine import GameEngine
    from ..models import Card, Player


class CostType(Enum):
    """Types of costs"""
    WILL = auto()           # Mana payment
    REST = auto()           # Tap this card
    LIFE = auto()           # Pay life
    SACRIFICE = auto()      # Sacrifice cards
    DISCARD = auto()        # Discard cards
    BANISH = auto()         # Banish from graveyard
    COUNTER = auto()        # Remove counters
    REVEAL = auto()         # Reveal cards from hand
    EXILE = auto()          # Exile cards from hand/field


@dataclass
class WillCost:
    """Will/mana cost component"""
    generic: int = 0
    light: int = 0          # W
    fire: int = 0           # R
    water: int = 0          # U
    wind: int = 0           # G
    darkness: int = 0       # B
    void_: int = 0          # V

    @property
    def total(self) -> int:
        """Total will required"""
        return (self.generic + self.light + self.fire + self.water +
                self.wind + self.darkness + self.void_)

    def to_dict(self) -> Dict[str, int]:
        """Convert to attribute->count mapping"""
        result = {}
        if self.light > 0:
            result['LIGHT'] = self.light
        if self.fire > 0:
            result['FIRE'] = self.fire
        if self.water > 0:
            result['WATER'] = self.water
        if self.wind > 0:
            result['WIND'] = self.wind
        if self.darkness > 0:
            result['DARKNESS'] = self.darkness
        if self.void_ > 0:
            result['VOID'] = self.void_
        if self.generic > 0:
            result['GENERIC'] = self.generic
        return result

    @classmethod
    def from_text(cls, text: str) -> 'WillCost':
        """Parse will cost from text like '{2}{G}{G}' or '2GG'"""
        cost = cls()

        # Pattern for {X} format
        symbols = re.findall(r'\{(\d+|[WRUGBV])\}', text.upper())
        for symbol in symbols:
            if symbol.isdigit():
                cost.generic += int(symbol)
            elif symbol == 'W':
                cost.light += 1
            elif symbol == 'R':
                cost.fire += 1
            elif symbol == 'U':
                cost.water += 1
            elif symbol == 'G':
                cost.wind += 1
            elif symbol == 'B':
                cost.darkness += 1
            elif symbol == 'V':
                cost.void_ += 1

        return cost


@dataclass
class SacrificeCost:
    """Sacrifice cost component"""
    count: int = 1                          # How many to sacrifice
    card_type: Optional[str] = None         # 'resonator', 'stone', etc.
    attribute: Optional[str] = None         # Required attribute
    name_contains: Optional[str] = None     # Name filter
    custom_filter: Optional[Callable[['Card'], bool]] = None


@dataclass
class DiscardCost:
    """Discard cost component"""
    count: int = 1                          # How many to discard
    card_type: Optional[str] = None         # Required card type
    random: bool = False                    # Random discard


@dataclass
class BanishCost:
    """Banish from graveyard cost"""
    count: int = 1
    card_type: Optional[str] = None


@dataclass
class Cost:
    """Complete cost for a card or ability"""
    will: WillCost = field(default_factory=WillCost)
    rest: bool = False                      # Tap this card
    life: int = 0                           # Life to pay
    sacrifice: Optional[SacrificeCost] = None
    discard: Optional[DiscardCost] = None
    banish: Optional[BanishCost] = None
    remove_counters: Optional[tuple] = None  # (counter_type, count)

    @classmethod
    def parse(cls, cost_text: str) -> 'Cost':
        """Parse a cost string into a Cost object"""
        cost = cls()
        text_lower = cost_text.lower()

        # Parse rest/tap cost
        if '{rest}' in text_lower or 'rest' in text_lower:
            cost.rest = True

        # Parse will cost
        cost.will = WillCost.from_text(cost_text)

        # Parse life payment
        life_match = re.search(r'pay\s+(\d+)\s+life', text_lower)
        if life_match:
            cost.life = int(life_match.group(1))

        # Parse sacrifice
        if 'sacrifice' in text_lower:
            count = 1
            count_match = re.search(r'sacrifice\s+(\d+)', text_lower)
            if count_match:
                count = int(count_match.group(1))

            card_type = None
            for t in ['resonator', 'stone', 'addition']:
                if t in text_lower:
                    card_type = t
                    break

            cost.sacrifice = SacrificeCost(count=count, card_type=card_type)

        # Parse discard
        discard_match = re.search(r'discard\s+(?:(\d+)\s+)?cards?', text_lower)
        if discard_match or 'discard' in text_lower:
            count = int(discard_match.group(1)) if discard_match and discard_match.group(1) else 1
            cost.discard = DiscardCost(count=count)

        # Parse banish
        if 'banish' in text_lower and 'graveyard' in text_lower:
            count = 1
            banish_match = re.search(r'banish\s+(\d+)', text_lower)
            if banish_match:
                count = int(banish_match.group(1))
            cost.banish = BanishCost(count=count)

        # Parse counter removal
        counter_match = re.search(r'remove\s+(?:(\d+)\s+)?(\w+)\s+counters?', text_lower)
        if counter_match:
            count = int(counter_match.group(1)) if counter_match.group(1) else 1
            counter_type = counter_match.group(2)
            cost.remove_counters = (counter_type, count)

        return cost


class CostValidator:
    """Validates if a player can pay a cost"""

    def __init__(self, game: 'GameEngine'):
        self.game = game

    def can_pay(self, player: 'Player', cost: Cost,
                source: Optional['Card'] = None) -> bool:
        """Check if player can pay the full cost"""

        # Check will
        if not self._can_pay_will(player, cost.will):
            return False

        # Check rest (source must be recovered)
        if cost.rest and source:
            if source.is_rested:
                return False

        # Check life
        if cost.life > 0:
            if player.life <= cost.life:
                return False

        # Check sacrifice
        if cost.sacrifice:
            if not self._can_sacrifice(player, cost.sacrifice, source):
                return False

        # Check discard
        if cost.discard:
            hand_count = len([c for c in player.hand if c != source])
            if hand_count < cost.discard.count:
                return False

        # Check banish
        if cost.banish:
            grave_count = len(player.graveyard)
            if grave_count < cost.banish.count:
                return False

        # Check counter removal
        if cost.remove_counters and source:
            counter_type, count = cost.remove_counters
            current = getattr(source, f'{counter_type}_counters', 0)
            if current < count:
                return False

        return True

    def _can_pay_will(self, player: 'Player', will_cost: WillCost) -> bool:
        """Check if player can pay will cost"""
        available = player.will_pool.copy()

        # Pay colored costs first (strict)
        for attr, required in [
            ('LIGHT', will_cost.light),
            ('FIRE', will_cost.fire),
            ('WATER', will_cost.water),
            ('WIND', will_cost.wind),
            ('DARKNESS', will_cost.darkness),
            ('VOID', will_cost.void_),
        ]:
            if required > 0:
                have = available.get(attr, 0)
                if have < required:
                    return False
                available[attr] = have - required

        # Pay generic with remaining will
        remaining = sum(available.values())
        if remaining < will_cost.generic:
            return False

        return True

    def _can_sacrifice(self, player: 'Player', sac_cost: SacrificeCost,
                      source: Optional['Card']) -> bool:
        """Check if player has cards to sacrifice"""
        from ..models import Zone

        valid_targets = []
        for card in player.field:
            # Can't sacrifice the source of the ability
            if source and card.uid == source.uid:
                continue

            # Check card type
            if sac_cost.card_type:
                if not self._matches_type(card, sac_cost.card_type):
                    continue

            # Check attribute
            if sac_cost.attribute:
                if not card.data or card.data.attribute.name.upper() != sac_cost.attribute.upper():
                    continue

            # Check name
            if sac_cost.name_contains:
                if not card.data or sac_cost.name_contains.lower() not in card.data.name.lower():
                    continue

            # Check custom filter
            if sac_cost.custom_filter:
                if not sac_cost.custom_filter(card):
                    continue

            valid_targets.append(card)

        return len(valid_targets) >= sac_cost.count

    def _matches_type(self, card: 'Card', card_type: str) -> bool:
        """Check if card matches type filter"""
        if not card.data:
            return False

        type_lower = card_type.lower()
        card_type_name = card.data.card_type.name.lower()

        if type_lower == 'resonator':
            return 'resonator' in card_type_name
        elif type_lower == 'stone':
            return 'stone' in card_type_name
        elif type_lower == 'addition':
            return 'addition' in card_type_name

        return type_lower in card_type_name


class CostPayer:
    """Handles actual payment of costs"""

    def __init__(self, game: 'GameEngine'):
        self.game = game

    def pay(self, player: 'Player', cost: Cost,
            source: Optional['Card'] = None,
            choices: Dict[str, Any] = None) -> bool:
        """Pay the full cost. Returns True if successful."""
        choices = choices or {}

        # Pay will
        if not self._pay_will(player, cost.will):
            return False

        # Rest source
        if cost.rest and source:
            source.is_rested = True
            self.game.emit_event('card_rested', {'card': source})

        # Pay life
        if cost.life > 0:
            player.life -= cost.life
            self.game.emit_event('life_lost', {
                'player': player,
                'amount': cost.life,
            })

        # Sacrifice (requires choice of what to sacrifice)
        if cost.sacrifice:
            targets = choices.get('sacrifice_targets', [])
            for card in targets[:cost.sacrifice.count]:
                self.game.move_card(card, 'GRAVEYARD')
                self.game.emit_event('card_sacrificed', {'card': card})

        # Discard (requires choice of what to discard)
        if cost.discard:
            targets = choices.get('discard_targets', [])
            for card in targets[:cost.discard.count]:
                self.game.move_card(card, 'GRAVEYARD')
                self.game.emit_event('card_discarded', {'card': card})

        # Banish from graveyard
        if cost.banish:
            targets = choices.get('banish_targets', [])
            for card in targets[:cost.banish.count]:
                self.game.move_card(card, 'REMOVED')
                self.game.emit_event('card_banished', {'card': card})

        # Remove counters
        if cost.remove_counters and source:
            counter_type, count = cost.remove_counters
            current = getattr(source, f'{counter_type}_counters', 0)
            setattr(source, f'{counter_type}_counters', current - count)
            self.game.emit_event('counters_removed', {
                'card': source,
                'type': counter_type,
                'count': count,
            })

        return True

    def _pay_will(self, player: 'Player', will_cost: WillCost) -> bool:
        """Pay will from player's pool"""
        if will_cost.total == 0:
            return True

        # Make working copy
        available = player.will_pool.copy()

        # Pay colored first (strict)
        for attr, required in [
            ('LIGHT', will_cost.light),
            ('FIRE', will_cost.fire),
            ('WATER', will_cost.water),
            ('WIND', will_cost.wind),
            ('DARKNESS', will_cost.darkness),
            ('VOID', will_cost.void_),
        ]:
            if required > 0:
                have = available.get(attr, 0)
                if have < required:
                    return False
                available[attr] = have - required

        # Pay generic from any remaining
        generic_remaining = will_cost.generic
        for attr in list(available.keys()):
            if generic_remaining <= 0:
                break
            can_pay = min(available[attr], generic_remaining)
            available[attr] -= can_pay
            generic_remaining -= can_pay

        if generic_remaining > 0:
            return False

        # Update actual pool
        player.will_pool = available
        return True


# =============================================================================
# COST BUILDERS
# =============================================================================

def rest_cost() -> Cost:
    """Simple rest/tap cost"""
    return Cost(rest=True)


def will_cost(text: str) -> Cost:
    """Create will cost from text"""
    return Cost(will=WillCost.from_text(text))


def will_and_rest(text: str) -> Cost:
    """Will cost plus rest"""
    cost = Cost(will=WillCost.from_text(text))
    cost.rest = True
    return cost


def sacrifice_resonator(count: int = 1) -> Cost:
    """Sacrifice resonator(s) cost"""
    return Cost(sacrifice=SacrificeCost(count=count, card_type='resonator'))


def sacrifice_with_attribute(attribute: str, count: int = 1) -> Cost:
    """Sacrifice resonator(s) with specific attribute"""
    return Cost(sacrifice=SacrificeCost(
        count=count,
        card_type='resonator',
        attribute=attribute
    ))


def discard_cards(count: int = 1) -> Cost:
    """Discard card(s) cost"""
    return Cost(discard=DiscardCost(count=count))


def pay_life(amount: int) -> Cost:
    """Pay life cost"""
    return Cost(life=amount)


def banish_from_graveyard(count: int = 1) -> Cost:
    """Banish from graveyard cost"""
    return Cost(banish=BanishCost(count=count))


def combined_cost(*costs: Cost) -> Cost:
    """Combine multiple costs into one"""
    result = Cost()

    for cost in costs:
        # Add will costs
        result.will.generic += cost.will.generic
        result.will.light += cost.will.light
        result.will.fire += cost.will.fire
        result.will.water += cost.will.water
        result.will.wind += cost.will.wind
        result.will.darkness += cost.will.darkness
        result.will.void_ += cost.will.void_

        # Combine other costs
        if cost.rest:
            result.rest = True
        result.life += cost.life

        if cost.sacrifice:
            if result.sacrifice:
                result.sacrifice.count += cost.sacrifice.count
            else:
                result.sacrifice = cost.sacrifice

        if cost.discard:
            if result.discard:
                result.discard.count += cost.discard.count
            else:
                result.discard = cost.discard

        if cost.banish:
            if result.banish:
                result.banish.count += cost.banish.count
            else:
                result.banish = cost.banish

    return result
