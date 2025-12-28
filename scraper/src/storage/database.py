import aiosqlite
from pathlib import Path
from typing import List
from ..models.item import VintedItem

DB_PATH = Path(__file__).parent.parent.parent / "data" / "vinted.db"


async def init_db():
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
                status TEXT DEFAULT 'active'
            )
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_vinted_id ON items(vinted_id)
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_market_category ON items(market, category)
        """)
        await db.commit()


async def save_items(items: List[VintedItem]):
    async with aiosqlite.connect(DB_PATH) as db:
        for item in items:
            await db.execute("""
                INSERT INTO items (vinted_id, title, price, currency, brand, size, url, image_url, favorites, market, category, scraped_at, last_seen)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(vinted_id) DO UPDATE SET
                    price = excluded.price,
                    favorites = excluded.favorites,
                    last_seen = CURRENT_TIMESTAMP
            """, (
                item.vinted_id,
                item.title,
                item.price,
                item.currency,
                item.brand,
                item.size,
                item.url,
                item.image_url,
                item.favorites,
                item.market,
                item.category,
                item.scraped_at.isoformat()
            ))
        await db.commit()
        print(f"Saved {len(items)} items to database")


async def get_item_count() -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM items")
        row = await cursor.fetchone()
        return row[0] if row else 0
