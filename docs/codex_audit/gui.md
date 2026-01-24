# GUI (fowpro/gui/*)

## Files and roles
- `app.py`: Qt application bootstrap; initializes main menu and duel screens.
- `main_menu.py`: main navigation; launch duel/deck editor/settings.
- `duel_screen.py`: main duel UI; renders zones, cards, actions, and integrates with `GameEngine`.
- `deck_editor.py`: deck builder/editor with import/export and card list management.
- `choice_dialogs.py`: modal dialogs for targeting, modal choices, confirmations.
- `assets.py`, `styles.py`: asset loading and UI styling.
- `settings.py`: settings UI.

## Observed behavior
- UI directly interacts with `GameEngine` for game state and actions.
- Deck editor uses local data and can save/load deck files (`.fdk`).
- Duel screen uses in-memory card data and calls engine methods for play/attack/block.

## Gaps / not hooked yet (observed)
- Many effect-related prompts rely on rules/choice systems; if rules engine lacks a prompt, UI falls back to defaults.
- Some scripted abilities (e.g., stones with selection) rely on GUI prompts that are noted as TODO in scripts.
- The UI expects certain engine events; mismatches can cause missing updates for complex effects.
