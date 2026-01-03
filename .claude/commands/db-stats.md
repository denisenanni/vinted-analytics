Check database statistics and data consistency.

## Quick Check via API
```bash
curl http://localhost:8000/api/db-stats | jq
```

This returns:
```json
{
  "total_items": 12500,
  "by_market": {
    "IT": {"total": 3000, "active": 2500, "sold": 500, "with_favorites": 1200},
    "FR": {"total": 2800, "active": 2300, "sold": 500, "with_favorites": 900},
    ...
  },
  "recent_with_favorites_7d": {
    "IT": 800,
    "FR": 600,
    ...
  },
  "markets_scraped": ["IT", "FR", "DE", ...]
}
```

## Interpreting Results

**If a market shows 0 in Trends tab:**

1. Check `by_market.{MARKET}` exists
   - Missing = scraper not running for that market
   
2. Check `by_market.{MARKET}.with_favorites`
   - 0 = scraper working but items have no favorites
   
3. Check `recent_with_favorites_7d.{MARKET}`
   - 0 = items exist but are stale (last_seen > 7 days ago)
   - This is what Trends uses!

**Data consistency checks:**

- `recent_with_favorites_7d` should match what Trends tab shows
- `with_favorites` should be >= `recent_with_favorites_7d`
- All 9 markets should be present: IT, FR, DE, ES, NL, PL, BE, AT, PT

## Manual Query (if API not running)
```python
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv('api/.env')

supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)

# Count by market
result = supabase.table("items").select("market", count="exact").execute()
print(f"Total items: {result.count}")

# Check specific market
fr_items = supabase.table("items").select("id", count="exact").eq("market", "FR").execute()
print(f"France items: {fr_items.count}")

# Check France with favorites
fr_favs = supabase.table("items").select("id", count="exact").eq("market", "FR").gt("favorites", 0).execute()
print(f"France with favorites: {fr_favs.count}")
```
