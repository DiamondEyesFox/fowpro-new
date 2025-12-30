"""
Keyword Abilities System
========================

Implements FoW keyword abilities according to comprehensive rules.
Keywords modify how cards interact in combat and other game phases.
"""

from enum import Enum, auto, Flag
from dataclasses import dataclass, field
from typing import Callable, Optional, List, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ..engine import GameEngine
    from ..models import Card


class Keyword(Flag):
    """All FoW keywords as flags for efficient checking"""
    NONE = 0

    # Evasion keywords
    FLYING = auto()           # Can only be blocked by Flying/Reach
    STEALTH = auto()          # Cannot be blocked

    # Combat keywords
    FIRST_STRIKE = auto()     # Deals damage first in combat
    SWIFTNESS = auto()        # Can attack the turn it enters
    PRECISION = auto()        # Can attack J/Resonators directly
    PIERCE = auto()           # Excess damage goes to opponent
    TARGET_ATTACK = auto()    # Can attack rested J/Resonators

    # Defensive keywords
    IMPERISHABLE = auto()     # Cannot be destroyed
    BARRIER = auto()          # Cannot be targeted by opponent
    ETERNAL = auto()          # Returns from graveyard

    # Triggered keywords
    DRAIN = auto()            # Gain life equal to damage dealt
    EXPLODE = auto()          # Deal damage when destroyed
    REMNANT = auto()          # Can be cast from graveyard

    # Static keywords
    QUICKCAST = auto()        # Can be played at instant speed
    INCARNATION = auto()      # Alternative cost from graveyard
    INHERITANCE = auto()      # Pass abilities when destroyed
    RESONANCE = auto()        # Trigger when card with same name played
    AWAKENING = auto()        # Can pay extra for bonus effect
    MOBILIZE = auto()         # Resonators can attack same turn


# Keyword display names for UI
KEYWORD_NAMES = {
    Keyword.FLYING: "Flying",
    Keyword.STEALTH: "Stealth",
    Keyword.FIRST_STRIKE: "First Strike",
    Keyword.SWIFTNESS: "Swiftness",
    Keyword.PRECISION: "Precision",
    Keyword.PIERCE: "Pierce",
    Keyword.TARGET_ATTACK: "Target Attack",
    Keyword.IMPERISHABLE: "Imperishable",
    Keyword.BARRIER: "Barrier",
    Keyword.ETERNAL: "Eternal",
    Keyword.DRAIN: "Drain",
    Keyword.EXPLODE: "Explode",
    Keyword.REMNANT: "Remnant",
    Keyword.QUICKCAST: "Quickcast",
    Keyword.INCARNATION: "Incarnation",
    Keyword.INHERITANCE: "Inheritance",
    Keyword.RESONANCE: "Resonance",
    Keyword.AWAKENING: "Awakening",
    Keyword.MOBILIZE: "Mobilize",
}


# Map text to keyword flags
TEXT_TO_KEYWORD = {
    'flying': Keyword.FLYING,
    'stealth': Keyword.STEALTH,
    'first strike': Keyword.FIRST_STRIKE,
    'swiftness': Keyword.SWIFTNESS,
    'precision': Keyword.PRECISION,
    'pierce': Keyword.PIERCE,
    'target attack': Keyword.TARGET_ATTACK,
    'imperishable': Keyword.IMPERISHABLE,
    'barrier': Keyword.BARRIER,
    'eternal': Keyword.ETERNAL,
    'drain': Keyword.DRAIN,
    'explode': Keyword.EXPLODE,
    'remnant': Keyword.REMNANT,
    'quickcast': Keyword.QUICKCAST,
    'incarnation': Keyword.INCARNATION,
    'inheritance': Keyword.INHERITANCE,
    'resonance': Keyword.RESONANCE,
    'awakening': Keyword.AWAKENING,
    'mobilize': Keyword.MOBILIZE,
}


def parse_keywords(text: str) -> Keyword:
    """Parse keywords from ability text"""
    result = Keyword.NONE
    text_lower = text.lower()

    for keyword_text, keyword_flag in TEXT_TO_KEYWORD.items():
        if keyword_text in text_lower:
            result |= keyword_flag

    return result


@dataclass
class KeywordState:
    """Runtime keyword state for a card"""
    base_keywords: Keyword = Keyword.NONE      # From card text
    granted_keywords: Keyword = Keyword.NONE   # Temporary grants
    removed_keywords: Keyword = Keyword.NONE   # Temporarily removed

    @property
    def effective_keywords(self) -> Keyword:
        """Get currently active keywords"""
        return (self.base_keywords | self.granted_keywords) & ~self.removed_keywords

    def has(self, keyword: Keyword) -> bool:
        """Check if card has a keyword"""
        return bool(self.effective_keywords & keyword)

    def grant(self, keyword: Keyword):
        """Grant a keyword temporarily"""
        self.granted_keywords |= keyword

    def remove(self, keyword: Keyword):
        """Remove a keyword temporarily"""
        self.removed_keywords |= keyword

    def reset_temporary(self):
        """Reset temporary grants/removals (end of turn)"""
        self.granted_keywords = Keyword.NONE
        self.removed_keywords = Keyword.NONE


class KeywordProcessor:
    """Processes keyword effects during game phases"""

    def __init__(self, game: 'GameEngine'):
        self.game = game

    # =========================================================================
    # COMBAT KEYWORDS
    # =========================================================================

    def can_attack(self, attacker: 'Card') -> bool:
        """Check if a card can attack (Swiftness check)"""
        keywords = self._get_keywords(attacker)

        # Check if summoning sick
        if attacker.entered_field_this_turn:
            if not keywords.has(Keyword.SWIFTNESS):
                return False

        # Must be recovered (not rested)
        if attacker.is_rested:
            return False

        return True

    def can_block(self, blocker: 'Card', attacker: 'Card') -> bool:
        """Check if blocker can block attacker"""
        attacker_keywords = self._get_keywords(attacker)
        blocker_keywords = self._get_keywords(blocker)

        # Stealth cannot be blocked
        if attacker_keywords.has(Keyword.STEALTH):
            return False

        # Flying can only be blocked by Flying
        if attacker_keywords.has(Keyword.FLYING):
            if not blocker_keywords.has(Keyword.FLYING):
                return False

        return True

    def can_be_targeted(self, card: 'Card', by_player: int) -> bool:
        """Check if card can be targeted (Barrier check)"""
        keywords = self._get_keywords(card)

        # Barrier prevents opponent targeting
        if keywords.has(Keyword.BARRIER):
            if card.controller != by_player:
                return False

        return True

    def can_be_destroyed(self, card: 'Card') -> bool:
        """Check if card can be destroyed (Imperishable check)"""
        keywords = self._get_keywords(card)
        return not keywords.has(Keyword.IMPERISHABLE)

    def get_damage_order(self, combatants: List['Card']) -> List[List['Card']]:
        """Order combatants by First Strike for damage assignment"""
        first_strikers = []
        normal = []

        for card in combatants:
            keywords = self._get_keywords(card)
            if keywords.has(Keyword.FIRST_STRIKE):
                first_strikers.append(card)
            else:
                normal.append(card)

        # First strikers deal damage first, then normal
        result = []
        if first_strikers:
            result.append(first_strikers)
        if normal:
            result.append(normal)

        return result

    def apply_pierce_damage(self, attacker: 'Card', defender: 'Card',
                           damage_dealt: int) -> int:
        """Calculate pierce damage to defending player"""
        keywords = self._get_keywords(attacker)

        if not keywords.has(Keyword.PIERCE):
            return 0

        # Pierce: excess damage over defender's DEF goes to player
        defender_def = defender.current_def
        excess = max(0, damage_dealt - defender_def)

        return excess

    def apply_drain(self, card: 'Card', damage_dealt: int):
        """Apply Drain life gain"""
        keywords = self._get_keywords(card)

        if keywords.has(Keyword.DRAIN) and damage_dealt > 0:
            controller = self.game.players[card.controller]
            controller.life += damage_dealt
            self.game.emit_event('life_gained', {
                'player': card.controller,
                'amount': damage_dealt,
                'source': card,
            })

    def can_attack_directly(self, attacker: 'Card', target: 'Card') -> bool:
        """Check if attacker can attack a specific J/Resonator"""
        keywords = self._get_keywords(attacker)

        # Precision allows attacking J/Resonators directly
        if keywords.has(Keyword.PRECISION):
            return True

        # Target Attack allows attacking rested J/Resonators
        if keywords.has(Keyword.TARGET_ATTACK):
            if target.is_rested:
                return True

        return False

    # =========================================================================
    # ZONE CHANGE KEYWORDS
    # =========================================================================

    def on_destroyed(self, card: 'Card'):
        """Handle keywords that trigger on destruction"""
        keywords = self._get_keywords(card)

        # Eternal: return to hand at end of turn
        if keywords.has(Keyword.ETERNAL):
            self.game.register_end_of_turn_effect(
                lambda: self._return_to_hand(card)
            )

        # Explode: deal damage
        if keywords.has(Keyword.EXPLODE):
            # Parse explode value from card text if available
            explode_damage = self._parse_explode_damage(card)
            if explode_damage > 0:
                # Trigger target selection for explode
                self.game.emit_event('explode_trigger', {
                    'source': card,
                    'damage': explode_damage,
                })

    def can_play_from_graveyard(self, card: 'Card') -> bool:
        """Check Remnant/Incarnation for graveyard play"""
        keywords = self._get_keywords(card)
        return keywords.has(Keyword.REMNANT) or keywords.has(Keyword.INCARNATION)

    def is_quickcast(self, card: 'Card') -> bool:
        """Check if card can be played at instant speed"""
        keywords = self._get_keywords(card)
        return keywords.has(Keyword.QUICKCAST)

    # =========================================================================
    # HELPERS
    # =========================================================================

    def _get_keywords(self, card: 'Card') -> KeywordState:
        """Get keyword state for a card"""
        if not hasattr(card, 'keyword_state'):
            # Initialize from card text
            card.keyword_state = KeywordState()
            if card.data and card.data.ability_text:
                card.keyword_state.base_keywords = parse_keywords(card.data.ability_text)
        return card.keyword_state

    def _return_to_hand(self, card: 'Card'):
        """Return card from graveyard to hand (Eternal)"""
        from ..models import Zone
        if card.zone == Zone.GRAVEYARD:
            self.game.move_card(card, Zone.HAND)

    def _parse_explode_damage(self, card: 'Card') -> int:
        """Parse explode damage value from card text"""
        import re
        if card.data and card.data.ability_text:
            match = re.search(r'explode\s*(\d+)', card.data.ability_text.lower())
            if match:
                return int(match.group(1))
        return 0


# =============================================================================
# KEYWORD GRANT EFFECTS
# =============================================================================

def grant_flying(game: 'GameEngine', target: 'Card', until_end_of_turn: bool = True):
    """Grant Flying to a card"""
    _grant_keyword(game, target, Keyword.FLYING, until_end_of_turn)


def grant_swiftness(game: 'GameEngine', target: 'Card', until_end_of_turn: bool = True):
    """Grant Swiftness to a card"""
    _grant_keyword(game, target, Keyword.SWIFTNESS, until_end_of_turn)


def grant_first_strike(game: 'GameEngine', target: 'Card', until_end_of_turn: bool = True):
    """Grant First Strike to a card"""
    _grant_keyword(game, target, Keyword.FIRST_STRIKE, until_end_of_turn)


def grant_pierce(game: 'GameEngine', target: 'Card', until_end_of_turn: bool = True):
    """Grant Pierce to a card"""
    _grant_keyword(game, target, Keyword.PIERCE, until_end_of_turn)


def grant_imperishable(game: 'GameEngine', target: 'Card', until_end_of_turn: bool = True):
    """Grant Imperishable to a card"""
    _grant_keyword(game, target, Keyword.IMPERISHABLE, until_end_of_turn)


def grant_barrier(game: 'GameEngine', target: 'Card', until_end_of_turn: bool = True):
    """Grant Barrier to a card"""
    _grant_keyword(game, target, Keyword.BARRIER, until_end_of_turn)


def _grant_keyword(game: 'GameEngine', target: 'Card', keyword: Keyword,
                   until_end_of_turn: bool):
    """Internal helper to grant a keyword"""
    if not hasattr(target, 'keyword_state'):
        target.keyword_state = KeywordState()

    target.keyword_state.grant(keyword)

    if until_end_of_turn:
        game.register_end_of_turn_effect(
            lambda: target.keyword_state.remove(keyword)
        )


# =============================================================================
# KEYWORD REMOVAL EFFECTS
# =============================================================================

def remove_all_keywords(game: 'GameEngine', target: 'Card', until_end_of_turn: bool = True):
    """Remove all keywords from a card"""
    if not hasattr(target, 'keyword_state'):
        target.keyword_state = KeywordState()

    # Remove all possible keywords
    all_keywords = Keyword.FLYING | Keyword.STEALTH | Keyword.FIRST_STRIKE | \
                   Keyword.SWIFTNESS | Keyword.PRECISION | Keyword.PIERCE | \
                   Keyword.TARGET_ATTACK | Keyword.IMPERISHABLE | Keyword.BARRIER | \
                   Keyword.ETERNAL | Keyword.DRAIN | Keyword.EXPLODE | \
                   Keyword.REMNANT | Keyword.QUICKCAST

    target.keyword_state.removed_keywords |= all_keywords

    if until_end_of_turn:
        game.register_end_of_turn_effect(
            lambda: setattr(target.keyword_state, 'removed_keywords', Keyword.NONE)
        )
