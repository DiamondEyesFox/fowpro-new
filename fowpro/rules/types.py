"""
Core types and enums based on the Force of Will Comprehensive Rules.

References:
- CR 901: Ability and Effect types
- CR 906: Automatic Abilities (triggers)
- CR 1000+: Action by Rules
- CR 1100+: Keywords and Keyword Abilities
"""

from enum import Enum, Flag, auto
from typing import Optional


class AbilityType(Enum):
    """
    Types of abilities per CR 901.

    CR 901.1: An ability is a text written on a card that makes effects of the game.
    """
    # CR 904: Continuous Ability - applies effects as long as active
    CONTINUOUS = "continuous"

    # CR 905: Activate Ability - controller may play at any time they can
    ACTIVATE = "activate"

    # CR 906: Automatic Ability - watches game, plays when condition met
    AUTOMATIC = "automatic"

    # CR 907: Will Ability - special fast abilities that produce will
    WILL = "will"

    # Keyword abilities that define behavior
    KEYWORD = "keyword"


class EffectTiming(Enum):
    """
    When an effect can be played.

    CR 701.2: "main timing" = turn player has priority, main phase,
              not in battle, chase area empty.
    """
    # Can only be played at main timing
    MAIN_TIMING = "main_timing"

    # Can be played whenever you have priority (CR 604.1)
    INSTANT = "instant"

    # Resolves immediately, doesn't use chase (CR 907.3)
    WILL_SPEED = "will_speed"


class TriggerCondition(Enum):
    """
    Trigger conditions for automatic abilities per CR 906.

    CR 906.4: Each automatic object has its own condition to play it.
    """
    # Zone movement triggers (CR 702.3e, 906.7)
    ENTER_FIELD = "enter_field"              # [Enter] - when enters field
    LEAVE_FIELD = "leave_field"              # When leaves field
    PUT_INTO_GRAVEYARD = "put_into_graveyard"
    REMOVED_FROM_GAME = "removed_from_game"

    # Phase triggers (CR 502-505)
    BEGINNING_OF_GAME = "beginning_of_game"  # CR 502.1 - first draw phase
    BEGINNING_OF_TURN = "beginning_of_turn"  # CR 502.2
    BEGINNING_OF_DRAW = "beginning_of_draw"  # CR 502.2
    BEGINNING_OF_RECOVERY = "beginning_of_recovery"  # CR 503.2
    BEGINNING_OF_MAIN = "beginning_of_main"  # CR 504.1
    BEGINNING_OF_END = "beginning_of_end"    # CR 505.1
    END_OF_TURN = "end_of_turn"              # CR 505.3

    # Battle triggers (CR 800)
    BEGINNING_OF_BATTLE = "beginning_of_battle"  # CR 802.1
    BEGINNING_OF_ATTACK_STEP = "beginning_of_attack_step"  # CR 803.1
    DECLARES_ATTACK = "declares_attack"      # When a J/resonator attacks
    DECLARES_BLOCK = "declares_block"        # When a J/resonator blocks
    BLOCKED = "blocked"                      # When attacking J/resonator is blocked
    NOT_BLOCKED = "not_blocked"              # When attack goes unblocked

    # Damage triggers (CR 1007)
    DEALS_DAMAGE = "deals_damage"            # Any damage
    DEALS_BATTLE_DAMAGE = "deals_battle_damage"  # Battle damage only
    IS_DEALT_DAMAGE = "is_dealt_damage"      # When this is dealt damage

    # State change triggers
    RESTED = "rested"                        # When this rests
    RECOVERED = "recovered"                  # When this recovers
    DESTROYED = "destroyed"                  # When destroyed (CR 1010)
    BANISHED = "banished"                    # When banished (CR 1011)

    # Counter triggers (CR 1022)
    GAINS_COUNTER = "gains_counter"
    LOSES_COUNTER = "loses_counter"

    # Life triggers
    GAINS_LIFE = "gains_life"                # When player gains life
    LOSES_LIFE = "loses_life"                # When player loses life

    # Generic turn triggers
    TURN_START = "turn_start"                # At start of any turn
    TURN_END = "turn_end"                    # At end of any turn

    # Spell/ability triggers
    SPELL_PLAYED = "spell_played"            # When a spell is played
    ABILITY_PLAYED = "ability_played"        # When an ability is played
    SPELL_RESOLVES = "spell_resolves"        # When a spell resolves

    # Judgment trigger
    JUDGMENT_PERFORMED = "judgment_performed"  # CR 705.3a-1


class TriggerTiming(Enum):
    """
    When a triggered ability goes on the chase.

    CR 906.5: During priority sequence, after rule processes,
    turn player checks for triggered automatic objects.
    """
    # Goes on chase, can be responded to
    CHASE = "chase"

    # Resolves immediately (like [Enter] in some contexts)
    IMMEDIATE = "immediate"


class EffectAction(Enum):
    """
    Actions that effects can perform, per CR 1000+.
    """
    # Damage (CR 1007)
    DEAL_DAMAGE = "deal_damage"
    REMOVE_DAMAGE = "remove_damage"

    # Zone movement
    DESTROY = "destroy"          # CR 1010
    BANISH = "banish"            # CR 1011
    CANCEL = "cancel"            # CR 1012
    REMOVE_FROM_GAME = "remove_from_game"  # CR 1004
    RETURN_TO_HAND = "return_to_hand"
    PUT_INTO_FIELD = "put_into_field"
    PUT_INTO_GRAVEYARD = "put_into_graveyard"
    PUT_ON_TOP_OF_DECK = "put_on_top_of_deck"
    PUT_ON_BOTTOM_OF_DECK = "put_on_bottom_of_deck"
    SHUFFLE_INTO_DECK = "shuffle_into_deck"

    # Card operations (CR 1009, 1014, 1019)
    DRAW = "draw"                # CR 1009
    DISCARD = "discard"          # CR 1019
    SEARCH = "search"            # CR 1014
    REVEAL = "reveal"            # CR 1005
    LOOK = "look"                # Look at cards without revealing

    # Life (CR 105.4)
    GAIN_LIFE = "gain_life"
    LOSE_LIFE = "lose_life"
    SET_LIFE = "set_life"

    # Will production (CR 907)
    PRODUCE_WILL = "produce_will"

    # Counters (CR 1022)
    ADD_COUNTER = "add_counter"
    REMOVE_COUNTER = "remove_counter"

    # Rest/Recover (CR 1013)
    REST = "rest"
    RECOVER = "recover"

    # Stat modification (CR 909)
    MODIFY_ATK = "modify_atk"
    MODIFY_DEF = "modify_def"
    SET_ATK = "set_atk"
    SET_DEF = "set_def"

    # Ability modification
    GRANT_ABILITY = "grant_ability"
    REMOVE_ABILITY = "remove_ability"
    GRANT_KEYWORD = "grant_keyword"
    REMOVE_KEYWORD = "remove_keyword"

    # Attribute modification
    GRANT_ATTRIBUTE = "grant_attribute"
    REMOVE_ATTRIBUTE = "remove_attribute"
    SET_ATTRIBUTE = "set_attribute"

    # Race/type modification
    GRANT_RACE = "grant_race"
    SET_TYPE = "set_type"

    # Control (CR 105.3)
    GAIN_CONTROL = "gain_control"

    # Copy (CR 1017)
    COPY = "copy"
    BECOME_COPY = "become_copy"

    # Prevent (CR 1018)
    PREVENT_DAMAGE = "prevent_damage"

    # Special
    SUMMON = "summon"            # CR 1006


class KeywordAbility(Flag):
    """
    Keyword abilities per CR 1100+.

    Grimm Cluster era keywords only.
    """
    NONE = 0

    # Combat keywords
    PIERCE = auto()              # CR 1103 - excess damage goes through
    PRECISION = auto()           # CR 1104 - can attack recovered J/resonators
    FIRST_STRIKE = auto()        # CR 1105 - deals damage first
    FLYING = auto()              # CR 1107 - can only be blocked by flying

    # Speed keywords
    SWIFTNESS = auto()           # CR 1108 - can attack/use abilities turn it enters
    QUICKCAST = auto()           # CR 1112 - can play at instant timing

    # Protection keywords
    IMPERISHABLE = auto()        # CR 1109 - J-ruler doesn't become astral when destroyed
    BARRIER = auto()             # CR 1120 - can't be targeted by opponent

    # Other Grimm-era keywords
    AWAKENING = auto()           # CR 1110 - pay additional cost for bonus
    INCARNATION = auto()         # CR 1111 - banish resonator instead of cost
    TRIGGER = auto()             # CR 1113 - special chant timing
    REMNANT = auto()             # CR 1115 - can play from graveyard
    TARGET_ATTACK = auto()       # Can attack specific targets
    DRAIN = auto()               # CR 1136 - gain life equal to damage dealt
    EXPLODE = auto()             # CR 1106 - mutual destruction on battle damage

    # Protection/Restriction keywords (not formal keywords but continuous effects)
    INDESTRUCTIBLE = auto()      # Cannot be destroyed
    HEXPROOF = auto()            # Cannot be targeted (alias for Barrier in some contexts)
    UNBLOCKABLE = auto()         # Cannot be blocked
    CANNOT_ATTACK = auto()       # Cannot attack
    CANNOT_BLOCK = auto()        # Cannot block


class EffectDuration(Enum):
    """
    How long a continuous effect lasts.

    CR 909: Continuous effects apply as specified.
    CR 505.5b: "until end of turn" effects end at end phase.
    """
    # Instant - applied once
    INSTANT = "instant"

    # Until end of turn (CR 505.5b)
    UNTIL_END_OF_TURN = "until_end_of_turn"

    # Until next turn
    UNTIL_NEXT_TURN = "until_next_turn"

    # Until will clearance (CR 503.4, 505.5c)
    UNTIL_WILL_CLEARANCE = "until_will_clearance"

    # As long as source is in field (CR 909)
    WHILE_ON_FIELD = "while_on_field"

    # As long as condition is met
    WHILE_CONDITION = "while_condition"

    # Permanent (until game end or card leaves)
    PERMANENT = "permanent"

    # Until end of game
    UNTIL_END_OF_GAME = "until_end_of_game"
