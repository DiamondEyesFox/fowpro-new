"""
FoWPro AI - Random AI
=====================
Basic AI that selects random legal moves.
Good baseline for testing and as opponent for new players.
"""

from __future__ import annotations
import random
from typing import TYPE_CHECKING

from .base import BaseAI, AIAction, ActionType

if TYPE_CHECKING:
    from ..engine import GameEngine


class RandomAI(BaseAI):
    """
    AI that picks random legal actions.

    Slightly smarter than pure random:
    - Prioritizes playing cards over passing
    - Will attack if able
    - Calls stones before playing expensive cards
    - Blocks when beneficial

    Good for:
    - Testing game mechanics
    - New player practice
    - Baseline for comparing smarter AIs
    """

    def __init__(self, player_index: int, aggression: float = 0.7):
        """
        Initialize RandomAI.

        Args:
            player_index: The player number this AI controls
            aggression: Probability of choosing aggressive actions (0.0-1.0)
        """
        super().__init__(player_index)
        self.name = "Random AI"
        self.aggression = aggression

    def choose_action(self, engine: 'GameEngine', legal_actions: list[dict]) -> AIAction:
        """
        Choose a random action, with slight bias toward playing cards and attacking.
        """
        if not legal_actions:
            return AIAction.pass_priority()

        # Categorize actions
        passes = []
        stones = []
        plays = []
        attacks = []
        blocks = []
        abilities = []
        will_producers = []
        other = []

        for action in legal_actions:
            atype = action.get("type")
            if atype == "pass_priority":
                passes.append(action)
            elif atype == "call_stone":
                stones.append(action)
            elif atype in ("play_card", "play_instant"):
                plays.append(action)
            elif atype == "attack":
                attacks.append(action)
            elif atype == "block":
                blocks.append(action)
            elif atype == "activate_ability":
                abilities.append(action)
            elif atype == "produce_will":
                will_producers.append(action)
            elif atype == "judgment":
                other.append(action)
            else:
                other.append(action)

        # Decision logic with weighted randomness

        # Always block if we can and it's beneficial
        if blocks:
            if random.random() < 0.8:  # 80% chance to block
                return self._convert_action(random.choice(blocks))

        # Prefer attacking if aggressive
        if attacks and random.random() < self.aggression:
            return self._convert_action(random.choice(attacks))

        # Call stone if we haven't and have cards to play
        if stones and plays:
            if random.random() < 0.9:  # 90% chance to call stone when we have plays
                return self._convert_action(stones[0])

        # Play cards with decent probability
        if plays and random.random() < 0.8:
            return self._convert_action(random.choice(plays))

        # Use abilities sometimes
        if abilities and random.random() < 0.5:
            return self._convert_action(random.choice(abilities))

        # Judgment if available and aggressive
        if other and random.random() < self.aggression:
            for action in other:
                if action.get("type") == "judgment":
                    return self._convert_action(action)

        # Tap for will if we might need it
        if will_producers and random.random() < 0.3:
            return self._convert_action(random.choice(will_producers))

        # Still have non-pass actions? Pick one randomly
        non_pass = [a for a in legal_actions if a.get("type") != "pass_priority"]
        if non_pass and random.random() < 0.5:
            return self._convert_action(random.choice(non_pass))

        # Default to passing
        return AIAction.pass_priority()

    def _convert_action(self, action_dict: dict) -> AIAction:
        """Convert engine action dict to AIAction object."""
        atype = action_dict.get("type")

        if atype == "pass_priority":
            return AIAction.pass_priority()

        elif atype == "call_stone":
            return AIAction.call_stone()

        elif atype == "play_card":
            return AIAction.play_card(action_dict.get("card"))

        elif atype == "play_instant":
            return AIAction.play_instant(action_dict.get("card"))

        elif atype == "judgment":
            return AIAction.judgment()

        elif atype == "attack":
            return AIAction.attack(
                action_dict.get("card"),
                target_player=None,  # Will default to opponent
                target_card_uid=None
            )

        elif atype == "block":
            return AIAction.block(action_dict.get("card"))

        elif atype == "produce_will":
            return AIAction.produce_will(action_dict.get("card"))

        elif atype == "activate_ability":
            return AIAction.activate_ability(
                action_dict.get("card"),
                action_dict.get("ability_index", 0)
            )

        # Fallback
        return AIAction.pass_priority()


class AggressiveAI(RandomAI):
    """
    More aggressive variant that prioritizes attacks and damage.
    """

    def __init__(self, player_index: int):
        super().__init__(player_index, aggression=0.9)
        self.name = "Aggressive AI"

    def choose_action(self, engine: 'GameEngine', legal_actions: list[dict]) -> AIAction:
        # Always attack if possible
        attacks = [a for a in legal_actions if a.get("type") == "attack"]
        if attacks:
            return self._convert_action(random.choice(attacks))

        # Prioritize damage-dealing cards and judgment
        return super().choose_action(engine, legal_actions)


class DefensiveAI(RandomAI):
    """
    More defensive variant that prioritizes blocking and survival.
    """

    def __init__(self, player_index: int):
        super().__init__(player_index, aggression=0.3)
        self.name = "Defensive AI"

    def choose_action(self, engine: 'GameEngine', legal_actions: list[dict]) -> AIAction:
        # Always block if possible
        blocks = [a for a in legal_actions if a.get("type") == "block"]
        if blocks:
            return self._convert_action(random.choice(blocks))

        return super().choose_action(engine, legal_actions)


class PassOnlyAI(BaseAI):
    """
    AI that always passes priority immediately.

    Useful for:
    - Testing your deck without AI interference
    - Practicing combos and card interactions
    - Speed-running through game phases
    - Goldfishing (playing solitaire against a non-interactive opponent)
    """

    def __init__(self, player_index: int):
        super().__init__(player_index)
        self.name = "Pass-Only AI"

    def choose_action(self, engine: 'GameEngine', legal_actions: list[dict]) -> AIAction:
        """Always pass priority - never take any action."""
        return AIAction.pass_priority()
