# FoWPro v1 Reality Check (Code-Based)

This summary is based on the actual v1 code paths in `fowpro/` (engine + rules + scripts + GUI). It does not rely on the project docs.

## What clearly exists and is wired up

### Core game loop
- Turn structure with phases: Draw -> Recovery -> Main -> End.
- Priority system with pass tracking and chase (stack) resolution.
- Chase items for spells/abilities/judgment with LIFO resolution.
- State-based actions checks after key state changes.

### Zones and movement
- Zones are modeled and card movement is implemented (hand/field/graveyard/deck/stone deck/chase/ruler area).
- Zone transitions emit events and are tracked for triggers.

### Combat (as an action in Main Phase)
- Attacking is allowed only in Main Phase (no separate Battle Phase in v1 engine).
- Attack declaration rules implemented:
  - summoning sickness unless Swiftness,
  - cannot attack with `CANNOT_ATTACK`,
  - direct attacking a resonator requires `TARGET_ATTACK`,
  - attacking recovered resonators requires `PRECISION`.
- Blocking rules implemented:
  - cannot block with `CANNOT_BLOCK`,
  - cannot block `UNBLOCKABLE` or `STEALTH` attackers,
  - `FLYING` checks.
- Damage steps implemented (first strike, normal damage, multiple blockers, Pierce, Drain).

### Will / stones
- Will pool exists (mutable) with pay/produce logic.
- Call stone implemented with ruler rest requirement (engine enforces rested ruler for stone call).
- Magic stone scripts (basic/dual/special) exist and return possible will colors.

### Ruler / Judgment
- Judgment cost checking and chase item creation exists.
- Ruler rests when judgment is performed.

### Scripts and registry
- Script registry is functional; default script and generated scripts are loaded.
- Generated scripts exist for Grimm cluster sets (CMF/MPR/MOA/TAT) with 300+ classes.

### GUI
- Full GUI stack exists (menu, duel screen, deck editor, dialogs, styles).
- GUI calls into `GameEngine` for actions and uses engine state to render.

## Partially implemented or fragile

### Rules engine integration
- `RulesEngine` is hooked into `GameEngine`, but multiple submodules are TODO or stubbed.
- Trigger legality checks and target validation are incomplete in rules engine.
- Layering system contains TODOs and does not fully implement CDA/continuous stacking.
- Replacement effect selection is stubbed when multiple replacements apply.

### Effects / ability resolution
- Effect builders and ability objects exist, but many effects rely on missing target checks or simplified rules.
- Modal spells are supported, but conditional upgrades are not implemented.
- Continuous effects are supported via manager, but full layer interaction is incomplete.

### Generated card scripts
- Large coverage of card scripts exists, but:
  - targeting is often generic or absent,
  - complex conditions are TODO,
  - some scripts only grant keywords without full rules nuance.

### Stone special abilities
- Some special stones rely on GUI prompts or internal defaults (e.g., Little Red choosing a color defaults without prompt).
- Activated abilities on stones depend on general activated-ability handling and target selection.

### AI
- Random AI exists and can drive basic actions, but no deep rules evaluation.

## Likely missing or incorrect vs real rules

### Priority windows and timing
- Priority system exists, but its interaction with triggers/continuous effects depends on incomplete rules engine modules.
- Trigger ordering and legality checks may not match CR for simultaneous triggers.

### Battle phase vs Main phase
- Engine implements combat inside Main Phase and does not model a Battle Phase.
- `rules/priority.py` expects `Phase.BATTLE`, which is inconsistent with engine behavior.

### Targeting and legality
- Many effect target requirements are not enforced during resolution (fizzle behavior is only partially implemented).
- Some effect handlers do not re-check legality on resolution.

### Layering / continuous effects
- Stat/keyword modifications exist, but full layer ordering and interactions are not fully enforced.

### Card text accuracy
- Generated scripts represent many cards but do not fully model CR edge cases, replacement effects, and conditional upgrades.

## Summary: current reality of v1

What is solid and usable today:
- Turn flow and zones
- Combat as a main-phase action
- Basic chase resolution
- Stone calling and will production
- Judgment process
- GUI and deck handling

What is incomplete or unstable:
- Rules engine correctness (targets, triggers, layering, replacements)
- Accurate card effect handling for most complex cards
- Strict CR timing and ordering

If the goal is rules-accurate gameplay, the biggest risks are in the effect system and rules engine, not the turn/combat loop.
