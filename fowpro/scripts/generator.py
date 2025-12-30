"""
Card Script Generator
=====================

Generates Python card scripts from parsed ability text.
"""

import re
from typing import List, Dict, Optional
from pathlib import Path

from .parser import AbilityParser, ParsedAbility, ParsedEffect, AbilityType


class ScriptGenerator:
    """Generates Python card script code from parsed abilities"""

    def __init__(self):
        self.parser = AbilityParser()

    def generate_script(self, code: str, name: str, card_type: str,
                        ability_text: str, attribute: str = None) -> str:
        """Generate a complete card script class"""

        # Clean up the class name
        class_name = self._make_class_name(name)

        # Parse abilities
        abilities = self.parser.parse(ability_text) if ability_text else []

        # Start building the script
        lines = []
        lines.append(f'@ScriptRegistry.register("{code}")')
        lines.append(f'class {class_name}(CardScript):')
        lines.append(f'    """')
        lines.append(f'    {name}')
        if ability_text:
            # Add ability text as docstring, truncated
            for line in ability_text.split('\n')[:5]:
                lines.append(f'    {line.strip()}')
        lines.append(f'    """')
        lines.append('')

        # Check if it's a magic stone
        if 'stone' in card_type.lower():
            method_lines = self._generate_stone_methods(abilities, attribute)
        else:
            method_lines = self._generate_card_methods(abilities, card_type)

        # Add methods or pass if none
        if method_lines:
            lines.extend(method_lines)
        else:
            lines.append('    pass')

        return '\n'.join(lines)

    def generate_file(self, cards: List[Dict], set_code: str) -> str:
        """Generate a complete Python file for a set of cards"""
        lines = [
            f'"""',
            f'Auto-generated card scripts for {set_code}',
            f'',
            f'All card scripts including magic stones are auto-generated from ability text.',
            f'"""',
            '',
            'from .. import CardScript, ScriptRegistry, Effect, EffectType, EffectTiming',
            'from ..effects import *',
            'from ...models import Attribute, Keyword',
            '',
            '',
        ]

        for card in cards:
            # Generate scripts for ALL cards including magic stones
            try:
                script = self.generate_script(
                    code=card['code'],
                    name=card['name'],
                    card_type=card['card_type'],
                    ability_text=card.get('ability_text', ''),
                    attribute=card.get('attribute'),
                )
                lines.append(script)
                lines.append('')
                lines.append('')
            except Exception as e:
                lines.append(f'# Failed to generate script for {card["code"]}: {e}')
                lines.append('')

        return '\n'.join(lines)

    def _make_class_name(self, name: str) -> str:
        """Convert card name to valid Python class name"""
        # Remove special characters and convert to PascalCase
        name = re.sub(r'[^\w\s]', '', name)
        words = name.split()
        return ''.join(word.capitalize() for word in words)

    def _generate_stone_methods(self, abilities: List[ParsedAbility],
                                 attribute: str) -> List[str]:
        """Generate methods for magic stone cards"""
        lines = []

        # Find will production effects
        will_colors = []
        # Track special effects
        has_enter_effect = False
        enter_effects = []
        has_activated_ability = False
        activated_effects = []

        for ability in abilities:
            for effect in ability.effects:
                # Handle dual will production (e.g., Produce{G} or{U})
                if effect.effect_type == 'produce_will_dual':
                    if 'attributes' in effect.params:
                        for attr in effect.params['attributes']:
                            if attr.upper() not in will_colors:
                                will_colors.append(attr.upper())
                # Handle single will production (e.g., Produce{G})
                elif effect.effect_type == 'produce_will':
                    if 'attribute' in effect.params:
                        attr = effect.params['attribute'].upper()
                        if attr not in will_colors:
                            will_colors.append(attr)
                    elif 'attribute_name' in effect.params:
                        # Map name to symbol
                        name_map = {
                            'light': 'W', 'fire': 'R', 'water': 'U',
                            'wind': 'G', 'darkness': 'B', 'void': 'V'
                        }
                        attr_name = effect.params['attribute_name'].lower()
                        if attr_name in name_map:
                            symbol = name_map[attr_name]
                            if symbol not in will_colors:
                                will_colors.append(symbol)
                # Conditional enter recovered
                elif effect.effect_type == 'conditional_enter_recovered':
                    has_enter_effect = True
                    enter_effects.append(effect)
                # Look at top
                elif effect.effect_type == 'look_at_top':
                    has_enter_effect = True
                    enter_effects.append(effect)
                # Enter lose life
                elif effect.effect_type == 'enter_lose_life':
                    has_enter_effect = True
                    enter_effects.append(effect)
                # Pay life draw
                elif effect.effect_type == 'pay_life_draw':
                    has_activated_ability = True
                    activated_effects.append(effect)
                # Pay life buff
                elif effect.effect_type == 'pay_life_buff':
                    has_activated_ability = True
                    activated_effects.append(effect)
                # Choose attribute on enter (Little Red style)
                elif effect.effect_type == 'choose_attribute_on_enter':
                    has_enter_effect = True
                    enter_effects.append(effect)
                # Produce any attribute
                elif effect.effect_type == 'produce_will_any':
                    # Mark as 5-color stone
                    for c in ['W', 'R', 'U', 'G', 'B']:
                        if c not in will_colors:
                            will_colors.append(c)
                # 5-color choice
                elif effect.effect_type == 'produce_will_choice_5':
                    if 'attributes' in effect.params:
                        for attr in effect.params['attributes']:
                            if attr not in will_colors:
                                will_colors.append(attr)

        if not will_colors and attribute:
            # Fall back to card attribute
            attr_map = {
                'LIGHT': 'W', 'FIRE': 'R', 'WATER': 'U',
                'WIND': 'G', 'DARKNESS': 'B', 'VOID': 'V'
            }
            if attribute.upper() in attr_map:
                will_colors = [attr_map[attribute.upper()]]

        # Generate get_will_colors method
        if will_colors:
            lines.append('    def get_will_colors(self, game, card):')
            attr_map = {
                'W': 'Attribute.LIGHT',
                'R': 'Attribute.FIRE',
                'U': 'Attribute.WATER',
                'G': 'Attribute.WIND',
                'B': 'Attribute.DARKNESS',
                'V': 'Attribute.VOID',
                'M': 'Attribute.MOON',  # Moon will
            }
            attrs = [attr_map.get(c, 'Attribute.VOID') for c in will_colors]
            lines.append(f'        return [{", ".join(attrs)}]')
            lines.append('')

        # Generate on_enter_field for special stones
        if has_enter_effect:
            lines.append('    def on_enter_field(self, game, card):')
            lines.append('        player = game.players[card.controller]')
            for effect in enter_effects:
                if effect.effect_type == 'conditional_enter_recovered':
                    if 'name_contains' in effect.params:
                        name = effect.params['name_contains']
                        lines.append(f'        # Enter recovered if you control "{name}"')
                        lines.append(f'        for c in player.field:')
                        lines.append(f'            if c != card and c.data and "{name.lower()}" in c.data.name.lower():')
                        lines.append(f'                if c.data.is_resonator() or "j_ruler" in c.data.card_type.name.lower():')
                        lines.append(f'                    card.is_rested = False')
                        lines.append(f'                    break')
                    elif 'race' in effect.params:
                        race = effect.params['race']
                        lines.append(f'        # Enter recovered if you control {race}')
                        lines.append(f'        for c in player.field:')
                        lines.append(f'            if c != card and c.data and c.data.race:')
                        lines.append(f'                if "{race.lower()}" in c.data.race.lower():')
                        lines.append(f'                    card.is_rested = False')
                        lines.append(f'                    break')
                elif effect.effect_type == 'look_at_top':
                    if effect.params.get('opponent_deck'):
                        lines.append(f'        # Look at opponent\'s top card')
                        lines.append(f'        opponent = game.players[1 - card.controller]')
                        lines.append(f'        if opponent.main_deck:')
                        lines.append(f'            game.emit_event("look_at_top", {{"player": card.controller, "cards": [opponent.main_deck[0]], "opponent": True}})')
                    else:
                        lines.append(f'        # Look at your top card')
                        lines.append(f'        if player.main_deck:')
                        lines.append(f'            game.emit_event("look_at_top", {{"player": card.controller, "cards": [player.main_deck[0]]}})')
                elif effect.effect_type == 'enter_lose_life':
                    amount = effect.params.get('amount', 100)
                    lines.append(f'        # Lose {amount} life on enter')
                    lines.append(f'        player.life -= {amount}')
                elif effect.effect_type == 'choose_attribute_on_enter':
                    lines.append(f'        # Choose an attribute on enter')
                    lines.append(f'        game.emit_event("choose_attribute", {{"card": card, "callback": lambda attr: setattr(card, "chosen_attribute", attr)}})')
            lines.append('')

        # Generate initial_effect for activated abilities
        if has_activated_ability:
            lines.append('    def initial_effect(self, game, card):')
            for effect in activated_effects:
                if effect.effect_type == 'pay_life_draw':
                    life_cost = effect.params.get('life_cost', 0)
                    draw_count = effect.params.get('draw_count', 1)
                    lines.append(f'        # {{Rest}}, Pay {life_cost} life: Draw {draw_count}')
                    lines.append(f'        def pay_life_draw_op(g, c):')
                    lines.append(f'            p = g.players[c.controller]')
                    lines.append(f'            if p.life > {life_cost}:')
                    lines.append(f'                p.life -= {life_cost}')
                    lines.append(f'                draw_cards(g, c.controller, {draw_count})')
                    lines.append(f'        self.register_effect(Effect(')
                    lines.append(f'            name="Pay Life Draw",')
                    lines.append(f'            effect_type=EffectType.ACTIVATED,')
                    lines.append(f'            timing=EffectTiming.INSTANT_SPEED,')
                    lines.append(f'            tap_cost=True,')
                    lines.append(f'            condition=lambda g, c: g.players[c.controller].life > {life_cost} and not c.is_rested,')
                    lines.append(f'            operation=pay_life_draw_op,')
                    lines.append(f'        ))')
                elif effect.effect_type == 'pay_life_buff':
                    life_cost = effect.params.get('life_cost', 0)
                    atk = effect.params.get('atk', 0)
                    def_ = effect.params.get('def', 0)
                    lines.append(f'        # {{Rest}}, Pay {life_cost} life: Target +{atk}/+{def_}')
                    lines.append(f'        def pay_life_buff_op(g, c):')
                    lines.append(f'            p = g.players[c.controller]')
                    lines.append(f'            if p.life > {life_cost}:')
                    lines.append(f'                p.life -= {life_cost}')
                    lines.append(f'                # Target selection handled by UI')
                    lines.append(f'                g.emit_event("buff_target_needed", {{"source": c, "atk": {atk}, "def": {def_}}})')
                    lines.append(f'        self.register_effect(Effect(')
                    lines.append(f'            name="Pay Life Buff",')
                    lines.append(f'            effect_type=EffectType.ACTIVATED,')
                    lines.append(f'            timing=EffectTiming.INSTANT_SPEED,')
                    lines.append(f'            tap_cost=True,')
                    lines.append(f'            condition=lambda g, c: g.players[c.controller].life > {life_cost} and not c.is_rested,')
                    lines.append(f'            operation=pay_life_buff_op,')
                    lines.append(f'        ))')
            lines.append('')

        return lines

    def _generate_card_methods(self, abilities: List[ParsedAbility],
                                card_type: str) -> List[str]:
        """Generate methods for non-stone cards"""
        lines = []

        enter_effects = []
        leave_effects = []
        activated_effects = []
        continuous_effects = []
        trigger_effects = []
        keywords = []

        for ability in abilities:
            if ability.ability_type == AbilityType.ENTER:
                enter_effects.append(ability)

            elif ability.ability_type == AbilityType.LEAVE:
                leave_effects.append(ability)

            elif ability.ability_type == AbilityType.ACTIVATE:
                activated_effects.append(ability)

            elif ability.ability_type == AbilityType.CONTINUOUS:
                continuous_effects.append(ability)

            elif ability.ability_type == AbilityType.KEYWORD:
                for effect in ability.effects:
                    if effect.effect_type == 'keyword':
                        keywords.append(effect.params.get('keyword', ''))

            elif ability.ability_type == AbilityType.TRIGGER:
                trigger_effects.append(ability)

        # Generate initial_effect to register triggers and effects
        if activated_effects or trigger_effects or continuous_effects:
            lines.append('    def initial_effect(self, game, card):')
            lines.append('        """Register effects when card is created"""')

            for ability in activated_effects:
                lines.extend(self._generate_activated_registration(ability))

            for ability in trigger_effects:
                lines.extend(self._generate_trigger_registration(ability))

            for ability in continuous_effects:
                lines.extend(self._generate_continuous_registration(ability))

            if not (activated_effects or trigger_effects or continuous_effects):
                lines.append('        pass')
            lines.append('')

        # Generate on_enter_field
        if enter_effects:
            lines.extend(self._generate_enter_effect(enter_effects))

        # Generate on_leave_field
        if leave_effects:
            lines.extend(self._generate_leave_effect(leave_effects))

        return lines

    def _generate_enter_effect(self, abilities: List[ParsedAbility]) -> List[str]:
        """Generate on_enter_field method"""
        lines = ['    def on_enter_field(self, game, card):']
        lines.append('        """Trigger effects when entering the field"""')

        has_code = False
        for ability in abilities:
            for effect in ability.effects:
                effect_code = self._effect_to_code(effect)
                if effect_code:
                    lines.append(f'        {effect_code}')
                    has_code = True

        if not has_code:
            lines.append('        pass  # Auto-generated from ability text')

        lines.append('')
        return lines

    def _generate_leave_effect(self, abilities: List[ParsedAbility]) -> List[str]:
        """Generate on_leave_field method"""
        lines = ['    def on_leave_field(self, game, card):']
        lines.append('        """Trigger effects when leaving the field"""')

        has_code = False
        for ability in abilities:
            for effect in ability.effects:
                effect_code = self._effect_to_code(effect)
                if effect_code:
                    lines.append(f'        {effect_code}')
                    has_code = True

        if not has_code:
            lines.append('        pass  # Auto-generated from ability text')

        lines.append('')
        return lines

    def _generate_activated_registration(self, ability: ParsedAbility) -> List[str]:
        """Generate Effect registration for an activated ability"""
        lines = []

        # Parse cost
        cost_info = self.parser.parse_cost(ability.cost_text)

        # Create unique operation name
        op_name = f'op_{hash(ability.raw_text) % 10000}'

        lines.append(f'        # {ability.raw_text[:60]}...' if len(ability.raw_text) > 60
                    else f'        # {ability.raw_text}')

        # Generate operation function
        lines.append(f'        def {op_name}(g, c):')

        has_op = False
        for effect in ability.effects:
            effect_code = self._effect_to_code(effect, in_function=True)
            if effect_code:
                lines.append(f'            {effect_code}')
                has_op = True

        if not has_op:
            lines.append('            pass  # TODO: Implement')

        # Generate Effect registration
        lines.append('')
        lines.append('        self.register_effect(Effect(')
        safe_name = ability.raw_text[:40].replace('"', '\\"').replace("'", "\\'")
        lines.append(f'            name="{safe_name}",')
        lines.append('            effect_type=EffectType.ACTIVATED,')
        lines.append('            timing=EffectTiming.INSTANT_SPEED,')

        if cost_info.get('tap'):
            lines.append('            tap_cost=True,')

        lines.append(f'            operation={op_name},')
        lines.append('        ))')
        lines.append('')

        return lines

    def _generate_trigger_registration(self, ability: ParsedAbility) -> List[str]:
        """Generate Effect registration for a triggered ability"""
        lines = []

        # Determine trigger type from condition text
        trigger_type = 'TRIGGER_ENTER'  # Default
        condition_lower = ability.condition_text.lower() if ability.condition_text else ''

        if 'attack' in condition_lower:
            trigger_type = 'TRIGGER_ATTACK'
        elif 'block' in condition_lower:
            trigger_type = 'TRIGGER_BLOCK'
        elif 'damage' in condition_lower:
            trigger_type = 'TRIGGER_DAMAGE'
        elif 'leave' in condition_lower or 'destroy' in condition_lower:
            trigger_type = 'TRIGGER_LEAVE'
        elif 'recover' in condition_lower:
            trigger_type = 'TRIGGER_RECOVER'
        elif 'rest' in condition_lower:
            trigger_type = 'TRIGGER_REST'

        op_name = f'trig_{hash(ability.raw_text) % 10000}'

        lines.append(f'        # >>> {ability.condition_text[:40]}...' if ability.condition_text and len(ability.condition_text) > 40
                    else f'        # >>> {ability.condition_text}')

        # Generate operation function
        lines.append(f'        def {op_name}(g, c, event_data):')

        has_op = False
        for effect in ability.effects:
            effect_code = self._effect_to_code(effect, in_function=True)
            if effect_code:
                lines.append(f'            {effect_code}')
                has_op = True

        if not has_op:
            lines.append('            pass  # TODO: Implement')

        # Generate Effect registration
        lines.append('')
        lines.append('        self.register_effect(Effect(')
        safe_name = ability.raw_text[:40].replace('"', '\\"').replace("'", "\\'")
        lines.append(f'            name="{safe_name}",')
        lines.append(f'            effect_type=EffectType.{trigger_type},')
        lines.append(f'            operation={op_name},')
        lines.append('        ))')
        lines.append('')

        return lines

    def _generate_continuous_registration(self, ability: ParsedAbility) -> List[str]:
        """Generate Effect registration for a continuous ability"""
        lines = []

        lines.append(f'        # [Continuous]: {ability.raw_text[:50]}...' if len(ability.raw_text) > 50
                    else f'        # [Continuous]: {ability.raw_text}')

        # Parse effects to determine what kind of continuous effect
        buff_atk = 0
        buff_def = 0
        race_buff = None
        restriction = None
        protection = None
        keyword_grant = None

        for effect in ability.effects:
            if effect.effect_type == 'buff':
                buff_atk = effect.params.get('atk', 0)
                buff_def = effect.params.get('def', 0)
            elif effect.effect_type == 'race_buff':
                race_buff = effect.params
            elif effect.effect_type == 'restriction_no_attack':
                restriction = 'no_attack'
            elif effect.effect_type == 'protection_targeting':
                protection = 'barrier'
            elif effect.effect_type == 'grant_keyword_to_race':
                keyword_grant = effect.params
            elif effect.effect_type == 'has_flying':
                keyword_grant = {'keyword': 'flying', 'self': True}
            elif effect.effect_type == 'has_imperishable':
                keyword_grant = {'keyword': 'imperishable', 'self': True}

        safe_name = ability.raw_text[:40].replace('"', '\\"').replace("'", "\\'")

        # Race-conditional buff: Each [Race] you control gains +X/+Y
        if race_buff:
            race = race_buff.get('race', 'Resonator')
            atk = race_buff.get('atk', 0)
            def_ = race_buff.get('def', 0)
            lines.append('        self.register_effect(Effect(')
            lines.append(f'            name="{safe_name}",')
            lines.append('            effect_type=EffectType.CONTINUOUS,')
            lines.append(f'            value={{"race": "{race}", "atk_mod": {atk}, "def_mod": {def_}}},')
            lines.append('        ))')
        # Simple self-buff
        elif buff_atk or buff_def:
            lines.append('        self.register_effect(Effect(')
            lines.append(f'            name="{safe_name}",')
            lines.append('            effect_type=EffectType.CONTINUOUS,')
            lines.append(f'            value={{"atk_mod": {buff_atk}, "def_mod": {buff_def}}},')
            lines.append('        ))')
        # Restriction: Cannot attack/block
        elif restriction == 'no_attack':
            lines.append('        self.register_effect(Effect(')
            lines.append(f'            name="{safe_name}",')
            lines.append('            effect_type=EffectType.CONTINUOUS,')
            lines.append('            value={"restriction": "no_attack"},')
            lines.append('        ))')
        # Protection: Cannot be targeted
        elif protection == 'barrier':
            lines.append('        self.register_effect(Effect(')
            lines.append(f'            name="{safe_name}",')
            lines.append('            effect_type=EffectType.CONTINUOUS,')
            lines.append('            value={"grant_keyword": "Barrier"},')
            lines.append('        ))')
        # Keyword grant
        elif keyword_grant:
            kw = keyword_grant.get('keyword', 'Flying')
            if keyword_grant.get('self'):
                lines.append('        self.register_effect(Effect(')
                lines.append(f'            name="{safe_name}",')
                lines.append('            effect_type=EffectType.CONTINUOUS,')
                lines.append(f'            value={{"grant_keyword": "{kw.capitalize()}"}},')
                lines.append('        ))')
            else:
                race = keyword_grant.get('race', 'Resonator')
                lines.append('        self.register_effect(Effect(')
                lines.append(f'            name="{safe_name}",')
                lines.append('            effect_type=EffectType.CONTINUOUS,')
                lines.append(f'            value={{"race": "{race}", "grant_keyword": "{kw.capitalize()}"}},')
                lines.append('        ))')
        else:
            # Fallback - still create an effect but mark as needing implementation
            lines.append('        self.register_effect(Effect(')
            lines.append(f'            name="{safe_name}",')
            lines.append('            effect_type=EffectType.CONTINUOUS,')
            lines.append('            value={"unimplemented": True},')
            lines.append('        ))')

        lines.append('')

        return lines

    def _effect_to_code(self, effect: ParsedEffect, in_function: bool = False) -> Optional[str]:
        """Convert a parsed effect to Python code.

        Args:
            effect: The parsed effect
            in_function: If True, use 'g' and 'c' variable names (for nested functions)

        Returns actual executable code only, not comments."""
        effect_type = effect.effect_type
        params = effect.params

        # Variable names depend on context
        game_var = 'g' if in_function else 'game'
        card_var = 'c' if in_function else 'card'

        if effect_type == 'draw':
            count = params.get('count', 1)
            return f'draw_cards({game_var}, {card_var}.controller, {count})'

        elif effect_type == 'gain_life':
            amount = params.get('amount', 0)
            return f'gain_life({game_var}, {card_var}.controller, {amount})'

        elif effect_type == 'lose_life':
            amount = params.get('amount', 0)
            return f'lose_life({game_var}, {card_var}.controller, {amount})'

        elif effect_type == 'pay_life':
            amount = params.get('amount', 0)
            return f'{game_var}.players[{card_var}.controller].life -= {amount}'

        elif effect_type == 'produce_will':
            attr = params.get('attribute', 'V')
            attr_map = {
                'W': 'Attribute.LIGHT', 'R': 'Attribute.FIRE',
                'U': 'Attribute.WATER', 'G': 'Attribute.WIND',
                'B': 'Attribute.DARKNESS', 'V': 'Attribute.VOID',
            }
            attr_enum = attr_map.get(attr.upper(), 'Attribute.VOID')
            return f'produce_will({game_var}, {card_var}.controller, {attr_enum})'

        elif effect_type == 'add_counter':
            counter_type = params.get('counter_type', 'knowledge')
            return f'add_counter({card_var}, "{counter_type}")'

        elif effect_type == 'damage':
            amount = params.get('amount', 0)
            # For now just deal to opponent - targeting requires UI
            return f'deal_damage({game_var}, 1 - {card_var}.controller, {amount})'

        elif effect_type == 'buff':
            atk = params.get('atk', 0)
            def_ = params.get('def', 0)
            # Self-buff for now
            return f'buff_card({card_var}, {atk}, {def_})'

        elif effect_type == 'rest':
            target = params.get('target', None)
            target_type = params.get('target_type', None)
            if target == 'self':
                return f'rest_card({game_var}, {card_var})'
            elif target_type == 'j_resonator':
                return f'rest_target_j_resonator({game_var}, {card_var})'
            elif target_type:
                return f'rest_target_resonator({game_var}, {card_var})'
            else:
                return f'rest_card({game_var}, {card_var})'

        elif effect_type == 'recover':
            target = params.get('target', None)
            target_type = params.get('target_type', None)
            if target == 'self':
                return f'recover_card({game_var}, {card_var})'
            elif target_type == 'j_resonator':
                return f'recover_target_resonator({game_var}, {card_var})'
            elif target_type:
                return f'recover_target_resonator({game_var}, {card_var})'
            else:
                return f'recover_card({game_var}, {card_var})'

        # Destruction effects
        elif effect_type == 'destroy':
            target_type = params.get('target_type', 'resonator')
            controller = params.get('controller', 'any')
            if target_type == 'addition':
                return f'destroy_target_addition({game_var}, {card_var}, "{controller}")'
            elif target_type == 'stone':
                special = params.get('special_only', False)
                return f'destroy_target_stone({game_var}, {card_var}, "{controller}", {special})'
            elif target_type == 'j_resonator':
                return f'destroy_target_j_resonator({game_var}, {card_var}, "{controller}")'
            else:
                return f'destroy_target_resonator({game_var}, {card_var}, "{controller}")'

        # Return to hand effects
        elif effect_type == 'return_to_hand':
            target = params.get('target', None)
            target_type = params.get('target_type', 'resonator')
            if target == 'self':
                return f'return_to_hand({game_var}, {card_var})'
            elif target_type == 'addition':
                return f'bounce_target_addition({game_var}, {card_var})'
            else:
                return f'bounce_target_resonator({game_var}, {card_var})'

        # Banish effects
        elif effect_type == 'banish':
            target = params.get('target', None)
            if target == 'it':
                return f'banish_card({game_var}, {card_var})'
            else:
                return f'banish_target_resonator({game_var}, {card_var})'

        # Cancel spell effects
        elif effect_type == 'cancel':
            return f'cancel_target_spell({game_var}, {card_var})'

        # Graveyard to hand
        elif effect_type == 'graveyard_to_hand':
            target_type = params.get('target_type', None)
            if target_type:
                # Filter by type
                return f'put_from_graveyard_to_hand({game_var}, {card_var}, lambda c: c.data and "{target_type.lower()}" in str(c.data.card_type).lower())'
            else:
                return f'put_from_graveyard_to_hand({game_var}, {card_var})'

        # Search deck to hand
        elif effect_type == 'search_to_hand':
            filter_val = params.get('filter', None)
            name_contains = params.get('name_contains', None)
            if filter_val:
                return f'search_deck_to_hand({game_var}, {card_var}, lambda c: c.data and c.data.race and "{filter_val.lower()}" in c.data.race.lower())'
            elif name_contains:
                return f'search_deck_to_hand({game_var}, {card_var}, lambda c: c.data and "{name_contains.lower()}" in c.data.name.lower())'
            else:
                return f'search_deck_to_hand({game_var}, {card_var})'

        # Search deck to field (special summon)
        elif effect_type == 'search_to_field':
            return f'search_deck_to_field({game_var}, {card_var})'

        # Discard effects
        elif effect_type == 'discard':
            count = params.get('count', 1)
            return f'{game_var}.players[{card_var}.controller].discard_random({count})'

        elif effect_type == 'discard_opponent':
            count = params.get('count', 1)
            return f'{game_var}.players[1 - {card_var}.controller].discard_random({count})'

        # Debuff (negative stats)
        elif effect_type == 'debuff':
            atk = params.get('atk', 0)
            def_ = params.get('def', 0)
            return f'buff_target_resonator({game_var}, {card_var}, {atk}, {def_})'

        # Damage to target
        elif effect_type == 'damage' and 'target_type' in params:
            amount = params.get('amount', 0)
            return f'deal_damage_to_target({game_var}, {card_var}, {amount})'

        # Self deals damage
        elif effect_type == 'self_deal_damage':
            amount = params.get('amount', 0)
            return f'deal_damage_to_target({game_var}, {card_var}, {amount})'

        # Prevent damage
        elif effect_type == 'prevent_damage':
            # For now, just mark as protection effect
            return f'grant_keyword({game_var}, {card_var}, Keyword.BARRIER, until_eot=True)'

        # Grant protection (cannot be targeted/destroyed)
        elif effect_type == 'grant_protection':
            return f'grant_keyword({game_var}, {card_var}, Keyword.BARRIER, until_eot=True)'

        # Remove counter from self (cost, not effect)
        elif effect_type == 'remove_counter_self':
            counter_type = params.get('counter_type', 'knowledge')
            # This is a cost, not an effect - the actual effect will be in another pattern
            return f'remove_counter({card_var}, "{counter_type}", 1)'

        # Grant keyword to self
        elif effect_type == 'grant_keyword_self':
            keyword = params.get('keyword', 'Flying')
            keyword_enum = {
                'Flying': 'Keyword.FLYING',
                'Imperishable': 'Keyword.IMPERISHABLE',
                'First Strike': 'Keyword.FIRST_STRIKE',
                'Swiftness': 'Keyword.SWIFTNESS',
                'Pierce': 'Keyword.PIERCE',
                'Barrier': 'Keyword.BARRIER',
                'Precision': 'Keyword.PRECISION',
            }.get(keyword, 'Keyword.FLYING')
            return f'grant_keyword({game_var}, {card_var}, {keyword_enum}, until_eot=True)'

        # Reveal top card
        elif effect_type == 'reveal_top':
            return f'{game_var}.reveal_top_card({card_var}.controller)'

        # Graveyard to field
        elif effect_type == 'graveyard_to_field':
            target_type = params.get('target_type', None)
            if target_type:
                return f'put_from_graveyard_to_field({game_var}, {card_var}, lambda c: c.data and "{target_type.lower()}" in str(c.data.race or "").lower())'
            else:
                return f'put_from_graveyard_to_field({game_var}, {card_var})'

        # Special summon (put into field)
        elif effect_type == 'special_summon':
            return f'search_deck_to_field({game_var}, {card_var})'

        # Grant keyword with choice (pick one from list)
        elif effect_type == 'grant_keyword_choice':
            keywords = params.get('keywords', ['Flying'])
            keyword_list = str(keywords)
            return f'grant_keyword_choice_until_eot({game_var}, {card_var}, {keyword_list})'

        # Grant multiple keywords
        elif effect_type == 'grant_keyword_multiple':
            keywords = params.get('keywords', ['Flying'])
            lines = []
            for kw in keywords:
                lines.append(f'grant_keyword_until_eot({game_var}, {card_var}, "{kw}")')
            return '; '.join(lines) if lines else None

        # Grant single keyword
        elif effect_type == 'grant_keyword':
            keyword = params.get('keyword', 'Flying')
            return f'grant_keyword_until_eot({game_var}, {card_var}, "{keyword}")'

        return None


# Global generator instance
generator = ScriptGenerator()


def generate_scripts_for_set(db, set_code: str, output_dir: Path):
    """Generate script files for all cards in a set"""
    from ..database import CardDatabase

    # Get all cards from the set
    cards = db.search_cards(set_code=set_code)

    if not cards:
        print(f"No cards found for set {set_code}")
        return

    # Convert CardData to dicts
    card_dicts = []
    for card in cards:
        card_dicts.append({
            'code': card.code,
            'name': card.name,
            'card_type': card.card_type.name,
            'ability_text': card.ability_text,
            'attribute': card.attribute.name if card.attribute else None,
        })

    # Generate the script file
    content = generator.generate_file(card_dicts, set_code)

    # Write to file
    output_file = output_dir / f"{set_code.lower()}.py"
    output_file.write_text(content)
    print(f"Generated {output_file}")


def generate_all_scripts(db, output_dir: Path):
    """Generate scripts for all sets"""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create __init__.py
    init_content = '"""Auto-generated card scripts"""\n\n'

    sets = ['CMF', 'TAT', 'MPR', 'MOA']
    for set_code in sets:
        generate_scripts_for_set(db, set_code, output_dir)
        init_content += f'from .{set_code.lower()} import *\n'

    (output_dir / '__init__.py').write_text(init_content)
    print(f"Generated {output_dir / '__init__.py'}")
