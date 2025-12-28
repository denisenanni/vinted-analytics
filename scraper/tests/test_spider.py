import pytest
from src.spiders.vinted_spider import VintedSpider


class TestVintedSpider:
    def test_base_url_mapping(self):
        """Test correct URL for each market."""
        assert VintedSpider.BASE_URLS["IT"] == "https://www.vinted.it"
        assert VintedSpider.BASE_URLS["FR"] == "https://www.vinted.fr"
        assert VintedSpider.BASE_URLS["DE"] == "https://www.vinted.de"
        assert VintedSpider.BASE_URLS["ES"] == "https://www.vinted.es"
        assert VintedSpider.BASE_URLS["NL"] == "https://www.vinted.nl"
        assert VintedSpider.BASE_URLS["PL"] == "https://www.vinted.pl"
        assert VintedSpider.BASE_URLS["BE"] == "https://www.vinted.be"
        assert VintedSpider.BASE_URLS["AT"] == "https://www.vinted.at"
        assert VintedSpider.BASE_URLS["PT"] == "https://www.vinted.pt"

    def test_catalog_ids(self):
        """Test catalog IDs are defined for all categories."""
        assert VintedSpider.CATALOG_IDS["women/dresses"] == 1904
        assert VintedSpider.CATALOG_IDS["women/shirts"] == 1903
        assert VintedSpider.CATALOG_IDS["men/jeans"] == 2053

    def test_category_slugs_all_markets(self):
        """Test that all markets have category slugs defined."""
        markets = ["IT", "FR", "DE", "ES", "NL", "PL", "BE", "AT", "PT"]
        categories = ["women/dresses", "women/shirts", "men/jeans"]

        for market in markets:
            assert market in VintedSpider.CATEGORY_SLUGS
            for category in categories:
                assert category in VintedSpider.CATEGORY_SLUGS[market]

    def test_get_category_url(self):
        """Test URL generation for different markets."""
        spider_it = VintedSpider(market="IT")
        url_it = spider_it._get_category_url("women/dresses", page_num=1)
        assert url_it == "https://www.vinted.it/catalog/1904-vestiti?page=1"

        spider_fr = VintedSpider(market="FR")
        url_fr = spider_fr._get_category_url("women/dresses", page_num=2)
        assert url_fr == "https://www.vinted.fr/catalog/1904-robes?page=2"

        spider_de = VintedSpider(market="DE")
        url_de = spider_de._get_category_url("men/jeans", page_num=1)
        assert url_de == "https://www.vinted.de/catalog/2053-jeans?page=1"

    def test_parse_price_euro_after(self):
        """Test parsing price with € after number."""
        spider = VintedSpider()
        assert spider._extract_price_from_text("25,00 €") == 25.0
        assert spider._extract_price_from_text("5,50 €") == 5.5
        assert spider._extract_price_from_text("100,00€") == 100.0

    def test_parse_price_euro_before(self):
        """Test parsing price with € before number."""
        spider = VintedSpider()
        assert spider._extract_price_from_text("€25,00") == 25.0
        assert spider._extract_price_from_text("€ 5,50") == 5.5

    def test_parse_price_dot_decimal(self):
        """Test parsing price with dot as decimal separator."""
        spider = VintedSpider()
        assert spider._extract_price_from_text("25.00 €") == 25.0
        assert spider._extract_price_from_text("€25.50") == 25.5

    def test_parse_price_invalid(self):
        """Test parsing invalid price returns 0."""
        spider = VintedSpider()
        assert spider._extract_price_from_text("no price here") == 0.0
        assert spider._extract_price_from_text("") == 0.0

    def test_extract_vinted_id_from_url(self):
        """Test extracting vinted_id from URL."""
        # This tests the logic used in _parse_item_card
        url = "/items/12345678-nice-dress-zara"
        vinted_id = url.split('/items/')[-1].split('-')[0]
        assert vinted_id == "12345678"

        url2 = "/items/99999999-single"
        vinted_id2 = url2.split('/items/')[-1].split('-')[0]
        assert vinted_id2 == "99999999"

    def test_spider_initialization(self):
        """Test spider initializes with correct market."""
        spider = VintedSpider(market="FR")
        assert spider.market == "FR"
        assert spider.base_url == "https://www.vinted.fr"

        spider_default = VintedSpider()
        assert spider_default.market == "IT"
