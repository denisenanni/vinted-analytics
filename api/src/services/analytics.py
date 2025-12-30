from typing import List, Optional
from datetime import datetime, timedelta
from ..db import get_supabase

# Cache for hot categories (refreshes every 5 minutes)
_hot_categories_cache = {
    "data": None,
    "expires_at": None
}
HOT_CATEGORIES_TTL = timedelta(minutes=5)

# Cache for market stats aggregation (refreshes every 3 minutes)
_market_stats_cache = {}
MARKET_STATS_TTL = timedelta(minutes=3)


def lookup_items(
    brand: Optional[str] = None,
    category: Optional[str] = None,
    size: Optional[str] = None,
    market: Optional[str] = None,
    limit: int = 20
) -> dict:
    """Core lookup: find similar items and calculate stats."""
    supabase = get_supabase()

    # Build base filters
    def apply_filters(query):
        if brand:
            query = query.ilike("brand", f"%{brand}%")
        if category:
            query = query.eq("category", category)
        if size:
            query = query.ilike("size", f"%{size}%")
        if market:
            query = query.eq("market", market)
        return query

    # Query 1: Get recent items for display (limited)
    items_query = supabase.table("items").select("*")
    items_query = apply_filters(items_query)
    items_query = items_query.order("last_seen", desc=True).limit(500)
    result = items_query.execute()
    items = result.data

    if not items:
        return {
            "total_items": 0,
            "avg_price": 0,
            "min_price": 0,
            "max_price": 0,
            "demand_score": "unknown",
            "best_markets": [],
            "recent_items": []
        }

    # Calculate stats from recent items
    prices = [i["price"] for i in items if i["price"]]
    avg_price = sum(prices) / len(prices) if prices else 0
    min_price = min(prices) if prices else 0
    max_price = max(prices) if prices else 0

    # Demand score based on favorites
    avg_favorites = sum(i["favorites"] or 0 for i in items) / len(items)
    if avg_favorites > 10:
        demand_score = "high"
    elif avg_favorites > 5:
        demand_score = "medium"
    else:
        demand_score = "low"

    # Query 2: Separate aggregation for best markets (with caching)
    cache_key = f"{brand or ''}:{category or ''}:{size or ''}:{market or ''}"
    cached = _market_stats_cache.get(cache_key)

    if cached and datetime.now() < cached["expires_at"]:
        # Use cached data
        best_markets = cached["best_markets"]
        total_items = cached["total_items"]
    else:
        # Fetch all items with pagination
        all_market_items = []
        page_size = 1000
        offset = 0

        while True:
            markets_query = supabase.table("items").select("market, price, favorites")
            markets_query = apply_filters(markets_query)
            markets_query = markets_query.range(offset, offset + page_size - 1)
            markets_result = markets_query.execute()
            batch = markets_result.data

            if not batch:
                break

            all_market_items.extend(batch)
            offset += page_size

            # Safety limit to prevent infinite loops (max 50k items)
            if offset >= 50000:
                break

        # Aggregate by market
        market_stats = {}
        for item in all_market_items:
            m = item["market"]
            if m not in market_stats:
                market_stats[m] = {"count": 0, "prices": [], "favorites": []}
            market_stats[m]["count"] += 1
            market_stats[m]["prices"].append(item["price"] or 0)
            market_stats[m]["favorites"].append(item["favorites"] or 0)

        best_markets = []
        for m, stats in market_stats.items():
            best_markets.append({
                "market": m,
                "count": stats["count"],
                "avg_price": sum(stats["prices"]) / len(stats["prices"]) if stats["prices"] else 0,
                "avg_favorites": sum(stats["favorites"]) / len(stats["favorites"]) if stats["favorites"] else 0
            })
        best_markets.sort(key=lambda x: x["count"], reverse=True)

        total_items = len(all_market_items)

        # Cache the results
        _market_stats_cache[cache_key] = {
            "best_markets": best_markets,
            "total_items": total_items,
            "expires_at": datetime.now() + MARKET_STATS_TTL
        }

    return {
        "total_items": total_items,
        "avg_price": round(avg_price, 2),
        "min_price": round(min_price, 2),
        "max_price": round(max_price, 2),
        "demand_score": demand_score,
        "best_markets": best_markets[:5],
        "recent_items": items[:limit]
    }


def compare_markets(
    brand: Optional[str] = None,
    category: Optional[str] = None,
    markets: List[str] = None
) -> dict:
    """Compare same item type across markets."""
    supabase = get_supabase()

    if not markets:
        markets = ["IT", "FR", "DE", "ES", "NL", "PL", "BE", "AT", "PT"]

    # Single batch query for all markets
    query = supabase.table("items").select("*").in_("market", markets)

    if brand:
        query = query.ilike("brand", f"%{brand}%")
    if category:
        query = query.eq("category", category)

    result = query.limit(2000).execute()
    all_items = result.data

    # Group items by market
    items_by_market = {}
    for item in all_items:
        m = item["market"]
        if m not in items_by_market:
            items_by_market[m] = []
        items_by_market[m].append(item)

    market_data = []
    for market in markets:
        items = items_by_market.get(market, [])

        if items:
            prices = [i["price"] for i in items if i["price"]]
            sold = [i for i in items if i["status"] == "sold"]
            favorites = [i["favorites"] or 0 for i in items]

            market_data.append({
                "market": market,
                "item_count": len(items),
                "avg_price": round(sum(prices) / len(prices), 2) if prices else 0,
                "min_price": round(min(prices), 2) if prices else 0,
                "max_price": round(max(prices), 2) if prices else 0,
                "sold_count": len(sold),
                "avg_favorites": round(sum(favorites) / len(favorites), 2) if favorites else 0
            })

    # Determine best market
    if market_data:
        # Sort by item count (demand indicator)
        market_data.sort(key=lambda x: x["item_count"], reverse=True)
        best = market_data[0]
        reason = f"Highest demand with {best['item_count']} items, avg price €{best['avg_price']}"
    else:
        best = {"market": "unknown"}
        reason = "No data available"

    return {
        "markets": market_data,
        "best_market": best.get("market", "unknown"),
        "reason": reason
    }


def get_trends(
    market: str = "IT",
    categories: Optional[List[str]] = None,
    period: str = "7d",
    limit: int = 20,
    offset: int = 0
) -> dict:
    """Get trending items sorted by favorites/popularity."""
    supabase = get_supabase()

    # Calculate date threshold
    days = int(period.replace("d", "")) if period.endswith("d") else 7
    threshold = (datetime.now() - timedelta(days=days)).isoformat()

    query = supabase.table("items").select("*", count="exact").eq("market", market).gte("last_seen", threshold)

    if categories and len(categories) > 0:
        query = query.in_("category", categories)

    # Only get items with favorites > 0 (actually trending)
    query = query.gt("favorites", 0)

    # Order by favorites (trending = most popular)
    result = query.order("favorites", desc=True).range(offset, offset + limit - 1).execute()
    items = result.data
    total_count = result.count or len(items)

    if not items:
        return {
            "total_items": 0,
            "avg_price": 0,
            "trending_items": [],
            "has_more": False
        }

    prices = [i["price"] for i in items if i["price"]]
    avg_price = sum(prices) / len(prices) if prices else 0

    # Format trending items
    trending_items = []
    for item in items:
        trending_items.append({
            "vinted_id": item["vinted_id"],
            "title": item["title"],
            "price": item["price"],
            "brand": item.get("brand"),
            "url": item.get("url"),
            "image_url": item.get("image_url"),
            "favorites": item.get("favorites") or 0,
            "market": item["market"],
            "category": item.get("category")
        })

    return {
        "total_items": total_count,
        "avg_price": round(avg_price, 2),
        "trending_items": trending_items,
        "has_more": offset + limit < total_count
    }


def get_hot_categories() -> dict:
    """Get the hottest (most trending) category for each market."""
    global _hot_categories_cache

    # Return cached data if still valid
    if (_hot_categories_cache["data"] is not None
        and _hot_categories_cache["expires_at"]
        and datetime.now() < _hot_categories_cache["expires_at"]):
        return _hot_categories_cache["data"]

    supabase = get_supabase()
    markets = ["IT", "FR", "DE", "ES", "NL", "PL", "BE", "AT", "PT"]

    # Only include categories that are shown in the UI filters
    allowed_categories = {
        # Women's clothing
        "women/dresses", "women/tops-and-t-shirts", "women/jumpers-and-sweaters",
        "women/jeans", "women/trousers-and-leggings", "women/skirts",
        "women/shorts-and-cropped-trousers", "women/outerwear", "women/suits-and-blazers",
        "women/jumpsuits-and-playsuits", "women/activewear", "women/swimwear",
        "women/lingerie-and-nightwear", "women/maternity-clothes", "women/other-clothing",
        # Women's shoes
        "women/boots", "women/heels", "women/trainers", "women/sandals",
        "women/ballerinas", "women/slippers", "women/sports-shoes",
        "women/flip-flops-and-slides", "women/espadrilles",
        # Women's bags
        "women/handbags", "women/backpacks", "women/shoulder-bags", "women/tote-bags",
        "women/clutches", "women/wallets-and-purses", "women/bucket-bags",
        "women/hobo-bags", "women/beach-bags", "women/gym-bags", "women/bum-bags",
        # Women's accessories
        "women/jewellery", "women/watches", "women/sunglasses", "women/belts",
        "women/hats-and-caps", "women/scarves-and-shawls", "women/gloves",
        "women/hair-accessories", "women/umbrellas", "women/keyrings",
        # Men's clothing
        "men/tops-and-t-shirts", "men/jumpers-and-sweaters", "men/jeans",
        "men/trousers", "men/shorts", "men/outerwear", "men/suits-and-blazers",
        "men/activewear", "men/swimwear", "men/sleepwear", "men/socks-and-underwear",
        # Men's shoes
        "men/boots", "men/trainers", "men/formal-shoes", "men/sandals",
        "men/sports-shoes", "men/slippers", "men/flip-flops-and-slides",
        # Men's accessories
        "men/bags-and-backpacks", "men/jewellery", "men/watches", "men/sunglasses",
        "men/belts", "men/hats-and-caps", "men/scarves-and-shawls", "men/gloves",
        "men/ties-and-bow-ties", "men/braces-and-suspenders",
    }

    # Get recent items with favorites - single batch query for all markets
    threshold = (datetime.now() - timedelta(days=7)).isoformat()

    result = supabase.table("items")\
        .select("market, category, favorites")\
        .in_("market", markets)\
        .gte("last_seen", threshold)\
        .gt("favorites", 0)\
        .execute()

    all_items = result.data

    # Group by market, then aggregate by category
    market_category_stats = {}
    for item in all_items:
        market = item.get("market")
        cat = item.get("category")

        if not market or not cat:
            continue
        if cat not in allowed_categories:
            continue

        if market not in market_category_stats:
            market_category_stats[market] = {}
        if cat not in market_category_stats[market]:
            market_category_stats[market][cat] = {"total_favorites": 0, "count": 0}

        market_category_stats[market][cat]["total_favorites"] += item.get("favorites") or 0
        market_category_stats[market][cat]["count"] += 1

    # Find hottest category per market
    hot_categories = {}
    for market, category_stats in market_category_stats.items():
        if category_stats:
            hot_cat = max(category_stats.items(), key=lambda x: x[1]["total_favorites"])
            hot_categories[market] = {
                "category": hot_cat[0],
                "total_favorites": hot_cat[1]["total_favorites"],
                "item_count": hot_cat[1]["count"]
            }

    # Cache the result
    result = {"hot_categories": hot_categories}
    _hot_categories_cache["data"] = result
    _hot_categories_cache["expires_at"] = datetime.now() + HOT_CATEGORIES_TTL

    return result


def get_sold_items(
    brand: Optional[str] = None,
    category: Optional[str] = None,
    market: str = "IT",
    period: str = "30d",
    limit: int = 50
) -> dict:
    """Get recently sold items."""
    supabase = get_supabase()

    days = int(period.replace("d", "")) if period.endswith("d") else 30
    threshold = (datetime.now() - timedelta(days=days)).isoformat()

    query = supabase.table("items")\
        .select("*")\
        .eq("market", market)\
        .eq("status", "sold")\
        .gte("sold_at", threshold)

    if brand:
        query = query.ilike("brand", f"%{brand}%")
    if category:
        query = query.eq("category", category)

    result = query.order("sold_at", desc=True).limit(limit).execute()
    items = result.data

    # Calculate time to sell
    sold_items = []
    days_to_sell_list = []

    for item in items:
        first_seen = item.get("first_seen")
        sold_at = item.get("sold_at")
        days_to_sell = None

        if first_seen and sold_at:
            try:
                fs = datetime.fromisoformat(first_seen.replace("Z", "+00:00"))
                sa = datetime.fromisoformat(sold_at.replace("Z", "+00:00"))
                days_to_sell = (sa - fs).days
                if days_to_sell >= 0:
                    days_to_sell_list.append(days_to_sell)
            except:
                pass

        sold_items.append({
            "vinted_id": item["vinted_id"],
            "title": item["title"],
            "price": item["price"],
            "brand": item.get("brand"),
            "market": item["market"],
            "first_seen": item.get("first_seen"),
            "sold_at": item.get("sold_at"),
            "days_to_sell": days_to_sell
        })

    prices = [i["price"] for i in items if i["price"]]
    avg_price = sum(prices) / len(prices) if prices else 0
    avg_days = sum(days_to_sell_list) / len(days_to_sell_list) if days_to_sell_list else None

    return {
        "total_sold": len(items),
        "avg_price": round(avg_price, 2),
        "avg_days_to_sell": round(avg_days, 1) if avg_days else None,
        "items": sold_items
    }
