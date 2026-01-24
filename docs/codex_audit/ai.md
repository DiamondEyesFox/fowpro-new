# AI (fowpro/ai/*)

## Files
- `fowpro/ai/base.py`: base AI interface with hooks for turn/priority actions.
- `fowpro/ai/random_ai.py`: simple random action AI.
- `fowpro/ai/__init__.py`: exports AI classes.

## Observed behavior
- Random AI picks from available actions with minimal evaluation.
- Interacts with `GameEngine` via high-level methods (draw, play, call stone, attack, pass).

## Gaps
- No strategic evaluation or rules-heavy decision logic.
- AI assumes engine exposes lists of legal actions; if those lists are incomplete, AI will miss actions.
