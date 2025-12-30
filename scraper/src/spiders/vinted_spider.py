import asyncio
import random
from typing import List, Optional
from playwright.async_api import async_playwright, Page
from ..models.item import VintedItem


class VintedSpider:
    BASE_URLS = {
        "IT": "https://www.vinted.it",
        "FR": "https://www.vinted.fr",
        "DE": "https://www.vinted.de",
        "ES": "https://www.vinted.es",
        "NL": "https://www.vinted.nl",
        "PL": "https://www.vinted.pl",
        "BE": "https://www.vinted.be",
        "AT": "https://www.vinted.at",
        "PT": "https://www.vinted.pt",
    }

    # Catalog IDs and slugs - IDs are universal across all markets
    # Format: /catalog/{id}-{slug}
    CATALOG_IDS = {
        # Parent categories (all items in category)
        "women/clothing": 4,      # All women's clothes
        "men/clothing": 2050,     # All men's clothes
        "women/shoes": 16,        # All women's shoes
        "men/shoes": 1231,        # All men's shoes
        "women/bags": 19,         # All women's bags
        # Women's Clothing subcategories
        "women/dresses": 10,
        "women/tops-and-t-shirts": 12,
        "women/jumpers-and-sweaters": 13,
        "women/jeans": 183,
        "women/trousers-and-leggings": 9,
        "women/skirts": 11,
        "women/shorts-and-cropped-trousers": 15,
        "women/outerwear": 1037,
        "women/suits-and-blazers": 8,
        "women/jumpsuits-and-playsuits": 1035,
        "women/activewear": 73,
        "women/swimwear": 28,
        "women/lingerie-and-nightwear": 29,
        "women/maternity-clothes": 1176,
        "women/costumes-and-special-outfits": 1782,
        "women/other-clothing": 18,
        # Women's Shoes
        "women/boots": 1049,
        "women/heels": 543,
        "women/trainers": 2632,
        "women/sandals": 2949,
        "women/ballerinas": 2955,
        "women/slippers": 215,
        "women/sports-shoes": 2630,
        "women/flip-flops-and-slides": 2952,
        "women/espadrilles": 2953,
        "women/boat-shoes-loafers-and-moccasins": 2954,
        "women/clogs-and-mules": 2623,
        "women/mary-janes-and-t-bar-shoes": 2950,
        "women/lace-up-shoes": 2951,
        # Women's Bags
        "women/handbags": 156,
        "women/backpacks": 157,
        "women/shoulder-bags": 158,
        "women/tote-bags": 552,
        "women/clutches": 159,
        "women/wallets-and-purses": 160,
        "women/bucket-bags": 2942,
        "women/hobo-bags": 2945,
        "women/beach-bags": 2940,
        "women/gym-bags": 2944,
        "women/bum-bags": 1848,
        "women/satchels-and-messenger-bags": 1784,
        "women/makeup-bags": 161,
        "women/luggage-and-suitcases": 1850,
        # Women's Accessories
        "women/jewellery": 21,
        "women/watches": 22,
        "women/sunglasses": 26,
        "women/belts": 20,
        "women/hats-and-caps": 88,
        "women/scarves-and-shawls": 89,
        "women/gloves": 90,
        "women/hair-accessories": 1123,
        "women/umbrellas": 1851,
        "women/keyrings": 1852,
        # Men's Clothing
        "men/tops-and-t-shirts": 76,
        "men/jumpers-and-sweaters": 79,
        "men/jeans": 257,
        "men/trousers": 34,
        "men/shorts": 80,
        "men/outerwear": 1206,
        "men/suits-and-blazers": 32,
        "men/activewear": 30,
        "men/swimwear": 84,
        "men/sleepwear": 2910,
        "men/socks-and-underwear": 85,
        "men/costumes-and-special-outfits": 92,
        "men/other-mens-clothing": 83,
        # Men's Shoes
        "men/boots": 1233,
        "men/trainers": 1242,
        "men/formal-shoes": 1238,
        "men/sandals": 2968,
        "men/sports-shoes": 1452,
        "men/slippers": 2659,
        "men/flip-flops-and-slides": 2969,
        "men/boat-shoes-loafers-and-moccasins": 2656,
        "men/espadrilles": 2657,
        "men/clogs-and-mules": 2970,
        # Men's Accessories
        "men/bags-and-backpacks": 94,
        "men/jewellery": 95,
        "men/watches": 97,
        "men/sunglasses": 98,
        "men/belts": 96,
        "men/hats-and-caps": 86,
        "men/scarves-and-shawls": 87,
        "men/gloves": 91,
        "men/ties-and-bow-ties": 2956,
        "men/braces-and-suspenders": 2959,
    }

    # Slug mappings per market (for URL construction)
    # Using English slugs works for all markets via redirect
    CATEGORY_SLUGS = {slug.split("/")[1]: slug.split("/")[1] for slug in CATALOG_IDS.keys()}

    # Reverse mapping: catalog_id -> category name
    CATALOG_ID_TO_CATEGORY = {v: k for k, v in CATALOG_IDS.items()}

    def __init__(self, market: str = "IT"):
        self.market = market
        self.base_url = self.BASE_URLS.get(market, self.BASE_URLS["IT"])

    async def random_delay(self, min_sec: float = 2, max_sec: float = 5):
        delay = random.uniform(min_sec, max_sec)
        await asyncio.sleep(delay)


    def _get_category_url(self, category: str, page_num: int = 1) -> str:
        """Build catalog URL for any market. IDs are universal, slugs redirect automatically."""
        catalog_id = self.CATALOG_IDS.get(category, self.CATALOG_IDS["women/dresses"])
        # Use the category slug from the key (e.g., "women/dresses" -> "dresses")
        slug = category.split("/")[-1] if "/" in category else category
        return f"{self.base_url}/catalog/{catalog_id}-{slug}?page={page_num}"

    @classmethod
    def get_all_categories(cls) -> list:
        """Return list of all available categories."""
        return list(cls.CATALOG_IDS.keys())

    async def scrape_listing_page(self, page: Page, category: str, page_num: int = 1) -> List[VintedItem]:
        url = self._get_category_url(category, page_num)

        print(f"Scraping: {url}")
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await self.random_delay(2, 3)

        items = []

        # Wait for item cards to load
        try:
            await page.wait_for_selector('[data-testid="grid-item"]', timeout=20000)
        except Exception:
            print(f"No items found on page {page_num}")
            return items

        # Get all item cards
        item_cards = await page.query_selector_all('[data-testid="grid-item"]')
        print(f"Found {len(item_cards)} items on page {page_num}")

        for card in item_cards:
            try:
                item = await self._parse_item_card(card, category)
                if item:
                    items.append(item)
            except Exception as e:
                print(f"Error parsing item: {e}")
                continue

        return items

    async def _parse_item_card(self, card, category: str) -> Optional[VintedItem]:
        # Get link and extract vinted_id
        link_el = await card.query_selector('a')
        if not link_el:
            return None

        href = await link_el.get_attribute('href')
        if not href:
            return None

        # Extract item ID from URL like /items/12345-item-title
        vinted_id = href.split('/items/')[-1].split('-')[0] if '/items/' in href else None
        if not vinted_id:
            return None

        # Get title/brand from description-title
        title_el = await card.query_selector('[data-testid$="--description-title"]')
        title = await title_el.inner_text() if title_el else "Unknown"

        # Get full card text to extract price
        card_text = await card.inner_text()
        price = self._extract_price_from_text(card_text)

        # Get image - extract brand from alt text if available
        img_el = await card.query_selector('img')
        image_url = None
        brand = None
        if img_el:
            image_url = await img_el.get_attribute('src')
            alt_text = await img_el.get_attribute('alt') or ""
            # Alt format varies by market: "brand:", "marca:", "marque:", etc.
            brand_keywords = ["brand:", "marca:", "marque:", "marke:"]
            alt_lower = alt_text.lower()
            for keyword in brand_keywords:
                if keyword in alt_lower:
                    brand_part = alt_lower.split(keyword)[1]
                    brand = brand_part.split(",")[0].strip().title()
                    break

        # Fallback: use title as brand (Vinted shows brand name in title area)
        if not brand and title and title.strip().lower() != "unknown":
            brand = title.strip()

        # Get favorites count (default to 0 if badge not shown)
        fav_el = await card.query_selector('[data-testid="favourite-count-text"]')
        favorites = 0
        if fav_el:
            fav_text = await fav_el.inner_text()
            try:
                favorites = int(fav_text)
            except ValueError:
                favorites = 0

        # Get size from description
        size = None
        desc_el = await card.query_selector('[data-testid$="--description--content"]')
        if desc_el:
            desc_text = await desc_el.inner_text()
            # Description format: "Brand\n\nS / IT 40 / EU 36 · Condition"
            # Size patterns: "XS / IT 38", "M / 42", "L / IT 44 / EU 40", "36 / S"
            import re
            lines = [line.strip() for line in desc_text.split('\n') if line.strip()]
            for line in lines:
                # Remove condition part after "·"
                clean_line = line.split('·')[0].strip()
                # Match size patterns: starts with size letter OR contains "IT/EU" size numbers
                size_pattern = r'^(XXS|XS|S|M|L|XL|XXL|XXXL|\d{2})\s*/'
                if re.match(size_pattern, clean_line, re.IGNORECASE):
                    size = clean_line
                    break

        return VintedItem(
            vinted_id=vinted_id,
            title=title.strip(),
            price=price,
            brand=brand,
            size=size,
            url=f"{self.base_url}{href}" if not href.startswith('http') else href,
            image_url=image_url,
            favorites=favorites,
            market=self.market,
            category=category
        )

    def _extract_price_from_text(self, text: str) -> float:
        """Extract price from card text like '4,00 €' or '€4.00' or '25,00 zł'"""
        import re
        # Look for price patterns for various currencies
        patterns = [
            r'(\d+[,\.]\d{2})\s*€',  # 4,00 € or 4.00 €
            r'€\s*(\d+[,\.]\d{2})',  # €4,00 or €4.00
            r'(\d+[,\.]\d{2})\s*zł',  # 25,00 zł (Polish złoty)
            r'zł\s*(\d+[,\.]\d{2})',  # zł25,00
            r'(\d+[,\.]\d{2})\s*PLN',  # 25,00 PLN
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                price_str = match.group(1).replace(',', '.')
                try:
                    return float(price_str)
                except ValueError:
                    pass
        return 0.0

    def _parse_price(self, price_text: str) -> float:
        # Remove currency symbols and convert to float
        # Handle formats like "€25,00" or "25,00 €"
        clean = price_text.replace('€', '').replace(' ', '').replace(',', '.').strip()
        try:
            return float(clean)
        except ValueError:
            return 0.0

    async def scrape(self, category: str = "women/dresses", max_pages: int = 3) -> List[VintedItem]:
        all_items = []

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 720}
            )
            page = await context.new_page()

            for page_num in range(1, max_pages + 1):
                try:
                    items = await self.scrape_listing_page(page, category, page_num)
                    all_items.extend(items)
                    print(f"Page {page_num}: scraped {len(items)} items (total: {len(all_items)})")

                    if page_num < max_pages:
                        await self.random_delay(2, 4)
                except Exception as e:
                    print(f"Error on page {page_num}: {e}")
                    continue

            await browser.close()

        return all_items
