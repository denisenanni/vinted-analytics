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
    demand_score: str  # low, medium, high
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


class TrendData(BaseModel):
    brand: str
    count: int
    avg_price: float
    trend: str  # up, down, stable


class TrendsResponse(BaseModel):
    market: str
    category: str
    period: str
    total_items: int
    avg_price: float
    trending_brands: List[TrendData]


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
