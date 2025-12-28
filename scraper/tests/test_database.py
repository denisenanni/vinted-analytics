import pytest
import pytest_asyncio
import aiosqlite
from pathlib import Path
from datetime import datetime, timedelta
from src.storage.database import (
    init_db_sqlite,
    save_items_sqlite,
    get_item_by_vinted_id,
    mark_sold_items_sqlite,
    get_stats_sqlite,
    DB_PATH,
)
from src.models.item import VintedItem

# Use a test database
TEST_DB_PATH = Path(__file__).parent / "test_vinted.db"


@pytest_asyncio.fixture
async def test_db(monkeypatch):
    """Create a fresh test database for each test."""
    # Override DB_PATH
    import src.storage.database as db_module
    monkeypatch.setattr(db_module, "DB_PATH", TEST_DB_PATH)

    # Remove existing test db
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()

    # Initialize fresh db (use SQLite directly for tests)
    await init_db_sqlite()

    yield

    # Cleanup
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()


def create_test_item(
    vinted_id: str = "123456",
    price: float = 25.0,
    market: str = "IT",
    category: str = "women/dresses",
) -> VintedItem:
    return VintedItem(
        vinted_id=vinted_id,
        title="Test Item",
        price=price,
        brand="TestBrand",
        url=f"https://www.vinted.it/items/{vinted_id}",
        market=market,
        category=category,
    )


@pytest.mark.asyncio
async def test_save_new_item(test_db):
    """Test that new items are inserted correctly."""
    item = create_test_item(vinted_id="111111", price=30.0)
    stats = await save_items_sqlite([item])

    assert stats["new"] == 1
    assert stats["updated"] == 0

    # Verify item was saved
    saved = await get_item_by_vinted_id("111111")
    assert saved is not None
    assert saved["price"] == 30.0
    assert saved["market"] == "IT"


@pytest.mark.asyncio
async def test_update_existing_item(test_db):
    """Test that existing items are updated."""
    item1 = create_test_item(vinted_id="222222", price=20.0)
    await save_items_sqlite([item1])

    # Update same item with new price
    item2 = create_test_item(vinted_id="222222", price=25.0)
    stats = await save_items_sqlite([item2])

    assert stats["new"] == 0
    assert stats["updated"] == 1

    saved = await get_item_by_vinted_id("222222")
    assert saved["price"] == 25.0


@pytest.mark.asyncio
async def test_price_history_tracked(test_db):
    """Test that price changes are logged."""
    item1 = create_test_item(vinted_id="333333", price=20.0)
    await save_items_sqlite([item1])

    # Change price
    item2 = create_test_item(vinted_id="333333", price=15.0)
    stats = await save_items_sqlite([item2])

    assert stats["price_changes"] == 1

    # Check price_history table
    async with aiosqlite.connect(TEST_DB_PATH) as db:
        cursor = await db.execute(
            "SELECT price FROM price_history WHERE vinted_id = ?",
            ("333333",)
        )
        rows = await cursor.fetchall()
        assert len(rows) == 1
        assert rows[0][0] == 15.0


@pytest.mark.asyncio
async def test_mark_sold_items(test_db):
    """Test sold detection marks old items as sold."""
    # Create items
    items = [
        create_test_item(vinted_id="sold1", price=10.0),
        create_test_item(vinted_id="sold2", price=20.0),
        create_test_item(vinted_id="active1", price=30.0),
    ]
    await save_items_sqlite(items)

    # Manually set last_seen to old date for sold1 and sold2
    async with aiosqlite.connect(TEST_DB_PATH) as db:
        old_date = (datetime.now() - timedelta(hours=48)).isoformat()
        await db.execute(
            "UPDATE items SET last_seen = ? WHERE vinted_id IN ('sold1', 'sold2')",
            (old_date,)
        )
        await db.commit()

    # Mark sold - only active1 is in the "active" list
    sold_count = await mark_sold_items_sqlite("IT", "women/dresses", ["active1"])
    assert sold_count == 2

    # Verify status
    sold1 = await get_item_by_vinted_id("sold1")
    sold2 = await get_item_by_vinted_id("sold2")
    active1 = await get_item_by_vinted_id("active1")

    assert sold1["status"] == "sold"
    assert sold2["status"] == "sold"
    assert active1["status"] == "active"


@pytest.mark.asyncio
async def test_get_stats(test_db):
    """Test stats aggregation."""
    items = [
        create_test_item(vinted_id="s1", price=10.0),
        create_test_item(vinted_id="s2", price=20.0),
    ]
    await save_items_sqlite(items)

    stats = await get_stats_sqlite()
    assert stats["total"] == 2
    assert stats["active"] == 2
    assert stats["sold"] == 0


@pytest.mark.asyncio
async def test_item_count(test_db):
    """Test item count."""
    stats = await get_stats_sqlite()
    assert stats["total"] == 0

    await save_items_sqlite([create_test_item(vinted_id="count1")])
    stats = await get_stats_sqlite()
    assert stats["total"] == 1

    await save_items_sqlite([create_test_item(vinted_id="count2")])
    stats = await get_stats_sqlite()
    assert stats["total"] == 2
