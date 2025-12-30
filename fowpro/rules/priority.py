"""
Priority System for Force of Will - Comprehensive Rules Implementation.

References:
- CR 604: Priority
- CR 605: Priority Sequence
- CR 701.2: Main Timing
- CR 707: Chase Resolution
- CR 903: Playing Spells and Abilities

This module implements the complete priority system including:
- Priority passing between players
- Main timing checks
- Response windows
- Chase resolution triggers
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import TYPE_CHECKING, Optional, List, Callable, Any

if TYPE_CHECKING:
    from ..engine import GameEngine
    from ..models import Card


class PriorityState(Enum):
    """
    Current state of the priority system.

    CR 604: A player with priority can perform actions.
    """
    # Player has priority and can act
    ACTIVE = "active"

    # Player has passed priority
    PASSED = "passed"

    # Waiting for opponent response
    WAITING_RESPONSE = "waiting_response"

    # Both players passed - resolve chase or advance phase
    BOTH_PASSED = "both_passed"

    # Resolving chase item
    RESOLVING = "resolving"

    # Waiting for player input (targeting, modal choice, etc.)
    WAITING_INPUT = "waiting_input"


class ActionType(Enum):
    """
    Types of actions a player can take with priority.

    CR 604.1: Actions available with priority.
    """
    # Play a card (spell, resonator, addition)
    PLAY_CARD = "play_card"

    # Play an activated ability
    ACTIVATE_ABILITY = "activate_ability"

    # Play a will ability (doesn't use chase)
    PRODUCE_WILL = "produce_will"

    # Call a magic stone (main timing only)
    CALL_STONE = "call_stone"

    # Perform Judgment (main timing only)
    JUDGMENT = "judgment"

    # Declare attack (battle phase only)
    ATTACK = "attack"

    # Declare block (battle phase only)
    BLOCK = "block"

    # Pass priority
    PASS = "pass"


@dataclass
class PendingAction:
    """
    An action waiting for additional input (targets, modes, etc.)

    CR 903.2: When playing a card or ability, choose targets and modes.
    """
    action_type: ActionType
    source: Optional['Card'] = None
    player: int = 0

    # What input is needed
    needs_targets: bool = False
    needs_modes: bool = False
    needs_will_choice: bool = False

    # Target requirements
    target_requirements: List[Any] = field(default_factory=list)
    selected_targets: List['Card'] = field(default_factory=list)

    # Modal requirements
    modal_choice: Optional[Any] = None
    selected_modes: List[int] = field(default_factory=list)

    # Will color choice (for dual stones)
    will_colors: List[Any] = field(default_factory=list)
    selected_color: Optional[Any] = None

    # Ability index for activated abilities
    ability_index: int = 0

    # Callback when action is complete
    on_complete: Optional[Callable] = None


class PriorityManager:
    """
    Manages the priority system according to CR 604-605.

    CR 604.1: A player can play a card or ability, or perform a special
    action, only when they have priority.

    CR 605: Priority Sequence - describes how priority passes.
    """

    def __init__(self, game: 'GameEngine'):
        self.game = game
        self.state = PriorityState.ACTIVE
        self.active_player = 0  # Who has priority
        self.turn_player = 0  # Whose turn it is

        # Pass tracking
        self.player_passed = [False, False]

        # Pending action awaiting input
        self.pending_action: Optional[PendingAction] = None

        # Action history for the current priority sequence
        self.action_history: List[tuple] = []

        # Callbacks
        self._on_priority_change: Optional[Callable] = None
        self._on_input_needed: Optional[Callable] = None
        self._on_both_passed: Optional[Callable] = None

    def set_callbacks(self,
                      on_priority_change: Callable = None,
                      on_input_needed: Callable = None,
                      on_both_passed: Callable = None):
        """Set callback functions for priority events."""
        self._on_priority_change = on_priority_change
        self._on_input_needed = on_input_needed
        self._on_both_passed = on_both_passed

    def reset_for_phase(self, turn_player: int):
        """
        Reset priority for a new phase.

        CR 605.2: At the beginning of each step or phase, the turn
        player receives priority.
        """
        self.turn_player = turn_player
        self.active_player = turn_player
        self.player_passed = [False, False]
        self.state = PriorityState.ACTIVE
        self.pending_action = None
        self.action_history = []

        self._notify_priority_change()

    def reset_passes(self):
        """Reset pass tracking (after an action is taken)."""
        self.player_passed = [False, False]

    def has_priority(self, player: int) -> bool:
        """Check if a player currently has priority."""
        return (self.state == PriorityState.ACTIVE and
                self.active_player == player)

    def is_main_timing(self, player: int) -> bool:
        """
        Check if it's main timing for a player.

        CR 701.2: "Main timing" requires:
        - It's the player's turn
        - Main phase
        - Not in battle
        - Chase area is empty
        """
        from ..engine import Phase

        return (
            self.game.turn_player == player and
            self.game.current_phase == Phase.MAIN and
            not self.game.battle.in_battle and
            len(self.game.chase) == 0
        )

    def can_take_action(self, player: int, action_type: ActionType) -> bool:
        """
        Check if a player can take a specific action type.

        CR 604.1: Player must have priority.
        CR 701.2: Some actions require main timing.
        """
        if not self.has_priority(player):
            return False

        # Check main timing requirements
        if action_type in (ActionType.CALL_STONE, ActionType.JUDGMENT):
            return self.is_main_timing(player)

        if action_type == ActionType.ATTACK:
            from ..engine import Phase
            return (self.game.current_phase == Phase.BATTLE and
                    self.game.turn_player == player)

        if action_type == ActionType.BLOCK:
            from ..engine import Phase
            return (self.game.current_phase == Phase.BATTLE and
                    self.game.turn_player != player and
                    self.game.battle.in_battle)

        return True

    def get_legal_actions(self, player: int) -> List[ActionType]:
        """Get all legal action types for a player."""
        if not self.has_priority(player):
            return []

        actions = [ActionType.PASS]

        # Always can produce will if able
        actions.append(ActionType.PRODUCE_WILL)

        # Instant-speed actions (anytime with priority)
        actions.append(ActionType.PLAY_CARD)
        actions.append(ActionType.ACTIVATE_ABILITY)

        # Main timing actions
        if self.is_main_timing(player):
            actions.append(ActionType.CALL_STONE)
            actions.append(ActionType.JUDGMENT)

        # Battle actions
        from ..engine import Phase
        if self.game.current_phase == Phase.BATTLE:
            if self.game.turn_player == player:
                actions.append(ActionType.ATTACK)
            else:
                actions.append(ActionType.BLOCK)

        return actions

    def take_action(self, player: int, action_type: ActionType,
                    source: 'Card' = None, **kwargs) -> bool:
        """
        Player takes an action.

        CR 604.1: When a player takes an action, they lose priority.
        CR 903.2: Some actions require additional choices.

        Returns True if action was started, False if illegal.
        """
        if not self.can_take_action(player, action_type):
            return False

        if action_type == ActionType.PASS:
            return self._handle_pass(player)

        if action_type == ActionType.PRODUCE_WILL:
            return self._handle_produce_will(player, source, **kwargs)

        if action_type == ActionType.PLAY_CARD:
            return self._handle_play_card(player, source, **kwargs)

        if action_type == ActionType.ACTIVATE_ABILITY:
            return self._handle_activate_ability(player, source, **kwargs)

        if action_type == ActionType.CALL_STONE:
            return self._handle_call_stone(player, **kwargs)

        if action_type == ActionType.JUDGMENT:
            return self._handle_judgment(player, **kwargs)

        if action_type == ActionType.ATTACK:
            return self._handle_attack(player, source, **kwargs)

        if action_type == ActionType.BLOCK:
            return self._handle_block(player, source, **kwargs)

        return False

    def _handle_pass(self, player: int) -> bool:
        """
        Handle a player passing priority.

        CR 605.3: When a player passes, opponent receives priority.
        CR 605.4: When both pass consecutively, resolve chase or advance.
        """
        self.player_passed[player] = True
        self.action_history.append((player, ActionType.PASS))

        opponent = 1 - player

        if self.player_passed[opponent]:
            # Both players have passed
            self.state = PriorityState.BOTH_PASSED
            self._handle_both_passed()
        else:
            # Give priority to opponent
            self.active_player = opponent
            self.state = PriorityState.ACTIVE
            self._notify_priority_change()

        return True

    def _handle_both_passed(self):
        """
        Handle both players passing consecutively.

        CR 605.4: When both pass in succession:
        - If chase has items: resolve top item
        - If chase empty: advance to next step/phase
        """
        if self._on_both_passed:
            self._on_both_passed()

        if self.game.chase:
            # Resolve top chase item
            self.state = PriorityState.RESOLVING
            # The engine will call us back after resolution
        else:
            # Phase/step advancement handled by engine
            pass

    def after_chase_resolution(self):
        """
        Called after a chase item resolves.

        CR 707.4: After resolution, active player receives priority again.
        """
        self.player_passed = [False, False]
        self.active_player = self.turn_player
        self.state = PriorityState.ACTIVE
        self._notify_priority_change()

    def after_action(self, player: int):
        """
        Called after any action that uses the chase.

        CR 605.3: After playing something, opponent receives priority.
        """
        self.reset_passes()
        opponent = 1 - player
        self.active_player = opponent
        self.state = PriorityState.ACTIVE
        self._notify_priority_change()

    def _handle_produce_will(self, player: int, source: 'Card', **kwargs) -> bool:
        """
        Handle will production.

        CR 907.3: Will abilities don't use the chase.
        """
        if not source:
            return False

        # Check if stone can produce will
        script = self.game.get_script(source)
        if not script:
            return False

        # Get will colors
        colors = script.get_will_colors(self.game, source)

        if len(colors) > 1 and 'color' not in kwargs:
            # Need color choice - create pending action
            self.pending_action = PendingAction(
                action_type=ActionType.PRODUCE_WILL,
                source=source,
                player=player,
                needs_will_choice=True,
                will_colors=colors,
            )
            self.state = PriorityState.WAITING_INPUT
            self._notify_input_needed()
            return True

        # Produce the will
        color = kwargs.get('color', colors[0] if colors else None)
        if color:
            self.game.players[player].will_pool.add(color, 1)
            source.is_rested = True

            # Will production doesn't pass priority to opponent
            # but resets passes since game state changed
            self.reset_passes()

        return True

    def _handle_play_card(self, player: int, source: 'Card', **kwargs) -> bool:
        """
        Handle playing a card.

        CR 903.2: Choose targets and modes when playing.
        """
        if not source:
            return False

        # Validate timing
        from ..models import CardType
        card_type = source.data.card_type if source.data else None

        # Check if instant-speed or main timing required
        is_instant = self._card_is_instant_speed(source)
        if not is_instant and not self.is_main_timing(player):
            return False

        # Check if can pay cost
        if not self._can_pay_cost(player, source):
            return False

        # Check targeting requirements
        script = self.game.get_script(source)
        target_reqs = []
        if script and hasattr(script, 'get_target_requirements'):
            target_reqs = script.get_target_requirements(self.game, source)

        if target_reqs and 'targets' not in kwargs:
            # Need target selection
            self.pending_action = PendingAction(
                action_type=ActionType.PLAY_CARD,
                source=source,
                player=player,
                needs_targets=True,
                target_requirements=target_reqs,
            )
            self.state = PriorityState.WAITING_INPUT
            self._notify_input_needed()
            return True

        # All requirements met - play the card
        targets = kwargs.get('targets', [])
        self._finalize_play_card(player, source, targets)
        return True

    def _finalize_play_card(self, player: int, source: 'Card', targets: List['Card']):
        """Finalize playing a card (pay cost, add to chase)."""
        from ..models import Zone, ChaseItem

        # Pay cost
        if source.data and source.data.cost:
            self.game.players[player].will_pool.pay(source.data.cost)

        # Move from hand to chase
        self.game.move_card(source, Zone.CHASE, player)

        # Add to chase
        item = ChaseItem(
            source=source,
            controller=player,
            item_type="SPELL",
            targets=targets,
        )
        self.game.add_to_chase(item)

        self.after_action(player)

    def _handle_activate_ability(self, player: int, source: 'Card', **kwargs) -> bool:
        """Handle activating an ability."""
        if not source:
            return False

        ability_index = kwargs.get('ability_index', 0)

        # Get the ability
        script = self.game.get_script(source)
        if not script:
            return False

        abilities = script.get_activated_abilities(self.game, source)
        if ability_index >= len(abilities):
            return False

        ability = abilities[ability_index]

        # Check if can activate
        if not ability.can_activate(self.game, source):
            return False

        # Check targeting
        if hasattr(ability, 'target_requirements') and ability.target_requirements:
            if 'targets' not in kwargs:
                self.pending_action = PendingAction(
                    action_type=ActionType.ACTIVATE_ABILITY,
                    source=source,
                    player=player,
                    needs_targets=True,
                    target_requirements=ability.target_requirements,
                    ability_index=ability_index,
                )
                self.state = PriorityState.WAITING_INPUT
                self._notify_input_needed()
                return True

        targets = kwargs.get('targets', [])
        self._finalize_activate_ability(player, source, ability_index, targets)
        return True

    def _finalize_activate_ability(self, player: int, source: 'Card',
                                    ability_index: int, targets: List['Card']):
        """Finalize activating an ability."""
        from ..models import ChaseItem

        script = self.game.get_script(source)
        abilities = script.get_activated_abilities(self.game, source)
        ability = abilities[ability_index]

        # Pay costs
        if hasattr(ability, 'tap_cost') and ability.tap_cost:
            source.is_rested = True
        if hasattr(ability, 'will_cost') and ability.will_cost:
            self.game.players[player].will_pool.pay(ability.will_cost)

        # Add to chase
        item = ChaseItem(
            source=source,
            controller=player,
            item_type="ABILITY",
            targets=targets,
            effect_data={'ability_index': ability_index},
        )
        self.game.add_to_chase(item)

        self.after_action(player)

    def _handle_call_stone(self, player: int, **kwargs) -> bool:
        """Handle calling a magic stone."""
        p = self.game.players[player]

        if p.has_called_stone:
            return False

        if not p.stone_deck:
            return False

        # Call the top stone
        stone = p.stone_deck.pop(0)
        from ..models import Zone
        self.game.move_card(stone, Zone.FIELD, player)
        p.has_called_stone = True

        from ..engine import EventType
        self.game.emit(EventType.STONE_CALLED, player, stone)

        # Stone calling doesn't use the chase but resets passes
        self.reset_passes()
        return True

    def _handle_judgment(self, player: int, **kwargs) -> bool:
        """Handle performing Judgment."""
        p = self.game.players[player]

        if not p.ruler or p.has_j_ruled:
            return False

        # Check Judgment cost
        j_cost = p.ruler.data.judgment_cost if p.ruler.data else None
        if j_cost and not p.will_pool.can_pay(j_cost):
            return False

        # Pay cost
        if j_cost:
            p.will_pool.pay(j_cost)

        # Add Judgment to chase
        from ..models import ChaseItem
        item = ChaseItem(
            source=p.ruler,
            controller=player,
            item_type="JUDGMENT",
        )
        self.game.add_to_chase(item)

        from ..engine import EventType
        self.game.emit(EventType.JUDGMENT, player, p.ruler)

        self.after_action(player)
        return True

    def _handle_attack(self, player: int, source: 'Card', **kwargs) -> bool:
        """Handle declaring an attack."""
        if not source:
            return False

        # Check if can attack
        if source.is_rested:
            return False

        from ..models import Keyword
        if source.entered_turn == self.game.turn_number:
            if not source.has_keyword(Keyword.SWIFTNESS):
                return False

        # Attack declaration handled by engine's battle system
        target = kwargs.get('target')
        self.game.declare_attack(source, target)

        return True

    def _handle_block(self, player: int, source: 'Card', **kwargs) -> bool:
        """Handle declaring a block."""
        if not source:
            return False

        if source.is_rested:
            return False

        self.game.declare_block(source)
        return True

    def provide_input(self, **kwargs) -> bool:
        """
        Provide input for a pending action.

        Called by UI when player makes targeting/modal choices.
        """
        if not self.pending_action:
            return False

        action = self.pending_action

        if action.needs_targets and 'targets' in kwargs:
            action.selected_targets = kwargs['targets']
            action.needs_targets = False

        if action.needs_modes and 'modes' in kwargs:
            action.selected_modes = kwargs['modes']
            action.needs_modes = False

        if action.needs_will_choice and 'color' in kwargs:
            action.selected_color = kwargs['color']
            action.needs_will_choice = False

        # Check if all input received
        if not (action.needs_targets or action.needs_modes or action.needs_will_choice):
            self._complete_pending_action()

        return True

    def cancel_pending_action(self):
        """Cancel the current pending action."""
        self.pending_action = None
        self.state = PriorityState.ACTIVE
        self._notify_priority_change()

    def _complete_pending_action(self):
        """Complete the pending action with all input received."""
        action = self.pending_action
        if not action:
            return

        self.pending_action = None
        self.state = PriorityState.ACTIVE

        if action.action_type == ActionType.PRODUCE_WILL:
            self._handle_produce_will(
                action.player, action.source,
                color=action.selected_color
            )

        elif action.action_type == ActionType.PLAY_CARD:
            self._finalize_play_card(
                action.player, action.source,
                action.selected_targets
            )

        elif action.action_type == ActionType.ACTIVATE_ABILITY:
            self._finalize_activate_ability(
                action.player, action.source,
                action.ability_index, action.selected_targets
            )

    def _card_is_instant_speed(self, card: 'Card') -> bool:
        """Check if a card can be played at instant speed."""
        if not card.data:
            return False

        from ..models import CardType, Keyword

        # Chant-Instant is always instant
        if card.data.card_type == CardType.CHANT_INSTANT:
            return True

        # Quickcast keyword
        if card.has_keyword(Keyword.QUICKCAST):
            return True

        # Check for Quickcast in ability text
        if card.data.ability_text and 'quickcast' in card.data.ability_text.lower():
            return True

        return False

    def _can_pay_cost(self, player: int, card: 'Card') -> bool:
        """Check if player can pay a card's cost."""
        if not card.data or not card.data.cost:
            return True

        return self.game.players[player].will_pool.can_pay(card.data.cost)

    def _notify_priority_change(self):
        """Notify that priority has changed."""
        if self._on_priority_change:
            self._on_priority_change(self.active_player, self.state)

    def _notify_input_needed(self):
        """Notify that input is needed."""
        if self._on_input_needed and self.pending_action:
            self._on_input_needed(self.pending_action)
