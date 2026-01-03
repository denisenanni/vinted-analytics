Debug and fix a Supabase timeout or 500 error.

Context from user: $ARGUMENTS

Common causes and fixes:

1. **Query too large** - Add pagination:
```python
all_items = []
page_size = 500  # Smaller for problematic queries
offset = 0
while True:
    result = query.range(offset, offset + page_size - 1).execute()
    if not result.data:
        break
    all_items.extend(result.data)
    offset += page_size
    if offset >= 10000:
        break
```

2. **No retry logic** - Wrap in retry:
```python
result = retry_supabase(
    lambda: supabase.table("items").select("id").eq("status", "active").execute()
)
```

3. **Selecting too many columns** - Only select what you need:
```python
# Bad: .select("*")
# Good: .select("id, price, market")
```

4. **Missing index** - Check if filtering on indexed columns (vinted_id, market, category, status)

5. **Cloudflare 500** - Usually transient, retry logic handles this

Check the specific function that's failing and apply the appropriate fix.
