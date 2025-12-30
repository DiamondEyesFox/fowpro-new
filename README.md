# FoWPro - Force of Will TCG Simulator

A complete Force of Will Trading Card Game simulator featuring all Grimm Cluster sets.

## Features

- **Complete Game Engine**: Full implementation of Force of Will rules including:
  - Turn structure (Recovery, Draw, Main, Battle, End phases)
  - Priority system and chase (stack) resolution
  - Combat with all timing windows
  - Will/mana system
  - Ruler/J-Ruler and Judgment mechanics
  - State-based actions

- **Grimm Cluster Sets**:
  - CMF: The Crimson Moon's Fairy Tale (105 cards)
  - TAT: The Castle of Heaven and The Two Towers (105 cards)
  - MPR: The Moon Priestess Returns (105 cards)
  - MOA: The Millennia of Ages (50 cards)

- **PyQt6 GUI**: Full graphical interface with:
  - Card visualization with attribute colors
  - Player areas with hand, field, ruler zones
  - Will pool display
  - Chase/stack visualization
  - Game log
  - Point-and-click gameplay

- **Card Database**: SQLite-based card storage with scraper for Force of Wind

## Installation

```bash
# Clone or download the project
cd fowpro

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or: .venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Launch GUI
```bash
python main.py
```

### Import Grimm Cluster Cards
```bash
python import_grimm.py
```
Note: This takes 10-15 minutes due to rate limiting.

### Test Game (CLI)
```bash
python main.py --test
```

### Commands in CLI Mode
- `state` - Show game state
- `hand` - Show your hand
- `field` - Show all fields
- `pass` - Pass priority
- `stone` - Call a magic stone
- `produce N` - Produce will from stone N
- `play N` - Play card N from hand
- `attack N` - Attack with creature N
- `judgment` - Perform Judgment
- `next` - Advance phase
- `quit` - Exit

## Project Structure

```
fowpro/
├── fowpro/
│   ├── __init__.py      # Package init
│   ├── models.py        # Data models (Card, Player, etc.)
│   ├── database.py      # SQLite card database
│   ├── scraper.py       # Force of Wind scraper
│   ├── engine.py        # Complete game engine
│   └── gui.py           # PyQt6 GUI
├── data/
│   └── cards.db         # Card database (created on first run)
├── main.py              # Entry point
├── import_grimm.py      # Grimm Cluster importer
├── requirements.txt     # Python dependencies
└── README.md            # This file
```

## How to Play

1. Start the GUI with `python main.py`
2. Go to **Game > Load Database** and select `data/cards.db`
3. Go to **Game > New Game** to start a test game
4. Click cards in your hand to play them
5. Click magic stones to produce will
6. Click creatures to attack
7. Use the action buttons for pass, next phase, etc.

## Technical Notes

### Game Engine Architecture

The engine uses an event-driven architecture:
- All state changes emit events
- GUI subscribes to events for updates
- Enables easy replay/undo and networking

Key components:
- `GameEngine`: Main orchestrator
- `TurnMachine`: Phase state machine (implicit in engine)
- `BattleContext`: Combat state tracking
- `ZoneManager`: Card location management (via PlayerState)

### Card Effects

Card effects are currently stored as text. A full implementation would parse
ability text into executable effect objects. The framework supports:
- Continuous effects
- Triggered abilities
- Activated abilities

### Limitations

- Card effects are not fully automated (text only)
- AI opponent not implemented
- Network play not implemented
- Some edge cases may not be handled

## License

This is a fan project for educational purposes.
Force of Will is a trademark of Force of Will Co., Ltd.
Card data is scraped from community sources.

## Contributing

This is a prototype demonstrating clean TCG engine architecture.
Feel free to extend with:
- Full effect parsing/execution
- AI opponents
- Network play
- More card sets
