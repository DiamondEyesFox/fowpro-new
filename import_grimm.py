#!/usr/bin/env python3
"""
Import all Grimm Cluster cards from Force of Wind.

This script scrapes card data for all four Grimm Cluster sets:
- CMF: The Crimson Moon's Fairy Tale (105 cards)
- TAT: The Castle of Heaven and The Two Towers (105 cards)
- MPR: The Moon Priestess Returns (105 cards)
- MOA: The Millennia of Ages (50 cards)

Total: ~365 cards

Usage:
    python import_grimm.py

Note: This will take 10-15 minutes due to rate limiting.
"""

import asyncio
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from fowpro.database import CardDatabase
from fowpro.scraper import CardScraper, GRIMM_CLUSTER_SETS


async def import_all():
    print("=" * 70)
    print("FoWPro - Grimm Cluster Card Importer")
    print("=" * 70)
    print()
    print("Sets to import:")
    for code, (_, start, end, name) in GRIMM_CLUSTER_SETS.items():
        print(f"  {code}: {name} ({end - start + 1} cards)")
    print()
    print("Estimated time: 10-15 minutes (rate limited to be nice to the server)")
    print()

    db_path = "data/cards.db"
    db = CardDatabase(db_path)
    print(f"Database: {db_path}")
    print(f"Current card count: {db.card_count()}")
    print()

    total_imported = 0

    async with CardScraper(db) as scraper:
        for set_code, (code, start, end, name) in GRIMM_CLUSTER_SETS.items():
            print(f"\n{'='*70}")
            print(f"Importing: {name} ({set_code})")
            print(f"{'='*70}")

            db.insert_set(set_code, name, cluster="Grimm")
            count = 0

            for num in range(start, end + 1):
                card_code = f"{code}-{num:03d}"
                print(f"  [{num - start + 1:3d}/{end - start + 1}] {card_code}...", end=" ")

                card = await scraper.scrape_card(card_code)
                if card:
                    db.insert_card(card)
                    print(f"{card.name[:40]}")
                    count += 1
                else:
                    print("(not found)")

                # Also check for J-Ruler version
                j_code = f"{code}-{num:03d}J"
                j_card = await scraper.scrape_card(j_code)
                if j_card:
                    db.insert_card(j_card)
                    print(f"         + {j_code}: {j_card.name[:40]}")
                    count += 1

                # Rate limiting
                await asyncio.sleep(0.5)

            print(f"\nImported {count} cards from {set_code}")
            total_imported += count

    print()
    print("=" * 70)
    print(f"Import complete!")
    print(f"Total cards imported this session: {total_imported}")
    print(f"Total cards in database: {db.card_count()}")
    print("=" * 70)

    # Generate scripts
    print()
    print("Generating card scripts...")
    from fowpro.scripts.generator import generate_all_scripts
    from pathlib import Path

    scripts_dir = Path(__file__).parent / "fowpro" / "scripts" / "generated"
    generate_all_scripts(db, scripts_dir)
    print("Scripts generated!")

    db.close()


def main():
    try:
        asyncio.run(import_all())
    except KeyboardInterrupt:
        print("\n\nImport cancelled by user.")
        sys.exit(1)


if __name__ == "__main__":
    main()
