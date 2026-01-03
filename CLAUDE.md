# Vinted Analytics - AI Assistant Guide

## Available Commands

**Use these commands first!** They contain project-specific patterns and step-by-step guides.

| Command | When to Use |
|---------|-------------|
| `/project:dev` | Starting local development |
| `/project:add-endpoint` | Adding new API endpoint (full workflow) |
| `/project:add-component` | Adding new React component/tab |
| `/project:add-scrape-category` | Adding category to GitHub Actions scraper |
| `/project:scrape` | Running scraper manually for testing |
| `/project:query` | Running ad-hoc database queries |
| `/project:db-stats` | Checking database health and counts |
| `/project:test` | Running tests, linting, type checks |
| `/project:deploy` | Deploying API, Web, or Scraper |
| `/project:fix-timeout` | Debugging Supabase timeout/500 errors |
| `/project:fix-actions` | Debugging failed GitHub Actions |
| `/project:clear-cache` | Clearing Python/Vite/browser caches |

**Examples:**
```
/project:add-endpoint price history tracking
/project:scrape IT women/bags 3
/project:fix-actions cleanup job timeout
/project:query top 10 sellers in France
```

---

## Project Overview
Cross-market analytics platform for Vinted sellers. Tracks items across 9 European markets (IT, FR, DE, ES, NL, PL, BE, AT, PT), analyzes pricing, and provides selling recommendations.

## Tech Stack

### API (`/api`)
- **Framework**: FastAPI (Python 3.11+)
- **Database**: Supabase (PostgreSQL)
- **Key files**:
  - `src/main.py` - App entry, CORS config
  - `src/routes/api.py` - All endpoints
  - `src/services/analytics.py` - Business logic (largest file)
  - `src/models/schemas.py` - Pydantic response models
  - `src/db.py` - Supabase client

### Web (`/web`)
- **Framework**: React 18 + TypeScript + Vite
- **Styling**: Plain CSS (no framework)
- **Key files**:
  - `src/App.tsx` - Main app, all tabs, state management
  - `src/api/client.ts` - API client, types, caching
  - `src/components/` - Feature components
  - `src/App.css` - All styles

### Scraper (`/scraper`)
- **Runtime**: Python async
- **Schedule**: GitHub Actions cron jobs
- **Key files**:
  - `src/main.py` - Entry point, CLI args
  - `src/scraper/vinted.py` - Scraping logic
  - `src/storage/database.py` - DB operations (SQLite + Supabase)
  - `src/jobs/cleanup.py` - Daily maintenance job

## Database Schema

```sql
-- Main items table
items (
  id, vinted_id (unique), title, price, currency, brand, size,
  url, image_url, favorites, market, category,
  status ('active'|'sold'), first_seen, last_seen, sold_at
)

-- Price tracking
price_history (id, vinted_id, price, recorded_at)

-- Daily aggregations
stats_daily (date, market, category, brand, active_count, sold_count, avg_price, ...)
```

## Common Patterns

### Supabase Pagination (required for large queries)
```python
all_items = []
page_size = 1000
offset = 0
while True:
    result = query.range(offset, offset + page_size - 1).execute()
    if not result.data:
        break
    all_items.extend(result.data)
    offset += page_size
    if offset >= 50000:  # Safety limit
        break
```

### Retry Logic (for Supabase timeouts)
```python
def retry_supabase(func, max_retries=3, delay=2):
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(delay * (2 ** attempt))
            else:
                raise
```

### Currency Conversion (Poland uses PLN)
```python
CURRENCY_RATES = {"PL": 4.3}  # 1 EUR = 4.3 PLN
def to_eur(price, market):
    return price / CURRENCY_RATES.get(market, 1)
```

## Known Issues & Solutions

### 1. Pydantic Schema Duplication
**Problem**: `schemas.py` had duplicate class definitions; Python uses the last one.
**Solution**: Keep only one definition of each class. Check for duplicates when editing.

### 2. Supabase Timeouts
**Problem**: Free tier times out on large queries (>8 seconds).
**Solution**: Use pagination + retry logic. Never fetch all items in one query. See `/project:fix-timeout`.

### 3. sold_at Accuracy
**Problem**: `sold_at` = when scraper noticed item gone, not actual sale time.
**Impact**: Timing insights need weeks of data to be accurate.

### 4. API Changes Not Reflecting
**Problem**: Python caches bytecode in `__pycache__`.
**Solution**: Run `/project:clear-cache` or `find . -name __pycache__ -exec rm -rf {} +`

## API Endpoints

| Endpoint | Purpose |
|----------|---------|
| GET /api/lookup | Search items by brand/category/size/market |
| GET /api/trends | Trending items (by favorites) |
| GET /api/sold | Recently sold items |
| GET /api/market-profitability | Where to sell analysis + price suggestions |
| GET /api/timing-insights | Best day to sell, trending categories |
| GET /api/arbitrage | Cross-market price gaps |
| GET /api/categories | Available categories |
| GET /api/hot-categories | Hottest category per market |

## Running Locally

Use `/project:dev` or manually:

```bash
# API
cd api
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Add SUPABASE_URL, SUPABASE_KEY
uvicorn src.main:app --reload

# Web
cd web
npm install
npm run dev

# Scraper (manual run)
cd scraper
python -m src.main --market IT --category women/dresses --pages 2
```

## Environment Variables

```
# API & Scraper
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJ...
USE_SUPABASE=true

# Web
VITE_API_URL=http://localhost:8000
```

## Adding New Features

Use `/project:add-endpoint` and `/project:add-component` for guided workflows, or follow manually:

### New API Endpoint
1. Add function in `api/src/services/analytics.py`
2. Add Pydantic models in `api/src/models/schemas.py`
3. Add route in `api/src/routes/api.py`
4. Add TypeScript types in `web/src/api/client.ts`
5. Add API function in `client.ts`
6. Build component in `web/src/components/`
7. Add tab/route in `web/src/App.tsx`
8. Add styles in `web/src/App.css`

### New Scraper Category
Use `/project:add-scrape-category` or edit `.github/workflows/scrape-*.yml` directly.

## Code Style

- **Python**: No type hints required but appreciated. Use f-strings.
- **TypeScript**: Strict types. Interfaces over types.
- **CSS**: BEM-ish naming (`.component-element`). No nesting.
- **Commits**: Conventional commits preferred (`feat:`, `fix:`, `chore:`)

## Testing

Use `/project:test` or:

```bash
# API
cd api && pytest

# Scraper
cd scraper && pytest
```

## Deployment

Use `/project:deploy` for full guide, or:

- **API**: Railway/Render (set env vars)
- **Web**: Vercel/Netlify (set VITE_API_URL)
- **Scraper**: GitHub Actions (secrets in repo settings)
