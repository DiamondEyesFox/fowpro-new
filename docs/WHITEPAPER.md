# FoWPro: A Comprehensive Force of Will TCG Simulator

**Technical White Paper**

*Version 1.0 - December 30, 2025*

---

## Abstract

FoWPro is an open-source digital implementation of the Force of Will Trading Card Game, featuring a rules-compliant game engine, automated card script generation, and a modern graphical interface. This document describes the architecture, design decisions, and technical implementation of the simulator, which currently supports 100% of the Grimm Cluster card set (381 cards) with full rules compliance per the Force of Will Comprehensive Rules (CR).

---

## 1. Introduction

### 1.1 Background

Force of Will (FoW) is a Japanese trading card game first released in 2012, featuring unique mechanics such as the Ruler/J-Ruler system, Magic Stones as resource cards, and the Chase (stack) system for spell resolution. Unlike other digital card game implementations, no official comprehensive simulator exists for FoW, creating an opportunity for community-driven development.

### 1.2 Project Goals

1. **Rules Accuracy**: Implement game mechanics exactly as specified in the Comprehensive Rules
2. **Automation**: Auto-generate card scripts from ability text rather than hand-coding each card
3. **Extensibility**: Design architecture that supports easy addition of new cards and sets
4. **Accessibility**: Provide both single-player and multiplayer gameplay experiences

### 1.3 Scope

This implementation focuses on the Grimm Cluster era (2013-2014), comprising four sets:
- Crimson Moon's Fairy Tale (CMF)
- The Age of the Twilight (TAT)
- The Moon Priestess Returns (MPR)
- The Millennia of Ages (MOA)

---

## 2. Architecture Overview

### 2.1 System Components

```
┌─────────────────────────────────────────────────────────────┐
│                        GUI Layer                             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐   │
│  │ Duel     │ │ Deck     │ │ Main     │ │ Settings     │   │
│  │ Screen   │ │ Editor   │ │ Menu     │ │ Screen       │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────┘   │
├─────────────────────────────────────────────────────────────┤
│                      Rules Engine                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐   │
│  │ Priority │ │ Layers   │ │ Replace- │ │ Targeting    │   │
│  │ Manager  │ │ System   │ │ ments    │ │ System       │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────┘   │
├─────────────────────────────────────────────────────────────┤
│                       Game Engine                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐   │
│  │ Turn     │ │ Combat   │ │ Chase    │ │ State-Based  │   │
│  │ System   │ │ System   │ │ System   │ │ Actions      │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────┘   │
├─────────────────────────────────────────────────────────────┤
│                     Script System                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐   │
│  │ CR       │ │ CR       │ │ Generated│ │ Effect       │   │
│  │ Parser   │ │ Generator│ │ Scripts  │ │ Handlers     │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────┘   │
├─────────────────────────────────────────────────────────────┤
│                       Data Layer                             │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────────────────┐│
│  │ Card     │ │ Web      │ │ SQLite Database              ││
│  │ Models   │ │ Scraper  │ │                              ││
│  └──────────┘ └──────────┘ └──────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Technology Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.11+ |
| GUI Framework | PyQt6 |
| Database | SQLite3 |
| Version Control | Git/GitHub |
| Testing | pytest |

---

## 3. Game Engine Design

### 3.1 State Management

The game state is encapsulated in the `GameEngine` class, which maintains:

```python
class GameEngine:
    players: List[PlayerState]      # Player states
    turn_number: int                # Current turn
    current_phase: Phase            # Current phase
    turn_player: int                # Active player index
    chase: List[ChaseItem]          # The Chase (stack)
    battle: BattleContext           # Combat state
    game_over: bool                 # Game end flag
    winner: int                     # Winner index
```

### 3.2 Zone System

Eight game zones are implemented per CR Section 4:

| Zone | Purpose | Visibility |
|------|---------|------------|
| Hand | Cards held by player | Owner only |
| Field | In-play permanents | Public |
| Graveyard | Destroyed/discarded cards | Public |
| Deck | Main deck | Hidden |
| Magic Stone Deck | Stone deck | Hidden |
| Removed | Banished cards | Public |
| Standby | Face-down Chant-Standby | Hidden |
| Chase | Spells/abilities resolving | Public |

### 3.3 Turn Structure

```
Turn Start
    ├── Draw Phase
    │   └── Draw 1 card (skip first turn for first player)
    ├── Recovery Phase
    │   └── Recover all cards
    ├── Main Phase
    │   ├── Play cards
    │   ├── Activate abilities
    │   ├── Call magic stones
    │   ├── Declare attacks
    │   └── Perform judgment
    └── End Phase
        └── Cleanup, discard to hand size
Turn End
```

### 3.4 Combat System

Combat follows CR Section 8:

```
Declare Attack
    ├── Check Swiftness/summoning sickness
    ├── Check CANNOT_ATTACK
    ├── Check Target Attack for resonator targeting
    ├── Check Precision for recovered targets
    └── Rest attacker (unless Vigilance)

Declare Blocker
    ├── Check CANNOT_BLOCK
    ├── Check UNBLOCKABLE/STEALTH
    └── Check FLYING requirements

Damage Steps
    ├── First Strike damage (if applicable)
    ├── Normal damage
    ├── Pierce calculation
    ├── Drain life gain
    └── Explode mutual destruction
```

---

## 4. Rules Compliance

### 4.1 Continuous Effect Layers (CR 909)

Effects are applied in strict layer order:

```python
class EffectLayer:
    COPY = 1          # Copy effects
    CONTROL = 2       # Control changes
    TEXT = 3          # Text changes
    TYPE = 4          # Type changes
    ATTRIBUTE = 5     # Attribute changes
    STATS_SET = 6     # Set ATK/DEF
    STATS_MODIFY = 7  # Modify ATK/DEF
    KEYWORDS = 8      # Keywords
    ABILITIES = 9     # Abilities
```

Within each layer, effects are applied by timestamp (CR 909.3b).

### 4.2 Replacement Effects (CR 910)

Replacement effects intercept events before they occur:

```python
class ReplacementType:
    DAMAGE = "damage"
    DESTROY = "destroy"
    DRAW = "draw"
    DISCARD = "discard"
    ENTER_FIELD = "enter_field"
    LEAVE_FIELD = "leave_field"
    LOSE_LIFE = "lose_life"
    GAIN_LIFE = "gain_life"
```

When multiple replacements apply, the affected player chooses (CR 910.3).

### 4.3 Targeting System (CR 903)

The targeting system validates:
- Zone restrictions
- Controller restrictions
- Card type requirements
- Attribute requirements
- Race requirements
- Keyword requirements
- Stat requirements (ATK/DEF/cost)
- State requirements (rested/recovered)
- Barrier/Hexproof protection (CR 1120)

---

## 5. Automated Script Generation

### 5.1 CR Parser

The CR Parser analyzes card ability text and extracts structured data:

**Input**: "When this card enters the field, draw 2 cards."

**Output**:
```python
ParsedAbility(
    ability_type=AbilityType.ENTER,
    trigger_condition=TriggerCondition.ENTER_FIELD,
    effects=[
        ParsedEffect(
            action=EffectAction.DRAW,
            params={'count': 2}
        )
    ]
)
```

### 5.2 Pattern Recognition

50+ effect patterns are recognized:

| Pattern | Example |
|---------|---------|
| `deal X damage to target` | "Deal 500 damage to target resonator" |
| `destroy target` | "Destroy target J/resonator" |
| `draw X cards` | "Draw 2 cards" |
| `gain X life` | "Gain 400 life" |
| `gains [+X/+Y]` | "Target resonator gains [+200/+200]" |
| `return to hand` | "Return target resonator to its owner's hand" |
| `search deck` | "Search your deck for a card and put it into your hand" |
| `gains [Keyword]` | "Target resonator gains [Flying]" |

### 5.3 CR Generator

The generator produces executable Python card scripts:

```python
# Auto-generated from: "When this card enters the field, draw 2 cards."
class CardNameScript(RulesCardScript):
    def __init__(self, card_code: str):
        super().__init__(card_code)

        self.register_trigger(
            TriggerCondition.ENTER_FIELD,
            self._on_enter_field
        )

    def _on_enter_field(self, game, card):
        player = card.controller
        game.draw_cards(player, 2)
```

### 5.4 Coverage Statistics

| Set | Cards | Parsed | Coverage |
|-----|-------|--------|----------|
| CMF | 100 | 100 | 100% |
| TAT | 100 | 100 | 100% |
| MPR | 101 | 101 | 100% |
| MOA | 80 | 80 | 100% |
| **Total** | **381** | **381** | **100%** |

---

## 6. GUI Design

### 6.1 Architecture

The GUI uses a screen-based architecture:

```python
class FoWProApp(QMainWindow):
    screens: Dict[Screen, QWidget]
    current_screen: Screen

    def navigate_to(self, screen: Screen):
        # Transitions between screens
```

### 6.2 Duel Screen Components

| Component | Purpose |
|-----------|---------|
| DuelCardWidget | Renders individual cards with hover effects |
| ZoneWidget | Contains cards for a specific zone |
| WillPoolWidget | Displays available will |
| FieldDropZone | Accepts card drops |
| PlayerAreaWidget | Groups all zones for a player |

### 6.3 Choice Dialogs

Six dialog types for player decisions:

1. **TargetSelectionDialog**: Select 1+ cards from valid targets
2. **ModalChoiceDialog**: Choose from modal options
3. **YesNoDialog**: Binary choice
4. **XValueDialog**: Select numeric X value
5. **CardListDialog**: Choose from card list
6. **AttributeChoiceDialog**: Select attribute

---

## 7. Performance Considerations

### 7.1 Lazy Loading

- Card images loaded on-demand
- Scripts loaded when cards enter play
- Database connections pooled

### 7.2 State Caching

- Effective ATK/DEF cached until continuous effects change
- Valid target lists cached per priority pass
- Keyword state cached on card objects

### 7.3 Memory Management

- Card instances pooled per zone
- Image cache with LRU eviction
- Event handlers weakly referenced

---

## 8. Future Work

### 8.1 AI Development

Planned AI approaches:
1. **Rule-based**: Hand-crafted heuristics
2. **Search-based**: Minimax with alpha-beta pruning
3. **Learning-based**: MCTS or neural networks

### 8.2 Network Play

Architecture considerations:
- Client-server model
- Game state synchronization
- Deterministic replay support
- Anti-cheat measures

### 8.3 Content Expansion

Remaining card sets (~1,600 cards across 4 clusters):
- Alice Cluster
- Lapis Cluster
- Reiya Cluster
- New Valhalla Cluster

---

## 9. Conclusion

FoWPro demonstrates that automated script generation can achieve 100% card coverage with CR-compliant rules implementation. The modular architecture supports extensibility for new card sets, UI improvements, and gameplay features. The project is open source and welcomes community contributions.

---

## Appendix A: File Statistics

| Category | Files | Lines |
|----------|-------|-------|
| Game Engine | 1 | ~2,000 |
| Models | 1 | ~700 |
| Rules System | 12 | ~4,500 |
| Script System | 15 | ~8,000 |
| Generated Scripts | 4 | ~6,000 |
| GUI | 8 | ~4,500 |
| Utilities | 16 | ~17,800 |
| **Total** | **57** | **~43,500** |

## Appendix B: Keywords Implemented

| Keyword | CR Reference |
|---------|-------------|
| Swiftness | 1108 |
| Flying | 1107 |
| First Strike | 1105 |
| Pierce | 1103 |
| Drain | 1136 |
| Imperishable | 1109 |
| Target Attack | - |
| Precision | 1104 |
| Barrier | 1120 |
| Explode | 1106 |
| Stealth | - |
| Vigilance | - |
| Indestructible | - |
| Unblockable | - |
| Cannot Attack | - |
| Cannot Block | - |
| Hexproof | - |
| Remnant | 1115 |
| Quickcast | 1112 |

## Appendix C: Effect Actions Implemented

35+ effect actions including: DEAL_DAMAGE, DESTROY, BANISH, RETURN_TO_HAND, DRAW, DISCARD, GAIN_LIFE, LOSE_LIFE, PRODUCE_WILL, REST, RECOVER, ADD_COUNTER, REMOVE_COUNTER, MODIFY_ATK, MODIFY_DEF, SET_ATK, SET_DEF, GRANT_KEYWORD, REMOVE_KEYWORD, CANCEL, PUT_INTO_FIELD, SEARCH, PREVENT_DAMAGE, GAIN_CONTROL, PUT_ON_TOP_OF_DECK, REVEAL, LOOK, GRANT_ABILITY, COPY, SUMMON, BECOME_COPY, GRANT_ATTRIBUTE, GRANT_RACE, SET_TYPE, REMOVE_DAMAGE.

---

## References

1. Force of Will Comprehensive Rules (CR) - Version dated to Grimm Cluster
2. PyQt6 Documentation - https://doc.qt.io/qtforpython-6/
3. SQLite Documentation - https://sqlite.org/docs.html

---

*Copyright 2025. Released under MIT License.*
