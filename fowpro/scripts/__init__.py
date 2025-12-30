"""
FoWPro Card Scripting System
============================

Inspired by YGOPro's Lua scripting, this system allows cards to define
their own behavior through Python scripts.

Each card can have a script that defines:
- Activated abilities (tap to produce will, pay cost to activate)
- Triggered abilities (when X happens, do Y)
- Continuous effects (while in play, modify game state)
- Enter/leave field effects

Scripts are registered by card code and looked up when cards are created.

NEW: Now supports CR (Comprehensive Rules) based ability system via rules_bridge.
- RulesCardScript: New base class using CR-compliant abilities
- CR types: ActivateAbility, AutomaticAbility, ContinuousAbility, WillAbility
- See fowpro/rules/ for CR-based type definitions
"""

from abc import ABC
from dataclasses import dataclass, field
from typing import Callable, Optional, List, Any, TYPE_CHECKING
from enum import Enum, auto

if TYPE_CHECKING:
    from ..engine import GameEngine
    from ..models import Card, Attribute, WillCost


# =============================================================================
# EFFECT TIMING / TYPES (similar to YGOPro's SetType, SetCode)
# =============================================================================

class EffectType(Enum):
    """When/how an effect applies"""
    # Activated - player chooses to use it
    ACTIVATED = auto()          # [Activate] abilities

    # Triggered - automatic when condition met
    TRIGGER_ENTER = auto()      # When enters field
    TRIGGER_LEAVE = auto()      # When leaves field
    TRIGGER_ATTACK = auto()     # When attacks
    TRIGGER_BLOCK = auto()      # When blocks
    TRIGGER_DAMAGE = auto()     # When deals/receives damage
    TRIGGER_RECOVER = auto()    # When recovers
    TRIGGER_REST = auto()       # When rests

    # Continuous - always applies while conditions met
    CONTINUOUS = auto()         # [Continuous] abilities

    # Static - modifies card properties
    STATIC = auto()             # ATK/DEF modifications, keyword grants


class EffectTiming(Enum):
    """Speed of effect activation"""
    SPELL_SPEED = auto()        # Sorcery speed - only on your main phase, empty chase
    INSTANT_SPEED = auto()      # Can respond to chase
    WILL_SPEED = auto()         # Immediate, doesn't use chase (will abilities)


class EffectCategory(Enum):
    """What the effect does (for UI/logging)"""
    PRODUCE_WILL = auto()
    DRAW = auto()
    DESTROY = auto()
    DAMAGE = auto()
    RECOVER_LIFE = auto()
    BUFF = auto()
    DEBUFF = auto()
    SPECIAL_SUMMON = auto()
    SEARCH = auto()
    BANISH = auto()
    RETURN_TO_HAND = auto()
    COUNTER = auto()            # Counter spell/ability
    NEGATE = auto()


# =============================================================================
# EFFECT DEFINITION
# =============================================================================

@dataclass
class Effect:
    """
    A single effect on a card.

    Similar to YGOPro's Effect object with SetType, SetCode, SetCondition, etc.
    """
    # Identity
    name: str = ""
    description: str = ""

    # Type and timing
    effect_type: EffectType = EffectType.ACTIVATED
    timing: EffectTiming = EffectTiming.SPELL_SPEED
    category: EffectCategory = EffectCategory.PRODUCE_WILL

    # Costs (like YGOPro's SetCost)
    will_cost: Optional['WillCost'] = None
    tap_cost: bool = False                      # Requires resting the card
    additional_cost: Optional[Callable] = None  # Custom cost function

    # Condition (like YGOPro's SetCondition)
    # Returns True if effect can be activated/applied
    condition: Optional[Callable[['GameEngine', 'Card'], bool]] = None

    # Target (like YGOPro's SetTarget)
    # For effects that need targets, validates and selects them
    # Returns True if valid targets exist, also stores selected targets
    target: Optional[Callable[['GameEngine', 'Card', bool], bool]] = None

    # Operation (like YGOPro's SetOperation)
    # The actual effect resolution
    operation: Optional[Callable[['GameEngine', 'Card'], None]] = None

    # For continuous effects - what value/modification to apply
    value: Any = None

    # Flags
    uses_chase: bool = True     # Does this go on the chase?
    is_mandatory: bool = False  # Must activate if conditions met?
    once_per_turn: bool = False

    # Internal tracking
    _activated_this_turn: bool = field(default=False, repr=False)


# =============================================================================
# CARD SCRIPT BASE CLASS
# =============================================================================

class CardScript(ABC):
    """
    Base class for card scripts.

    Like YGOPro's initial_effect function, but as a class.
    Override methods to define card behavior.
    """

    def __init__(self, card_code: str):
        self.card_code = card_code
        self._effects: List[Effect] = []

    def initial_effect(self, game: 'GameEngine', card: 'Card'):
        """
        Called when card is created. Register effects here.
        Override this in subclasses - like YGOPro's initial_effect(c).
        """
        pass

    def register_effect(self, effect: Effect):
        """Register an effect to this card script"""
        self._effects.append(effect)

    def get_effects(self) -> List[Effect]:
        """Get all registered effects"""
        return self._effects

    def get_activated_abilities(self, game: 'GameEngine', card: 'Card') -> List[Effect]:
        """Get activated abilities that can currently be used"""
        abilities = []
        for effect in self._effects:
            if effect.effect_type != EffectType.ACTIVATED:
                continue
            # Check condition
            if effect.condition and not effect.condition(game, card):
                continue
            # Check once per turn
            if effect.once_per_turn and effect._activated_this_turn:
                continue
            # Check tap cost
            if effect.tap_cost and card.is_rested:
                continue
            abilities.append(effect)
        return abilities

    # === Lifecycle Hooks ===

    def on_enter_field(self, game: 'GameEngine', card: 'Card'):
        """Called when card enters the field"""
        for effect in self._effects:
            if effect.effect_type == EffectType.TRIGGER_ENTER:
                if not effect.condition or effect.condition(game, card):
                    if effect.operation:
                        effect.operation(game, card)

    def on_leave_field(self, game: 'GameEngine', card: 'Card'):
        """Called when card leaves the field"""
        for effect in self._effects:
            if effect.effect_type == EffectType.TRIGGER_LEAVE:
                if not effect.condition or effect.condition(game, card):
                    if effect.operation:
                        effect.operation(game, card)

    def on_recover(self, game: 'GameEngine', card: 'Card'):
        """Called when card recovers (untaps)"""
        pass

    def on_rest(self, game: 'GameEngine', card: 'Card'):
        """Called when card rests (taps)"""
        pass

    def on_turn_start(self, game: 'GameEngine', card: 'Card'):
        """Called at start of controller's turn - reset once-per-turn effects"""
        for effect in self._effects:
            effect._activated_this_turn = False

    # === Magic Stone Specific ===

    def get_will_colors(self, game: 'GameEngine', card: 'Card') -> List['Attribute']:
        """
        For magic stones: return list of will colors this stone can produce.
        Override in stone scripts.
        """
        return []

    def produce_will(self, game: 'GameEngine', card: 'Card',
                     chosen_color: 'Attribute') -> bool:
        """
        Produce will of the chosen color and rest the card.
        Override for complex cards (e.g., Moon Shade life cost).
        """
        from ..models import Attribute
        if chosen_color in self.get_will_colors(game, card):
            game.players[card.controller].will_pool.add(chosen_color, 1)
            card.rest()
            return True
        return False


# =============================================================================
# SCRIPT REGISTRY
# =============================================================================

class ScriptRegistry:
    """
    Registry mapping card codes to their scripts.

    Usage:
        @ScriptRegistry.register("CMF-096")
        class MagicStoneOfFlame(CardScript):
            ...
    """
    _scripts: dict[str, type[CardScript]] = {}
    _instances: dict[str, CardScript] = {}  # Cache instances
    _default_script_class: Optional[type[CardScript]] = None

    @classmethod
    def register(cls, card_code: str):
        """Decorator to register a script class for a card code"""
        def decorator(script_class: type[CardScript]):
            cls._scripts[card_code] = script_class
            return script_class
        return decorator

    @classmethod
    def register_default(cls, script_class: type[CardScript]):
        """Register the default script class for cards without custom scripts"""
        cls._default_script_class = script_class
        return script_class

    @classmethod
    def get(cls, card_code: str) -> CardScript:
        """Get a script instance for a card code"""
        print(f"[DEBUG] ScriptRegistry.get({card_code})", flush=True)
        # Check cache
        if card_code in cls._instances:
            print(f"[DEBUG] ScriptRegistry: returning cached {cls._instances[card_code].__class__.__name__}", flush=True)
            return cls._instances[card_code]

        # Create new instance
        if card_code in cls._scripts:
            print(f"[DEBUG] ScriptRegistry: creating new {cls._scripts[card_code].__name__}", flush=True)
            instance = cls._scripts[card_code](card_code)
        elif cls._default_script_class:
            print(f"[DEBUG] ScriptRegistry: using default script", flush=True)
            instance = cls._default_script_class(card_code)
        else:
            print(f"[DEBUG] ScriptRegistry: using base CardScript", flush=True)
            instance = CardScript(card_code)

        cls._instances[card_code] = instance
        return instance

    @classmethod
    def has_script(cls, card_code: str) -> bool:
        """Check if a custom script exists for this card"""
        return card_code in cls._scripts

    @classmethod
    def clear_cache(cls):
        """Clear the instance cache (useful for testing)"""
        cls._instances.clear()


# =============================================================================
# HELPER FUNCTIONS (like YGOPro's aux functions)
# =============================================================================

def make_will_effect(colors: List['Attribute']) -> Effect:
    """Helper to create a standard will production effect"""
    from ..models import Attribute

    color_names = [c.name for c in colors]

    def operation(game, card):
        # Will production is handled by the script's produce_will method
        pass

    return Effect(
        name="Produce Will",
        description=f"Produce {' or '.join(color_names)} will",
        effect_type=EffectType.ACTIVATED,
        timing=EffectTiming.WILL_SPEED,
        category=EffectCategory.PRODUCE_WILL,
        tap_cost=True,
        uses_chase=False,
        operation=operation,
    )


# =============================================================================
# IMPORT SUBSYSTEMS
# =============================================================================

# Effect subsystems
from .effects import (
    produce_will, draw_cards, deal_damage, destroy_card,
    buff_card, set_stats, gain_life, lose_life,
    return_to_hand, banish_card, rest_card, recover_card,
    TargetType, is_valid_target, get_valid_targets,
    get_resonators_on_field, get_spells_on_chase, require_target,
    search_deck, search_graveyard, get_field_cards,
    special_summon, put_into_play,
    add_counter, remove_counter, get_counters,
    cancel_spell,
)

# Keywords
from .keywords import (
    Keyword, KeywordState, KeywordProcessor,
    parse_keywords, KEYWORD_NAMES, TEXT_TO_KEYWORD,
    grant_flying, grant_swiftness, grant_first_strike,
    grant_pierce, grant_imperishable, grant_barrier,
)

# Triggers
from .triggers import (
    TriggerEvent, TriggerTiming, TriggerCondition,
    TriggeredAbility, TriggerManager,
    when_enters_field, when_leaves_field, when_attacks,
    when_deals_damage, when_destroyed, at_turn_start, at_turn_end,
)

# Continuous effects
from .continuous import (
    EffectLayer, EffectDuration, AffectedCardFilter,
    ContinuousEffect, ContinuousEffectManager,
    all_resonators_get_buff, all_resonators_gain_keyword,
    opponent_resonators_lose_keyword, attribute_resonators_get_buff,
)

# Costs
from .costs import (
    CostType, WillCost, SacrificeCost, DiscardCost, BanishCost, Cost,
    CostValidator, CostPayer,
    rest_cost, will_cost, will_and_rest,
    sacrifice_resonator, discard_cards, pay_life, banish_from_graveyard,
)

# Targeting
from .targeting import (
    TargetZone, TargetController, TargetFilter, TargetRequirement,
    TargetSelection, TargetingManager,
    target_resonator, target_j_resonator, target_opponent_resonator,
    target_your_resonator, target_spell_on_chase, target_stone,
    single_target, multiple_targets, up_to_targets, optional_target,
)

# Zone operations
from .zones import (
    SearchDestination, SearchFilter, ZoneOperations,
    any_resonator, any_spell, resonator_with_cost,
    resonator_with_attribute, card_named, any_card,
)

# Tokens
from .tokens import (
    TokenData, Token, TokenManager,
    WOLF_TOKEN, ZOMBIE_TOKEN, FAIRY_TOKEN, KNIGHT_TOKEN, GOLEM_TOKEN,
    create_wolf_token, create_zombie_token, create_fairy_token, create_custom_token,
)

# Combat
from .combat import (
    CombatPhase, AttackDeclaration, CombatState, CombatManager,
    ControlManager, ControlEffect,
    steal_until_end_of_turn, steal_permanently,
)

# Counter/Cancel
from .counter import (
    ChaseItemType, ChaseItem, ChaseManager,
    CounterManager,
    counter_target_spell, counter_target_ability, counter_unless_pay,
    add_plus_counter, add_minus_counter, remove_plus_counter, remove_minus_counter,
)

# Effect resolution
from .resolution import (
    ChoiceType, EffectMode, ModalEffect, EffectResolver, ChoiceRequest,
    choose_one, choose_two, do_both,
    if_you_control_resonator, if_opponent_controls_resonator,
    if_graveyard_has_cards, if_life_at_or_below, if_hand_has_cards,
)

# Parser for ability text
from .parser import (
    AbilityType, ParsedEffect, ParsedAbility, AbilityParser,
    parse_ability_text,
)

# Import submodules to register scripts
# Generated scripts include stones - auto-generated from ability text
try:
    from . import generated
except ImportError:
    pass  # Generated scripts may not exist yet

# Import hand-crafted special stone scripts
try:
    from . import stones
except ImportError:
    pass  # Stones module may not exist

# Import hand-crafted deck scripts - DEPRECATED, to be removed
# The deck_grimm scripts were a temporary crutch before the CR-based system
# These will be replaced by generated CR-compliant scripts
try:
    from . import deck_grimm
except ImportError:
    pass  # Deck scripts may not exist

# Import default script for fallback behavior
from . import default

# =============================================================================
# CR (COMPREHENSIVE RULES) BASED SYSTEM
# =============================================================================

# Import the rules bridge for CR-compliant card scripts
try:
    from .rules_bridge import (
        RulesCardScript,
        # Re-exported from rules module
        AbilityType, TriggerCondition, TriggerTiming,
        EffectAction, KeywordAbility, EffectDuration,
        TargetRequirement, TargetFilter, TargetZone, TargetController, CommonFilters,
        Condition, ConditionType, ConditionOperator, ConditionBuilder,
        ModalChoice, Mode, ModalPatterns,
        ContinuousEffect, ReplacementEffect, EffectBuilder,
        Ability, ActivateAbility, AutomaticAbility, ContinuousAbility, WillAbility,
        AbilityFactory,
        RulesEffect,
    )
except ImportError as e:
    print(f"[WARN] Could not import rules_bridge: {e}")
    RulesCardScript = CardScript  # Fallback to old system

# Import CR-based parser and generator
try:
    from .cr_parser import CRAbilityParser, parse_ability_text_cr
    from .cr_generator import CRScriptGenerator, cr_generator
except ImportError as e:
    print(f"[WARN] Could not import CR parser/generator: {e}")
    CRAbilityParser = None
    parse_ability_text_cr = None


# =============================================================================
# PUBLIC API
# =============================================================================

__all__ = [
    # Core (legacy)
    'EffectType', 'EffectTiming', 'EffectCategory', 'Effect',
    'CardScript', 'ScriptRegistry', 'make_will_effect',

    # Keywords
    'Keyword', 'KeywordState', 'KeywordProcessor',

    # Triggers
    'TriggerEvent', 'TriggerManager', 'TriggeredAbility',

    # Continuous
    'ContinuousEffect', 'ContinuousEffectManager',

    # Costs
    'Cost', 'WillCost', 'CostValidator', 'CostPayer',

    # Targeting
    'TargetFilter', 'TargetRequirement', 'TargetingManager',

    # Zones
    'ZoneOperations', 'SearchFilter',

    # Tokens
    'TokenManager', 'TokenData', 'Token',

    # Combat
    'CombatManager', 'ControlManager',

    # Counter
    'ChaseManager', 'CounterManager',

    # Resolution
    'EffectResolver', 'ModalEffect',

    # Parser (legacy)
    'AbilityParser', 'parse_ability_text',

    # ==========================================================================
    # CR (Comprehensive Rules) based system - NEW
    # ==========================================================================

    # New base class
    'RulesCardScript',

    # CR Ability types (CR 901-907)
    'AbilityType', 'ActivateAbility', 'AutomaticAbility',
    'ContinuousAbility', 'WillAbility', 'Ability', 'AbilityFactory',

    # CR Effects (CR 908-910)
    'RulesEffect', 'EffectBuilder', 'ReplacementEffect',
    'EffectAction', 'EffectDuration',

    # CR Triggers (CR 906)
    'TriggerCondition', 'TriggerTiming',

    # CR Keywords (CR 1100+)
    'KeywordAbility',

    # CR Targeting (CR 903.2i)
    'TargetZone', 'TargetController', 'CommonFilters',

    # CR Conditions
    'Condition', 'ConditionType', 'ConditionOperator', 'ConditionBuilder',

    # CR Modals (CR 903.2g)
    'ModalChoice', 'Mode', 'ModalPatterns',

    # CR Parser and Generator
    'CRAbilityParser', 'parse_ability_text_cr',
    'CRScriptGenerator', 'cr_generator',
]
