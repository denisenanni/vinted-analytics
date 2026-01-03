import os
import time
import aiosqlite
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Optional
from dotenv import load_dotenv

from ..models.item import VintedItem

load_dotenv()


def retry_supabase(func, max_retries=3, delay=2):
    """Retry a Supabase operation with exponential backoff."""
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt < max_retries - 1:
                wait = delay * (2 ** attempt)  # 2, 4, 8 seconds
                print(f"Supabase error (attempt {attempt + 1}/{max_retries}), retrying in {wait}s: {type(e).__name__}")
                time.sleep(wait)
            else:
                raise


# Database configuration
USE_SUPABASE = os.getenv("USE_SUPABASE", "false").lower() == "true"
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
DB_PATH = Path(__file__).parent.parent.parent / "data" / "vinted.db"

# Supabase client (lazy loaded)
_supabase_client = None


def get_supabase():
    global _supabase_client
    if _supabase_client is None:
        from supabase import create_client
        _supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _supabase_client


# ============================================================================
# SQLite Implementation (local development)
# ============================================================================

async def init_db_sqlite():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vinted_id TEXT UNIQUE,
                title TEXT,
                price REAL,
                currency TEXT,
                brand TEXT,
                size TEXT,
                url TEXT,
                image_url TEXT,
                favorites INTEGER,
                market TEXT,
                category TEXT,
                scraped_at TIMESTAMP,
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'active',
                sold_at TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS price_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vinted_id TEXT,
                price REAL,
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (vinted_id) REFERENCES items(vinted_id)
            )
        """)
        await db.execute("CREATE INDEX IF NOT EXISTS idx_vinted_id ON items(vinted_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_market_category ON items(market, category)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_status ON items(status)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_price_history_vinted_id ON price_history(vinted_id)")
        await db.commit()


async def save_items_sqlite(items: List[VintedItem]) -> dict:
    stats = {"new": 0, "updated": 0, "price_changes": 0}

    async with aiosqlite.connect(DB_PATH) as db:
        for item in items:
            cursor = await db.execute(
                "SELECT price FROM items WHERE vinted_id = ?", (item.vinted_id,)
            )
            existing = await cursor.fetchone()

            if existing:
                old_price = existing[0]
                if old_price != item.price:
                    await db.execute(
                        "INSERT INTO price_history (vinted_id, price) VALUES (?, ?)",
                        (item.vinted_id, item.price)
                    )
                    stats["price_changes"] += 1
                stats["updated"] += 1
            else:
                stats["new"] += 1

            await db.execute("""
                INSERT INTO items (vinted_id, title, price, currency, brand, size, url, image_url, favorites, market, category, scraped_at, last_seen, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, 'active')
                ON CONFLICT(vinted_id) DO UPDATE SET
                    price = excluded.price,
                    favorites = excluded.favorites,
                    last_seen = CURRENT_TIMESTAMP,
                    status = 'active'
            """, (
                item.vinted_id, item.title, item.price, item.currency,
                item.brand, item.size, item.url, item.image_url,
                item.favorites, item.market, item.category,
                item.scraped_at.isoformat()
            ))
        await db.commit()

    return stats


async def mark_sold_items_sqlite(market: str, category: str, active_vinted_ids: List[str], hours_threshold: int = 24) -> int:
    threshold = datetime.now() - timedelta(hours=hours_threshold)

    async with aiosqlite.connect(DB_PATH) as db:
        placeholders = ",".join("?" * len(active_vinted_ids)) if active_vinted_ids else "''"
        query = f"""
            UPDATE items SET status = 'sold', sold_at = CURRENT_TIMESTAMP
            WHERE market = ? AND category = ? AND status = 'active'
            AND last_seen < ? AND vinted_id NOT IN ({placeholders})
        """
        params = [market, category, threshold.isoformat()] + active_vinted_ids
        cursor = await db.execute(query, params)
        sold_count = cursor.rowcount
        await db.commit()
        return sold_count


async def get_stats_sqlite() -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            SELECT COUNT(*), SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END),
                   SUM(CASE WHEN status = 'sold' THEN 1 ELSE 0 END)
            FROM items
        """)
        row = await cursor.fetchone()
        cursor2 = await db.execute("SELECT COUNT(*) FROM price_history")
        price_changes = (await cursor2.fetchone())[0]
        return {"total": row[0], "active": row[1], "sold": row[2], "price_changes": price_changes}


# ============================================================================
# Supabase Implementation (production)
# ============================================================================

async def init_db_supabase():
    # Tables should be created via migrations/001_create_tables.sql
    # This is a no-op for Supabase
    pass


async def save_items_supabase(items: List[VintedItem]) -> dict:
    stats = {"new": 0, "updated": 0, "price_changes": 0}
    supabase = get_supabase()

    for i, item in enumerate(items):
        # Rate limiting: pause every 50 items to avoid overwhelming Supabase
        if i > 0 and i % 50 == 0:
            time.sleep(1)

        # Check if exists (with retry)
        result = retry_supabase(
            lambda: supabase.table("items").select("price").eq("vinted_id", item.vinted_id).execute()
        )
        existing = result.data[0] if result.data else None

        if existing:
            old_price = existing["price"]
            if old_price != item.price:
                retry_supabase(
                    lambda: supabase.table("price_history").insert({
                        "vinted_id": item.vinted_id,
                        "price": item.price
                    }).execute()
                )
                stats["price_changes"] += 1
            stats["updated"] += 1
        else:
            stats["new"] += 1

        # Upsert item (with retry)
        retry_supabase(
            lambda: supabase.table("items").upsert({
                "vinted_id": item.vinted_id,
                "title": item.title,
                "price": item.price,
                "currency": item.currency,
                "brand": item.brand,
                "size": item.size,
                "url": item.url,
                "image_url": item.image_url,
                "favorites": item.favorites,
                "market": item.market,
                "category": item.category,
                "scraped_at": item.scraped_at.isoformat(),
                "last_seen": datetime.now().isoformat(),
                "status": "active"
            }, on_conflict="vinted_id").execute()
        )

    return stats


async def mark_sold_items_supabase(market: str, category: str, active_vinted_ids: List[str], hours_threshold: int = 24) -> int:
    threshold = (datetime.now() - timedelta(hours=hours_threshold)).isoformat()
    supabase = get_supabase()

    # Get items to mark as sold (with retry)
    result = retry_supabase(
        lambda: supabase.table("items")
            .select("vinted_id")
            .eq("market", market)
            .eq("category", category)
            .eq("status", "active")
            .lt("last_seen", threshold)
            .not_.in_("vinted_id", active_vinted_ids)
            .execute()
    )

    sold_ids = [row["vinted_id"] for row in result.data]

    if sold_ids:
        retry_supabase(
            lambda: supabase.table("items")
                .update({"status": "sold", "sold_at": datetime.now().isoformat()})
                .in_("vinted_id", sold_ids)
                .execute()
        )

    return len(sold_ids)


async def get_stats_supabase() -> dict:
    supabase = get_supabase()

    # Single lightweight query - fetch only status column, count in Python
    # Much faster than 4 separate count queries that timeout on free tier
    items_result = retry_supabase(
        lambda: supabase.table("items").select("status").execute()
    )
    items = items_result.data

    total = len(items)
    active = sum(1 for item in items if item.get("status") == "active")
    sold = sum(1 for item in items if item.get("status") == "sold")

    # Price history - use head=True for count-only (no data transfer)
    price_result = retry_supabase(
        lambda: supabase.table("price_history").select("id", count="exact", head=True).execute()
    )

    return {
        "total": total,
        "active": active,
        "sold": sold,
        "price_changes": price_result.count or 0
    }


# ============================================================================
# Public API (auto-selects backend)
# ============================================================================

async def init_db():
    if USE_SUPABASE:
        print("Using Supabase database")
        await init_db_supabase()
    else:
        print("Using SQLite database")
        await init_db_sqlite()


async def save_items(items: List[VintedItem]) -> dict:
    if USE_SUPABASE:
        stats = await save_items_supabase(items)
    else:
        stats = await save_items_sqlite(items)

    print(f"Saved {len(items)} items (new: {stats['new']}, updated: {stats['updated']}, price changes: {stats['price_changes']})")
    return stats


async def mark_sold_items(market: str, category: str, active_vinted_ids: List[str], hours_threshold: int = 24) -> int:
    if USE_SUPABASE:
        sold_count = await mark_sold_items_supabase(market, category, active_vinted_ids, hours_threshold)
    else:
        sold_count = await mark_sold_items_sqlite(market, category, active_vinted_ids, hours_threshold)

    if sold_count > 0:
        print(f"Marked {sold_count} items as sold in {market}/{category}")
    return sold_count


async def get_stats() -> dict:
    if USE_SUPABASE:
        return await get_stats_supabase()
    else:
        return await get_stats_sqlite()


async def get_item_count() -> int:
    stats = await get_stats()
    return stats["total"]


async def get_item_by_vinted_id(vinted_id: str) -> Optional[dict]:
    """Get item by vinted_id (used for tests)."""
    if USE_SUPABASE:
        supabase = get_supabase()
        result = retry_supabase(
            lambda: supabase.table("items").select("*").eq("vinted_id", vinted_id).execute()
        )
        return result.data[0] if result.data else None
    else:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM items WHERE vinted_id = ?", (vinted_id,)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None
