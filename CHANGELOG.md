# Changelog

All notable changes to FoWPro will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.1] - 2026-01-04

### Added
- **CostManager Integration (CR 402)**: Engine now uses CR-compliant cost system
  - Cost reductions/increases applied properly (CR 402.2)
  - Alternative costs (Incarnation, Remnant) handled by CostManager
  - Awakening costs integrated
  - Scripts can register cost modifiers via `get_cost_modifiers()`

- **Replacement Effects Integration (CR 910)**: Full replacement effect system enabled
  - Scripts can register replacement effects via `get_replacement_effects()`
  - Destruction, damage, and zone changes check for replacements
  - Proper handling of "If X would Y, Z instead" effects

### Changed
- `play_card()` now uses CostManager for cost calculation and payment
- `get_available_alternative_costs()` delegates to CostManager when available
- Added `get_will_pool()` and `spend_will()` methods to engine

### Technical
- `_register_card_continuous_effects()` now also registers cost modifiers and replacement effects
- Card leave-field cleanup now unregisters costs and replacement effects

## [0.2.0] - 2026-01-04

### Added
- **CR-Compliant Rules Engine**: Full migration to Comprehensive Rules (CR) compliant systems
  - APNAPTriggerManager for proper trigger ordering (CR 906)
  - LayerManager for continuous effect application (CR 909)
  - Support for intervening-if triggers (CR 906.9)

### Changed
- **Trigger System Migration**: Engine now uses APNAPTriggerManager exclusively
  - Triggers are registered with RulesEngine.triggers instead of legacy TriggerManager
  - APNAP ordering ensures active player's triggers resolve last (CR 906.5)
  - Removed duplicate trigger firing from rules_bridge.py lifecycle hooks

- **Continuous Effects Migration**: Engine now uses LayerManager exclusively
  - Effects are registered with RulesEngine.layers instead of legacy ContinuousEffectManager
  - 9-layer system for proper effect ordering (CR 909.1a-h)
  - Timestamp-based ordering within layers (CR 909.2)
  - Dependency handling for complex interactions (CR 909.3)

- **Stats Overlay**: Now shows stats for all resonators/J-rulers regardless of base stats
  - Fixes display for cards like Tinker Bell with 0/0 base that gain stats from abilities

### Fixed
- Gretel enter trigger now fires correctly (was firing twice before)
- Elvish Priest tap-for-will now rests the card properly
  - Fixed summoning sickness check to use `card.entered_turn == game.turn_number`
  - Removed broken `can_use_tap_abilities` property from Card model
- Tinker Bell ATK/DEF overlay now displays (was hidden when base stats were 0/0)

### Technical
- `engine.emit()` no longer calls legacy `_check_triggers()` - RulesEngine handles this
- `_register_card_triggers()` now registers directly with APNAPTriggerManager
- `_register_card_continuous_effects()` now registers with LayerManager
- `run_state_based_actions()` uses RulesEngine.apply_continuous_effects()
- rules_bridge.py lifecycle hooks (on_enter_field, etc.) only handle legacy effects

## [0.1.0] - 2025-12-28

### Added
- Initial release of FoWPro - Force of Will TCG Simulator
- Core game engine with turn structure, phases, and priority system
- Card database with Grimm Cluster sets (CMF, TAT, MPR, MOA)
- CR-compliant rules module (287KB) covering:
  - CR 901-907: Ability types (Activate, Automatic, Continuous, Will)
  - CR 908-910: Effect system, layers, replacement effects
  - CR 1100+: Keyword abilities
- Script generation from card text
- PyQt5 GUI with duel screen
- AI opponents (Random, Aggressive, Defensive)
