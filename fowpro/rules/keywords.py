"""
Keyword Abilities Implementation for Force of Will.

Complete implementation of all Grimm Cluster era keywords per CR 1100+.

References:
- CR 1101: Definition of Keyword Abilities
- CR 1103-1140: Individual keyword definitions
"""

from dataclasses import dataclass, field
from enum import Enum, Flag, auto
from typing import TYPE_CHECKING, List, Optional, Callable, Any, Dict

if TYPE_CHECKING:
    from ..engine import GameEngine
    from ..models import Card


class Keyword(Flag):
    """
    All keyword abilities in Force of Will (Grimm Cluster era).

    CR 1101: Keyword abilities are abilities represented by a single word.
    """
    NONE = 0

    # ==========================================================================
    # COMBAT KEYWORDS
    # ==========================================================================

    # CR 1103: Pierce
    # When this deals battle damage to a J/resonator, it deals the excess
    # damage to that J/resonator's controller.
    PIERCE = auto()

    # CR 1104: Precision
    # This can attack recovered J/resonators.
    PRECISION = auto()

    # CR 1105: First Strike
    # This deals its battle damage before J/resonators without first strike.
    FIRST_STRIKE = auto()

    # CR 1107: Flying
    # This can only be blocked by J/resonators with flying.
    FLYING = auto()

    # CR 1108: Swiftness
    # This can attack and use activated abilities with tap cost
    # the turn it enters the field.
    SWIFTNESS = auto()

    # CR 1106: Explode
    # When this deals battle damage to a J/resonator, destroy both this
    # and that J/resonator after the battle.
    EXPLODE = auto()

    # CR 1136: Drain
    # When this deals damage, its controller gains that much life.
    DRAIN = auto()

    # Target Attack
    # This can attack J/resonators directly (not just J-ruler/player).
    TARGET_ATTACK = auto()

    # ==========================================================================
    # PROTECTION KEYWORDS
    # ==========================================================================

    # CR 1109: Imperishable
    # If this J-ruler would be destroyed, it isn't destroyed and instead
    # the controller loses 100 life for each damage on it.
    IMPERISHABLE = auto()

    # CR 1120: Barrier
    # This can't be targeted by spells or abilities your opponent controls.
    BARRIER = auto()

    # Stealth
    # This can't be blocked.
    STEALTH = auto()

    # ==========================================================================
    # SPELL/ABILITY TIMING KEYWORDS
    # ==========================================================================

    # CR 1112: Quickcast
    # You may play this card or ability any time you could play an instant.
    QUICKCAST = auto()

    # CR 1113: Trigger
    # Special timing for chant cards that can respond to specific events.
    TRIGGER = auto()

    # ==========================================================================
    # ALTERNATIVE COST KEYWORDS
    # ==========================================================================

    # CR 1110: Awakening
    # When playing this card, you may pay an additional cost for a bonus effect.
    AWAKENING = auto()

    # CR 1111: Incarnation
    # You may banish a resonator you control with the specified race instead
    # of paying this card's cost.
    INCARNATION = auto()

    # Shift
    # Alternative cost that lets you swap with another card.
    SHIFT = auto()

    # ==========================================================================
    # GRAVEYARD KEYWORDS
    # ==========================================================================

    # CR 1115: Remnant
    # You may play this card from your graveyard. When you do, remove it
    # from the game instead of putting it into the graveyard.
    REMNANT = auto()

    # Eternal
    # When this would be put into a graveyard from anywhere, you may put
    # it into your hand instead.
    ETERNAL = auto()

    # ==========================================================================
    # ADDITION KEYWORDS
    # ==========================================================================

    # Bestow
    # You may play this addition onto a J/resonator.
    BESTOW = auto()

    # ==========================================================================
    # RULER KEYWORDS
    # ==========================================================================

    # Limit Break
    # Special ability that can only be used once per game.
    LIMIT_BREAK = auto()

    # Providence
    # Static ability that provides an ongoing effect from the ruler area.
    PROVIDENCE = auto()


@dataclass
class KeywordHandler:
    """
    Handler for a specific keyword's behavior.

    Each keyword can have:
    - Static effects (always active while card has keyword)
    - Triggered effects (trigger on specific events)
    - Replacement effects (modify how things happen)
    - Cost modifications (alternative/additional costs)
    """
    keyword: Keyword

    # Static continuous effect
    static_effect: Optional[Callable] = None

    # Triggered ability
    trigger_event: Optional[str] = None
    trigger_effect: Optional[Callable] = None

    # Replacement effect
    replaces_event: Optional[str] = None
    replacement: Optional[Callable] = None

    # Cost modification
    cost_modifier: Optional[Callable] = None

    # Restriction check
    restriction_check: Optional[Callable] = None


class KeywordManager:
    """
    Manages keyword ability behavior and effects.

    Integrates keywords into the game engine.
    """

    def __init__(self, game: 'GameEngine'):
        self.game = game
        self.handlers: Dict[Keyword, KeywordHandler] = {}
        self._register_all_handlers()

    def _register_all_handlers(self):
        """Register handlers for all keywords."""

        # ==== PIERCE (CR 1103) ====
        def pierce_damage_handler(game, source, target, damage, is_battle_damage):
            """Handle pierce excess damage."""
            if not is_battle_damage:
                return damage, 0

            if not hasattr(target, 'current_def') or target.current_def is None:
                return damage, 0

            excess = max(0, damage - target.current_def)
            if excess > 0:
                # Deal excess to controller
                target_controller = target.controller
                game.players[target_controller].life -= excess

            return damage, excess

        self.handlers[Keyword.PIERCE] = KeywordHandler(
            keyword=Keyword.PIERCE,
            trigger_event='deals_battle_damage',
            trigger_effect=pierce_damage_handler,
        )

        # ==== PRECISION (CR 1104) ====
        def precision_attack_check(game, attacker, target):
            """Allow attacking recovered J/resonators."""
            return True  # Always allows

        self.handlers[Keyword.PRECISION] = KeywordHandler(
            keyword=Keyword.PRECISION,
            restriction_check=precision_attack_check,
        )

        # ==== FIRST STRIKE (CR 1105) ====
        # First strike is handled in combat resolution
        self.handlers[Keyword.FIRST_STRIKE] = KeywordHandler(
            keyword=Keyword.FIRST_STRIKE,
        )

        # ==== FLYING (CR 1107) ====
        def flying_block_restriction(game, attacker, blocker):
            """Can only be blocked by flying."""
            if attacker.has_keyword(Keyword.FLYING):
                return blocker.has_keyword(Keyword.FLYING)
            return True

        self.handlers[Keyword.FLYING] = KeywordHandler(
            keyword=Keyword.FLYING,
            restriction_check=flying_block_restriction,
        )

        # ==== SWIFTNESS (CR 1108) ====
        # Handled by checking can_use_tap_abilities flag
        self.handlers[Keyword.SWIFTNESS] = KeywordHandler(
            keyword=Keyword.SWIFTNESS,
        )

        # ==== EXPLODE (CR 1106) ====
        def explode_handler(game, source, target, damage):
            """Mutual destruction after battle damage."""
            if damage > 0:
                # Mark both for destruction after battle
                source._explode_pending = True
                target._explode_pending = True

        self.handlers[Keyword.EXPLODE] = KeywordHandler(
            keyword=Keyword.EXPLODE,
            trigger_event='deals_battle_damage',
            trigger_effect=explode_handler,
        )

        # ==== DRAIN (CR 1136) ====
        def drain_handler(game, source, target, damage):
            """Gain life equal to damage dealt."""
            if damage > 0:
                game.players[source.controller].life += damage

        self.handlers[Keyword.DRAIN] = KeywordHandler(
            keyword=Keyword.DRAIN,
            trigger_event='deals_damage',
            trigger_effect=drain_handler,
        )

        # ==== IMPERISHABLE (CR 1109) ====
        def imperishable_replacement(game, card, event_data):
            """Prevent J-ruler destruction, lose life instead."""
            from ..models import CardType

            if card.data and card.data.card_type == CardType.J_RULER:
                damage = card.damage or 0
                if damage > 0:
                    game.players[card.controller].life -= damage * 100
                card.damage = 0
                return True  # Replaced - don't destroy
            return False  # Not replaced

        self.handlers[Keyword.IMPERISHABLE] = KeywordHandler(
            keyword=Keyword.IMPERISHABLE,
            replaces_event='destroy',
            replacement=imperishable_replacement,
        )

        # ==== BARRIER (CR 1120) ====
        def barrier_targeting_check(game, source, target, source_controller):
            """Prevent opponent targeting."""
            if target.has_keyword(Keyword.BARRIER):
                if source_controller != target.controller:
                    return False
            return True

        self.handlers[Keyword.BARRIER] = KeywordHandler(
            keyword=Keyword.BARRIER,
            restriction_check=barrier_targeting_check,
        )

        # ==== STEALTH ====
        def stealth_block_restriction(game, attacker, blocker):
            """Can't be blocked."""
            return not attacker.has_keyword(Keyword.STEALTH)

        self.handlers[Keyword.STEALTH] = KeywordHandler(
            keyword=Keyword.STEALTH,
            restriction_check=stealth_block_restriction,
        )

        # ==== QUICKCAST (CR 1112) ====
        # Handled in priority/timing checks
        self.handlers[Keyword.QUICKCAST] = KeywordHandler(
            keyword=Keyword.QUICKCAST,
        )

        # ==== ETERNAL ====
        def eternal_replacement(game, card, event_data):
            """Return to hand instead of graveyard."""
            from ..models import Zone
            target_zone = event_data.get('zone')
            if target_zone == Zone.GRAVEYARD:
                # Move to hand instead
                game.move_card(card, Zone.HAND, card.owner)
                return True
            return False

        self.handlers[Keyword.ETERNAL] = KeywordHandler(
            keyword=Keyword.ETERNAL,
            replaces_event='zone_change',
            replacement=eternal_replacement,
        )

        # ==== REMNANT (CR 1115) ====
        # Handled by allowing play from graveyard
        self.handlers[Keyword.REMNANT] = KeywordHandler(
            keyword=Keyword.REMNANT,
        )

        # ==== TARGET ATTACK ====
        # Handled by allowing selection of J/resonators as attack targets
        self.handlers[Keyword.TARGET_ATTACK] = KeywordHandler(
            keyword=Keyword.TARGET_ATTACK,
        )

    def card_has_keyword(self, card: 'Card', keyword: Keyword) -> bool:
        """Check if a card has a keyword (printed or granted)."""
        # Check granted keywords
        if card.granted_keywords & keyword:
            return True

        # Check printed keywords (from card data)
        if card.data and card.data.keywords:
            if keyword in card.data.keywords:
                return True

        return False

    def get_all_keywords(self, card: 'Card') -> Keyword:
        """Get all keywords a card currently has."""
        keywords = card.granted_keywords

        if card.data and card.data.keywords:
            keywords |= card.data.keywords

        return keywords

    def check_targeting(self, source: 'Card', target: 'Card',
                        source_controller: int) -> bool:
        """
        Check if targeting is allowed by keywords.

        CR 1120: Barrier prevents opponent targeting.
        """
        handler = self.handlers.get(Keyword.BARRIER)
        if handler and handler.restriction_check:
            if self.card_has_keyword(target, Keyword.BARRIER):
                return handler.restriction_check(
                    self.game, source, target, source_controller
                )
        return True

    def check_blocking(self, attacker: 'Card', blocker: 'Card') -> bool:
        """
        Check if blocking is allowed by keywords.

        CR 1107: Flying can only be blocked by flying.
        """
        # Check flying
        if self.card_has_keyword(attacker, Keyword.FLYING):
            if not self.card_has_keyword(blocker, Keyword.FLYING):
                return False

        # Check stealth
        if self.card_has_keyword(attacker, Keyword.STEALTH):
            return False

        return True

    def can_attack_target(self, attacker: 'Card', target: 'Card') -> bool:
        """
        Check if an attacker can target something.

        Target Attack allows attacking J/resonators.
        Precision allows attacking recovered J/resonators.
        """
        from ..models import CardType

        # J-ruler and player can always be attacked
        if not target or not target.data:
            return True

        if target.data.card_type == CardType.J_RULER:
            return True

        # Resonators require Target Attack
        if target.data.card_type == CardType.RESONATOR:
            if not self.card_has_keyword(attacker, Keyword.TARGET_ATTACK):
                return False

            # Recovered resonators require Precision
            if not target.is_rested:
                if not self.card_has_keyword(attacker, Keyword.PRECISION):
                    return False

        return True

    def can_act_on_entry(self, card: 'Card') -> bool:
        """
        Check if a card can attack/use tap abilities the turn it enters.

        CR 1108: Swiftness allows this.
        """
        return self.card_has_keyword(card, Keyword.SWIFTNESS)

    def on_deals_damage(self, source: 'Card', target: 'Card',
                        damage: int, is_battle_damage: bool) -> int:
        """Handle damage-related keyword effects."""
        total_damage = damage

        # Pierce
        if is_battle_damage and self.card_has_keyword(source, Keyword.PIERCE):
            handler = self.handlers.get(Keyword.PIERCE)
            if handler and handler.trigger_effect:
                _, excess = handler.trigger_effect(
                    self.game, source, target, damage, is_battle_damage
                )

        # Drain
        if self.card_has_keyword(source, Keyword.DRAIN):
            handler = self.handlers.get(Keyword.DRAIN)
            if handler and handler.trigger_effect:
                handler.trigger_effect(self.game, source, target, damage)

        # Explode
        if is_battle_damage and self.card_has_keyword(source, Keyword.EXPLODE):
            handler = self.handlers.get(Keyword.EXPLODE)
            if handler and handler.trigger_effect:
                handler.trigger_effect(self.game, source, target, damage)

        return total_damage

    def check_destroy_replacement(self, card: 'Card') -> bool:
        """
        Check for replacement effects on destruction.

        CR 1109: Imperishable replaces destruction.

        Returns True if destruction was replaced.
        """
        if self.card_has_keyword(card, Keyword.IMPERISHABLE):
            handler = self.handlers.get(Keyword.IMPERISHABLE)
            if handler and handler.replacement:
                return handler.replacement(self.game, card, {})
        return False

    def check_zone_change_replacement(self, card: 'Card', from_zone, to_zone) -> bool:
        """
        Check for replacement effects on zone change.

        CR (Eternal): Returns to hand instead of graveyard.

        Returns True if zone change was replaced.
        """
        from ..models import Zone

        if to_zone == Zone.GRAVEYARD:
            if self.card_has_keyword(card, Keyword.ETERNAL):
                handler = self.handlers.get(Keyword.ETERNAL)
                if handler and handler.replacement:
                    return handler.replacement(
                        self.game, card, {'zone': to_zone}
                    )
        return False

    def can_play_from_graveyard(self, card: 'Card') -> bool:
        """
        Check if a card can be played from graveyard.

        CR 1115: Remnant allows this.
        """
        return self.card_has_keyword(card, Keyword.REMNANT)

    def is_quickcast(self, card: 'Card') -> bool:
        """Check if a card has Quickcast."""
        return self.card_has_keyword(card, Keyword.QUICKCAST)

    def process_end_of_battle_keywords(self):
        """Process keywords that trigger at end of battle (Explode)."""
        for p in self.game.players:
            for card in list(p.field):
                if getattr(card, '_explode_pending', False):
                    card._explode_pending = False
                    self.game._destroy_card(card)


# Utility functions
def parse_keywords_from_text(text: str) -> Keyword:
    """Parse keyword abilities from card text."""
    keywords = Keyword.NONE

    if not text:
        return keywords

    text_lower = text.lower()

    keyword_map = {
        'pierce': Keyword.PIERCE,
        'precision': Keyword.PRECISION,
        'first strike': Keyword.FIRST_STRIKE,
        'flying': Keyword.FLYING,
        'swiftness': Keyword.SWIFTNESS,
        'explode': Keyword.EXPLODE,
        'drain': Keyword.DRAIN,
        'target attack': Keyword.TARGET_ATTACK,
        'imperishable': Keyword.IMPERISHABLE,
        'barrier': Keyword.BARRIER,
        'stealth': Keyword.STEALTH,
        'quickcast': Keyword.QUICKCAST,
        '[quickcast]': Keyword.QUICKCAST,
        'trigger': Keyword.TRIGGER,
        'awakening': Keyword.AWAKENING,
        'incarnation': Keyword.INCARNATION,
        'remnant': Keyword.REMNANT,
        'eternal': Keyword.ETERNAL,
        'bestow': Keyword.BESTOW,
        'limit break': Keyword.LIMIT_BREAK,
        'providence': Keyword.PROVIDENCE,
    }

    for kw_text, kw_enum in keyword_map.items():
        if kw_text in text_lower:
            keywords |= kw_enum

    return keywords
