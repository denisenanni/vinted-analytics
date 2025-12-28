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
    period: str = Query("7d", description="Time period: 7d, 30d, 90d")
):
    """
    Get trending brands and price movements for a market/category.
    """
    result = analytics.get_trends(
        market=market,
        category=category,
        period=period
    )

    return TrendsResponse(
        market=market,
        category=category or "all",
        period=period,
        total_items=result["total_items"],
        avg_price=result["avg_price"],
        trending_brands=result["trending_brands"]
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


@router.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}
