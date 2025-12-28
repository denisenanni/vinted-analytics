import asyncio
import argparse
from .spiders.vinted_spider import VintedSpider
from .storage.database import init_db, save_items, get_item_count


async def main(market: str = "IT", category: str = "women/dresses", pages: int = 3):
    print(f"Starting Vinted scraper")
    print(f"  Market: {market}")
    print(f"  Category: {category}")
    print(f"  Pages: {pages}")
    print("-" * 40)

    # Initialize database
    await init_db()

    # Run spider
    spider = VintedSpider(market=market)
    items = await spider.scrape(category=category, max_pages=pages)

    print("-" * 40)
    print(f"Scraped {len(items)} items total")

    # Save to database
    if items:
        await save_items(items)

    # Show stats
    total_count = await get_item_count()
    print(f"Total items in database: {total_count}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Vinted Scraper")
    parser.add_argument("--market", "-m", default="IT", choices=["IT", "FR", "DE", "ES"], help="Market to scrape")
    parser.add_argument("--category", "-c", default="women/dresses", help="Category to scrape")
    parser.add_argument("--pages", "-p", type=int, default=3, help="Number of pages to scrape")

    args = parser.parse_args()
    asyncio.run(main(args.market, args.category, args.pages))
