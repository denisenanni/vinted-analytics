from typing import List, Optional
from datetime import datetime, timedelta
from ..db import get_supabase


def lookup_items(
    brand: Optional[str] = None,
    category: Optional[str] = None,
    size: Optional[str] = None,
    market: Optional[str] = None,
    limit: int = 20
) -> dict:
    """Core lookup: find similar items and calculate stats."""
    supabase = get_supabase()

    # Build query
    query = supabase.table("items").select("*")

    if brand:
        query = query.ilike("brand", f"%{brand}%")
    if category:
        query = query.eq("category", category)
    if size:
        query = query.ilike("size", f"%{size}%")
    if market:
        query = query.eq("market", market)

    query = query.order("last_seen", desc=True).limit(500)
    result = query.execute()
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

    # Calculate stats
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

    # Best markets
    market_stats = {}
    for item in items:
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

    return {
        "total_items": len(items),
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

    market_data = []

    for market in markets:
        query = supabase.table("items").select("*").eq("market", market)

        if brand:
            query = query.ilike("brand", f"%{brand}%")
        if category:
            query = query.eq("category", category)

        result = query.limit(200).execute()
        items = result.data

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
    category: Optional[str] = None,
    period: str = "7d"
) -> dict:
    """Get trending brands and price movements."""
    supabase = get_supabase()

    # Calculate date threshold
    days = int(period.replace("d", "")) if period.endswith("d") else 7
    threshold = (datetime.now() - timedelta(days=days)).isoformat()

    query = supabase.table("items").select("*").eq("market", market).gte("last_seen", threshold)

    if category:
        query = query.eq("category", category)

    result = query.limit(1000).execute()
    items = result.data

    if not items:
        return {
            "total_items": 0,
            "avg_price": 0,
            "trending_brands": []
        }

    # Aggregate by brand
    brand_stats = {}
    for item in items:
        brand = item["brand"] or "Unknown"
        if brand not in brand_stats:
            brand_stats[brand] = {"count": 0, "prices": []}
        brand_stats[brand]["count"] += 1
        brand_stats[brand]["prices"].append(item["price"] or 0)

    # Build trending list
    trending = []
    for brand, stats in brand_stats.items():
        if stats["count"] >= 2:  # Minimum items to be considered
            avg_price = sum(stats["prices"]) / len(stats["prices"])
            trending.append({
                "brand": brand,
                "count": stats["count"],
                "avg_price": round(avg_price, 2),
                "trend": "stable"  # Would need historical data to calculate
            })

    trending.sort(key=lambda x: x["count"], reverse=True)

    prices = [i["price"] for i in items if i["price"]]
    avg_price = sum(prices) / len(prices) if prices else 0

    return {
        "total_items": len(items),
        "avg_price": round(avg_price, 2),
        "trending_brands": trending[:10]
    }


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
