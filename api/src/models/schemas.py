from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ItemResponse(BaseModel):
    vinted_id: str
    title: str
    price: float
    currency: str = "EUR"
    brand: Optional[str] = None
    size: Optional[str] = None
    url: str
    image_url: Optional[str] = None
    favorites: Optional[int] = None
    market: str
    category: str
    status: str
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None


class LookupResponse(BaseModel):
    query: dict
    total_items: int
    avg_price: float
    min_price: float
    max_price: float
    price_range: str
    avg_time_to_sell_days: Optional[float] = None
    demand_score: str
    best_markets: List[dict]
    recent_items: List[ItemResponse]


class MarketComparison(BaseModel):
    market: str
    item_count: int
    avg_price: float
    min_price: float
    max_price: float
    sold_count: int
    avg_favorites: float


class CompareResponse(BaseModel):
    query: dict
    markets: List[MarketComparison]
    best_market: str
    reason: str


class TrendingItem(BaseModel):
    vinted_id: str
    title: str
    price: float
    brand: Optional[str] = None
    url: Optional[str] = None
    image_url: Optional[str] = None
    favorites: int
    market: str
    category: Optional[str] = None


class TrendsResponse(BaseModel):
    market: str
    categories: List[str]
    period: str
    total_items: int
    avg_price: float
    trending_items: List[TrendingItem]
    has_more: bool = False


class SoldItem(BaseModel):
    vinted_id: str
    title: str
    price: float
    brand: Optional[str]
    market: str
    first_seen: Optional[datetime]
    sold_at: Optional[datetime]
    days_to_sell: Optional[int]


class SoldResponse(BaseModel):
    query: dict
    total_sold: int
    avg_price: float
    avg_days_to_sell: Optional[float]
    items: List[SoldItem]


class ScoreBreakdown(BaseModel):
    price: int
    speed: int
    demand: int
    competition: int


class PriceRange(BaseModel):
    min: float
    max: float


class SuggestedPrice(BaseModel):
    quick_sale: PriceRange
    recommended: PriceRange
    premium: PriceRange
    data_points: int


class MarketProfitability(BaseModel):
    market: str
    avg_selling_price: float
    suggested_price: Optional[SuggestedPrice] = None
    avg_days_to_sell: Optional[float]
    sell_through_rate: float
    active_listings: int
    sold_last_period: int
    competition_level: str
    total_data_points: int
    profitability_score: int
    score_breakdown: ScoreBreakdown


class ProfitabilityRecommendation(BaseModel):
    best_market: Optional[str]
    score: Optional[int] = None
    suggested_price: Optional[PriceRange] = None
    reason: str


class MarketProfitabilityResponse(BaseModel):
    category: str
    brand: Optional[str]
    markets: List[MarketProfitability]
    recommendation: ProfitabilityRecommendation

# Timing Insights
class DayBreakdown(BaseModel):
    day: str
    sales: int
    percentage: float


class CategoryTrend(BaseModel):
    category: str
    this_week: int
    last_week: int
    change_percent: float


class TimingInsightsResponse(BaseModel):
    market: str
    best_day: Optional[str]
    day_breakdown: List[DayBreakdown]
    trending_up: List[CategoryTrend]
    trending_down: List[CategoryTrend]
    total_sales_analyzed: int
    message: Optional[str] = None


# Arbitrage Finder
class ArbitrageOpportunity(BaseModel):
    category: str
    buy_market: str
    buy_price: float
    buy_count: int
    sell_market: str
    sell_price: float
    sell_count: int
    price_gap_percent: float
    potential_profit: float


class ArbitrageResponse(BaseModel):
    opportunities: List[ArbitrageOpportunity]
    total_found: int
    min_gap_threshold: float
    message: Optional[str] = None