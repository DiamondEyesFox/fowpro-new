# FoWPro Development Roadmap

A phased development plan for the Force of Will TCG Simulator.

---

## Phase 1: Foundation (COMPLETED)

### 1.1 Core Engine
- [x] Game state management
- [x] Turn structure (phases)
- [x] Zone system (all 8 zones)
- [x] Will system
- [x] Card models

### 1.2 Combat System
- [x] Attack declaration
- [x] Blocker declaration
- [x] First strike damage step
- [x] Normal damage step
- [x] Combat keyword enforcement

### 1.3 Rules Compliance
- [x] CR 909 - Continuous effect layers
- [x] CR 910 - Replacement effects
- [x] CR 1102 - Awakening
- [x] CR 1105 - Incarnation
- [x] CR 711 - Chant-Standby
- [x] All 19 keywords

### 1.4 Card Scripting
- [x] CR Parser (100% coverage)
- [x] CR Generator
- [x] 381 Grimm Cluster scripts

### 1.5 GUI Foundation
- [x] Main menu
- [x] Duel screen
- [x] Deck editor
- [x] Settings
- [x] Choice dialogs

---

## Phase 2: Polish & Playability

### 2.1 AI Development
**Goal**: Create a competent AI opponent for single-player games.

#### 2.1.1 Basic AI
- [ ] Random legal move selection
- [ ] Combat damage calculation
- [ ] Basic threat assessment

#### 2.1.2 Rule-Based AI
- [ ] Card value heuristics
- [ ] Mana efficiency evaluation
- [ ] Combat attack/block decisions
- [ ] Removal priority targeting

#### 2.1.3 Advanced AI
- [ ] Search algorithms (minimax, MCTS)
- [ ] Opening/midgame/endgame strategies
- [ ] Deck archetype recognition
- [ ] Counter-play detection

### 2.2 UI Polish
**Goal**: Make the game visually appealing and intuitive.

#### 2.2.1 Animations
- [ ] Card draw animation
- [ ] Card play animation
- [ ] Attack animation
- [ ] Damage animation
- [ ] Zone transition effects

#### 2.2.2 Audio
- [ ] Background music
- [ ] Card play sounds
- [ ] Combat sounds
- [ ] Victory/defeat sounds
- [ ] UI interaction sounds

#### 2.2.3 Visual Improvements
- [ ] Better card rendering
- [ ] Field layout improvements
- [ ] Chase/stack visualization
- [ ] Graveyard browser
- [ ] Hand fanning

### 2.3 Quality of Life
- [ ] Undo system
- [ ] Save/load games
- [ ] Auto-pass options
- [ ] Keyboard shortcuts
- [ ] Confirmation dialogs

---

## Phase 3: Content Expansion

### 3.1 Alice Cluster
**~400 cards across 4 sets**
- [ ] The Seven Kings of the Lands (SKL)
- [ ] The Twilight Wanderer (TTW)
- [ ] Battle for Attoractia (BFA)
- [ ] Curse of the Frozen Casket (CFC)

### 3.2 Lapis Cluster
**~400 cards across 4 sets**
- [ ] Legacy Lost (LEL)
- [ ] Return of the Dragon Emperor (RDE)
- [ ] Advent of the Demon King (ADK)
- [ ] Echoes of the New World (ENW)

### 3.3 Reiya Cluster
**~400 cards across 4 sets**
- [ ] Ancient Nights (ACN)
- [ ] Winds of the Ominous Moon (WOM)
- [ ] Time Spinning Witch (TSW)
- [ ] Strangers of New Valhalla (SNV)

### 3.4 New Valhalla Cluster
**~400 cards across 4 sets**
- [ ] The Decisive Battle of Valhalla (DBV)
- [ ] The Magic Stone War (MSW)
- [ ] The Time Spinning Witch (TSW)
- [ ] Saga of the Star Dragon (SSS)

---

## Phase 4: Multiplayer

### 4.1 Network Infrastructure
- [ ] Server architecture design
- [ ] Protocol specification
- [ ] Game state synchronization
- [ ] Latency handling

### 4.2 Player Management
- [ ] Account system
- [ ] Authentication
- [ ] Friend lists
- [ ] Player profiles

### 4.3 Matchmaking
- [ ] Lobby system
- [ ] Quick match
- [ ] Ranked ladder
- [ ] ELO/rating system

### 4.4 Social Features
- [ ] Chat system
- [ ] Spectator mode
- [ ] Game replay sharing

---

## Phase 5: Competitive Features

### 5.1 Tournament Support
- [ ] Tournament creation
- [ ] Swiss pairing
- [ ] Single elimination
- [ ] Match reporting
- [ ] Standings/brackets

### 5.2 Format Support
- [ ] New Frontiers (Standard)
- [ ] Wanderer (Extended)
- [ ] Cluster (Block)
- [ ] Limited (Draft/Sealed)
- [ ] Custom formats

### 5.3 Deck Building
- [ ] Format legality checking
- [ ] Banned/restricted enforcement
- [ ] Deck statistics
- [ ] Import/export formats

---

## Phase 6: Platform Expansion

### 6.1 Mobile
- [ ] Touch controls
- [ ] Responsive UI
- [ ] Android build
- [ ] iOS build

### 6.2 Web
- [ ] Browser-based client
- [ ] WebSocket communication
- [ ] Progressive web app

### 6.3 Distribution
- [ ] Steam release
- [ ] App store listings
- [ ] Auto-updates

---

## Technical Milestones

### Testing
| Phase | Unit Tests | Integration Tests | Coverage Target |
|-------|------------|-------------------|-----------------|
| 1 | 0 | 0 | 0% |
| 2 | 100+ | 20+ | 50% |
| 3 | 200+ | 50+ | 70% |
| 4 | 300+ | 100+ | 80% |
| 5 | 400+ | 150+ | 85% |
| 6 | 500+ | 200+ | 90% |

### Documentation
- [ ] API documentation
- [ ] Card scripting guide
- [ ] Contribution guidelines
- [ ] Architecture overview

### Performance
- [ ] Memory profiling
- [ ] CPU profiling
- [ ] Network optimization
- [ ] Mobile optimization

---

## Release Schedule (Projected)

| Version | Phase | Key Features |
|---------|-------|--------------|
| 0.1.0 | 1 | Core engine, Grimm Cluster |
| 0.2.0 | 2.1 | Basic AI |
| 0.3.0 | 2.2 | Animations & audio |
| 0.4.0 | 2.3 | QoL features |
| 0.5.0 | 3.1 | Alice Cluster |
| 0.6.0 | 3.2 | Lapis Cluster |
| 0.7.0 | 3.3 | Reiya Cluster |
| 0.8.0 | 3.4 | New Valhalla Cluster |
| 0.9.0 | 4 | Multiplayer |
| 1.0.0 | 5 | Tournament support |
| 1.1.0 | 6.1 | Mobile |
| 1.2.0 | 6.2 | Web |

---

## Contributing

### Priority Areas
1. AI development
2. Card scripting for new sets
3. UI/UX improvements
4. Testing
5. Documentation

### Getting Started
1. Fork the repository
2. Read the architecture docs
3. Pick an issue from the roadmap
4. Submit a pull request

---

*Last updated: December 30, 2025*
*Version: 0.1.0*
