# Data + Scraper Audit (v1)

Files covered:
- `fowpro/database.py`
- `fowpro/scraper.py`

## fowpro/database.py
- SQLite database with tables: `cards`, `sets`.
- `insert_card()` stores all core fields; keywords stored as bitmask; costs stored per color; judgment cost stored as string.
- `get_card()`, `get_cards_by_set()`, `get_all_cards()`, `search_cards()` return `CardData` objects.
- `_row_to_card()` parses enums and reconstructs `WillCost`, `Keyword`, `Rarity`, `CardType`.
- No schema migrations beyond simple table creation.
- Not storing full parsed ability structure; only raw `ability_text`.

## fowpro/scraper.py
- Async scraper against `https://www.forceofwind.online/card/{code}/`.
- Parses name via title/h1/h2/class fallback; parses type via `card_type=` links; attribute via colour links or text.
- Parses cost from cost image alt text inside `.card-text-info` “Cost:” section.
- Parses ATK/DEF via text patterns or X/Y pattern.
- Parses races via `race=` links or fallback text match.
- Parses ability text from “Text:” section, preserving `[Activate]` etc and cost symbols.
- Keyword extraction is simple text match.
- Ruler/J-ruler linkage via `{code}J` search and judgment cost regex.
- `scrape_set()` and `scrape_grimm_cluster()` drive bulk import with rate limiting.
- `generate_scripts()` calls `scripts.generator.generate_all_scripts()` to produce Python scripts.

Notes/risks:
- HTML parsing is heuristic and may break if site changes.
- Keyword detection is naive and may mis-detect keywords from unrelated text.
- Judgment cost parsing is regex-based and could miss complex symbols.
