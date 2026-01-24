# Codex Changelog (v1 Focus)

## 2026-01-24

### Added
- `docs/codex_audit/fix_list_v1.md` with detailed fixes and progress log.
- `docs/codex_audit/reality_check_v1.md` (code-based reality check of v1).
- Audit notes across subsystems in `docs/codex_audit/`.
- Legacy `ActivatedAbility` wrapper for stone scripts in `fowpro/scripts/__init__.py`.

### Changed
- Priority/combat alignment: attack/block legality now matches v1 Main Phase combat model (`fowpro/rules/priority.py`).
- Trigger flow: targets chosen on chase entry, revalidated on resolution, fizzle on invalid required targets (`fowpro/rules/triggers.py`).
- CR ActivateAbility: activation costs paid on activation, chase resolution executes effects, target revalidation at resolution (`fowpro/engine.py`).
- Replacement effects: multiple replacement choice now uses modal choice when UI callback exists (`fowpro/rules/replacement.py`).
- Modal spells: engine respects `get_choose_count()` for upgrade conditions (`fowpro/engine.py`).
- Legacy activated abilities: target prompting and revalidation wired; resolution passes targets (`fowpro/engine.py`).
- Spell revalidation: target requirements from scripts are checked at resolution (`fowpro/engine.py`).
- Multi-color will: prompts for attribute choice via ChoiceManager when UI available (`fowpro/engine.py`).
- Little Red stone: attribute choice prompt via ChoiceManager when UI available (`fowpro/scripts/stones/special.py`).
- Layer system: STAT_CDA now applies `set_atk/set_def` (`fowpro/rules/layers.py`).

### Notes / Remaining Gaps
- CR ActivateAbility `additional_costs` not implemented (activation blocked if present).
- Generated scripts still lack detailed target filters and many modal upgrade conditions.
- Layer system still lacks full dependency and CDA nuance beyond basic set_atk/set_def.
