"""
Effect Primitives
=================

Reusable effect functions that card scripts can call.
Like YGOPro's Duel.Draw(), Duel.Destroy(), etc.

These functions integrate with the CR-compliant rules systems when available,
including replacement effects, keyword handling, and choice management.
"""

from typing import List, Optional, Callable, TYPE_CHECKING
from dataclasses import dataclass

if TYPE_CHECKING:
    from ..engine import GameEngine
    from ..models import Card, Attribute, Zone


def _get_rules_engine(game: 'GameEngine'):
    """Get the RulesEngine wrapper if available."""
    if hasattr(game, '_rules_engine'):
        return game._rules_engine
    return None


# =============================================================================
# WILL / MANA EFFECTS
# =============================================================================

def produce_will(game: 'GameEngine', player: int, attribute: 'Attribute', amount: int = 1):
    """Add will to a player's pool"""
    game.players[player].will_pool.add(attribute, amount)


def pay_will(game: 'GameEngine', player: int, attribute: 'Attribute', amount: int = 1) -> bool:
    """Remove will from a player's pool. Returns False if not enough."""
    pool = game.players[player].will_pool
    if pool.get(attribute) >= amount:
        pool.remove(attribute, amount)
        return True
    return False


# =============================================================================
# CARD DRAWING
# =============================================================================

def draw_cards(game: 'GameEngine', player: int, count: int = 1) -> List['Card']:
    """Draw cards from deck. Returns list of drawn cards."""
    return game.draw_cards(player, count)


def can_draw(game: 'GameEngine', player: int, count: int = 1) -> bool:
    """Check if player can draw the specified number of cards."""
    return len(game.players[player].main_deck) >= count


# =============================================================================
# CARD STATE CHANGES
# =============================================================================

def rest_card(game: 'GameEngine', card: 'Card'):
    """Rest (tap) a card"""
    card.rest()


def recover_card(game: 'GameEngine', card: 'Card'):
    """Recover (untap) a card"""
    card.recover()


def destroy_card(game: 'GameEngine', card: 'Card', cause: str = "") -> bool:
    """Destroy a card (move to graveyard).

    Checks replacement effects (CR 910) before destroying.
    Returns True if actually destroyed, False if replaced.
    """
    from ..models import Zone

    # Check rules engine for replacement effects
    rules = _get_rules_engine(game)
    if rules:
        should_destroy, reason = rules.would_destroy(card, cause)
        if not should_destroy:
            return False

    game.move_card(card, Zone.GRAVEYARD)
    return True


def banish_card(game: 'GameEngine', card: 'Card'):
    """Banish a card (remove from game)"""
    from ..models import Zone
    game.move_card(card, Zone.REMOVED)


def return_to_hand(game: 'GameEngine', card: 'Card'):
    """Return a card to its owner's hand"""
    from ..models import Zone
    game.move_card(card, Zone.HAND, card.owner)


def return_to_deck(game: 'GameEngine', card: 'Card', position: str = 'top'):
    """Return card to owner's deck (top or bottom)"""
    from ..models import Zone
    p = game.players[card.owner]
    # Remove from current zone first
    game.move_card(card, Zone.MAIN_DECK, card.owner)
    # Reposition in deck
    if card in p.main_deck:
        p.main_deck.remove(card)
        if position == 'top':
            p.main_deck.insert(0, card)
        else:
            p.main_deck.append(card)


# =============================================================================
# STAT MODIFICATIONS
# =============================================================================

@dataclass
class StatMod:
    """Temporary stat modification"""
    card: 'Card'
    atk_mod: int = 0
    def_mod: int = 0
    until_eot: bool = True


def buff_card(game: 'GameEngine', card: 'Card', atk: int = 0, defense: int = 0,
              until_eot: bool = True) -> StatMod:
    """Give a card +ATK/+DEF"""
    card.atk_mod += atk
    card.def_mod += defense

    mod = StatMod(card, atk, defense, until_eot)

    if until_eot:
        # Register cleanup at end of turn
        game.register_eot_effect(lambda: remove_buff(card, atk, defense))

    return mod


def remove_buff(card: 'Card', atk: int, defense: int):
    """Remove a buff from a card"""
    card.atk_mod -= atk
    card.def_mod -= defense


def set_stats(game: 'GameEngine', card: 'Card', atk: int, defense: int):
    """Set card's ATK/DEF to specific values"""
    # Calculate the modification needed
    current_atk = card.data.atk + card.atk_mod
    current_def = card.data.defense + card.def_mod
    card.atk_mod = atk - card.data.atk
    card.def_mod = defense - card.data.defense


# =============================================================================
# DAMAGE AND LIFE
# =============================================================================

def deal_damage(game: 'GameEngine', source: 'Card', target: 'Card', amount: int,
                is_combat: bool = False) -> int:
    """Deal damage to a J/resonator.

    Checks replacement effects (CR 910) for damage prevention/modification.
    Returns the actual damage dealt.
    """
    # Check rules engine for replacement effects
    rules = _get_rules_engine(game)
    if rules:
        final_amount, was_modified = rules.would_deal_damage(source, target, amount, is_combat)
        amount = final_amount

    if amount <= 0:
        return 0

    target.damage += amount

    # Emit event if method exists
    if hasattr(game, 'emit_damage'):
        game.emit_damage(source, target, amount)

    # Handle keyword effects (Drain, Pierce, etc.)
    if rules:
        rules.on_deals_damage(source, target, amount, is_combat)

    # Check for destruction
    current_def = target.data.defense + getattr(target, 'def_mod', 0)
    if target.damage >= current_def:
        destroy_card(game, target, "lethal damage")

    return amount


def deal_damage_to_player(game: 'GameEngine', source: 'Card', player: int, amount: int):
    """Deal damage to a player"""
    game.players[player].life -= amount
    game.emit_player_damage(source, player, amount)


def gain_life(game: 'GameEngine', player: int, amount: int):
    """Player gains life"""
    game.players[player].life += amount


def lose_life(game: 'GameEngine', player: int, amount: int):
    """Player loses life (not damage)"""
    game.players[player].life -= amount


# =============================================================================
# KEYWORD MANIPULATION
# =============================================================================

def grant_keyword(game: 'GameEngine', card: 'Card', keyword: 'Keyword',
                  until_eot: bool = True):
    """Grant a keyword to a card"""
    from ..models import Keyword
    card.granted_keywords |= keyword

    if until_eot:
        game.register_eot_effect(lambda: remove_keyword(card, keyword))


def remove_keyword(card: 'Card', keyword: 'Keyword'):
    """Remove a granted keyword"""
    card.granted_keywords &= ~keyword


def remove_all_keywords(card: 'Card'):
    """Remove all keywords from a card"""
    from ..models import Keyword
    card.removed_keywords = Keyword.ALL


# =============================================================================
# SEARCHING AND FILTERING
# =============================================================================

def search_deck(game: 'GameEngine', player: int,
                filter_fn: Callable[['Card'], bool] = None) -> List['Card']:
    """Search player's deck for cards matching filter"""
    deck = game.players[player].main_deck
    if filter_fn:
        return [c for c in deck if filter_fn(c)]
    return list(deck)


def search_graveyard(game: 'GameEngine', player: int,
                     filter_fn: Callable[['Card'], bool] = None) -> List['Card']:
    """Search player's graveyard for cards matching filter"""
    grave = game.players[player].graveyard
    if filter_fn:
        return [c for c in grave if filter_fn(c)]
    return list(grave)


def get_field_cards(game: 'GameEngine', player: int,
                    filter_fn: Callable[['Card'], bool] = None) -> List['Card']:
    """Get cards on player's field matching filter"""
    field = game.players[player].field
    if filter_fn:
        return [c for c in field if filter_fn(c)]
    return list(field)


# =============================================================================
# TARGETING HELPERS
# =============================================================================

class TargetType:
    """Common target type filters"""
    RESONATOR = lambda c: c.data.is_resonator()
    J_RESONATOR = lambda c: c.data.is_resonator() or c.data.card_type.name == 'J_RULER'
    SPELL = lambda c: c.data.is_spell()
    ADDITION = lambda c: 'ADDITION' in c.data.card_type.name
    STONE = lambda c: c.data.is_stone()
    ANY = lambda c: True


def is_valid_target(card: 'Card', source: 'Card' = None, source_controller: int = None) -> bool:
    """Check if a card can be targeted.

    Uses the KeywordManager (CR 1120) to check Barrier and other restrictions.
    """
    from ..models import Keyword

    # If we have a source, use rules engine for proper keyword checks
    if source:
        # Get the game engine from the source card's context
        game = getattr(source, '_game', None)
        if game:
            rules = _get_rules_engine(game)
            if rules:
                controller = source_controller if source_controller is not None else source.controller
                return rules.check_targeting_allowed(source, card, controller)

    # Fallback to simple keyword check
    if card.has_keyword(Keyword.BARRIER):
        # Barrier prevents opponent targeting
        if source and source.controller != card.controller:
            return False

    return True


def get_valid_targets(game: 'GameEngine', player: int,
                      zone: 'Zone', filter_fn: Callable[['Card'], bool] = None,
                      include_opponent: bool = True) -> List['Card']:
    """Get all valid targets in a zone"""
    targets = []

    # Own cards
    own_zone = game.players[player].get_zone(zone)
    targets.extend([c for c in own_zone if is_valid_target(c)])

    # Opponent's cards
    if include_opponent:
        opp = 1 - player
        opp_zone = game.players[opp].get_zone(zone)
        targets.extend([c for c in opp_zone if is_valid_target(c)])

    if filter_fn:
        targets = [c for c in targets if filter_fn(c)]

    return targets


def get_resonators_on_field(game: 'GameEngine', player: int = None,
                            include_j_rulers: bool = True) -> List['Card']:
    """Get all resonators/J-rulers on the field"""
    from ..models import CardType
    targets = []

    players_to_check = [player] if player is not None else [0, 1]

    for p_idx in players_to_check:
        for card in game.players[p_idx].field:
            if card.data.is_resonator():
                if is_valid_target(card):
                    targets.append(card)
            elif include_j_rulers and card.data.card_type == CardType.J_RULER:
                if is_valid_target(card):
                    targets.append(card)

    return targets


def get_spells_on_chase(game: 'GameEngine') -> List['Card']:
    """Get all spells on the chase (for counter effects)"""
    spells = []
    for item in game.chase:
        if item.item_type == "SPELL":
            spells.append(item.source)
    return spells


def require_target(game: 'GameEngine', player: int, target_type: Callable,
                   prompt: str = "Choose a target") -> Optional['Card']:
    """Helper for effects that need to select a target.

    In an actual implementation, this would interact with the UI.
    For now, returns None to indicate target selection is needed.
    """
    from ..models import Zone
    targets = get_valid_targets(game, player, Zone.FIELD, target_type)
    if not targets:
        return None
    # Return first valid target for AI/testing; real UI would prompt
    return targets[0] if targets else None


# =============================================================================
# SPECIAL SUMMON / PLAY
# =============================================================================

def special_summon(game: 'GameEngine', card: 'Card', player: int):
    """Special summon a card to the field (bypassing normal play)"""
    from ..models import Zone
    game.move_card(card, Zone.FIELD, player)
    card.controller = player


def put_into_play(game: 'GameEngine', card: 'Card', player: int, rested: bool = False):
    """Put a card directly into play"""
    from ..models import Zone
    game.move_card(card, Zone.FIELD, player)
    card.controller = player
    if rested:
        card.rest()


# =============================================================================
# COUNTERS (for cards that use counters)
# =============================================================================

def add_counter(card: 'Card', counter_type: str, amount: int = 1):
    """Add counters to a card"""
    if not hasattr(card, 'counters'):
        card.counters = {}
    if counter_type not in card.counters:
        card.counters[counter_type] = 0
    card.counters[counter_type] += amount


def remove_counter(card: 'Card', counter_type: str, amount: int = 1) -> bool:
    """Remove counters from a card. Returns False if not enough."""
    if not hasattr(card, 'counters') or counter_type not in card.counters:
        return False
    if card.counters[counter_type] < amount:
        return False
    card.counters[counter_type] -= amount
    return True


def get_counters(card: 'Card', counter_type: str) -> int:
    """Get number of counters on a card"""
    if not hasattr(card, 'counters') or counter_type not in card.counters:
        return 0
    return card.counters[counter_type]


# =============================================================================
# CHASE / STACK MANIPULATION
# =============================================================================

def cancel_spell(game: 'GameEngine', chase_index: int = 0) -> bool:
    """Cancel a spell on the chase"""
    if chase_index < len(game.chase):
        item = game.chase[chase_index]
        # Move the card to graveyard without resolving
        from ..models import Zone
        game.move_card(item.card, Zone.GRAVEYARD)
        game.chase.pop(chase_index)
        return True
    return False


# =============================================================================
# TARGETING CONVENIENCE FUNCTIONS
# =============================================================================

def target_resonator(game: 'GameEngine', source: 'Card', controller: str = 'any') -> Optional['Card']:
    """
    Get a target resonator. Returns first valid target (AI behavior).

    Args:
        game: Game engine
        source: Source card (for controller reference)
        controller: 'you', 'opponent', or 'any'
    """
    player = source.controller
    targets = []

    if controller in ('you', 'any'):
        for card in game.players[player].field:
            if card.data.is_resonator() and is_valid_target(card, source):
                targets.append(card)

    if controller in ('opponent', 'any'):
        opp = 1 - player
        for card in game.players[opp].field:
            if card.data.is_resonator() and is_valid_target(card, source):
                targets.append(card)

    return targets[0] if targets else None


def target_j_resonator(game: 'GameEngine', source: 'Card', controller: str = 'any') -> Optional['Card']:
    """Get a target J/resonator (J-ruler or resonator)."""
    from ..models import CardType
    player = source.controller
    targets = []

    if controller in ('you', 'any'):
        for card in game.players[player].field:
            if (card.data.is_resonator() or card.data.card_type == CardType.J_RULER) and is_valid_target(card, source):
                targets.append(card)

    if controller in ('opponent', 'any'):
        opp = 1 - player
        for card in game.players[opp].field:
            if (card.data.is_resonator() or card.data.card_type == CardType.J_RULER) and is_valid_target(card, source):
                targets.append(card)

    return targets[0] if targets else None


def target_addition(game: 'GameEngine', source: 'Card', controller: str = 'any') -> Optional['Card']:
    """Get a target addition."""
    player = source.controller
    targets = []

    if controller in ('you', 'any'):
        for card in game.players[player].field:
            if card.data.is_addition() and is_valid_target(card, source):
                targets.append(card)

    if controller in ('opponent', 'any'):
        opp = 1 - player
        for card in game.players[opp].field:
            if card.data.is_addition() and is_valid_target(card, source):
                targets.append(card)

    return targets[0] if targets else None


def target_stone(game: 'GameEngine', source: 'Card', controller: str = 'any', special_only: bool = False) -> Optional['Card']:
    """Get a target magic stone."""
    player = source.controller
    targets = []

    if controller in ('you', 'any'):
        for card in game.players[player].stone_zone:
            if card.data.is_stone():
                if not special_only or card.data.is_special_stone():
                    if is_valid_target(card, source):
                        targets.append(card)

    if controller in ('opponent', 'any'):
        opp = 1 - player
        for card in game.players[opp].stone_zone:
            if card.data.is_stone():
                if not special_only or card.data.is_special_stone():
                    if is_valid_target(card, source):
                        targets.append(card)

    return targets[0] if targets else None


def target_card_on_chase(game: 'GameEngine', source: 'Card') -> Optional['Card']:
    """Get a target spell/ability on the chase."""
    if game.chase:
        # Return the top item on chase
        item = game.chase[-1]
        if hasattr(item, 'card'):
            return item.card
    return None


def target_card_in_graveyard(game: 'GameEngine', source: 'Card',
                              controller: str = 'any',
                              filter_fn: Callable[['Card'], bool] = None) -> Optional['Card']:
    """Get a target card in graveyard."""
    player = source.controller
    targets = []

    if controller in ('you', 'any'):
        for card in game.players[player].graveyard:
            if filter_fn is None or filter_fn(card):
                targets.append(card)

    if controller in ('opponent', 'any'):
        opp = 1 - player
        for card in game.players[opp].graveyard:
            if filter_fn is None or filter_fn(card):
                targets.append(card)

    return targets[0] if targets else None


# =============================================================================
# EFFECT EXECUTION WITH TARGETING
# =============================================================================

def destroy_target_resonator(game: 'GameEngine', source: 'Card', controller: str = 'any') -> bool:
    """Destroy target resonator."""
    target = target_resonator(game, source, controller)
    if target:
        destroy_card(game, target)
        return True
    return False


def destroy_target_addition(game: 'GameEngine', source: 'Card', controller: str = 'any') -> bool:
    """Destroy target addition."""
    target = target_addition(game, source, controller)
    if target:
        destroy_card(game, target)
        return True
    return False


def destroy_target_j_resonator(game: 'GameEngine', source: 'Card', controller: str = 'any') -> bool:
    """Destroy target J/resonator."""
    target = target_j_resonator(game, source, controller)
    if target:
        destroy_card(game, target)
        return True
    return False


def destroy_target_stone(game: 'GameEngine', source: 'Card', controller: str = 'any', special_only: bool = False) -> bool:
    """Destroy target magic stone."""
    target = target_stone(game, source, controller, special_only)
    if target:
        destroy_card(game, target)
        return True
    return False


def bounce_target_resonator(game: 'GameEngine', source: 'Card', controller: str = 'any') -> bool:
    """Return target resonator to owner's hand."""
    target = target_resonator(game, source, controller)
    if target:
        return_to_hand(game, target)
        return True
    return False


def bounce_target_addition(game: 'GameEngine', source: 'Card', controller: str = 'any') -> bool:
    """Return target addition to owner's hand."""
    target = target_addition(game, source, controller)
    if target:
        return_to_hand(game, target)
        return True
    return False


def rest_target_resonator(game: 'GameEngine', source: 'Card', controller: str = 'any') -> bool:
    """Rest target resonator."""
    target = target_resonator(game, source, controller)
    if target:
        rest_card(game, target)
        return True
    return False


def rest_target_j_resonator(game: 'GameEngine', source: 'Card', controller: str = 'any') -> bool:
    """Rest target J/resonator."""
    target = target_j_resonator(game, source, controller)
    if target:
        rest_card(game, target)
        return True
    return False


def recover_target_resonator(game: 'GameEngine', source: 'Card', controller: str = 'any') -> bool:
    """Recover target resonator."""
    target = target_resonator(game, source, controller)
    if target:
        recover_card(game, target)
        return True
    return False


def banish_target_resonator(game: 'GameEngine', source: 'Card', controller: str = 'any') -> bool:
    """Banish target resonator (remove from game)."""
    target = target_resonator(game, source, controller)
    if target:
        banish_card(game, target)
        return True
    return False


def cancel_target_spell(game: 'GameEngine', source: 'Card') -> bool:
    """Cancel target spell on the chase."""
    if game.chase:
        return cancel_spell(game, len(game.chase) - 1)
    return False


def buff_target_resonator(game: 'GameEngine', source: 'Card', atk: int, defense: int,
                          controller: str = 'any') -> bool:
    """Give target resonator +ATK/+DEF until end of turn."""
    target = target_resonator(game, source, controller)
    if target:
        buff_card(game, target, atk, defense, until_eot=True)
        return True
    return False


def deal_damage_to_target(game: 'GameEngine', source: 'Card', amount: int,
                          controller: str = 'any') -> bool:
    """Deal damage to target J/resonator."""
    target = target_j_resonator(game, source, controller)
    if target:
        deal_damage(game, source, target, amount)
        return True
    return False


def put_from_graveyard_to_hand(game: 'GameEngine', source: 'Card',
                                filter_fn: Callable[['Card'], bool] = None) -> bool:
    """Put target card from your graveyard into your hand."""
    target = target_card_in_graveyard(game, source, 'you', filter_fn)
    if target:
        from ..models import Zone
        game.move_card(target, Zone.HAND, source.controller)
        return True
    return False


def search_deck_to_hand(game: 'GameEngine', source: 'Card',
                        filter_fn: Callable[['Card'], bool] = None) -> bool:
    """Search your deck for a card and put it into your hand, then shuffle."""
    player = source.controller
    deck = game.players[player].main_deck

    # Find matching cards
    matches = [c for c in deck if filter_fn is None or filter_fn(c)]

    if matches:
        target = matches[0]  # AI picks first match
        from ..models import Zone
        game.move_card(target, Zone.HAND, player)
        game.shuffle_deck(player)
        return True
    return False


def search_deck_to_field(game: 'GameEngine', source: 'Card',
                         filter_fn: Callable[['Card'], bool] = None) -> bool:
    """Search your deck for a card and put it into the field, then shuffle."""
    player = source.controller
    deck = game.players[player].main_deck

    # Find matching cards
    matches = [c for c in deck if filter_fn is None or filter_fn(c)]

    if matches:
        target = matches[0]  # AI picks first match
        special_summon(game, target, player)
        game.shuffle_deck(player)
        return True
    return False


def put_counters_on(game: 'GameEngine', card: 'Card', counter_type: str, amount: int = 1) -> bool:
    """Put counters on a card."""
    if not hasattr(card, 'counters'):
        card.counters = {}
    if counter_type not in card.counters:
        card.counters[counter_type] = 0
    card.counters[counter_type] += amount
    return True


def remove_counters_from(game: 'GameEngine', card: 'Card', counter_type: str, amount: int = 1) -> bool:
    """Remove counters from a card. Returns False if not enough counters."""
    if not hasattr(card, 'counters') or counter_type not in card.counters:
        return False
    if card.counters[counter_type] < amount:
        return False
    card.counters[counter_type] -= amount
    return True


def get_counter_count(card: 'Card', counter_type: str) -> int:
    """Get the number of counters of a specific type on a card."""
    if not hasattr(card, 'counters') or counter_type not in card.counters:
        return 0
    return card.counters[counter_type]


def trigger_on_attack(game: 'GameEngine', source: 'Card', effect_fn: Callable) -> None:
    """Register an effect to trigger when this card attacks."""
    if not hasattr(source, 'attack_triggers'):
        source.attack_triggers = []
    source.attack_triggers.append(effect_fn)


def trigger_on_block(game: 'GameEngine', source: 'Card', effect_fn: Callable) -> None:
    """Register an effect to trigger when this card blocks."""
    if not hasattr(source, 'block_triggers'):
        source.block_triggers = []
    source.block_triggers.append(effect_fn)


def put_from_graveyard_to_field(game: 'GameEngine', source: 'Card',
                                 filter_fn: Callable[['Card'], bool] = None) -> bool:
    """Put target card from your graveyard into the field."""
    target = target_card_in_graveyard(game, source, 'you', filter_fn)
    if target:
        special_summon(game, target, source.controller)
        return True
    return False


def grant_keyword_until_eot(game: 'GameEngine', card: 'Card', keyword: str) -> None:
    """Grant a keyword to a card until end of turn."""
    from ..models import Keyword
    keyword_enum = getattr(Keyword, keyword.upper().replace(' ', '_'), None)
    if keyword_enum:
        if not hasattr(card, 'temp_keywords'):
            card.temp_keywords = []
        card.temp_keywords.append(keyword_enum)


def grant_keyword_choice_until_eot(game: 'GameEngine', card: 'Card', keywords: list) -> None:
    """Grant one of several keywords to a card until end of turn (AI picks first)."""
    if keywords:
        grant_keyword_until_eot(game, card, keywords[0])
