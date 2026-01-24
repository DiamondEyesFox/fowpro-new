# Magic Stone Scripts (fowpro/scripts/stones/*)

## Basic stones
- `basic.py` defines single-color stones for Light/Fire/Water/Wind/Darkness.
- Each stone overrides `get_will_colors()` and returns its attribute.

## Dual stones
- `dual.py` defines dual-attribute stones (wind/darkness, wind/fire, etc.).
- Each stone overrides `get_will_colors()` to return two attributes.

## Special stones
- `special.py` includes stones with extra logic:
  - `MagicStoneOfMoonLight` produces any color another controlled stone can produce (falls back to void).
  - `MagicStoneOfMoonShade` can produce void, or pay 200 life for light/fire/water/wind.
  - `LittleRedThePureStone` chooses an attribute on entry and then produces only that.
  - Several "true magic stones" grant activated abilities (e.g., grant Flying).

## Observed gaps
- Some special stones rely on GUI prompts or chosen-attribute storage that default to a placeholder (e.g., Little Red default attribute).
- Activated abilities for stones are defined but depend on generic `ActivatedAbility` handling and target filtering support in the engine/UI.
