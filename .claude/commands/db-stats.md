Check database statistics and health.

Run this Python script to get current DB stats:

```python
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv('api/.env')

supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)

# Get counts
items = supabase.table("items").select("status", count="exact", head=True).execute()
active = supabase.table("items").select("id", count="exact", head=True).eq("status", "active").execute()
sold = supabase.table("items").select("id", count="exact", head=True).eq("status", "sold").execute()
price_history = supabase.table("price_history").select("id", count="exact", head=True).execute()

print(f"Total items: {items.count}")
print(f"Active: {active.count}")
print(f"Sold: {sold.count}")
print(f"Price history records: {price_history.count}")

# Items per market
markets = supabase.table("items").select("market").execute()
from collections import Counter
market_counts = Counter(item['market'] for item in markets.data)
print("\nItems per market:")
for market, count in sorted(market_counts.items(), key=lambda x: -x[1]):
    print(f"  {market}: {count}")
```

Run from project root: `python -c "..."`

Or use the API endpoint: `curl http://localhost:8000/api/stats` (if implemented)
