import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes.api import router as api_router
from .config.openapi_tags import OPENAPI_TAGS

# Documentation configuration
DOCS_ENABLED = os.getenv("DOCS_ENABLED", "true").lower() == "true"

app = FastAPI(
    title="Vinted Analytics API",
    description="""
    Cross-market analytics platform for Vinted sellers.

    Track items across 9 European markets (IT, FR, DE, ES, NL, PL, BE, AT, PT),
    analyze pricing trends, and get data-driven selling recommendations.

    ## Features

    - **Lookup & Search**: Find similar items and pricing statistics
    - **Trends & Insights**: Discover trending items and optimal selling times
    - **Profitability Analysis**: Determine best markets for your items
    - **Arbitrage Opportunities**: Find cross-market price gaps

    ## Data Notes

    - Prices are normalized to EUR (Poland uses PLN conversion: 1 EUR = 4.3 PLN)
    - `sold_at` timestamp indicates when scraper detected sale (not exact sale time)
    - Timing insights require weeks of data for accuracy
    """,
    version="1.0.0",
    contact={
        "name": "Vinted Analytics"
    },
    license_info={
        "name": "MIT"
    },
    openapi_tags=OPENAPI_TAGS,
    docs_url="/docs" if DOCS_ENABLED else None,
    redoc_url="/redoc" if DOCS_ENABLED else None,
    openapi_url="/openapi.json" if DOCS_ENABLED else None
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(api_router)


@app.get("/")
async def root():
    return {
        "name": "Vinted Analytics API",
        "version": "1.0.0",
        "docs": "/docs"
    }
