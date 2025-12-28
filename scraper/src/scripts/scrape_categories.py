"""Scrape all available categories from Vinted catalog."""
import asyncio
import json
import re
from playwright.async_api import async_playwright


async def get_category_links(page, base_url: str, url_path: str):
    """Extract catalog links from a page."""
    categories = []

    await page.goto(f"{base_url}{url_path}", wait_until="domcontentloaded", timeout=60000)
    await asyncio.sleep(2)

    links = await page.query_selector_all('a[href*="/catalog/"]')

    seen = set()
    for link in links:
        href = await link.get_attribute('href')
        text = await link.inner_text()

        if not href or '/catalog/' not in href:
            continue

        match = re.search(r'/catalog/(\d+)-([a-z0-9-]+)', href)
        if match:
            catalog_id = int(match.group(1))
            slug = match.group(2)

            if catalog_id not in seen:
                seen.add(catalog_id)
                categories.append({
                    "id": catalog_id,
                    "slug": slug,
                    "name": text.strip(),
                    "url": href
                })

    return categories


async def scrape_deep_categories(market: str = "IT"):
    """Scrape 2 levels deep into category hierarchy."""
    base_urls = {
        "IT": "https://www.vinted.it",
        "FR": "https://www.vinted.fr",
        "DE": "https://www.vinted.de",
    }

    base_url = base_urls.get(market, base_urls["IT"])
    all_categories = []

    # Categories to explore (clothing specifically)
    to_explore = [
        # Women's clothing subcategories
        {"path": "/catalog/4-clothing", "parent": "women"},
        # Men's clothing subcategories
        {"path": "/catalog/2050-clothing", "parent": "men"},
        # Women's shoes
        {"path": "/catalog/16-shoes", "parent": "women"},
        # Men's shoes
        {"path": "/catalog/1231-shoes", "parent": "men"},
        # Women's bags
        {"path": "/catalog/19-bags", "parent": "women"},
        # Women's accessories
        {"path": "/catalog/1187-accessories", "parent": "women"},
        # Men's accessories
        {"path": "/catalog/82-accessories", "parent": "men"},
    ]

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            viewport={"width": 1280, "height": 720}
        )
        page = await context.new_page()

        for item in to_explore:
            print(f"Exploring: {item['path']}...")
            cats = await get_category_links(page, base_url, item['path'])

            for cat in cats:
                cat['parent'] = item['parent']

            all_categories.extend(cats)
            print(f"  Found {len(cats)} subcategories")
            await asyncio.sleep(1)

        await browser.close()

    # Remove duplicates
    seen_ids = set()
    unique = []
    for cat in all_categories:
        if cat['id'] not in seen_ids:
            seen_ids.add(cat['id'])
            unique.append(cat)

    unique.sort(key=lambda x: (x['parent'], x['id']))
    return unique


async def main():
    print("=" * 70)
    print("VINTED CATEGORY SCRAPER - Deep Dive")
    print("=" * 70)

    categories = await scrape_deep_categories("IT")

    print(f"\n{'=' * 70}")
    print(f"Found {len(categories)} categories:\n")

    current_parent = None
    for cat in categories:
        if cat['parent'] != current_parent:
            current_parent = cat['parent']
            print(f"\n  {current_parent.upper()}")
            print("  " + "-" * 60)

        print(f"    {cat['id']:5} | {cat['slug']:<30} | {cat['name']}")

    # Save to JSON
    output_path = "categories.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(categories, f, indent=2, ensure_ascii=False)
    print(f"\n\nSaved to {output_path}")

    # Generate Python dict format for spider
    print("\n\n" + "=" * 70)
    print("PYTHON DICT FORMAT (copy to spider):")
    print("=" * 70)
    print("\nCATALOG_IDS = {")
    for cat in categories:
        key = f"{cat['parent']}/{cat['slug']}"
        print(f'    "{key}": {cat["id"]},')
    print("}")


if __name__ == "__main__":
    asyncio.run(main())
