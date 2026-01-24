# FoWPro v1 Fix List (Detailed)

This document expands the Top-10 mismatches into concrete, code-level fixes. The goal is rules-accurate gameplay in v1.

## Progress
- 2026-01-24: Updated `rules/priority.py` to align combat actions with v1 engine (Main Phase combat action, no Battle Phase).
- 2026-01-24: Trigger targets now selected on chase entry and revalidated on resolution; basic fizzle handling added for invalid targets.
- 2026-01-24: CR ActivateAbility support in `GameEngine` (costs paid on activation, chase resolution executes effects, target revalidation).
- 2026-01-24: Replacement effect selection now uses a modal choice when UI callback is available; falls back to first effect.
- 2026-01-24: Little Red stone now prompts for attribute choice via rules engine UI when available.
- 2026-01-24: Spell target revalidation now checks script target requirements in addition to barrier/zone checks.
- 2026-01-24: CR ActivateAbility main-timing check now uses `game.battle.in_battle` when `game.in_battle` is absent.
- 2026-01-24: Added legacy `ActivatedAbility` wrapper for stone scripts and wired target prompts for legacy abilities.
- 2026-01-24: Legacy activated ability resolution now passes targets when available.
- 2026-01-24: Legacy activated abilities now revalidate targets on resolution and fizzle if all required targets are illegal.
- 2026-01-24: Multi-color will production now prompts for attribute choice when UI callback is available.
- 2026-01-24: Layer system now applies STAT_CDA `set_atk/set_def` instead of skipping CDA pass.

## 1) Combat phase vs priority mismatch

**Problem**
- `GameEngine` has no `Phase.BATTLE`; combat is handled inside `Phase.MAIN`.
- `fowpro/rules/priority.py` assumes `Phase.BATTLE` exists and may open priority windows incorrectly.

**Code refs**
- `fowpro/engine.py` (combat methods and phase sequencing)
- `fowpro/rules/priority.py` (priority windows)

**Fix options**
- Option A (minimal): Update `rules/priority.py` to align with v1 engine (no battle phase).
- Option B (larger): Add `Phase.BATTLE` to engine and adjust phase progression + combat flow.

**Recommendation**
- Option A first (smaller diff, keeps v1 behavior consistent with your design choice).

**Expected outcome**
- Priority windows and combat actions align with engine’s phase model.

---

## 2) Trigger legality checks + APNAP ordering

**Problem**
- Trigger legality checks are incomplete and APNAP ordering is not fully enforced.

**Code refs**
- `fowpro/rules/triggers.py`
- `fowpro/rules/priority.py`
- `fowpro/engine.py` (event emission)

**Fix**
- Implement legality checks at trigger creation and before resolution.
- Apply APNAP ordering for triggers that are added simultaneously.

**Expected outcome**
- Trigger timing and ordering matches CR 906.

---

## 3) Target revalidation + fizzle on resolution

**Problem**
- Targets are often not revalidated on resolution; fizzle is not consistently applied.

**Code refs**
- `fowpro/rules/targeting.py`
- `fowpro/rules/effects.py`
- `fowpro/engine.py` (chase resolution)

**Fix**
- Enforce target legality checks at resolution.
- Apply fizzle rule to all chase items with targets.

**Expected outcome**
- Effects that lose all legal targets fizzle correctly (CR 903.5).

---

## 4) Replacement effects: multiple replacement choice

**Problem**
- Replacement effects select the first matching effect; affected player choice is not implemented.

**Code refs**
- `fowpro/rules/replacement.py`
- `fowpro/rules/integration.py`

**Fix**
- Implement player choice when multiple replacement effects apply.
- Add a simple UI/choice manager hook to choose replacement.

**Expected outcome**
- Replacement effects follow CR 910 (affected player chooses).

---

## 5) Layer system completion

**Problem**
- Continuous effect layering contains TODOs (CDA/stat pass).

**Code refs**
- `fowpro/rules/layers.py`

**Fix**
- Implement missing layer pass(es) with correct ordering.
- Ensure stat modifications apply after CDA and before keyword updates as required.

**Expected outcome**
- Continuous effects interact correctly.

---

## 6) Modal upgrade conditions

**Problem**
- Modal upgrades (“choose more if condition”) are recognized but not implemented.

**Code refs**
- `fowpro/scripts/rules_bridge.py`
- `fowpro/rules/modals.py`
- `fowpro/scripts/generated/*.py`

**Fix**
- Add condition checks for modal upgrades.
- Allow dynamic `choose_count` based on condition.

**Expected outcome**
- Modal choices match card text for upgrade cases.

---

## 7) Generated script target filters

**Problem**
- Generated scripts often omit targeting requirements or use generic targets.

**Code refs**
- `fowpro/scripts/parser.py`
- `fowpro/scripts/generator.py`
- `fowpro/scripts/targeting.py`

**Fix**
- Improve parsing or post-process generation to add target filters.
- Add runtime validation fallback if targets are missing.

**Expected outcome**
- Targeted effects enforce card text requirements.

---

## 8) Special stone choices (GUI prompts)

**Problem**
- Some stones (e.g., Little Red) choose attributes with defaults instead of prompting.

**Code refs**
- `fowpro/scripts/stones/special.py`
- `fowpro/gui/choice_dialogs.py`

**Fix**
- Add prompt flow for attribute choice when stone enters.

**Expected outcome**
- Player choice is required and stored correctly.

---

## 9) Rules integration sanity pass

**Problem**
- Rules engine hooks are partially used; some effects bypass correct pipelines.

**Code refs**
- `fowpro/rules/integration.py`
- `fowpro/engine.py`

**Fix**
- Ensure all effect resolutions go through rules engine pipeline where appropriate.

**Expected outcome**
- Consistent effect handling.

---

## 10) Minimal regression tests for CR edge cases

**Problem**
- No automated checks for priority, triggers, replacements, fizzle.

**Fix**
- Add small scripted tests (or manual harness) for key CR flows.

**Expected outcome**
- Prevents regressions while iterating.
