# Generated Card Scripts (fowpro/scripts/generated/*, fowpro/cards/generated/__init__.py)

## Files
- `fowpro/scripts/generated/cmf_cr.py`
- `fowpro/scripts/generated/mpr_cr.py`
- `fowpro/scripts/generated/moa_cr.py`
- `fowpro/scripts/generated/tat_cr.py`
- `fowpro/scripts/generated/__init__.py`
- `fowpro/cards/generated/__init__.py` (imports the generated sets)

## Structure (observed)
- Each file contains many `@ScriptRegistry.register("SET-NNN")` classes.
- Each class extends `RulesCardScript` and typically implements:
  - `initial_effect()` registering abilities via `ActivateAbility`, `AutomaticAbility`, `ContinuousAbility`, `ModalAbility`, etc.
  - `get_keywords()` for static keyword grants.
- Effects are constructed through `EffectBuilder` helpers in `rules_bridge.py`.

## Common patterns
- Simple continuous effects: `EffectBuilder.grant_keyword(...)`.
- Activated abilities: `ActivateAbility` with optional `tap_cost`, `will_cost`, `once_per_turn`.
- Enter-field triggers: `AutomaticAbility` with `TriggerCondition.ENTER_FIELD`.
- Modal spells: `ModalAbility` with `choices` and `choose_count`.

## TODOs / incomplete logic
- Detected TODO markers (counts by file):
- `cmf_cr.py`: 1 TODO
- `moa_cr.py`: 0 TODO
- `mpr_cr.py`: 0 TODO
- `tat_cr.py`: 0 TODO
- TODOs are usually for missing condition checks or modal upgrades.
- Modal upgrade conditions are recognized but not wired into logic (placeholder only).
- Targeting details are often generic; some abilities register no explicit targets.

## Practical impact
- These scripts are a wide scaffold for the Grimm Cluster card pool but depend on:
  - the rules engine and effect builder being complete,
  - correct target validation and condition checks.
- As-is, a large portion of card text is represented only partially or with placeholders.

## Quick counts (per file)
- `cmf_cr.py`: 114 registered scripts/classes, 2664 lines
- `moa_cr.py`: 50 registered scripts/classes, 1291 lines
- `mpr_cr.py`: 110 registered scripts/classes, 2652 lines
- `tat_cr.py`: 110 registered scripts/classes, 2602 lines
