import asyncio
import argparse
from .spiders.vinted_spider import VintedSpider
from .storage.database import init_db, save_items, get_stats, mark_sold_items


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

        # Mark items as sold if they disappeared (only if we scraped enough pages)
        if pages >= 2:
            active_ids = [item.vinted_id for item in items]
            await mark_sold_items(market, category, active_ids)

    # Show stats (non-critical, don't fail if it times out)
    try:
        stats = await get_stats()
        print(f"\nDatabase stats:")
        print(f"  Total items: {stats['total']}")
        print(f"  Active: {stats['active']}")
        print(f"  Sold: {stats['sold']}")
        print(f"  Price changes tracked: {stats['price_changes']}")
    except Exception as e:
        print(f"\nCould not fetch stats (non-critical): {e}")


MARKETS = ["IT", "FR", "DE", "ES", "NL", "PL", "BE", "AT", "PT"]

# Scrape individual subcategories for accurate filtering
CATEGORIES = [
    # Women's clothing
    "women/dresses",
    "women/tops-and-t-shirts",
    "women/jumpers-and-sweaters",
    "women/jeans",
    "women/trousers-and-leggings",
    "women/skirts",
    "women/outerwear",
    "women/suits-and-blazers",
    "women/activewear",
    "women/shorts-and-cropped-trousers"
    # Women's shoes
    "women/boots",
    "women/heels",
    "women/trainers",
    "women/sandals",
    # Women's bags
    "women/handbags",
    "women/backpacks",
    "women/shoulder-bags",
    # Women's accessories
    "women/jewellery",
    "women/watches",
    "women/sunglasses",
    # Men's clothing
    "men/tops-and-t-shirts",
    "men/jumpers-and-sweaters",
    "men/jeans",
    "men/trousers",
    "men/outerwear",
    "men/suits-and-blazers",
    "men/activewear",
    # Men's shoes
    "men/boots",
    "men/trainers",
    "men/formal-shoes",
    # Men's accessories
    "men/bags-and-backpacks",
    "men/jewellery",
    "men/watches",
    "men/sunglasses",
]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Vinted Scraper")
    parser.add_argument("--market", "-m", default="IT", choices=MARKETS, help="Market to scrape")
    parser.add_argument("--category", "-c", default="women/dresses", choices=CATEGORIES, help="Category to scrape")
    parser.add_argument("--pages", "-p", type=int, default=3, help="Number of pages to scrape")
    parser.add_argument("--cleanup", action="store_true", help="Run daily cleanup job instead of scraping")

    args = parser.parse_args()

    if args.cleanup:
        from .jobs.cleanup import run_daily_cleanup
        asyncio.run(run_daily_cleanup())
    else:
        asyncio.run(main(args.market, args.category, args.pages))
