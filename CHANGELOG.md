# Changelog

All notable changes to FoWPro will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.3] - 2026-02-02

### Added
- CR script generation for all set codes present in the DB
- UI preflight for missing CR scripts in the player deck

### Changed
- CR-only rules engine (removed legacy script system and fallbacks)
- Script registry now hard-fails on missing scripts
- AI deck selection filters to scripted cards only
- v2 folder moved out of main repo

### Fixed
- Continuous effects pipeline improvements and script generation updates

## [0.3.2] - 2026-02-01

### Added
- Attachment UI stacking with top-peek behavior for Additions
- J-ruler appears in field row (large) after Judgment

### Changed
- Judgment eligibility/cost parsing from ability text
- Auto-pass and priority checks respect quickcast timing and will abilities
- Target selection highlights and dialog behavior improvements
- Call Stone can be performed by J-ruler (rules-correct), blocked after Judgment that turn

### Fixed
- Addition:Resonator targeting and attachment flow
- Targeting filters for card types, barrier, and cost comparisons
- Replacement-effect wiring and modal/trigger handling
- Left-click behavior for J-ruler (context menu)

## [0.2.2] - 2026-01-24

### Added
- **Codex Audit Documentation**: Comprehensive codebase analysis in `docs/codex_audit/`
  - `fix_list_v1.md` tracking identified issues and fixes
  - `reality_check_v1.md` documenting actual v1 capabilities
  - Audit notes for engine, rules, scripts, GUI, models subsystems
- Legacy `ActivatedAbility` wrapper for stone scripts with proper target prompting

### Changed
- **Ability Resolution**: CR abilities and legacy stone abilities now resolve correctly
  - Targets chosen when abilities go on chase, revalidated at resolution
  - Triggers fizzle when required targets become illegal (CR 906)
  - CR ActivateAbility: costs paid on activation, effects execute on resolution
- **Combat/Priority**: Attack/block legality aligned with v1's "combat in Main Phase" model
- **Replacement Effects**: Multiple replacements now use modal choice when UI callback exists
- **Modal Spells**: Engine respects `get_choose_count()` for upgrade conditions
- **Will Production**: Multi-color will and Little Red stones prompt for attribute choice via ChoiceManager
- **Layer System**: STAT_CDA layer now applies `set_atk`/`set_def` effects

### Fixed
- Spell target revalidation at resolution (checks script requirements)
- Legacy activated abilities properly pass targets to operations

### Known Issues
- CR ActivateAbility `additional_costs` not yet implemented (activation blocked if present)
- Generated scripts lack detailed target filters and modal upgrade conditions
- Layer system lacks full dependency and CDA nuance beyond basic set_atk/set_def

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
