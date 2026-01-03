from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# Error response models for OpenAPI documentation
class ErrorDetail(BaseModel):
    detail: str = Field(..., description="Human-readable error message", example="Resource not found")


class ValidationErrorDetail(BaseModel):
    loc: List[str] = Field(..., description="Location of the error in the request", example=["query", "market"])
    msg: str = Field(..., description="Error message", example="Field required")
    type: str = Field(..., description="Error type", example="value_error.missing")


class ValidationError(BaseModel):
    detail: List[ValidationErrorDetail] = Field(..., description="List of validation errors")


class ItemResponse(BaseModel):
    vinted_id: str = Field(..., description="Unique Vinted item ID", example="3456789012")
    title: str = Field(..., description="Item title/description", example="Zara floral summer dress size M")
    price: float = Field(..., description="Current price (in specified currency)", example=29.99)
    currency: str = Field("EUR", description="Currency code (EUR or PLN)", example="EUR")
    brand: Optional[str] = Field(None, description="Brand name if available", example="Zara")
    size: Optional[str] = Field(None, description="Size if available", example="M")
    url: str = Field(..., description="Vinted item URL")
    image_url: Optional[str] = Field(None, description="Item image URL")
    favorites: Optional[int] = Field(None, description="Number of favorites/likes", example=12)
    market: str = Field(..., description="Market code (IT, FR, DE, ES, NL, PL, BE, AT, PT)", example="IT")
    category: str = Field(..., description="Category path", example="women/dresses")
    status: str = Field(..., description="Item status: 'active' or 'sold'", example="active")
    first_seen: Optional[datetime] = Field(None, description="When item was first scraped")
    last_seen: Optional[datetime] = Field(None, description="When item was last seen by scraper")


class LookupResponse(BaseModel):
    query: dict = Field(..., description="Search parameters used", example={"brand": "Zara", "category": "women/dresses"})
    total_items: int = Field(..., description="Total items found matching criteria", example=156)
    avg_price: float = Field(..., description="Average price in EUR", example=32.45)
    min_price: float = Field(..., description="Minimum price found in EUR", example=15.00)
    max_price: float = Field(..., description="Maximum price found in EUR", example=89.99)
    price_range: str = Field(
        ...,
        description="Human-readable price range description",
        example="€15.00 - €89.99"
    )
    avg_time_to_sell_days: Optional[float] = Field(
        None,
        description="Average days to sell. Only available for sold items.",
        example=14.2
    )
    demand_score: str = Field(
        ...,
        description="Demand level: 'Low', 'Medium', or 'High' based on favorites and sell-through rate",
        example="High"
    )
    best_markets: List[dict] = Field(
        ...,
        description="Top markets ranked by sell-through rate and price"
    )
    recent_items: List[ItemResponse] = Field(
        ...,
        description="Sample of recent items matching criteria"
    )


class MarketComparison(BaseModel):
    market: str = Field(..., description="Market code", example="IT")
    item_count: int = Field(..., description="Total items found in this market", example=234)
    avg_price: float = Field(..., description="Average price in EUR", example=35.67)
    min_price: float = Field(..., description="Minimum price in EUR", example=15.00)
    max_price: float = Field(..., description="Maximum price in EUR", example=89.99)
    sold_count: int = Field(..., description="Number of sold items", example=87)
    avg_favorites: float = Field(
        ...,
        description="Average number of favorites per item (demand indicator)",
        example=8.3
    )


class CompareResponse(BaseModel):
    query: dict = Field(..., description="Search parameters used for comparison", example={"brand": "Zara", "category": "women/dresses"})
    markets: List[MarketComparison] = Field(..., description="Comparison data for each market")
    best_market: str = Field(
        ...,
        description="Recommended market based on price and demand",
        example="IT"
    )
    reason: str = Field(
        ...,
        description="Explanation of why this market was recommended",
        example="IT has highest average price (€35.67) with strong demand (8.3 avg favorites)."
    )


class TrendingItem(BaseModel):
    vinted_id: str = Field(..., description="Unique Vinted item ID", example="3456789012")
    title: str = Field(..., description="Item title", example="Zara floral summer dress")
    price: float = Field(..., description="Current price in EUR", example=29.99)
    brand: Optional[str] = Field(None, description="Brand name", example="Zara")
    url: Optional[str] = Field(None, description="Vinted item URL")
    image_url: Optional[str] = Field(None, description="Item image URL")
    favorites: int = Field(..., description="Number of users who favorited this item", example=87)
    market: str = Field(..., description="Market code", example="IT")
    category: Optional[str] = Field(None, description="Category path", example="women/dresses")


class TrendsResponse(BaseModel):
    market: str = Field(..., description="Market code analyzed", example="IT")
    categories: List[str] = Field(..., description="Categories included in analysis", example=["women/dresses", "women/tops"])
    period: str = Field(
        ...,
        description="Time period analyzed: '7d', '14d', '30d'",
        example="7d"
    )
    total_items: int = Field(..., description="Total items analyzed", example=1247)
    avg_price: float = Field(..., description="Average price of trending items in EUR", example=35.67)
    trending_items: List[TrendingItem] = Field(
        ...,
        description="Items sorted by popularity (favorites)"
    )
    has_more: bool = Field(
        False,
        description="Whether more results are available with pagination"
    )


class SoldItem(BaseModel):
    vinted_id: str = Field(..., description="Unique Vinted item ID", example="3456789012")
    title: str = Field(..., description="Item title", example="Zara summer dress")
    price: float = Field(..., description="Sold price in EUR", example=28.50)
    brand: Optional[str] = Field(None, description="Brand name", example="Zara")
    market: str = Field(..., description="Market code", example="IT")
    first_seen: Optional[datetime] = Field(None, description="When item was first scraped (listing date)")
    sold_at: Optional[datetime] = Field(
        None,
        description="When scraper detected item as sold (not exact sale time)"
    )
    days_to_sell: Optional[int] = Field(
        None,
        description="Days between first_seen and sold_at",
        example=12
    )


class SoldResponse(BaseModel):
    query: dict = Field(..., description="Search parameters used", example={"brand": "Zara", "market": "IT"})
    total_sold: int = Field(..., description="Total sold items found", example=87)
    avg_price: float = Field(..., description="Average selling price in EUR", example=32.45)
    avg_days_to_sell: Optional[float] = Field(
        None,
        description="Average days to sell. Only available when first_seen data exists.",
        example=14.2
    )
    items: List[SoldItem] = Field(..., description="Recently sold items")


class ScoreBreakdown(BaseModel):
    price: int = Field(
        ...,
        description="Price score (0-25). Based on average selling price compared to other markets.",
        ge=0,
        le=25,
        example=20
    )
    speed: int = Field(
        ...,
        description="Speed score (0-25). Based on average days to sell. Faster is better.",
        ge=0,
        le=25,
        example=18
    )
    demand: int = Field(
        ...,
        description="Demand score (0-25). Based on sell-through rate and favorites.",
        ge=0,
        le=25,
        example=22
    )
    competition: int = Field(
        ...,
        description="Competition score (0-25). Lower competition = higher score.",
        ge=0,
        le=25,
        example=18
    )


class PriceRange(BaseModel):
    min: float = Field(..., description="Minimum price in EUR", example=25.0)
    max: float = Field(..., description="Maximum price in EUR", example=35.0)


class SuggestedPrice(BaseModel):
    quick_sale: PriceRange = Field(
        ...,
        description="Price range for quick sale (25th percentile). Price lower for faster sale."
    )
    recommended: PriceRange = Field(
        ...,
        description="Recommended price range (median, 50th percentile). Best balance of speed and profit."
    )
    premium: PriceRange = Field(
        ...,
        description="Premium price range (75th percentile). Higher price, may take longer to sell."
    )
    data_points: int = Field(
        ...,
        description="Number of sold items used to calculate price suggestions",
        example=47
    )


class MarketProfitability(BaseModel):
    market: str = Field(..., description="Market code (IT, FR, DE, ES, NL, PL, BE, AT, PT)", example="IT")
    avg_selling_price: float = Field(..., description="Average selling price in EUR", example=45.99)
    suggested_price: Optional[SuggestedPrice] = Field(
        None,
        description="Price suggestions based on percentiles (25th, 50th, 75th). Only available if sufficient data."
    )
    avg_days_to_sell: Optional[float] = Field(
        None,
        description="Average days from listing to sale. Lower is better.",
        example=12.5
    )
    sell_through_rate: float = Field(
        ...,
        description="Percentage of items that sold (0-100)",
        ge=0,
        le=100,
        example=68.5
    )
    active_listings: int = Field(..., description="Current active listings in this market", example=234)
    sold_last_period: int = Field(..., description="Items sold in the last 30 days", example=87)
    competition_level: str = Field(
        ...,
        description="Competition level: 'Low', 'Medium', or 'High'",
        example="Medium"
    )
    total_data_points: int = Field(
        ...,
        description="Total items analyzed (active + sold)",
        example=321
    )
    profitability_score: int = Field(
        ...,
        description="Overall profitability score (0-100). Higher is better. Sum of price, speed, demand, and competition scores.",
        ge=0,
        le=100,
        example=78
    )
    score_breakdown: ScoreBreakdown = Field(
        ...,
        description="Breakdown of profitability score by category"
    )


class ProfitabilityRecommendation(BaseModel):
    best_market: Optional[str] = Field(
        None,
        description="Recommended market code for selling. None if insufficient data.",
        example="IT"
    )
    score: Optional[int] = Field(
        None,
        description="Profitability score of the best market (0-100)",
        ge=0,
        le=100,
        example=78
    )
    suggested_price: Optional[PriceRange] = Field(
        None,
        description="Recommended price range for the best market"
    )
    reason: str = Field(
        ...,
        description="Explanation of why this market was recommended or why no recommendation was made",
        example="IT has the highest profitability score with good demand and low competition."
    )


class MarketProfitabilityResponse(BaseModel):
    category: str = Field(..., description="Category analyzed (e.g., women/dresses)", example="women/dresses")
    brand: Optional[str] = Field(None, description="Brand filter applied, if any", example="Zara")
    markets: List[MarketProfitability] = Field(
        ...,
        description="Profitability analysis for each market"
    )
    recommendation: ProfitabilityRecommendation = Field(
        ...,
        description="Overall recommendation for best market to sell"
    )

# Timing Insights
class DayBreakdown(BaseModel):
    day: str = Field(..., description="Day of week (Monday, Tuesday, etc.)", example="Saturday")
    sales: int = Field(..., description="Number of sales on this day", example=145)
    percentage: float = Field(
        ...,
        description="Percentage of total weekly sales (0-100)",
        ge=0,
        le=100,
        example=20.5
    )


class CategoryTrend(BaseModel):
    category: str = Field(..., description="Category path (e.g., women/dresses)", example="women/dresses")
    this_week: int = Field(..., description="Sales this week", example=87)
    last_week: int = Field(..., description="Sales last week", example=62)
    change_percent: float = Field(
        ...,
        description="Percentage change from last week. Positive = trending up.",
        example=40.3
    )


class TimingInsightsResponse(BaseModel):
    market: str = Field(..., description="Market code analyzed", example="IT")
    best_day: Optional[str] = Field(
        None,
        description="Best day to list items (highest sales). None if insufficient data.",
        example="Saturday"
    )
    day_breakdown: List[DayBreakdown] = Field(
        ...,
        description="Sales breakdown by day of week"
    )
    trending_up: List[CategoryTrend] = Field(
        ...,
        description="Categories with increasing sales"
    )
    trending_down: List[CategoryTrend] = Field(
        ...,
        description="Categories with decreasing sales"
    )
    total_sales_analyzed: int = Field(
        ...,
        description="Total sales analyzed for this report",
        example=543
    )
    message: Optional[str] = Field(
        None,
        description="Additional context or warnings about data quality",
        example="Note: Timing data requires weeks of historical data for accuracy."
    )


# Arbitrage Finder
class ArbitrageOpportunity(BaseModel):
    category: str = Field(..., description="Category with price gap", example="women/dresses")
    buy_market: str = Field(..., description="Market where items are cheaper", example="PL")
    buy_price: float = Field(..., description="Average price in buy market (EUR)", example=25.50)
    buy_count: int = Field(..., description="Number of items available in buy market", example=34)
    sell_market: str = Field(..., description="Market where items sell for more", example="IT")
    sell_price: float = Field(..., description="Average price in sell market (EUR)", example=45.99)
    sell_count: int = Field(..., description="Number of items in sell market", example=28)
    price_gap_percent: float = Field(
        ...,
        description="Price difference as percentage of buy price",
        example=80.4
    )
    potential_profit: float = Field(
        ...,
        description="Potential profit per item (sell price - buy price) in EUR",
        example=20.49
    )


class ArbitrageResponse(BaseModel):
    opportunities: List[ArbitrageOpportunity] = Field(
        ...,
        description="List of arbitrage opportunities sorted by potential profit"
    )
    total_found: int = Field(..., description="Total opportunities found", example=12)
    min_gap_threshold: float = Field(
        ...,
        description="Minimum price gap percentage used for filtering",
        example=50.0
    )
    message: Optional[str] = Field(
        None,
        description="Additional context or warnings",
        example="Opportunities require buying in one market and selling in another."
    )