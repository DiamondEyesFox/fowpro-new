"""
FoWPro - Data Models
====================
Core data structures for Force of Will game simulation.
"""

from __future__ import annotations
from dataclasses import dataclass, field as dataclass_field
from enum import Enum, auto, Flag
from typing import Optional, Callable, Any
import uuid
import json


# =============================================================================
# ENUMS
# =============================================================================

class Attribute(Flag):
    """Card attributes/colors"""
    NONE = 0
    LIGHT = auto()
    FIRE = auto()
    WATER = auto()
    WIND = auto()
    DARKNESS = auto()
    VOID = auto()  # Colorless/generic

    # Multi-attribute shortcuts
    @classmethod
    def from_string(cls, s: str) -> "Attribute":
        mapping = {
            "light": cls.LIGHT, "white": cls.LIGHT, "w": cls.LIGHT,
            "fire": cls.FIRE, "red": cls.FIRE, "r": cls.FIRE,
            "water": cls.WATER, "blue": cls.WATER, "u": cls.WATER,
            "wind": cls.WIND, "green": cls.WIND, "g": cls.WIND,
            "darkness": cls.DARKNESS, "black": cls.DARKNESS, "b": cls.DARKNESS,
            "void": cls.VOID, "colorless": cls.VOID,
        }
        return mapping.get(s.lower().strip(), cls.NONE)


class CardType(Enum):
    """Card types in FoW"""
    RULER = "Ruler"
    J_RULER = "J-Ruler"
    RESONATOR = "Resonator"
    SPELL_CHANT = "Spell:Chant"
    SPELL_CHANT_INSTANT = "Spell:Chant-Instant"
    SPELL_CHANT_STANDBY = "Spell:Chant-Standby"
    ADDITION_FIELD = "Addition:Field"
    ADDITION_RESONATOR = "Addition:Resonator"
    ADDITION_RULER = "Addition:Ruler"
    REGALIA = "Regalia"
    MAGIC_STONE = "Magic Stone"
    SPECIAL_MAGIC_STONE = "Special Magic Stone"

    @classmethod
    def from_string(cls, s: str) -> "CardType":
        s = s.strip()
        for t in cls:
            if t.value.lower() == s.lower():
                return t
        # Fuzzy matching
        if "ruler" in s.lower() and "j-" in s.lower():
            return cls.J_RULER
        if "ruler" in s.lower():
            return cls.RULER
        if "resonator" in s.lower():
            return cls.RESONATOR
        if "chant-instant" in s.lower() or "instant" in s.lower():
            return cls.SPELL_CHANT_INSTANT
        if "chant-standby" in s.lower() or "standby" in s.lower():
            return cls.SPELL_CHANT_STANDBY
        if "chant" in s.lower() or "spell" in s.lower():
            return cls.SPELL_CHANT
        if "addition" in s.lower() and "field" in s.lower():
            return cls.ADDITION_FIELD
        if "addition" in s.lower() and "resonator" in s.lower():
            return cls.ADDITION_RESONATOR
        if "addition" in s.lower():
            return cls.ADDITION_FIELD
        if "regalia" in s.lower():
            return cls.REGALIA
        if "special" in s.lower() and "stone" in s.lower():
            return cls.SPECIAL_MAGIC_STONE
        if "stone" in s.lower():
            return cls.MAGIC_STONE
        return cls.RESONATOR  # Default


class Zone(Enum):
    """Game zones"""
    MAIN_DECK = auto()
    MAGIC_STONE_DECK = auto()
    HAND = auto()
    FIELD = auto()
    RULER_AREA = auto()
    GRAVEYARD = auto()
    REMOVED = auto()
    CHASE = auto()
    SIDEBOARD = auto()
    STANDBY = auto()  # For Chant-Standby cards


class Phase(Enum):
    """Turn phases - official FoW order"""
    DRAW = auto()
    RECOVERY = auto()
    MAIN = auto()
    END = auto()
    # Note: Battle/Attack happens DURING Main Phase, not as a separate phase


class CombatStep(Enum):
    """Combat timing windows"""
    NONE = auto()
    DECLARE_ATTACK = auto()
    DECLARE_BLOCKER = auto()
    BEFORE_DAMAGE = auto()
    FIRST_STRIKE_DAMAGE = auto()
    NORMAL_DAMAGE = auto()
    AFTER_DAMAGE = auto()
    END_OF_BATTLE = auto()


class Keyword(Flag):
    """Card keywords"""
    NONE = 0
    SWIFTNESS = auto()
    FLYING = auto()
    FIRST_STRIKE = auto()
    PIERCE = auto()
    DRAIN = auto()
    IMPERISHABLE = auto()
    ETERNAL = auto()
    QUICKCAST = auto()
    TARGET_ATTACK = auto()
    PRECISION = auto()
    BARRIER = auto()
    EXPLODE = auto()
    AWAKENING = auto()
    INCARNATION = auto()
    STEALTH = auto()
    VIGILANCE = auto()  # Does not rest to attack
    # Protection/restriction keywords
    INDESTRUCTIBLE = auto()  # Cannot be destroyed
    UNBLOCKABLE = auto()     # Cannot be blocked
    CANNOT_ATTACK = auto()   # Cannot declare attacks
    CANNOT_BLOCK = auto()    # Cannot be declared as blocker
    HEXPROOF = auto()        # Cannot be targeted by opponent (alias for Barrier)
    REMNANT = auto()         # Can be played from graveyard

    @classmethod
    def from_string(cls, s: str) -> "Keyword":
        mapping = {
            "swiftness": cls.SWIFTNESS,
            "flying": cls.FLYING,
            "first strike": cls.FIRST_STRIKE,
            "pierce": cls.PIERCE,
            "drain": cls.DRAIN,
            "imperishable": cls.IMPERISHABLE,
            "eternal": cls.ETERNAL,
            "quickcast": cls.QUICKCAST,
            "target attack": cls.TARGET_ATTACK,
            "precision": cls.PRECISION,
            "barrier": cls.BARRIER,
            "explode": cls.EXPLODE,
            "awakening": cls.AWAKENING,
            "incarnation": cls.INCARNATION,
            "stealth": cls.STEALTH,
            "vigilance": cls.VIGILANCE,
            "indestructible": cls.INDESTRUCTIBLE,
            "unblockable": cls.UNBLOCKABLE,
            "cannot attack": cls.CANNOT_ATTACK,
            "cannot block": cls.CANNOT_BLOCK,
            "hexproof": cls.HEXPROOF,
            "remnant": cls.REMNANT,
        }
        return mapping.get(s.lower().strip(), cls.NONE)


class Rarity(Enum):
    """Card rarities"""
    COMMON = "C"
    UNCOMMON = "U"
    RARE = "R"
    SUPER_RARE = "SR"
    RULER = "Ruler"  # Ruler cards have their own rarity


class EffectType(Enum):
    """Types of card effects"""
    CONTINUOUS = auto()
    ACTIVATED = auto()
    TRIGGER = auto()
    ENTER = auto()  # ETB
    LEAVE = auto()  # LTB
    ATTACK = auto()
    BLOCK = auto()
    DAMAGE = auto()
    JUDGMENT = auto()


class TriggerCondition(Enum):
    """When triggered effects trigger"""
    ENTERS_FIELD = auto()
    LEAVES_FIELD = auto()
    DESTROYED = auto()
    ATTACKS = auto()
    BLOCKS = auto()
    DEALS_DAMAGE = auto()
    TAKES_DAMAGE = auto()
    BEGINNING_OF_TURN = auto()
    END_OF_TURN = auto()
    DRAW_CARD = auto()
    PLAY_CARD = auto()
    JUDGMENT = auto()


# =============================================================================
# COST STRUCTURES
# =============================================================================

@dataclass
class WillCost:
    """Represents will/mana cost"""
    light: int = 0
    fire: int = 0
    water: int = 0
    wind: int = 0
    darkness: int = 0
    void: int = 0  # Generic/colorless
    x: bool = False  # Has X in cost

    @property
    def total(self) -> int:
        return self.light + self.fire + self.water + self.wind + self.darkness + self.void

    @property
    def colored_total(self) -> int:
        return self.light + self.fire + self.water + self.wind + self.darkness

    @classmethod
    def parse(cls, cost_str: str) -> "WillCost":
        """Parse cost string like '{W}{1}' or 'WW1'"""
        cost = cls()
        if not cost_str:
            return cost

        # Remove braces and spaces
        s = cost_str.replace("{", "").replace("}", "").replace(" ", "").upper()

        for char in s:
            if char == 'W' or char == 'L':  # White/Light
                cost.light += 1
            elif char == 'R' or char == 'F':  # Red/Fire
                cost.fire += 1
            elif char == 'U' or char == 'B':  # blUe/Water (B can be darkness too)
                if char == 'B':
                    cost.darkness += 1
                else:
                    cost.water += 1
            elif char == 'G' or char == 'N':  # Green/Wind
                cost.wind += 1
            elif char == 'D':  # Darkness
                cost.darkness += 1
            elif char == 'X':
                cost.x = True
            elif char.isdigit():
                cost.void += int(char)

        return cost

    def to_dict(self) -> dict:
        d = {}
        if self.light: d["light"] = self.light
        if self.fire: d["fire"] = self.fire
        if self.water: d["water"] = self.water
        if self.wind: d["wind"] = self.wind
        if self.darkness: d["darkness"] = self.darkness
        if self.void: d["void"] = self.void
        if self.x: d["x"] = True
        return d

    def __str__(self) -> str:
        parts = []
        if self.x: parts.append("X")
        if self.void: parts.append(str(self.void))
        parts.extend(["W"] * self.light)
        parts.extend(["R"] * self.fire)
        parts.extend(["U"] * self.water)
        parts.extend(["G"] * self.wind)
        parts.extend(["B"] * self.darkness)
        return "".join(parts) if parts else "0"


@dataclass
class WillPool:
    """Player's current will pool"""
    light: int = 0
    fire: int = 0
    water: int = 0
    wind: int = 0
    darkness: int = 0
    void: int = 0

    def add(self, attr: Attribute, amount: int = 1):
        if Attribute.LIGHT in attr: self.light += amount
        if Attribute.FIRE in attr: self.fire += amount
        if Attribute.WATER in attr: self.water += amount
        if Attribute.WIND in attr: self.wind += amount
        if Attribute.DARKNESS in attr: self.darkness += amount
        if Attribute.VOID in attr: self.void += amount

    def add_will(self, light=0, fire=0, water=0, wind=0, darkness=0, void=0):
        self.light += light
        self.fire += fire
        self.water += water
        self.wind += wind
        self.darkness += darkness
        self.void += void

    def can_pay(self, cost: WillCost, any_will_pays_colored: bool = False) -> bool:
        """Check if pool can pay a cost

        If any_will_pays_colored is True, any will color can pay for colored costs
        (used for Grimm's ability with Fairy Tale resonators)
        """
        if any_will_pays_colored:
            # Any will can pay any cost - just check total
            total_cost = cost.light + cost.fire + cost.water + cost.wind + cost.darkness + cost.void
            total_will = self.light + self.fire + self.water + self.wind + self.darkness + self.void
            return total_will >= total_cost

        # Check specific colors
        if self.light < cost.light: return False
        if self.fire < cost.fire: return False
        if self.water < cost.water: return False
        if self.wind < cost.wind: return False
        if self.darkness < cost.darkness: return False

        # Calculate remaining after colored costs
        remaining = (
            (self.light - cost.light) +
            (self.fire - cost.fire) +
            (self.water - cost.water) +
            (self.wind - cost.wind) +
            (self.darkness - cost.darkness) +
            self.void
        )

        return remaining >= cost.void

    def pay(self, cost: WillCost, any_will_pays_colored: bool = False) -> bool:
        """Pay a cost, return True if successful

        If any_will_pays_colored is True, any will color can pay for colored costs
        """
        if not self.can_pay(cost, any_will_pays_colored):
            return False

        if any_will_pays_colored:
            # Pay from any will - just deduct total cost
            total_cost = cost.light + cost.fire + cost.water + cost.wind + cost.darkness + cost.void
            for attr in ['light', 'fire', 'water', 'wind', 'darkness', 'void']:
                available = getattr(self, attr)
                paid = min(total_cost, available)
                setattr(self, attr, available - paid)
                total_cost -= paid
                if total_cost <= 0:
                    break
        else:
            self.light -= cost.light
            self.fire -= cost.fire
            self.water -= cost.water
            self.wind -= cost.wind
            self.darkness -= cost.darkness

            # Pay generic from remaining
            to_pay = cost.void
            for attr in ['light', 'fire', 'water', 'wind', 'darkness', 'void']:
                available = getattr(self, attr)
                paid = min(to_pay, available)
                setattr(self, attr, available - paid)
                to_pay -= paid
                if to_pay <= 0:
                    break

        return True

    def clear(self):
        self.light = self.fire = self.water = self.wind = self.darkness = self.void = 0

    @property
    def total(self) -> int:
        return self.light + self.fire + self.water + self.wind + self.darkness + self.void

    def to_dict(self) -> dict:
        return {
            "light": self.light, "fire": self.fire, "water": self.water,
            "wind": self.wind, "darkness": self.darkness, "void": self.void
        }


# =============================================================================
# CARD STRUCTURES
# =============================================================================

@dataclass
class CardAbility:
    """Represents a single ability on a card"""
    ability_type: EffectType
    text: str
    cost: Optional[WillCost] = None
    additional_cost: str = ""  # "Rest", "Banish this card", etc.
    trigger: Optional[TriggerCondition] = None

    # For effect execution
    effect_id: str = ""  # Links to effect implementation


@dataclass
class CardData:
    """Static card data (database template)"""
    code: str  # e.g., "CMF-001"
    name: str
    card_type: CardType
    attribute: Attribute
    cost: WillCost
    atk: int = 0
    defense: int = 0
    races: list[str] = dataclass_field(default_factory=list)  # Traits like "Human", "Fairy Tale"
    keywords: Keyword = Keyword.NONE
    abilities: list[CardAbility] = dataclass_field(default_factory=list)
    ability_text: str = ""  # Raw ability text
    flavor_text: str = ""
    rarity: Rarity = Rarity.COMMON
    set_code: str = ""  # CMF, TAT, MPR, MOA

    # Ruler-specific
    j_ruler_code: str = ""  # Code of J-Ruler side
    judgment_cost: Optional[WillCost] = None

    # J-Ruler specific
    ruler_code: str = ""  # Code of Ruler side

    def is_ruler(self) -> bool:
        return self.card_type in [CardType.RULER, CardType.J_RULER]

    def is_resonator(self) -> bool:
        return self.card_type == CardType.RESONATOR

    def is_spell(self) -> bool:
        return self.card_type in [CardType.SPELL_CHANT, CardType.SPELL_CHANT_INSTANT,
                                  CardType.SPELL_CHANT_STANDBY]

    def is_instant(self) -> bool:
        return (self.card_type == CardType.SPELL_CHANT_INSTANT or
                Keyword.QUICKCAST in self.keywords)

    def is_stone(self) -> bool:
        return self.card_type in [CardType.MAGIC_STONE, CardType.SPECIAL_MAGIC_STONE]

    def has_keyword(self, kw: Keyword) -> bool:
        return kw in self.keywords

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "name": self.name,
            "type": self.card_type.value,
            "attribute": self.attribute.name if self.attribute else "NONE",
            "cost": str(self.cost),
            "atk": self.atk,
            "def": self.defense,
            "races": self.races,
            "keywords": self.keywords.name if self.keywords else "NONE",
            "ability_text": self.ability_text,
            "rarity": self.rarity.value,
            "set": self.set_code,
        }


@dataclass
class Card:
    """Runtime card instance"""
    uid: str
    data: CardData
    owner: int  # Player index
    controller: int  # Current controller
    zone: Zone

    # Runtime state
    is_rested: bool = False
    is_face_down: bool = False
    damage: int = 0
    entered_turn: int = -1  # Turn card entered current zone

    # Modifiers from effects
    atk_mod: int = 0
    def_mod: int = 0
    granted_keywords: Keyword = Keyword.NONE
    removed_keywords: Keyword = Keyword.NONE

    # Attached cards (additions, counters)
    attachments: list["Card"] = dataclass_field(default_factory=list)
    attached_to: Optional["Card"] = None

    # Counters
    counters: dict[str, int] = dataclass_field(default_factory=dict)

    @property
    def effective_atk(self) -> int:
        return max(0, self.data.atk + self.atk_mod)

    @property
    def effective_def(self) -> int:
        return max(0, self.data.defense + self.def_mod)

    @property
    def effective_keywords(self) -> Keyword:
        return (self.data.keywords | self.granted_keywords) & ~self.removed_keywords

    def has_keyword(self, kw: Keyword) -> bool:
        return kw in self.effective_keywords

    def rest(self):
        self.is_rested = True

    def recover(self):
        self.is_rested = False

    def add_counter(self, counter_type: str, amount: int = 1):
        self.counters[counter_type] = self.counters.get(counter_type, 0) + amount

    def remove_counter(self, counter_type: str, amount: int = 1) -> int:
        current = self.counters.get(counter_type, 0)
        removed = min(current, amount)
        self.counters[counter_type] = current - removed
        return removed

    def to_dict(self) -> dict:
        return {
            "uid": self.uid,
            "code": self.data.code,
            "name": self.data.name,
            "type": self.data.card_type.value,
            "owner": self.owner,
            "controller": self.controller,
            "zone": self.zone.name,
            "is_rested": self.is_rested,
            "atk": self.effective_atk,
            "def": self.effective_def,
            "damage": self.damage,
            "counters": self.counters,
        }


# =============================================================================
# CHASE/STACK ITEMS
# =============================================================================

@dataclass
class ChaseItem:
    """An item on the chase (stack)"""
    uid: str
    source: Card
    item_type: str  # "SPELL", "ABILITY", "JUDGMENT"
    controller: int
    targets: list[Any] = dataclass_field(default_factory=list)  # Cards, players, etc.
    effect_data: dict = dataclass_field(default_factory=dict)
    paid_cost: Optional[WillCost] = None

    def to_dict(self) -> dict:
        return {
            "uid": self.uid,
            "source": self.source.data.name,
            "type": self.item_type,
            "controller": self.controller,
            "targets": [str(t) for t in self.targets],
        }


# =============================================================================
# PLAYER STATE
# =============================================================================

@dataclass
class PlayerState:
    """Complete state for one player"""
    index: int
    life: int = 4000
    will_pool: WillPool = dataclass_field(default_factory=WillPool)

    # Zones (lists of Card)
    main_deck: list[Card] = dataclass_field(default_factory=list)
    stone_deck: list[Card] = dataclass_field(default_factory=list)
    hand: list[Card] = dataclass_field(default_factory=list)
    field: list[Card] = dataclass_field(default_factory=list)
    graveyard: list[Card] = dataclass_field(default_factory=list)
    removed: list[Card] = dataclass_field(default_factory=list)
    sideboard: list[Card] = dataclass_field(default_factory=list)
    standby: list[Card] = dataclass_field(default_factory=list)  # Chant-Standby cards

    # Ruler
    ruler: Optional[Card] = None
    j_ruler: Optional[Card] = None
    has_j_ruled: bool = False  # Has performed Judgment this game

    # Turn flags
    has_called_stone: bool = False
    has_drawn_for_turn: bool = False
    has_had_recovery: bool = False  # Each player skips recovery on their first turn

    # Match state
    has_mulliganed: bool = False
    has_lost: bool = False

    def get_zone(self, zone: Zone) -> list[Card]:
        match zone:
            case Zone.MAIN_DECK: return self.main_deck
            case Zone.MAGIC_STONE_DECK: return self.stone_deck
            case Zone.HAND: return self.hand
            case Zone.FIELD: return self.field
            case Zone.GRAVEYARD: return self.graveyard
            case Zone.REMOVED: return self.removed
            case Zone.SIDEBOARD: return self.sideboard
            case Zone.STANDBY: return self.standby
            case _: return []

    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "life": self.life,
            "will_pool": self.will_pool.to_dict(),
            "deck_count": len(self.main_deck),
            "stone_deck_count": len(self.stone_deck),
            "hand": [c.to_dict() for c in self.hand],
            "field": [c.to_dict() for c in self.field],
            "graveyard_count": len(self.graveyard),
            "ruler": self.ruler.to_dict() if self.ruler else None,
            "j_ruler": self.j_ruler.to_dict() if self.j_ruler else None,
            "has_j_ruled": self.has_j_ruled,
        }


# =============================================================================
# BATTLE CONTEXT
# =============================================================================

@dataclass
class BattleContext:
    """Tracks combat state"""
    in_battle: bool = False
    step: CombatStep = CombatStep.NONE
    attacking_player: int = -1
    attacker: Optional[Card] = None
    defender: Optional[Card] = None  # None if attacking player directly
    defending_player: int = -1
    blockers: list[Card] = dataclass_field(default_factory=list)
    damage_dealt: dict[str, int] = dataclass_field(default_factory=dict)  # uid -> damage

    def clear(self):
        self.in_battle = False
        self.step = CombatStep.NONE
        self.attacking_player = -1
        self.attacker = None
        self.defender = None
        self.defending_player = -1
        self.blockers.clear()
        self.damage_dealt.clear()
