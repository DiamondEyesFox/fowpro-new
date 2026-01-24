# Script System (fowpro/scripts/*)

## Registry and base script
- `fowpro/scripts/__init__.py`: `ScriptRegistry` registers card scripts by code; provides `get()` and `create()`.
- `fowpro/scripts/default.py`: fallback script class for cards without a dedicated script.

## Rules bridge (v1)
- `fowpro/scripts/rules_bridge.py`: adapter layer between v1 scripts and the rules engine.
  - Defines `RulesCardScript`, `AbilityFactory`, `EffectBuilder`, and ability classes.
  - Provides helpers for common effect patterns (destroy, draw, search, etc.).
  - Bridges to `RulesEngine` for target selection and resolution.

## Parsing/generation pipeline
- `cr_parser.py` + `cr_generator.py`: parse comprehensive rules text and generate rule data / script scaffolding.
- `generator.py`: generates Python script classes from parsed card text.
- `parser.py`: parses individual card text to structured ability/action formats.

## Execution and utilities
- `effects.py`, `continuous.py`, `triggers.py`, `targeting.py`, `zones.py`, `combat.py`, `costs.py`, `keywords.py`, `resolution.py`, `counter.py`, `tokens.py`:
  - Provide helpers used by scripts and the rules bridge.
  - Many functions delegate into `GameEngine` or `RulesEngine` methods.

## Observed gaps / risks
- Several helpers rely on game/rules engine behavior that is incomplete (see rules audit).
- Generated scripts include TODOs for condition checks and complex text parsing.
- Some effect builder actions are placeholders or simplified (e.g., modal upgrades, complex targeting).
