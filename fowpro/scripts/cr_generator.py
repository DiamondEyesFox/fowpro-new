"""
Comprehensive Rules-based Script Generator
===========================================

Generates Python card scripts from parsed ability text using CR-compliant
ability structures.

This generator produces scripts that use:
- RulesCardScript base class
- AbilityFactory for common patterns
- CR-compliant ability registrations
"""

import re
from typing import List, Dict, Optional
from pathlib import Path

from .cr_parser import (
    CRAbilityParser, ParsedAbility, ParsedEffect, ParsedCost, ParsedTarget,
    ParsedModalChoice, ParsedIncarnation, ParsedAwakening,
    parse_ability_text_cr
)
from ..rules import (
    AbilityType, EffectAction, EffectDuration, TriggerCondition, KeywordAbility
)


class CRScriptGenerator:
    """
    Generates Python card scripts using CR-compliant ability structures.

    Output uses RulesCardScript base class and registers abilities using
    the rules module types (ActivateAbility, AutomaticAbility, etc.)
    """

    def __init__(self):
        self.parser = CRAbilityParser()

    def generate_script(self, code: str, name: str, card_type: str,
                        ability_text: str, attribute: str = None) -> str:
        """Generate a complete card script class."""
        class_name = self._make_class_name(name)
        abilities = self.parser.parse(ability_text) if ability_text else []

        # Check for Judgment cost on Rulers
        judgment_cost = None
        if 'ruler' in card_type.lower() and 'j-ruler' not in card_type.lower():
            judgment_cost = self.parser._parse_judgment_cost(ability_text) if ability_text else None

        lines = [
            f'@ScriptRegistry.register("{code}")',
            f'class {class_name}(RulesCardScript):',
            f'    """',
            f'    {name}',
        ]

        # Add ability text as docstring
        if ability_text:
            for line in ability_text.split('\n')[:5]:
                lines.append(f'    {line.strip()}')
        lines.append(f'    """')
        lines.append('')

        # Generate method content
        if 'stone' in card_type.lower():
            method_lines = self._generate_stone_methods(abilities, attribute)
        else:
            method_lines = self._generate_card_methods(abilities, card_type, code, judgment_cost)

        if method_lines:
            lines.extend(method_lines)
        else:
            lines.append('    pass')

        return '\n'.join(lines)

    def generate_file(self, cards: List[Dict], set_code: str) -> str:
        """Generate a complete Python file for a set of cards."""
        lines = [
            '"""',
            f'Auto-generated card scripts for {set_code}',
            '',
            'Generated using CR-compliant ability system.',
            '"""',
            '',
            '# Core imports',
            'from .. import ScriptRegistry',
            'from ..rules_bridge import (',
            '    RulesCardScript,',
            '    AbilityFactory, EffectBuilder,',
            '    ActivateAbility, AutomaticAbility, ContinuousAbility, WillAbility, JudgmentAbility,',
            '    TriggerCondition, EffectDuration, KeywordAbility,',
            '    TargetRequirement, TargetFilter, TargetZone, TargetController,',
            '    Condition, ConditionType, ConditionBuilder,',
            '    ContinuousEffect, RulesEffect, EffectAction,',
            '    ModalAbility, IncarnationCost, AwakeningCost,',
            '    ReplacementEffectCR, ReplacementEventType, ReplacementEffectResult,',
            '    ReplacementBuilder,',
            '    CostPaymentModifier,',
            ')',
            'from ...models import Attribute, WillCost, Phase, Zone',
            '',
            '',
        ]

        for card in cards:
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
        """Convert card name to valid Python class name."""
        name = re.sub(r'[^\w\s]', '', name)
        words = name.split()
        return ''.join(word.capitalize() for word in words)

    def _escape_name(self, text: str, max_len: int = 40) -> str:
        """Escape quotes in ability name for Python string."""
        safe = text[:max_len].replace('\\', '\\\\').replace('"', '\\"').replace("'", "\\'")
        return safe

    def _build_upgrade_condition_code(self, text: str) -> Optional[str]:
        """Build a Condition expression from a modal upgrade condition string."""
        if not text:
            return None

        text_lower = text.lower()

        # Match quoted card names
        names = re.findall(r'"([^"]+)"', text)
        if not names:
            names = re.findall(r"'([^']+)'", text)

        if names:
            cleaned = [n.strip() for n in names]
            conds = [
                f'Condition(ConditionType.CONTROL_CARD, params={{"name": {name!r}}})'
                for name in cleaned
            ]
            if ' or ' in text_lower and ' and ' not in text_lower:
                return f'ConditionBuilder.any_of({", ".join(conds)})'
            return f'ConditionBuilder.all_of({", ".join(conds)})'

        # Match "you control a [race]"
        race_match = re.search(r'you\s+control\s+an?\s+([a-z\s]+?)(?:\s+resonator|\s+addition|\s+card|\s*$)', text_lower)
        if race_match:
            race = race_match.group(1).strip().title()
            return f'ConditionBuilder.control_race({race!r})'

        return None

    def _generate_stone_methods(self, abilities: List[ParsedAbility],
                                 attribute: str) -> List[str]:
        """Generate methods for magic stone cards."""
        lines = []
        will_colors = []
        has_enter_effect = False
        has_activated = False

        # Analyze abilities
        for ability in abilities:
            for effect in ability.effects:
                if effect.action == EffectAction.PRODUCE_WILL:
                    colors = effect.params.get('colors', [])
                    for c in colors:
                        if c not in will_colors:
                            will_colors.append(c)

            if ability.trigger_condition == TriggerCondition.ENTER_FIELD:
                has_enter_effect = True

            if ability.ability_type == AbilityType.ACTIVATE:
                has_activated = True

        # Fallback to card attribute if no explicit will colors
        if not will_colors and attribute:
            attr_map = {
                'LIGHT': 'LIGHT', 'FIRE': 'FIRE', 'WATER': 'WATER',
                'WIND': 'WIND', 'DARKNESS': 'DARKNESS', 'VOID': 'VOID'
            }
            if attribute.upper() in attr_map:
                will_colors = [attr_map[attribute.upper()]]

        # Generate initial_effect
        lines.append('    def initial_effect(self, game, card):')

        if will_colors:
            color_str = ', '.join(f'Attribute.{c}' for c in will_colors)
            lines.append(f'        # Will ability: tap to produce will')
            lines.append(f'        self.register_ability(AbilityFactory.will_ability(')
            lines.append(f'            colors=[{color_str}],')
            lines.append(f'            tap=True')
            lines.append(f'        ))')
            lines.append('')

        if has_enter_effect:
            for ability in abilities:
                if ability.trigger_condition == TriggerCondition.ENTER_FIELD:
                    lines.extend(self._generate_enter_ability(ability))

        if has_activated:
            for ability in abilities:
                if ability.ability_type == AbilityType.ACTIVATE:
                    lines.extend(self._generate_activate_ability(ability))

        if not (will_colors or has_enter_effect or has_activated):
            lines.append('        pass')

        lines.append('')
        return lines

    def _generate_card_methods(self, abilities: List[ParsedAbility],
                                card_type: str, code: str = "",
                                judgment_cost: 'ParsedCost' = None) -> List[str]:
        """Generate methods for non-stone cards."""
        lines = []

        enter_abilities = []
        leave_abilities = []
        attack_abilities = []
        activate_abilities = []
        continuous_abilities = []
        replacement_abilities = []
        modal_abilities = []
        incarnation_abilities = []
        awakening_abilities = []
        x_cost_abilities = []
        other_triggered_abilities = []  # For triggers other than enter/leave/attack
        spell_effects = []  # Effects for spell cards
        cost_modifiers = []
        keywords = KeywordAbility.NONE
        is_ruler = 'ruler' in card_type.lower() and 'j-ruler' not in card_type.lower()
        is_spell = 'spell' in card_type.lower()

        # Categorize abilities
        for ability in abilities:
            if getattr(ability, 'cost_modifiers', None):
                cost_modifiers.extend(ability.cost_modifiers)

            if ability.keywords != KeywordAbility.NONE:
                keywords |= ability.keywords
                continue

            # Check for special ability types first
            if ability.is_modal:
                modal_abilities.append(ability)
                continue

            if getattr(ability, 'replacement_effects', None):
                replacement_abilities.append(ability)
                continue

            if ability.incarnation:
                incarnation_abilities.append(ability)
                # Don't continue - also categorize by type

            if ability.awakening:
                awakening_abilities.append(ability)
                # Don't continue - also categorize by type

            if ability.uses_x:
                x_cost_abilities.append(ability)
                continue

            if ability.ability_type == AbilityType.AUTOMATIC:
                tc = ability.trigger_condition
                if tc == TriggerCondition.ENTER_FIELD:
                    enter_abilities.append(ability)
                elif tc == TriggerCondition.LEAVE_FIELD:
                    leave_abilities.append(ability)
                elif tc == TriggerCondition.DECLARES_ATTACK:
                    attack_abilities.append(ability)
                elif tc is not None:
                    # Handle other triggers generically
                    other_triggered_abilities.append(ability)
                else:
                    enter_abilities.append(ability)  # Default for unknown

            elif ability.ability_type == AbilityType.ACTIVATE:
                activate_abilities.append(ability)

            elif ability.ability_type == AbilityType.CONTINUOUS:
                # For spells, continuous abilities are actually spell effects
                if is_spell and not ability.raw_text.startswith('Continuous'):
                    spell_effects.append(ability)
                else:
                    continuous_abilities.append(ability)

        # Generate initial_effect
        has_registered = False
        all_abilities = (enter_abilities + leave_abilities + attack_abilities +
                        activate_abilities + continuous_abilities + replacement_abilities + modal_abilities +
                        incarnation_abilities + awakening_abilities + x_cost_abilities +
                        other_triggered_abilities + spell_effects)

        # Also need initial_effect if ruler has Judgment
        has_judgment = is_ruler and judgment_cost is not None

        if all_abilities or has_judgment:
            lines.append('    def initial_effect(self, game, card):')
            lines.append('        """Register abilities when card is created."""')

            # Generate Judgment for rulers first
            if has_judgment:
                lines.extend(self._generate_judgment_ability(code, judgment_cost))
                has_registered = True

            # Generate incarnation/awakening first (they modify costs)
            for ability in incarnation_abilities:
                lines.extend(self._generate_incarnation(ability))
                has_registered = True

            for ability in awakening_abilities:
                lines.extend(self._generate_awakening(ability))
                has_registered = True

            # Generate modal abilities
            for ability in modal_abilities:
                lines.extend(self._generate_modal_ability(ability))
                has_registered = True

            # Generate X cost abilities
            for ability in x_cost_abilities:
                lines.extend(self._generate_x_cost_ability(ability))
                has_registered = True

            for ability in enter_abilities:
                lines.extend(self._generate_enter_ability(ability))
                has_registered = True

            for ability in leave_abilities:
                lines.extend(self._generate_leave_ability(ability))
                has_registered = True

            for ability in attack_abilities:
                lines.extend(self._generate_attack_ability(ability))
                has_registered = True

            for ability in activate_abilities:
                lines.extend(self._generate_activate_ability(ability))
                has_registered = True

            for ability in continuous_abilities:
                lines.extend(self._generate_continuous_ability(ability))
                has_registered = True

            for ability in other_triggered_abilities:
                lines.extend(self._generate_triggered_ability(ability))
                has_registered = True

            for ability in spell_effects:
                lines.extend(self._generate_spell_effect(ability))
                has_registered = True

            if not has_registered:
                lines.append('        pass')
            lines.append('')

        # Generate keyword method if needed
        if keywords != KeywordAbility.NONE:
            keyword_names = []
            for kw in KeywordAbility:
                if kw != KeywordAbility.NONE and keywords & kw:
                    keyword_names.append(kw.name)

            if keyword_names:
                lines.append('    def get_keywords(self) -> KeywordAbility:')
                kw_str = ' | '.join(f'KeywordAbility.{name}' for name in keyword_names)
                lines.append(f'        return {kw_str}')
                lines.append('')

        # Generate replacement effects method if present
        if replacement_abilities:
            lines.extend(self._generate_replacement_effects(replacement_abilities))

        # Generate cost payment modifiers if needed
        if cost_modifiers:
            lines.append('    def get_cost_modifiers(self, game, card):')
            lines.append('        return [')
            for mod in cost_modifiers:
                name = getattr(mod, 'name', '') or "Cost Payment Modifier"
                any_will = 'True' if getattr(mod, 'any_will_pays_colored', False) else 'False'
                applies_type = getattr(mod, 'applies_to_type', None)
                applies_race = getattr(mod, 'applies_to_race', None)
                filter_parts = []
                if applies_type == 'resonator':
                    filter_parts.append('c.data.is_resonator()')
                elif applies_type == 'spell':
                    filter_parts.append('c.data.is_spell()')
                elif applies_type == 'stone':
                    filter_parts.append('c.data.is_stone()')
                if applies_race:
                    race_str = repr(applies_race)
                    filter_parts.append(f'any(r.lower() == {race_str}.lower() for r in (c.data.races or []))')
                if filter_parts:
                    filter_expr = ' and '.join(filter_parts)
                    filter_code = f'lambda c, player: c and c.data and {filter_expr}'
                else:
                    filter_code = 'lambda c, player: True'
                lines.append('            CostPaymentModifier(')
                lines.append(f'                name="{self._escape_name(name, 60)}",')
                lines.append(f'                any_will_pays_colored={any_will},')
                lines.append(f'                applies_to_filter={filter_code},')
                lines.append('            ),')
            lines.append('        ]')
            lines.append('')

        return lines

    def _generate_enter_ability(self, ability: ParsedAbility) -> List[str]:
        """Generate [Enter] ability registration."""
        lines = []
        lines.append(f'        # [Enter] ability')
        lines.append(f'        self.register_ability(AutomaticAbility(')
        lines.append(f'            name="{self._escape_name(ability.raw_text)}",')
        lines.append(f'            trigger_condition=TriggerCondition.ENTER_FIELD,')

        effects_code = self._generate_effects_list(ability.effects)
        lines.append(f'            effects={effects_code},')
        lines.append(f'            is_mandatory={ability.is_mandatory},')
        lines.append(f'        ))')
        lines.append('')
        return lines

    def _generate_leave_ability(self, ability: ParsedAbility) -> List[str]:
        """Generate leave field ability registration."""
        lines = []
        lines.append(f'        # Leave field ability')
        lines.append(f'        self.register_ability(AutomaticAbility(')
        lines.append(f'            name="{self._escape_name(ability.raw_text)}",')
        lines.append(f'            trigger_condition=TriggerCondition.LEAVE_FIELD,')

        effects_code = self._generate_effects_list(ability.effects)
        lines.append(f'            effects={effects_code},')
        lines.append(f'            is_mandatory={ability.is_mandatory},')
        lines.append(f'        ))')
        lines.append('')
        return lines

    def _generate_attack_ability(self, ability: ParsedAbility) -> List[str]:
        """Generate attack trigger ability registration."""
        lines = []
        lines.append(f'        # Attack trigger ability')
        lines.append(f'        self.register_ability(AutomaticAbility(')
        lines.append(f'            name="{self._escape_name(ability.raw_text)}",')
        lines.append(f'            trigger_condition=TriggerCondition.DECLARES_ATTACK,')

        effects_code = self._generate_effects_list(ability.effects)
        lines.append(f'            effects={effects_code},')
        lines.append(f'            is_mandatory={ability.is_mandatory},')
        lines.append(f'        ))')
        lines.append('')
        return lines

    def _generate_triggered_ability(self, ability: ParsedAbility) -> List[str]:
        """Generate generic triggered ability with actual trigger condition."""
        lines = []
        tc = ability.trigger_condition
        tc_name = tc.name if tc else 'ENTER_FIELD'
        lines.append(f'        # Triggered ability ({tc_name})')
        lines.append(f'        self.register_ability(AutomaticAbility(')
        lines.append(f'            name="{self._escape_name(ability.raw_text)}",')
        lines.append(f'            trigger_condition=TriggerCondition.{tc_name},')

        effects_code = self._generate_effects_list(ability.effects)
        lines.append(f'            effects={effects_code},')
        lines.append(f'            is_mandatory={ability.is_mandatory},')
        lines.append(f'        ))')
        lines.append('')
        return lines

    def _generate_activate_ability(self, ability: ParsedAbility) -> List[str]:
        """Generate [Activate] ability registration."""
        lines = []
        lines.append(f'        # [Activate] ability')
        lines.append(f'        self.register_ability(ActivateAbility(')
        lines.append(f'            name="{self._escape_name(ability.raw_text)}",')

        # Generate cost
        if ability.cost:
            if ability.cost.tap:
                lines.append(f'            tap_cost=True,')
            # Generate WillCost (colored and/or generic)
            will_parts = []
            if ability.cost.will:
                for attr, count in ability.cost.will.items():
                    will_parts.append(f'{attr.lower()}={count}')
            if ability.cost.generic:
                will_parts.append(f'generic={ability.cost.generic}')
            if will_parts:
                lines.append(f'            will_cost=WillCost({", ".join(will_parts)}),')
            # Additional costs (discard, etc.)
            additional_costs = []
            if ability.cost.discard:
                add = {
                    "type": "discard",
                    "count": ability.cost.discard,
                }
                if getattr(ability.cost, "discard_types", None):
                    add["card_types"] = ability.cost.discard_types
                if getattr(ability.cost, "discard_races", None):
                    add["races"] = ability.cost.discard_races
                additional_costs.append(add)
            if additional_costs:
                lines.append(f'            additional_costs={additional_costs},')

        effects_code = self._generate_effects_list(ability.effects)
        lines.append(f'            effects={effects_code},')

        if ability.once_per_turn:
            lines.append(f'            once_per_turn=True,')

        lines.append(f'        ))')
        lines.append('')
        return lines

    def _generate_continuous_ability(self, ability: ParsedAbility) -> List[str]:
        """Generate [Continuous] ability registration."""
        lines = []
        lines.append(f'        # [Continuous] ability')

        # Check for various continuous effect patterns
        generated = False
        for effect in ability.effects:
            params = effect.params

            # Scaling buff: "gains +X/+Y for each Z"
            if params.get('scaling'):
                atk_per = params.get('atk_per', 0)
                def_per = params.get('def_per', 0)
                lines.append(f'        self.register_continuous_effect(ContinuousEffect(')
                lines.append(f'            name="{self._escape_name(ability.raw_text, 40)}",')
                lines.append(f'            affects_self_only=True,')
                lines.append(f'            # Scaling: +{atk_per}/+{def_per} for each matching card')
                lines.append(f'            apply_func=lambda game, card: self._apply_scaling_buff(game, card, {atk_per}, {def_per}),')
                lines.append(f'        ))')
                generated = True
                break

            # Group buff: "Each X you control gains +Y/+Y"
            if params.get('to_others') and effect.action == EffectAction.MODIFY_ATK:
                atk_mod = params.get('atk', 0)
                def_mod = params.get('def', 0)
                target_type = params.get('target_type', 'Resonator')
                lines.append(f'        # Group buff: Each {target_type} you control')
                lines.append(f'        self.register_continuous_effect(ContinuousEffect(')
                lines.append(f'            name="{self._escape_name(ability.raw_text, 40)}",')
                lines.append(f'            affects_self_only=False,')
                lines.append(f'            modifier=StatModifier(atk={atk_mod}, def_={def_mod}),')
                lines.append(f'            filter_func=lambda card: "{target_type}" in card.races,')
                lines.append(f'        ))')
                generated = True
                break

            # Force attack: "must attack if able"
            if params.get('force_attack'):
                lines.append(f'        self.register_continuous_effect(ContinuousEffect(')
                lines.append(f'            name="Must Attack",')
                lines.append(f'            affects_self_only=True,')
                lines.append(f'            # Forces this card to attack if able')
                lines.append(f'        ))')
                generated = True
                break

            # Double damage
            if params.get('double_damage'):
                lines.append(f'        self.register_continuous_effect(ContinuousEffect(')
                lines.append(f'            name="Double Damage",')
                lines.append(f'            affects_self_only=True,')
                lines.append(f'            # This card deals double damage')
                lines.append(f'        ))')
                generated = True
                break

            # Dynamic ATK/DEF
            if params.get('dynamic'):
                lines.append(f'        self.register_continuous_effect(ContinuousEffect(')
                lines.append(f'            name="{self._escape_name(ability.raw_text, 40)}",')
                lines.append(f'            affects_self_only=True,')
                lines.append(f'            # ATK/DEF calculated dynamically')
                lines.append(f'        ))')
                generated = True
                break

            # Simple stat modification (skip if group buff - handled above)
            if effect.action == EffectAction.MODIFY_ATK and not params.get('to_others'):
                atk_mod = params.get('atk', 0)
                def_mod = params.get('def', 0)
                if params.get('swap_stats'):
                    lines.append(f'        # Swap ATK and DEF')
                    lines.append(f'        effects = [EffectBuilder.swap_stats()]')
                    generated = True
                    break
                if atk_mod or def_mod:
                    lines.append(f'        self.register_ability(AbilityFactory.continuous_buff(')
                    lines.append(f'            atk={atk_mod},')
                    lines.append(f'            def_={def_mod},')
                    lines.append(f'            name="{self._escape_name(ability.raw_text, 30)}",')
                    lines.append(f'        ))')
                    generated = True
                    break

            # Search deck effect
            if effect.action == EffectAction.SEARCH:
                search_code = self._effect_to_code(effect)
                if search_code:
                    lines.append(f'        effects = [{search_code}]')
                generated = True
                break

            # Remove from game (exile) effect
            if effect.action == EffectAction.REMOVE_FROM_GAME:
                lines.append(f'        effects = [EffectBuilder.remove_from_game()]')
                generated = True
                break

            # Grant keyword (protection, indestructible, etc.)
            if effect.action == EffectAction.GRANT_KEYWORD:
                keyword = params.get('keyword')
                if keyword:
                    if params.get('inherent'):
                        # Inherent keyword - card has this ability naturally
                        lines.append(f'        # Inherent keyword: {keyword.name if hasattr(keyword, "name") else keyword}')
                        lines.append(f'        card.add_keyword(KeywordAbility.{keyword.name if hasattr(keyword, "name") else keyword})')
                    else:
                        # Granted keyword with duration
                        lines.append(f'        effects = [EffectBuilder.grant_keyword(KeywordAbility.{keyword.name if hasattr(keyword, "name") else keyword})]')
                    generated = True
                    # Continue to collect all keywords, don't break

        if not generated:
            # Try to generate using _effect_to_code as fallback
            effect_strs = []
            for effect in ability.effects:
                effect_code = self._effect_to_code(effect)
                if effect_code:
                    effect_strs.append(effect_code)

            if effect_strs:
                lines.append(f'        effects = [')
                for effect_code in effect_strs:
                    lines.append(f'            {effect_code},')
                lines.append(f'        ]')
                lines.append(f'        self.register_continuous_effect_with_effects(effects)')
                generated = True
            elif ability.effects:
                effect_types = [e.action.name for e in ability.effects]
                lines.append(f'        # Continuous effect with: {", ".join(effect_types)}')
                lines.append(f'        # {self._escape_name(ability.raw_text, 70)}')
            else:
                lines.append(f'        # Complex continuous effect (needs manual implementation)')
                lines.append(f'        # {self._escape_name(ability.raw_text, 70)}')

        lines.append('')
        return lines

    def _generate_replacement_effects(self, abilities: List[ParsedAbility]) -> List[str]:
        """Generate replacement effect registration method."""
        lines = []
        lines.append('    def get_replacement_effects(self, game, card):')
        lines.append('        effects = []')
        lines.append('        source_controller = card.controller')
        lines.append('')

        effect_idx = 0
        for ability in abilities:
            for repl in getattr(ability, 'replacement_effects', []) or []:
                effect_idx += 1
                event_type = repl.event_type
                event_type_code = f'ReplacementEventType.{event_type}'

                cond_parts = []
                if 'not_draw_phase' in repl.condition_flags:
                    cond_parts.append('game.current_phase != Phase.DRAW')
                if 'event_player_is_controller' in repl.condition_flags:
                    cond_parts.append('event_data.get("player") == source_controller')
                cond_code = None
                if cond_parts:
                    cond_code = ' and '.join(cond_parts)

                func_name = f'_repl_effect_{effect_idx}'
                lines.append(f'        def {func_name}(game, affected_card, event_data, source_controller=source_controller):')
                lines.append('            player = event_data.get("player", source_controller)')

                if repl.may:
                    lines.append('            if getattr(game, "_rules_engine", None) and game._rules_engine.choices:')
                    lines.append(f'                if not game._rules_engine.request_yes_no(player, card, "{self._escape_name(repl.raw_text, 60)}"):')
                    lines.append('                    return ReplacementEffectResult(was_replaced=False)')

                if repl.replacement_kind == 'skip_draw':
                    lines.append('            return ReplacementEffectResult(')
                    lines.append('                was_replaced=True,')
                    lines.append('                new_event_data={"skip_draw": True, "handled": True, "replacement_name": "skip draw"},')
                    lines.append('                continue_chain=False,')
                    lines.append('                prevent_original=True,')
                    lines.append('            )')
                elif repl.replacement_kind == 'look_pick_bottom':
                    count = repl.replacement_params.get('count', 3)
                    lines.append(f'            count = min({count}, len(game.players[player].main_deck))')
                    lines.append('            if count <= 0:')
                    lines.append('                return ReplacementEffectResult(')
                    lines.append('                    was_replaced=True,')
                    lines.append('                    new_event_data={"handled": True, "replacement_name": "look and pick"},')
                    lines.append('                    continue_chain=False,')
                    lines.append('                    prevent_original=True,')
                    lines.append('                )')
                    lines.append('            p = game.players[player]')
                    lines.append('            top_cards = p.main_deck[:count]')
                    lines.append('            p.main_deck = p.main_deck[count:]')
                    lines.append('            chosen = []')
                    lines.append('            if getattr(game, "_rules_engine", None) and game._rules_engine.choices:')
                    lines.append('                chosen = game._rules_engine.choices.request_card_from_list(')
                    lines.append('                    player, card, top_cards, count=1, up_to=False,')
                    lines.append('                    prompt="Choose a card to put into your hand"')
                    lines.append('                )')
                    lines.append('            if not chosen and top_cards:')
                    lines.append('                chosen = [top_cards[0]]')
                    lines.append('            if chosen:')
                    lines.append('                game.move_card(chosen[0], Zone.HAND, player)')
                    lines.append('            remaining = [c for c in top_cards if c not in chosen]')
                    lines.append('            if remaining:')
                    lines.append('                order = remaining')
                    lines.append('                if getattr(game, "_rules_engine", None) and game._rules_engine.choices:')
                    lines.append('                    order = game._rules_engine.choices.request_order(')
                    lines.append('                        player, card, remaining,')
                    lines.append('                        prompt="Put the rest on the bottom in any order"')
                    lines.append('                    ) or remaining')
                    lines.append('                for c in order:')
                    lines.append('                    p.main_deck.append(c)')
                    lines.append('            return ReplacementEffectResult(')
                    lines.append('                was_replaced=True,')
                    lines.append('                new_event_data={"handled": True, "replacement_name": "look and pick"},')
                    lines.append('                continue_chain=False,')
                    lines.append('                prevent_original=True,')
                    lines.append('            )')
                else:
                    effect_strs = []
                    for eff in repl.replacement_effects:
                        code = self._effect_to_code(eff)
                        if code:
                            effect_strs.append(code)
                    if effect_strs:
                        lines.append('            effects = [')
                        for code in effect_strs:
                            lines.append(f'                {code},')
                        lines.append('            ]')
                        lines.append('            for eff in effects:')
                        lines.append('                if isinstance(eff, list):')
                        lines.append('                    for sub in eff:')
                        lines.append('                        sub.execute(game, card, [], player, {})')
                        lines.append('                else:')
                        lines.append('                    eff.execute(game, card, [], player, {})')
                        lines.append('            return ReplacementEffectResult(')
                        lines.append('                was_replaced=True,')
                        lines.append('                new_event_data={"handled": True, "replacement_name": "replacement"},')
                        lines.append('                continue_chain=False,')
                        lines.append('                prevent_original=True,')
                        lines.append('            )')
                    else:
                        lines.append('            return ReplacementEffectResult(was_replaced=False)')

                lines.append('')
                lines.append('        effects.append(ReplacementEffectCR(')
                lines.append(f'            name="{self._escape_name(repl.raw_text, 60)}",')
                lines.append(f'            replaces={event_type_code},')
                lines.append(f'            replacement={func_name},')
                if repl.affects_self_only:
                    lines.append('            affects_self_only=True,')
                if repl.affects_source_controller_only and event_type != 'WOULD_DRAW':
                    lines.append('            affects_source_controller_only=True,')
                if cond_code:
                    lines.append(f'            event_condition=lambda game, c, event_data, source_controller=source_controller: {cond_code},')
                lines.append('            is_self_replacement=True,')
                lines.append('        ))')
                lines.append('')

        lines.append('        return effects')
        lines.append('')
        return lines

    def _generate_spell_effect(self, ability: ParsedAbility) -> List[str]:
        """Generate spell effect (what happens when spell resolves)."""
        lines = []
        lines.append(f'        # Spell effect')

        # Generate effects list for the spell
        effect_strs = []
        for effect in ability.effects:
            effect_code = self._effect_to_code(effect)
            if effect_code:
                effect_strs.append(effect_code)

        if effect_strs:
            lines.append(f'        effects = [')
            for effect_code in effect_strs:
                lines.append(f'            {effect_code},')
            lines.append(f'        ]')
            lines.append(f'        self.register_spell_effect(effects)')
        else:
            # Fallback for unhandled spell effects
            effect_types = [e.action.name for e in ability.effects]
            lines.append(f'        # Effects: {", ".join(effect_types)}')
            lines.append(f'        # {self._escape_name(ability.raw_text, 70)}')

        lines.append('')
        return lines

    def _generate_effects_list(self, effects: List[ParsedEffect]) -> str:
        """Generate list of Effect objects from parsed effects."""
        if not effects:
            return '[]'

        effect_strs = []
        for effect in effects:
            effect_str = self._effect_to_code(effect)
            if effect_str:
                effect_strs.append(effect_str)

        if not effect_strs:
            return '[]'

        return '[' + ', '.join(effect_strs) + ']'

    def _effect_to_code(self, effect: ParsedEffect) -> Optional[str]:
        """Convert a parsed effect to code string."""
        action = effect.action
        params = effect.params

        if action == EffectAction.DRAW:
            count = params.get('count', 1)
            if params.get('variable'):
                return 'EffectBuilder.draw_variable()'
            return f'EffectBuilder.draw({count})'

        elif action == EffectAction.DEAL_DAMAGE:
            amount = params.get('amount', 0)
            if params.get('x_variable'):
                return 'EffectBuilder.deal_damage_x()'
            if params.get('equal_to_atk'):
                return 'EffectBuilder.deal_damage_equal_to_atk()'
            if params.get('variable_x'):
                return 'EffectBuilder.deal_damage_variable()'
            if params.get('mutual'):
                return 'EffectBuilder.deal_damage_mutual()'
            return f'EffectBuilder.deal_damage({amount})'

        elif action == EffectAction.DESTROY:
            return 'EffectBuilder.destroy()'

        elif action == EffectAction.RETURN_TO_HAND:
            from_zone = params.get('from_zone')
            if from_zone == 'graveyard':
                return 'EffectBuilder.return_from_graveyard()'
            return 'EffectBuilder.return_to_hand()'

        elif action == EffectAction.GAIN_LIFE:
            amount = params.get('amount', 0)
            if params.get('equal_to_damage'):
                return 'EffectBuilder.gain_life_equal_to_damage()'
            return f'EffectBuilder.gain_life({amount})'

        elif action == EffectAction.LOSE_LIFE:
            amount = params.get('amount', 0)
            return f'EffectBuilder.lose_life({amount})'

        elif action == EffectAction.PRODUCE_WILL:
            colors = params.get('colors', ['VOID'])
            if params.get('any_color'):
                return 'EffectBuilder.produce_will_any()'
            if len(colors) == 1:
                return f'EffectBuilder.produce_will(Attribute.{colors[0]})'
            return f'EffectBuilder.produce_will(Attribute.{colors[0]})'

        elif action == EffectAction.REST:
            if params.get('x_variable'):
                return 'EffectBuilder.rest_x_targets()'
            return 'EffectBuilder.rest()'

        elif action == EffectAction.RECOVER:
            return 'EffectBuilder.recover()'

        elif action == EffectAction.CANCEL:
            return 'EffectBuilder.cancel()'

        elif action == EffectAction.ADD_COUNTER:
            counter_type = params.get('counter_type', 'generic')
            return f'EffectBuilder.add_counter("{counter_type}")'

        elif action == EffectAction.REMOVE_COUNTER:
            counter_type = params.get('counter_type', 'generic')
            return f'EffectBuilder.remove_counter("{counter_type}")'

        elif action in (EffectAction.MODIFY_ATK, EffectAction.MODIFY_DEF, EffectAction.SET_ATK):
            atk = params.get('atk', 0)
            def_ = params.get('def', 0)
            if params.get('swap_stats'):
                return 'EffectBuilder.swap_stats()'
            if params.get('scaling'):
                atk_per = params.get('atk_per', 0)
                def_per = params.get('def_per', 0)
                return f'EffectBuilder.scaling_buff({atk_per}, {def_per})'
            if params.get('dynamic'):
                return 'EffectBuilder.dynamic_stats()'
            if params.get('double_damage'):
                return 'EffectBuilder.double_damage()'
            if params.get('replacement'):
                return 'EffectBuilder.damage_replacement()'
            duration = effect.duration
            dur_str = 'EffectDuration.UNTIL_END_OF_TURN' if duration == EffectDuration.UNTIL_END_OF_TURN else 'EffectDuration.INSTANT'
            return f'EffectBuilder.buff({atk}, {def_}, {dur_str})'

        elif action == EffectAction.GRANT_KEYWORD:
            keyword = params.get('keyword', KeywordAbility.NONE)
            if keyword != KeywordAbility.NONE:
                return f'EffectBuilder.grant_keyword(KeywordAbility.{keyword.name})'
            # Handle special grant types
            if params.get('force_attack'):
                return 'EffectBuilder.force_attack()'
            if params.get('force_block'):
                return 'EffectBuilder.force_block()'
            if params.get('redirect'):
                return 'EffectBuilder.redirect_target()'
            if params.get('to_others'):
                return 'EffectBuilder.grant_to_others()'
            if params.get('end_of_turn_trigger'):
                return 'EffectBuilder.end_of_turn_trigger()'
            if params.get('on_targeted'):
                return 'EffectBuilder.on_targeted_trigger()'
            if params.get('play_restriction'):
                return 'EffectBuilder.play_restriction()'
            if params.get('move'):
                return 'EffectBuilder.move_addition()'

        elif action == EffectAction.REMOVE_FROM_GAME:
            return 'EffectBuilder.remove_from_game()'

        elif action == EffectAction.PUT_INTO_FIELD:
            from_zone = params.get('from_zone', 'hand')
            if params.get('x_variable'):
                return 'EffectBuilder.put_into_field_x_cost()'
            if params.get('on_added_death'):
                return 'EffectBuilder.put_on_added_death()'
            if params.get('this_turn'):
                return f'EffectBuilder.put_into_field(from_zone="{from_zone}", this_turn=True)'
            return f'EffectBuilder.put_into_field(from_zone="{from_zone}")'

        elif action == EffectAction.SEARCH:
            dest = params.get('destination', 'hand')
            if params.get('on_death'):
                return f'EffectBuilder.search_on_death(destination="{dest}")'
            kwargs = [f'destination="{dest}"']
            if params.get('filter_type'):
                kwargs.append(f'filter_type={params.get("filter_type")!r}')
            if params.get('filter_name'):
                kwargs.append(f'filter_name={params.get("filter_name")!r}')
            if params.get('filter_race'):
                kwargs.append(f'filter_race={params.get("filter_race")!r}')
            if params.get('reveal') is True:
                kwargs.append('reveal=True')
            if params.get('shuffle') is False:
                kwargs.append('shuffle=False')
            if params.get('optional_destination'):
                kwargs.append(f'optional_destination={params.get("optional_destination")!r}')
            if params.get('conditional_ruler_name'):
                kwargs.append(f'conditional_ruler_name={params.get("conditional_ruler_name")!r}')
            return f'EffectBuilder.search({", ".join(kwargs)})'

        elif action == EffectAction.BANISH:
            if params.get('self') and params.get('conditional'):
                return 'EffectBuilder.banish_self_conditional()'
            if params.get('controller') == 'opponent':
                return 'EffectBuilder.opponent_banishes()'
            return 'EffectBuilder.banish()'

        elif action == EffectAction.DISCARD:
            if params.get('all'):
                return 'EffectBuilder.discard_all()'
            count = params.get('count', 1)
            return f'EffectBuilder.discard({count})'

        elif action == EffectAction.GAIN_CONTROL:
            return 'EffectBuilder.gain_control()'

        elif action == EffectAction.REMOVE_ABILITY:
            if params.get('all'):
                return 'EffectBuilder.remove_all_abilities()'
            if params.get('restriction'):
                return 'EffectBuilder.add_restriction()'
            if params.get('prevent_recovery'):
                return 'EffectBuilder.prevent_recovery()'
            return 'EffectBuilder.remove_ability()'

        elif action == EffectAction.REVEAL:
            if params.get('from_top'):
                kwargs = []
                if params.get('deck_type'):
                    kwargs.append(f'deck_type={params.get("deck_type")!r}')
                if params.get('count') is not None:
                    kwargs.append(f'count={params.get("count")}')
                if params.get('condition_attribute'):
                    kwargs.append(f'condition_attribute={params.get("condition_attribute")!r}')
                if params.get('move_if_condition'):
                    kwargs.append('move_if_condition=True')
                if params.get('move_zone'):
                    kwargs.append(f'move_zone={params.get("move_zone")!r}')
                if kwargs:
                    return f'EffectBuilder.reveal_top({", ".join(kwargs)})'
                return 'EffectBuilder.reveal_top()'
            if params.get('secret_choice'):
                return 'EffectBuilder.secret_choice()'
            return 'EffectBuilder.reveal()'

        elif action == EffectAction.PREVENT_DAMAGE:
            if params.get('redirect'):
                return 'EffectBuilder.redirect_damage()'
            if params.get('next_only'):
                return 'EffectBuilder.prevent_next_damage()'
            if params.get('all'):
                if params.get('battle_only'):
                    return 'EffectBuilder.prevent_all_battle_damage()'
                return 'EffectBuilder.prevent_all_damage()'
            return 'EffectBuilder.prevent_damage()'

        elif action == EffectAction.PUT_ON_TOP_OF_DECK:
            return 'EffectBuilder.put_on_top_of_deck()'

        elif action == EffectAction.SHUFFLE_INTO_DECK:
            return 'EffectBuilder.shuffle_into_deck()'

        # ====== CR 1007: REMOVE_DAMAGE ======
        elif action == EffectAction.REMOVE_DAMAGE:
            if params.get('all'):
                return 'EffectBuilder.remove_all_damage()'
            amount = params.get('amount', 0)
            return f'EffectBuilder.remove_damage({amount})'

        # ====== CR 1006: SUMMON ======
        elif action == EffectAction.SUMMON:
            return 'EffectBuilder.summon()'

        # ====== CR 1017: COPY ======
        elif action == EffectAction.COPY:
            copy_type = params.get('type', 'spell')
            if copy_type == 'entity':
                return 'EffectBuilder.copy_entity()'
            return 'EffectBuilder.copy_spell()'

        # ====== CR 1017: BECOME_COPY ======
        elif action == EffectAction.BECOME_COPY:
            return 'EffectBuilder.become_copy()'

        # ====== CR 1014: LOOK ======
        elif action == EffectAction.LOOK:
            count = params.get('count', 1)
            if params.get('foresee'):
                return f'EffectBuilder.foresee({count})'
            return f'EffectBuilder.look({count})'

        # ====== PUT_ON_BOTTOM_OF_DECK ======
        elif action == EffectAction.PUT_ON_BOTTOM_OF_DECK:
            return 'EffectBuilder.put_on_bottom_of_deck()'

        # ====== PUT_INTO_GRAVEYARD ======
        elif action == EffectAction.PUT_INTO_GRAVEYARD:
            return 'EffectBuilder.put_into_graveyard()'

        # ====== SET_LIFE ======
        elif action == EffectAction.SET_LIFE:
            amount = params.get('amount', 0)
            return f'EffectBuilder.set_life({amount})'

        # ====== SET_ATK / SET_DEF ======
        elif action == EffectAction.SET_ATK:
            if 'def' in params:
                atk = params.get('atk', 0)
                def_ = params.get('def', 0)
                return f'EffectBuilder.set_stats({atk}, {def_})'
            value = params.get('value', 0)
            return f'EffectBuilder.set_atk({value})'

        elif action == EffectAction.SET_DEF:
            value = params.get('value', 0)
            return f'EffectBuilder.set_def({value})'

        # ====== GRANT_RACE ======
        elif action == EffectAction.GRANT_RACE:
            race = params.get('race', 'Unknown')
            if params.get('replace'):
                return f'EffectBuilder.set_race("{race}")'
            return f'EffectBuilder.grant_race("{race}")'

        # ====== GRANT_ATTRIBUTE / SET_ATTRIBUTE ======
        elif action == EffectAction.GRANT_ATTRIBUTE:
            attr = params.get('attribute', 'VOID')
            return f'EffectBuilder.grant_attribute(Attribute.{attr})'

        elif action == EffectAction.SET_ATTRIBUTE:
            attr = params.get('attribute', 'VOID')
            return f'EffectBuilder.set_attribute(Attribute.{attr})'

        # ====== REMOVE_KEYWORD ======
        elif action == EffectAction.REMOVE_KEYWORD:
            keyword = params.get('keyword', KeywordAbility.NONE)
            if keyword != KeywordAbility.NONE:
                return f'EffectBuilder.remove_keyword(KeywordAbility.{keyword.name})'
            return None

        # ====== GRANT_ABILITY (complex) ======
        elif action == EffectAction.GRANT_ABILITY:
            if params.get('move'):
                return 'EffectBuilder.move_addition()'
            if params.get('call_stone'):
                return 'EffectBuilder.call_magic_stone()'
            if params.get('force_attack'):
                return 'EffectBuilder.force_attack()'
            if params.get('force_block'):
                return 'EffectBuilder.force_block()'
            if params.get('redirect'):
                return 'EffectBuilder.redirect_target()'
            # Generic grant ability
            return 'EffectBuilder.grant_ability()'

        return None

    def _generate_modal_ability(self, ability: ParsedAbility) -> List[str]:
        """Generate modal 'Choose one/two' ability."""
        lines = []
        lines.append(f'        # Modal ability: Choose {ability.modal_count}')

        # Generate choice options
        choices_code = []
        for i, choice in enumerate(ability.modal_choices):
            effect_code = self._effect_to_code(choice.effect) or 'None'
            safe_text = self._escape_name(choice.raw_text, 30)
            choices_code.append((safe_text, effect_code))

        if ability.ability_type == AbilityType.AUTOMATIC and ability.trigger_condition:
            lines.append(f'        modal_modes = [')
            for safe_text, effect_code in choices_code:
                lines.append(
                    f'            Mode(name="{safe_text}", description="{safe_text}", '
                    f'operation=lambda game, card, event_data, eff={effect_code}: '
                    f'eff.execute(game, card, [], card.controller, {{}})),'
                )
            lines.append(f'        ]')
            lines.append(f'        modal = ModalChoice(')
            lines.append(f'            modes=modal_modes,')
            lines.append(f'            choose_count={ability.modal_count},')
            lines.append(f'            prompt="Choose one",')
            lines.append(f'        )')
            lines.append(f'        self.register_ability(AutomaticAbility(')
            lines.append(f'            name="Modal Choice",')
            lines.append(f'            trigger_condition=TriggerCondition.{ability.trigger_condition.name},')
            lines.append(f'            modal=modal,')
            lines.append(f'            is_mandatory={ability.is_mandatory},')
            lines.append(f'        ))')
            lines.append('')
            return lines

        lines.append(f'        modal_choices = [')
        for safe_text, effect_code in choices_code:
            lines.append(f'            ("{safe_text}", {effect_code}),')
        lines.append(f'        ]')

        # Generate upgrade condition if present
        if ability.modal_upgrade_condition:
            lines.append(f'        # Upgrade: {ability.modal_upgrade_condition[:50]}')
            lines.append(f'        modal_upgrade_count = {ability.modal_upgrade_count}')
            condition_code = self._build_upgrade_condition_code(ability.modal_upgrade_condition)
            if condition_code:
                lines.append(f'        modal_upgrade_condition = {condition_code}')
            else:
                lines.append(f'        modal_upgrade_condition = None')

        lines.append(f'        self.register_ability(ModalAbility(')
        lines.append(f'            name="Modal Choice",')
        lines.append(f'            choices=modal_choices,')
        lines.append(f'            choose_count={ability.modal_count},')
        if ability.modal_upgrade_condition:
            lines.append(f'            upgrade_condition=modal_upgrade_condition,')
            lines.append(f'            upgrade_count=modal_upgrade_count,')
        lines.append(f'        ))')
        lines.append('')
        return lines

    def _generate_incarnation(self, ability: ParsedAbility) -> List[str]:
        """Generate Incarnation alternative cost."""
        if not ability.incarnation:
            return []

        lines = []
        inc = ability.incarnation
        attrs = ', '.join(f'Attribute.{a}' for a in inc.attributes)

        lines.append(f'        # Incarnation alternative cost')
        lines.append(f'        self.register_alternative_cost(IncarnationCost(')
        lines.append(f'            required_attributes=[{attrs}],')
        lines.append(f'            banish_count={inc.count},')
        lines.append(f'        ))')
        lines.append('')
        return lines

    def _generate_awakening(self, ability: ParsedAbility) -> List[str]:
        """Generate Awakening enhanced cost."""
        if not ability.awakening:
            return []

        lines = []
        awk = ability.awakening

        # Build will cost string
        will_parts = []
        for attr, count in awk.will.items():
            if attr == 'GENERIC':
                will_parts.append(f'generic={count}')
            else:
                will_parts.append(f'{attr.lower()}={count}')

        if awk.x_cost:
            will_parts.append('x_cost=True')

        will_str = ', '.join(will_parts) if will_parts else ''

        lines.append(f'        # Awakening enhanced cost')
        lines.append(f'        self.awakening_cost = AwakeningCost({will_str})')
        lines.append(f'        # Enhanced effect triggers when awakening cost is paid')
        lines.append('')
        return lines

    def _generate_x_cost_ability(self, ability: ParsedAbility) -> List[str]:
        """Generate ability with X cost."""
        lines = []
        lines.append(f'        # Activated ability with X cost')
        lines.append(f'        self.register_ability(ActivateAbility(')
        lines.append(f'            name="{self._escape_name(ability.raw_text)}",')

        if ability.cost:
            if ability.cost.tap:
                lines.append(f'            tap_cost=True,')
            lines.append(f'            x_cost=True,')
            if ability.cost.generic:
                lines.append(f'            generic_cost={ability.cost.generic},')

        # Generate effects that use X
        effects_code = self._generate_effects_list(ability.effects)
        lines.append(f'            effects={effects_code},')
        lines.append(f'            uses_x=True,  # Effect uses X value from cost')
        lines.append(f'        ))')
        lines.append('')
        return lines

    def _generate_judgment_ability(self, code: str, judgment_cost: 'ParsedCost') -> List[str]:
        """Generate Judgment ability for Rulers."""
        lines = []

        # Derive J-Ruler code from Ruler code (e.g., CMF-013 -> CMF-013J)
        j_ruler_code = code + 'J'

        lines.append(f'        # Judgment ability - flip to J-Ruler')

        # Build will cost string
        will_parts = []
        for attr, count in judgment_cost.will.items():
            will_parts.append(f'{attr.lower()}={count}')
        if judgment_cost.generic:
            will_parts.append(f'generic={judgment_cost.generic}')

        will_str = ', '.join(will_parts) if will_parts else ''

        lines.append(f'        self.register_ability(JudgmentAbility(')
        lines.append(f'            name="Judgment",')
        if will_str:
            lines.append(f'            will_cost=WillCost({will_str}),')
        lines.append(f'            j_ruler_code="{j_ruler_code}",')
        lines.append(f'        ))')
        lines.append('')
        return lines


# Global generator instance
cr_generator = CRScriptGenerator()


def generate_cr_scripts_for_set(db, set_code: str, output_dir: Path):
    """Generate CR-compliant script files for all cards in a set."""
    cards = db.search_cards(set_code=set_code)

    if not cards:
        print(f"No cards found for set {set_code}")
        return

    card_dicts = []
    for card in cards:
        card_dicts.append({
            'code': card.code,
            'name': card.name,
            'card_type': card.card_type.name,
            'ability_text': card.ability_text,
            'attribute': card.attribute.name if card.attribute else None,
        })

    content = cr_generator.generate_file(card_dicts, set_code)

    output_file = output_dir / f"{set_code.lower()}_cr.py"
    output_file.write_text(content)
    print(f"Generated {output_file}")


def generate_all_cr_scripts(db, output_dir: Path):
    """Generate CR-compliant scripts for all sets."""
    output_dir.mkdir(parents=True, exist_ok=True)

    init_content = '"""Auto-generated CR-compliant card scripts"""\n\n'

    sets = ['CMF', 'TAT', 'MPR', 'MOA']
    for set_code in sets:
        generate_cr_scripts_for_set(db, set_code, output_dir)
        init_content += f'from .{set_code.lower()}_cr import *\n'

    (output_dir / '__init__.py').write_text(init_content)
    print(f"Generated {output_dir / '__init__.py'}")
