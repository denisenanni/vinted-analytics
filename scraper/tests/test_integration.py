import pytest
import pytest_asyncio
from src.spiders.vinted_spider import VintedSpider


@pytest.mark.asyncio
@pytest.mark.integration
async def test_scrape_single_page_it():
    """Test scraping a single page from IT market returns valid items."""
    spider = VintedSpider(market="IT")
    items = await spider.scrape(category="women/dresses", max_pages=1)

    assert len(items) > 0
    assert len(items) <= 100  # Vinted shows ~96 items per page

    # Verify item structure
    item = items[0]
    assert item.vinted_id is not None
    assert item.title is not None
    assert item.price >= 0
    assert item.market == "IT"
    assert item.category == "women/dresses"
    assert item.url.startswith("https://www.vinted.it")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_scrape_single_page_fr():
    """Test scraping a single page from FR market."""
    spider = VintedSpider(market="FR")
    items = await spider.scrape(category="women/dresses", max_pages=1)

    assert len(items) > 0
    item = items[0]
    assert item.market == "FR"
    assert item.url.startswith("https://www.vinted.fr")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_scrape_single_page_de():
    """Test scraping a single page from DE market."""
    spider = VintedSpider(market="DE")
    items = await spider.scrape(category="women/dresses", max_pages=1)

    assert len(items) > 0
    item = items[0]
    assert item.market == "DE"
    assert item.url.startswith("https://www.vinted.de")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_category_women_shirts():
    """Test scraping women/shirts category."""
    spider = VintedSpider(market="IT")
    items = await spider.scrape(category="women/shirts", max_pages=1)

    assert len(items) > 0
    assert items[0].category == "women/shirts"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_category_men_jeans():
    """Test scraping men/jeans category."""
    spider = VintedSpider(market="IT")
    items = await spider.scrape(category="men/jeans", max_pages=1)

    assert len(items) > 0
    assert items[0].category == "men/jeans"
