"""
Ability Text Parser
===================

Parses FoW card ability text into structured effect definitions.
Used by the script generator to create card scripts automatically.
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict, Any
from enum import Enum, auto


class AbilityType(Enum):
    """Types of abilities in FoW"""
    ACTIVATE = auto()       # [Activate] - Tap abilities
    CONTINUOUS = auto()     # [Continuous] - Always-on effects
    ENTER = auto()          # [Enter] - When enters field
    LEAVE = auto()          # [Leave] / When leaves field
    TRIGGER = auto()        # >>> Triggered abilities
    BREAK = auto()          # [Break] - When destroyed
    JUDGMENT = auto()       # Judgment ability for rulers
    QUICKCAST = auto()      # [Quickcast] - Can play as instant
    KEYWORD = auto()        # Keyword abilities (Flying, Swiftness, etc.)
    STATIC = auto()         # Static ability text


@dataclass
class ParsedEffect:
    """A parsed effect from ability text"""
    effect_type: str                    # e.g., "produce_will", "draw", "buff"
    params: Dict[str, Any] = field(default_factory=dict)
    raw_text: str = ""


@dataclass
class ParsedAbility:
    """A parsed ability from card text"""
    ability_type: AbilityType
    cost_text: str = ""                 # e.g., "{Rest}" or "{G}{G}"
    effects: List[ParsedEffect] = field(default_factory=list)
    condition_text: str = ""            # Trigger condition if any
    raw_text: str = ""


class AbilityParser:
    """Parses FoW ability text into structured data"""

    # Ability type markers - both bracketed and unbracketed forms
    ABILITY_MARKERS = {
        '[activate]': AbilityType.ACTIVATE,
        'activate': AbilityType.ACTIVATE,
        '[continuous]': AbilityType.CONTINUOUS,
        'continuous': AbilityType.CONTINUOUS,
        '[enter]': AbilityType.ENTER,
        'enter': AbilityType.ENTER,
        '[leave]': AbilityType.LEAVE,
        'leave': AbilityType.LEAVE,
        '[break]': AbilityType.BREAK,
        'break': AbilityType.BREAK,
        '[quickcast]': AbilityType.QUICKCAST,
        'quickcast': AbilityType.QUICKCAST,
        'judgment': AbilityType.JUDGMENT,
    }

    # Keywords
    KEYWORDS = [
        'flying', 'swiftness', 'first strike', 'pierce', 'drain',
        'imperishable', 'eternal', 'barrier', 'precision', 'remnant',
        'incarnation', 'inheritance', 'resonance', 'awakening',
        'stealth', 'explode', 'target attack', 'mobilize',
    ]

    # Effect patterns: (regex, effect_type, param_extractor)
    # NOTE: These patterns are matched against lowercase text, so use lowercase letters
    EFFECT_PATTERNS = [
        # Will production - handle multiple patterns:
        # "Produce{G} or{U}" - dual stones with choice
        # "Produce{G} and{U}" - dual stones producing both
        # "Produce{G}" - basic stones
        # "produce {G}" - with space
        (r'produce\s*\{([wrugbv])\}\s*(?:or|and)\s*\{([wrugbv])\}', 'produce_will_dual',
         lambda m: {'attributes': [m.group(1).upper(), m.group(2).upper()]}),
        (r'produce\s*\{([wrugbvm])\}', 'produce_will', lambda m: {'attribute': m.group(1).upper()}),
        (r'produce\s+(\w+)\s+will', 'produce_will', lambda m: {'attribute_name': m.group(1)}),
        (r'produce one will of any attribute', 'produce_will_any', lambda m: {}),
        (r'produce\s*\{([wrugb])\}\s*,\s*\{([wrugb])\}\s*,\s*\{([wrugb])\}\s*,\s*\{([wrugb])\}\s*or\s*\{([wrugb])\}',
         'produce_will_choice_5', lambda m: {'attributes': [m.group(i).upper() for i in range(1, 6)]}),

        # Choose attribute on enter (Little Red)
        (r'(?:as|when).*?comes into.*?choose an attribute', 'choose_attribute_on_enter', lambda m: {}),

        # Conditional enter effects (for special stones)
        # "if you control a J/resonator with "Red" in its name, ... recovered"
        (r'if you control.*?["\'](\w+)["\'].*?(?:enter|call).*?recovered', 'conditional_enter_recovered',
         lambda m: {'name_contains': m.group(1)}),
        # "if you control a (race) resonator, ... recovered"
        (r'if you control.*?(\w+)\s+resonator.*?(?:enter|call).*?recovered', 'conditional_enter_recovered',
         lambda m: {'race': m.group(1)}),

        # Look at top of deck
        (r'look at the top (?:card|(\d+) cards?) of (?:your|owner\'s) (?:main )?deck', 'look_at_top',
         lambda m: {'count': int(m.group(1)) if m.group(1) else 1, 'your_deck': True}),
        (r'look at the top (?:card|(\d+) cards?) of (?:your )?opponent\'s (?:main )?deck', 'look_at_top',
         lambda m: {'count': int(m.group(1)) if m.group(1) else 1, 'opponent_deck': True}),
        # May put on bottom
        (r'(?:you )?may put (?:it|that card|them) (?:on the bottom|on bottom)', 'may_put_bottom',
         lambda m: {}),

        # Life cost with effect (for activated abilities on stones)
        # "{Rest}, Pay 300 life: Draw a card"
        (r'pay\s+(\d+)\s+life[,:\s]+draw\s+(?:a\s+)?cards?', 'pay_life_draw',
         lambda m: {'life_cost': int(m.group(1)), 'draw_count': 1}),
        # "{Rest}, Pay 200 life: Target resonator gains +200/+200"
        (r'pay\s+(\d+)\s+life[,:\s]+target.*?gains?\s+\[?\+?(\d+)/\+?(\d+)\]?', 'pay_life_buff',
         lambda m: {'life_cost': int(m.group(1)), 'atk': int(m.group(2)), 'def': int(m.group(3))}),

        # Enter effects with life loss
        (r'(?:when|as).*?(?:enter|call).*?(?:you )?(?:lose|pay)\s+(\d+)\s+life', 'enter_lose_life',
         lambda m: {'amount': int(m.group(1))}),

        # Drawing
        (r'draw\s+(\d+)\s+cards?', 'draw', lambda m: {'count': int(m.group(1))}),
        (r'draw\s+a\s+card', 'draw', lambda m: {'count': 1}),

        # Damage
        (r'deal\s+(\d+)\s+damage\s+to\s+target\s+(\w+)', 'damage',
         lambda m: {'amount': int(m.group(1)), 'target_type': m.group(2)}),
        (r'deal\s+(\d+)\s+damage', 'damage', lambda m: {'amount': int(m.group(1))}),

        # Stat modifications
        (r'target\s+.*?gains?\s+\[?\+(\d+)/\+(\d+)\]?', 'buff',
         lambda m: {'atk': int(m.group(1)), 'def': int(m.group(2))}),
        (r'gains?\s+\[?\+(\d+)/\+(\d+)\]?', 'buff',
         lambda m: {'atk': int(m.group(1)), 'def': int(m.group(2))}),
        (r'gets?\s+\[?\+(\d+)/\+(\d+)\]?', 'buff',
         lambda m: {'atk': int(m.group(1)), 'def': int(m.group(2))}),
        (r'gains?\s+\[?(\d+)/(\d+)\]?', 'set_stats',
         lambda m: {'atk': int(m.group(1)), 'def': int(m.group(2))}),

        # Negative stat mods
        (r'target\s+.*?gains?\s+\[?\+?(-?\d+)/\+?(-?\d+)\]?', 'debuff',
         lambda m: {'atk': int(m.group(1)), 'def': int(m.group(2))}),

        # Continuous effect patterns
        # Race-conditional buffs: "Each [Race] you control gains [+X/+Y]"
        (r'each\s+(\w+)\s+(?:you\s+control\s+)?gains?\s+\[?\+(\d+)/\+(\d+)\]?', 'race_buff',
         lambda m: {'race': m.group(1), 'atk': int(m.group(2)), 'def': int(m.group(3))}),

        # Restriction: Cannot attack
        (r'(?:this\s+card\s+)?cannot\s+attack(?:\s+or\s+block)?', 'restriction_no_attack',
         lambda m: {'can_attack': False, 'can_block': 'block' in m.group(0).lower()}),

        # Restriction: Cannot be targeted
        (r'cannot\s+be\s+targeted\s+by\s+.*?(?:opponent|your\s+opponent)', 'protection_targeting',
         lambda m: {'from_opponent': True}),

        # Grant keyword to race
        (r'each\s+(\w+)\s+(?:you\s+control\s+)?gains?\s+(\w+)', 'grant_keyword_to_race',
         lambda m: {'race': m.group(1), 'keyword': m.group(2)}),

        # Flying protection
        (r'can\s+only\s+be\s+blocked\s+by.*?flying', 'has_flying', lambda m: {}),

        # Prevent damage
        (r'prevent.*?damage', 'prevent_damage', lambda m: {}),

        # Imperishable
        (r'imperishable', 'has_imperishable', lambda m: {}),

        # Destruction - more specific patterns
        (r'destroy\s+target\s+(?:special\s+)?magic\s+stone', 'destroy',
         lambda m: {'target_type': 'stone', 'special_only': 'special' in m.group(0)}),
        (r'destroy\s+target\s+addition', 'destroy', lambda m: {'target_type': 'addition'}),
        (r'destroy\s+target\s+j[/-]?resonator', 'destroy', lambda m: {'target_type': 'j_resonator'}),
        (r'destroy\s+target\s+(\w+)\s+resonator\s+(?:you\s+control|your\s+opponent\s+controls)',
         'destroy', lambda m: {'target_type': 'resonator', 'attribute': m.group(1),
                               'controller': 'you' if 'you control' in m.group(0).lower() else 'opponent'}),
        (r'destroy\s+target\s+resonator\s+your?\s+opponent\s+controls?', 'destroy',
         lambda m: {'target_type': 'resonator', 'controller': 'opponent'}),
        (r'destroy\s+target\s+resonator\s+you\s+control', 'destroy',
         lambda m: {'target_type': 'resonator', 'controller': 'you'}),
        (r'destroy\s+target\s+resonator', 'destroy', lambda m: {'target_type': 'resonator'}),
        (r'destroy\s+target\s+(\w+)', 'destroy', lambda m: {'target_type': m.group(1)}),
        (r'destroy\s+all\s+(\w+)', 'destroy_all', lambda m: {'target_type': m.group(1)}),
        (r'destroy\s+it', 'destroy', lambda m: {'target': 'it'}),

        # Return to hand - more specific
        (r'return\s+target\s+addition.*?to\s+.*?hand', 'return_to_hand',
         lambda m: {'target_type': 'addition'}),
        (r'return\s+target\s+resonator.*?to\s+.*?hand', 'return_to_hand',
         lambda m: {'target_type': 'resonator'}),
        (r'return\s+this\s+card\s+to\s+.*?hand', 'return_to_hand',
         lambda m: {'target': 'self'}),
        (r'return\s+target\s+.*?to\s+.*?hand', 'return_to_hand', lambda m: {}),
        (r'return\s+.*?to\s+.*?hand', 'return_to_hand', lambda m: {}),

        # Banish - more specific
        (r'banish\s+target\s+resonator', 'banish', lambda m: {'target_type': 'resonator'}),
        (r'banish\s+target', 'banish', lambda m: {}),
        (r'banish\s+it', 'banish', lambda m: {'target': 'it'}),

        # Life gain/loss
        (r'gain\s+(\d+)\s+life', 'gain_life', lambda m: {'amount': int(m.group(1))}),
        (r'lose\s+(\d+)\s+life', 'lose_life', lambda m: {'amount': int(m.group(1))}),
        (r'pay\s+(\d+)\s+life', 'pay_life', lambda m: {'amount': int(m.group(1))}),

        # Keyword grants - more specific patterns
        (r'this\s+card\s+gains?\s+flying\s+until', 'grant_keyword_self',
         lambda m: {'keyword': 'Flying'}),
        (r'this\s+card\s+gains?\s+imperishable\s+until', 'grant_keyword_self',
         lambda m: {'keyword': 'Imperishable'}),
        (r'this\s+card\s+gains?\s+first\s+strike\s+until', 'grant_keyword_self',
         lambda m: {'keyword': 'First Strike'}),
        (r'this\s+card\s+gains?\s+swiftness\s+until', 'grant_keyword_self',
         lambda m: {'keyword': 'Swiftness'}),
        (r'this\s+card\s+gains?\s+pierce\s+until', 'grant_keyword_self',
         lambda m: {'keyword': 'Pierce'}),
        (r'this\s+card\s+gains?\s+target\s+attack\s+until', 'grant_keyword_self',
         lambda m: {'keyword': 'Target Attack'}),
        # Keyword grants with multiple options (Swiftness, Flying or Target Attack)
        (r'gains?\s+(\w+(?:\s+\w+)?)\s*,\s*(\w+(?:\s+\w+)?)\s+or\s+(\w+(?:\s+\w+)?)\s+until',
         'grant_keyword_choice', lambda m: {'keywords': [m.group(1), m.group(2), m.group(3)]}),
        (r'gains?\s+(\w+(?:\s+\w+)?)\s+and\s+(\w+(?:\s+\w+)?)\s+until',
         'grant_keyword_multiple', lambda m: {'keywords': [m.group(1), m.group(2)]}),
        (r'gains?\s+\[(\w+(?:\s+\w+)?)\]', 'grant_keyword', lambda m: {'keyword': m.group(1)}),
        (r'gains?\s+(\w+)\s+until', 'grant_keyword', lambda m: {'keyword': m.group(1)}),

        # Reveal top card
        (r'reveal\s+the\s+top\s+card', 'reveal_top', lambda m: {}),

        # Card movement
        (r'put\s+.*?into\s+your\s+hand', 'search_to_hand', lambda m: {}),
        (r'search\s+.*?deck.*?put.*?hand', 'search_to_hand', lambda m: {}),
        (r'look\s+at\s+the\s+top\s+(\d+)', 'look_at_top', lambda m: {'count': int(m.group(1))}),

        # Counters
        (r'put\s+.*?(\w+)\s+counter', 'add_counter', lambda m: {'counter_type': m.group(1)}),
        (r'remove\s+.*?(\w+)\s+counter\s+from\s+this\s+card', 'remove_counter_self',
         lambda m: {'counter_type': m.group(1)}),
        (r'remove\s+.*?(\w+)\s+counter', 'remove_counter', lambda m: {'counter_type': m.group(1)}),

        # Prevention effects
        (r'prevent\s+(?:all\s+)?(?:the\s+next\s+)?(\d+)?\s*damage', 'prevent_damage',
         lambda m: {'amount': int(m.group(1)) if m.group(1) else 0}),
        (r'(?:target\s+)?.*?cannot\s+be\s+(?:destroyed|targeted)', 'grant_protection',
         lambda m: {}),

        # This card deals X damage
        (r'this\s+card\s+deals\s+(\d+)\s+damage\s+to\s+target', 'self_deal_damage',
         lambda m: {'amount': int(m.group(1))}),

        # Remove target
        (r'remove\s+target\s+(?:addition|resonator)', 'banish', lambda m: {'target_type': 'any'}),

        # Cancel/Negate
        (r'cancel\s+target\s+spell', 'cancel', lambda m: {'target_type': 'spell'}),
        (r'negate\s+.*?effect', 'negate', lambda m: {}),

        # Rest/Recover - more specific
        (r'rest\s+target\s+j[/-]?resonator', 'rest', lambda m: {'target_type': 'j_resonator'}),
        (r'rest\s+target\s+(\w+)\s+resonator', 'rest',
         lambda m: {'target_type': 'resonator', 'attribute': m.group(1)}),
        (r'rest\s+target\s+resonator', 'rest', lambda m: {'target_type': 'resonator'}),
        (r'rest\s+target', 'rest', lambda m: {}),
        (r'recover\s+target\s+j[/-]?resonator', 'recover', lambda m: {'target_type': 'j_resonator'}),
        (r'recover\s+target\s+resonator', 'recover', lambda m: {'target_type': 'resonator'}),
        (r'recover\s+target', 'recover', lambda m: {}),
        (r'recover\s+this\s+card', 'recover', lambda m: {'target': 'self'}),

        # Graveyard retrieval to hand
        (r'put\s+target\s+(\w+)\s+(?:resonator\s+)?from\s+your\s+graveyard\s+into\s+your\s+hand',
         'graveyard_to_hand', lambda m: {'target_type': m.group(1)}),
        (r'put\s+target\s+(?:card|resonator|addition)\s+from\s+.*?graveyard\s+into\s+.*?hand',
         'graveyard_to_hand', lambda m: {}),

        # Graveyard retrieval to field
        (r'put\s+target\s+(\w+)\s+.*?from\s+your\s+graveyard\s+into\s+your\s+field',
         'graveyard_to_field', lambda m: {'target_type': m.group(1)}),
        (r'put\s+target\s+.*?from\s+.*?graveyard\s+into\s+.*?field',
         'graveyard_to_field', lambda m: {}),

        # Searching
        (r'search\s+your\s+(?:main\s+)?deck\s+for\s+(?:a\s+)?(\w+)\s+resonator',
         'search_to_hand', lambda m: {'filter': m.group(1)}),
        (r'search\s+your\s+(?:main\s+)?deck\s+for\s+a\s+card\s+with\s+["\'](\w+)["\']',
         'search_to_hand', lambda m: {'name_contains': m.group(1)}),
        (r'search\s+your\s+(?:main\s+)?deck\s+for\s+a\s+card\s+named.*?put\s+it\s+into\s+your\s+field',
         'search_to_field', lambda m: {}),
        (r'search\s+.*?deck.*?put.*?field', 'search_to_field', lambda m: {}),
        (r'search\s+.*?deck.*?put.*?hand', 'search_to_hand', lambda m: {}),

        # Special summon
        (r'put\s+.*?into\s+.*?field', 'special_summon', lambda m: {}),

        # Discard
        (r'(?:target\s+)?(?:opponent|player)\s+discards?\s+(?:a\s+)?card', 'discard_opponent',
         lambda m: {'count': 1}),
        (r'discard\s+a\s+card', 'discard', lambda m: {'count': 1}),
        (r'discard\s+(\d+)\s+cards?', 'discard', lambda m: {'count': int(m.group(1))}),
    ]

    def parse(self, ability_text: str) -> List[ParsedAbility]:
        """Parse ability text into structured abilities"""
        if not ability_text:
            return []

        abilities = []
        text = ability_text.strip()

        # Split by ability markers
        segments = self._split_by_markers(text)

        for ability_type, segment_text in segments:
            ability = self._parse_segment(ability_type, segment_text)
            if ability:
                abilities.append(ability)

        return abilities

    def _split_by_markers(self, text: str) -> List[Tuple[AbilityType, str]]:
        """Split text by ability markers like [Activate], [Continuous], etc.

        Handles both bracketed forms like [Activate] and unbracketed forms
        that appear at the start of lines.
        """
        segments = []

        # First, split by newlines to get individual ability lines
        lines = text.split('\n')

        for line in lines:
            line = line.strip()
            if not line:
                continue

            line_lower = line.lower()

            # Find marker at the start of this line
            found_marker = False
            for marker, ability_type in self.ABILITY_MARKERS.items():
                # Check if line starts with this marker
                if line_lower.startswith(marker):
                    # Extract the content after the marker
                    content = line[len(marker):].strip()
                    if content:
                        segments.append((ability_type, content))
                    found_marker = True
                    break

            if not found_marker:
                # No marker found - treat as static or check for inline markers
                # Check for markers anywhere in the line (for bracketed forms)
                marker_found_inline = False
                for marker, ability_type in self.ABILITY_MARKERS.items():
                    if marker.startswith('[') and marker in line_lower:
                        pos = line_lower.find(marker)
                        # Text before the marker (if any) is static
                        if pos > 0:
                            prefix = line[:pos].strip()
                            if prefix:
                                segments.append((AbilityType.STATIC, prefix))
                        # Text after the marker is the ability content
                        content = line[pos + len(marker):].strip()
                        if content:
                            segments.append((ability_type, content))
                        marker_found_inline = True
                        break

                if not marker_found_inline:
                    # No markers at all - treat as static
                    segments.append((AbilityType.STATIC, line))

        return segments

    def _parse_segment(self, ability_type: AbilityType, text: str) -> Optional[ParsedAbility]:
        """Parse a single ability segment"""
        ability = ParsedAbility(
            ability_type=ability_type,
            raw_text=text,
        )

        text_lower = text.lower()

        # Check for keywords first (for STATIC segments)
        if ability_type == AbilityType.STATIC:
            for keyword in self.KEYWORDS:
                if keyword in text_lower:
                    ability.ability_type = AbilityType.KEYWORD
                    ability.effects.append(ParsedEffect(
                        effect_type='keyword',
                        params={'keyword': keyword},
                        raw_text=text,
                    ))
            # Don't return early - also check effect patterns below

        # Parse cost (text before : )
        if ':' in text:
            parts = text.split(':', 1)
            ability.cost_text = parts[0].strip()
            effect_text = parts[1].strip() if len(parts) > 1 else ""
        else:
            effect_text = text

        # Look for trigger conditions (>>> marker)
        if '>>>' in effect_text or '»' in effect_text:
            parts = re.split(r'>>>|»', effect_text, 1)
            ability.condition_text = parts[0].strip()
            effect_text = parts[1].strip() if len(parts) > 1 else effect_text
            if ability.ability_type == AbilityType.STATIC:
                ability.ability_type = AbilityType.TRIGGER

        # Parse effects from the effect text AND full text (for enter effects, etc.)
        search_texts = [effect_text.lower(), text_lower]
        found_effects = set()  # Avoid duplicates

        for search_text in search_texts:
            for pattern, effect_type, extractor in self.EFFECT_PATTERNS:
                if effect_type in found_effects:
                    continue  # Already found this effect type
                match = re.search(pattern, search_text)
                if match:
                    try:
                        params = extractor(match)
                        ability.effects.append(ParsedEffect(
                            effect_type=effect_type,
                            params=params,
                            raw_text=match.group(0),
                        ))
                        found_effects.add(effect_type)
                    except Exception:
                        pass  # Skip malformed matches

        return ability if ability.effects or ability.ability_type == AbilityType.KEYWORD else None

    def parse_cost(self, cost_text: str) -> Dict[str, Any]:
        """Parse a cost string into components"""
        cost = {
            'tap': False,
            'will': {},
            'life': 0,
            'sacrifice': False,
            'discard': 0,
            'banish': False,
            'remove_counter': None,
        }

        text_lower = cost_text.lower()

        # Check for rest/tap cost
        if '{rest}' in text_lower or 'rest' in text_lower:
            cost['tap'] = True

        # Parse will cost symbols
        will_matches = re.findall(r'\{([WRUGBV\d]+)\}', cost_text)
        for symbol in will_matches:
            if symbol.isdigit():
                cost['will']['generic'] = cost['will'].get('generic', 0) + int(symbol)
            else:
                attr_map = {'W': 'light', 'R': 'fire', 'U': 'water',
                           'G': 'wind', 'B': 'darkness', 'V': 'void'}
                if symbol in attr_map:
                    attr = attr_map[symbol]
                    cost['will'][attr] = cost['will'].get(attr, 0) + 1

        # Life payment
        life_match = re.search(r'pay\s+(\d+)\s+life', text_lower)
        if life_match:
            cost['life'] = int(life_match.group(1))

        # Sacrifice
        if 'sacrifice' in text_lower:
            cost['sacrifice'] = True

        # Discard
        discard_match = re.search(r'discard\s+(\d+)', text_lower)
        if discard_match:
            cost['discard'] = int(discard_match.group(1))

        # Counter removal
        counter_match = re.search(r'remove\s+.*?(\w+)\s+counter', text_lower)
        if counter_match:
            cost['remove_counter'] = counter_match.group(1)

        return cost


# Global parser instance
parser = AbilityParser()


def parse_ability_text(text: str) -> List[ParsedAbility]:
    """Convenience function to parse ability text"""
    return parser.parse(text)
