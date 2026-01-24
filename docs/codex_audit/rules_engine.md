# Rules Engine (fowpro/rules/*)

## Entry points
- `fowpro/rules/integration.py`: `RulesEngine` wrapper used by `GameEngine`.
- `fowpro/rules/__init__.py`: re-exports rule types and helpers.

## Major components (observed)
- Types and data:
  - `types.py`: enums for ability/effect types, targeting, triggers, costs, layers.
- Abilities:
  - `abilities.py`: `Ability`, `ActivateAbility`, `AutomaticAbility`, `ContinuousAbility`, `WillAbility`, `JudgmentAbility`.
- Effects and execution:
  - `effects.py`: effect object, resolution hooks, and effect action helpers.
  - `replacement.py`: replacement effect representation.
  - `layers.py`: layer system for continuous effects (includes TODOs).
- Costs:
  - `costs.py`: cost model and `CostManager` to validate/pay costs.
- Targeting and choices:
  - `targeting.py`: `TargetFilter`, `TargetRequirement`, zone/controller filters, validation.
  - `choices.py`: `ChoiceManager` for prompts and selection flows.
  - `modals.py`: modal abilities and modal choices.
- Triggers and priority:
  - `triggers.py`: trigger system, TODOs for target validation and pending triggers.
  - `priority.py`: priority logic and stack/chase handling (assumes `Phase.BATTLE` exists).
- Keywords/conditions:
  - `keywords.py`: keyword effects (barrier, swiftness, etc.).
  - `conditions.py`: condition building for effects.

## Integration behavior (observed)
- `RulesEngine` registers with `GameEngine` event hooks and provides:
  - cost payment/validation,
  - modal choice requests,
  - replacement effect check for damage (`would_deal_damage()`),
  - continuous effect application,
  - effect resolution pipeline.

## Known mismatches / TODOs (code-level)
- `priority.py` expects a `Phase.BATTLE`, but `GameEngine` has no battle phase (combat is inside `MAIN`).
- Trigger handling has TODOs for legality checks, target validation, and trigger ordering.
- Layer system includes TODO for `STAT_CDA` pass.
- Replacement effects selection (multiple replacements) is stubbed or uses a default choice.

## Practical impact
- The rules engine exists and is wired into `GameEngine`, but several sub-systems are incomplete or stubbed.
- These gaps can cause effects to resolve without proper legality checks or correct ordering in complex interactions.
