#!/usr/bin/env python3
"""
FoWPro - Force of Will Simulator
=================================
Main entry point for the application.

Usage:
    python main.py              - Launch GUI
    python main.py --import     - Import Grimm Cluster cards
    python main.py --test       - Run test game in CLI
"""

import sys
import argparse
import asyncio
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="FoWPro - Force of Will Simulator")
    parser.add_argument("--import", dest="do_import", action="store_true",
                       help="Import Grimm Cluster cards from online database")
    parser.add_argument("--test", action="store_true",
                       help="Run a test game in CLI mode")
    parser.add_argument("--db", default="data/cards.db",
                       help="Path to card database")

    args = parser.parse_args()

    if args.do_import:
        import_cards(args.db)
    elif args.test:
        run_test_game(args.db)
    else:
        run_gui(args.db)


def import_cards(db_path: str):
    """Import cards from Force of Wind"""
    print("=" * 60)
    print("FoWPro Card Importer")
    print("=" * 60)

    from fowpro.database import CardDatabase
    from fowpro.scraper import CardScraper, GRIMM_CLUSTER_SETS

    db = CardDatabase(db_path)
    print(f"Database: {db_path}")
    print(f"Current card count: {db.card_count()}")
    print()

    def progress(code, name, current, total):
        print(f"  [{current}/{total}] {code}: {name}")

    async def do_import():
        async with CardScraper(db) as scraper:
            total = await scraper.scrape_grimm_cluster(progress)
            # Generate scripts after importing
            scraper.generate_scripts()
            return total

    print("Importing Grimm Cluster sets...")
    print("This may take several minutes due to rate limiting.")
    print()

    total = asyncio.run(do_import())

    print()
    print("=" * 60)
    print(f"Import complete! Total cards: {db.card_count()}")
    print("Scripts generated from ability text.")
    print("=" * 60)

    db.close()


def run_test_game(db_path: str):
    """Run a test game in CLI"""
    print("=" * 60)
    print("FoWPro Test Game")
    print("=" * 60)

    from fowpro.database import CardDatabase
    from fowpro.engine import GameEngine, EventType
    from fowpro.models import CardData, CardType, Attribute, WillCost, Keyword

    # Load or create database
    db = CardDatabase(db_path)

    # Create test cards if database is empty
    if db.card_count() == 0:
        print("Creating test cards...")
        create_test_cards(db)

    # Get cards
    all_cards = db.get_all_cards()
    rulers = [c for c in all_cards if c.card_type == CardType.RULER]
    resonators = [c for c in all_cards if c.card_type == CardType.RESONATOR]
    stones = [c for c in all_cards if c.is_stone()]

    if not rulers or not resonators or not stones:
        print("Insufficient cards. Creating test cards...")
        create_test_cards(db)
        all_cards = db.get_all_cards()
        rulers = [c for c in all_cards if c.card_type == CardType.RULER]
        resonators = [c for c in all_cards if c.card_type == CardType.RESONATOR]
        stones = [c for c in all_cards if c.is_stone()]

    # Build decks
    p0_deck = (resonators * 10)[:40]
    p0_stones = (stones * 5)[:10]
    p0_ruler = rulers[0]

    p1_deck = (resonators * 10)[:40]
    p1_stones = (stones * 5)[:10]
    p1_ruler = rulers[0]

    # Create engine
    engine = GameEngine(db)

    def log_event(event):
        print(f"  [{event.event_type.name}]", end="")
        if event.card:
            print(f" {event.card.data.name}", end="")
        if event.data:
            print(f" {event.data}", end="")
        print()

    engine.subscribe(log_event)

    # Set up and start
    engine.setup_game(p0_deck, p0_stones, p0_ruler, p1_deck, p1_stones, p1_ruler)
    engine.shuffle_decks()
    engine.start_game(0)

    print()
    print("Game started! Commands:")
    print("  state     - Show game state")
    print("  hand      - Show your hand")
    print("  field     - Show fields")
    print("  pass      - Pass priority")
    print("  stone     - Call a magic stone")
    print("  produce N - Produce will from stone N")
    print("  play N    - Play card N from hand")
    print("  attack N  - Attack with creature N")
    print("  next      - Advance phase")
    print("  quit      - Exit")
    print()

    while not engine.game_over:
        p = engine.players[0]

        # Show prompt
        prompt = f"[T{engine.turn_number} {engine.current_phase.name}] "
        prompt += f"Life:{p.life} Will:{p.will_pool.total} "
        prompt += f"Hand:{len(p.hand)} > "

        try:
            cmd = input(prompt).strip().lower()
        except EOFError:
            break

        if not cmd:
            continue

        parts = cmd.split()
        action = parts[0]

        try:
            if action == "quit" or action == "q":
                break

            elif action == "state":
                print(f"Turn: {engine.turn_number}, Phase: {engine.current_phase.name}")
                print(f"Priority: Player {engine.priority_player + 1}")
                print(f"P1 Life: {engine.players[0].life}, P2 Life: {engine.players[1].life}")

            elif action == "hand":
                print("Your hand:")
                for i, card in enumerate(p.hand):
                    print(f"  [{i}] {card.data.name} ({card.data.cost})")

            elif action == "field":
                for pi, player in enumerate(engine.players):
                    print(f"Player {pi + 1} field:")
                    for i, card in enumerate(player.field):
                        status = "R" if card.is_rested else ""
                        print(f"  [{i}] {card.data.name} {card.effective_atk}/{card.effective_def} {status}")

            elif action == "pass":
                if engine.pass_priority(0):
                    print("Both passed - advancing phase")
                    engine.advance_phase()

            elif action == "stone":
                if engine.call_stone(0):
                    print("Called a magic stone!")
                else:
                    print("Cannot call stone")

            elif action == "produce":
                idx = int(parts[1]) if len(parts) > 1 else 0
                field_stones = [c for c in p.field if c.data.is_stone()]
                if idx < len(field_stones):
                    if engine.produce_will(0, field_stones[idx]):
                        print(f"Produced will from {field_stones[idx].data.name}")
                    else:
                        print("Cannot produce will")
                else:
                    print("Invalid stone index")

            elif action == "play":
                idx = int(parts[1]) if len(parts) > 1 else 0
                if idx < len(p.hand):
                    card = p.hand[idx]
                    if engine.play_card(0, card):
                        print(f"Played {card.data.name}")
                    else:
                        print("Cannot play that card")
                else:
                    print("Invalid hand index")

            elif action == "attack":
                idx = int(parts[1]) if len(parts) > 1 else 0
                creatures = [c for c in p.field if c.data.is_resonator()]
                if idx < len(creatures):
                    if engine.declare_attack(0, creatures[idx], target_player=1):
                        print(f"{creatures[idx].data.name} attacks!")
                    else:
                        print("Cannot attack with that creature")
                else:
                    print("Invalid creature index")

            elif action == "next":
                engine.advance_phase()

            elif action == "judgment" or action == "j":
                if engine.perform_judgment(0):
                    print("Judgment!")
                else:
                    print("Cannot perform Judgment")

            else:
                print(f"Unknown command: {action}")

        except Exception as e:
            print(f"Error: {e}")

    print()
    if engine.game_over:
        winner = "Player 1" if engine.winner == 0 else "Player 2"
        print(f"Game Over! {winner} wins!")

    db.close()


def create_test_cards(db):
    """Create test cards in the database"""
    from fowpro.models import CardData, CardType, Attribute, WillCost, Keyword, Rarity

    # Test ruler
    ruler = CardData(
        code="TEST-001",
        name="Grimm, the Fairy Tale Prince",
        card_type=CardType.RULER,
        attribute=Attribute.LIGHT,
        cost=WillCost(),
        ability_text="Continuous: You may pay the attribute cost of Fairy Tale resonators with will of any attribute.",
        rarity=Rarity.RARE,
        set_code="TEST",
        j_ruler_code="TEST-001J",
        judgment_cost=WillCost(light=2, void=1),
    )
    db.insert_card(ruler)

    j_ruler = CardData(
        code="TEST-001J",
        name="Grimm, the Avenger",
        card_type=CardType.J_RULER,
        attribute=Attribute.LIGHT,
        cost=WillCost(),
        atk=1000,
        defense=1000,
        rarity=Rarity.RARE,
        set_code="TEST",
        ruler_code="TEST-001",
    )
    db.insert_card(j_ruler)

    # Resonators
    resonator_data = [
        ("Fire Resonator", Attribute.FIRE, 500, 500, WillCost(fire=1)),
        ("Water Resonator", Attribute.WATER, 400, 600, WillCost(water=1)),
        ("Wind Resonator", Attribute.WIND, 600, 400, WillCost(wind=1)),
        ("Light Resonator", Attribute.LIGHT, 450, 550, WillCost(light=1)),
        ("Dark Resonator", Attribute.DARKNESS, 550, 450, WillCost(darkness=1)),
        ("Swift Attacker", Attribute.WIND, 300, 300, WillCost(wind=1)),
        ("Big Resonator", Attribute.FIRE, 800, 800, WillCost(fire=2, void=1)),
    ]

    for i, (name, attr, atk, def_, cost) in enumerate(resonator_data):
        card = CardData(
            code=f"TEST-{100+i:03d}",
            name=name,
            card_type=CardType.RESONATOR,
            attribute=attr,
            cost=cost,
            atk=atk,
            defense=def_,
            rarity=Rarity.COMMON,
            set_code="TEST",
        )
        if name == "Swift Attacker":
            card.keywords = Keyword.SWIFTNESS
        db.insert_card(card)

    # Magic Stones
    for i, (name, attr) in enumerate([
        ("Fire Stone", Attribute.FIRE),
        ("Water Stone", Attribute.WATER),
        ("Wind Stone", Attribute.WIND),
        ("Light Stone", Attribute.LIGHT),
        ("Dark Stone", Attribute.DARKNESS),
    ]):
        stone = CardData(
            code=f"TEST-{200+i:03d}",
            name=name,
            card_type=CardType.MAGIC_STONE,
            attribute=attr,
            cost=WillCost(),
            rarity=Rarity.COMMON,
            set_code="TEST",
        )
        db.insert_card(stone)

    print(f"Created {db.card_count()} test cards")


def run_gui(db_path: str):
    """Run the GUI"""
    import datetime
    import traceback

    # Set up logging to file
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"fowpro_{timestamp}.log"
    crash_log = log_dir / "crash.log"

    # Tell user where log is before redirecting
    print(f"Logging to: {log_file.absolute()}")

    # Redirect stdout and stderr to log file (unbuffered for crash safety)
    log_handle = open(log_file, 'w')
    sys.stdout = log_handle
    sys.stderr = log_handle

    # Make prints flush immediately
    import builtins
    _original_print = builtins.print
    def flushing_print(*args, **kwargs):
        kwargs.setdefault('flush', True)
        _original_print(*args, **kwargs)
    builtins.print = flushing_print

    # Set up global exception handler to catch any uncaught exceptions
    def crash_handler(exc_type, exc_value, exc_tb):
        crash_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        crash_info = f"\n{'='*60}\nCRASH at {crash_time}\n{'='*60}\n"
        crash_info += ''.join(traceback.format_exception(exc_type, exc_value, exc_tb))
        crash_info += f"\n{'='*60}\n"

        # Write to both session log and persistent crash log
        print(crash_info)

        # Also append to persistent crash log
        with open(crash_log, 'a') as f:
            f.write(crash_info)

    sys.excepthook = crash_handler

    print(f"FoWPro GUI started at {datetime.datetime.now()}")
    print(f"Log file: {log_file}")
    print(f"Crash log: {crash_log}")
    print("=" * 60)

    try:
        from fowpro.gui.app import run_app
        result = run_app()
    except Exception as e:
        crash_handler(type(e), e, e.__traceback__)
        result = 1
    finally:
        print("=" * 60)
        print(f"FoWPro GUI ended at {datetime.datetime.now()}")
        log_handle.close()

    sys.exit(result)


if __name__ == "__main__":
    main()
