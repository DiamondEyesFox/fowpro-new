"""
Comprehensive Rules-based Ability Parser
=========================================

Parses FoW card ability text into CR-compliant ability structures.

This parser recognizes:
- CR 904: [Continuous] abilities
- CR 905: [Activate] abilities with costs
- CR 906: >>> triggered abilities (automatic abilities)
- CR 907: Will abilities
- Grimm-era keywords

References:
- CR 901.1: Ability text interpretation
- CR 903.2: Playing cards and abilities
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict, Any
from enum import Enum, auto

from ..rules import (
    AbilityType, EffectTiming, TriggerCondition, TriggerTiming,
    EffectAction, KeywordAbility, EffectDuration,
    TargetRequirement, TargetFilter, TargetZone, TargetController,
    Condition, ConditionType, ConditionOperator,
)


# =============================================================================
# PARSED STRUCTURES
# =============================================================================

@dataclass
class ParsedCost:
    """Parsed cost information."""
    tap: bool = False
    will: Dict[str, int] = field(default_factory=dict)  # attribute -> count
    life: int = 0
    sacrifice: Optional[str] = None  # What to sacrifice
    discard: int = 0
    banish: Optional[str] = None  # What to banish from where
    remove_counter: Optional[str] = None  # Counter type
    generic: int = 0  # Generic will cost
    x_cost: bool = False  # Has {X} variable cost


@dataclass
class ParsedModalChoice:
    """Parsed modal choice option."""
    effect: 'ParsedEffect'
    raw_text: str = ""


@dataclass
class ParsedIncarnation:
    """Parsed Incarnation alternative cost."""
    attributes: List[str] = field(default_factory=list)  # Required attributes to banish
    count: int = 1  # Number of resonators to banish


@dataclass
class ParsedAwakening:
    """Parsed Awakening enhanced cost."""
    will: Dict[str, int] = field(default_factory=dict)  # Extra will to pay
    x_cost: bool = False  # Has {X} in awakening cost


@dataclass
class ParsedTarget:
    """Parsed targeting information."""
    count: int = 1
    up_to: bool = False
    zone: TargetZone = TargetZone.FIELD
    controller: TargetController = TargetController.ANY
    card_types: List[str] = field(default_factory=list)
    races: List[str] = field(default_factory=list)
    attributes: List[str] = field(default_factory=list)
    name_contains: Optional[str] = None
    has_keywords: List[str] = field(default_factory=list)
    max_cost: Optional[int] = None


@dataclass
class ParsedEffect:
    """Parsed effect information."""
    action: EffectAction
    params: Dict[str, Any] = field(default_factory=dict)
    target: Optional[ParsedTarget] = None
    duration: EffectDuration = EffectDuration.INSTANT
    raw_text: str = ""


@dataclass
class ParsedAbility:
    """Parsed ability structure matching CR types."""
    ability_type: AbilityType
    name: str = ""
    cost: Optional[ParsedCost] = None
    effects: List[ParsedEffect] = field(default_factory=list)
    trigger_condition: Optional[TriggerCondition] = None
    condition: Optional[Dict[str, Any]] = None  # Parsed condition info
    timing: EffectTiming = EffectTiming.INSTANT
    is_mandatory: bool = True
    once_per_turn: bool = False
    keywords: KeywordAbility = KeywordAbility.NONE
    raw_text: str = ""
    # Modal choice support (CR 903.2)
    is_modal: bool = False
    modal_choices: List['ParsedModalChoice'] = field(default_factory=list)
    modal_count: int = 1  # "Choose one" = 1, "Choose two" = 2
    modal_upgrade_condition: Optional[str] = None  # e.g., "If you control Juliet..."
    modal_upgrade_count: int = 0  # Max choices if condition met
    # Alternative costs
    incarnation: Optional['ParsedIncarnation'] = None
    awakening: Optional['ParsedAwakening'] = None
    # Variable cost linkage
    uses_x: bool = False  # Effect references X from cost
    # J-Ruler only
    j_ruler_only: bool = False  # Only usable by J-Rulers (J-Activate)
    # Judgment
    judgment_cost: Optional['ParsedCost'] = None  # Cost for Judgment (rulers only)


# =============================================================================
# COMPREHENSIVE RULES PARSER
# =============================================================================

class CRAbilityParser:
    """
    Parser that produces CR-compliant ability structures.

    Recognizes Grimm Cluster-era patterns and keywords.
    """

    # Grimm-era keywords (CR 1100+)
    GRIMM_KEYWORDS = {
        'flying': KeywordAbility.FLYING,
        'swiftness': KeywordAbility.SWIFTNESS,
        'first strike': KeywordAbility.FIRST_STRIKE,
        'pierce': KeywordAbility.PIERCE,
        'drain': KeywordAbility.DRAIN,
        'imperishable': KeywordAbility.IMPERISHABLE,
        'barrier': KeywordAbility.BARRIER,
        'precision': KeywordAbility.PRECISION,
        'quickcast': KeywordAbility.QUICKCAST,
        'awakening': KeywordAbility.AWAKENING,
        'target attack': KeywordAbility.TARGET_ATTACK,
        'remnant': KeywordAbility.REMNANT,
        'incarnation': KeywordAbility.INCARNATION,
        'explode': KeywordAbility.EXPLODE,
        'indestructible': KeywordAbility.INDESTRUCTIBLE,
        'unblockable': KeywordAbility.UNBLOCKABLE,
    }

    # Protection text patterns mapped to keywords
    PROTECTION_PATTERNS = {
        r'cannot be destroyed': KeywordAbility.INDESTRUCTIBLE,
        r'cannot be targeted': KeywordAbility.BARRIER,
        r'cannot attack': KeywordAbility.CANNOT_ATTACK,
        r'cannot block': KeywordAbility.CANNOT_BLOCK,
        r'cannot be blocked': KeywordAbility.UNBLOCKABLE,
    }

    # Ability type markers
    ABILITY_MARKERS = {
        '[activate]': AbilityType.ACTIVATE,
        'activate': AbilityType.ACTIVATE,
        'j-activate': AbilityType.ACTIVATE,  # J-Ruler specific activate
        '[continuous]': AbilityType.CONTINUOUS,
        'continuous': AbilityType.CONTINUOUS,
        '[enter]': AbilityType.AUTOMATIC,  # Enter is a triggered ability
        'enter': AbilityType.AUTOMATIC,
        '[leave]': AbilityType.AUTOMATIC,
        'leave': AbilityType.AUTOMATIC,
        '[break]': AbilityType.AUTOMATIC,
        'break': AbilityType.AUTOMATIC,
        '[quickcast]': AbilityType.ACTIVATE,  # Quickcast modifies timing
        'quickcast': AbilityType.ACTIVATE,
        'judgment': AbilityType.ACTIVATE,
        'trigger': AbilityType.AUTOMATIC,  # CR Trigger abilities
    }

    # Trigger conditions
    TRIGGER_PATTERNS = {
        r'^\[?enter\]?': TriggerCondition.ENTER_FIELD,
        r'when.*?enters?\s+(the\s+)?field': TriggerCondition.ENTER_FIELD,
        r'when.*?comes?\s+into\s+play': TriggerCondition.ENTER_FIELD,
        r'when.*?comes?\s+into\s+a?\s*field': TriggerCondition.ENTER_FIELD,  # "comes into a field"
        r'whenever.*?comes?\s+into\s+a?\s*field': TriggerCondition.ENTER_FIELD,  # "whenever ... comes into a field"
        r'when.*?is\s+called': TriggerCondition.ENTER_FIELD,
        r'^\[?leave\]?': TriggerCondition.LEAVE_FIELD,
        r'when.*?leaves?\s+(the\s+)?field': TriggerCondition.LEAVE_FIELD,
        r'when.*?attacks?': TriggerCondition.DECLARES_ATTACK,
        r'whenever.*?attacks?': TriggerCondition.DECLARES_ATTACK,
        r'when.*?blocks?': TriggerCondition.DECLARES_BLOCK,
        r'whenever.*?blocks?': TriggerCondition.DECLARES_BLOCK,
        r'when.*?deals?\s+damage': TriggerCondition.DEALS_DAMAGE,
        r'whenever.*?deals?\s+damage': TriggerCondition.DEALS_DAMAGE,
        r'when.*?deals?\s+battle\s+damage': TriggerCondition.DEALS_BATTLE_DAMAGE,
        r'whenever.*?deals?\s+battle\s+damage': TriggerCondition.DEALS_BATTLE_DAMAGE,
        r'when.*?is\s+destroyed': TriggerCondition.DESTROYED,
        r'^\[?break\]?': TriggerCondition.DESTROYED,
        r'at\s+the\s+beginning\s+of.*?turn': TriggerCondition.TURN_START,
        r'at\s+the\s+end\s+of.*?turn': TriggerCondition.TURN_END,
        r'when.*?recovers?': TriggerCondition.RECOVERED,
        r'whenever.*?recovers?': TriggerCondition.RECOVERED,
        r'when.*?rests?': TriggerCondition.RESTED,
        r'whenever.*?rests?': TriggerCondition.RESTED,
        r'whenever\s+you\s+gain\s+life': TriggerCondition.GAINS_LIFE,
        r'whenever\s+you\s+lose\s+life': TriggerCondition.LOSES_LIFE,
        r'whenever.*?becomes?\s+rested': TriggerCondition.RESTED,  # "becomes rested"
    }

    # Will symbol mapping
    WILL_SYMBOLS = {
        'W': 'LIGHT', 'R': 'FIRE', 'U': 'WATER',
        'G': 'WIND', 'B': 'DARKNESS', 'V': 'VOID', 'M': 'MOON'
    }

    def parse(self, ability_text: str) -> List[ParsedAbility]:
        """Parse ability text into CR-compliant structures."""
        if not ability_text:
            return []

        abilities = []
        text = ability_text.strip()

        # Check for modal ability first (takes precedence)
        modal_ability = self._parse_modal_ability(text)
        if modal_ability:
            abilities.append(modal_ability)

        # Check for keywords
        keywords = self._extract_keywords(text)
        if keywords != KeywordAbility.NONE:
            abilities.append(ParsedAbility(
                ability_type=AbilityType.CONTINUOUS,  # Keywords are continuous
                name="Keywords",
                keywords=keywords,
                raw_text=text,
            ))

        # Check for Incarnation alternative cost
        incarnation = self._parse_incarnation(text)

        # Check for Awakening enhanced cost
        awakening = self._parse_awakening(text)

        # Split by newlines and markers
        segments = self._split_into_segments(text)

        for segment_type, segment_text in segments:
            ability = self._parse_segment(segment_type, segment_text)
            if ability:
                # Attach incarnation/awakening to the first non-keyword ability
                if incarnation and not ability.keywords:
                    ability.incarnation = incarnation
                    incarnation = None  # Only attach once
                if awakening and not ability.keywords:
                    ability.awakening = awakening
                    awakening = None  # Only attach once
                abilities.append(ability)

        # If incarnation/awakening wasn't attached (only keywords found),
        # create a dedicated ability for it
        if incarnation or awakening:
            special_ability = ParsedAbility(
                ability_type=AbilityType.CONTINUOUS,
                name="Incarnation/Awakening",
                incarnation=incarnation,
                awakening=awakening,
                raw_text=text,
            )
            abilities.append(special_ability)

        return abilities

    def _extract_keywords(self, text: str) -> KeywordAbility:
        """Extract keyword abilities from text."""
        keywords = KeywordAbility.NONE
        text_lower = text.lower()

        # Check for explicit keywords
        for keyword, flag in self.GRIMM_KEYWORDS.items():
            # Look for keyword at word boundaries
            pattern = rf'\b{re.escape(keyword)}\b'
            if re.search(pattern, text_lower):
                keywords |= flag

        # Check for protection text patterns
        for pattern, flag in self.PROTECTION_PATTERNS.items():
            if re.search(pattern, text_lower):
                keywords |= flag

        return keywords

    def _split_into_segments(self, text: str) -> List[Tuple[AbilityType, str]]:
        """Split text into ability segments."""
        segments = []
        lines = text.split('\n')

        for line in lines:
            line = line.strip()
            if not line:
                continue

            line_lower = line.lower()

            # Check for ability markers at start
            marker_found = False
            for marker, ability_type in self.ABILITY_MARKERS.items():
                if line_lower.startswith(marker):
                    content = line[len(marker):].strip()
                    # Handle colon after marker
                    if content.startswith(':'):
                        content = content[1:].strip()
                    segments.append((ability_type, content))
                    marker_found = True
                    break

                # Check for bracketed markers anywhere
                if marker.startswith('[') and marker in line_lower:
                    pos = line_lower.find(marker)
                    content = line[pos + len(marker):].strip()
                    if content.startswith(':'):
                        content = content[1:].strip()
                    segments.append((ability_type, content))
                    marker_found = True
                    break

            if not marker_found:
                # Check for >>> trigger pattern
                if '>>>' in line or '»' in line:
                    segments.append((AbilityType.AUTOMATIC, line))
                # Check for will production (indicates Will ability)
                elif re.search(r'produce\s*\{[wrugbvm]\}', line_lower):
                    segments.append((AbilityType.WILL, line))
                # Check for cost pattern (e.g., "{1}{X},{Rest}:" indicates activated)
                elif re.search(r'^\s*(?:\{[^}]+\}\s*,?\s*)+\s*:\s*', line):
                    segments.append((AbilityType.ACTIVATE, line))
                # Check for text-based cost pattern "Rest/Tap/Sacrifice X: Effect"
                elif re.search(r'^(?:rest|tap|sacrifice|banish|pay|discard)\s+.+?:\s*', line_lower):
                    segments.append((AbilityType.ACTIVATE, line))
                else:
                    # Likely static or continuous
                    segments.append((AbilityType.CONTINUOUS, line))

        return segments

    def _parse_segment(self, ability_type: AbilityType, text: str) -> Optional[ParsedAbility]:
        """Parse a single ability segment."""
        text_lower = text.lower()

        # Re-classify CONTINUOUS with "whenever"/"when" as AUTOMATIC (triggered)
        if ability_type == AbilityType.CONTINUOUS:
            if re.search(r'\bwhenever\b|\bwhen\s+this\b|\bwhen\s+a\b|\bwhen\s+an?\b', text_lower):
                ability_type = AbilityType.AUTOMATIC

        ability = ParsedAbility(
            ability_type=ability_type,
            raw_text=text,
        )

        # Check for J-Activate (J-Ruler only ability)
        if text_lower.startswith('j-activate'):
            ability.j_ruler_only = True

        # Parse trigger condition for automatic abilities
        if ability_type == AbilityType.AUTOMATIC:
            ability.trigger_condition = self._parse_trigger_condition(text_lower)

        # Handle >>> separator
        effect_text = text
        condition_text = ""
        if '>>>' in text:
            parts = text.split('>>>', 1)
            condition_text = parts[0].strip()
            effect_text = parts[1].strip() if len(parts) > 1 else text
            ability.trigger_condition = self._parse_trigger_condition(condition_text.lower())
        elif '»' in text:
            parts = text.split('»', 1)
            condition_text = parts[0].strip()
            effect_text = parts[1].strip() if len(parts) > 1 else text
            ability.trigger_condition = self._parse_trigger_condition(condition_text.lower())

        # Parse cost (text before : or "Pay{...}" pattern)
        if ':' in effect_text and ability_type in (AbilityType.ACTIVATE, AbilityType.WILL):
            parts = effect_text.split(':', 1)
            ability.cost = self._parse_cost(parts[0].strip())
            effect_text = parts[1].strip() if len(parts) > 1 else effect_text
        # Handle "J-Activate Pay{...}" without colon (effect is implicit)
        elif 'pay{' in text_lower:
            pay_match = re.search(r'pay\s*((?:\{[^}]+\}\s*)+)', text_lower)
            if pay_match:
                ability.cost = self._parse_cost(pay_match.group(1))
            # Check for additional costs after comma
            comma_match = re.search(r'pay\s*(?:\{[^}]+\}\s*)+\s*,\s*(.+)', text_lower)
            if comma_match:
                additional = comma_match.group(1).strip()
                # Parse discard, sacrifice, etc. as additional cost
                if 'discard' in additional:
                    if not ability.cost:
                        ability.cost = ParsedCost()
                    ability.cost.discard = 1

        # Parse effects
        ability.effects = self._parse_effects(effect_text.lower())

        # Also check for X-based effects
        if ability.cost and ability.cost.x_cost:
            x_effects = self._parse_x_cost_effect(effect_text, ability.cost)
            ability.effects.extend(x_effects)
            ability.uses_x = True

        # Set timing
        if ability_type == AbilityType.WILL:
            ability.timing = EffectTiming.WILL_SPEED
        elif ability_type == AbilityType.ACTIVATE:
            # Check for quickcast
            if 'quickcast' in text_lower:
                ability.timing = EffectTiming.INSTANT
            else:
                ability.timing = EffectTiming.MAIN_TIMING

        # Check for once per turn
        if 'once per turn' in text_lower or 'only once per turn' in text_lower:
            ability.once_per_turn = True

        # Check for optional
        if 'you may' in text_lower:
            ability.is_mandatory = False

        # Return ability if it has meaningful content:
        # - effects parsed
        # - trigger condition detected (for triggered abilities)
        # - cost parsed (for activated abilities)
        # - j_ruler_only flag (J-Activate)
        has_content = (
            ability.effects or
            ability.trigger_condition or
            ability.cost or
            ability.j_ruler_only
        )
        return ability if has_content else None

    def _parse_trigger_condition(self, text: str) -> Optional[TriggerCondition]:
        """Parse trigger condition from text."""
        for pattern, condition in self.TRIGGER_PATTERNS.items():
            if re.search(pattern, text, re.IGNORECASE):
                return condition
        return None

    def _parse_cost(self, cost_text: str) -> ParsedCost:
        """Parse cost string into structured cost."""
        cost = ParsedCost()
        text_lower = cost_text.lower()

        # Tap/Rest cost
        if '{rest}' in text_lower or 'rest' in text_lower:
            cost.tap = True

        # Will costs - {X} where X is number, will symbol, or variable X
        will_matches = re.findall(r'\{(\d+|[WRUGBVMX])\}', cost_text, re.IGNORECASE)
        for symbol in will_matches:
            symbol_upper = symbol.upper()
            if symbol_upper == 'X':
                cost.x_cost = True
            elif symbol.isdigit():
                cost.generic = int(symbol)
            else:
                attr = self.WILL_SYMBOLS.get(symbol_upper, 'VOID')
                cost.will[attr] = cost.will.get(attr, 0) + 1

        # Life payment
        life_match = re.search(r'pay\s+(\d+)\s+life', text_lower)
        if life_match:
            cost.life = int(life_match.group(1))

        # Sacrifice
        sac_match = re.search(r'sacrifice\s+(an?|this)\s+(\w+)', text_lower)
        if sac_match:
            cost.sacrifice = sac_match.group(2)

        # Discard
        discard_match = re.search(r'discard\s+(\d+|a|an)\s+cards?', text_lower)
        if discard_match:
            count = discard_match.group(1)
            cost.discard = 1 if count in ('a', 'an') else int(count)

        # Banish from graveyard
        banish_match = re.search(r'banish\s+(an?|this)\s+(\w+)\s+from.*?graveyard', text_lower)
        if banish_match:
            cost.banish = banish_match.group(2)

        # Remove counter
        counter_match = re.search(r'remove\s+.*?(\w+)\s+counter', text_lower)
        if counter_match:
            cost.remove_counter = counter_match.group(1)

        # Multi-tap cost "Rest two/three X you control:"
        multi_tap_match = re.search(r'rest\s+(two|three|\d+)\s+(?:recovered\s+)?(\w+)', text_lower)
        if multi_tap_match:
            cost.tap = True  # Mark as tap cost
            # Store count in sacrifice field as workaround
            count_word = multi_tap_match.group(1)
            word_to_num = {'two': 2, 'three': 3}
            count = word_to_num.get(count_word, int(count_word) if count_word.isdigit() else 2)
            cost.sacrifice = f"tap_{count}_{multi_tap_match.group(2)}"

        return cost

    def _parse_effects(self, text: str) -> List[ParsedEffect]:
        """Parse effects from effect text."""
        effects = []

        # Will production
        will_match = re.search(r'produce\s*\{([wrugbvm])\}(?:\s*(?:or|and)\s*\{([wrugbvm])\})?', text)
        if will_match:
            colors = [will_match.group(1).upper()]
            if will_match.group(2):
                colors.append(will_match.group(2).upper())
            effects.append(ParsedEffect(
                action=EffectAction.PRODUCE_WILL,
                params={'colors': [self.WILL_SYMBOLS.get(c, 'VOID') for c in colors]},
                raw_text=will_match.group(0),
            ))

        # Draw cards
        draw_match = re.search(r'draw\s+(\d+|a|an)\s+cards?', text)
        if draw_match:
            count = draw_match.group(1)
            effects.append(ParsedEffect(
                action=EffectAction.DRAW,
                params={'count': 1 if count in ('a', 'an') else int(count)},
                raw_text=draw_match.group(0),
            ))

        # Deal damage - "deals X damage to target"
        damage_match = re.search(r'deals?\s+(\d+)\s+damage\s+to\s+(target\s+)?(.+?)(?:\.|$)', text)
        if damage_match:
            target = self._parse_target_phrase(damage_match.group(3))
            effects.append(ParsedEffect(
                action=EffectAction.DEAL_DAMAGE,
                params={'amount': int(damage_match.group(1))},
                target=target,
                raw_text=damage_match.group(0),
            ))

        # "This card deals X damage" pattern
        this_damage_match = re.search(r'this\s+card\s+deals?\s+(\d+)\s+damage\s+to\s+(target\s+)?(.+?)(?:\.|$)', text)
        if this_damage_match:
            target = self._parse_target_phrase(this_damage_match.group(3))
            effects.append(ParsedEffect(
                action=EffectAction.DEAL_DAMAGE,
                params={'amount': int(this_damage_match.group(1)), 'source': 'self'},
                target=target,
                raw_text=this_damage_match.group(0),
            ))

        # Destroy
        destroy_match = re.search(r'destroy\s+(target\s+)?(.+?)(?:\.|$)', text)
        if destroy_match:
            target = self._parse_target_phrase(destroy_match.group(2))
            effects.append(ParsedEffect(
                action=EffectAction.DESTROY,
                target=target,
                raw_text=destroy_match.group(0),
            ))

        # Return to hand
        if re.search(r'return.*?to.*?hand', text):
            effects.append(ParsedEffect(
                action=EffectAction.RETURN_TO_HAND,
                raw_text="return to hand",
            ))

        # Put [target] into hand (from graveyard, etc.)
        put_hand_match = re.search(r'put\s+(target\s+)?(.+?)\s+(?:from.*?\s+)?into\s+(?:your\s+|its owner\'?s?\s+)?hand', text)
        if put_hand_match and 'counter' not in text:  # Exclude "put counter"
            target = self._parse_target_phrase(put_hand_match.group(2) if put_hand_match.group(2) else '')
            effects.append(ParsedEffect(
                action=EffectAction.RETURN_TO_HAND,
                params={'from_zone': 'graveyard'},  # Usually from graveyard
                target=target,
                raw_text=put_hand_match.group(0),
            ))

        # Move onto (Addition movement)
        move_match = re.search(r'move\s+(target\s+)?(.+?)\s+onto\s+', text)
        if move_match:
            target = self._parse_target_phrase(move_match.group(2) if move_match.group(2) else '')
            effects.append(ParsedEffect(
                action=EffectAction.GRANT_ABILITY,  # Moving an addition is like re-attaching
                params={'move': True},
                target=target,
                raw_text=move_match.group(0),
            ))

        # Remove from game / banish
        remove_match = re.search(r'remove\s+(target\s+)?(.+?)\s+from\s+the\s+game', text)
        if remove_match:
            target = self._parse_target_phrase(remove_match.group(2) if remove_match.group(2) else '')
            effects.append(ParsedEffect(
                action=EffectAction.REMOVE_FROM_GAME,
                target=target,
                raw_text=remove_match.group(0),
            ))

        # Gain life
        life_gain_match = re.search(r'gain\s+(\d+)\s+life', text)
        if life_gain_match:
            effects.append(ParsedEffect(
                action=EffectAction.GAIN_LIFE,
                params={'amount': int(life_gain_match.group(1))},
                raw_text=life_gain_match.group(0),
            ))

        # Lose life
        life_lose_match = re.search(r'lose\s+(\d+)\s+life', text)
        if life_lose_match:
            effects.append(ParsedEffect(
                action=EffectAction.LOSE_LIFE,
                params={'amount': int(life_lose_match.group(1))},
                raw_text=life_lose_match.group(0),
            ))

        # Stat buff/debuff
        buff_match = re.search(r'gains?\s+\[?\+?(-?\d+)/\+?(-?\d+)\]?', text)
        if buff_match:
            atk = int(buff_match.group(1))
            def_ = int(buff_match.group(2))
            effects.append(ParsedEffect(
                action=EffectAction.MODIFY_ATK if atk != 0 else EffectAction.MODIFY_DEF,
                params={'atk': atk, 'def': def_},
                duration=self._parse_duration(text),
                raw_text=buff_match.group(0),
            ))

        # Rest/Recover target
        if re.search(r'rest\s+target', text):
            effects.append(ParsedEffect(
                action=EffectAction.REST,
                raw_text="rest target",
            ))
        if re.search(r'recover\s+target', text):
            effects.append(ParsedEffect(
                action=EffectAction.RECOVER,
                raw_text="recover target",
            ))

        # Cancel spell
        if re.search(r'cancel\s+target\s+spell', text):
            effects.append(ParsedEffect(
                action=EffectAction.CANCEL,
                raw_text="cancel target spell",
            ))

        # Add counters
        counter_match = re.search(r'put\s+(?:a|an|\d+)\s+(\w+)\s+counter', text)
        if counter_match:
            effects.append(ParsedEffect(
                action=EffectAction.ADD_COUNTER,
                params={'counter_type': counter_match.group(1)},
                raw_text=counter_match.group(0),
            ))

        # Remove counters
        remove_counter_match = re.search(r'remove\s+(?:a|an|\d+)\s+(\w+)\s+counter', text)
        if remove_counter_match:
            effects.append(ParsedEffect(
                action=EffectAction.REMOVE_COUNTER,
                params={'counter_type': remove_counter_match.group(1)},
                raw_text=remove_counter_match.group(0),
            ))

        # Search deck
        if re.search(r'search.*?deck.*?put.*?hand', text):
            effects.append(ParsedEffect(
                action=EffectAction.SEARCH,
                params={'destination': 'hand'},
                raw_text="search deck",
            ))

        # Grant keyword
        keyword_match = re.search(r'gains?\s+\[?(\w+(?:\s+\w+)?)\]?(?:\s+until|\.)', text)
        if keyword_match:
            keyword = keyword_match.group(1).lower()
            if keyword in self.GRIMM_KEYWORDS:
                effects.append(ParsedEffect(
                    action=EffectAction.GRANT_KEYWORD,
                    params={'keyword': self.GRIMM_KEYWORDS[keyword]},
                    duration=self._parse_duration(text),
                    raw_text=keyword_match.group(0),
                ))

        # Banish (zone -> removed from game)
        if re.search(r'banish(?:es)?\s+(?:a|one|an?|another)\s+', text):
            effects.append(ParsedEffect(
                action=EffectAction.BANISH,
                raw_text="banish",
            ))

        # "Your opponent banishes" - forced banish
        if re.search(r'(?:your\s+)?opponent\s+banish(?:es)?', text):
            effects.append(ParsedEffect(
                action=EffectAction.BANISH,
                params={'controller': 'opponent'},
                raw_text="opponent banishes",
            ))

        # Put resonator from graveyard into field
        gy_to_field_match = re.search(r'put\s+(?:a\s+|an?\s+)?(\w+)?\s*resonator\s+from\s+(?:your\s+)?graveyard\s+into\s+(?:your\s+)?field', text)
        if gy_to_field_match:
            effects.append(ParsedEffect(
                action=EffectAction.PUT_INTO_FIELD,
                params={'from_zone': 'graveyard', 'card_type': 'resonator'},
                raw_text=gy_to_field_match.group(0),
            ))

        # Discard cards
        discard_match = re.search(r'discard(?:s)?\s+(?:all\s+cards|two\s+cards|(\d+)\s+cards?|a\s+card)', text)
        if discard_match:
            count = discard_match.group(1)
            params = {'all': 'all cards' in text, 'count': int(count) if count and count.isdigit() else 1}
            effects.append(ParsedEffect(
                action=EffectAction.DISCARD,
                params=params,
                raw_text=discard_match.group(0),
            ))

        # Gain control
        if re.search(r'gain\s+control\s+of', text):
            effects.append(ParsedEffect(
                action=EffectAction.GAIN_CONTROL,
                raw_text="gain control",
            ))

        # "Cannot play/summon" restrictions
        if re.search(r'cannot\s+play|cannot\s+summon', text):
            effects.append(ParsedEffect(
                action=EffectAction.REMOVE_ABILITY,  # Represents a restriction
                params={'restriction': True},
                raw_text="cannot play/summon",
            ))

        # Scaling stat gain "gains +X/+Y for each"
        scale_match = re.search(r'gains?\s*\[?\+?(\d+)/\+?(\d+)\]?\s+for\s+each', text)
        if scale_match:
            effects.append(ParsedEffect(
                action=EffectAction.MODIFY_ATK,
                params={'atk_per': int(scale_match.group(1)), 'def_per': int(scale_match.group(2)), 'scaling': True},
                raw_text=scale_match.group(0),
            ))

        # "Must attack/block if able"
        if re.search(r'must\s+attack\s+if\s+able', text):
            effects.append(ParsedEffect(
                action=EffectAction.GRANT_ABILITY,
                params={'force_attack': True},
                raw_text="must attack if able",
            ))
        if re.search(r'must\s+block\s+if\s+able', text):
            effects.append(ParsedEffect(
                action=EffectAction.GRANT_ABILITY,
                params={'force_block': True},
                raw_text="must block if able",
            ))

        # "Loses all abilities"
        if re.search(r'loses?\s+all\s+abilities', text):
            effects.append(ParsedEffect(
                action=EffectAction.REMOVE_ABILITY,
                params={'all': True},
                raw_text="loses all abilities",
            ))

        # "Reveal top card"
        if re.search(r'reveal\s+(?:the\s+)?top\s+card', text):
            effects.append(ParsedEffect(
                action=EffectAction.REVEAL,
                params={'from_top': True},
                raw_text="reveal top card",
            ))

        # "Deals damage equal to ATK"
        if re.search(r'deals?\s+damage\s+equal\s+to\s+(?:its\s+)?atk', text):
            effects.append(ParsedEffect(
                action=EffectAction.DEAL_DAMAGE,
                params={'equal_to_atk': True},
                raw_text="deals damage equal to ATK",
            ))

        # Draw cards equal to X
        if re.search(r'draw\s+cards?\s+equal\s+to', text):
            effects.append(ParsedEffect(
                action=EffectAction.DRAW,
                params={'variable': True},
                raw_text="draw cards equal to",
            ))

        # Prevent damage patterns
        if re.search(r'prevent\s+(?:all\s+)?(?:battle\s+)?damage|prevent\s+(?:the\s+next\s+)?(\d+)\s+', text):
            effects.append(ParsedEffect(
                action=EffectAction.PREVENT_DAMAGE,
                params={'all': 'all' in text, 'battle_only': 'battle damage' in text},
                raw_text="prevent damage",
            ))

        # Damage replacement "If damage would be dealt"
        if re.search(r'if\s+(?:this\s+card|damage)\s+would\s+(?:deal|be dealt)\s+damage', text):
            effects.append(ParsedEffect(
                action=EffectAction.MODIFY_ATK,
                params={'replacement': True},
                raw_text="damage replacement",
            ))

        # "When target X is put into graveyard"
        if re.search(r'when\s+target\s+.*?is\s+put\s+into\s+(?:a\s+)?graveyard', text):
            effects.append(ParsedEffect(
                action=EffectAction.SEARCH,  # Often triggers a search
                params={'on_death': True},
                raw_text="when put into graveyard",
            ))

        # Change target of spell
        if re.search(r'change\s+the\s+target\s+of', text):
            effects.append(ParsedEffect(
                action=EffectAction.GRANT_ABILITY,  # Redirect is a special ability
                params={'redirect': True},
                raw_text="change target",
            ))

        # Put multiple things from graveyard to field
        if re.search(r'put\s+(?:up\s+to\s+)?(?:one\s+)?target\s+.*?from\s+(?:your\s+)?graveyard\s+into\s+(?:your\s+)?field', text):
            effects.append(ParsedEffect(
                action=EffectAction.PUT_INTO_FIELD,
                params={'from_zone': 'graveyard'},
                raw_text="put from graveyard into field",
            ))

        # Double damage
        if re.search(r'deals?\s+double\s+(?:that\s+much\s+)?(?:damage)?', text):
            effects.append(ParsedEffect(
                action=EffectAction.MODIFY_ATK,
                params={'double_damage': True},
                raw_text="deals double damage",
            ))

        # "As you/your opponent plays"
        if re.search(r'as\s+(?:you|your\s+opponent)\s+play', text):
            effects.append(ParsedEffect(
                action=EffectAction.GRANT_ABILITY,
                params={'play_restriction': True},
                raw_text="as you play",
            ))

        # Put on top of deck
        if re.search(r'put\s+(?:target\s+)?.*?on\s+top\s+of\s+(?:its\s+)?owner\'?s?\s+(?:main\s+)?deck', text):
            effects.append(ParsedEffect(
                action=EffectAction.PUT_ON_TOP_OF_DECK,
                raw_text="put on top of deck",
            ))

        # Prevent next damage (by/to)
        if re.search(r'prevent\s+the\s+next\s+damage', text):
            effects.append(ParsedEffect(
                action=EffectAction.PREVENT_DAMAGE,
                params={'next_only': True},
                raw_text="prevent next damage",
            ))

        # Damage redirection "dealt to X, it's dealt to Y instead"
        if re.search(r'damage\s+.*?dealt\s+to\s+.*?instead', text):
            effects.append(ParsedEffect(
                action=EffectAction.PREVENT_DAMAGE,
                params={'redirect': True},
                raw_text="damage redirection",
            ))

        # Mutual damage "deal damage to each other"
        if re.search(r'deal\s+damage\s+.*?to\s+each\s+other', text):
            effects.append(ParsedEffect(
                action=EffectAction.DEAL_DAMAGE,
                params={'mutual': True},
                raw_text="deal damage to each other",
            ))

        # Conditional self-banish "Banish this card if"
        if re.search(r'banish\s+this\s+card\s+if', text):
            effects.append(ParsedEffect(
                action=EffectAction.BANISH,
                params={'self': True, 'conditional': True},
                raw_text="banish this card if",
            ))

        # Grant ability to other permanents "X you control gain"
        if re.search(r'(?:stones?|resonators?)\s+you\s+control\s+gain', text):
            effects.append(ParsedEffect(
                action=EffectAction.GRANT_ABILITY,
                params={'to_others': True},
                raw_text="grant ability to others",
            ))

        # "don't recover during recovery phase"
        if re.search(r"don'?t\s+recover\s+during\s+recovery\s+phase", text):
            effects.append(ParsedEffect(
                action=EffectAction.REMOVE_ABILITY,
                params={'prevent_recovery': True},
                raw_text="prevent recovery",
            ))

        # "When added resonator is put into graveyard"
        if re.search(r'when\s+added\s+resonator\s+is\s+put\s+into\s+(?:a\s+)?graveyard', text):
            effects.append(ParsedEffect(
                action=EffectAction.PUT_INTO_FIELD,
                params={'on_added_death': True},
                raw_text="when added resonator dies",
            ))

        # "put into that zone this turn" - temporal graveyard targeting
        if re.search(r'(?:from\s+a?\s+)?graveyard\s+that\s+was\s+put\s+into\s+(?:that\s+zone|.*?graveyard)\s+.*?this\s+turn', text):
            effects.append(ParsedEffect(
                action=EffectAction.PUT_INTO_FIELD,
                params={'from_zone': 'graveyard', 'this_turn': True},
                raw_text="put from graveyard this turn",
            ))

        # ATK/DEF equal to X - dynamic stat
        if re.search(r"(?:atk|def)\s+is\s+equal\s+to", text):
            effects.append(ParsedEffect(
                action=EffectAction.SET_ATK,
                params={'dynamic': True},
                raw_text="stat equal to",
            ))

        # "At the end of your turn" trigger
        if re.search(r'at\s+the\s+end\s+of\s+(?:your|each)\s+turn', text):
            effects.append(ParsedEffect(
                action=EffectAction.GRANT_ABILITY,
                params={'end_of_turn_trigger': True},
                raw_text="end of turn trigger",
            ))

        # "becomes targeted by" trigger
        if re.search(r'becomes?\s+targeted\s+by', text):
            effects.append(ParsedEffect(
                action=EffectAction.GRANT_ABILITY,
                params={'on_targeted': True},
                raw_text="becomes targeted",
            ))

        # Life gain equal to damage
        if re.search(r'gain\s+life\s+equal\s+to\s+(?:the\s+)?damage', text):
            effects.append(ParsedEffect(
                action=EffectAction.GAIN_LIFE,
                params={'equal_to_damage': True},
                raw_text="gain life equal to damage",
            ))

        # "chooses a number secretly"
        if re.search(r'chooses?\s+(?:a\s+)?number\s+secretly', text):
            effects.append(ParsedEffect(
                action=EffectAction.REVEAL,
                params={'secret_choice': True},
                raw_text="choose number secretly",
            ))

        # "deals X damage...where X is" - variable damage from game state
        if re.search(r'deals?\s+x\s+damage.*?where\s+x\s+is', text):
            effects.append(ParsedEffect(
                action=EffectAction.DEAL_DAMAGE,
                params={'variable_x': True},
                raw_text="deals X damage where X is",
            ))

        # "Produce one will of any attribute"
        if re.search(r'produce\s+(?:one\s+)?will\s+of\s+any\s+attribute', text):
            effects.append(ParsedEffect(
                action=EffectAction.PRODUCE_WILL,
                params={'any_color': True},
                raw_text="produce any will",
            ))

        return effects

    def _parse_target_phrase(self, phrase: str) -> ParsedTarget:
        """Parse a target description phrase."""
        target = ParsedTarget()
        phrase_lower = phrase.lower().strip()

        # Controller
        if 'opponent' in phrase_lower:
            target.controller = TargetController.OPPONENT
        elif 'you control' in phrase_lower or 'your' in phrase_lower:
            target.controller = TargetController.YOU

        # Card types
        if 'resonator' in phrase_lower:
            target.card_types.append('resonator')
        if 'j/resonator' in phrase_lower or 'j-resonator' in phrase_lower:
            target.card_types.extend(['resonator', 'j_ruler'])
        if 'spell' in phrase_lower:
            target.card_types.append('spell')
        if 'magic stone' in phrase_lower or 'stone' in phrase_lower:
            target.card_types.append('magic_stone')
        if 'addition' in phrase_lower:
            target.card_types.append('addition')
        if 'player' in phrase_lower:
            target.card_types.append('player')

        # Zone
        if 'graveyard' in phrase_lower:
            target.zone = TargetZone.GRAVEYARD
        elif 'chase' in phrase_lower:
            target.zone = TargetZone.CHASE
        elif 'hand' in phrase_lower:
            target.zone = TargetZone.HAND

        # Count
        up_to_match = re.search(r'up to (\d+)', phrase_lower)
        if up_to_match:
            target.count = int(up_to_match.group(1))
            target.up_to = True

        count_match = re.search(r'(\d+) target', phrase_lower)
        if count_match:
            target.count = int(count_match.group(1))

        # Cost restriction
        cost_match = re.search(r'total cost (\d+) or less', phrase_lower)
        if cost_match:
            target.max_cost = int(cost_match.group(1))

        return target

    def _parse_duration(self, text: str) -> EffectDuration:
        """Parse effect duration from text."""
        if 'until end of turn' in text:
            return EffectDuration.UNTIL_END_OF_TURN
        elif 'this turn' in text:
            return EffectDuration.UNTIL_END_OF_TURN
        elif 'as long as' in text or 'while' in text:
            return EffectDuration.WHILE_ON_FIELD
        else:
            return EffectDuration.INSTANT

    def _parse_modal_ability(self, text: str) -> Optional[ParsedAbility]:
        """Parse modal 'Choose one/two' abilities (CR 903.2)."""
        text_lower = text.lower()

        # Check for modal pattern
        modal_match = re.search(
            r'choose\s+(one|two|three)\.?\s*'
            r'(?:if\s+([^-]+?),?\s*choose\s+(?:up\s+to\s+)?(\w+)\s+instead)?'
            r'\s*[-–—]?\s*(.+)',
            text_lower, re.DOTALL
        )
        if not modal_match:
            return None

        base_count_word = modal_match.group(1)
        upgrade_condition = modal_match.group(2)
        upgrade_count_word = modal_match.group(3)
        choices_text = modal_match.group(4)

        # Convert word to number
        word_to_num = {'one': 1, 'two': 2, 'three': 3}
        modal_count = word_to_num.get(base_count_word, 1)
        upgrade_count = word_to_num.get(upgrade_count_word, 0) if upgrade_count_word else 0

        # Split choices by "; or", ": or", "; ", or standalone "or" at boundaries
        # Handles: "X; or Y; or Z" and "X: or Y; or Z"
        choices_raw = re.split(r';\s*or\s+|:\s*or\s+|;\s+or\s+|;\s+', choices_text)
        choices = []

        for choice_text in choices_raw:
            choice_text = choice_text.strip()
            if not choice_text:
                continue
            # Parse each choice as an effect
            effects = self._parse_effects(choice_text)
            if effects:
                choices.append(ParsedModalChoice(
                    effect=effects[0],
                    raw_text=choice_text,
                ))

        if not choices:
            return None

        ability = ParsedAbility(
            ability_type=AbilityType.ACTIVATE,  # Modal spells are usually activated
            name="Modal Choice",
            is_modal=True,
            modal_choices=choices,
            modal_count=modal_count,
            raw_text=text,
        )

        if upgrade_condition:
            ability.modal_upgrade_condition = upgrade_condition.strip()
            ability.modal_upgrade_count = upgrade_count

        return ability

    def _parse_incarnation(self, text: str) -> Optional[ParsedIncarnation]:
        """Parse Incarnation alternative cost.

        Examples:
        - Incarnation{R} - banish one fire resonator
        - Incarnation{B},{B} or{R} - banish one darkness and one fire/darkness
        """
        text_lower = text.lower()

        # Basic pattern: Incarnation{X}
        incarnation_match = re.search(
            r'incarnation\s*\{([wrugbv])\}'
            r'(?:\s*,?\s*\{([wrugbv])\}\s*(?:or\s*\{([wrugbv])\})?)?',
            text_lower
        )
        if not incarnation_match:
            return None

        attributes = []
        attr1 = incarnation_match.group(1)
        if attr1:
            attributes.append(self.WILL_SYMBOLS.get(attr1.upper(), 'VOID'))

        attr2 = incarnation_match.group(2)
        if attr2:
            attributes.append(self.WILL_SYMBOLS.get(attr2.upper(), 'VOID'))

        attr3 = incarnation_match.group(3)
        if attr3:
            # "or" means choice - store both options
            attributes.append(self.WILL_SYMBOLS.get(attr3.upper(), 'VOID'))

        return ParsedIncarnation(
            attributes=attributes,
            count=len([a for a in [attr1, attr2] if a]),  # Count of required banishes
        )

    def _parse_awakening(self, text: str) -> Optional[ParsedAwakening]:
        """Parse Awakening enhanced cost.

        Examples:
        - Awakening{W}{W} - pay extra white will for enhanced effect
        - Awakening{X} - pay X extra for variable effect
        """
        text_lower = text.lower()

        # Pattern: Awakening{...} (may have multiple {} and optional colon after)
        awakening_match = re.search(r'awakening\s*((?:\{[^}]+\}\s*)+)', text_lower)
        if not awakening_match:
            return None

        cost_part = awakening_match.group(1)
        will = {}
        x_cost = False

        # Extract will symbols
        will_matches = re.findall(r'\{(\d+|[wrugbvmx])\}', cost_part, re.IGNORECASE)
        for symbol in will_matches:
            symbol_upper = symbol.upper()
            if symbol_upper == 'X':
                x_cost = True
            elif symbol.isdigit():
                will['GENERIC'] = will.get('GENERIC', 0) + int(symbol)
            else:
                attr = self.WILL_SYMBOLS.get(symbol_upper, 'VOID')
                will[attr] = will.get(attr, 0) + 1

        return ParsedAwakening(
            will=will,
            x_cost=x_cost,
        )

    def _parse_judgment_cost(self, text: str) -> Optional[ParsedCost]:
        """
        Parse Judgment cost from ruler ability text.

        Judgment is indicated by "J-Activate Pay{...}" on the Ruler side.
        The cost pattern is the same as regular activated abilities.
        """
        text_lower = text.lower()

        # Look for J-Activate Pay pattern
        j_activate_match = re.search(
            r'j-activate\s+pay\s*((?:\{[^}]+\}\s*)+)',
            text_lower
        )
        if j_activate_match:
            return self._parse_cost(j_activate_match.group(1))

        return None

    def _parse_x_cost_effect(self, text: str, cost: Optional[ParsedCost]) -> List[ParsedEffect]:
        """Parse effects that reference X from the cost."""
        effects = []
        text_lower = text.lower()

        # Check if cost has X
        has_x_cost = cost and cost.x_cost

        # X damage pattern
        x_damage_match = re.search(r'deal\s+x\s+damage\s+to\s+(target\s+)?(\w+)', text_lower)
        if x_damage_match:
            target = self._parse_target_phrase(x_damage_match.group(2))
            effects.append(ParsedEffect(
                action=EffectAction.DEAL_DAMAGE,
                params={'amount': 'X', 'x_variable': True},
                target=target,
                raw_text=x_damage_match.group(0),
            ))

        # X targets pattern (rest X target resonators)
        x_targets_match = re.search(r'rest\s+x\s+target\s+(\w+)', text_lower)
        if x_targets_match:
            target = self._parse_target_phrase(x_targets_match.group(1))
            target.count = -1  # -1 indicates X
            effects.append(ParsedEffect(
                action=EffectAction.REST,
                params={'count': 'X', 'x_variable': True},
                target=target,
                raw_text=x_targets_match.group(0),
            ))

        # Cost X or less pattern
        cost_x_match = re.search(r'(?:total\s+)?cost\s+x\s+or\s+less', text_lower)
        if cost_x_match:
            # This modifies a target restriction, not an effect
            pass

        # Put resonator with cost X or less
        put_x_match = re.search(
            r'put\s+(?:a\s+)?resonator\s+with\s+(?:total\s+)?cost\s+x\s+or\s+less',
            text_lower
        )
        if put_x_match:
            effects.append(ParsedEffect(
                action=EffectAction.PUT_INTO_FIELD,
                params={'from_zone': 'hand', 'max_cost': 'X', 'x_variable': True},
                raw_text=put_x_match.group(0),
            ))

        return effects


# Global parser instance
cr_parser = CRAbilityParser()


def parse_ability_text_cr(text: str) -> List[ParsedAbility]:
    """Convenience function to parse ability text using CR parser."""
    return cr_parser.parse(text)
