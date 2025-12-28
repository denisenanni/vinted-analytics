from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes.api import router as api_router

app = FastAPI(
    title="Vinted Analytics API",
    description="Cross-market analytics for Vinted sellers",
    version="1.0.0"
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
