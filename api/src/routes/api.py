from fastapi import APIRouter, Query
from typing import Optional, List
from ..services import analytics
from ..models.schemas import LookupResponse, CompareResponse, TrendsResponse, SoldResponse

router = APIRouter(prefix="/api", tags=["analytics"])


@router.get("/lookup", response_model=LookupResponse)
async def lookup(
    brand: Optional[str] = Query(None, description="Brand name (partial match)"),
    category: Optional[str] = Query(None, description="Category path, e.g. women/dresses"),
    size: Optional[str] = Query(None, description="Size (partial match)"),
    market: Optional[str] = Query(None, description="Market code, e.g. IT, FR, DE"),
    limit: int = Query(20, ge=1, le=100, description="Number of recent items to return")
):
    """
    Core lookup endpoint: find similar items and get pricing stats.

    Returns average price, price range, demand score, best markets, and recent items.
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


@router.get("/compare", response_model=CompareResponse)
async def compare(
    brand: Optional[str] = Query(None, description="Brand name"),
    category: Optional[str] = Query(None, description="Category path"),
    markets: Optional[str] = Query(None, description="Comma-separated market codes, e.g. IT,FR,DE")
):
    """
    Compare same item type across markets.

    Returns stats per market and identifies the best market for selling.
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


@router.get("/trends", response_model=TrendsResponse)
async def trends(
    market: str = Query("IT", description="Market code"),
    category: Optional[str] = Query(None, description="Category path"),
    period: str = Query("7d", description="Time period: 7d, 30d, 90d"),
    limit: int = Query(20, ge=1, le=50, description="Number of trending items")
):
    """
    Get trending items (by favorites/popularity) for a market/category.
    """
    result = analytics.get_trends(
        market=market,
        category=category,
        period=period,
        limit=limit
    )

    return TrendsResponse(
        market=market,
        category=category or "all",
        period=period,
        total_items=result["total_items"],
        avg_price=result["avg_price"],
        trending_items=result["trending_items"]
    )


@router.get("/sold", response_model=SoldResponse)
async def sold(
    brand: Optional[str] = Query(None, description="Brand name"),
    category: Optional[str] = Query(None, description="Category path"),
    market: str = Query("IT", description="Market code"),
    period: str = Query("30d", description="Time period: 7d, 30d, 90d"),
    limit: int = Query(50, ge=1, le=200, description="Number of items to return")
):
    """
    Get recently sold items with time-to-sell stats.
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


@router.get("/categories")
async def categories():
    """
    Get all available categories organized by section.
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


@router.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}
