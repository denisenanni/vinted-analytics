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

- [ ] **Multi-market scraping** — IT, FR, DE, ES, NL, PL, BE, AT, PT to start
- [ ] **Item lookup** — Two ways to input:
  - Manual form: select brand, category, size, condition
  - Paste Vinted URL: auto-extracts item details
- [ ] **Sold price history** — What similar items actually sold for (not just listings)
- [ ] **Time-to-sell estimates** — Realistic expectations by brand/category/market
- [ ] **Market comparison** — Same item type: which country has highest demand?
- [ ] **Pricing guidance** — Suggested price range based on sold data
- [ ] **Basic dashboard** — Search, filter, visualize

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

### `markets`
| Field | Type | Description |
|-------|------|-------------|
| id | uuid | Primary key |
| code | string | IT, FR, DE, ES, NL, PL, BE, AT, PT |
| base_url | string | https://www.vinted.it |
| currency | string | EUR (all eurozone) |

### `items`
| Field | Type | Description |
|-------|------|-------------|
| id | uuid | Primary key |
| vinted_id | string | Vinted's item ID |
| market_id | uuid | FK to markets |
| title | string | Listing title |
| brand | string | Brand name |
| category | string | Category path |
| size | string | Size if applicable |
| condition | string | New, Like new, Good, etc. |
| first_seen | timestamp | When we first scraped it |
| last_seen | timestamp | Last time it appeared |
| status | enum | active, sold, removed |

### `price_history`
| Field | Type | Description |
|-------|------|-------------|
| id | uuid | Primary key |
| item_id | uuid | FK to items |
| price | decimal | Price at this point |
| recorded_at | timestamp | When recorded |

### `snapshots`
| Field | Type | Description |
|-------|------|-------------|
| id | uuid | Primary key |
| item_id | uuid | FK to items |
| favorites | int | Favorite count |
| views | int | View count (if available) |
| recorded_at | timestamp | When recorded |

### `market_activity` (for boost timing)
| Field | Type | Description |
|-------|------|-------------|
| id | uuid | Primary key |
| market_id | uuid | FK to markets |
| category | string | Category path |
| hour | int | Hour of day (0-23) |
| day_of_week | int | 0=Monday, 6=Sunday |
| avg_sales | decimal | Avg items sold in this slot |
| avg_new_listings | int | Avg new listings |
| recorded_week | date | Week this data covers |

### `searches` (V2)
| Field | Type | Description |
|-------|------|-------------|
| id | uuid | Primary key |
| market_id | uuid | FK to markets |
| query | string | Search term |
| results_count | int | Number of results |
| recorded_at | timestamp | When recorded |

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

### Target
- **Main category**: Clothes (women, men, kids)
- **Subcategories**: Dresses, shirts, jeans, jackets, sportswear, etc.
- **Brands**: Mix of fast fashion (Zara, H&M) and premium (Nike, Adidas, Levi's)

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
1. **Search results pages** — listing cards with basic info
2. **Individual item pages** — full details, view/fav counts, seller info
3. **Category pages** — women/men/kids → subcategories
4. **Seller profiles (V2)** — sold count, rating, total listings

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

1. **Week 1-2**: Scraper MVP — one category, 4 markets, basic storage
2. **Week 3-4**: API + Dashboard — trends, price history, basic viz
3. **Month 2**: Sold detection, velocity metrics, arbitrage POC
4. **Month 3**: Evaluate: personal tool or worth expanding?

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