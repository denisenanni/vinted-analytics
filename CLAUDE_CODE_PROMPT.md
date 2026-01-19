# Vinted Analytics - Claude Code Handoff

## Project Overview

Read the README.md first — it has the full context, features, data model, and architecture.

This is a personal analytics tool for Vinted sellers. Core use case: "I have this item, what's it worth, where should I list it, when should I boost it?"

## Tech Stack

- **Scraper**: Python + Playwright
- **Database**: PostgreSQL (Supabase) — start with SQLite locally
- **API**: Python + FastAPI
- **Frontend**: React + TypeScript + Vite (use yarn)
- **Hosting**: Railway (API), Vercel (frontend), GitHub Actions (cron)

## Phase 1: Scraper MVP ✅ COMPLETE

Phase 1 is done. The scraper works for IT market and women/dresses category.

Current state:
- CLI accepts `--market`, `--category`, `--pages` parameters
- Scrapes vinted.it successfully
- Stores in local SQLite
- Handles pagination and rate limiting

## Phase 2: Expand Scraper (after Phase 1 works)

### 2.1 Add all markets

Add missing markets to `BASE_URLS` and CLI choices:

```python
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
```

Update `main.py` argparse choices to include all markets.

### 2.2 Category mapping per market

The category catalog IDs and URL paths may differ per market. Test if the current path works on other markets — if not, create a nested mapping:

```python
CATEGORIES = {
    "IT": {
        "women/dresses": "/vestiti?catalog[]=1904",
        "women/shirts": "/vestiti?catalog[]=...",
        "men/jeans": "/abbigliamento-uomo?catalog[]=...",
    },
    "FR": {
        "women/dresses": "/vetements?catalog[]=1904",
        # ...
    },
    "DE": {
        "women/dresses": "/kleidung?catalog[]=1904",
        # ...
    },
    # ... other markets
}
```

To find correct catalog IDs:
1. Go to each vinted.XX site
2. Navigate to the category manually
3. Copy the URL path and catalog parameter

Priority categories to add:
- women/dresses
- women/shirts
- women/jeans
- men/shirts
- men/jeans
- men/sneakers

### 2.3 Sold detection

Items that disappear = likely sold. Implementation:

1. On each scrape, record `last_seen` timestamp
2. Add a periodic job that checks: if `last_seen` < 24h ago and item not in latest scrape → mark `status = 'sold'`
3. Store `sold_at` timestamp when detected

```python
# In database.py
async def mark_sold_items(market: str, category: str, active_vinted_ids: List[str]):
    """Mark items as sold if they disappeared from results"""
    # Items we have that weren't in this scrape and were last seen > 24h ago
    # → update status to 'sold'
```

### 2.4 Price history tracking

When an item's price changes, log it:

```python
# New table: price_history
# item_id, price, recorded_at

async def save_items(items: List[VintedItem]):
    for item in items:
        existing = await get_item_by_vinted_id(item.vinted_id)
        if existing:
            # Update last_seen
            await update_last_seen(item.vinted_id)
            # If price changed, log to price_history
            if existing.price != item.price:
                await log_price_change(item.vinted_id, item.price)
        else:
            # Insert new item
            await insert_item(item)
```

### 2.5 Migrate to Supabase

1. Create Supabase project (free tier)
2. Create tables matching the data model in README.md
3. Replace SQLite connection with Supabase client:

```python
from supabase import create_client

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

async def save_item(item: VintedItem):
    supabase.table('items').upsert(item.dict()).execute()
```

4. Update environment variables

### 2.6 Testing

Add tests to verify scraper works correctly across markets and categories.

```
scraper/
├── tests/
│   ├── __init__.py
│   ├── test_spider.py        # Spider unit tests
│   ├── test_database.py      # Database operations
│   └── test_integration.py   # End-to-end scraping tests
```

**Unit tests (`test_spider.py`):**
- `test_parse_price()` — various price formats (€25,00 / 25.00 € / etc.)
- `test_extract_vinted_id()` — from different URL formats
- `test_base_url_mapping()` — correct URL for each market

**Database tests (`test_database.py`):**
- `test_save_new_item()` — item inserted correctly
- `test_update_last_seen()` — existing item updated
- `test_mark_sold()` — sold detection works
- `test_price_history()` — price change logged

**Integration tests (`test_integration.py`):**
- `test_scrape_single_page()` — returns valid items
- `test_scrape_multiple_markets()` — IT, FR, DE all work
- `test_category_paths()` — each category resolves correctly

Use `pytest` + `pytest-asyncio` for async tests.

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_spider.py -v
```

### 2.7 GitHub Actions Workflows

Create CI/CD pipelines for testing and scheduled scraping.

```
.github/
└── workflows/
    ├── test.yml      # Run tests on push/PR
    └── scrape.yml    # Scheduled scraping cron
```

**`.github/workflows/test.yml`** — Run tests on every push and PR:

```yaml
name: Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: self-hosted
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        working-directory: ./scraper
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest pytest-asyncio
          playwright install chromium
      
      - name: Run tests
        working-directory: ./scraper
        run: pytest tests/ -v
```

**`.github/workflows/scrape.yml`** — Scheduled scraping every 12 hours:

```yaml
name: Scheduled Scrape

on:
  schedule:
    - cron: '0 */12 * * *'  # Every 12 hours
  workflow_dispatch:  # Manual trigger

jobs:
  scrape:
    runs-on: self-hosted
    
    strategy:
      matrix:
        market: [IT, FR, DE, ES, NL, PL, BE, AT, PT]
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        working-directory: ./scraper
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          playwright install chromium
      
      - name: Run scraper for ${{ matrix.market }}
        working-directory: ./scraper
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_KEY: ${{ secrets.SUPABASE_KEY }}
        run: |
          python -m src.main --market ${{ matrix.market }} --category women/dresses --pages 10
          python -m src.main --market ${{ matrix.market }} --category women/shirts --pages 10
          python -m src.main --market ${{ matrix.market }} --category men/jeans --pages 10
```

**Required GitHub Secrets:**
- `DATABASE_URL` — Supabase connection string
- `SUPABASE_URL` — Supabase project URL
- `SUPABASE_KEY` — Supabase anon/service key

**Notes:**
- Matrix strategy runs all 9 markets in parallel
- `workflow_dispatch` allows manual trigger for testing
- Add more categories to the scrape commands as needed
- Consider adding error notifications (Slack/email) on failure

## Phase 3: API

FastAPI backend with endpoints defined in README:
- `/api/lookup` — core use case
- `/api/boost` — boost timing advice
- `/api/compare` — cross-market comparison
- `/api/sold` — sold history
- `/api/trends` — trending data

## Phase 4: Frontend

React + TypeScript dashboard:
- Search form (brand, category, size, condition)
- Paste Vinted URL option
- Results display with price range, time-to-sell, best market
- Charts for trends

---

## Current Task: Phase 2

Start with 2.1 and 2.2:
1. Add all markets to `BASE_URLS` and CLI choices
2. Test if current category path works on FR and DE
3. If not, implement per-market category mapping
4. Add 2-3 more categories (women/shirts, men/jeans)

Then move to 2.3 (sold detection) and 2.4 (price history).

Save 2.5 (Supabase migration) for after the scraper is fully working with all markets.

Add 2.6 (testing) — pytest tests for spider, database, and integration.

Finish with 2.7 (GitHub Actions) — test.yml and scrape.yml workflows.