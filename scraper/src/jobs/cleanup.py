"""
Daily cleanup and aggregation job for Vinted Analytics.

This script:
1. Aggregates daily stats before cleanup
2. Deletes stale active items (not seen in 7 days)
3. Deletes old sold items (older than 90 days)
4. Deletes old price history (older than 90 days)
5. Deletes orphaned price history records
"""

import asyncio
import os
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()

USE_SUPABASE = os.getenv("USE_SUPABASE", "false").lower() == "true"


def get_supabase():
    """Get Supabase client."""
    from supabase import create_client
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        raise ValueError(f"Supabase credentials missing. SUPABASE_URL={'set' if url else 'missing'}, SUPABASE_KEY={'set' if key else 'missing'}")
    return create_client(url, key)


async def aggregate_daily_stats_supabase():
    """Aggregate stats into stats_daily table using Supabase."""
    supabase = get_supabase()
    today = datetime.now(timezone.utc).date().isoformat()

    # Get all unique market/category/brand combinations with their stats
    # Note: Supabase doesn't support complex aggregations directly,
    # so we fetch data and aggregate in Python

    print(f"Aggregating stats for {today}...")

    # Get all items grouped by market, category, brand
    items_result = supabase.table("items").select("market, category, brand, price, status, first_seen, sold_at").execute()
    items = items_result.data

    if not items:
        print("No items to aggregate")
        return

    # Group by market/category/brand
    from collections import defaultdict
    groups = defaultdict(list)
    for item in items:
        key = (item["market"], item["category"], item.get("brand"))
        groups[key].append(item)

    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    stats_to_insert = []

    for (market, category, brand), group_items in groups.items():
        active_items = [i for i in group_items if i["status"] == "active"]
        sold_items = [i for i in group_items if i["status"] == "sold"]

        # Count items sold in the last day
        recent_sold = [i for i in sold_items if i.get("sold_at") and i["sold_at"] >= yesterday]

        # Calculate prices from active items
        prices = [i["price"] for i in active_items if i.get("price")]

        # Calculate time to sell for sold items
        time_to_sell_days = []
        for item in sold_items:
            if item.get("sold_at") and item.get("first_seen"):
                try:
                    sold = datetime.fromisoformat(item["sold_at"].replace("Z", "+00:00"))
                    first = datetime.fromisoformat(item["first_seen"].replace("Z", "+00:00"))
                    days = (sold - first).total_seconds() / 86400
                    if days >= 0:
                        time_to_sell_days.append(days)
                except (ValueError, TypeError):
                    pass

        stats_to_insert.append({
            "date": today,
            "market": market,
            "category": category,
            "brand": brand,
            "active_count": len(active_items),
            "sold_count": len(recent_sold),
            "avg_price": round(sum(prices) / len(prices), 2) if prices else None,
            "min_price": min(prices) if prices else None,
            "max_price": max(prices) if prices else None,
            "avg_time_to_sell_days": round(sum(time_to_sell_days) / len(time_to_sell_days), 1) if time_to_sell_days else None,
        })

    # Upsert stats (handles conflicts on date/market/category/brand)
    if stats_to_insert:
        for stat in stats_to_insert:
            try:
                supabase.table("stats_daily").upsert(
                    stat,
                    on_conflict="date,market,category,brand"
                ).execute()
            except Exception as e:
                # Log but continue - some may fail on conflict resolution
                print(f"Warning: Could not upsert stat for {stat['market']}/{stat['category']}: {e}")

        print(f"Aggregated {len(stats_to_insert)} stat records")


async def cleanup_stale_items_supabase():
    """Delete active items not seen in 7 days."""
    supabase = get_supabase()
    cutoff = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()

    result = supabase.table("items").delete().eq("status", "active").lt("last_seen", cutoff).execute()
    deleted = len(result.data) if result.data else 0
    print(f"Deleted {deleted} stale active items (not seen in 7 days)")
    return deleted


async def cleanup_old_sold_items_supabase():
    """Delete sold items older than 90 days."""
    supabase = get_supabase()
    cutoff = (datetime.now(timezone.utc) - timedelta(days=90)).isoformat()

    result = supabase.table("items").delete().eq("status", "sold").lt("sold_at", cutoff).execute()
    deleted = len(result.data) if result.data else 0
    print(f"Deleted {deleted} old sold items (older than 90 days)")
    return deleted


async def cleanup_old_price_history_supabase():
    """Delete price history older than 90 days."""
    supabase = get_supabase()
    cutoff = (datetime.now(timezone.utc) - timedelta(days=90)).isoformat()

    result = supabase.table("price_history").delete().lt("recorded_at", cutoff).execute()
    deleted = len(result.data) if result.data else 0
    print(f"Deleted {deleted} old price history records (older than 90 days)")
    return deleted


async def cleanup_orphaned_price_history_supabase():
    """Delete price history for items that no longer exist."""
    supabase = get_supabase()

    # Get all valid vinted_ids
    items_result = supabase.table("items").select("vinted_id").execute()
    valid_ids = {item["vinted_id"] for item in items_result.data}

    # Get all price_history records
    history_result = supabase.table("price_history").select("id, vinted_id").execute()

    # Find orphans
    orphan_ids = [h["id"] for h in history_result.data if h["vinted_id"] not in valid_ids]

    if orphan_ids:
        # Delete in batches to avoid timeout
        batch_size = 100
        for i in range(0, len(orphan_ids), batch_size):
            batch = orphan_ids[i:i + batch_size]
            for orphan_id in batch:
                supabase.table("price_history").delete().eq("id", orphan_id).execute()
        print(f"Deleted {len(orphan_ids)} orphaned price history records")
    else:
        print("No orphaned price history records found")

    return len(orphan_ids)


# SQLite implementations for local development
import aiosqlite
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / "data" / "vinted.db"


async def aggregate_daily_stats_sqlite():
    """Aggregate stats for SQLite."""
    today = datetime.now(timezone.utc).date().isoformat()
    print(f"Aggregating stats for {today}...")

    async with aiosqlite.connect(DB_PATH) as db:
        # Create stats_daily table if not exists
        await db.execute("""
            CREATE TABLE IF NOT EXISTS stats_daily (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                market TEXT NOT NULL,
                category TEXT NOT NULL,
                brand TEXT,
                active_count INTEGER,
                sold_count INTEGER,
                avg_price REAL,
                min_price REAL,
                max_price REAL,
                avg_time_to_sell_days REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(date, market, category, brand)
            )
        """)

        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()

        # Aggregate and insert stats
        await db.execute("""
            INSERT OR REPLACE INTO stats_daily (date, market, category, brand, active_count, sold_count, avg_price, min_price, max_price, avg_time_to_sell_days)
            SELECT
                ?,
                market,
                category,
                brand,
                SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active_count,
                SUM(CASE WHEN status = 'sold' AND sold_at >= ? THEN 1 ELSE 0 END) as sold_count,
                AVG(CASE WHEN status = 'active' THEN price END) as avg_price,
                MIN(CASE WHEN status = 'active' THEN price END) as min_price,
                MAX(CASE WHEN status = 'active' THEN price END) as max_price,
                AVG(CASE WHEN status = 'sold' THEN
                    (julianday(sold_at) - julianday(first_seen))
                END) as avg_time_to_sell_days
            FROM items
            GROUP BY market, category, brand
        """, (today, yesterday))

        await db.commit()

        cursor = await db.execute("SELECT COUNT(*) FROM stats_daily WHERE date = ?", (today,))
        count = (await cursor.fetchone())[0]
        print(f"Aggregated {count} stat records")


async def cleanup_stale_items_sqlite():
    """Delete stale items from SQLite."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()

    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "DELETE FROM items WHERE status = 'active' AND last_seen < ?",
            (cutoff,)
        )
        deleted = cursor.rowcount
        await db.commit()
        print(f"Deleted {deleted} stale active items (not seen in 7 days)")
        return deleted


async def cleanup_old_sold_items_sqlite():
    """Delete old sold items from SQLite."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=90)).isoformat()

    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "DELETE FROM items WHERE status = 'sold' AND sold_at < ?",
            (cutoff,)
        )
        deleted = cursor.rowcount
        await db.commit()
        print(f"Deleted {deleted} old sold items (older than 90 days)")
        return deleted


async def cleanup_old_price_history_sqlite():
    """Delete old price history from SQLite."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=90)).isoformat()

    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "DELETE FROM price_history WHERE recorded_at < ?",
            (cutoff,)
        )
        deleted = cursor.rowcount
        await db.commit()
        print(f"Deleted {deleted} old price history records (older than 90 days)")
        return deleted


async def cleanup_orphaned_price_history_sqlite():
    """Delete orphaned price history from SQLite."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            DELETE FROM price_history
            WHERE vinted_id NOT IN (SELECT vinted_id FROM items)
        """)
        deleted = cursor.rowcount
        await db.commit()
        print(f"Deleted {deleted} orphaned price history records")
        return deleted


async def run_daily_cleanup():
    """Run all cleanup tasks in order."""
    print("=" * 50)
    print("Starting daily cleanup...")
    print(f"Using {'Supabase' if USE_SUPABASE else 'SQLite'} database")
    print("=" * 50)

    if USE_SUPABASE:
        # 1. Aggregate stats first (before we delete anything!)
        print("\n1. Aggregating daily stats...")
        await aggregate_daily_stats_supabase()

        # 2. Cleanup stale active items
        print("\n2. Cleaning stale active items...")
        await cleanup_stale_items_supabase()

        # 3. Cleanup old sold items
        print("\n3. Cleaning old sold items...")
        await cleanup_old_sold_items_supabase()

        # 4. Cleanup old price history
        print("\n4. Cleaning old price history...")
        await cleanup_old_price_history_supabase()

        # 5. Cleanup orphaned price history
        print("\n5. Cleaning orphaned price history...")
        await cleanup_orphaned_price_history_supabase()
    else:
        # SQLite implementations
        print("\n1. Aggregating daily stats...")
        await aggregate_daily_stats_sqlite()

        print("\n2. Cleaning stale active items...")
        await cleanup_stale_items_sqlite()

        print("\n3. Cleaning old sold items...")
        await cleanup_old_sold_items_sqlite()

        print("\n4. Cleaning old price history...")
        await cleanup_old_price_history_sqlite()

        print("\n5. Cleaning orphaned price history...")
        await cleanup_orphaned_price_history_sqlite()

    print("\n" + "=" * 50)
    print("Daily cleanup complete!")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(run_daily_cleanup())
