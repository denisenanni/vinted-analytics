# Vinted Analytics - Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              GitHub Actions                                  │
│                           (Scheduled Cron Jobs)                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                                SCRAPER                                       │
│                          (Python + Playwright)                              │
│                                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  vinted.it  │  │  vinted.fr  │  │  vinted.de  │  │    ...      │        │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘        │
│         │               │               │               │                   │
│         └───────────────┴───────────────┴───────────────┘                   │
│                                 │                                           │
│                                 ▼                                           │
│                        ┌───────────────┐                                    │
│                        │  Item Parser  │                                    │
│                        └───────────────┘                                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DATABASE                                        │
│                        (PostgreSQL / Supabase)                              │
│                                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐  ┌──────────────────┐        │
│  │ markets  │  │  items   │  │ price_history│  │  market_activity │        │
│  └──────────┘  └──────────┘  └──────────────┘  └──────────────────┘        │
│                    │                                                        │
│                    │  ┌──────────┐  ┌──────────┐                           │
│                    └─▶│snapshots │  │ searches │                           │
│                       └──────────┘  └──────────┘                           │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                                 API                                          │
│                         (Python + FastAPI)                                  │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                           Endpoints                                  │   │
│  │                                                                      │   │
│  │  /api/lookup    /api/boost    /api/compare   /api/sold   /api/trends│   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                               FRONTEND                                       │
│                        (React + TypeScript)                                 │
│                                                                             │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐                   │
│  │  Item Lookup  │  │ Boost Advisor │  │    Trends     │                   │
│  │     Form      │  │   Dashboard   │  │    Charts     │                   │
│  └───────────────┘  └───────────────┘  └───────────────┘                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Components

### 1. Scraper

**Purpose:** Collect item listings from Vinted markets

**Technology:** Python + Playwright (headless browser)

**Responsibilities:**
- Scrape search result pages across 9 EU markets
- Extract item details (title, brand, price, size, etc.)
- Handle JavaScript-rendered content
- Respect rate limits (2-5s delays)
- Detect sold items (disappearance tracking)
- Track price changes over time

**Flow:**
```
Cron trigger (every 12h)
    │
    ▼
For each market (IT, FR, DE, ES, NL, PL, BE, AT, PT):
    │
    ▼
For each category (women/dresses, men/jeans, etc.):
    │
    ▼
Scrape pages → Parse items → Save to DB
    │
    ▼
Compare with previous scrape → Mark sold items
```

---

### 2. Database

**Purpose:** Store all scraped data and derived analytics

**Technology:** PostgreSQL (Supabase free tier)

**Schema:**

```
markets
├── id (uuid, PK)
├── code (string) — IT, FR, DE, etc.
├── base_url (string)
└── currency (string)

items
├── id (uuid, PK)
├── vinted_id (string, unique per market)
├── market_id (uuid, FK → markets)
├── title (string)
├── brand (string, nullable)
├── category (string)
├── size (string, nullable)
├── condition (string, nullable)
├── url (string)
├── image_url (string, nullable)
├── first_seen (timestamp)
├── last_seen (timestamp)
├── sold_at (timestamp, nullable)
└── status (enum: active, sold, removed)

price_history
├── id (uuid, PK)
├── item_id (uuid, FK → items)
├── price (decimal)
└── recorded_at (timestamp)

snapshots
├── id (uuid, PK)
├── item_id (uuid, FK → items)
├── favorites (int)
├── views (int, nullable)
└── recorded_at (timestamp)

market_activity
├── id (uuid, PK)
├── market_id (uuid, FK → markets)
├── category (string)
├── hour (int) — 0-23
├── day_of_week (int) — 0=Mon, 6=Sun
├── avg_sales (decimal)
├── avg_new_listings (int)
└── recorded_week (date)

searches (V2)
├── id (uuid, PK)
├── market_id (uuid, FK → markets)
├── query (string)
├── results_count (int)
└── recorded_at (timestamp)
```

**Indexes:**
- `items(vinted_id, market_id)` — unique constraint
- `items(brand, category, market_id)` — lookup queries
- `items(status, last_seen)` — sold detection
- `price_history(item_id, recorded_at)` — price trends
- `market_activity(market_id, category, day_of_week, hour)` — boost timing

---

### 3. API

**Purpose:** Serve analytics data to the frontend

**Technology:** Python + FastAPI

**Endpoints:**

| Endpoint | Purpose | Key Query Params |
|----------|---------|------------------|
| `GET /api/lookup` | "What's this item worth?" | brand, category, size, condition |
| `GET /api/boost` | "When/where to boost?" | brand, category, size, price |
| `GET /api/compare` | "Price across markets" | brand, category, markets |
| `GET /api/sold` | "Recent sold items" | brand, category, size, period, market |
| `GET /api/trends` | "What's trending?" | market, category, period |
| `GET /api/items` | "Raw item data" | market, brand, status, sort, limit |

**Response example (`/api/lookup`):**
```json
{
  "query": {
    "brand": "zara",
    "category": "women/dresses",
    "size": "M"
  },
  "results": {
    "avg_sold_price": 18.50,
    "price_range": { "min": 8.00, "max": 35.00 },
    "avg_time_to_sell_days": 12,
    "demand_score": 0.72,
    "total_active": 1423,
    "total_sold_30d": 312,
    "best_markets": [
      { "market": "FR", "avg_price": 22.00, "velocity": 0.85 },
      { "market": "DE", "avg_price": 19.50, "velocity": 0.71 },
      { "market": "IT", "avg_price": 15.00, "velocity": 0.65 }
    ]
  }
}
```

**Response example (`/api/boost`):**
```json
{
  "recommendation": {
    "worth_boosting": true,
    "best_market": "FR",
    "best_days": ["saturday", "sunday"],
    "best_hours": ["10:00-12:00", "20:00-22:00"],
    "reason": "High demand in FR, your price is competitive"
  },
  "market_comparison": [
    { "market": "FR", "demand_score": 0.85, "competition": "medium" },
    { "market": "IT", "demand_score": 0.62, "competition": "high" }
  ]
}
```

---

### 4. Frontend

**Purpose:** User interface for item lookup and analytics

**Technology:** React + TypeScript + Vite

**Pages:**

| Page | Purpose |
|------|---------|
| `/` | Home — item lookup form |
| `/results` | Lookup results with pricing, markets, time-to-sell |
| `/boost` | Boost timing advisor |
| `/trends` | Category trends and charts |
| `/my-items` (V2) | Saved items list (local storage) |

**Key Components:**
```
src/
├── components/
│   ├── LookupForm.tsx        # Brand/category/size selector
│   ├── UrlInput.tsx          # Paste Vinted URL
│   ├── PriceChart.tsx        # Price distribution chart
│   ├── MarketComparison.tsx  # Side-by-side market stats
│   ├── BoostAdvice.tsx       # When/where to boost
│   └── TrendChart.tsx        # Time series trends
├── pages/
│   ├── Home.tsx
│   ├── Results.tsx
│   ├── Boost.tsx
│   └── Trends.tsx
├── hooks/
│   ├── useLookup.ts          # /api/lookup fetcher
│   ├── useBoost.ts           # /api/boost fetcher
│   └── useTrends.ts          # /api/trends fetcher
└── utils/
    ├── api.ts                # API client
    └── formatters.ts         # Price, date formatting
```

---

## Data Flow

### Item Lookup Flow

```
User enters: "Zara dress, size M, good condition"
                    │
                    ▼
            Frontend sends:
        GET /api/lookup?brand=zara&category=women/dresses&size=M
                    │
                    ▼
              API queries:
        - items WHERE brand=zara, category=women/dresses, size=M
        - Aggregate: avg price, time-to-sell, by market
        - Recent sold items for comparison
                    │
                    ▼
            API returns:
        { avg_price, price_range, time_to_sell, best_markets }
                    │
                    ▼
          Frontend displays:
        - Suggested price range
        - "Sells fastest in FR"
        - "Avg 12 days to sell"
```

### Sold Detection Flow

```
Scrape at T=0: Items A, B, C found
                    │
                    ▼
            Save to DB:
        A (last_seen=T0), B (last_seen=T0), C (last_seen=T0)
                    │
                    ▼
Scrape at T=12h: Items A, C found (B missing)
                    │
                    ▼
            Update DB:
        A (last_seen=T1), C (last_seen=T1)
        B unchanged (last_seen still T0)
                    │
                    ▼
Scrape at T=24h: Items A, C found (B still missing)
                    │
                    ▼
          Sold detection job:
        B missing for 24h → mark status='sold', sold_at=T1
```

---

## Infrastructure

### Development
```
Local machine
├── Scraper: python -m src.main
├── API: uvicorn src.main:app --reload
├── Frontend: yarn dev
└── Database: SQLite (local file)
```

### Production
```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  GitHub Actions │     │     Railway     │     │     Vercel      │
│    (Scraper)    │     │      (API)      │     │   (Frontend)    │
│   cron: 0 */12  │     │   FastAPI app   │     │  React static   │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │        Supabase         │
                    │       (PostgreSQL)      │
                    │      Free tier: 500MB   │
                    └─────────────────────────┘
```

### Environment Variables

```bash
# Scraper & API
DATABASE_URL=postgresql://user:pass@host:5432/db
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJxxx...

# Frontend
VITE_API_URL=https://api.vinted-analytics.com
```

---

## Scaling Considerations

### Current (MVP)
- 9 markets × ~5 categories = 45 scrape jobs
- ~12h scrape cycle
- Free tier hosting sufficient

### Future
- **Rate limiting**: May need proxies if blocked
- **Data volume**: ~100k items/month → consider data retention policy
- **API caching**: Redis for frequent queries
- **Job queue**: Celery/RQ if scraping needs parallelization

---

## Security

- No user authentication in MVP
- API is read-only (no user data stored)
- Supabase Row Level Security (RLS) disabled for simplicity
- Rate limit API endpoints to prevent abuse (if public)

---

## Monitoring (Future)

- Scraper success/failure alerts (GitHub Actions)
- API response times (Railway metrics)
- Database size monitoring (Supabase dashboard)
- Error tracking (Sentry, optional)