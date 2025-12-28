from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class VintedItem(BaseModel):
    vinted_id: str
    title: str
    price: float
    currency: str = "EUR"
    brand: Optional[str] = None
    size: Optional[str] = None
    url: str
    image_url: Optional[str] = None
    favorites: Optional[int] = None
    market: str = "IT"
    category: str
    scraped_at: datetime = datetime.now()

    class Config:
        from_attributes = True
