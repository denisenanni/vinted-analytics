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
    }

    CATEGORIES = {
        "women/dresses": "/vetements?catalog[]=1904",  # Women's dresses
    }

    def __init__(self, market: str = "IT"):
        self.market = market
        self.base_url = self.BASE_URLS.get(market, self.BASE_URLS["IT"])

    async def random_delay(self, min_sec: float = 2, max_sec: float = 5):
        delay = random.uniform(min_sec, max_sec)
        await asyncio.sleep(delay)

    async def scrape_listing_page(self, page: Page, category: str, page_num: int = 1) -> List[VintedItem]:
        category_path = self.CATEGORIES.get(category, self.CATEGORIES["women/dresses"])
        url = f"{self.base_url}{category_path}&page={page_num}"

        print(f"Scraping: {url}")
        await page.goto(url, wait_until="networkidle")
        await self.random_delay(1, 2)

        items = []

        # Wait for item cards to load
        try:
            await page.wait_for_selector('[data-testid="grid-item"]', timeout=10000)
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
            # Alt format: "Title, brand: BrandName, condizioni: ..."
            if "brand:" in alt_text.lower():
                brand_part = alt_text.lower().split("brand:")[1]
                brand = brand_part.split(",")[0].strip().title()

        # Get favorites count
        fav_el = await card.query_selector('[data-testid="favourite-count-text"]')
        favorites = None
        if fav_el:
            fav_text = await fav_el.inner_text()
            try:
                favorites = int(fav_text)
            except ValueError:
                pass

        # Get size from description
        size = None
        desc_el = await card.query_selector('[data-testid$="--description--content"]')
        if desc_el:
            desc_text = await desc_el.inner_text()
            # Size is often in format "M / IT 42" or similar
            if "/" in desc_text:
                size = desc_text.split("·")[0].strip() if "·" in desc_text else desc_text.split("\n")[0].strip()

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
        """Extract price from card text like '4,00 €' or '€4.00'"""
        import re
        # Look for price patterns: "4,00 €" or "€4.00"
        patterns = [
            r'(\d+[,\.]\d{2})\s*€',  # 4,00 € or 4.00 €
            r'€\s*(\d+[,\.]\d{2})',  # €4,00 or €4.00
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
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
