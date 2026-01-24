# Engine (fowpro/engine.py)

## High-level structure
- `GameEngine` is the core runtime. It owns players, turn/phase state, chase stack, combat state, card registry, and event queue.
- Effect systems are split into:
  - `TriggerManager` (script triggers),
  - `ContinuousEffectManager` (continuous effects),
  - `ChoiceManager` (targeting/choices),
  - `RulesEngine` wrapper (`fowpro/rules/integration.py`) which is instantiated in `__init__` to hook rules logic.
- Script loading is lazy via `ScriptRegistry`; `scripts.default` and `scripts.generated` are imported if present.

## Turn structure (observed)
- Phases used by engine: `DRAW`, `RECOVERY`, `MAIN`, `END` (no `BATTLE` phase in `GameEngine`).
- `start_game()` -> initial shuffles, draw hands, sets up first turn, then `change_phase(Phase.DRAW)`.
- `change_phase()` triggers phase entry effects and `check_state_based_actions()`.
- `next_phase()` cycles through `[DRAW, RECOVERY, MAIN, END]`.
- Will pool is cleared at Recovery (rule 503.4) and at End (rule 505.5c).

## Priority system (observed)
- `give_priority(player)` sets the current priority player.
- Passing priority is tracked with `consecutive_passes` and event `BOTH_PASSED` triggers `resolve_chase()`.
- Priority is given to opponent after playing a resonator or addition; spells go to chase.

## Chase (stack)
- `ChaseItem` stores spell/ability/judgment effects, targets, paid cost, and `effect_data` (e.g., modal choices).
- Spells are moved to `Zone.CHASE` and added as `ChaseItem`.
- `resolve_chase()` resolves LIFO and handles fizzle if targets became illegal (CR 903.5).

## Combat model (battle is an action within Main phase)
- `declare_attack()` only allowed during `Phase.MAIN` (not a separate battle phase).
- Combat is tracked via `BattleContext` and `CombatStep` sequence:
  `DECLARE_ATTACK -> DECLARE_BLOCKER -> BEFORE_DAMAGE -> FIRST_STRIKE_DAMAGE -> NORMAL_DAMAGE -> AFTER_DAMAGE -> END_OF_BATTLE`.
- Attack restrictions enforced:
  - summoning sickness (unless `SWIFTNESS`),
  - `CANNOT_ATTACK` keyword,
  - direct attack vs resonator attack requires `TARGET_ATTACK`,
  - attacking recovered resonators requires `PRECISION`.
- Block restrictions enforced:
  - `CANNOT_BLOCK`,
  - `UNBLOCKABLE`/`STEALTH` on attacker,
  - `FLYING` vs non-flying blocker.
- Damage logic:
  - Supports first strike, normal damage, multiple blockers with damage assignment (CR 807.3), `PIERCE`, `DRAIN`.

## Damage and state-based actions
- `_deal_damage_to_card()` consults rules engine replacement effects via `RulesEngine.would_deal_damage()`.
- `check_state_based_actions()` handles lethal damage -> destruction, and ruler loss conditions.

## Ruler/Judgment
- `perform_judgment()` pays judgment cost (if any), rests the ruler, and pushes a `JUDGMENT` chase item.

## Notable integrations and gaps
- Rules integration is present but many rules modules contain TODOs; see `docs/codex_audit/rules_engine.md`.
- `GameEngine` treats combat as part of `MAIN` phase. `rules/priority.py` assumes a `BATTLE` phase exists (mismatch).
- Modal spell choice exists: engine checks for `ModalAbility` in script `_abilities` and records selections in `ChaseItem.effect_data`.
