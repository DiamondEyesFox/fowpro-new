"""
Condition system for Force of Will effects.

Handles "if you control...", "if your graveyard has...", etc.

References:
- CR 104.2: Partial effects when conditions aren't fully met
- CR 906.9: Status automatic objects (condition watching)
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Optional, Dict, Any, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from ..engine import GameEngine
    from ..models import Card


class ConditionType(Enum):
    """Types of conditions that can be checked."""

    # Control conditions
    CONTROL_CARD = "control_card"           # "if you control..."
    CONTROL_J_RULER = "control_j_ruler"     # "if you control a J-ruler..."
    CONTROL_ATTRIBUTE = "control_attribute" # "if you control a [attribute] card..."
    CONTROL_RACE = "control_race"           # "if you control a [race]..."
    CONTROL_COUNT = "control_count"         # "if you control X or more..."

    # Graveyard conditions
    GRAVEYARD_HAS = "graveyard_has"         # "if your graveyard has..."
    GRAVEYARD_COUNT = "graveyard_count"     # "if your graveyard has X or more..."
    GRAVEYARD_ATTRIBUTE = "graveyard_attribute"

    # Hand conditions
    HAND_COUNT = "hand_count"               # "if you have X cards in hand..."
    HAND_HAS = "hand_has"                   # "if you have [type] in hand..."

    # Deck conditions
    DECK_COUNT = "deck_count"               # "if your deck has X or more cards..."

    # Removed area conditions
    REMOVED_HAS = "removed_has"             # "if your removed area has..."
    REMOVED_COUNT = "removed_count"

    # Life conditions
    LIFE_THRESHOLD = "life_threshold"       # "if your life is X or less/more..."
    LIFE_COMPARISON = "life_comparison"     # "if your life is higher than opponent's..."

    # Magic stone conditions
    STONE_COUNT = "stone_count"             # "if you control X magic stones..."
    STONE_ATTRIBUTE = "stone_attribute"     # "if you control a [attribute] stone..."

    # Ruler conditions
    RULER_IS = "ruler_is"                   # "if your ruler is [name]..."
    RULER_RECOVERED = "ruler_recovered"     # "if your ruler is recovered..."
    J_RULER_EXISTS = "j_ruler_exists"       # "if you control a J-ruler..."

    # Turn conditions
    IS_YOUR_TURN = "is_your_turn"
    IS_OPPONENT_TURN = "is_opponent_turn"
    TURN_NUMBER = "turn_number"             # "if it's turn X or later..."

    # Phase conditions
    IS_MAIN_PHASE = "is_main_phase"
    IS_BATTLE_PHASE = "is_battle_phase"
    IS_END_PHASE = "is_end_phase"

    # Chase conditions
    CHASE_HAS = "chase_has"                 # "if there's a spell on the chase..."
    CHASE_EMPTY = "chase_empty"

    # This card conditions
    THIS_RESTED = "this_rested"
    THIS_RECOVERED = "this_recovered"
    THIS_HAS_COUNTER = "this_has_counter"   # "if this has X counters..."
    THIS_ATTACKED = "this_attacked"         # "if this attacked this turn..."
    THIS_DEALT_DAMAGE = "this_dealt_damage"

    # Event conditions
    CARD_WAS_PLAYED = "card_was_played"     # "if a spell was played this turn..."
    DAMAGE_WAS_DEALT = "damage_was_dealt"   # "if damage was dealt this turn..."

    # Opponent conditions
    OPPONENT_CONTROLS = "opponent_controls"
    OPPONENT_HAND_COUNT = "opponent_hand_count"
    OPPONENT_GRAVEYARD = "opponent_graveyard"

    # Awakening condition
    WAS_AWAKENED = "was_awakened"           # "if this was awakened..."

    # Combination conditions
    AND = "and"                             # Both conditions must be true
    OR = "or"                               # Either condition must be true
    NOT = "not"                             # Condition must be false

    # Custom
    CUSTOM = "custom"                       # Custom check function


class ConditionOperator(Enum):
    """Comparison operators for numeric conditions."""
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER = "greater"
    GREATER_OR_EQUAL = "greater_or_equal"
    LESS = "less"
    LESS_OR_EQUAL = "less_or_equal"


@dataclass
class Condition:
    """
    A condition that must be met for an effect to apply.

    CR 906.9: Status automatic objects watch if a specific status is fulfilled.
    """
    condition_type: ConditionType

    # Parameters for the condition check
    params: Dict[str, Any] = field(default_factory=dict)

    # For numeric comparisons
    operator: ConditionOperator = ConditionOperator.GREATER_OR_EQUAL
    value: int = 0

    # For compound conditions (AND, OR, NOT)
    sub_conditions: List['Condition'] = field(default_factory=list)

    # Custom check function
    custom_check: Optional[Callable] = None

    def check(self, game: 'GameEngine', card: 'Card', player: int) -> bool:
        """
        Check if this condition is met.

        Args:
            game: The game engine
            card: The source card (for "this card" conditions)
            player: The player to check for

        Returns:
            True if condition is met
        """
        ct = self.condition_type

        # Compound conditions
        if ct == ConditionType.AND:
            return all(c.check(game, card, player) for c in self.sub_conditions)
        if ct == ConditionType.OR:
            return any(c.check(game, card, player) for c in self.sub_conditions)
        if ct == ConditionType.NOT:
            return not self.sub_conditions[0].check(game, card, player)

        # Control conditions
        if ct == ConditionType.CONTROL_CARD:
            return self._check_control_card(game, player)
        if ct == ConditionType.CONTROL_J_RULER:
            return self._check_control_j_ruler(game, player)
        if ct == ConditionType.CONTROL_ATTRIBUTE:
            return self._check_control_attribute(game, player)
        if ct == ConditionType.CONTROL_RACE:
            return self._check_control_race(game, player)
        if ct == ConditionType.CONTROL_COUNT:
            return self._check_control_count(game, player)

        # Graveyard conditions
        if ct == ConditionType.GRAVEYARD_HAS:
            return self._check_graveyard_has(game, player)
        if ct == ConditionType.GRAVEYARD_COUNT:
            return self._check_graveyard_count(game, player)

        # Hand conditions
        if ct == ConditionType.HAND_COUNT:
            count = len(game.players[player].hand)
            return self._compare(count, self.value)

        # Life conditions
        if ct == ConditionType.LIFE_THRESHOLD:
            life = game.players[player].life
            return self._compare(life, self.value)
        if ct == ConditionType.LIFE_COMPARISON:
            my_life = game.players[player].life
            opp_life = game.players[1 - player].life
            return self._compare(my_life, opp_life)

        # Stone conditions
        if ct == ConditionType.STONE_COUNT:
            stones = sum(1 for c in game.players[player].field if c.data and c.data.is_stone())
            return self._compare(stones, self.value)

        # Turn conditions
        if ct == ConditionType.IS_YOUR_TURN:
            return game.turn_player == player
        if ct == ConditionType.IS_OPPONENT_TURN:
            return game.turn_player != player

        # Phase conditions
        if ct == ConditionType.IS_MAIN_PHASE:
            from ..engine import Phase
            return game.current_phase == Phase.MAIN

        # This card conditions
        if ct == ConditionType.THIS_RESTED:
            return card.is_rested
        if ct == ConditionType.THIS_RECOVERED:
            return not card.is_rested
        if ct == ConditionType.THIS_HAS_COUNTER:
            counter_type = self.params.get('counter_type', 'any')
            if counter_type == 'any':
                count = sum(card.counters.values())
            else:
                count = card.counters.get(counter_type, 0)
            return self._compare(count, self.value)

        # Awakening
        if ct == ConditionType.WAS_AWAKENED:
            return getattr(card, 'was_awakened', False)

        # J-ruler exists
        if ct == ConditionType.J_RULER_EXISTS:
            from ..models import CardType
            p = game.players[player]
            for c in p.field:
                if c.data and c.data.card_type == CardType.J_RULER:
                    return True
            return False

        # Ruler is
        if ct == ConditionType.RULER_IS:
            name = self.params.get('name', '')
            p = game.players[player]
            if p.ruler and p.ruler.data:
                return name.lower() in p.ruler.data.name.lower()
            return False

        # Custom
        if ct == ConditionType.CUSTOM and self.custom_check:
            return self.custom_check(game, card, player)

        # Default: condition not implemented
        print(f"[WARN] Condition type {ct} not implemented")
        return True

    def _compare(self, actual: int, expected: int) -> bool:
        """Compare two values using the operator."""
        op = self.operator
        if op == ConditionOperator.EQUALS:
            return actual == expected
        if op == ConditionOperator.NOT_EQUALS:
            return actual != expected
        if op == ConditionOperator.GREATER:
            return actual > expected
        if op == ConditionOperator.GREATER_OR_EQUAL:
            return actual >= expected
        if op == ConditionOperator.LESS:
            return actual < expected
        if op == ConditionOperator.LESS_OR_EQUAL:
            return actual <= expected
        return False

    def _check_control_card(self, game: 'GameEngine', player: int) -> bool:
        """Check if player controls a card matching params."""
        name = self.params.get('name', '')
        card_type = self.params.get('card_type', '')

        for c in game.players[player].field:
            if c.data:
                if name and name.lower() not in c.data.name.lower():
                    continue
                if card_type and c.data.card_type.value != card_type:
                    continue
                return True
        return False

    def _check_control_j_ruler(self, game: 'GameEngine', player: int) -> bool:
        """Check if player controls a J-ruler."""
        from ..models import CardType
        for c in game.players[player].field:
            if c.data and c.data.card_type == CardType.J_RULER:
                return True
        return False

    def _check_control_attribute(self, game: 'GameEngine', player: int) -> bool:
        """Check if player controls a card with specified attribute."""
        attr = self.params.get('attribute', '')
        for c in game.players[player].field:
            if c.data and c.data.attribute:
                if c.data.attribute.name.lower() == attr.lower():
                    return True
        return False

    def _check_control_race(self, game: 'GameEngine', player: int) -> bool:
        """Check if player controls a card with specified race."""
        race = self.params.get('race', '').lower()
        for c in game.players[player].field:
            if c.data and c.data.race:
                races = [r.strip().lower() for r in c.data.race.split('/')]
                if race in races:
                    return True
        return False

    def _check_control_count(self, game: 'GameEngine', player: int) -> bool:
        """Check if player controls X or more cards matching filter."""
        filter_type = self.params.get('filter', 'any')
        count = 0

        for c in game.players[player].field:
            if filter_type == 'any':
                count += 1
            elif filter_type == 'resonator' and c.data and c.data.is_resonator():
                count += 1
            elif filter_type == 'stone' and c.data and c.data.is_stone():
                count += 1

        return self._compare(count, self.value)

    def _check_graveyard_has(self, game: 'GameEngine', player: int) -> bool:
        """Check if graveyard has a card matching params."""
        card_type = self.params.get('card_type', '')
        race = self.params.get('race', '')

        for c in game.players[player].graveyard:
            if c.data:
                if card_type and c.data.card_type.value != card_type:
                    continue
                if race:
                    races = [r.strip().lower() for r in (c.data.race or '').split('/')]
                    if race.lower() not in races:
                        continue
                return True
        return False

    def _check_graveyard_count(self, game: 'GameEngine', player: int) -> bool:
        """Check if graveyard has X or more cards."""
        count = len(game.players[player].graveyard)
        return self._compare(count, self.value)


# Convenience condition builders
class ConditionBuilder:
    """Builder for common conditions."""

    @staticmethod
    def control_j_ruler() -> Condition:
        """You control a J-ruler."""
        return Condition(ConditionType.CONTROL_J_RULER)

    @staticmethod
    def control_race(race: str) -> Condition:
        """You control a [race]."""
        return Condition(
            ConditionType.CONTROL_RACE,
            params={'race': race}
        )

    @staticmethod
    def control_attribute(attribute: str) -> Condition:
        """You control a [attribute] card."""
        return Condition(
            ConditionType.CONTROL_ATTRIBUTE,
            params={'attribute': attribute}
        )

    @staticmethod
    def graveyard_has_race(race: str) -> Condition:
        """Your graveyard has a [race]."""
        return Condition(
            ConditionType.GRAVEYARD_HAS,
            params={'race': race}
        )

    @staticmethod
    def graveyard_count(count: int, op: ConditionOperator = ConditionOperator.GREATER_OR_EQUAL) -> Condition:
        """Your graveyard has X or more cards."""
        return Condition(
            ConditionType.GRAVEYARD_COUNT,
            operator=op,
            value=count
        )

    @staticmethod
    def life_or_less(amount: int) -> Condition:
        """Your life is X or less."""
        return Condition(
            ConditionType.LIFE_THRESHOLD,
            operator=ConditionOperator.LESS_OR_EQUAL,
            value=amount
        )

    @staticmethod
    def stones_count(count: int, op: ConditionOperator = ConditionOperator.GREATER_OR_EQUAL) -> Condition:
        """You control X magic stones."""
        return Condition(
            ConditionType.STONE_COUNT,
            operator=op,
            value=count
        )

    @staticmethod
    def is_your_turn() -> Condition:
        """It's your turn."""
        return Condition(ConditionType.IS_YOUR_TURN)

    @staticmethod
    def is_main_phase() -> Condition:
        """It's the main phase."""
        return Condition(ConditionType.IS_MAIN_PHASE)

    @staticmethod
    def this_is_rested() -> Condition:
        """This card is rested."""
        return Condition(ConditionType.THIS_RESTED)

    @staticmethod
    def this_has_counters(count: int, counter_type: str = 'any') -> Condition:
        """This card has X counters."""
        return Condition(
            ConditionType.THIS_HAS_COUNTER,
            params={'counter_type': counter_type},
            operator=ConditionOperator.GREATER_OR_EQUAL,
            value=count
        )

    @staticmethod
    def was_awakened() -> Condition:
        """This card was awakened."""
        return Condition(ConditionType.WAS_AWAKENED)

    @staticmethod
    def all_of(*conditions: Condition) -> Condition:
        """All conditions must be true."""
        return Condition(
            ConditionType.AND,
            sub_conditions=list(conditions)
        )

    @staticmethod
    def any_of(*conditions: Condition) -> Condition:
        """Any condition must be true."""
        return Condition(
            ConditionType.OR,
            sub_conditions=list(conditions)
        )

    @staticmethod
    def not_(condition: Condition) -> Condition:
        """Condition must be false."""
        return Condition(
            ConditionType.NOT,
            sub_conditions=[condition]
        )
