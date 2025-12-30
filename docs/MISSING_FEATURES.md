# FoWPro Missing Features

Features not yet implemented in the Force of Will TCG Simulator.

---

## High Priority

### AI System
- [ ] Basic AI opponent
- [ ] Rule-based decision making
- [ ] Combat evaluation
- [ ] Card value assessment
- [ ] Priority passing logic
- [ ] Targeting decisions
- [ ] Alternative cost evaluation
- [ ] Modal choice selection

### Network Play
- [ ] Server architecture
- [ ] Client-server protocol
- [ ] Game state synchronization
- [ ] Player authentication
- [ ] Lobby system
- [ ] Match history
- [ ] Reconnection handling

### Card Database Completeness
- [ ] Alice Cluster cards (~400 cards)
- [ ] Lapis Cluster cards (~400 cards)
- [ ] Reiya Cluster cards (~400 cards)
- [ ] New Valhalla Cluster cards (~400 cards)
- [ ] Promos and special sets
- [ ] Future sets as released

---

## Medium Priority

### Gameplay Polish

#### Combat
- [ ] Multiple blocker assignment
- [ ] Blocker damage ordering
- [ ] Combat damage redirection effects

#### Special Mechanics
- [ ] Shift (alternate cost using J-Ruler)
- [ ] Stranger (special card type)
- [ ] Order (special ability timing)
- [ ] Inheritance (creature enchantment transfer)
- [ ] Sealed (face-down resonators)
- [ ] Secret Area mechanics

#### Will System
- [ ] Multi-attribute will checking for complex costs
- [ ] Will fixing effects
- [ ] Will doubling effects

### UI Improvements

#### Duel Screen
- [ ] Animation system (card movements, damage, effects)
- [ ] Sound effects
- [ ] Background music
- [ ] Combat resolution visualization
- [ ] Chain/Chase visualization improvements
- [ ] Graveyard browser
- [ ] Removed zone browser
- [ ] Opponent hand count display

#### Deck Editor
- [ ] Deck statistics panel
- [ ] Mana curve visualization
- [ ] Card type distribution
- [ ] Attribute distribution
- [ ] Import from text files
- [ ] Export to text files
- [ ] Deck validation (format legality)
- [ ] Save/load multiple decks

#### Settings
- [ ] Key binding customization
- [ ] Card display size options
- [ ] Animation speed settings
- [ ] Auto-pass options
- [ ] Confirmation dialog settings

### Quality of Life
- [ ] Undo system (revert illegal actions)
- [ ] Game state serialization (save/load games)
- [ ] Game replay system
- [ ] Tutorial mode
- [ ] Practice mode with hints
- [ ] Card rulings database

---

## Low Priority

### Advanced Features

#### Tournament Support
- [ ] Swiss pairing
- [ ] Single elimination brackets
- [ ] Match reporting
- [ ] Player standings
- [ ] Tournament timer

#### Collection Management
- [ ] Owned card tracking
- [ ] Trade list management
- [ ] Want list
- [ ] Collection statistics

#### Social Features
- [ ] Friend list
- [ ] Chat system
- [ ] Spectator mode
- [ ] Game sharing/streaming

### Platform Expansion
- [ ] Mobile port (Android/iOS)
- [ ] Web version
- [ ] Steam integration

### Localization
- [ ] Japanese card names
- [ ] Other language support
- [ ] RTL language support

---

## Technical Debt

### Code Quality
- [ ] Unit test coverage (currently ~0%)
- [ ] Integration tests
- [ ] Performance benchmarks
- [ ] Memory profiling
- [ ] Code documentation (docstrings)
- [ ] Type hints completion

### Architecture
- [ ] Event bus abstraction
- [ ] Plugin system for custom cards
- [ ] Mod support
- [ ] Theme/skin system expansion

### Data
- [ ] Card errata tracking
- [ ] Banned/restricted list per format
- [ ] Format definitions (New Frontiers, Wanderer, etc.)

---

## Known Issues

### Bugs
- [ ] 1 generated TODO (CMF-004 condition check)
- [ ] Some continuous effect EOT cleanup may not trigger

### Missing Interactions
- [ ] "Cannot be prevented" damage
- [ ] "Cannot be countered" spells
- [ ] "Cannot use abilities" effects
- [ ] Multi-step triggered abilities
- [ ] Delayed triggers ("at beginning of next turn")

### Edge Cases
- [ ] Copying cards with X costs
- [ ] Permanent control changes
- [ ] Recursive triggers (infinite loop detection)
- [ ] Layer interaction edge cases

---

## Statistics

| Category | Implemented | Missing | % Complete |
|----------|-------------|---------|------------|
| Grimm Cluster Cards | 381 | 0 | 100% |
| Other Cluster Cards | 0 | ~1,600 | 0% |
| Keywords | 19 | ~5 | 79% |
| Effect Actions | 35 | ~10 | 78% |
| GUI Components | 29 | ~15 | 66% |
| AI | 0 | 1 | 0% |
| Network | 0 | 1 | 0% |

**Overall Completion**: ~70% (Grimm Cluster only), ~15% (all sets)

---

*Last updated: December 30, 2025*
