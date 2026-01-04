"""
FoWPro - Game Engine
====================
Complete Force of Will game engine with all mechanics.
"""

from __future__ import annotations
import uuid
import random
from dataclasses import dataclass, field
from typing import Optional, Callable, Any
from collections import deque
from enum import Enum, auto

from .models import (
    Card, CardData, CardType, Attribute, Zone, Phase, CombatStep,
    Keyword, WillCost, WillPool, PlayerState, BattleContext, ChaseItem
)
from .database import CardDatabase

# Import script system - do this lazily to avoid circular imports
def _get_script_registry():
    from .scripts import ScriptRegistry
    # Import default script handler
    from .scripts import default  # noqa
    # Import generated scripts (includes stones)
    try:
        from .scripts import generated  # noqa
    except ImportError:
        pass  # Generated scripts may not exist yet
    return ScriptRegistry

def _get_trigger_manager_class():
    from .scripts.triggers import TriggerManager, TriggerEvent
    return TriggerManager, TriggerEvent

def _get_continuous_manager_class():
    from .scripts.continuous import ContinuousEffectManager
    return ContinuousEffectManager


# =============================================================================
# EVENTS
# =============================================================================

class EventType(Enum):
    """All game event types"""
    # Game flow
    GAME_START = auto()
    GAME_END = auto()
    TURN_START = auto()
    TURN_END = auto()
    PHASE_CHANGE = auto()

    # Card movement
    CARD_DRAWN = auto()
    CARD_PLAYED = auto()
    CARD_MOVED = auto()
    CARD_DESTROYED = auto()
    CARD_BANISHED = auto()

    # Zone events
    ENTERS_FIELD = auto()
    LEAVES_FIELD = auto()
    ENTERS_GRAVEYARD = auto()

    # Combat
    ATTACK_DECLARED = auto()
    BLOCKER_DECLARED = auto()
    DAMAGE_DEALT = auto()
    COMBAT_END = auto()

    # Life/damage
    LIFE_CHANGED = auto()
    PLAYER_DAMAGED = auto()

    # Chase/stack
    CHASE_ITEM_ADDED = auto()
    CHASE_ITEM_RESOLVED = auto()
    CHASE_ITEM_COUNTERED = auto()

    # Will/mana
    WILL_PRODUCED = auto()
    WILL_SPENT = auto()
    STONE_CALLED = auto()

    # Ruler
    JUDGMENT = auto()
    J_RULER_ENTERS = auto()

    # Priority
    PRIORITY_PASSED = auto()
    BOTH_PASSED = auto()

    # State-based
    STATE_BASED_ACTIONS = auto()


@dataclass
class GameEvent:
    """A game event with data"""
    event_type: EventType
    player: int = -1
    card: Optional[Card] = None
    target: Any = None
    data: dict = field(default_factory=dict)

    def __str__(self):
        return f"[{self.event_type.name}] P{self.player}: {self.data}"


# =============================================================================
# GAME ENGINE
# =============================================================================

class GameEngine:
    """
    Complete Force of Will game engine.

    Handles all game mechanics including:
    - Turn structure and phases
    - Priority system
    - Chase (stack) resolution
    - Combat with all timing windows
    - State-based actions
    - Card movement between zones
    - Will production and payment
    - Ruler/J-Ruler and Judgment
    """

    def __init__(self, db: Optional[CardDatabase] = None):
        self.db = db

        # Players
        self.players: list[PlayerState] = [PlayerState(0), PlayerState(1)]

        # Turn state
        self.turn_number: int = 0
        self.turn_player: int = 0
        self.current_phase: Phase = Phase.RECOVERY
        self.priority_player: int = 0
        self.consecutive_passes: int = 0

        # Chase (stack)
        self.chase: list[ChaseItem] = []

        # Combat
        self.battle: BattleContext = BattleContext()

        # Game state
        self.game_over: bool = False
        self.winner: int = -1
        self.is_first_turn: bool = True

        # Event system
        self._event_queue: deque[GameEvent] = deque()
        self._event_handlers: list[Callable[[GameEvent], None]] = []

        # Card tracking
        self._all_cards: dict[str, Card] = {}  # uid -> Card
        self._uid_counter: int = 0

        # Effect system managers
        TriggerManager, _ = _get_trigger_manager_class()
        ContinuousEffectManager = _get_continuous_manager_class()
        self.trigger_manager = TriggerManager(self)
        self.continuous_manager = ContinuousEffectManager(self)

        # Rules engine (CR-compliant wrapper) - initialize eagerly to set up event hooks
        self._rules_engine = None
        self._get_rules_engine()  # Initialize now so hooks are registered

        # EventType -> TriggerEvent mapping
        self._event_trigger_map = self._build_event_trigger_map()

    def _get_rules_engine(self):
        """Get or create the rules engine wrapper."""
        if self._rules_engine is None:
            try:
                from .rules.integration import RulesEngine
                self._rules_engine = RulesEngine(self)
            except ImportError:
                pass  # Rules module not available
        return self._rules_engine

    def _build_event_trigger_map(self) -> dict:
        """Build mapping from EventType to TriggerEvent"""
        _, TriggerEvent = _get_trigger_manager_class()
        return {
            EventType.TURN_START: TriggerEvent.TURN_START,
            EventType.TURN_END: TriggerEvent.TURN_END,
            EventType.PHASE_CHANGE: TriggerEvent.NONE,  # Handled by specific phase triggers
            EventType.ENTERS_FIELD: TriggerEvent.ENTER_FIELD,
            EventType.LEAVES_FIELD: TriggerEvent.LEAVE_FIELD,
            EventType.CARD_DESTROYED: TriggerEvent.DESTROYED,
            EventType.CARD_BANISHED: TriggerEvent.BANISHED,
            EventType.ATTACK_DECLARED: TriggerEvent.ATTACK_DECLARED,
            EventType.BLOCKER_DECLARED: TriggerEvent.BLOCKER_DECLARED,
            EventType.DAMAGE_DEALT: TriggerEvent.DAMAGE_DEALT,
            EventType.PLAYER_DAMAGED: TriggerEvent.PLAYER_DAMAGED,
            EventType.CARD_DRAWN: TriggerEvent.CARD_DRAWN,
            EventType.WILL_PRODUCED: TriggerEvent.WILL_PRODUCED,
            EventType.STONE_CALLED: TriggerEvent.STONE_CALLED,
            EventType.LIFE_CHANGED: TriggerEvent.NONE,  # Handled by gain/loss
        }

    # =========================================================================
    # EVENT SYSTEM
    # =========================================================================

    def emit(self, event_type: EventType, player: int = -1, card: Card = None,
             target: Any = None, **data):
        """Emit a game event.

        Note: Trigger checking is handled by RulesEngine via wrapped emit().
        The RulesEngine hooks this method in _setup_event_hooks() and calls
        APNAPTriggerManager.check_triggers() after the event is processed.
        """
        print(f"[DEBUG] emit: {event_type.name}", flush=True)
        event = GameEvent(event_type, player, card, target, data)
        self._event_queue.append(event)

        for i, handler in enumerate(self._event_handlers):
            print(f"[DEBUG] emit: calling handler {i}", flush=True)
            try:
                handler(event)
            except Exception as e:
                print(f"[DEBUG] emit: handler {i} CRASHED: {e}", flush=True)
                import traceback
                traceback.print_exc()
                raise
            print(f"[DEBUG] emit: handler {i} done", flush=True)

        # Note: Trigger checking moved to RulesEngine (CR 906 APNAP ordering)
        # Legacy _check_triggers() removed - triggers now handled by APNAPTriggerManager

    def subscribe(self, handler: Callable[[GameEvent], None]):
        """Subscribe to game events"""
        self._event_handlers.append(handler)

    def poll_events(self) -> list[GameEvent]:
        """Poll and clear event queue"""
        events = list(self._event_queue)
        self._event_queue.clear()
        return events

    def _check_triggers(self, event: GameEvent):
        """Check for triggered abilities that respond to this event"""
        # Map EventType to TriggerEvent
        trigger_event = self._event_trigger_map.get(event.event_type)
        if not trigger_event:
            return

        # Build event data from GameEvent
        event_data = dict(event.data) if event.data else {}
        if event.card:
            event_data['card'] = event.card
            event_data['source'] = event.card
        if event.target:
            event_data['target'] = event.target
        event_data['player'] = event.player
        event_data['event_type'] = event.event_type

        # Check triggers
        self.trigger_manager.check_triggers(trigger_event, event_data)

    def process_pending_triggers(self):
        """Process all pending triggered abilities.

        Called after events settle to add triggered abilities to the chase.
        Uses RulesEngine's APNAPTriggerManager for CR 906 compliant ordering.
        """
        if self._rules_engine:
            self._rules_engine.add_triggers_to_chase()
        else:
            # Fallback to legacy (shouldn't happen if RulesEngine initialized)
            self.trigger_manager.process_pending_triggers()

    # =========================================================================
    # CARD MANAGEMENT
    # =========================================================================

    def create_card(self, data: CardData, owner: int) -> Card:
        """Create a new card instance"""
        self._uid_counter += 1
        uid = f"card_{self._uid_counter:04d}"

        card = Card(
            uid=uid,
            data=data,
            owner=owner,
            controller=owner,
            zone=Zone.MAIN_DECK,
        )

        self._all_cards[uid] = card
        return card

    def get_card(self, uid: str) -> Optional[Card]:
        """Get a card by UID"""
        return self._all_cards.get(uid)

    def get_script(self, card: Card):
        """Get the script for a card"""
        registry = _get_script_registry()
        return registry.get(card.data.code)

    def get_will_colors(self, card: Card) -> list:
        """Get the will colors a stone can produce"""
        script = self.get_script(card)
        return script.get_will_colors(self, card)

    def move_card(self, card: Card, to_zone: Zone, to_player: Optional[int] = None):
        """Move a card to a new zone"""
        print(f"[DEBUG] move_card: {card.data.name} to {to_zone.name}", flush=True)
        from_zone = card.zone
        from_player = card.controller

        # Remove from old zone
        old_zone = self.players[from_player].get_zone(from_zone)
        if card in old_zone:
            old_zone.remove(card)

        # Handle ruler area specially
        if from_zone == Zone.RULER_AREA:
            p = self.players[from_player]
            if p.ruler == card:
                p.ruler = None
            if p.j_ruler == card:
                p.j_ruler = None

        # Update controller if specified
        if to_player is not None:
            card.controller = to_player

        # Special handling for field entry
        if to_zone == Zone.FIELD and from_zone != Zone.FIELD:
            card.entered_turn = self.turn_number
            card.is_rested = False
            card.damage = 0

        # Add to new zone
        card.zone = to_zone
        new_zone = self.players[card.controller].get_zone(to_zone)
        new_zone.append(card)

        self.emit(EventType.CARD_MOVED, card.controller, card,
                  from_zone=from_zone.name, to_zone=to_zone.name)

        # Emit zone-specific events and call script hooks
        if to_zone == Zone.FIELD and from_zone != Zone.FIELD:
            print(f"[DEBUG] move_card: setting up card for {card.data.name} (code={card.data.code})", flush=True)
            script = self.get_script(card)
            print(f"[DEBUG] move_card: got script {script.__class__.__name__} for {card.data.code}", flush=True)
            try:
                # Initialize the script BEFORE emitting event (so triggers are registered)
                script.initial_effect(self, card)
                # Register card's triggers with the TriggerManager BEFORE emit
                self._register_card_triggers(card, script)
                # Register card's continuous effects
                self._register_card_continuous_effects(card, script)
            except Exception as e:
                print(f"[DEBUG] move_card: script setup CRASHED: {e}", flush=True)
                import traceback
                traceback.print_exc()
                raise

            # NOW emit the event (triggers are registered and will fire)
            print(f"[DEBUG] move_card: emitting ENTERS_FIELD for {card.data.name}", flush=True)
            self.emit(EventType.ENTERS_FIELD, card.controller, card)

            # Call script's on_enter_field hook (legacy, for manual handling)
            try:
                script.on_enter_field(self, card)
            except Exception as e:
                print(f"[DEBUG] move_card: on_enter_field hook error: {e}", flush=True)
            print(f"[DEBUG] move_card: on_enter_field done for {card.data.name}", flush=True)

        if from_zone == Zone.FIELD and to_zone != Zone.FIELD:
            self.emit(EventType.LEAVES_FIELD, from_player, card)
            # Unregister card's effects from RulesEngine
            if self._rules_engine:
                self._rules_engine.triggers.unregister_triggers(card)
                self._rules_engine.layers.unregister_effects_from_source(card.uid)
            # Call script's on_leave_field hook
            script = self.get_script(card)
            script.on_leave_field(self, card)

        if to_zone == Zone.GRAVEYARD:
            self.emit(EventType.ENTERS_GRAVEYARD, card.controller, card)

    # =========================================================================
    # GAME SETUP
    # =========================================================================

    def setup_game(self, p0_deck: list[CardData], p0_stones: list[CardData],
                   p0_ruler: CardData, p1_deck: list[CardData],
                   p1_stones: list[CardData], p1_ruler: CardData):
        """Set up a new game with the given decks"""
        self.players = [PlayerState(0), PlayerState(1)]
        self._all_cards.clear()
        self._uid_counter = 0

        for player_idx, (deck, stones, ruler) in enumerate([
            (p0_deck, p0_stones, p0_ruler),
            (p1_deck, p1_stones, p1_ruler)
        ]):
            p = self.players[player_idx]

            # Main deck
            for data in deck:
                card = self.create_card(data, player_idx)
                card.zone = Zone.MAIN_DECK
                p.main_deck.append(card)

            # Stone deck
            for data in stones:
                card = self.create_card(data, player_idx)
                card.zone = Zone.MAGIC_STONE_DECK
                p.stone_deck.append(card)

            # Ruler
            ruler_card = self.create_card(ruler, player_idx)
            ruler_card.zone = Zone.RULER_AREA
            p.ruler = ruler_card

    def shuffle_decks(self):
        """Shuffle both players' decks"""
        for p in self.players:
            random.shuffle(p.main_deck)
            random.shuffle(p.stone_deck)

    def start_game(self, first_player: int = 0):
        """Start the game"""
        self.turn_number = 1
        self.turn_player = first_player
        self.priority_player = first_player
        self.game_over = False
        self.winner = -1
        self.is_first_turn = True

        self.emit(EventType.GAME_START, first_player)

        # Draw starting hands (5 cards each)
        for p_idx in [0, 1]:
            self.draw_cards(p_idx, 5)

        # Start Turn 1 with Draw phase (official FoW order: Draw → Recovery → Main → End)
        self.change_phase(Phase.DRAW)

    # =========================================================================
    # TURN STRUCTURE
    # =========================================================================

    def start_turn(self):
        """Start a new turn"""
        p = self.players[self.turn_player]

        # Reset turn flags
        p.has_called_stone = False
        p.has_drawn_for_turn = False

        # Reset once-per-turn triggers at turn start
        if self._rules_engine:
            self._rules_engine.triggers.reset_turn()
        else:
            self.trigger_manager.reset_turn_triggers()

        # Call on_turn_start on all card scripts for this player's cards
        self._call_turn_start_hooks(self.turn_player)

        self.emit(EventType.TURN_START, self.turn_player, turn=self.turn_number)

        # Process any pending triggers from turn start
        self.process_pending_triggers()

        # Go to draw phase first (official FoW order: Draw → Recovery → Main → End)
        self.change_phase(Phase.DRAW)

    def _call_turn_start_hooks(self, player: int):
        """Call on_turn_start hooks on all cards controlled by player"""
        p = self.players[player]
        for card in p.field:
            script = self.get_script(card)
            if script:
                script.on_turn_start(self, card)

    def _call_turn_end_hooks(self, player: int):
        """Call on_turn_end hooks on all cards controlled by player"""
        p = self.players[player]
        for card in p.field:
            script = self.get_script(card)
            if script and hasattr(script, 'on_turn_end'):
                try:
                    script.on_turn_end(self, card)
                except Exception as e:
                    print(f"[DEBUG] on_turn_end hook error for {card.data.name}: {e}")

    def _register_card_triggers(self, card: Card, script):
        """Register a card's triggered abilities with RulesEngine's APNAPTriggerManager.

        CR 906: Automatic abilities use APNAP ordering when multiple trigger simultaneously.
        """
        if not self._rules_engine:
            return

        from .rules.types import TriggerCondition, TriggerTiming
        from .rules.triggers import TriggeredAbility, TriggerType

        # Check for RulesCardScript-style AutomaticAbility first (preferred)
        if hasattr(script, '_abilities'):
            from .rules.abilities import AutomaticAbility
            for ability in script._abilities:
                if isinstance(ability, AutomaticAbility):
                    # Create trigger that calls the ability's resolve method
                    def make_operation(ab):
                        def operation(game, source, event_data):
                            ab.resolve(game, source, source.controller)
                        return operation

                    trigger = TriggeredAbility(
                        name=ability.name or "Triggered Ability",
                        trigger_condition=ability.trigger_condition,
                        trigger_type=TriggerType.STANDARD,
                        operation=make_operation(ability),
                        is_mandatory=ability.is_mandatory,
                        once_per_turn=ability.once_per_turn,
                        timing=ability.trigger_timing,
                    )
                    self._rules_engine.triggers.register_trigger(card, trigger)

        # Also check for legacy-style effects (backward compatibility)
        from .scripts import EffectType
        effect_type_to_trigger = {
            EffectType.TRIGGER_ENTER: TriggerCondition.ENTER_FIELD,
            EffectType.TRIGGER_LEAVE: TriggerCondition.LEAVE_FIELD,
            EffectType.TRIGGER_ATTACK: TriggerCondition.DECLARES_ATTACK,
            EffectType.TRIGGER_BLOCK: TriggerCondition.DECLARES_BLOCK,
            EffectType.TRIGGER_DAMAGE: TriggerCondition.DEALS_DAMAGE,
            EffectType.TRIGGER_RECOVER: TriggerCondition.RECOVERED,
            EffectType.TRIGGER_REST: TriggerCondition.RESTED,
        }

        for effect in script.get_effects():
            trigger_cond = effect_type_to_trigger.get(effect.effect_type)
            if trigger_cond and effect.operation:
                trigger = TriggeredAbility(
                    name=effect.name or "Triggered Ability",
                    trigger_condition=trigger_cond,
                    trigger_type=TriggerType.STANDARD,
                    operation=effect.operation,
                    is_mandatory=effect.is_mandatory,
                    once_per_turn=effect.once_per_turn,
                    timing=TriggerTiming.CHASE if effect.uses_chase else TriggerTiming.IMMEDIATE,
                )
                self._rules_engine.triggers.register_trigger(card, trigger)

    def _register_card_continuous_effects(self, card: Card, script):
        """Register a card's continuous effects with RulesEngine's LayerManager.

        CR 909: Continuous effects are applied in layer order.
        """
        if not self._rules_engine:
            return

        from .rules.layers import LayeredEffect, Layer
        from .rules.types import EffectDuration

        # Check for RulesCardScript-style continuous effects (preferred)
        if hasattr(script, 'get_continuous_effects'):
            try:
                cr_effects = script.get_continuous_effects(self, card)
                for cr_effect in cr_effects:
                    # Convert to LayeredEffect for the layer system
                    layered = LayeredEffect(
                        source_id=card.uid,
                        name=cr_effect.name,
                        layer=Layer.STAT_MODIFY,
                        duration=EffectDuration.WHILE_ON_FIELD,
                        modify_atk=cr_effect.atk_modifier,
                        modify_def=cr_effect.def_modifier,
                        affects_self_only=cr_effect.affects_self_only if hasattr(cr_effect, 'affects_self_only') else True,
                    )
                    self._rules_engine.layers.register_effect(layered)
            except Exception as e:
                print(f"[DEBUG] Error registering CR continuous effects: {e}")

        # Also handle legacy effects for backward compatibility
        from .scripts import EffectType
        for effect in script.get_effects():
            if effect.effect_type in (EffectType.CONTINUOUS, EffectType.STATIC):
                if effect.value and isinstance(effect.value, dict):
                    layered = LayeredEffect(
                        source_id=card.uid,
                        name=effect.name or "Continuous Effect",
                        layer=Layer.STAT_MODIFY,
                        duration=EffectDuration.WHILE_ON_FIELD,
                        modify_atk=effect.value.get('atk_mod', 0),
                        modify_def=effect.value.get('def_mod', 0),
                        affects_self_only=True,
                    )
                    self._rules_engine.layers.register_effect(layered)

    def change_phase(self, new_phase: Phase):
        """Change to a new phase"""
        old_phase = self.current_phase
        self.current_phase = new_phase
        self.priority_player = self.turn_player
        self.consecutive_passes = 0

        self.emit(EventType.PHASE_CHANGE, self.turn_player,
                  old_phase=old_phase.name if old_phase else "None", new_phase=new_phase.name)

        # Phase entry effects
        if new_phase == Phase.DRAW:
            self._do_draw_phase()
        elif new_phase == Phase.RECOVERY:
            self._do_recovery_phase()
        elif new_phase == Phase.END:
            self._do_end_phase()

    def advance_phase(self):
        """Advance to the next phase"""
        # If in battle, resolve combat first instead of advancing phase
        if self.battle.in_battle:
            print(f"[DEBUG] advance_phase: in battle, advancing combat instead")
            self.advance_combat_step()
            return

        # Official FoW order: Draw → Recovery → Main → End
        phases = [Phase.DRAW, Phase.RECOVERY, Phase.MAIN, Phase.END]
        idx = phases.index(self.current_phase)
        print(f"[DEBUG] advance_phase: turn={self.turn_number}, player={self.turn_player}, current={self.current_phase.name}")

        if idx == len(phases) - 1:
            # End phase -> next turn
            print(f"[DEBUG] advance_phase: calling end_turn()")
            self.end_turn()
        else:
            next_phase = phases[idx + 1]
            print(f"[DEBUG] advance_phase: changing to {next_phase.name}")
            self.change_phase(next_phase)

    def end_turn(self):
        """End the current turn"""
        print(f"[DEBUG] end_turn: BEFORE turn={self.turn_number}, player={self.turn_player}")

        # Call on_turn_end hooks on all cards controlled by turn player
        self._call_turn_end_hooks(self.turn_player)

        self.emit(EventType.TURN_END, self.turn_player, turn=self.turn_number)

        # Process any end-of-turn triggers
        self.process_pending_triggers()

        # Clear "until end of turn" continuous effects
        self.continuous_manager.remove_end_of_turn_effects()

        # Clear will pools at end of End Phase (rule 505.5c)
        for p in self.players:
            p.will_pool.clear()

        # Clear temporary damage and reset cards for next turn
        for p in self.players:
            for card in p.field:
                # Reset temporary stat modifications
                if card.data:
                    card.current_atk = card.data.atk or 0
                    card.current_def = card.data.defense or 0
                card.damage = 0

        # Switch turn player
        self.turn_number += 1
        self.turn_player = 1 - self.turn_player
        self.is_first_turn = False
        print(f"[DEBUG] end_turn: AFTER turn={self.turn_number}, player={self.turn_player}")

        # Start next turn
        self.start_turn()

    def _do_recovery_phase(self):
        """Recovery phase logic"""
        p = self.players[self.turn_player]
        print(f"[DEBUG] _do_recovery_phase: turn={self.turn_number}, player={self.turn_player}, has_had_recovery={p.has_had_recovery}")

        # Clear will pool at start of Recovery Phase (rule 503.4)
        p.will_pool.clear()

        # Each player skips their recovery phase on their first turn
        # Track this per-player, not globally
        if not p.has_had_recovery:
            p.has_had_recovery = True
            print(f"[DEBUG] Recovery SKIPPED: turn={self.turn_number}, player={self.turn_player}, first recovery - setting has_had_recovery=True")
            return  # Skip recovery on first turn

        # Recover all rested cards
        rested_count = sum(1 for c in p.field if c.is_rested)
        for card in p.field:
            print(f"[DEBUG] Recovering card: {card.data.name}, was_rested={card.is_rested}")
            card.recover()
        print(f"[DEBUG] Recovery COMPLETE: turn={self.turn_number}, player={self.turn_player}, recovered {rested_count} cards")

        # Ruler/J-Ruler also recovers
        if p.ruler and p.ruler.is_rested:
            p.ruler.recover()
            print(f"[DEBUG] Ruler recovered")

    def _do_draw_phase(self):
        """Draw phase logic"""
        # Draw 1 card (except first player's first turn)
        if not (self.is_first_turn and self.turn_player == 0):
            self.draw_cards(self.turn_player, 1)
            self.players[self.turn_player].has_drawn_for_turn = True

    def _do_end_phase(self):
        """End phase logic"""
        p = self.players[self.turn_player]

        # Discard down to 7 cards
        while len(p.hand) > 7:
            # In real game, player chooses. For now, discard random
            card = p.hand[-1]
            self.move_card(card, Zone.GRAVEYARD)

        # Clear "until end of turn" effects
        # TODO: Implement temporary effect clearing

    # =========================================================================
    # PRIORITY SYSTEM
    # =========================================================================

    def pass_priority(self, player: int) -> bool:
        """
        Player passes priority.
        Returns True if both players have passed (chase resolves or phase advances).
        """
        if player != self.priority_player:
            return False

        self.consecutive_passes += 1
        self.emit(EventType.PRIORITY_PASSED, player)

        if self.consecutive_passes >= 2:
            self.emit(EventType.BOTH_PASSED, player)

            # If chase has items, resolve top item
            if self.chase:
                self._resolve_top_chase_item()
                self.consecutive_passes = 0
                return False
            else:
                # Chase empty, advance phase
                return True

        # Pass to opponent
        self.priority_player = 1 - player
        return False

    def give_priority(self, player: int):
        """Give priority to a player"""
        self.priority_player = player
        self.consecutive_passes = 0

    # =========================================================================
    # CHASE (STACK)
    # =========================================================================

    def add_to_chase(self, item: ChaseItem):
        """Add an item to the chase"""
        self.chase.append(item)
        self.emit(EventType.CHASE_ITEM_ADDED, item.controller, item.source,
                  item_type=item.item_type)

        # Give priority to opponent
        self.give_priority(1 - item.controller)

    def _resolve_top_chase_item(self):
        """Resolve the top item on the chase"""
        if not self.chase:
            return

        item = self.chase.pop()
        self.emit(EventType.CHASE_ITEM_RESOLVED, item.controller, item.source,
                  item_type=item.item_type)

        # Resolve based on type
        if item.item_type == "SPELL":
            self._resolve_spell(item)
        elif item.item_type == "ABILITY":
            self._resolve_ability(item)
        elif item.item_type == "TRIGGER":
            self._resolve_trigger(item)
        elif item.item_type == "JUDGMENT":
            self._resolve_judgment(item)

        # Run state-based actions
        self.run_state_based_actions()

        # Give priority back to active player
        self.give_priority(self.turn_player)

    def resolve_full_chase(self):
        """Resolve the entire chase"""
        while self.chase:
            self._resolve_top_chase_item()

    def _resolve_spell(self, item: ChaseItem):
        """Resolve a spell"""
        card = item.source

        # Execute spell effect
        self._execute_card_effect(card, item.targets)

        # Move to graveyard
        self.move_card(card, Zone.GRAVEYARD)

    def _resolve_ability(self, item: ChaseItem):
        """Resolve an activated/triggered ability"""
        card = item.source

        # Get the ability from the script
        if 'ability_index' in item.effect_data:
            script = self.get_script(card)
            if script:
                abilities = script.get_activated_abilities(self, card)
                ability_index = item.effect_data['ability_index']
                if ability_index < len(abilities):
                    ability = abilities[ability_index]
                    if ability.operation:
                        ability.operation(self, card)
                    return

        # Fallback to old behavior
        self._execute_card_effect(card, item.targets, item.effect_data)

    def _resolve_trigger(self, item: ChaseItem):
        """Resolve a triggered ability.

        Uses RulesEngine for CR 906 compliant resolution including
        intervening-if condition checking.
        """
        if self._rules_engine:
            # Use CR-compliant resolution (handles intervening-if)
            success = self._rules_engine.resolve_trigger(item)
            if success:
                print(f"[DEBUG] Resolved trigger: {item.effect_data.get('trigger_name', 'unnamed')} from {item.source.data.name}", flush=True)
            else:
                print(f"[DEBUG] Trigger fizzled (condition no longer met): {item.effect_data.get('trigger_name', 'unnamed')}", flush=True)
            return

        # Legacy fallback
        card = item.source
        effect_data = item.effect_data
        operation = effect_data.get('operation')
        event_data = effect_data.get('event_data', {})

        if operation:
            try:
                operation(self, card, event_data)
                print(f"[DEBUG] Resolved trigger: {effect_data.get('trigger_name', 'unnamed')} from {card.data.name}", flush=True)
            except Exception as e:
                print(f"[DEBUG] Trigger resolution failed: {e}", flush=True)
                import traceback
                traceback.print_exc()

    def _resolve_judgment(self, item: ChaseItem):
        """Resolve a Judgment"""
        ruler_card = item.source
        player_idx = item.controller
        p = self.players[player_idx]

        # Find J-Ruler data
        j_ruler_code = ruler_card.data.j_ruler_code
        if not j_ruler_code or not self.db:
            return

        j_ruler_data = self.db.get_card(j_ruler_code)
        if not j_ruler_data:
            return

        # Remove ruler from ruler area
        p.ruler = None

        # Create J-Ruler
        j_ruler = self.create_card(j_ruler_data, player_idx)
        j_ruler.zone = Zone.FIELD
        p.field.append(j_ruler)
        p.j_ruler = j_ruler
        p.has_j_ruled = True

        j_ruler.entered_turn = self.turn_number

        self.emit(EventType.J_RULER_ENTERS, player_idx, j_ruler)

    def _execute_card_effect(self, card: Card, targets: list, effect_data: dict = None):
        """Execute a card's effect via its script"""
        script = self.get_script(card)
        if hasattr(script, 'on_resolve'):
            script.on_resolve(self, card)
        print(f"[DEBUG] Executed effect for {card.data.name}", flush=True)

    # =========================================================================
    # CARD ACTIONS
    # =========================================================================

    def draw_cards(self, player: int, count: int) -> list[Card]:
        """Draw cards from deck to hand"""
        p = self.players[player]
        drawn = []

        for _ in range(count):
            if not p.main_deck:
                # Deck out - player loses
                self._player_loses(player, "deck out")
                break

            card = p.main_deck.pop(0)
            self.move_card(card, Zone.HAND, player)
            drawn.append(card)

            self.emit(EventType.CARD_DRAWN, player, card)

        return drawn

    def call_stone(self, player: int) -> bool:
        """Call a magic stone - requires resting the ruler"""
        print(f"[DEBUG] call_stone: player={player}", flush=True)
        p = self.players[player]

        # Check conditions
        if p.has_called_stone:
            return False
        if self.current_phase != Phase.MAIN:
            return False
        if player != self.turn_player:
            return False
        if not p.stone_deck:
            return False
        # Ruler must be able to rest to call a stone
        if not p.ruler or p.ruler.is_rested:
            return False

        # Rest the ruler
        print(f"[DEBUG] call_stone: resting ruler", flush=True)
        p.ruler.rest()

        # Call stone
        stone = p.stone_deck.pop(0)
        print(f"[DEBUG] call_stone: moving stone {stone.data.name}", flush=True)
        self.move_card(stone, Zone.FIELD, player)
        p.has_called_stone = True

        print(f"[DEBUG] call_stone: emitting event", flush=True)
        self.emit(EventType.STONE_CALLED, player, stone)
        print(f"[DEBUG] call_stone: done", flush=True)
        return True

    def produce_will(self, player: int, card: Card, chosen_attr: Attribute = None) -> bool:
        """Produce will from a card (stone or resonator with will ability).

        Args:
            player: Player index
            card: The card to tap for will
            chosen_attr: The chosen attribute to produce. Required for multi-color sources.
        """
        p = self.players[player]

        if card.zone != Zone.FIELD:
            return False
        if card.is_rested:
            return False

        # Get the card's script and check if it can produce will
        script = self.get_script(card)
        available_colors = script.get_will_colors(self, card)

        # If no colors available, this card can't produce will
        if not available_colors:
            return False

        # Determine which color to produce
        if chosen_attr is not None:
            attr = chosen_attr
        elif len(available_colors) == 1:
            attr = available_colors[0]
        else:
            # Multiple colors available but none chosen - use first
            attr = available_colors[0]

        # Validate the chosen color is valid for this card
        if attr not in available_colors and attr != Attribute.VOID:
            return False

        # Use script's produce_will (handles resting, special cases like Moon Shade life cost)
        success = script.produce_will(self, card, attr)

        if success:
            self.emit(EventType.WILL_PRODUCED, player, card, attribute=attr.name)

        return success

    def activate_ability(self, player: int, card: Card, ability_index: int,
                         targets: list = None) -> bool:
        """Activate an ability on a card.

        Args:
            player: Player activating the ability
            card: Card with the ability
            ability_index: Index of the ability in the card's ability list
            targets: Optional targets for the ability

        Returns:
            True if ability was activated successfully
        """
        p = self.players[player]
        script = self.get_script(card)
        if not script:
            return False

        abilities = script.get_activated_abilities(self, card)
        if ability_index >= len(abilities):
            return False

        ability = abilities[ability_index]

        # Check costs
        if ability.will_cost and not p.will_pool.can_pay(ability.will_cost):
            return False
        if ability.tap_cost and card.is_rested:
            return False

        # Pay costs
        if ability.will_cost:
            p.will_pool.pay(ability.will_cost)
            self.emit(EventType.WILL_SPENT, player, card, cost=str(ability.will_cost))
        if ability.tap_cost:
            card.rest()

        # Check if additional cost (like sacrifice, discard, etc.)
        if ability.additional_cost:
            if not ability.additional_cost(self, card):
                # Cost couldn't be paid, refund will
                if ability.will_cost:
                    for attr, amount in ability.will_cost.to_dict().items():
                        if attr != 'generic':
                            attr_enum = Attribute[attr.upper()]
                            p.will_pool.add(attr_enum, amount)
                return False

        # Mark as used if once per turn
        if ability.once_per_turn:
            ability._activated_this_turn = True

        # Check if this ability uses the Chase
        if ability.uses_chase:
            # Add to Chase for resolution
            item = ChaseItem(
                uid=str(uuid.uuid4()),
                source=card,
                item_type="ABILITY",
                controller=player,
                targets=targets or [],
                effect_data={"ability_index": ability_index},
            )
            self.add_to_chase(item)
        else:
            # Resolve immediately (like Will abilities)
            if ability.operation:
                ability.operation(self, card)

        return True

    def play_card(self, player: int, card: Card, targets: list = None,
                   use_awakening: bool = False, use_incarnation: bool = False,
                   incarnation_cards: list = None, x_value: int = 0) -> bool:
        """
        Play a card from hand.

        Args:
            player: Player index
            card: Card to play
            targets: Target cards for the spell/ability
            use_awakening: Whether to pay awakening cost for enhanced effect
            use_incarnation: Whether to use incarnation alternative cost
            incarnation_cards: Cards to banish for incarnation
            x_value: Value for X costs
        """
        p = self.players[player]

        if card.zone != Zone.HAND:
            return False
        if card.controller != player:
            return False

        # Check timing
        if not self._can_play_card(player, card):
            return False

        # Validate targets (CR 1120 - Barrier/Hexproof)
        if targets:
            valid_targets = self.validate_targets(card, targets, player)
            # If we had targets but none are valid, spell can't be played
            if len(valid_targets) == 0 and len(targets) > 0:
                return False
            targets = valid_targets

        # Get script for alternative costs
        script = self.get_script(card)

        # Handle Incarnation (CR 1105) - alternative cost via banishing
        if use_incarnation and script:
            incarnation_cost = getattr(script, 'incarnation_cost', None)
            if not incarnation_cost:
                # Check registered alternative costs
                alt_costs = getattr(script, '_alternative_costs', [])
                for cost in alt_costs:
                    if hasattr(cost, 'banish_count'):  # IncarnationCost
                        incarnation_cost = cost
                        break

            if incarnation_cost:
                if not incarnation_cost.can_pay(self, player):
                    return False
                if not incarnation_cards or len(incarnation_cards) < incarnation_cost.banish_count:
                    return False
                # Pay incarnation cost (banish resonators)
                incarnation_cost.pay(self, player, incarnation_cards)
                # Mark card as played via incarnation
                card.played_via_incarnation = True
            else:
                return False  # No incarnation cost available
        else:
            # Normal cost payment
            # Check for Grimm's ability: Fairy Tale resonators can be paid with any will
            any_will = self._grimm_fairy_tale_check(player, card)

            # Check base cost
            if not p.will_pool.can_pay(card.data.cost, any_will_pays_colored=any_will):
                return False

            # Pay base cost
            p.will_pool.pay(card.data.cost, any_will_pays_colored=any_will)
            self.emit(EventType.WILL_SPENT, player, card, cost=str(card.data.cost))

        # Handle Awakening (CR 1102) - extra cost for enhanced effect
        if use_awakening and script:
            awakening_cost = getattr(script, 'awakening_cost', None)
            if awakening_cost:
                if not awakening_cost.can_pay(self, player, x_value):
                    return False
                awakening_cost.pay(self, player, x_value)
                # Mark card as awakened
                card.is_awakened = True
                self.emit(EventType.WILL_SPENT, player, card, cost="awakening")

        # Store X value on card for effect resolution
        if x_value > 0:
            card.x_value = x_value

        # Handle based on card type
        if card.data.is_resonator():
            self._play_resonator(player, card)
        elif card.data.is_spell():
            self._play_spell(player, card, targets)
        elif card.data.card_type in [CardType.ADDITION_FIELD, CardType.REGALIA]:
            self._play_addition(player, card, targets)

        self.emit(EventType.CARD_PLAYED, player, card)
        return True

    def get_available_alternative_costs(self, card: Card, player: int) -> dict:
        """
        Get available alternative costs for a card.

        Returns dict with 'awakening' and 'incarnation' keys if available.
        """
        result = {'awakening': None, 'incarnation': None}
        script = self.get_script(card)

        if not script:
            return result

        # Check awakening
        awakening = getattr(script, 'awakening_cost', None)
        if awakening and awakening.can_pay(self, player):
            result['awakening'] = awakening

        # Check incarnation
        incarnation = getattr(script, 'incarnation_cost', None)
        if not incarnation:
            alt_costs = getattr(script, '_alternative_costs', [])
            for cost in alt_costs:
                if hasattr(cost, 'banish_count'):
                    incarnation = cost
                    break

        if incarnation and incarnation.can_pay(self, player):
            result['incarnation'] = incarnation

        return result

    # =========================================================================
    # CHANT-STANDBY ZONE
    # =========================================================================

    def set_in_standby(self, player: int, card: Card) -> bool:
        """
        Set a Chant-Standby card face-down in the standby zone.

        CR 711: Chant-Standby cards can be set face-down by paying {2}.
        They can be played from the next turn when their Trigger condition is met.
        """
        if card.zone != Zone.HAND:
            return False
        if card.data.card_type != CardType.SPELL_CHANT_STANDBY:
            return False
        if card.controller != player:
            return False

        p = self.players[player]

        # Pay {2} to set in standby
        standby_cost = WillCost(generic=2)
        if not p.will_pool.can_pay(standby_cost):
            return False

        p.will_pool.pay(standby_cost)
        self.emit(EventType.WILL_SPENT, player, card, cost="{2}")

        # Move to standby zone
        self.move_card(card, Zone.STANDBY, player)
        card.is_face_down = True
        card.set_turn = self.turn_number  # Track when it was set

        return True

    def can_play_from_standby(self, player: int, card: Card) -> bool:
        """
        Check if a Chant-Standby card can be played from standby.

        Requirements:
        - Card is in standby zone
        - It's not the turn it was set
        - Player controls magic stones >= card cost
        - Trigger condition is met (if any)
        """
        if card.zone != Zone.STANDBY:
            return False
        if card.controller != player:
            return False

        # Can't play on the turn it was set
        set_turn = getattr(card, 'set_turn', 0)
        if set_turn == self.turn_number:
            return False

        # Check stone count >= cost
        p = self.players[player]
        card_cost = card.data.cost.total() if card.data and card.data.cost else 0
        stone_count = len([c for c in p.field if c.data and c.data.card_type == CardType.MAGIC_STONE])
        if stone_count < card_cost:
            return False

        # Check trigger condition (script should define this)
        script = self.get_script(card)
        if script and hasattr(script, 'check_trigger_condition'):
            if not script.check_trigger_condition(self, card):
                return False

        return True

    def play_from_standby(self, player: int, card: Card, targets: list = None) -> bool:
        """
        Play a Chant-Standby card from the standby zone.
        """
        if not self.can_play_from_standby(player, card):
            return False

        p = self.players[player]

        # Pay the card's cost
        if not p.will_pool.can_pay(card.data.cost):
            return False

        p.will_pool.pay(card.data.cost)
        self.emit(EventType.WILL_SPENT, player, card, cost=str(card.data.cost))

        # Remove from standby, add to chase as spell
        card.is_face_down = False
        self._play_spell(player, card, targets)

        self.emit(EventType.CARD_PLAYED, player, card)
        return True

    def get_playable_standby_cards(self, player: int) -> list:
        """Get all standby cards that can currently be played."""
        p = self.players[player]
        playable = []
        for card in p.standby:
            if self.can_play_from_standby(player, card):
                playable.append(card)
        return playable

    def _can_play_card(self, player: int, card: Card) -> bool:
        """Check if a card can be played right now"""
        # Check if it's this player's turn for sorcery-speed cards
        if not card.data.is_instant():
            if player != self.turn_player:
                return False
            if self.current_phase != Phase.MAIN:
                return False

        return True

    def is_valid_target(self, source: Card, target: Card, source_controller: int,
                         target_filter=None) -> bool:
        """
        Check if a card is a valid target for a spell/ability.

        CR 1120: Barrier - Can't be targeted by opponent's spells/abilities.
        Also checks Hexproof (alias for Barrier in some contexts).

        Args:
            source: The spell or ability source card
            target: The card being targeted
            source_controller: Controller of the source
            target_filter: Optional TargetFilter for additional restrictions

        Returns:
            True if targeting is allowed
        """
        if target is None:
            return False

        # Check Barrier/Hexproof (CR 1120)
        # Only blocks opponent targeting
        if target.controller != source_controller:
            if target.has_keyword(Keyword.BARRIER):
                return False
            if target.has_keyword(Keyword.HEXPROOF):
                return False

        # Check custom target filter
        if target_filter is not None:
            try:
                from .rules.targeting import TargetFilter
                if isinstance(target_filter, TargetFilter):
                    if not target_filter.matches(target, target.controller, source_controller):
                        return False
            except ImportError:
                pass

        # Use rules engine if available for additional checks
        rules = self._get_rules_engine()
        if rules:
            return rules.check_targeting_allowed(source, target, source_controller)

        return True

    def validate_targets(self, source: Card, targets: list, source_controller: int,
                          target_filter=None) -> list:
        """
        Validate a list of targets, removing invalid ones.

        Returns only the valid targets from the input list.
        """
        if not targets:
            return []

        valid = []
        for target in targets:
            if isinstance(target, Card):
                if self.is_valid_target(source, target, source_controller, target_filter):
                    valid.append(target)
            else:
                # Non-card targets (players, etc.) are valid
                valid.append(target)

        return valid

    def get_valid_targets(self, source: Card, source_controller: int,
                           target_filter=None, zone=None) -> list:
        """
        Get all valid targets for a spell/ability.

        Args:
            source: The spell or ability source card
            source_controller: Controller of the source
            target_filter: Optional TargetFilter for restrictions
            zone: Optional zone to search (default: FIELD)

        Returns:
            List of valid target cards
        """
        if zone is None:
            zone = Zone.FIELD

        valid = []
        for p_idx, p in enumerate(self.players):
            cards_in_zone = p.get_zone(zone) if hasattr(p, 'get_zone') else []
            if zone == Zone.FIELD:
                cards_in_zone = p.field
            elif zone == Zone.GRAVEYARD:
                cards_in_zone = p.graveyard
            elif zone == Zone.HAND:
                # Can only target own hand typically
                if p_idx == source_controller:
                    cards_in_zone = p.hand
                else:
                    continue

            for card in cards_in_zone:
                if self.is_valid_target(source, card, source_controller, target_filter):
                    valid.append(card)

        return valid

    def get_targets_with_cost_filter(self, source: Card, source_controller: int,
                                      max_cost: int = None, min_cost: int = None,
                                      card_types: list = None) -> list:
        """
        Convenience method for finding targets by cost.

        Common pattern: "target resonator with total cost X or less"
        """
        try:
            from .rules.targeting import TargetFilter, TargetController
            target_filter = TargetFilter(
                max_total_cost=max_cost,
                min_total_cost=min_cost,
                card_types=card_types,
                controllers=[TargetController.ANY]
            )
            return self.get_valid_targets(source, source_controller, target_filter)
        except ImportError:
            # Fallback without targeting module
            valid = []
            for p in self.players:
                for card in p.field:
                    if max_cost is not None and card.data and card.data.cost:
                        if card.data.cost.total > max_cost:
                            continue
                    if min_cost is not None and card.data and card.data.cost:
                        if card.data.cost.total < min_cost:
                            continue
                    if card_types and card.data:
                        if card.data.card_type.value not in card_types:
                            continue
                    if self.is_valid_target(source, card, source_controller):
                        valid.append(card)
            return valid

    def _grimm_fairy_tale_check(self, player: int, card: Card) -> bool:
        """Check if Grimm's ability allows paying with any will color.

        Grimm, the Fairy Tale Prince (CMF-005):
        'You may pay the attribute cost of Fairy Tale resonators with will of any attribute.'
        """
        p = self.players[player]

        # Check if ruler is Grimm
        ruler = p.ruler or p.j_ruler
        if not ruler:
            return False

        # Grimm is CMF-005
        if ruler.data.code != "CMF-005":
            return False

        # Check if card is a Fairy Tale resonator
        if not card.data.is_resonator():
            return False

        if not card.data.races:
            return False

        if 'Fairy Tale' not in card.data.races:
            return False

        return True

    def _play_resonator(self, player: int, card: Card):
        """Play a resonator to the field"""
        # Remove from hand and add to field
        self.move_card(card, Zone.FIELD, player)

        # Give priority to opponent
        self.give_priority(1 - player)

    def _play_spell(self, player: int, card: Card, targets: list = None):
        """Play a spell (add to chase)"""
        p = self.players[player]

        # Remove from hand
        p.hand.remove(card)
        card.zone = Zone.CHASE

        # Create chase item
        item = ChaseItem(
            uid=f"chase_{len(self.chase)}",
            source=card,
            item_type="SPELL",
            controller=player,
            targets=targets or [],
            paid_cost=card.data.cost,
        )

        self.add_to_chase(item)

    def _play_addition(self, player: int, card: Card, targets: list = None):
        """Play an addition"""
        # For field additions, just move to field
        if card.data.card_type == CardType.ADDITION_FIELD:
            self.move_card(card, Zone.FIELD, player)
        elif card.data.card_type == CardType.ADDITION_RESONATOR:
            # Attach to target resonator
            if targets and len(targets) > 0:
                target = targets[0]
                if isinstance(target, Card):
                    self.move_card(card, Zone.FIELD, player)
                    card.attached_to = target
                    target.attachments.append(card)

        self.give_priority(1 - player)

    def perform_judgment(self, player: int) -> bool:
        """Perform Judgment with ruler"""
        p = self.players[player]

        if not p.ruler:
            return False
        if p.has_j_ruled:
            return False
        if p.ruler.data.card_type != CardType.RULER:
            return False

        ruler = p.ruler
        judgment_cost = ruler.data.judgment_cost

        # Check and pay judgment cost
        if judgment_cost and not p.will_pool.can_pay(judgment_cost):
            return False

        if judgment_cost:
            p.will_pool.pay(judgment_cost)

        # Rest ruler (if not already)
        ruler.rest()

        # Create Judgment chase item
        item = ChaseItem(
            uid=f"judgment_{player}",
            source=ruler,
            item_type="JUDGMENT",
            controller=player,
        )

        self.add_to_chase(item)
        self.emit(EventType.JUDGMENT, player, ruler)
        return True

    # =========================================================================
    # COMBAT
    # =========================================================================

    def declare_attack(self, player: int, attacker: Card,
                       target_player: int = None, target_card: Card = None) -> bool:
        """Declare an attack"""
        print(f"[DEBUG] declare_attack: {attacker.data.name}, in_battle={self.battle.in_battle}, phase={self.current_phase.name}, player={player}, turn_player={self.turn_player}", flush=True)
        if self.battle.in_battle:
            print(f"[DEBUG] declare_attack FAIL: already in battle", flush=True)
            return False
        if self.current_phase != Phase.MAIN:
            print(f"[DEBUG] declare_attack FAIL: not main phase", flush=True)
            return False
        if player != self.turn_player:
            print(f"[DEBUG] declare_attack FAIL: not turn player", flush=True)
            return False
        if attacker.zone != Zone.FIELD:
            print(f"[DEBUG] declare_attack FAIL: not on field", flush=True)
            return False
        if attacker.is_rested:
            print(f"[DEBUG] declare_attack FAIL: attacker is rested", flush=True)
            return False

        # Check for summoning sickness
        if (attacker.entered_turn == self.turn_number and
            not attacker.has_keyword(Keyword.SWIFTNESS)):
            print(f"[DEBUG] declare_attack FAIL: summoning sickness", flush=True)
            return False

        # Check CANNOT_ATTACK keyword
        if attacker.has_keyword(Keyword.CANNOT_ATTACK):
            print(f"[DEBUG] declare_attack FAIL: has CANNOT_ATTACK", flush=True)
            return False

        # Check if attacking a resonator (requires Target Attack)
        if target_card is not None:
            # Must have TARGET_ATTACK to attack resonators directly
            if target_card.data.is_resonator():
                if not attacker.has_keyword(Keyword.TARGET_ATTACK):
                    print(f"[DEBUG] declare_attack FAIL: no TARGET_ATTACK to attack resonator", flush=True)
                    return False

                # PRECISION allows attacking recovered resonators
                # Without it, can only attack rested resonators
                if not target_card.is_rested and not attacker.has_keyword(Keyword.PRECISION):
                    print(f"[DEBUG] declare_attack FAIL: target recovered, no PRECISION", flush=True)
                    return False

        print(f"[DEBUG] declare_attack: SUCCESS, starting battle", flush=True)

        # Rest attacker (unless Vigilance)
        if not attacker.has_keyword(Keyword.VIGILANCE):
            attacker.rest()

        # Set up battle
        self.battle.in_battle = True
        self.battle.step = CombatStep.DECLARE_ATTACK
        self.battle.attacking_player = player
        self.battle.attacker = attacker
        self.battle.defending_player = target_player if target_player is not None else (1 - player)
        self.battle.defender = target_card

        self.emit(EventType.ATTACK_DECLARED, player, attacker,
                  target=target_card or self.battle.defending_player)

        # Call script's on_attack hook
        script = self.get_script(attacker)
        if script and hasattr(script, 'on_attack'):
            try:
                script.on_attack(self, attacker)
            except Exception as e:
                print(f"[DEBUG] on_attack hook error: {e}")

        # Give priority to defending player
        self.give_priority(self.battle.defending_player)
        return True

    def declare_blocker(self, player: int, blocker: Card) -> bool:
        """Declare a blocker"""
        if not self.battle.in_battle:
            return False
        if self.battle.step != CombatStep.DECLARE_BLOCKER:
            return False
        if player != self.battle.defending_player:
            return False
        if blocker.zone != Zone.FIELD:
            return False
        if blocker.is_rested:
            return False
        if blocker.controller != player:
            return False

        # Check CANNOT_BLOCK keyword
        if blocker.has_keyword(Keyword.CANNOT_BLOCK):
            return False

        # Check if attacker is UNBLOCKABLE or has STEALTH
        attacker = self.battle.attacker
        if attacker and attacker.has_keyword(Keyword.UNBLOCKABLE):
            return False
        if attacker and attacker.has_keyword(Keyword.STEALTH):
            return False

        # Check Flying
        if attacker and attacker.has_keyword(Keyword.FLYING):
            if not blocker.has_keyword(Keyword.FLYING):
                return False

        # Rest blocker
        blocker.rest()
        self.battle.blockers.append(blocker)

        self.emit(EventType.BLOCKER_DECLARED, player, blocker)
        return True

    def advance_combat_step(self):
        """Advance to the next combat step"""
        print(f"[DEBUG] advance_combat_step: current step={self.battle.step.name}", flush=True)
        steps = [
            CombatStep.DECLARE_ATTACK,
            CombatStep.DECLARE_BLOCKER,
            CombatStep.BEFORE_DAMAGE,
            CombatStep.FIRST_STRIKE_DAMAGE,
            CombatStep.NORMAL_DAMAGE,
            CombatStep.AFTER_DAMAGE,
            CombatStep.END_OF_BATTLE,
        ]

        idx = steps.index(self.battle.step)

        # Skip first strike if no first strikers
        if self.battle.step == CombatStep.BEFORE_DAMAGE:
            has_first_strike = (
                (self.battle.attacker and
                 self.battle.attacker.has_keyword(Keyword.FIRST_STRIKE)) or
                any(b.has_keyword(Keyword.FIRST_STRIKE) for b in self.battle.blockers)
            )
            if not has_first_strike:
                idx += 1  # Skip first strike damage

        if idx >= len(steps) - 1:
            print(f"[DEBUG] advance_combat_step: at end, calling _end_combat", flush=True)
            self._end_combat()
            return

        self.battle.step = steps[idx + 1]
        print(f"[DEBUG] advance_combat_step: new step={self.battle.step.name}", flush=True)

        # Handle damage steps
        if self.battle.step == CombatStep.FIRST_STRIKE_DAMAGE:
            print(f"[DEBUG] advance_combat_step: dealing first strike damage", flush=True)
            self._deal_first_strike_damage()
        elif self.battle.step == CombatStep.NORMAL_DAMAGE:
            print(f"[DEBUG] advance_combat_step: dealing normal damage", flush=True)
            self._deal_normal_damage()
        elif self.battle.step == CombatStep.END_OF_BATTLE:
            print(f"[DEBUG] advance_combat_step: end of battle step, calling _end_combat", flush=True)
            self._end_combat()

    def _deal_first_strike_damage(self):
        """Deal first strike damage"""
        attacker = self.battle.attacker
        if not attacker:
            return

        if attacker.has_keyword(Keyword.FIRST_STRIKE):
            self._deal_combat_damage(attacker, first_strike=True)

        for blocker in self.battle.blockers:
            if blocker.has_keyword(Keyword.FIRST_STRIKE):
                self._deal_combat_damage(blocker, first_strike=True, is_blocker=True)

    def _deal_normal_damage(self):
        """Deal normal combat damage"""
        attacker = self.battle.attacker
        if not attacker:
            return

        # Skip if attacker already dealt first strike damage and doesn't have double strike
        if not attacker.has_keyword(Keyword.FIRST_STRIKE):
            self._deal_combat_damage(attacker, first_strike=False)

        for blocker in self.battle.blockers:
            if not blocker.has_keyword(Keyword.FIRST_STRIKE):
                self._deal_combat_damage(blocker, first_strike=False, is_blocker=True)

    def _deal_combat_damage(self, card: Card, first_strike: bool = False, is_blocker: bool = False):
        """Deal combat damage from a card"""
        damage = card.effective_atk

        if is_blocker:
            # Blocker damages attacker
            target = self.battle.attacker
            if target:
                self._deal_damage_to_card(target, damage, card)
        else:
            # Attacker damages blocker(s) or player
            if self.battle.blockers:
                # Damage first blocker (simplified)
                target = self.battle.blockers[0]
                self._deal_damage_to_card(target, damage, card)

                # Pierce: excess damage to player
                if card.has_keyword(Keyword.PIERCE):
                    excess = damage - target.effective_def
                    if excess > 0:
                        self._deal_damage_to_player(
                            self.battle.defending_player, excess, card
                        )
            elif self.battle.defender:
                # Attacking another creature
                self._deal_damage_to_card(self.battle.defender, damage, card)
            else:
                # Direct attack on player
                self._deal_damage_to_player(self.battle.defending_player, damage, card)

        # Drain
        if card.has_keyword(Keyword.DRAIN) and damage > 0:
            self.players[card.controller].life += damage
            self.emit(EventType.LIFE_CHANGED, card.controller, card,
                      amount=damage, reason="drain")

    def _deal_damage_to_card(self, target: Card, amount: int, source: Card,
                             is_combat: bool = True) -> int:
        """Deal damage to a card.

        Checks replacement effects (CR 910) for damage prevention/modification.
        Returns actual damage dealt.
        """
        # Check rules engine for replacement effects
        if hasattr(self, '_rules_engine') and self._rules_engine:
            amount, was_modified = self._rules_engine.would_deal_damage(
                source, target, amount, is_combat
            )

        if amount <= 0:
            return 0

        target.damage += amount
        self.emit(EventType.DAMAGE_DEALT, source.controller, source,
                  target=target, amount=amount)

        # Handle keyword effects (Drain handled in combat, Pierce in combat damage)
        if hasattr(self, '_rules_engine') and self._rules_engine:
            self._rules_engine.on_deals_damage(source, target, amount, is_combat)

        return amount

    def _deal_damage_to_player(self, player: int, amount: int, source: Card):
        """Deal damage to a player"""
        p = self.players[player]
        p.life -= amount

        self.emit(EventType.PLAYER_DAMAGED, player, source, amount=amount)
        self.emit(EventType.LIFE_CHANGED, player, source,
                  old_life=p.life + amount, new_life=p.life)

        # Check for game loss
        if p.life <= 0:
            self._player_loses(player, "life reached 0")

    def _end_combat(self):
        """End the current combat"""
        print(f"[DEBUG] _end_combat: clearing battle state", flush=True)

        # Handle Explode - destroy creatures that dealt damage with Explode
        attacker = self.battle.attacker
        if attacker and attacker.has_keyword(Keyword.EXPLODE):
            if attacker.zone == Zone.FIELD:  # Still on field
                # Check if it dealt damage (was in combat)
                if self.battle.blockers or self.battle.defender:
                    self._destroy_card(attacker)
                    for blocker in self.battle.blockers:
                        if blocker.zone == Zone.FIELD:
                            self._destroy_card(blocker)

        self.emit(EventType.COMBAT_END, self.battle.attacking_player)
        self.battle.clear()
        print(f"[DEBUG] _end_combat: in_battle is now {self.battle.in_battle}", flush=True)

        # Run state-based actions (checks for lethal damage, 0 life, etc.)
        self.run_state_based_actions()

    # =========================================================================
    # STATE-BASED ACTIONS
    # =========================================================================

    def run_state_based_actions(self) -> bool:
        """
        Run state-based actions.

        CR 704: State-based actions are checked whenever a player would receive priority.
        CR 909: Continuous effects are applied in layer order before checking state.
        """
        # Apply continuous effects first using LayerManager (CR 909)
        if self._rules_engine:
            self._rules_engine.apply_continuous_effects()
        else:
            self.continuous_manager.apply_all_effects()

        changed = True
        iterations = 0

        while changed and iterations < 100:
            changed = False
            iterations += 1

            for p_idx, p in enumerate(self.players):
                # Destroy creatures with lethal damage
                for card in list(p.field):
                    if card.data.is_resonator() or card.data.card_type == CardType.J_RULER:
                        if card.damage >= card.effective_def:
                            if not card.has_keyword(Keyword.IMPERISHABLE):
                                self._destroy_card(card)
                                changed = True

                # Check for player loss
                if p.life <= 0 and not p.has_lost:
                    self._player_loses(p_idx, "life reached 0")
                    changed = True

            # Re-apply continuous effects if state changed
            if changed:
                if self._rules_engine:
                    self._rules_engine.apply_continuous_effects()
                else:
                    self.continuous_manager.apply_all_effects()

        # Process any pending triggered abilities (APNAP ordering)
        self.process_pending_triggers()

        self.emit(EventType.STATE_BASED_ACTIONS, -1)
        return iterations > 1

    def _destroy_card(self, card: Card, cause: str = ""):
        """Destroy a card (send to graveyard).

        Checks replacement effects (CR 910), Indestructible, and Imperishable (CR 1109).
        """
        # Check INDESTRUCTIBLE keyword - prevents all destruction
        if card.has_keyword(Keyword.INDESTRUCTIBLE):
            return False

        # Check rules engine for replacement effects
        if hasattr(self, '_rules_engine') and self._rules_engine:
            should_destroy, reason = self._rules_engine.would_destroy(card, cause)
            if not should_destroy:
                return False

        # Check Imperishable keyword (for J-rulers)
        if card.has_keyword(Keyword.IMPERISHABLE):
            if card.data.card_type == CardType.J_RULER:
                # Convert damage to life loss instead of destruction
                damage = card.damage or 0
                if damage > 0:
                    self.players[card.controller].life -= damage * 100
                    card.damage = 0
                return False  # Not destroyed

        self.emit(EventType.CARD_DESTROYED, card.controller, card)
        self.move_card(card, Zone.GRAVEYARD)
        return True

    def banish_card(self, card: Card, cause: str = "") -> bool:
        """
        Banish a card (remove from game).

        Banishing bypasses Indestructible and goes to removed zone.
        Used for Incarnation costs, exile effects, etc.
        """
        if card.zone == Zone.REMOVED:
            return False  # Already removed

        self.emit(EventType.CARD_BANISHED, card.controller, card)
        self.move_card(card, Zone.REMOVED)
        return True

    def _player_loses(self, player: int, reason: str):
        """Player loses the game"""
        p = self.players[player]
        p.has_lost = True

        # Check if game ends
        losers = [i for i, p in enumerate(self.players) if p.has_lost]
        if len(losers) == 2:
            # Draw
            self.game_over = True
            self.winner = -1
        elif len(losers) == 1:
            self.game_over = True
            self.winner = 1 - losers[0]

        if self.game_over:
            self.emit(EventType.GAME_END, self.winner, reason=reason)

    # =========================================================================
    # UTILITY
    # =========================================================================

    def get_legal_actions(self, player: int) -> list[dict]:
        """Get all legal actions for a player"""
        actions = []
        p = self.players[player]

        # Can pass priority?
        if player == self.priority_player:
            actions.append({"type": "pass_priority"})

        # Only more actions if it's our priority
        if player != self.priority_player:
            return actions

        # Main phase sorcery-speed actions
        if (player == self.turn_player and
            self.current_phase == Phase.MAIN and
            not self.chase):

            # Call stone (requires ruler that can rest)
            if (not p.has_called_stone and p.stone_deck and
                p.ruler and not p.ruler.is_rested):
                actions.append({"type": "call_stone"})

            # Play cards from hand
            for card in p.hand:
                any_will = self._grimm_fairy_tale_check(player, card)
                if p.will_pool.can_pay(card.data.cost, any_will_pays_colored=any_will):
                    actions.append({
                        "type": "play_card",
                        "card": card.uid,
                        "name": card.data.name,
                    })

            # Judgment
            if p.ruler and not p.has_j_ruled:
                if p.ruler.data.judgment_cost:
                    if p.will_pool.can_pay(p.ruler.data.judgment_cost):
                        actions.append({"type": "judgment"})

            # Attack
            if not self.battle.in_battle:
                for card in p.field:
                    if (card.data.is_resonator() or
                        card.data.card_type == CardType.J_RULER):
                        if not card.is_rested:
                            if (card.entered_turn != self.turn_number or
                                card.has_keyword(Keyword.SWIFTNESS)):
                                actions.append({
                                    "type": "attack",
                                    "card": card.uid,
                                    "name": card.data.name,
                                })

        # Produce will (any priority)
        for card in p.field:
            if card.data.is_stone() and not card.is_rested:
                actions.append({
                    "type": "produce_will",
                    "card": card.uid,
                    "name": card.data.name,
                })

        # Activated abilities from cards on field
        for card in p.field:
            script = self.get_script(card)
            if script:
                abilities = script.get_activated_abilities(self, card)
                for i, ability in enumerate(abilities):
                    # Check if costs can be paid
                    can_pay = True
                    if ability.will_cost and not p.will_pool.can_pay(ability.will_cost):
                        can_pay = False
                    if ability.tap_cost and card.is_rested:
                        can_pay = False
                    # Summoning sickness for tap abilities on resonators
                    if ability.tap_cost and card.data.is_resonator():
                        if (card.entered_turn == self.turn_number and
                            not card.has_keyword(Keyword.SWIFTNESS)):
                            can_pay = False

                    if can_pay:
                        actions.append({
                            "type": "activate_ability",
                            "card": card.uid,
                            "name": card.data.name,
                            "ability_index": i,
                            "ability_name": ability.name or f"Ability {i+1}",
                            "uses_chase": ability.uses_chase,
                        })

        # Instant-speed actions
        for card in p.hand:
            if card.data.is_instant():
                if p.will_pool.can_pay(card.data.cost):
                    actions.append({
                        "type": "play_instant",
                        "card": card.uid,
                        "name": card.data.name,
                    })

        # Blocking
        if (self.battle.in_battle and
            self.battle.step == CombatStep.DECLARE_BLOCKER and
            player == self.battle.defending_player):
            for card in p.field:
                if (card.data.is_resonator() and
                    not card.is_rested):
                    actions.append({
                        "type": "block",
                        "card": card.uid,
                        "name": card.data.name,
                    })

        return actions

    def to_dict(self) -> dict:
        """Export game state as dictionary"""
        return {
            "turn": self.turn_number,
            "turn_player": self.turn_player,
            "phase": self.current_phase.name,
            "priority_player": self.priority_player,
            "game_over": self.game_over,
            "winner": self.winner,
            "players": [p.to_dict() for p in self.players],
            "chase": [item.to_dict() for item in self.chase],
            "battle": {
                "in_battle": self.battle.in_battle,
                "step": self.battle.step.name,
                "attacker": self.battle.attacker.uid if self.battle.attacker else None,
                "defender": self.battle.defender.uid if self.battle.defender else None,
                "blockers": [b.uid for b in self.battle.blockers],
            }
        }
