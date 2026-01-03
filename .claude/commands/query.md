Run ad-hoc database queries for analysis.

User wants: $ARGUMENTS

Quick query template:
```python
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv('api/.env')
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

# Example queries:

# Top 10 most favorited items
result = supabase.table("items").select("title, brand, price, favorites, market").order("favorites", desc=True).limit(10).execute()

# Average price by market for a category
result = supabase.table("items").select("market, price").eq("category", "women/dresses").eq("status", "active").execute()

# Recently sold items
result = supabase.table("items").select("*").eq("status", "sold").order("sold_at", desc=True).limit(20).execute()

# Items in price range
result = supabase.table("items").select("*").gte("price", 50).lte("price", 100).execute()

# Count by status
result = supabase.table("items").select("status", count="exact").execute()

for item in result.data:
    print(item)
```

Common filters:
- `.eq("market", "IT")` - specific market
- `.eq("category", "women/dresses")` - specific category
- `.ilike("brand", "%Nike%")` - brand contains
- `.gte("price", 50)` - price >= 50
- `.eq("status", "sold")` - sold items only
- `.order("favorites", desc=True)` - sort by favorites
- `.limit(100)` - limit results
