# Vinted Analytics

Cross-market analytics tool for Vinted — track trends, pricing, and selling velocity across European markets.

## Problem

You have clothes to sell. But you're guessing:
- What price should I set?
- Is this item even in demand right now?
- Should I list in my local market or cross-border?
- How long will it realistically take to sell?
- Is it worth listing at all, or should I donate it?

Existing tools are either basic, expensive, or risky browser extensions.

## Solution

A personal analytics tool that answers: **"I have X item — what's the market like for it?"**

- See what similar items sold for (not just listed prices)
- Check demand across EU markets
- Get realistic time-to-sell estimates
- Make informed pricing decisions

Secondary use case: spot arbitrage/flipping opportunities if you want to go that route.

---

## Features

### MVP (Personal Use)

- [x] **Multi-market scraping** — IT, FR, DE, ES, NL, PL, BE, AT, PT to start
- [x] **Item lookup** — Two ways to input:
  - [x] Manual form: select brand, category, size, condition
  - [ ] Paste Vinted URL: auto-extracts item details
- [x] **Sold price history** — What similar items actually sold for (not just listings)
- [x] **Time-to-sell estimates** — Realistic expectations by brand/category/market
- [x] **Market comparison** — Same item type: which country has highest demand?
- [x] **Pricing guidance** — Suggested price range based on sold data
- [x] **Basic dashboard** — Search, filter, visualize

### V2 (Expanded)

- [ ] **My items list** — Save items you want to track (local storage, no signin)
- [ ] **Boost optimization** — When, what, and where to boost:
  - Peak activity hours by market (when are buyers online?)
  - Best days of the week for your category
  - Which items benefit most from boosting (high demand, competitive price)
  - **Which market to boost in** — "Boost this in FR not IT, 3x more demand"
  - ROI estimate: "This item is worth boosting" vs "Save your money"
- [ ] **"Worth listing?" score** — Based on demand, avg price, time-to-sell
- [ ] **Best market suggestion** — "List this in FR, sells 2x faster than IT"
- [ ] **Seasonal trends** — When to list certain items
- [ ] **Brand performance** — Which brands move fast vs sit forever
- [ ] **Alerts** — "Items like yours are selling well right now"

### V3 (Monetizable)

- [ ] **User accounts** — Signin to sync saved items across devices
- [ ] **My wardrobe** — Import all your Vinted listings automatically
- [ ] **Arbitrage finder** — For users who want to flip
- [ ] **Listing optimizer** — "Your price is 15% above market"
- [ ] **Bulk analysis** — Upload your closet, get recommendations
- [ ] **API access** — For power sellers / other tools

---

## Tech Stack

| Layer | Technology | Notes |
|-------|------------|-------|
| Scraper | Python + Playwright | Handles JS rendering, multi-country |
| Database | PostgreSQL (Supabase) | Free tier, managed |
| Backend | Python + FastAPI | REST API, auth later |
| Frontend | React + TypeScript | Vite, Recharts for viz |
| Hosting | Railway (API), Vercel (frontend) | Free tiers |
| Jobs | GitHub Actions | Scheduled scraping |

---

## Data Model

### `items`
| Field | Type | Description |
|-------|------|-------------|
| id | bigserial | Primary key |
| vinted_id | text | Vinted's item ID (unique) |
| title | text | Listing title |
| price | decimal(10,2) | Current price |
| currency | text | EUR (default) |
| brand | text | Brand name |
| size | text | Size if applicable |
| url | text | Full item URL |
| image_url | text | Primary image |
| favorites | int | Favorite count |
| market | text | Market code (IT, FR, etc.) |
| category | text | Category path (women/dresses) |
| scraped_at | timestamptz | When this data was scraped |
| first_seen | timestamptz | When we first saw this item |
| last_seen | timestamptz | Last time it appeared |
| status | text | active, sold, removed |
| sold_at | timestamptz | When marked as sold |

### `price_history`
| Field | Type | Description |
|-------|------|-------------|
| id | bigserial | Primary key |
| vinted_id | text | FK to items.vinted_id |
| price | decimal(10,2) | Price at this point |
| recorded_at | timestamptz | When recorded |

### `stats_daily` (aggregated metrics)
| Field | Type | Description |
|-------|------|-------------|
| id | bigserial | Primary key |
| date | date | Stats date |
| market | text | Market code |
| category | text | Category path |
| brand | text | Brand (nullable for category-wide stats) |
| active_count | int | Number of active listings |
| sold_count | int | Items sold that day |
| avg_price | decimal(10,2) | Average price |
| min_price | decimal(10,2) | Minimum price |
| max_price | decimal(10,2) | Maximum price |
| avg_time_to_sell_days | decimal(5,1) | Average days to sell |

**Unique constraint:** `(date, market, category, brand)`

### Indexes
- `idx_items_vinted_id` — fast lookup by Vinted ID
- `idx_items_market_category` — filter by market and category
- `idx_items_status` — filter active/sold items
- `idx_items_last_seen` — cleanup queries
- `idx_price_history_vinted_id` — price history lookups
- `idx_stats_daily_lookup` — stats queries by date/market/category

---

## Data Retention Policy

To keep the database lean and ensure data freshness:

| Data | Retention | Action |
|------|-----------|--------|
| Active items not seen in 7 days | Stale | Delete |
| Sold items older than 90 days | Expired | Delete |
| Price history older than 90 days | Expired | Delete |
| Orphaned price history | Invalid | Delete |
| Daily aggregated stats | Forever | Keep |

### Cleanup SQL (runs daily)

```sql
-- 1. First, aggregate stats BEFORE cleanup
INSERT INTO stats_daily (date, market, category, brand, active_count, sold_count, avg_price, min_price, max_price, avg_time_to_sell_days)
SELECT 
    CURRENT_DATE,
    market,
    category,
    brand,
    COUNT(*) FILTER (WHERE status = 'active') as active_count,
    COUNT(*) FILTER (WHERE status = 'sold' AND sold_at >= CURRENT_DATE - INTERVAL '1 day') as sold_count,
    AVG(price) as avg_price,
    MIN(price) as min_price,
    MAX(price) as max_price,
    AVG(EXTRACT(EPOCH FROM (sold_at - first_seen)) / 86400) FILTER (WHERE status = 'sold') as avg_time_to_sell_days
FROM items
GROUP BY market, category, brand
ON CONFLICT (date, market, category, brand) DO UPDATE SET
    active_count = EXCLUDED.active_count,
    sold_count = EXCLUDED.sold_count,
    avg_price = EXCLUDED.avg_price,
    min_price = EXCLUDED.min_price,
    max_price = EXCLUDED.max_price,
    avg_time_to_sell_days = EXCLUDED.avg_time_to_sell_days;

-- 2. Delete stale active items (not seen in 7 days)
DELETE FROM items 
WHERE status = 'active' 
AND last_seen < NOW() - INTERVAL '7 days';

-- 3. Delete old sold items (older than 90 days)
DELETE FROM items 
WHERE status = 'sold' 
AND sold_at < NOW() - INTERVAL '90 days';

-- 4. Delete old price history
DELETE FROM price_history 
WHERE recorded_at < NOW() - INTERVAL '90 days';

-- 5. Delete orphaned price history (items no longer exist)
DELETE FROM price_history 
WHERE vinted_id NOT IN (SELECT vinted_id FROM items);
```

---

## API Endpoints

### Item Lookup (core use case)
```
GET /api/lookup
  ?brand=zara
  &category=women/dresses
  &size=M
  &condition=good
```
Returns: avg sold price, price range, avg time-to-sell, demand score, best markets

### Boost Advice
```
GET /api/boost
  ?brand=zara
  &category=women/dresses
  &size=M
  &price=25
```
Returns: 
- best_market: "FR" 
- best_days: ["saturday", "sunday"]
- best_hours: ["10:00-12:00", "20:00-22:00"]
- worth_boosting: true/false
- reason: "High demand, your price is competitive"

### Market Comparison
```
GET /api/compare
  ?brand=nike
  &category=men/sneakers
  &markets=IT,FR,DE,ES
```
Returns: price and velocity by market

### Sold History
```
GET /api/sold
  ?brand=levis
  &category=men/jeans
  &size=32
  &period=30d
  &market=IT
```
Returns: recent sold items with prices and time-on-market

### Trends
```
GET /api/trends
  ?market=IT
  &category=women/shirts
  &period=7d|30d|90d
```
Returns: trending brands, avg prices, volume changes

### Items (raw data)
```
GET /api/items
  ?market=IT
  &brand=zara
  &status=active|sold
  &sort=price|recent|velocity
  &limit=50
```

---

## Scraping Strategy

### Target Categories

Using universal catalog IDs that work across all markets. 80+ categories available:

**Women's Clothing**
- `women/clothing` (all), `women/dresses`, `women/tops-and-t-shirts`, `women/jumpers-and-sweaters`, `women/jeans`, `women/trousers-and-leggings`, `women/skirts`, `women/shorts-and-cropped-trousers`, `women/outerwear`, `women/suits-and-blazers`, `women/jumpsuits-and-playsuits`, `women/activewear`, `women/swimwear`, `women/lingerie-and-nightwear`, `women/maternity-clothes`, `women/costumes-and-special-outfits`

**Women's Shoes**
- `women/shoes` (all), `women/boots`, `women/heels`, `women/trainers`, `women/sandals`, `women/ballerinas`, `women/slippers`, `women/sports-shoes`, `women/flip-flops-and-slides`, `women/espadrilles`, `women/boat-shoes-loafers-and-moccasins`, `women/clogs-and-mules`, `women/mary-janes-and-t-bar-shoes`, `women/lace-up-shoes`

**Women's Bags**
- `women/bags` (all), `women/handbags`, `women/backpacks`, `women/shoulder-bags`, `women/tote-bags`, `women/clutches`, `women/wallets-and-purses`, `women/bucket-bags`, `women/hobo-bags`, `women/beach-bags`, `women/gym-bags`, `women/bum-bags`, `women/satchels-and-messenger-bags`, `women/makeup-bags`, `women/luggage-and-suitcases`

**Women's Accessories**
- `women/jewellery`, `women/watches`, `women/sunglasses`, `women/belts`, `women/hats-and-caps`, `women/scarves-and-shawls`, `women/gloves`, `women/hair-accessories`, `women/umbrellas`, `women/keyrings`

**Men's Clothing**
- `men/clothing` (all), `men/tops-and-t-shirts`, `men/jumpers-and-sweaters`, `men/jeans`, `men/trousers`, `men/shorts`, `men/outerwear`, `men/suits-and-blazers`, `men/activewear`, `men/swimwear`, `men/sleepwear`, `men/socks-and-underwear`, `men/costumes-and-special-outfits`

**Men's Shoes**
- `men/shoes` (all), `men/boots`, `men/trainers`, `men/formal-shoes`, `men/sandals`, `men/sports-shoes`, `men/slippers`, `men/flip-flops-and-slides`, `men/boat-shoes-loafers-and-moccasins`, `men/espadrilles`, `men/clogs-and-mules`

**Men's Accessories**
- `men/bags-and-backpacks`, `men/jewellery`, `men/watches`, `men/sunglasses`, `men/belts`, `men/hats-and-caps`, `men/scarves-and-shawls`, `men/gloves`, `men/ties-and-bow-ties`, `men/braces-and-suspenders`

### URL Construction

Catalog IDs are universal across all markets. URL format:
```
https://www.vinted.{market}/catalog/{catalog_id}-{slug}?page={page}
```

Example: `https://www.vinted.it/catalog/10-dresses?page=1`

### Frequency
- Active listings: every 12h
- Price changes: captured in price_history on each scrape

### Sold Detection (Hybrid Approach)

**Phase 1 — Disappearance inference:**
- Track all items by vinted_id
- If item missing for 2 consecutive scrapes (24h) → mark as `sold`
- Simple, covers ~80% of cases
- Edge cases: deleted or removed items count as "sold" (acceptable noise at scale)

**Phase 2 — Seller profile correlation (V2):**
- Scrape seller profiles periodically
- Track `sold_count` delta over time
- Cross-reference with disappeared items for accuracy
- Helps distinguish sold vs deleted

### Rate Limiting
- Random delays (2-5s between requests)
- Rotate user agents
- Respect robots.txt where reasonable
- Start small: 1 category, then expand markets gradually
- 9 markets = stagger scraping to avoid spikes

### What to Scrape
1. **Category pages** — listing cards via catalog URLs
2. **Individual item pages** — full details, view/fav counts, seller info
3. **Seller profiles (V2)** — sold count, rating, total listings

---

## Project Structure

```
vinted-analytics/
├── scraper/
│   ├── src/
│   │   ├── spiders/          # Market-specific scrapers
│   │   ├── models/           # Data models
│   │   └── utils/            # Helpers, rate limiting
│   ├── requirements.txt
│   └── README.md
├── api/
│   ├── src/
│   │   ├── routes/           # API endpoints
│   │   ├── services/         # Business logic
│   │   ├── models/           # SQLAlchemy models
│   │   └── db/               # Database connection
│   ├── requirements.txt
│   └── README.md
├── web/
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── pages/            # Dashboard pages
│   │   ├── hooks/            # Data fetching
│   │   └── utils/            # Helpers
│   ├── package.json
│   └── README.md
├── .github/
│   └── workflows/
│       └── scrape.yml        # Scheduled scraping
└── README.md
```

---

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL (or Supabase account)

### Setup

```bash
# Clone
git clone https://github.com/yourusername/vinted-analytics.git
cd vinted-analytics

# Scraper
cd scraper
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# API
cd ../api
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Web
cd ../web
yarn install
```

### Environment Variables

```bash
# .env
DATABASE_URL=postgresql://...
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=xxx
```

### Running

```bash
# Scraper (manual run)
cd scraper
python -m src.main --market IT --category women/dresses

# API
cd api
uvicorn src.main:app --reload

# Web
cd web
yarn dev
```

---

## Roadmap

- [x] **Phase 1**: Scraper MVP — single market, single category, SQLite storage
- [x] **Phase 2**: Expand scraper — all 9 markets, 80+ categories, Supabase, sold detection, price history, tests, GitHub Actions
- [x] **Phase 3**: API — FastAPI backend with lookup, boost, compare, sold, trends endpoints
- [x] **Phase 4**: Frontend — React dashboard with search, results, charts
- [ ] **Phase 5**: Polish & deploy — Railway (API), Vercel (frontend), production testing
- [ ] **Phase 6**: V2 features — saved items, boost optimization, alerts

---

## Legal Considerations

- Scraping for personal/research use
- No reselling of raw data
- Respect rate limits
- No authentication bypass
- Consider Vinted ToS if productizing

---

## License

MIT (for now)