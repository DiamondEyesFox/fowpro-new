# Entry Points Audit (v1)

Files covered:
- `main.py`
- `import_grimm.py`

## main.py
- CLI entry with three modes: GUI (default), import (`--import`), and CLI test (`--test`).
- `import_cards()` uses `CardScraper.scrape_grimm_cluster()` then `scraper.generate_scripts()`.
- `run_test_game()` builds decks from DB, falls back to `create_test_cards()` if DB empty.
- CLI test supports basic actions: state/hand/field/pass/call stone/produce/play/attack/next/judgment.
- GUI run sets up logging, global exception handler, then calls `fowpro.gui.app.run_app()`.
- Explicitly uses `engine.pass_priority()` and `engine.advance_phase()` for CLI.
- Contains test cards with simple stats and keywords; no effects beyond keywords.

## import_grimm.py
- Async scraper to import all Grimm cluster sets with rate limiting.
- Inserts set metadata, card data; also attempts J-ruler codes.
- Generates scripts to `fowpro/scripts/generated` after import using `generate_all_scripts()`.
- Hard-coded DB path `data/cards.db`.

Notes/risks:
- CLI test is minimal and doesn’t exercise full rules system or effects beyond keywords.
- Import scripts depend on Force of Wind site availability/structure.
