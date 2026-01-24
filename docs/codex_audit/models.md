# Models (fowpro/models.py, fowpro/shared/will.py)

## Core enums and data objects
- `Attribute`, `CardType`, `Zone`, `Phase`, `CombatStep`, `Keyword` define game constants.
- `WillCost` and `WillPool` implement cost payment, reduction, and attribute checks.
- `CardData` holds database-backed card metadata: name, type, attributes, races, costs, abilities text, ATK/DEF, judgment cost, etc.
- `Card` represents a single card instance (zone, controller, rested, damage, attachments, etc.).
- `PlayerState` tracks life, zones (hand/field/decks/graveyard), will pool, ruler, J-ruler, and turn flags.
- `BattleContext` and `ChaseItem` are the mutable combat/chase structures used by `GameEngine`.

## Observed behaviors
- `Card` exposes helpers like `rest()`, `recover()`, `destroy()`, and keyword checks.
- Damage and combat stats are handled on the card instance (`damage`, `effective_atk/def`).
- Attachments are tracked on `Card.attachments` and `Card.attached_to`.
- `WillPool` can compute and pay costs, supports flexible attribute payment (`pay()`), and reports `total`.

## Notable gaps/risks
- `CardData` is permissive (many optional fields), which allows partial card definitions but increases runtime null checks.
- `WillCost` reduction logic is simple; any cost-reduction rule complexity must be handled elsewhere (rules engine or scripts).
