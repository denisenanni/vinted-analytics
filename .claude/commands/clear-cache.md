Clear all caches when changes aren't reflecting.

Problem: $ARGUMENTS

## Python API Cache
```bash
# Remove bytecode cache
find api -name __pycache__ -exec rm -rf {} + 2>/dev/null
find scraper -name __pycache__ -exec rm -rf {} + 2>/dev/null

# Restart uvicorn (it should auto-reload, but sometimes doesn't)
# Kill and restart the server
```

## In-memory caches (api/src/services/analytics.py)
- `_hot_categories_cache` - 5 min TTL
- `_market_stats_cache` - 3 min TTL

To force refresh: restart the API server.

## Frontend cache (web/src/api/client.ts)
- Client-side cache with 2 min TTL
- Hard refresh: Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows)
- Or clear in devtools: Application > Storage > Clear site data

## Vite cache
```bash
cd web
rm -rf node_modules/.vite
npm run dev
```

## Browser cache
- Open DevTools (F12)
- Right-click refresh button → "Empty Cache and Hard Reload"
