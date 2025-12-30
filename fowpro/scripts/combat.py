"""
Combat System
=============

Handles the battle phase including:
- Attack declaration
- Blocker declaration
- Damage calculation and assignment
- First Strike damage step
- Control change effects
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Callable, Optional, List, Dict, Any, TYPE_CHECKING

from .keywords import Keyword, KeywordProcessor
from .triggers import TriggerEvent

if TYPE_CHECKING:
    from ..engine import GameEngine
    from ..models import Card, Player


class CombatPhase(Enum):
    """Phases within combat"""
    BEGINNING = auto()          # Start of battle phase
    DECLARE_ATTACKERS = auto()  # Active player declares attackers
    DECLARE_BLOCKERS = auto()   # Defending player declares blockers
    FIRST_STRIKE_DAMAGE = auto() # First strike damage step
    DAMAGE = auto()             # Regular damage step
    END = auto()                # End of battle phase


@dataclass
class AttackDeclaration:
    """An attack being made"""
    attacker: 'Card'
    target: Optional['Card'] = None     # J-Ruler/Resonator being attacked
    target_player: Optional[int] = None  # Player being attacked directly
    blocked_by: Optional['Card'] = None  # Blocking resonator


@dataclass
class CombatState:
    """Current state of combat"""
    phase: CombatPhase = CombatPhase.BEGINNING
    attacks: List[AttackDeclaration] = field(default_factory=list)
    active_player: int = 0
    defending_player: int = 1


class CombatManager:
    """Manages the battle phase"""

    def __init__(self, game: 'GameEngine'):
        self.game = game
        self.state: Optional[CombatState] = None
        self._ui_callback: Optional[Callable] = None

    def set_ui_callback(self, callback: Callable):
        """Set UI callback for combat decisions"""
        self._ui_callback = callback

    def begin_battle_phase(self, active_player: int):
        """Start the battle phase"""
        self.state = CombatState(
            phase=CombatPhase.BEGINNING,
            active_player=active_player,
            defending_player=1 - active_player,
        )

        self.game.emit_event('battle_phase_begin', {
            'active_player': active_player,
        })

        # Trigger beginning of battle effects
        self.game.trigger_manager.check_triggers(
            TriggerEvent.COMBAT_END,  # Use COMBAT_START if added
            {'phase': 'begin'}
        )

        self._advance_to_attackers()

    def _advance_to_attackers(self):
        """Move to attacker declaration"""
        self.state.phase = CombatPhase.DECLARE_ATTACKERS

        # Get legal attackers
        attackers = self._get_legal_attackers()

        if not attackers:
            # No attackers, skip combat
            self.end_battle_phase()
            return

        # Request attacker declaration from UI
        self._request_attackers(attackers)

    def _get_legal_attackers(self) -> List['Card']:
        """Get all cards that can legally attack"""
        player = self.game.players[self.state.active_player]
        kp = KeywordProcessor(self.game)
        legal = []

        for card in player.field:
            if not hasattr(card, 'is_token'):
                if not card.data or not card.data.is_resonator():
                    continue

            if kp.can_attack(card):
                legal.append(card)

        return legal

    def _request_attackers(self, legal: List['Card']):
        """Request attacker selection from UI"""
        if self._ui_callback:
            self._ui_callback({
                'type': 'declare_attackers',
                'legal_attackers': legal,
                'callback': self.declare_attackers,
            })
        else:
            # Auto: attack with all
            self.declare_attackers([
                {'attacker': a.uid, 'target_player': self.state.defending_player}
                for a in legal
            ])

    def declare_attackers(self, declarations: List[Dict]):
        """Process attacker declarations"""
        for decl in declarations:
            attacker = self._find_card(decl['attacker'])
            if not attacker:
                continue

            attack = AttackDeclaration(attacker=attacker)

            if 'target' in decl:
                attack.target = self._find_card(decl['target'])
            if 'target_player' in decl:
                attack.target_player = decl['target_player']

            self.state.attacks.append(attack)

            # Rest attacker
            attacker.is_rested = True

            # Trigger attack declaration
            self.game.trigger_manager.check_triggers(
                TriggerEvent.ATTACK_DECLARED,
                {
                    'attacker': attacker,
                    'target': attack.target,
                    'target_player': attack.target_player,
                }
            )

        if not self.state.attacks:
            self.end_battle_phase()
            return

        self._advance_to_blockers()

    def _advance_to_blockers(self):
        """Move to blocker declaration"""
        self.state.phase = CombatPhase.DECLARE_BLOCKERS

        # Get legal blockers
        blockers = self._get_legal_blockers()

        if not blockers:
            # No blockers possible, go to damage
            self._advance_to_damage()
            return

        self._request_blockers(blockers)

    def _get_legal_blockers(self) -> List['Card']:
        """Get all cards that can block"""
        player = self.game.players[self.state.defending_player]
        legal = []

        for card in player.field:
            if not hasattr(card, 'is_token'):
                if not card.data or not card.data.is_resonator():
                    continue

            # Must be recovered to block
            if card.is_rested:
                continue

            legal.append(card)

        return legal

    def _request_blockers(self, legal: List['Card']):
        """Request blocker selection from UI"""
        if self._ui_callback:
            self._ui_callback({
                'type': 'declare_blockers',
                'attacks': self.state.attacks,
                'legal_blockers': legal,
                'callback': self.declare_blockers,
            })
        else:
            # Auto: no blocks
            self.declare_blockers([])

    def declare_blockers(self, blocks: List[Dict]):
        """Process blocker declarations"""
        kp = KeywordProcessor(self.game)

        for block in blocks:
            blocker = self._find_card(block['blocker'])
            attack_index = block.get('attack_index', 0)

            if not blocker or attack_index >= len(self.state.attacks):
                continue

            attack = self.state.attacks[attack_index]

            # Check if blocker can block this attacker
            if not kp.can_block(blocker, attack.attacker):
                continue

            attack.blocked_by = blocker

            # Trigger blocker declaration
            self.game.trigger_manager.check_triggers(
                TriggerEvent.BLOCKER_DECLARED,
                {
                    'blocker': blocker,
                    'attacker': attack.attacker,
                }
            )

        self._advance_to_damage()

    def _advance_to_damage(self):
        """Move to damage step"""
        kp = KeywordProcessor(self.game)

        # Check for first strikers
        has_first_strike = False
        has_normal = False

        for attack in self.state.attacks:
            attacker_kw = kp._get_keywords(attack.attacker)
            if attacker_kw.has(Keyword.FIRST_STRIKE):
                has_first_strike = True
            else:
                has_normal = True

            if attack.blocked_by:
                blocker_kw = kp._get_keywords(attack.blocked_by)
                if blocker_kw.has(Keyword.FIRST_STRIKE):
                    has_first_strike = True
                else:
                    has_normal = True

        # First strike damage step
        if has_first_strike:
            self.state.phase = CombatPhase.FIRST_STRIKE_DAMAGE
            self._process_damage(first_strike_only=True)

            # Check for deaths
            self._check_combat_deaths()

        # Normal damage step
        if has_normal:
            self.state.phase = CombatPhase.DAMAGE
            self._process_damage(first_strike_only=False)

            # Check for deaths
            self._check_combat_deaths()

        self.end_battle_phase()

    def _process_damage(self, first_strike_only: bool):
        """Process damage for current step"""
        kp = KeywordProcessor(self.game)

        for attack in self.state.attacks:
            attacker = attack.attacker
            attacker_kw = kp._get_keywords(attacker)
            is_first_strike = attacker_kw.has(Keyword.FIRST_STRIKE)

            # Skip based on phase
            if first_strike_only and not is_first_strike:
                continue
            if not first_strike_only and is_first_strike:
                continue

            # Attacker is dead, skip
            if attacker.current_def <= 0:
                continue

            attacker_damage = attacker.current_atk

            if attack.blocked_by:
                blocker = attack.blocked_by
                blocker_kw = kp._get_keywords(blocker)
                blocker_is_fs = blocker_kw.has(Keyword.FIRST_STRIKE)

                # Attacker damages blocker
                if attacker_damage > 0 and blocker.current_def > 0:
                    blocker.current_def -= attacker_damage

                    self.game.trigger_manager.check_triggers(
                        TriggerEvent.DAMAGE_DEALT,
                        {
                            'source': attacker,
                            'target': blocker,
                            'amount': attacker_damage,
                        }
                    )

                    # Apply drain
                    kp.apply_drain(attacker, attacker_damage)

                    # Apply pierce
                    pierce_damage = kp.apply_pierce_damage(
                        attacker, blocker, attacker_damage
                    )
                    if pierce_damage > 0:
                        self._damage_player(
                            self.state.defending_player, pierce_damage, attacker
                        )

                # Blocker damages attacker (in appropriate phase)
                if (first_strike_only and blocker_is_fs) or \
                   (not first_strike_only and not blocker_is_fs):
                    blocker_damage = blocker.current_atk
                    if blocker_damage > 0 and attacker.current_def > 0:
                        attacker.current_def -= blocker_damage

                        self.game.trigger_manager.check_triggers(
                            TriggerEvent.DAMAGE_DEALT,
                            {
                                'source': blocker,
                                'target': attacker,
                                'amount': blocker_damage,
                            }
                        )

                        kp.apply_drain(blocker, blocker_damage)

            elif attack.target:
                # Attacking a J-Ruler/Resonator directly (Precision)
                target = attack.target
                if attacker_damage > 0 and target.current_def > 0:
                    target.current_def -= attacker_damage

                    self.game.trigger_manager.check_triggers(
                        TriggerEvent.DAMAGE_DEALT,
                        {
                            'source': attacker,
                            'target': target,
                            'amount': attacker_damage,
                        }
                    )

                    kp.apply_drain(attacker, attacker_damage)

            elif attack.target_player is not None:
                # Attacking player directly
                self._damage_player(attack.target_player, attacker_damage, attacker)

                kp.apply_drain(attacker, attacker_damage)

    def _damage_player(self, player_index: int, amount: int, source: 'Card'):
        """Deal damage to a player"""
        player = self.game.players[player_index]
        player.life -= amount

        self.game.trigger_manager.check_triggers(
            TriggerEvent.PLAYER_DAMAGED,
            {
                'player': player_index,
                'amount': amount,
                'source': source,
            }
        )

        self.game.emit_event('player_damaged', {
            'player': player_index,
            'amount': amount,
            'source': source,
        })

    def _check_combat_deaths(self):
        """Check for and process combat deaths"""
        from ..models import Zone
        kp = KeywordProcessor(self.game)

        for attack in self.state.attacks:
            # Check attacker
            if attack.attacker.current_def <= 0:
                if kp.can_be_destroyed(attack.attacker):
                    self.game.move_card(attack.attacker, Zone.GRAVEYARD)
                    kp.on_destroyed(attack.attacker)

            # Check blocker
            if attack.blocked_by and attack.blocked_by.current_def <= 0:
                if kp.can_be_destroyed(attack.blocked_by):
                    self.game.move_card(attack.blocked_by, Zone.GRAVEYARD)
                    kp.on_destroyed(attack.blocked_by)

            # Check target
            if attack.target and attack.target.current_def <= 0:
                if kp.can_be_destroyed(attack.target):
                    self.game.move_card(attack.target, Zone.GRAVEYARD)
                    kp.on_destroyed(attack.target)

    def end_battle_phase(self):
        """End the battle phase"""
        self.state.phase = CombatPhase.END

        self.game.trigger_manager.check_triggers(
            TriggerEvent.COMBAT_END,
            {}
        )

        self.game.emit_event('battle_phase_end', {})
        self.state = None

    def _find_card(self, card_id: str) -> Optional['Card']:
        """Find card by UID"""
        for player in self.game.players:
            for card in player.get_all_cards():
                if card.uid == card_id:
                    return card
        return None


# =============================================================================
# CONTROL CHANGE EFFECTS
# =============================================================================

class ControlManager:
    """Manages control change effects"""

    def __init__(self, game: 'GameEngine'):
        self.game = game
        self._control_effects: List[ControlEffect] = []

    def gain_control(self, card: 'Card', new_controller: int,
                    duration: str = 'permanent'):
        """Take control of a card"""
        old_controller = card.controller

        if old_controller == new_controller:
            return

        # Track control change
        effect = ControlEffect(
            card_id=card.uid,
            original_controller=old_controller,
            new_controller=new_controller,
            duration=duration,
        )
        self._control_effects.append(effect)

        # Actually change control
        self._apply_control_change(card, old_controller, new_controller)

        self.game.emit_event('control_changed', {
            'card': card,
            'from': old_controller,
            'to': new_controller,
        })

    def _apply_control_change(self, card: 'Card', old: int, new: int):
        """Apply the control change"""
        # Remove from old controller's field
        old_player = self.game.players[old]
        if card in old_player.field:
            old_player.field.remove(card)

        # Add to new controller's field
        new_player = self.game.players[new]
        new_player.field.append(card)

        # Update controller
        card.controller = new

    def end_turn_control_changes(self):
        """Revert 'until end of turn' control changes"""
        for effect in self._control_effects[:]:
            if effect.duration == 'end_of_turn':
                card = self._find_card(effect.card_id)
                if card:
                    self._apply_control_change(
                        card,
                        effect.new_controller,
                        effect.original_controller
                    )
                self._control_effects.remove(effect)

    def on_card_leaves_field(self, card: 'Card'):
        """Handle card leaving field - goes to owner's zones"""
        # Remove control effects for this card
        self._control_effects = [
            e for e in self._control_effects if e.card_id != card.uid
        ]

        # Card returns to owner
        card.controller = card.owner

    def _find_card(self, card_id: str) -> Optional['Card']:
        """Find card by UID"""
        for player in self.game.players:
            for card in player.get_all_cards():
                if card.uid == card_id:
                    return card
        return None


@dataclass
class ControlEffect:
    """Tracking for a control change"""
    card_id: str
    original_controller: int
    new_controller: int
    duration: str  # 'permanent', 'end_of_turn', 'source_leaves'


# =============================================================================
# CONTROL CHANGE HELPERS
# =============================================================================

def steal_until_end_of_turn(game: 'GameEngine', card: 'Card', new_controller: int):
    """Steal a card until end of turn"""
    game.control_manager.gain_control(card, new_controller, 'end_of_turn')


def steal_permanently(game: 'GameEngine', card: 'Card', new_controller: int):
    """Permanently steal a card"""
    game.control_manager.gain_control(card, new_controller, 'permanent')
