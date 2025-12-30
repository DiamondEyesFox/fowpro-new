"""
FoWPro - Card Database
======================
SQLite database for card storage and retrieval.
"""

import sqlite3
import json
from pathlib import Path
from typing import Optional
from .models import (
    CardData, CardType, Attribute, WillCost, Keyword, Rarity, CardAbility
)


class CardDatabase:
    """SQLite-based card database"""

    def __init__(self, db_path: str = "data/cards.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn: Optional[sqlite3.Connection] = None
        self._connect()
        self._create_tables()

    def _connect(self):
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row

    def _create_tables(self):
        cursor = self.conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cards (
                code TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                card_type TEXT NOT NULL,
                attribute TEXT,
                cost_light INTEGER DEFAULT 0,
                cost_fire INTEGER DEFAULT 0,
                cost_water INTEGER DEFAULT 0,
                cost_wind INTEGER DEFAULT 0,
                cost_darkness INTEGER DEFAULT 0,
                cost_void INTEGER DEFAULT 0,
                cost_x INTEGER DEFAULT 0,
                atk INTEGER DEFAULT 0,
                def INTEGER DEFAULT 0,
                races TEXT,
                keywords INTEGER DEFAULT 0,
                ability_text TEXT,
                flavor_text TEXT,
                rarity TEXT,
                set_code TEXT,
                j_ruler_code TEXT,
                judgment_cost TEXT,
                ruler_code TEXT,
                image_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sets (
                code TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                release_date TEXT,
                card_count INTEGER,
                cluster TEXT
            )
        """)

        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_cards_set ON cards(set_code)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_cards_type ON cards(card_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_cards_name ON cards(name)")

        self.conn.commit()

    def insert_card(self, card: CardData, image_url: str = "") -> bool:
        """Insert or update a card"""
        cursor = self.conn.cursor()

        try:
            cursor.execute("""
                INSERT OR REPLACE INTO cards (
                    code, name, card_type, attribute,
                    cost_light, cost_fire, cost_water, cost_wind, cost_darkness, cost_void, cost_x,
                    atk, def, races, keywords, ability_text, flavor_text,
                    rarity, set_code, j_ruler_code, judgment_cost, ruler_code, image_url,
                    updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                card.code,
                card.name,
                card.card_type.value,
                card.attribute.name if card.attribute else "NONE",
                card.cost.light,
                card.cost.fire,
                card.cost.water,
                card.cost.wind,
                card.cost.darkness,
                card.cost.void,
                1 if card.cost.x else 0,
                card.atk,
                card.defense,
                json.dumps(card.races),
                card.keywords.value if card.keywords else 0,
                card.ability_text,
                card.flavor_text,
                card.rarity.value if card.rarity else "C",
                card.set_code,
                card.j_ruler_code,
                str(card.judgment_cost) if card.judgment_cost else "",
                card.ruler_code,
                image_url,
            ))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error inserting card {card.code}: {e}")
            return False

    def get_card(self, code: str) -> Optional[CardData]:
        """Get a card by code"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM cards WHERE code = ?", (code,))
        row = cursor.fetchone()

        if not row:
            return None

        return self._row_to_card(row)

    def get_cards_by_set(self, set_code: str) -> list[CardData]:
        """Get all cards in a set"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM cards WHERE set_code = ? ORDER BY code", (set_code,))
        return [self._row_to_card(row) for row in cursor.fetchall()]

    def get_all_cards(self) -> list[CardData]:
        """Get all cards"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM cards ORDER BY code")
        return [self._row_to_card(row) for row in cursor.fetchall()]

    def search_cards(self, name: str = "", card_type: str = "",
                     attribute: str = "", set_code: str = "") -> list[CardData]:
        """Search cards with filters"""
        cursor = self.conn.cursor()

        query = "SELECT * FROM cards WHERE 1=1"
        params = []

        if name:
            query += " AND name LIKE ?"
            params.append(f"%{name}%")
        if card_type:
            query += " AND card_type = ?"
            params.append(card_type)
        if attribute:
            query += " AND attribute = ?"
            params.append(attribute)
        if set_code:
            query += " AND set_code = ?"
            params.append(set_code)

        query += " ORDER BY code"
        cursor.execute(query, params)

        return [self._row_to_card(row) for row in cursor.fetchall()]

    def _row_to_card(self, row: sqlite3.Row) -> CardData:
        """Convert database row to CardData"""
        cost = WillCost(
            light=row["cost_light"],
            fire=row["cost_fire"],
            water=row["cost_water"],
            wind=row["cost_wind"],
            darkness=row["cost_darkness"],
            void=row["cost_void"],
            x=bool(row["cost_x"]),
        )

        # Parse attribute
        attr_str = row["attribute"] or "NONE"
        try:
            attribute = Attribute[attr_str]
        except KeyError:
            attribute = Attribute.NONE

        # Parse card type
        card_type = CardType.from_string(row["card_type"])

        # Parse races
        try:
            races = json.loads(row["races"]) if row["races"] else []
        except:
            races = []

        # Parse keywords
        keywords = Keyword(row["keywords"]) if row["keywords"] else Keyword.NONE

        # Parse rarity
        try:
            rarity = Rarity(row["rarity"])
        except:
            rarity = Rarity.COMMON

        # Parse judgment cost
        judgment_cost = None
        if row["judgment_cost"]:
            judgment_cost = WillCost.parse(row["judgment_cost"])

        return CardData(
            code=row["code"],
            name=row["name"],
            card_type=card_type,
            attribute=attribute,
            cost=cost,
            atk=row["atk"] or 0,
            defense=row["def"] or 0,
            races=races,
            keywords=keywords,
            ability_text=row["ability_text"] or "",
            flavor_text=row["flavor_text"] or "",
            rarity=rarity,
            set_code=row["set_code"] or "",
            j_ruler_code=row["j_ruler_code"] or "",
            judgment_cost=judgment_cost,
            ruler_code=row["ruler_code"] or "",
        )

    def card_count(self) -> int:
        """Get total card count"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM cards")
        return cursor.fetchone()[0]

    def set_count(self, set_code: str) -> int:
        """Get card count for a set"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM cards WHERE set_code = ?", (set_code,))
        return cursor.fetchone()[0]

    def insert_set(self, code: str, name: str, release_date: str = "",
                   card_count: int = 0, cluster: str = ""):
        """Insert a set"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO sets (code, name, release_date, card_count, cluster)
            VALUES (?, ?, ?, ?, ?)
        """, (code, name, release_date, card_count, cluster))
        self.conn.commit()

    def close(self):
        if self.conn:
            self.conn.close()
