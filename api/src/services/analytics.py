from typing import List, Optional
from datetime import datetime, timedelta
from ..db import get_supabase


def percentile(data: List[float], p: float) -> float:
    """Calculate the p-th percentile of a list of numbers."""
    if not data:
        return 0
    sorted_data = sorted(data)
    k = (len(sorted_data) - 1) * p / 100
    f = int(k)
    c = f + 1 if f + 1 < len(sorted_data) else f
    if f == c:
        return sorted_data[f]
    return sorted_data[f] * (c - k) + sorted_data[c] * (k - f)


# Currency conversion constants
CURRENCY_RATES = {
    "PL": 4.3,  # 1 EUR = 4.3 PLN
    # Add more if needed (e.g., "CZ": 25.0 for Czech koruna)
}


def to_eur(price: float, market: str) -> float:
    """Convert price to EUR based on market."""
    if market in CURRENCY_RATES:
        return price / CURRENCY_RATES[market]
    return price  # Already in EUR


def get_market_profitability(
    category: str,
    brand: Optional[str] = None
) -> dict:
    """
    Calculate profitability score for each market to help decide where to sell.
    
    Considers:
    - Average selling price (higher = better)
    - Average days to sell (lower = better)
    - Sell-through rate (higher = better)
    - Competition level (lower active listings = better)
    
    Also provides suggested price ranges per market.
    """
    supabase = get_supabase()
    markets = ["IT", "FR", "DE", "ES", "NL", "PL", "BE", "AT", "PT"]
    
    # Get all items for this category across all markets
    query = supabase.table("items").select("*").eq("category", category)
    if brand:
        query = query.ilike("brand", f"%{brand}%")
    
    # Fetch with pagination to get all data
    all_items = []
    page_size = 1000
    offset = 0
    
    while True:
        result = query.range(offset, offset + page_size - 1).execute()
        batch = result.data
        if not batch:
            break
        all_items.extend(batch)
        offset += page_size
        if offset >= 50000:  # Safety limit
            break
    
    if not all_items:
        return {
            "category": category,
            "brand": brand,
            "markets": [],
            "recommendation": {
                "best_market": None,
                "reason": "No data available for this category"
            }
        }
    
    # Group items by market
    items_by_market = {m: [] for m in markets}
    for item in all_items:
        m = item.get("market")
        if m in items_by_market:
            items_by_market[m].append(item)
    
    # Calculate stats per market
    market_stats = []
    
    for market in markets:
        items = items_by_market[market]
        if not items:
            continue
        
        active = [i for i in items if i.get("status") == "active"]
        sold = [i for i in items if i.get("status") == "sold"]

        # Prices from sold items (actual selling prices) - convert to EUR
        sold_prices = [to_eur(i["price"], market) for i in sold if i.get("price") and i["price"] > 0]
        active_prices = [to_eur(i["price"], market) for i in active if i.get("price") and i["price"] > 0]

        # Use sold prices if available, otherwise active
        all_prices = sold_prices if sold_prices else active_prices

        avg_selling_price = sum(all_prices) / len(all_prices) if all_prices else 0
        
        # Calculate suggested price ranges (percentiles)
        if all_prices:
            suggested_price = {
                "quick_sale": {
                    "min": round(percentile(all_prices, 15), 2),
                    "max": round(percentile(all_prices, 35), 2)
                },
                "recommended": {
                    "min": round(percentile(all_prices, 40), 2),
                    "max": round(percentile(all_prices, 60), 2)
                },
                "premium": {
                    "min": round(percentile(all_prices, 65), 2),
                    "max": round(percentile(all_prices, 85), 2)
                },
                "data_points": len(all_prices)
            }
        else:
            suggested_price = None
        
        # Calculate days to sell
        days_to_sell_list = []
        for item in sold:
            first_seen = item.get("first_seen")
            sold_at = item.get("sold_at")
            if first_seen and sold_at:
                try:
                    fs = datetime.fromisoformat(first_seen.replace("Z", "+00:00"))
                    sa = datetime.fromisoformat(sold_at.replace("Z", "+00:00"))
                    days = (sa - fs).days
                    if 0 <= days <= 365:  # Reasonable range
                        days_to_sell_list.append(days)
                except:
                    pass
        
        avg_days_to_sell = (
            sum(days_to_sell_list) / len(days_to_sell_list)
            if days_to_sell_list else None
        )
        
        # Sell-through rate
        total_tracked = len(active) + len(sold)
        sell_through_rate = len(sold) / total_tracked if total_tracked > 0 else 0
        
        # Competition level
        active_count = len(active)
        if active_count < 50:
            competition = "low"
        elif active_count < 200:
            competition = "medium"
        else:
            competition = "high"
        
        market_stats.append({
            "market": market,
            "avg_selling_price": round(avg_selling_price, 2),
            "suggested_price": suggested_price,
            "avg_days_to_sell": round(avg_days_to_sell, 1) if avg_days_to_sell else None,
            "sell_through_rate": round(sell_through_rate, 3),
            "active_listings": active_count,
            "sold_last_period": len(sold),
            "competition_level": competition,
            "total_data_points": total_tracked
        })
    
    if not market_stats:
        return {
            "category": category,
            "brand": brand,
            "markets": [],
            "recommendation": {
                "best_market": None,
                "reason": "No data available for this category"
            }
        }
    
    # Calculate profitability scores
    prices = [m["avg_selling_price"] for m in market_stats if m["avg_selling_price"] > 0]
    max_price = max(prices) if prices else 1
    min_price = min(prices) if prices else 0
    price_range = max_price - min_price if max_price > min_price else 1
    
    days_list = [m["avg_days_to_sell"] for m in market_stats if m["avg_days_to_sell"] is not None]
    max_days = max(days_list) if days_list else 30
    min_days = min(days_list) if days_list else 1
    
    str_rates = [m["sell_through_rate"] for m in market_stats]
    max_str = max(str_rates) if str_rates else 1
    
    active_counts = [m["active_listings"] for m in market_stats]
    max_active = max(active_counts) if active_counts else 1
    
    for m in market_stats:
        # Price score: higher price = better (0-30 points)
        price_score = ((m["avg_selling_price"] - min_price) / price_range * 30) if price_range > 0 else 15
        
        # Speed score: faster = better (0-25 points)
        if m["avg_days_to_sell"] is not None and max_days > min_days:
            speed_score = ((max_days - m["avg_days_to_sell"]) / (max_days - min_days) * 25)
        else:
            speed_score = 12.5
        
        # Demand score: higher sell-through = better (0-25 points)
        demand_score = (m["sell_through_rate"] / max_str * 25) if max_str > 0 else 12.5
        
        # Competition score: fewer active = better (0-20 points)
        if max_active > 0:
            competition_score = ((max_active - m["active_listings"]) / max_active * 20)
        else:
            competition_score = 10
        
        m["profitability_score"] = round(price_score + speed_score + demand_score + competition_score)
        
        m["score_breakdown"] = {
            "price": round(price_score),
            "speed": round(speed_score),
            "demand": round(demand_score),
            "competition": round(competition_score)
        }
    
    # Sort by profitability score
    market_stats.sort(key=lambda x: x["profitability_score"], reverse=True)
    
    # Generate recommendation
    best = market_stats[0]
    reasons = []
    
    if best["avg_selling_price"] == max_price:
        reasons.append(f"highest avg price (€{best['avg_selling_price']})")
    if best["avg_days_to_sell"] and best["avg_days_to_sell"] == min_days:
        reasons.append(f"fastest sales ({best['avg_days_to_sell']} days avg)")
    if best["sell_through_rate"] == max_str:
        reasons.append(f"best sell-through rate ({best['sell_through_rate']*100:.1f}%)")
    if best["competition_level"] == "low":
        reasons.append("low competition")
    
    if not reasons:
        reasons.append(f"best overall balance (score: {best['profitability_score']})")
    
    # Add suggested price to recommendation
    rec_price = None
    if best.get("suggested_price"):
        rec_price = best["suggested_price"]["recommended"]
    
    return {
        "category": category,
        "brand": brand,
        "markets": market_stats,
        "recommendation": {
            "best_market": best["market"],
            "score": best["profitability_score"],
            "suggested_price": rec_price,
            "reason": f"Best market: {', '.join(reasons)}"
        }
    }


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

    # Convert prices to EUR
    prices = [to_eur(i["price"], i["market"]) for i in items if i["price"]]
    avg_price = sum(prices) / len(prices) if prices else 0
    min_price = min(prices) if prices else 0
    max_price = max(prices) if prices else 0

    avg_favorites = sum(i["favorites"] or 0 for i in items) / len(items)
    if avg_favorites > 10:
        demand_score = "high"
    elif avg_favorites > 5:
        demand_score = "medium"
    else:
        demand_score = "low"

    # Skip "Best Markets" calculation if market is already filtered
    # (showing one market as "best" when it's the only one is redundant)
    if market:
        best_markets = []
        # Get actual count from database (not limited to 500)
        count_query = supabase.table("items").select("*", count="exact", head=True)
        count_query = apply_filters(count_query)
        count_result = count_query.execute()
        total_items = count_result.count
    else:
        cache_key = f"{brand or ''}:{category or ''}:{size or ''}:{market or ''}"
        cached = _market_stats_cache.get(cache_key)

        if cached and datetime.now() < cached["expires_at"]:
            best_markets = cached["best_markets"]
            total_items = cached["total_items"]
        else:
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

                if offset >= 50000:
                    break

            market_stats = {}
            for item in all_market_items:
                m = item["market"]
                if m not in market_stats:
                    market_stats[m] = {"count": 0, "prices": [], "favorites": []}
                market_stats[m]["count"] += 1
                # Convert price to EUR before storing
                market_stats[m]["prices"].append(to_eur(item["price"] or 0, m))
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

            # Get actual count from database
            count_query = supabase.table("items").select("*", count="exact", head=True)
            count_query = apply_filters(count_query)
            count_result = count_query.execute()
            total_items = count_result.count

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

    query = supabase.table("items").select("*").in_("market", markets)

    if brand:
        query = query.ilike("brand", f"%{brand}%")
    if category:
        query = query.eq("category", category)

    result = query.limit(2000).execute()
    all_items = result.data

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
            # Convert prices to EUR
            prices = [to_eur(i["price"], market) for i in items if i["price"]]
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

    if market_data:
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

    days = int(period.replace("d", "")) if period.endswith("d") else 7
    threshold = (datetime.now() - timedelta(days=days)).isoformat()

    query = supabase.table("items").select("*", count="exact").eq("market", market).gte("last_seen", threshold)

    if categories and len(categories) > 0:
        query = query.in_("category", categories)

    query = query.gt("favorites", 0)

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

    # Convert prices to EUR
    prices = [to_eur(i["price"], market) for i in items if i["price"]]
    avg_price = sum(prices) / len(prices) if prices else 0

    trending_items = []
    for item in items:
        trending_items.append({
            "vinted_id": item["vinted_id"],
            "title": item["title"],
            "price": to_eur(item["price"], market) if item["price"] else 0,
            "brand": item.get("brand"),
            "url": item.get("url"),
            "image_url": item.get("image_url"),
            "favorites": item.get("favorites") or 0,
            "market": item["market"],
            "category": item.get("category"),
            "first_seen": item.get("first_seen")
        })

    return {
        "total_items": total_count,
        "avg_price": round(avg_price, 2),
        "trending_items": trending_items,
        "has_more": offset + limit < total_count
    }


def get_db_stats() -> dict:
    """Get database statistics for debugging and consistency checks."""
    supabase = get_supabase()

    # Get counts by market and status with pagination
    all_items = []
    page_size = 1000
    offset = 0
    while True:
        result = supabase.table("items").select("market, status, favorites")\
            .range(offset, offset + page_size - 1).execute()
        if not result.data:
            break
        all_items.extend(result.data)
        offset += page_size
        if offset >= 50000:  # Safety limit
            break

    items = all_items
    
    stats_by_market = {}
    for item in items:
        market = item.get("market")
        status = item.get("status")
        favorites = item.get("favorites") or 0
        
        if market not in stats_by_market:
            stats_by_market[market] = {
                "total": 0,
                "active": 0,
                "sold": 0,
                "with_favorites": 0
            }
        
        stats_by_market[market]["total"] += 1
        if status == "active":
            stats_by_market[market]["active"] += 1
        elif status == "sold":
            stats_by_market[market]["sold"] += 1
        if favorites > 0:
            stats_by_market[market]["with_favorites"] += 1
    
    # Get recent items (last 7 days) with favorites
    threshold = (datetime.now() - timedelta(days=7)).isoformat()
    recent_result = supabase.table("items")\
        .select("market", count="exact")\
        .gte("last_seen", threshold)\
        .gt("favorites", 0)\
        .execute()
    
    recent_by_market = {}
    if recent_result.data:
        for item in recent_result.data:
            market = item.get("market")
            recent_by_market[market] = recent_by_market.get(market, 0) + 1
    
    return {
        "total_items": len(items),
        "by_market": stats_by_market,
        "recent_with_favorites_7d": recent_by_market,
        "markets_scraped": list(stats_by_market.keys())
    }


def get_hot_categories() -> dict:
    """Get the hottest (most trending) category for each market."""
    global _hot_categories_cache

    if (_hot_categories_cache["data"] is not None
        and _hot_categories_cache["expires_at"]
        and datetime.now() < _hot_categories_cache["expires_at"]):
        return _hot_categories_cache["data"]

    supabase = get_supabase()
    markets = ["IT", "FR", "DE", "ES", "NL", "PL", "BE", "AT", "PT"]

    allowed_categories = {
        "women/dresses", "women/tops-and-t-shirts", "women/jumpers-and-sweaters",
        "women/jeans", "women/trousers-and-leggings", "women/skirts",
        "women/shorts-and-cropped-trousers", "women/outerwear", "women/suits-and-blazers",
        "women/jumpsuits-and-playsuits", "women/activewear", "women/swimwear",
        "women/lingerie-and-nightwear", "women/maternity-clothes", "women/other-clothing",
        "women/boots", "women/heels", "women/trainers", "women/sandals",
        "women/ballerinas", "women/slippers", "women/sports-shoes",
        "women/flip-flops-and-slides", "women/espadrilles",
        "women/handbags", "women/backpacks", "women/shoulder-bags", "women/tote-bags",
        "women/clutches", "women/wallets-and-purses", "women/bucket-bags",
        "women/hobo-bags", "women/beach-bags", "women/gym-bags", "women/bum-bags",
        "women/jewellery", "women/watches", "women/sunglasses", "women/belts",
        "women/hats-and-caps", "women/scarves-and-shawls", "women/gloves",
        "women/hair-accessories", "women/umbrellas", "women/keyrings",
        "men/tops-and-t-shirts", "men/jumpers-and-sweaters", "men/jeans",
        "men/trousers", "men/shorts", "men/outerwear", "men/suits-and-blazers",
        "men/activewear", "men/swimwear", "men/sleepwear", "men/socks-and-underwear",
        "men/boots", "men/trainers", "men/formal-shoes", "men/sandals",
        "men/sports-shoes", "men/slippers", "men/flip-flops-and-slides",
        "men/bags-and-backpacks", "men/jewellery", "men/watches", "men/sunglasses",
        "men/belts", "men/hats-and-caps", "men/scarves-and-shawls", "men/gloves",
        "men/ties-and-bow-ties", "men/braces-and-suspenders",
    }

    threshold = (datetime.now() - timedelta(days=7)).isoformat()

    all_items = []
    page_size = 1000
    offset = 0

    while True:
        result = supabase.table("items")\
            .select("market, category, favorites")\
            .in_("market", markets)\
            .gte("last_seen", threshold)\
            .gt("favorites", 0)\
            .range(offset, offset + page_size - 1)\
            .execute()

        batch = result.data
        if not batch:
            break

        all_items.extend(batch)
        offset += page_size

        if offset >= 100000:
            break

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

    hot_categories = {}
    for market, category_stats in market_category_stats.items():
        if category_stats:
            hot_cat = max(category_stats.items(), key=lambda x: x[1]["total_favorites"])
            hot_categories[market] = {
                "category": hot_cat[0],
                "total_favorites": hot_cat[1]["total_favorites"],
                "item_count": hot_cat[1]["count"]
            }

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

    # Get actual total count (not limited to 50)
    count_query = supabase.table("items")\
        .select("*", count="exact", head=True)\
        .eq("market", market)\
        .eq("status", "sold")\
        .gte("sold_at", threshold)

    if brand:
        count_query = count_query.ilike("brand", f"%{brand}%")
    if category:
        count_query = count_query.eq("category", category)

    count_result = count_query.execute()
    total_sold = count_result.count

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
            "price": to_eur(item["price"], market) if item["price"] else 0,
            "brand": item.get("brand"),
            "market": item["market"],
            "first_seen": item.get("first_seen"),
            "sold_at": item.get("sold_at"),
            "days_to_sell": days_to_sell
        })

    # Convert prices to EUR
    prices = [to_eur(i["price"], market) for i in items if i["price"]]
    avg_price = sum(prices) / len(prices) if prices else 0
    avg_days = sum(days_to_sell_list) / len(days_to_sell_list) if days_to_sell_list else None

    # Get category breakdown for all sold items in this period (paginated)
    category_breakdown = {}
    all_sold_items = []
    page_size = 1000
    offset = 0

    while offset < 50000:  # Safety limit
        breakdown_query = supabase.table("items")\
            .select("category")\
            .eq("market", market)\
            .eq("status", "sold")\
            .gte("sold_at", threshold)\
            .range(offset, offset + page_size - 1)

        if brand:
            breakdown_query = breakdown_query.ilike("brand", f"%{brand}%")
        if category:
            breakdown_query = breakdown_query.eq("category", category)

        breakdown_result = breakdown_query.execute()
        if not breakdown_result.data:
            break

        all_sold_items.extend(breakdown_result.data)
        offset += page_size

    # Count by category
    for item in all_sold_items:
        cat = item.get("category") or "Unknown"
        category_breakdown[cat] = category_breakdown.get(cat, 0) + 1

    # Convert to percentage
    total_for_breakdown = len(all_sold_items)
    category_percentages = []
    if total_for_breakdown > 0:
        for cat, count in sorted(category_breakdown.items(), key=lambda x: x[1], reverse=True):
            category_percentages.append({
                "category": cat,
                "count": count,
                "percentage": round((count / total_for_breakdown) * 100, 1)
            })

    return {
        "total_sold": total_sold,
        "avg_price": round(avg_price, 2),
        "avg_days_to_sell": round(avg_days, 1) if avg_days else None,
        "category_breakdown": category_percentages,
        "items": sold_items
    }


def get_timing_insights(
    category: Optional[str] = None,
    market: str = "IT"
) -> dict:
    """
    Analyze timing patterns for sales.
    - Best day of week to list
    - Trending categories (up/down vs last period)
    """
    supabase = get_supabase()
    
    # Get sold items from last 30 days
    threshold_30d = (datetime.now() - timedelta(days=30)).isoformat()
    threshold_7d = (datetime.now() - timedelta(days=7)).isoformat()
    threshold_14d = (datetime.now() - timedelta(days=14)).isoformat()
    
    query = supabase.table("items")\
        .select("sold_at, category, price")\
        .eq("market", market)\
        .eq("status", "sold")\
        .gte("sold_at", threshold_30d)
    
    if category:
        query = query.eq("category", category)
    
    result = query.limit(5000).execute()
    sold_items = result.data
    
    if not sold_items:
        return {
            "market": market,
            "best_day": None,
            "day_breakdown": [],
            "trending_up": [],
            "trending_down": [],
            "message": "Not enough sold data yet"
        }
    
    # Analyze by day of week
    day_counts = {i: 0 for i in range(7)}  # 0=Monday, 6=Sunday
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    
    for item in sold_items:
        sold_at = item.get("sold_at")
        if sold_at:
            try:
                dt = datetime.fromisoformat(sold_at.replace("Z", "+00:00"))
                day_counts[dt.weekday()] += 1
            except:
                pass
    
    total_sales = sum(day_counts.values())
    day_breakdown = []
    for i, name in enumerate(day_names):
        count = day_counts[i]
        pct = round(count / total_sales * 100, 1) if total_sales > 0 else 0
        day_breakdown.append({
            "day": name,
            "sales": count,
            "percentage": pct
        })
    
    best_day_idx = max(day_counts, key=day_counts.get)
    best_day = day_names[best_day_idx]
    
    # Check if data is too skewed (one day has >50% of sales or less than 5 days have data)
    max_day_pct = max(d["percentage"] for d in day_breakdown)
    days_with_sales = sum(1 for d in day_breakdown if d["sales"] > 0)
    
    if days_with_sales < 5 or max_day_pct > 50:
        # Not enough spread - return data but no recommendation
        best_day = None
        message = "Not enough data spread across days yet. Need more time to analyze patterns."
    else:
        message = None
    
    # Analyze trending categories (this week vs last week)
    this_week = [i for i in sold_items if i.get("sold_at") and i["sold_at"] >= threshold_7d]
    last_week = [i for i in sold_items if i.get("sold_at") and threshold_14d <= i["sold_at"] < threshold_7d]
    
    def count_by_category(items):
        counts = {}
        for item in items:
            cat = item.get("category")
            if cat:
                counts[cat] = counts.get(cat, 0) + 1
        return counts
    
    this_week_counts = count_by_category(this_week)
    last_week_counts = count_by_category(last_week)
    
    # Calculate trends
    trends = []
    all_cats = set(this_week_counts.keys()) | set(last_week_counts.keys())
    
    for cat in all_cats:
        this_count = this_week_counts.get(cat, 0)
        last_count = last_week_counts.get(cat, 0)
        
        if last_count > 0:
            change_pct = round((this_count - last_count) / last_count * 100, 1)
        elif this_count > 0:
            change_pct = 100  # New category
        else:
            change_pct = 0
        
        if this_count >= 3 or last_count >= 3:  # Min threshold
            trends.append({
                "category": cat,
                "this_week": this_count,
                "last_week": last_count,
                "change_percent": change_pct
            })
    
    # Sort and split into up/down
    trending_up = sorted([t for t in trends if t["change_percent"] > 10], 
                         key=lambda x: x["change_percent"], reverse=True)[:5]
    trending_down = sorted([t for t in trends if t["change_percent"] < -10], 
                           key=lambda x: x["change_percent"])[:5]
    
    return {
        "market": market,
        "best_day": best_day,
        "day_breakdown": day_breakdown,
        "trending_up": trending_up,
        "trending_down": trending_down,
        "total_sales_analyzed": total_sales,
        "message": message
    }


def get_arbitrage_opportunities(
    category: Optional[str] = None,
    min_price_gap_percent: float = 20.0
) -> dict:
    """
    Find cross-market arbitrage opportunities.
    Items/categories that are cheap in one market but expensive in another.
    """
    supabase = get_supabase()

    # Get recent active items
    threshold = (datetime.now() - timedelta(days=14)).isoformat()
    
    query = supabase.table("items")\
        .select("market, category, brand, price")\
        .eq("status", "active")\
        .gte("last_seen", threshold)
    
    if category:
        query = query.eq("category", category)
    
    # Fetch all items
    all_items = []
    page_size = 1000
    offset = 0
    
    while True:
        result = query.range(offset, offset + page_size - 1).execute()
        batch = result.data
        if not batch:
            break
        all_items.extend(batch)
        offset += page_size
        if offset >= 50000:
            break
    
    if not all_items:
        return {
            "opportunities": [],
            "message": "Not enough data"
        }
    
    # Group by category and calculate avg price per market (converted to EUR)
    category_market_prices = {}
    
    for item in all_items:
        cat = item.get("category")
        market = item.get("market")
        price = item.get("price", 0)
        
        if not cat or not market or price <= 0:
            continue
        
        # Convert to EUR
        price_eur = to_eur(price, market)
        
        if cat not in category_market_prices:
            category_market_prices[cat] = {}
        if market not in category_market_prices[cat]:
            category_market_prices[cat][market] = []
        
        category_market_prices[cat][market].append(price_eur)
    
    # Find opportunities
    opportunities = []
    
    for cat, market_prices in category_market_prices.items():
        if len(market_prices) < 2:
            continue
        
        # Calculate averages
        market_avgs = {}
        for market, prices in market_prices.items():
            if len(prices) >= 3:  # Need minimum data
                market_avgs[market] = {
                    "avg_price": round(sum(prices) / len(prices), 2),
                    "count": len(prices)
                }
        
        if len(market_avgs) < 2:
            continue
        
        # Find min and max markets
        sorted_markets = sorted(market_avgs.items(), key=lambda x: x[1]["avg_price"])
        cheapest = sorted_markets[0]
        most_expensive = sorted_markets[-1]
        
        cheap_price = cheapest[1]["avg_price"]
        expensive_price = most_expensive[1]["avg_price"]
        
        if cheap_price > 0:
            price_gap_pct = round((expensive_price - cheap_price) / cheap_price * 100, 1)
            
            if price_gap_pct >= min_price_gap_percent:
                opportunities.append({
                    "category": cat,
                    "buy_market": cheapest[0],
                    "buy_price": cheap_price,
                    "buy_count": cheapest[1]["count"],
                    "sell_market": most_expensive[0],
                    "sell_price": expensive_price,
                    "sell_count": most_expensive[1]["count"],
                    "price_gap_percent": price_gap_pct,
                    "potential_profit": round(expensive_price - cheap_price, 2)
                })
    
    # Sort by potential profit percentage
    opportunities.sort(key=lambda x: x["price_gap_percent"], reverse=True)
    
    return {
        "opportunities": opportunities[:20],  # Top 20
        "total_found": len(opportunities),
        "min_gap_threshold": min_price_gap_percent
    }