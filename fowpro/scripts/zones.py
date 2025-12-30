"""
Zone Operations System
======================

Handles zone-related operations:
- Search deck and put into hand/field
- Mill (put top cards into graveyard)
- Look at top X cards
- Reveal cards
- Shuffle deck
- Return cards to deck
- Banish/remove from game
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Callable, Optional, List, Dict, Any, TYPE_CHECKING
import random

if TYPE_CHECKING:
    from ..engine import GameEngine
    from ..models import Card, Player


class SearchDestination(Enum):
    """Where searched cards go"""
    HAND = auto()
    FIELD = auto()
    GRAVEYARD = auto()
    TOP_OF_DECK = auto()
    BOTTOM_OF_DECK = auto()


@dataclass
class SearchFilter:
    """Filter for searchable cards"""
    card_types: Optional[set] = None
    attributes: Optional[set] = None
    max_total_cost: Optional[int] = None
    name_contains: Optional[str] = None
    custom: Optional[Callable[['Card'], bool]] = None

    def matches(self, card: 'Card') -> bool:
        """Check if card matches search criteria"""
        if not card.data:
            return False

        # Card type check
        if self.card_types:
            type_name = card.data.card_type.name.lower()
            if not any(t.lower() in type_name for t in self.card_types):
                return False

        # Attribute check
        if self.attributes:
            if not card.data.attribute:
                return False
            if card.data.attribute.name.upper() not in {a.upper() for a in self.attributes}:
                return False

        # Cost check
        if self.max_total_cost is not None:
            if card.data.get_total_cost() > self.max_total_cost:
                return False

        # Name check
        if self.name_contains:
            if self.name_contains.lower() not in card.data.name.lower():
                return False

        # Custom check
        if self.custom:
            if not self.custom(card):
                return False

        return True


class ZoneOperations:
    """Handles all zone-related operations"""

    def __init__(self, game: 'GameEngine'):
        self.game = game
        self._ui_callback: Optional[Callable] = None
        self._pending_selection: Optional['ZoneSelectionRequest'] = None

    def set_ui_callback(self, callback: Callable):
        """Set UI callback for card selection"""
        self._ui_callback = callback

    # =========================================================================
    # SEARCH OPERATIONS
    # =========================================================================

    def search_deck(self, player: 'Player', filter: SearchFilter,
                   count: int, destination: SearchDestination,
                   reveal: bool = False,
                   callback: Optional[Callable[[List['Card']], None]] = None):
        """Search deck for cards matching filter"""
        from ..models import Zone

        # Find matching cards in deck
        matches = [c for c in player.main_deck if filter.matches(c)]

        if not matches:
            if callback:
                callback([])
            return

        # Request selection from UI
        def on_selected(cards: List['Card']):
            for card in cards:
                if reveal:
                    self.game.emit_event('card_revealed', {
                        'card': card,
                        'player': player.index,
                    })

                # Move to destination
                if destination == SearchDestination.HAND:
                    self.game.move_card(card, Zone.HAND)
                elif destination == SearchDestination.FIELD:
                    self.game.move_card(card, Zone.FIELD)
                elif destination == SearchDestination.GRAVEYARD:
                    self.game.move_card(card, Zone.GRAVEYARD)
                elif destination == SearchDestination.TOP_OF_DECK:
                    player.main_deck.remove(card)
                    player.main_deck.insert(0, card)
                elif destination == SearchDestination.BOTTOM_OF_DECK:
                    player.main_deck.remove(card)
                    player.main_deck.append(card)

            # Shuffle deck after search
            self.shuffle_deck(player)

            if callback:
                callback(cards)

        self._request_selection(
            cards=matches,
            count=count,
            prompt=f"Select up to {count} card(s) from your deck",
            callback=on_selected,
        )

    def search_stone_deck(self, player: 'Player', filter: SearchFilter,
                         destination: SearchDestination = SearchDestination.FIELD,
                         callback: Optional[Callable[['Card'], None]] = None):
        """Search stone deck for a card"""
        from ..models import Zone

        matches = [c for c in player.stone_deck if filter.matches(c)]

        if not matches:
            if callback:
                callback(None)
            return

        def on_selected(cards: List['Card']):
            if cards:
                card = cards[0]
                if destination == SearchDestination.FIELD:
                    self.game.move_card(card, Zone.FIELD)
                    card.is_rested = True  # Stones enter rested
                if callback:
                    callback(card)
            else:
                if callback:
                    callback(None)

        self._request_selection(
            cards=matches,
            count=1,
            prompt="Select a magic stone from your stone deck",
            callback=on_selected,
        )

    # =========================================================================
    # LOOK AT TOP OPERATIONS
    # =========================================================================

    def look_at_top(self, player: 'Player', count: int,
                   callback: Optional[Callable[[List['Card']], None]] = None):
        """Look at top X cards of deck"""
        top_cards = player.main_deck[:count]

        # Reveal to player (not opponent)
        self.game.emit_event('cards_looked_at', {
            'player': player.index,
            'cards': top_cards,
        })

        if callback:
            callback(top_cards)

        return top_cards

    def look_and_rearrange(self, player: 'Player', count: int,
                          put_bottom: int = 0,
                          callback: Optional[Callable[[], None]] = None):
        """Look at top X, put some on bottom, rearrange rest"""
        top_cards = player.main_deck[:count]

        def on_arranged(top_order: List['Card'], bottom: List['Card']):
            # Remove all looked cards from deck
            for card in top_cards:
                if card in player.main_deck:
                    player.main_deck.remove(card)

            # Put selected on bottom
            player.main_deck.extend(bottom)

            # Put rest on top in chosen order
            for card in reversed(top_order):
                player.main_deck.insert(0, card)

            if callback:
                callback()

        # Request arrangement from UI
        self._request_arrangement(
            cards=top_cards,
            put_bottom_count=put_bottom,
            callback=on_arranged,
        )

    # =========================================================================
    # MILL OPERATIONS
    # =========================================================================

    def mill(self, player: 'Player', count: int) -> List['Card']:
        """Put top X cards into graveyard"""
        from ..models import Zone

        milled = []
        for _ in range(min(count, len(player.main_deck))):
            card = player.main_deck[0]
            self.game.move_card(card, Zone.GRAVEYARD)
            milled.append(card)

            self.game.emit_event('card_milled', {
                'card': card,
                'player': player.index,
            })

        return milled

    # =========================================================================
    # RETURN OPERATIONS
    # =========================================================================

    def return_to_hand(self, card: 'Card'):
        """Return a card to owner's hand"""
        from ..models import Zone
        self.game.move_card(card, Zone.HAND)
        self.game.emit_event('card_returned_to_hand', {'card': card})

    def return_to_deck_top(self, card: 'Card'):
        """Return card to top of owner's deck"""
        from ..models import Zone
        owner = self.game.players[card.owner]

        if card.zone != Zone.MAIN_DECK:
            # Remove from current zone
            self.game.move_card(card, Zone.MAIN_DECK)

        # Move to top
        owner.main_deck.remove(card)
        owner.main_deck.insert(0, card)

    def return_to_deck_bottom(self, card: 'Card'):
        """Return card to bottom of owner's deck"""
        from ..models import Zone
        owner = self.game.players[card.owner]

        if card.zone != Zone.MAIN_DECK:
            self.game.move_card(card, Zone.MAIN_DECK)

        # Move to bottom
        owner.main_deck.remove(card)
        owner.main_deck.append(card)

    def shuffle_into_deck(self, card: 'Card'):
        """Shuffle card into owner's deck"""
        from ..models import Zone
        owner = self.game.players[card.owner]
        self.game.move_card(card, Zone.MAIN_DECK)
        self.shuffle_deck(owner)

    # =========================================================================
    # GRAVEYARD OPERATIONS
    # =========================================================================

    def banish(self, card: 'Card'):
        """Remove card from game (exile)"""
        from ..models import Zone
        self.game.move_card(card, Zone.REMOVED)
        self.game.emit_event('card_banished', {'card': card})

    def recover_from_graveyard(self, player: 'Player', filter: SearchFilter,
                               destination: SearchDestination = SearchDestination.HAND,
                               callback: Optional[Callable[['Card'], None]] = None):
        """Return a card from graveyard"""
        from ..models import Zone

        matches = [c for c in player.graveyard if filter.matches(c)]

        if not matches:
            if callback:
                callback(None)
            return

        def on_selected(cards: List['Card']):
            if cards:
                card = cards[0]
                if destination == SearchDestination.HAND:
                    self.game.move_card(card, Zone.HAND)
                elif destination == SearchDestination.FIELD:
                    self.game.move_card(card, Zone.FIELD)
                elif destination == SearchDestination.TOP_OF_DECK:
                    self.return_to_deck_top(card)

                if callback:
                    callback(card)
            else:
                if callback:
                    callback(None)

        self._request_selection(
            cards=matches,
            count=1,
            prompt="Select a card from your graveyard",
            callback=on_selected,
        )

    # =========================================================================
    # SHUFFLE OPERATIONS
    # =========================================================================

    def shuffle_deck(self, player: 'Player'):
        """Shuffle player's main deck"""
        random.shuffle(player.main_deck)
        self.game.emit_event('deck_shuffled', {'player': player.index})

    def shuffle_stone_deck(self, player: 'Player'):
        """Shuffle player's stone deck"""
        random.shuffle(player.stone_deck)

    # =========================================================================
    # REVEAL OPERATIONS
    # =========================================================================

    def reveal_hand(self, player: 'Player'):
        """Reveal player's hand to opponent"""
        self.game.emit_event('hand_revealed', {
            'player': player.index,
            'cards': list(player.hand),
        })

    def reveal_top_of_deck(self, player: 'Player', count: int = 1) -> List['Card']:
        """Reveal top cards of deck"""
        top = player.main_deck[:count]
        self.game.emit_event('cards_revealed', {
            'player': player.index,
            'cards': top,
            'source': 'deck',
        })
        return top

    # =========================================================================
    # DRAW OPERATIONS
    # =========================================================================

    def draw_cards(self, player: 'Player', count: int) -> List['Card']:
        """Draw cards from deck"""
        from ..models import Zone

        drawn = []
        for _ in range(count):
            if not player.main_deck:
                # Deck out - game loss
                self.game.emit_event('deck_out', {'player': player.index})
                break

            card = player.main_deck[0]
            self.game.move_card(card, Zone.HAND)
            drawn.append(card)

            self.game.emit_event('card_drawn', {
                'card': card,
                'player': player.index,
            })

        return drawn

    # =========================================================================
    # DISCARD OPERATIONS
    # =========================================================================

    def discard(self, card: 'Card'):
        """Discard a card"""
        from ..models import Zone
        self.game.move_card(card, Zone.GRAVEYARD)
        self.game.emit_event('card_discarded', {'card': card})

    def discard_random(self, player: 'Player', count: int = 1) -> List['Card']:
        """Randomly discard cards"""
        discarded = []
        hand = list(player.hand)

        for _ in range(min(count, len(hand))):
            card = random.choice(hand)
            hand.remove(card)
            self.discard(card)
            discarded.append(card)

        return discarded

    def discard_choice(self, player: 'Player', count: int,
                      callback: Optional[Callable[[List['Card']], None]] = None):
        """Player chooses cards to discard"""
        if len(player.hand) <= count:
            # Must discard all
            discarded = list(player.hand)
            for card in discarded:
                self.discard(card)
            if callback:
                callback(discarded)
            return

        def on_selected(cards: List['Card']):
            for card in cards:
                self.discard(card)
            if callback:
                callback(cards)

        self._request_selection(
            cards=list(player.hand),
            count=count,
            prompt=f"Discard {count} card(s)",
            callback=on_selected,
        )

    # =========================================================================
    # UI HELPERS
    # =========================================================================

    def _request_selection(self, cards: List['Card'], count: int,
                          prompt: str,
                          callback: Callable[[List['Card']], None]):
        """Request card selection from UI"""
        if self._ui_callback:
            self._pending_selection = ZoneSelectionRequest(
                cards=cards,
                count=count,
                prompt=prompt,
                callback=callback,
            )
            self._ui_callback(self._pending_selection)
        else:
            # Auto-select first N
            callback(cards[:count])

    def _request_arrangement(self, cards: List['Card'], put_bottom_count: int,
                            callback: Callable[[List['Card'], List['Card']], None]):
        """Request card arrangement from UI"""
        if self._ui_callback:
            # UI handles complex arrangement
            pass
        else:
            # Auto: put last N on bottom, keep rest on top in order
            top = cards[:-put_bottom_count] if put_bottom_count > 0 else cards
            bottom = cards[-put_bottom_count:] if put_bottom_count > 0 else []
            callback(top, bottom)

    def submit_selection(self, card_ids: List[str]):
        """Called by UI when player selects cards"""
        if not self._pending_selection:
            return

        req = self._pending_selection
        self._pending_selection = None

        selected = []
        for cid in card_ids:
            for card in req.cards:
                if card.uid == cid:
                    selected.append(card)
                    break

        req.callback(selected[:req.count])


@dataclass
class ZoneSelectionRequest:
    """Request for UI to show zone selection"""
    cards: List['Card']
    count: int
    prompt: str
    callback: Callable[[List['Card']], None]


# =============================================================================
# SEARCH FILTER BUILDERS
# =============================================================================

def any_resonator() -> SearchFilter:
    """Match any resonator"""
    return SearchFilter(card_types={'resonator'})


def any_spell() -> SearchFilter:
    """Match any spell"""
    return SearchFilter(card_types={'spell'})


def resonator_with_cost(max_cost: int) -> SearchFilter:
    """Resonator with total cost <= X"""
    return SearchFilter(
        card_types={'resonator'},
        max_total_cost=max_cost,
    )


def resonator_with_attribute(attribute: str) -> SearchFilter:
    """Resonator with specific attribute"""
    return SearchFilter(
        card_types={'resonator'},
        attributes={attribute.upper()},
    )


def card_named(name: str) -> SearchFilter:
    """Card with exact name"""
    return SearchFilter(name_contains=name)


def any_card() -> SearchFilter:
    """Match any card"""
    return SearchFilter()
