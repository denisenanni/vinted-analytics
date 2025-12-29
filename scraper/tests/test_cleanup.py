import pytest
import pytest_asyncio
import aiosqlite
from pathlib import Path
from datetime import datetime, timedelta

from src.jobs.cleanup import (
    aggregate_daily_stats_sqlite,
    cleanup_stale_items_sqlite,
    cleanup_old_sold_items_sqlite,
    cleanup_old_price_history_sqlite,
    cleanup_orphaned_price_history_sqlite,
    DB_PATH,
)

# Use a test database
TEST_DB_PATH = Path(__file__).parent / "test_cleanup.db"


@pytest_asyncio.fixture
async def test_db(monkeypatch):
    """Create a fresh test database for each test."""
    import src.jobs.cleanup as cleanup_module
    monkeypatch.setattr(cleanup_module, "DB_PATH", TEST_DB_PATH)
    monkeypatch.setattr(cleanup_module, "USE_SUPABASE", False)

    # Remove existing test db
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()

    # Initialize fresh db
    async with aiosqlite.connect(TEST_DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vinted_id TEXT UNIQUE,
                title TEXT,
                price REAL,
                currency TEXT DEFAULT 'EUR',
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
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
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
        await db.commit()

    yield

    # Cleanup
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()


async def insert_test_item(db, vinted_id, market="IT", category="women/dresses",
                           brand="TestBrand", price=25.0, status="active",
                           last_seen=None, first_seen=None, sold_at=None):
    """Helper to insert test items."""
    now = datetime.now().isoformat()
    last_seen = last_seen or now
    first_seen = first_seen or now

    await db.execute("""
        INSERT INTO items (vinted_id, title, price, brand, market, category, status, last_seen, first_seen, sold_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (vinted_id, f"Test {vinted_id}", price, brand, market, category, status, last_seen, first_seen, sold_at))
    await db.commit()


async def insert_test_price_history(db, vinted_id, price, recorded_at=None):
    """Helper to insert test price history."""
    recorded_at = recorded_at or datetime.now().isoformat()
    await db.execute("""
        INSERT INTO price_history (vinted_id, price, recorded_at)
        VALUES (?, ?, ?)
    """, (vinted_id, price, recorded_at))
    await db.commit()


@pytest.mark.asyncio
async def test_aggregate_daily_stats(test_db):
    """Test that daily stats are aggregated correctly."""
    async with aiosqlite.connect(TEST_DB_PATH) as db:
        # Insert test items
        await insert_test_item(db, "item1", market="IT", category="women/dresses", brand="Zara", price=20.0)
        await insert_test_item(db, "item2", market="IT", category="women/dresses", brand="Zara", price=30.0)
        await insert_test_item(db, "item3", market="IT", category="women/dresses", brand="H&M", price=15.0)
        await insert_test_item(db, "item4", market="FR", category="men/jeans", brand="Levis", price=50.0)

    # Run aggregation
    await aggregate_daily_stats_sqlite()

    # Verify stats were created
    async with aiosqlite.connect(TEST_DB_PATH) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM stats_daily")
        count = (await cursor.fetchone())[0]
        assert count > 0

        # Check specific stats for Zara
        cursor = await db.execute("""
            SELECT active_count, avg_price FROM stats_daily
            WHERE market = 'IT' AND category = 'women/dresses' AND brand = 'Zara'
        """)
        row = await cursor.fetchone()
        assert row is not None
        assert row[0] == 2  # 2 active Zara items
        assert row[1] == 25.0  # avg of 20 and 30


@pytest.mark.asyncio
async def test_cleanup_stale_items(test_db):
    """Test that stale active items are deleted."""
    old_date = (datetime.now() - timedelta(days=10)).isoformat()
    recent_date = (datetime.now() - timedelta(days=1)).isoformat()

    async with aiosqlite.connect(TEST_DB_PATH) as db:
        # Insert stale item (not seen in 10 days)
        await insert_test_item(db, "stale1", status="active", last_seen=old_date)
        # Insert recent item
        await insert_test_item(db, "recent1", status="active", last_seen=recent_date)

    # Run cleanup
    deleted = await cleanup_stale_items_sqlite()

    assert deleted == 1

    # Verify only recent item remains
    async with aiosqlite.connect(TEST_DB_PATH) as db:
        cursor = await db.execute("SELECT vinted_id FROM items WHERE status = 'active'")
        rows = await cursor.fetchall()
        assert len(rows) == 1
        assert rows[0][0] == "recent1"


@pytest.mark.asyncio
async def test_cleanup_old_sold_items(test_db):
    """Test that old sold items are deleted."""
    old_date = (datetime.now() - timedelta(days=100)).isoformat()
    recent_date = (datetime.now() - timedelta(days=30)).isoformat()

    async with aiosqlite.connect(TEST_DB_PATH) as db:
        # Insert old sold item (sold 100 days ago)
        await insert_test_item(db, "old_sold", status="sold", sold_at=old_date)
        # Insert recent sold item (sold 30 days ago)
        await insert_test_item(db, "recent_sold", status="sold", sold_at=recent_date)

    # Run cleanup
    deleted = await cleanup_old_sold_items_sqlite()

    assert deleted == 1

    # Verify only recent sold item remains
    async with aiosqlite.connect(TEST_DB_PATH) as db:
        cursor = await db.execute("SELECT vinted_id FROM items WHERE status = 'sold'")
        rows = await cursor.fetchall()
        assert len(rows) == 1
        assert rows[0][0] == "recent_sold"


@pytest.mark.asyncio
async def test_cleanup_old_price_history(test_db):
    """Test that old price history is deleted."""
    old_date = (datetime.now() - timedelta(days=100)).isoformat()
    recent_date = (datetime.now() - timedelta(days=30)).isoformat()

    async with aiosqlite.connect(TEST_DB_PATH) as db:
        await insert_test_item(db, "item1")
        # Insert old price history
        await insert_test_price_history(db, "item1", 20.0, recorded_at=old_date)
        # Insert recent price history
        await insert_test_price_history(db, "item1", 25.0, recorded_at=recent_date)

    # Run cleanup
    deleted = await cleanup_old_price_history_sqlite()

    assert deleted == 1

    # Verify only recent price history remains
    async with aiosqlite.connect(TEST_DB_PATH) as db:
        cursor = await db.execute("SELECT price FROM price_history")
        rows = await cursor.fetchall()
        assert len(rows) == 1
        assert rows[0][0] == 25.0


@pytest.mark.asyncio
async def test_cleanup_orphaned_price_history(test_db):
    """Test that orphaned price history is deleted."""
    async with aiosqlite.connect(TEST_DB_PATH) as db:
        # Insert item with price history
        await insert_test_item(db, "exists")
        await insert_test_price_history(db, "exists", 20.0)

        # Insert orphaned price history (no matching item)
        await insert_test_price_history(db, "orphan1", 30.0)
        await insert_test_price_history(db, "orphan2", 40.0)

    # Run cleanup
    deleted = await cleanup_orphaned_price_history_sqlite()

    assert deleted == 2

    # Verify only valid price history remains
    async with aiosqlite.connect(TEST_DB_PATH) as db:
        cursor = await db.execute("SELECT vinted_id FROM price_history")
        rows = await cursor.fetchall()
        assert len(rows) == 1
        assert rows[0][0] == "exists"


@pytest.mark.asyncio
async def test_cleanup_does_not_delete_recent_items(test_db):
    """Test that recent items are not deleted."""
    now = datetime.now().isoformat()

    async with aiosqlite.connect(TEST_DB_PATH) as db:
        # Insert fresh active items
        await insert_test_item(db, "fresh1", status="active", last_seen=now)
        await insert_test_item(db, "fresh2", status="active", last_seen=now)
        # Insert fresh sold items
        await insert_test_item(db, "sold1", status="sold", sold_at=now)

    # Run all cleanup operations
    stale_deleted = await cleanup_stale_items_sqlite()
    sold_deleted = await cleanup_old_sold_items_sqlite()

    assert stale_deleted == 0
    assert sold_deleted == 0

    # Verify all items still exist
    async with aiosqlite.connect(TEST_DB_PATH) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM items")
        count = (await cursor.fetchone())[0]
        assert count == 3


@pytest.mark.asyncio
async def test_stats_aggregation_with_sold_items(test_db):
    """Test that sold items are counted in stats."""
    yesterday = (datetime.now() - timedelta(hours=12)).isoformat()
    first_seen = (datetime.now() - timedelta(days=5)).isoformat()

    async with aiosqlite.connect(TEST_DB_PATH) as db:
        # Active items
        await insert_test_item(db, "active1", market="IT", category="women/dresses", price=20.0)
        await insert_test_item(db, "active2", market="IT", category="women/dresses", price=30.0)
        # Recently sold item
        await insert_test_item(db, "sold1", market="IT", category="women/dresses",
                              status="sold", price=25.0, first_seen=first_seen, sold_at=yesterday)

    # Run aggregation
    await aggregate_daily_stats_sqlite()

    # Verify stats
    async with aiosqlite.connect(TEST_DB_PATH) as db:
        cursor = await db.execute("""
            SELECT active_count, sold_count FROM stats_daily
            WHERE market = 'IT' AND category = 'women/dresses' AND brand IS NULL
        """)
        row = await cursor.fetchone()
        # Should have category-level stats (brand = NULL aggregates all)
        # The test inserts items with brand='TestBrand' by default

        cursor = await db.execute("""
            SELECT active_count, sold_count FROM stats_daily
            WHERE market = 'IT' AND category = 'women/dresses' AND brand = 'TestBrand'
        """)
        row = await cursor.fetchone()
        assert row is not None
        assert row[0] == 2  # 2 active
        assert row[1] == 1  # 1 sold recently
