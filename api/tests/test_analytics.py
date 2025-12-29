import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta


class MockSupabaseResponse:
    """Mock Supabase response object."""
    def __init__(self, data):
        self.data = data
        self.count = len(data) if data else 0


class MockSupabaseQuery:
    """Mock Supabase query builder."""
    def __init__(self, data=None):
        self._data = data or []

    def select(self, *args, **kwargs):
        return self

    def eq(self, field, value):
        if self._data:
            self._data = [d for d in self._data if d.get(field) == value]
        return self

    def gte(self, field, value):
        return self

    def gt(self, field, value):
        if self._data:
            self._data = [d for d in self._data if (d.get(field) or 0) > value]
        return self

    def execute(self):
        return MockSupabaseResponse(self._data)


class MockSupabaseClient:
    """Mock Supabase client."""
    def __init__(self, items_data):
        self._items_data = items_data

    def table(self, table_name):
        if table_name == "items":
            return MockSupabaseQuery(list(self._items_data))
        return MockSupabaseQuery([])


@pytest.fixture
def mock_supabase_with_items():
    """Create a mock Supabase client with test items."""
    items = [
        # Italy - bags should be hot (highest favorites)
        {"market": "IT", "category": "women/handbags", "favorites": 50},
        {"market": "IT", "category": "women/handbags", "favorites": 30},
        {"market": "IT", "category": "women/dresses", "favorites": 10},
        {"market": "IT", "category": "women/dresses", "favorites": 5},
        # Categories not in allowed list should be excluded
        {"market": "IT", "category": "women/jewellery", "favorites": 200},
        {"market": "IT", "category": "clothing", "favorites": 150},
        # France - dresses should be hot
        {"market": "FR", "category": "women/dresses", "favorites": 100},
        {"market": "FR", "category": "women/dresses", "favorites": 50},
        {"market": "FR", "category": "women/handbags", "favorites": 20},
        # Germany - no favorites (should not appear)
        {"market": "DE", "category": "women/dresses", "favorites": 0},
    ]
    return MockSupabaseClient(items)


def test_get_hot_categories_returns_dict(mock_supabase_with_items):
    """Test that get_hot_categories returns a dictionary with hot_categories key."""
    with patch("src.services.analytics.get_supabase", return_value=mock_supabase_with_items):
        from src.services.analytics import get_hot_categories
        result = get_hot_categories()

        assert "hot_categories" in result
        assert isinstance(result["hot_categories"], dict)


def test_get_hot_categories_italy_is_bags(mock_supabase_with_items):
    """Test that Italy's hot category is handbags (highest total favorites)."""
    with patch("src.services.analytics.get_supabase", return_value=mock_supabase_with_items):
        from src.services.analytics import get_hot_categories
        result = get_hot_categories()

        assert "IT" in result["hot_categories"]
        assert result["hot_categories"]["IT"]["category"] == "women/handbags"
        assert result["hot_categories"]["IT"]["total_favorites"] == 80  # 50 + 30


def test_get_hot_categories_france_is_dresses(mock_supabase_with_items):
    """Test that France's hot category is dresses."""
    with patch("src.services.analytics.get_supabase", return_value=mock_supabase_with_items):
        from src.services.analytics import get_hot_categories
        result = get_hot_categories()

        assert "FR" in result["hot_categories"]
        assert result["hot_categories"]["FR"]["category"] == "women/dresses"
        assert result["hot_categories"]["FR"]["total_favorites"] == 150  # 100 + 50


def test_get_hot_categories_empty_market():
    """Test that markets with no items are not included."""
    empty_client = MockSupabaseClient([])

    with patch("src.services.analytics.get_supabase", return_value=empty_client):
        from src.services.analytics import get_hot_categories
        result = get_hot_categories()

        assert result["hot_categories"] == {}


def test_get_hot_categories_includes_item_count(mock_supabase_with_items):
    """Test that hot categories include item count."""
    with patch("src.services.analytics.get_supabase", return_value=mock_supabase_with_items):
        from src.services.analytics import get_hot_categories
        result = get_hot_categories()

        assert "IT" in result["hot_categories"]
        assert result["hot_categories"]["IT"]["item_count"] == 2  # 2 handbag items


def test_get_hot_categories_only_includes_allowed_categories(mock_supabase_with_items):
    """Test that only categories in the allowed list are considered."""
    with patch("src.services.analytics.get_supabase", return_value=mock_supabase_with_items):
        from src.services.analytics import get_hot_categories
        result = get_hot_categories()

        # Italy has 'women/jewellery' with 200 favorites but it's not in the allowed list
        # So handbags (80 favorites) should win instead
        assert "IT" in result["hot_categories"]
        assert result["hot_categories"]["IT"]["category"] == "women/handbags"
        assert result["hot_categories"]["IT"]["category"] != "women/jewellery"
