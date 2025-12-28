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

## Phase 1: Scraper MVP

Start here. Build a scraper that:

1. Scrapes `vinted.it` (Italy market first)
2. Targets one category: `women/dresses`
3. Extracts from search results:
   - vinted_id
   - title
   - brand
   - size
   - price
   - condition
   - url
   - favorites count (if visible)
4. Stores in local SQLite for now (we'll migrate to Supabase later)
5. Handles pagination (scrape multiple pages)
6. Respects rate limits: random delays 2-5s between requests

### Scraper structure

```
scraper/
├── src/
│   ├── main.py              # Entry point, CLI
│   ├── spiders/
│   │   └── vinted.py        # Main scraper logic
│   ├── models/
│   │   └── item.py          # Pydantic models
│   ├── db/
│   │   └── database.py      # SQLite connection
│   └── utils/
│       ├── rate_limit.py    # Delay helpers
│       └── user_agents.py   # UA rotation
├── requirements.txt
└── README.md
```

### CLI usage goal

```bash
python -m src.main --market IT --category women/dresses --pages 5
```

### Key considerations

- Vinted uses JavaScript rendering — Playwright is needed, not just requests
- Inspect vinted.it to understand the DOM structure for selectors
- Items might also be fetchable via internal API (check network tab) — if so, prefer API over DOM scraping
- Store `first_seen` timestamp on each item
- Handle duplicates: if item already exists (by vinted_id), update `last_seen`

## Phase 2: Expand Scraper (after Phase 1 works)

- Add more markets: FR, DE, ES, NL, PL, BE, AT, PT
- Add more categories
- Implement sold detection (item disappears = mark as sold)
- Add price_history tracking (new price → new record)
- Move from SQLite to Supabase

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

## First Task

Set up the scraper project:
1. Create the folder structure
2. Set up Python environment with requirements.txt (playwright, pydantic, sqlite, etc.)
3. Implement basic spider for vinted.it women/dresses
4. Store results in SQLite
5. Test with 2-3 pages

Don't build everything at once — get Phase 1 working first, then we iterate.
