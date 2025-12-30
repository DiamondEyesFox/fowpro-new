"""
Token Creation System
=====================

Handles creation of token resonators.
Tokens are non-card game objects with card-like properties.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Set, TYPE_CHECKING
import uuid

from .keywords import Keyword, KeywordState

if TYPE_CHECKING:
    from ..engine import GameEngine
    from ..models import Card


@dataclass
class TokenData:
    """Data for a token type"""
    name: str
    atk: int
    def_: int
    attribute: Optional[str] = None     # WIND, FIRE, WATER, LIGHT, DARKNESS, VOID
    race: Optional[str] = None          # Fairy, Zombie, etc.
    keywords: Keyword = Keyword.NONE
    abilities: List[str] = field(default_factory=list)  # Ability text

    # Art/display
    art_id: Optional[str] = None        # For custom token art


@dataclass
class Token:
    """A token on the battlefield"""
    uid: str
    data: TokenData
    controller: int
    owner: int

    # Combat stats (can be modified)
    current_atk: int = 0
    current_def: int = 0

    # State
    is_rested: bool = False
    entered_field_this_turn: bool = True
    keyword_state: KeywordState = field(default_factory=KeywordState)

    # Counters
    counters: dict = field(default_factory=dict)

    # Zone (always FIELD for tokens that exist)
    zone: str = "FIELD"

    def __post_init__(self):
        self.current_atk = self.data.atk
        self.current_def = self.data.defense
        self.keyword_state.base_keywords = self.data.keywords

    @property
    def is_token(self) -> bool:
        return True

    def take_damage(self, amount: int) -> int:
        """Token takes damage, returns actual damage taken"""
        self.current_def -= amount
        return amount

    def add_counter(self, counter_type: str, count: int = 1):
        """Add counters to token"""
        self.counters[counter_type] = self.counters.get(counter_type, 0) + count

    def remove_counter(self, counter_type: str, count: int = 1) -> int:
        """Remove counters, returns how many were actually removed"""
        have = self.counters.get(counter_type, 0)
        removed = min(have, count)
        self.counters[counter_type] = have - removed
        return removed


class TokenManager:
    """Manages token creation and lifecycle"""

    def __init__(self, game: 'GameEngine'):
        self.game = game
        self._tokens: List[Token] = []

    def create_token(self, controller: int, token_data: TokenData,
                    count: int = 1, rested: bool = False) -> List[Token]:
        """Create token(s) for a player"""
        created = []

        for _ in range(count):
            token = Token(
                uid=f"token_{uuid.uuid4().hex[:8]}",
                data=token_data,
                controller=controller,
                owner=controller,
                is_rested=rested,
            )

            self._tokens.append(token)
            created.append(token)

            # Add to player's field
            self.game.players[controller].field.append(token)

            # Emit creation event
            self.game.emit_event('token_created', {
                'token': token,
                'controller': controller,
            })

        return created

    def destroy_token(self, token: Token):
        """Destroy a token (removes from game entirely)"""
        if token in self._tokens:
            self._tokens.remove(token)

        # Remove from controller's field
        player = self.game.players[token.controller]
        if token in player.field:
            player.field.remove(token)

        self.game.emit_event('token_destroyed', {'token': token})

    def get_tokens_for_player(self, player_index: int) -> List[Token]:
        """Get all tokens controlled by a player"""
        return [t for t in self._tokens if t.controller == player_index]

    def cleanup_dead_tokens(self):
        """Remove tokens with 0 or less DEF"""
        dead = [t for t in self._tokens if t.current_def <= 0]
        for token in dead:
            self.destroy_token(token)

    def on_zone_change(self, token: Token, to_zone: str):
        """Handle token leaving the field"""
        if to_zone != "FIELD":
            # Tokens cease to exist when leaving the field
            self.destroy_token(token)

    def reset_turn_state(self):
        """Reset turn-based state for all tokens"""
        for token in self._tokens:
            token.entered_field_this_turn = False
            token.keyword_state.reset_temporary()


# =============================================================================
# COMMON TOKEN DEFINITIONS
# =============================================================================

# Basic tokens
WOLF_TOKEN = TokenData(
    name="Wolf",
    atk=200,
    def_=200,
    attribute="WIND",
    race="Beast",
)

ZOMBIE_TOKEN = TokenData(
    name="Zombie",
    atk=100,
    def_=100,
    attribute="DARKNESS",
    race="Zombie",
)

FAIRY_TOKEN = TokenData(
    name="Fairy",
    atk=100,
    def_=100,
    attribute="WIND",
    race="Fairy",
    keywords=Keyword.FLYING,
)

KNIGHT_TOKEN = TokenData(
    name="Knight",
    atk=300,
    def_=300,
    attribute="LIGHT",
    race="Human",
)

GOLEM_TOKEN = TokenData(
    name="Golem",
    atk=600,
    def_=600,
    attribute="VOID",
    race="Golem",
)

RABBIT_TOKEN = TokenData(
    name="Rabbit",
    atk=0,
    def_=100,
    attribute="WIND",
    race="Beast",
)

SPIRIT_TOKEN = TokenData(
    name="Spirit",
    atk=200,
    def_=200,
    attribute="LIGHT",
    race="Spirit",
)


# Grimm Cluster specific tokens
RED_RIDING_HOOD_TOKEN = TokenData(
    name="Little Red, the True Fairy Tale",
    atk=400,
    def_=400,
    attribute="FIRE",
    race="Fairy Tale",
    keywords=Keyword.SWIFTNESS,
)

CINDERELLA_TOKEN = TokenData(
    name="Cinderella, the Ashen Maiden",
    atk=400,
    def_=400,
    attribute="LIGHT",
    race="Fairy Tale",
)

SNOW_WHITE_TOKEN = TokenData(
    name="Snow White, the Valkyrie of Passion",
    atk=500,
    def_=500,
    attribute="WATER",
    race="Fairy Tale",
    keywords=Keyword.FIRST_STRIKE,
)


# =============================================================================
# TOKEN CREATION HELPERS
# =============================================================================

def create_wolf_token(game: 'GameEngine', controller: int,
                     count: int = 1) -> List[Token]:
    """Create Wolf token(s)"""
    return game.token_manager.create_token(controller, WOLF_TOKEN, count)


def create_zombie_token(game: 'GameEngine', controller: int,
                       count: int = 1) -> List[Token]:
    """Create Zombie token(s)"""
    return game.token_manager.create_token(controller, ZOMBIE_TOKEN, count)


def create_fairy_token(game: 'GameEngine', controller: int,
                      count: int = 1) -> List[Token]:
    """Create Fairy token(s)"""
    return game.token_manager.create_token(controller, FAIRY_TOKEN, count)


def create_custom_token(game: 'GameEngine', controller: int,
                       name: str, atk: int, def_: int,
                       attribute: str = None,
                       race: str = None,
                       keywords: Keyword = Keyword.NONE,
                       count: int = 1) -> List[Token]:
    """Create custom token(s)"""
    token_data = TokenData(
        name=name,
        atk=atk,
        def_=def_,
        attribute=attribute,
        race=race,
        keywords=keywords,
    )
    return game.token_manager.create_token(controller, token_data, count)
