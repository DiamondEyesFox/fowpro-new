"""
FoWPro - Card Scraper
=====================
Scrapes card data from Force of Wind website.
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup
import re
from typing import Optional
from .models import CardData, CardType, Attribute, WillCost, Keyword, Rarity
from .database import CardDatabase


# Grimm Cluster set ranges
GRIMM_CLUSTER_SETS = {
    "CMF": ("CMF", 1, 105, "The Crimson Moon's Fairy Tale"),
    "TAT": ("TAT", 1, 105, "The Castle of Heaven and The Two Towers"),
    "MPR": ("MPR", 1, 105, "The Moon Priestess Returns"),
    "MOA": ("MOA", 1, 50, "The Millennia of Ages"),
}


class CardScraper:
    """Scrapes card data from Force of Wind"""

    BASE_URL = "https://www.forceofwind.online/card/"

    def __init__(self, db: CardDatabase):
        self.db = db
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, *args):
        if self.session:
            await self.session.close()

    async def scrape_card(self, code: str) -> Optional[CardData]:
        """Scrape a single card by code"""
        url = f"{self.BASE_URL}{code}/"

        try:
            async with self.session.get(url, timeout=30) as response:
                if response.status != 200:
                    return None

                html = await response.text()
                return self._parse_card_page(html, code)
        except Exception as e:
            print(f"Error scraping {code}: {e}")
            return None

    def _parse_card_page(self, html: str, code: str) -> Optional[CardData]:
        """Parse card data from HTML"""
        soup = BeautifulSoup(html, 'html.parser')

        try:
            # Get full page text for searching
            page_text = soup.get_text()

            # Find card name - it's usually the first heading or in a title element
            name = code  # Default fallback

            # Try multiple methods to find the name
            # Method 1: Look for the page title
            title_tag = soup.find('title')
            if title_tag:
                title_text = title_tag.get_text(strip=True)
                # Title format is "FoWind - Card Name" so take the part after " - "
                if ' - ' in title_text:
                    parts = title_text.split(' - ', 1)
                    if len(parts) > 1:
                        name = parts[1].strip()
                    else:
                        name = parts[0].strip()
                elif '|' in title_text:
                    name = title_text.split('|')[-1].strip()

            # Method 2: Look for h1 or h2 tags
            if name == code:
                for heading in soup.find_all(['h1', 'h2']):
                    heading_text = heading.get_text(strip=True)
                    if heading_text and len(heading_text) > 2 and heading_text != code:
                        # Skip if it looks like a navigation element
                        if 'search' not in heading_text.lower() and 'menu' not in heading_text.lower():
                            name = heading_text
                            break

            # Method 3: Look for card-specific classes
            if name == code:
                for class_name in ['card-name', 'card-title', 'cardname', 'title']:
                    elem = soup.find(class_=class_name)
                    if elem:
                        name = elem.get_text(strip=True)
                        break

            # Initialize defaults
            card_type = CardType.RESONATOR
            attribute = Attribute.NONE
            cost = WillCost()
            atk = 0
            defense = 0
            races = []
            ability_text = ""
            rarity = Rarity.COMMON
            j_ruler_code = None
            ruler_code = None
            judgment_cost = None

            # Parse card type from links (more reliable than text)
            # Look for card_type= parameter in search links
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                if 'card_type=' in href:
                    type_match = re.search(r'card_type=([^&]+)', href)
                    if type_match:
                        type_str = type_match.group(1).lower().replace('%20', ' ').replace('+', ' ')
                        type_map = {
                            'j-ruler': CardType.J_RULER,
                            'ruler': CardType.RULER,
                            'resonator': CardType.RESONATOR,
                            'spell:chant-instant': CardType.SPELL_CHANT_INSTANT,
                            'spell:chant-standby': CardType.SPELL_CHANT_STANDBY,
                            'spell:chant': CardType.SPELL_CHANT,
                            'chant-instant': CardType.SPELL_CHANT_INSTANT,
                            'chant-standby': CardType.SPELL_CHANT_STANDBY,
                            'chant': CardType.SPELL_CHANT,
                            'addition:field': CardType.ADDITION_FIELD,
                            'addition:resonator': CardType.ADDITION_RESONATOR,
                            'regalia': CardType.REGALIA,
                            'special magic stone': CardType.SPECIAL_MAGIC_STONE,
                            'magic stone': CardType.MAGIC_STONE,
                            'basic magic stone': CardType.MAGIC_STONE,
                        }
                        if type_str in type_map:
                            card_type = type_map[type_str]
                            break

            page_lower = page_text.lower()

            # Parse attribute from color indicators
            # Look for attribute symbols like {W}, {R}, {U}, {G}, {B}
            attr_map = {
                '{w}': Attribute.LIGHT,
                '{r}': Attribute.FIRE,
                '{u}': Attribute.WATER,
                '{g}': Attribute.WIND,
                '{b}': Attribute.DARKNESS,
                'light': Attribute.LIGHT,
                'fire': Attribute.FIRE,
                'water': Attribute.WATER,
                'wind': Attribute.WIND,
                'darkness': Attribute.DARKNESS,
            }

            # Check for attribute in links (like /search?colours=W)
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                if 'colours=' in href:
                    color_match = re.search(r'colours=([WRUGB])', href)
                    if color_match:
                        color_char = color_match.group(1).lower()
                        color_map = {'w': Attribute.LIGHT, 'r': Attribute.FIRE,
                                    'u': Attribute.WATER, 'g': Attribute.WIND,
                                    'b': Attribute.DARKNESS}
                        attribute = color_map.get(color_char, Attribute.NONE)
                        break

            # Fallback: check page text for attribute words
            if attribute == Attribute.NONE:
                for pattern, attr in attr_map.items():
                    if pattern in page_lower:
                        attribute = attr
                        break

            # Parse cost using proper DOM traversal
            # Find the "Cost:" section in card-text-info divs
            for info_div in soup.find_all('div', class_='card-text-info'):
                title_div = info_div.find('div', class_='card-text-info-title')
                if title_div and 'Cost:' in title_div.get_text():
                    text_div = info_div.find('div', class_='card-text-info-text')
                    if text_div:
                        # Extract alt text from cost images
                        cost_symbols = []
                        for img in text_div.find_all('img', class_='cost-img'):
                            alt = img.get('alt', '')
                            # Extract symbol from {X} format
                            match = re.match(r'\{(\w+)\}', alt)
                            if match:
                                cost_symbols.append(match.group(1))
                        if cost_symbols:
                            cost_str = ''.join(cost_symbols)
                            cost = WillCost.parse(cost_str)
                    break

            # Parse ATK/DEF - look for "ATK: 500" or "500/500" patterns
            atk_match = re.search(r'ATK[:\s]*(\d+)', page_text, re.IGNORECASE)
            def_match = re.search(r'DEF[:\s]*(\d+)', page_text, re.IGNORECASE)
            if atk_match:
                atk = int(atk_match.group(1))
            if def_match:
                defense = int(def_match.group(1))

            # Fallback: look for X/Y pattern
            if not atk and not defense:
                stat_match = re.search(r'(\d{2,})\s*/\s*(\d{2,})', page_text)
                if stat_match:
                    atk = int(stat_match.group(1))
                    defense = int(stat_match.group(2))

            # Parse races from race links
            race_patterns = ['human', 'fairy tale', 'vampire', 'dragon', 'beast',
                           'elf', 'wizard', 'demon', 'angel', 'god', 'zombie',
                           'machine', 'plant', 'spirit', 'nightmare', 'knight',
                           'wererabbit', 'werewolf', 'golem', 'insect', 'fish',
                           'bird', 'four sacred beasts', 'fantasias']

            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                if 'race=' in href:
                    race_match = re.search(r'race=([^&]+)', href)
                    if race_match:
                        race = race_match.group(1).replace('%20', ' ').replace('+', ' ')
                        if race not in races:
                            races.append(race.title())

            # Fallback: check text for race patterns (only for resonators)
            # Skip fallback for non-resonator cards to avoid matching sidebar/navigation
            is_resonator = card_type in (CardType.RESONATOR, CardType.J_RULER)
            if not races and is_resonator:
                for pattern in race_patterns:
                    if pattern in page_lower:
                        races.append(pattern.title())

            # Parse ability text - find the "Text:" section specifically
            ability_parts = []

            # Find the card-text-info section containing "Text:"
            text_section_found = False
            for title_div in soup.find_all('div', class_='card-text-info-title'):
                if 'Text:' in title_div.get_text():
                    text_section_found = True
                    # Get the parent card-text-info div
                    parent = title_div.find_parent('div', class_='card-text-info')
                    if parent:
                        # Find all card-text-info-text divs within this section
                        for text_div in parent.find_all('div', class_='card-text-info-text'):
                            # Get text, preserving bubble-text keywords and cost symbols
                            parts = []
                            for child in text_div.descendants:
                                # Handle img tags (cost symbols)
                                if hasattr(child, 'name') and child.name == 'img':
                                    alt = child.get('alt', '')
                                    if alt:
                                        parts.append(alt)
                                # Handle bubble-text spans (keywords like [Activate])
                                elif hasattr(child, 'name') and child.name == 'span':
                                    class_list = child.get('class', [])
                                    if 'bubble-text' in class_list:
                                        text = child.get_text(strip=True)
                                        if text:
                                            parts.append(f"[{text}]")
                                # Handle direct text nodes (not inside elements we've already processed)
                                elif isinstance(child, str):
                                    text = child.strip()
                                    if text:
                                        # Don't add text if it's just whitespace or already in an img/span
                                        parts.append(text)

                            # Join and clean up the line
                            line = ' '.join(parts)
                            # Clean up extra spaces around symbols
                            line = re.sub(r'\s+', ' ', line).strip()
                            line = re.sub(r'\s*\{\s*', '{', line)
                            line = re.sub(r'\s*\}\s*', '} ', line)
                            line = line.strip()
                            if line and line not in ability_parts:
                                ability_parts.append(line)
                    break

            # Join with newlines for readability
            ability_text = '\n'.join(ability_parts) if ability_parts else ""

            # Parse keywords from ability text
            keywords = Keyword.NONE
            keyword_map = {
                'swiftness': Keyword.SWIFTNESS,
                'flying': Keyword.FLYING,
                'first strike': Keyword.FIRST_STRIKE,
                'pierce': Keyword.PIERCE,
                'drain': Keyword.DRAIN,
                'imperishable': Keyword.IMPERISHABLE,
                'eternal': Keyword.ETERNAL,
                'quickcast': Keyword.QUICKCAST,
                'target attack': Keyword.TARGET_ATTACK,
                'precision': Keyword.PRECISION,
                'barrier': Keyword.BARRIER,
                'vigilance': Keyword.VIGILANCE,
            }
            for kw_text, kw_enum in keyword_map.items():
                if kw_text in page_lower:
                    keywords |= kw_enum

            # Parse rarity from page
            rarity_map = {
                'super rare': Rarity.SUPER_RARE,
                'rare': Rarity.RARE,
                'uncommon': Rarity.UNCOMMON,
                'common': Rarity.COMMON,
            }
            for rarity_text, rarity_enum in rarity_map.items():
                if rarity_text in page_lower:
                    rarity = rarity_enum
                    break

            # Handle Ruler/J-Ruler relationships
            if card_type == CardType.RULER:
                # Look for J-Ruler code reference
                j_match = re.search(rf'{code}J', page_text)
                if j_match:
                    j_ruler_code = f"{code}J"

                # Look for judgment cost
                judgment_match = re.search(r'Judgment[:\s]*(\{[^}]+\})+', page_text, re.IGNORECASE)
                if judgment_match:
                    j_cost_str = re.findall(r'\{([WRUGB\d]+)\}', judgment_match.group(0))
                    if j_cost_str:
                        judgment_cost = WillCost.parse(''.join(j_cost_str))

            elif card_type == CardType.J_RULER:
                # Link back to ruler
                base_code = code.rstrip('J')
                ruler_code = base_code

            # Determine set code
            set_code = code.split('-')[0] if '-' in code else ""

            return CardData(
                code=code,
                name=name,
                card_type=card_type,
                attribute=attribute,
                cost=cost,
                atk=atk,
                defense=defense,
                races=races,
                keywords=keywords,
                ability_text=ability_text,
                rarity=rarity,
                set_code=set_code,
                j_ruler_code=j_ruler_code,
                ruler_code=ruler_code,
                judgment_cost=judgment_cost,
            )

        except Exception as e:
            print(f"Error parsing {code}: {e}")
            return None

    async def scrape_set(self, set_code: str, start: int, end: int,
                        progress_callback=None) -> int:
        """Scrape all cards in a set range"""
        count = 0

        for num in range(start, end + 1):
            code = f"{set_code}-{num:03d}"

            card = await self.scrape_card(code)
            if card:
                self.db.insert_card(card)
                count += 1

                if progress_callback:
                    progress_callback(code, card.name, num - start + 1, end - start + 1)

            # Also check for J-Ruler version
            j_code = f"{set_code}-{num:03d}J"
            j_card = await self.scrape_card(j_code)
            if j_card:
                self.db.insert_card(j_card)
                count += 1

            # Rate limiting
            await asyncio.sleep(0.5)

        return count

    async def scrape_grimm_cluster(self, progress_callback=None) -> int:
        """Scrape all Grimm Cluster sets"""
        total = 0

        for set_code, (code, start, end, name) in GRIMM_CLUSTER_SETS.items():
            print(f"\nScraping {name} ({set_code})...")
            self.db.insert_set(set_code, name, cluster="Grimm")

            count = await self.scrape_set(code, start, end, progress_callback)
            total += count
            print(f"  Scraped {count} cards from {set_code}")

        return total

    def generate_scripts(self, output_dir: str = None):
        """Generate Python scripts from scraped card data"""
        from pathlib import Path
        from .scripts.generator import generate_all_scripts

        if output_dir is None:
            # Default to scripts/generated directory
            output_dir = Path(__file__).parent / "scripts" / "generated"
        else:
            output_dir = Path(output_dir)

        print(f"\nGenerating scripts to {output_dir}...")
        generate_all_scripts(self.db, output_dir)
        print("Script generation complete!")


async def main():
    """Test scraper"""
    db = CardDatabase("data/cards.db")

    async with CardScraper(db) as scraper:
        # Test single card
        card = await scraper.scrape_card("CMF-001")
        if card:
            print(f"Scraped: {card.name} ({card.code})")
            print(f"  Type: {card.card_type.value}")
            print(f"  Attribute: {card.attribute}")
            print(f"  Cost: {card.cost}")
            print(f"  ATK/DEF: {card.atk}/{card.defense}")

    db.close()


if __name__ == "__main__":
    asyncio.run(main())
