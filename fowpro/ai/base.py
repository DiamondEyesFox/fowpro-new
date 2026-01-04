"""
FoWPro AI - Base Classes
========================
Abstract interface for AI implementations.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional, Any
from enum import Enum, auto

if TYPE_CHECKING:
    from ..engine import GameEngine
    from ..models import Card


class ActionType(Enum):
    """Types of actions the AI can take"""
    PASS_PRIORITY = auto()
    CALL_STONE = auto()
    PLAY_CARD = auto()
    PLAY_INSTANT = auto()
    JUDGMENT = auto()
    ATTACK = auto()
    BLOCK = auto()
    PRODUCE_WILL = auto()
    ACTIVATE_ABILITY = auto()
    DECLINE_BLOCK = auto()


@dataclass
class AIAction:
    """
    Represents an action chosen by the AI.

    Attributes:
        action_type: The type of action to perform
        card_uid: UID of the card involved (if applicable)
        targets: List of target UIDs (if applicable)
        ability_index: Index of ability to activate (if applicable)
        extra: Additional parameters for special cases
    """
    action_type: ActionType
    card_uid: Optional[str] = None
    targets: Optional[list] = None
    ability_index: Optional[int] = None
    extra: Optional[dict] = None

    @classmethod
    def pass_priority(cls) -> 'AIAction':
        return cls(ActionType.PASS_PRIORITY)

    @classmethod
    def call_stone(cls) -> 'AIAction':
        return cls(ActionType.CALL_STONE)

    @classmethod
    def play_card(cls, card_uid: str, targets: list = None) -> 'AIAction':
        return cls(ActionType.PLAY_CARD, card_uid=card_uid, targets=targets)

    @classmethod
    def play_instant(cls, card_uid: str, targets: list = None) -> 'AIAction':
        return cls(ActionType.PLAY_INSTANT, card_uid=card_uid, targets=targets)

    @classmethod
    def judgment(cls) -> 'AIAction':
        return cls(ActionType.JUDGMENT)

    @classmethod
    def attack(cls, card_uid: str, target_player: int = None, target_card_uid: str = None) -> 'AIAction':
        return cls(ActionType.ATTACK, card_uid=card_uid, extra={
            'target_player': target_player,
            'target_card_uid': target_card_uid
        })

    @classmethod
    def block(cls, card_uid: str) -> 'AIAction':
        return cls(ActionType.BLOCK, card_uid=card_uid)

    @classmethod
    def decline_block(cls) -> 'AIAction':
        return cls(ActionType.DECLINE_BLOCK)

    @classmethod
    def produce_will(cls, card_uid: str, chosen_attr: Any = None) -> 'AIAction':
        return cls(ActionType.PRODUCE_WILL, card_uid=card_uid, extra={'chosen_attr': chosen_attr})

    @classmethod
    def activate_ability(cls, card_uid: str, ability_index: int, targets: list = None) -> 'AIAction':
        return cls(ActionType.ACTIVATE_ABILITY, card_uid=card_uid,
                   ability_index=ability_index, targets=targets)


class BaseAI(ABC):
    """
    Abstract base class for AI implementations.

    Subclasses must implement choose_action() to select from legal actions.
    """

    def __init__(self, player_index: int):
        """
        Initialize AI for a specific player.

        Args:
            player_index: The player number this AI controls (0 or 1)
        """
        self.player_index = player_index
        self.name = "AI"

    @abstractmethod
    def choose_action(self, engine: 'GameEngine', legal_actions: list[dict]) -> AIAction:
        """
        Choose an action from the list of legal actions.

        Args:
            engine: The game engine (for reading game state)
            legal_actions: List of legal action dicts from engine.get_legal_actions()

        Returns:
            AIAction representing the chosen action
        """
        pass

    def on_game_start(self, engine: 'GameEngine'):
        """Called when a game starts. Override for initialization."""
        pass

    def on_game_end(self, engine: 'GameEngine', winner: int):
        """Called when a game ends. Override for learning/logging."""
        pass

    def on_turn_start(self, engine: 'GameEngine'):
        """Called at the start of each turn. Override for turn-based logic."""
        pass

    def choose_targets(self, engine: 'GameEngine', card: 'Card',
                       valid_targets: list['Card'], num_targets: int = 1) -> list['Card']:
        """
        Choose targets for a card or ability.

        Default implementation picks randomly. Override for smarter targeting.

        Args:
            engine: The game engine
            card: The card requiring targets
            valid_targets: List of valid target cards
            num_targets: Number of targets to choose

        Returns:
            List of chosen target cards
        """
        import random
        if len(valid_targets) <= num_targets:
            return valid_targets
        return random.sample(valid_targets, num_targets)

    def choose_modal(self, engine: 'GameEngine', card: 'Card',
                     modes: list[str], num_choices: int = 1) -> list[int]:
        """
        Choose modes for a modal spell/ability.

        Default implementation picks randomly. Override for smarter choices.

        Args:
            engine: The game engine
            card: The modal card
            modes: List of mode descriptions
            num_choices: Number of modes to choose

        Returns:
            List of chosen mode indices
        """
        import random
        indices = list(range(len(modes)))
        if len(indices) <= num_choices:
            return indices
        return random.sample(indices, num_choices)

    def choose_x_value(self, engine: 'GameEngine', card: 'Card',
                       max_x: int) -> int:
        """
        Choose X value for X-cost spells.

        Default returns max. Override for resource management.

        Args:
            engine: The game engine
            card: The X-cost card
            max_x: Maximum payable X value

        Returns:
            Chosen X value
        """
        return max_x

    def choose_will_to_produce(self, engine: 'GameEngine', card: 'Card',
                               options: list) -> Any:
        """
        Choose which color of will to produce from a multi-color stone.

        Default picks randomly. Override for mana management.

        Args:
            engine: The game engine
            card: The stone card
            options: List of Attribute options

        Returns:
            Chosen Attribute
        """
        import random
        return random.choice(options) if options else None


class AIExecutor:
    """
    Executes AI actions on the game engine.

    Translates AIAction objects into engine method calls.
    """

    def __init__(self, engine: 'GameEngine'):
        self.engine = engine

    def execute(self, action: AIAction, player: int) -> bool:
        """
        Execute an AI action on the engine.

        Args:
            action: The AIAction to execute
            player: The player index performing the action

        Returns:
            True if action succeeded, False otherwise
        """
        engine = self.engine

        if action.action_type == ActionType.PASS_PRIORITY:
            return engine.pass_priority(player)

        elif action.action_type == ActionType.CALL_STONE:
            return engine.call_stone(player)

        elif action.action_type == ActionType.PLAY_CARD:
            card = engine.get_card_by_uid(action.card_uid)
            if card:
                return engine.play_card(player, card, action.targets)
            return False

        elif action.action_type == ActionType.PLAY_INSTANT:
            card = engine.get_card_by_uid(action.card_uid)
            if card:
                return engine.play_card(player, card, action.targets)
            return False

        elif action.action_type == ActionType.JUDGMENT:
            return engine.perform_judgment(player)

        elif action.action_type == ActionType.ATTACK:
            card = engine.get_card_by_uid(action.card_uid)
            if card:
                extra = action.extra or {}
                target_player = extra.get('target_player', 1 - player)
                target_card_uid = extra.get('target_card_uid')
                target_card = None
                if target_card_uid:
                    target_card = engine.get_card_by_uid(target_card_uid)
                return engine.declare_attack(player, card, target_player, target_card)
            return False

        elif action.action_type == ActionType.BLOCK:
            card = engine.get_card_by_uid(action.card_uid)
            if card:
                return engine.declare_blocker(player, card)
            return False

        elif action.action_type == ActionType.DECLINE_BLOCK:
            return engine.pass_priority(player)

        elif action.action_type == ActionType.PRODUCE_WILL:
            card = engine.get_card_by_uid(action.card_uid)
            if card:
                extra = action.extra or {}
                chosen_attr = extra.get('chosen_attr')
                return engine.produce_will(player, card, chosen_attr)
            return False

        elif action.action_type == ActionType.ACTIVATE_ABILITY:
            card = engine.get_card_by_uid(action.card_uid)
            if card and action.ability_index is not None:
                return engine.activate_ability(player, card, action.ability_index,
                                               action.targets)
            return False

        return False
