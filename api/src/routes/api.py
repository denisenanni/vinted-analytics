from fastapi import APIRouter, Query
from typing import Optional, List
from ..services import analytics
from ..models.schemas import (
    LookupResponse, CompareResponse, TrendsResponse, SoldResponse,
    MarketProfitabilityResponse, TimingInsightsResponse, ArbitrageResponse
)
from ..config.responses import STANDARD_RESPONSES

router = APIRouter(prefix="/api")

@router.get(
    "/timing-insights",
    response_model=TimingInsightsResponse,
    responses=STANDARD_RESPONSES,
    tags=["Trends & Insights"],
    summary="Best day to list items"
)
async def timing_insights(
    market: str = Query("IT", description="Market code"),
    category: Optional[str] = Query(None, description="Category filter (optional)")
):
    """
    Discover the best day of the week to list items for maximum sales.

    Analyzes sales patterns to provide:
    - Best day to list items (highest sales volume)
    - Day-by-day sales breakdown with percentages
    - Trending categories (week-over-week changes)

    Note: Timing insights require weeks of historical data for accuracy.
    Results improve over time as more data is collected.
    """
    result = analytics.get_timing_insights(
        category=category,
        market=market
    )
    return result


@router.get(
    "/arbitrage",
    response_model=ArbitrageResponse,
    responses=STANDARD_RESPONSES,
    tags=["Profitability"],
    summary="Cross-market price gaps"
)
async def arbitrage_opportunities(
    category: Optional[str] = Query(None, description="Category filter (optional)"),
    min_gap: float = Query(20.0, description="Minimum price gap percentage")
):
    """
    Find cross-market arbitrage opportunities where prices differ significantly.

    Identifies categories where you could potentially:
    - Buy items cheaper in one market
    - Sell them for more in another market

    Each opportunity includes:
    - Buy and sell markets
    - Price difference as percentage
    - Potential profit per item
    - Number of items available

    Note: Actual arbitrage requires purchasing, shipping, and relisting in another market.
    Use this for strategic insights on market pricing differences.
    """
    result = analytics.get_arbitrage_opportunities(
        category=category,
        min_price_gap_percent=min_gap
    )
    return result

@router.get(
    "/lookup",
    response_model=LookupResponse,
    responses=STANDARD_RESPONSES,
    tags=["Lookup & Search"],
    summary="Find similar items and pricing stats"
)
async def lookup(
    brand: Optional[str] = Query(None, description="Brand name (partial match)"),
    category: Optional[str] = Query(None, description="Category path, e.g. women/dresses"),
    size: Optional[str] = Query(None, description="Size (partial match)"),
    market: Optional[str] = Query(None, description="Market code, e.g. IT, FR, DE"),
    limit: int = Query(20, ge=1, le=100, description="Number of recent items to return")
):
    """
    Find similar items and get pricing statistics.

    Searches the database for items matching your criteria and returns:
    - Price statistics (avg, min, max)
    - Demand score based on favorites and sell-through rate
    - Best markets for selling ranked by profitability
    - Recent similar items with details

    At least one filter parameter (brand, category, size, or market) should be provided for meaningful results.
    """
    result = analytics.lookup_items(
        brand=brand,
        category=category,
        size=size,
        market=market,
        limit=limit
    )

    return LookupResponse(
        query={"brand": brand, "category": category, "size": size, "market": market},
        total_items=result["total_items"],
        avg_price=result["avg_price"],
        min_price=result["min_price"],
        max_price=result["max_price"],
        price_range=f"€{result['min_price']} - €{result['max_price']}",
        demand_score=result["demand_score"],
        best_markets=result["best_markets"],
        recent_items=result["recent_items"]
    )


@router.get(
    "/compare",
    response_model=CompareResponse,
    responses=STANDARD_RESPONSES,
    tags=["Lookup & Search"],
    summary="Compare same item across markets"
)
async def compare(
    brand: Optional[str] = Query(None, description="Brand name"),
    category: Optional[str] = Query(None, description="Category path"),
    markets: Optional[str] = Query(None, description="Comma-separated market codes, e.g. IT,FR,DE")
):
    """
    Compare the same item type across different markets.

    Analyzes price, demand, and availability across markets and recommends
    the best market for selling based on:
    - Average prices
    - Number of sold items
    - Average favorites (demand indicator)

    Returns detailed statistics for each market and identifies the most profitable option.
    """
    market_list = markets.split(",") if markets else None

    result = analytics.compare_markets(
        brand=brand,
        category=category,
        markets=market_list
    )

    return CompareResponse(
        query={"brand": brand, "category": category, "markets": markets},
        markets=result["markets"],
        best_market=result["best_market"],
        reason=result["reason"]
    )


@router.get(
    "/trends",
    response_model=TrendsResponse,
    responses=STANDARD_RESPONSES,
    tags=["Trends & Insights"],
    summary="Get trending items by popularity"
)
async def trends(
    market: str = Query("IT", description="Market code"),
    categories: Optional[str] = Query(None, description="Comma-separated category paths"),
    period: str = Query("7d", description="Time period: 7d, 30d, 90d"),
    limit: int = Query(20, ge=1, le=100, description="Number of trending items"),
    offset: int = Query(0, ge=0, description="Offset for pagination")
):
    """
    Get trending items ranked by popularity (favorites).

    Finds the most popular items in a market based on user favorites.
    Supports:
    - Multiple categories via comma-separated values
    - Different time periods (7d, 30d, 90d)
    - Pagination with limit and offset

    Useful for identifying what's currently popular to help price and position your items.
    """
    category_list = [c.strip() for c in categories.split(",")] if categories else []

    result = analytics.get_trends(
        market=market,
        categories=category_list if category_list else None,
        period=period,
        limit=limit,
        offset=offset
    )

    return TrendsResponse(
        market=market,
        categories=category_list if category_list else ["all"],
        period=period,
        total_items=result["total_items"],
        avg_price=result["avg_price"],
        trending_items=result["trending_items"],
        has_more=result["has_more"]
    )


@router.get(
    "/sold",
    response_model=SoldResponse,
    responses=STANDARD_RESPONSES,
    tags=["Trends & Insights"],
    summary="Get recently sold items"
)
async def sold(
    brand: Optional[str] = Query(None, description="Brand name"),
    category: Optional[str] = Query(None, description="Category path"),
    market: str = Query("IT", description="Market code"),
    period: str = Query("30d", description="Time period: 7d, 30d, 90d"),
    limit: int = Query(50, ge=1, le=200, description="Number of items to return")
):
    """
    Get recently sold items with time-to-sell statistics.

    Analyzes sold items to help understand:
    - How quickly items sell (days to sell)
    - What prices items actually sold for
    - Trends in specific brands or categories

    Note: sold_at timestamp indicates when the scraper detected the item as sold,
    not the exact moment of sale. Timing data improves with weeks of historical data.
    """
    result = analytics.get_sold_items(
        brand=brand,
        category=category,
        market=market,
        period=period,
        limit=limit
    )

    return SoldResponse(
        query={"brand": brand, "category": category, "market": market, "period": period},
        total_sold=result["total_sold"],
        avg_price=result["avg_price"],
        avg_days_to_sell=result["avg_days_to_sell"],
        items=result["items"]
    )


@router.get(
    "/market-profitability",
    response_model=MarketProfitabilityResponse,
    responses=STANDARD_RESPONSES,
    tags=["Profitability"],
    summary="Best markets for selling"
)
async def market_profitability(
    category: str = Query(..., description="Category path, e.g. women/trousers-and-leggings"),
    brand: Optional[str] = Query(None, description="Brand name (optional)")
):
    """
    Analyze which market is most profitable for selling a specific item type.

    Calculates a profitability score (0-100) for each market based on:
    - Price score: Average selling price compared to other markets (0-25 points)
    - Speed score: How quickly items sell (0-25 points)
    - Demand score: Sell-through rate and favorites (0-25 points)
    - Competition score: Number of active listings (0-25 points)

    Returns detailed analysis for each market plus a recommendation for the best market to sell.
    Includes suggested pricing based on percentiles (quick sale, recommended, premium).

    Use this endpoint to decide which country to list your item in for maximum profitability.
    """
    result = analytics.get_market_profitability(
        category=category,
        brand=brand
    )
    return result


@router.get(
    "/categories",
    responses=STANDARD_RESPONSES,
    tags=["Metadata"],
    summary="Available categories"
)
async def categories():
    """
    Get all available categories and markets.

    Returns:
    - Complete list of categories organized by section (women/men clothing, shoes, bags, accessories)
    - All supported market codes (IT, FR, DE, ES, NL, PL, BE, AT, PT)

    Use this to discover valid values for category and market parameters in other endpoints.
    """
    return {
        "categories": {
            "women_clothing": [
                "women/dresses", "women/tops-and-t-shirts", "women/jumpers-and-sweaters",
                "women/jeans", "women/trousers-and-leggings", "women/skirts",
                "women/shorts-and-cropped-trousers", "women/outerwear", "women/suits-and-blazers",
                "women/jumpsuits-and-playsuits", "women/activewear", "women/swimwear",
                "women/lingerie-and-nightwear", "women/maternity-clothes", "women/other-clothing"
            ],
            "women_shoes": [
                "women/boots", "women/heels", "women/trainers", "women/sandals",
                "women/ballerinas", "women/slippers", "women/sports-shoes",
                "women/flip-flops-and-slides", "women/espadrilles"
            ],
            "women_bags": [
                "women/handbags", "women/backpacks", "women/shoulder-bags", "women/tote-bags",
                "women/clutches", "women/wallets-and-purses", "women/bucket-bags",
                "women/hobo-bags", "women/beach-bags", "women/gym-bags", "women/bum-bags"
            ],
            "women_accessories": [
                "women/jewellery", "women/watches", "women/sunglasses", "women/belts",
                "women/hats-and-caps", "women/scarves-and-shawls", "women/gloves",
                "women/hair-accessories", "women/umbrellas", "women/keyrings"
            ],
            "men_clothing": [
                "men/tops-and-t-shirts", "men/jumpers-and-sweaters", "men/jeans",
                "men/trousers", "men/shorts", "men/outerwear", "men/suits-and-blazers",
                "men/activewear", "men/swimwear", "men/sleepwear", "men/socks-and-underwear"
            ],
            "men_shoes": [
                "men/boots", "men/trainers", "men/formal-shoes", "men/sandals",
                "men/sports-shoes", "men/slippers", "men/flip-flops-and-slides"
            ],
            "men_accessories": [
                "men/bags-and-backpacks", "men/jewellery", "men/watches", "men/sunglasses",
                "men/belts", "men/hats-and-caps", "men/scarves-and-shawls", "men/gloves",
                "men/ties-and-bow-ties", "men/braces-and-suspenders"
            ]
        },
        "markets": ["IT", "FR", "DE", "ES", "NL", "PL", "BE", "AT", "PT"]
    }


@router.get(
    "/hot-categories",
    responses=STANDARD_RESPONSES,
    tags=["Trends & Insights"],
    summary="Hottest category per market"
)
async def hot_categories():
    """
    Get the hottest (most trending) category for each market.

    Analyzes recent activity to identify the single most popular category in each market
    based on total favorites in the last 7 days.

    Returns one category per market showing where user interest is highest right now.
    Use this to identify trending categories for listing decisions.
    """
    return analytics.get_hot_categories()


@router.get(
    "/health",
    responses=STANDARD_RESPONSES,
    tags=["Metadata"],
    summary="Health check"
)
async def health():
    """
    API health check endpoint.

    Returns a simple status indicator to verify the API is running.
    Use this for monitoring and uptime checks.
    """
    return {"status": "ok"}


@router.get(
    "/db-stats",
    responses=STANDARD_RESPONSES,
    tags=["Metadata"],
    summary="Database statistics"
)
async def db_stats():
    """
    Get database statistics for debugging and monitoring data consistency.

    Provides comprehensive stats including:
    - Total items per market
    - Active vs sold item breakdown
    - Items with favorites > 0 (engagement indicator)
    - Recent items from last 7 days

    Use this endpoint for monitoring data collection health and debugging issues.
    """
    return analytics.get_db_stats()
