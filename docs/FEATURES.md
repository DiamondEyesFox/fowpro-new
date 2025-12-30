# FoWPro Feature List

A comprehensive list of all implemented features in the Force of Will TCG Simulator.

## Core Engine (43,514 lines across 57 Python files)

### Game Engine (`fowpro/engine.py`)
- **Turn Structure**: Full phase system (Draw, Recovery, Main, End)
- **Combat System**: Attack declaration, blocker declaration, damage steps
- **Chase System**: Stack-like spell/ability resolution with LIFO ordering
- **Priority System**: Proper priority passing between players
- **State-Based Actions**: Automatic checks for lethal damage, 0 life, etc.
- **Zone Management**: Hand, Field, Graveyard, Deck, Magic Stone Deck, Removed, Standby, Chase

### Card Models (`fowpro/models.py`)
- **Card Types**: Ruler, J-Ruler, Resonator, Spell (Chant/Chant-Instant/Chant-Standby), Addition, Magic Stone, Regalia
- **Attributes**: Light, Fire, Water, Wind, Darkness, Void, Moon
- **Will System**: WillCost, WillPool with proper payment logic
- **Abilities**: CardAbility with trigger conditions and effects

### Keywords (19 implemented)
| Keyword | CR Reference | Description |
|---------|-------------|-------------|
| Swiftness | CR 1108 | Can attack/use abilities turn it enters |
| Flying | CR 1107 | Can only be blocked by Flying |
| First Strike | CR 1105 | Deals damage first in combat |
| Pierce | CR 1103 | Excess damage goes to player |
| Drain | CR 1136 | Gain life equal to damage dealt |
| Imperishable | CR 1109 | J-Ruler doesn't go astral when destroyed |
| Target Attack | - | Can attack specific targets |
| Precision | CR 1104 | Can attack recovered J/resonators |
| Barrier | CR 1120 | Can't be targeted by opponent |
| Explode | CR 1106 | Mutual destruction on battle damage |
| Stealth | - | Cannot be blocked |
| Vigilance | - | Does not rest to attack |
| Indestructible | - | Cannot be destroyed |
| Unblockable | - | Cannot be blocked |
| Cannot Attack | - | Cannot declare attacks |
| Cannot Block | - | Cannot be declared as blocker |
| Hexproof | - | Cannot be targeted by opponent |
| Remnant | CR 1115 | Can be played from graveyard |
| Quickcast | CR 1112 | Can play at instant timing |

---

## Rules Engine (`fowpro/rules/`)

### Continuous Effect Layer System (CR 909)
Proper layering for stat modifications:
1. Layer 1: Copy effects
2. Layer 2: Control-changing effects
3. Layer 3: Text-changing effects
4. Layer 4: Type-changing effects
5. Layer 5: Attribute-changing effects
6. Layer 6a: Set ATK/DEF to value
7. Layer 6b: Modify ATK/DEF (+/-)
8. Layer 7: Keyword-granting effects
9. Layer 8: Ability-granting effects

### Replacement Effects (CR 910)
- Damage prevention/modification
- Destruction replacement
- Draw replacement
- Life gain/loss replacement
- Zone change replacement
- Counter manipulation
- Rest/Recover replacement

### Alternative Costs
- **Awakening** (CR 1102): Pay extra will for enhanced effects
- **Incarnation** (CR 1105): Banish resonators instead of paying will

### Targeting System
- Controller filtering (you/opponent/any)
- Zone filtering (field/graveyard/hand/etc.)
- Card type filtering
- Attribute filtering
- Race filtering
- Keyword filtering
- Stat filtering (ATK/DEF ranges)
- Cost filtering (total cost X or less)
- State filtering (rested/recovered)
- Name filtering
- Custom filter functions

### Choice System
- Target selection
- Modal choices (choose one/two)
- X value selection
- Yes/No prompts
- Card selection from lists
- Attribute choice

### Trigger System
- Enter field triggers
- Leave field triggers
- Damage triggers
- Combat triggers
- Phase triggers
- Counter triggers
- Life change triggers

---

## Card Script System

### CR Parser (`fowpro/scripts/cr_parser.py`)
**100% coverage (381/381 Grimm Cluster cards)**

Parses ability text into structured data:
- Keyword detection
- Trigger condition parsing
- Cost parsing (will, rest, sacrifice, banish, discard, pay life)
- Effect parsing (50+ effect patterns)
- Modal ability parsing
- Awakening/Incarnation cost parsing

### Effect Patterns Recognized
- Deal damage (flat, X-based, ATK-based, scaled)
- Destroy target
- Return to hand
- Put into hand/field/graveyard
- Draw cards
- Gain/lose life
- Rest/recover
- Add/remove counters
- Grant/remove keywords
- Modify ATK/DEF
- Cancel spells
- Search deck
- Prevent damage
- Gain control
- Banish
- Remove from game
- Copy cards
- Summon tokens
- Grant abilities
- Change attributes/types/races

### CR Generator (`fowpro/scripts/cr_generator.py`)
Auto-generates Python card scripts from parsed ability data.

### Generated Scripts
- `cmf_cr.py`: Crimson Moon's Fairy Tale (100 cards)
- `tat_cr.py`: The Age of the Twilight (100 cards)
- `mpr_cr.py`: The Moon Priestess Returns (101 cards)
- `moa_cr.py`: The Millennia of Ages (80 cards)

---

## GUI System (`fowpro/gui/`)

### Main Application
- Screen navigation (Menu, Duel, Deck Editor, Settings)
- Skinning system with customizable themes
- Asset management with image downloading

### Duel Screen
- Card widgets with hover effects
- Zone widgets for all game zones
- Will pool visualization
- Player area with life/will display
- Field drop zones
- Chase visualization

### Deck Editor
- Card search with filters
- Deck zone widgets (main deck, stone deck, ruler)
- Card count management
- Deck import/export
- Ruler/J-Ruler selection

### Choice Dialogs
- TargetSelectionDialog
- ModalChoiceDialog
- YesNoDialog
- XValueDialog
- CardListDialog
- AttributeChoiceDialog

### Settings
- Background selector
- Volume controls
- Resolution options

---

## Magic Stone System (`fowpro/scripts/stones/`)

### Basic Stones
- Light Magic Stone
- Fire Magic Stone
- Water Magic Stone
- Wind Magic Stone
- Darkness Magic Stone

### Dual Stones
- All 10 two-color combinations

### Special Stones
- Magic Stone of Moon Light (produces any color another stone can)
- Magic Stone of Moon Shade (pay 200 life for colored will)
- Little Red, the Pure Stone (choose attribute on entry)
- True Magic Stones with activated abilities:
  - Almerius: Grant Flying
  - Feethsing: Grant Barrier
  - Grubalesta: -200 DEF
  - Milest: +200 damage
  - Moojdart: Change race

---

## Chant-Standby System

- `set_in_standby()`: Pay {2} to set face-down
- `can_play_from_standby()`: Check trigger conditions, stone count, timing
- `play_from_standby()`: Execute when conditions met
- `get_playable_standby_cards()`: List available cards

---

## Combat Keyword Enforcement

- **Flying**: Only blocked by Flying
- **First Strike**: Deals damage first
- **Pierce**: Excess damage to player
- **Drain**: Heal on damage
- **Explode**: Mutual destruction
- **Target Attack**: Required to attack resonators
- **Precision**: Required to attack recovered
- **Stealth/Unblockable**: Cannot be blocked
- **Cannot Attack/Cannot Block**: Restrictions enforced
- **Swiftness**: No summoning sickness
- **Vigilance**: Doesn't rest to attack
- **Indestructible**: Prevents destruction

---

## Data Layer

### Database (`fowpro/database.py`)
- SQLite card database
- Card search by name, type, attribute, race
- Set filtering
- Image path management

### Card Scraper (`fowpro/scraper.py`)
- Scrapes card data from fowdb.altervista.org
- Downloads card images
- Stores in SQLite database

---

## Effect Handlers (30+ implemented)

| Action | Description |
|--------|-------------|
| DEAL_DAMAGE | Deal damage to target |
| DESTROY | Destroy target (to graveyard) |
| BANISH | Remove from game |
| RETURN_TO_HAND | Return to owner's hand |
| REMOVE_FROM_GAME | Remove from game permanently |
| DRAW | Draw cards |
| DISCARD | Discard from hand |
| GAIN_LIFE | Increase life total |
| LOSE_LIFE | Decrease life total |
| PRODUCE_WILL | Add will to pool |
| REST | Rest (tap) target |
| RECOVER | Recover (untap) target |
| ADD_COUNTER | Add counter to card |
| REMOVE_COUNTER | Remove counter from card |
| MODIFY_ATK | Modify ATK value |
| MODIFY_DEF | Modify DEF value |
| SET_ATK | Set ATK to value |
| SET_DEF | Set DEF to value |
| GRANT_KEYWORD | Grant keyword ability |
| REMOVE_KEYWORD | Remove keyword ability |
| CANCEL | Cancel spell/ability |
| PUT_INTO_FIELD | Put card into field |
| SEARCH | Search deck |
| PREVENT_DAMAGE | Prevent damage |
| GAIN_CONTROL | Take control of target |
| PUT_ON_TOP_OF_DECK | Put on top of deck |
| PUT_ON_BOTTOM_OF_DECK | Put on bottom of deck |
| PUT_INTO_GRAVEYARD | Put into graveyard |
| SHUFFLE_INTO_DECK | Shuffle into deck |
| REVEAL | Reveal card(s) |
| LOOK | Look at card(s) |
| GRANT_ABILITY | Grant ability text |
| REMOVE_ABILITY | Remove abilities |
| COPY | Copy card |
| SUMMON | Create token |
| BECOME_COPY | Become copy of target |
| GRANT_ATTRIBUTE | Grant attribute |
| REMOVE_ATTRIBUTE | Remove attribute |
| SET_ATTRIBUTE | Set attribute |
| GRANT_RACE | Grant race |
| SET_TYPE | Set card type |
| REMOVE_DAMAGE | Heal damage |

---

## EffectBuilder Methods

Static factory methods for creating Effect objects:
- `deal_damage(amount)`
- `destroy()`
- `draw(count)`
- `gain_life(amount)`
- `lose_life(amount)`
- `add_counter(type, count)`
- `remove_counter(type, count)`
- `modify_atk(amount)`
- `modify_def(amount)`
- `grant_keyword(keyword)`
- `remove_keyword(keyword)`
- `return_to_hand()`
- `put_on_top_of_deck()`
- `put_on_bottom_of_deck()`
- `put_into_graveyard()`
- `shuffle_into_deck()`
- `reveal()`
- `look_at(count)`
- `set_atk(value)`
- `set_def(value)`
- `set_life(value)`
- `grant_ability(text)`
- `remove_all_abilities()`
- `copy_card()`
- `summon_token(name, atk, def)`
- `remove_damage(amount, all)`
- `grant_attribute(attr)`
- `remove_attribute(attr)`
- `set_attribute(attr)`
- `grant_race(race)`
- `set_type(type)`
- `become_copy()`

---

## Test Coverage

- Import verification for all modules
- Generated script validation
- Engine initialization tests
- 381/381 card scripts validated

---

## File Statistics

| Category | Files | Lines |
|----------|-------|-------|
| Engine | 1 | ~2,000 |
| Models | 1 | ~700 |
| Rules | 12 | ~4,500 |
| Scripts | 15 | ~8,000 |
| Generated | 4 | ~6,000 |
| GUI | 8 | ~4,500 |
| Other | 16 | ~17,800 |
| **Total** | **57** | **~43,500** |

---

*Last updated: December 30, 2025*
