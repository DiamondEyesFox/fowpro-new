# v2 Code Snapshot (fowpro/v2/*)

## Scope note
- Current audit focus is v1 behavior. v2 is present in the repo but is not being validated for correctness in this pass.

## Observed structure
- `fowpro/v2/core/*` implements a message-based engine with immutable state snapshots and an effect registry.
- `fowpro/v2/core/events.py` defines a YGOPro-style event system and trigger handling.
- `fowpro/v2/core/effects.py` defines effect objects, flags, event codes, and a global registry.
- `fowpro/v2/core/state.py` defines immutable snapshots of cards/players/chase/combat.
- `fowpro/v2/core/processor.py` is the main message-driven duel processor (long file).
- `fowpro/v2/core/lua_bridge.py` integrates Lua scripts via `lupa` (not reviewed in depth).
- `fowpro/v2/scripts/*` contains per-card Lua scripts and stone scripts.

## Note
- If/when v2 becomes the focus, these files need a separate audit pass, especially the Lua script set.
