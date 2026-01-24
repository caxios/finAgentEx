"""
FastAPI Backend for Multi-Agent Stock Analysis System
Main application entry point with router registration.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import routers
from backend.routers import analysis, chart

app = FastAPI(
    title="Stock Analysis API",
    description="Multi-Agent System for Stock Analysis with Interactive Charts",
    version="2.0.0"
)

# CORS configuration for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(analysis.router)
app.include_router(chart.router)


@app.get("/")
async def root():
    return {
        "message": "Stock Analysis API",
        "version": "2.0.0",
        "status": "running",
        "endpoints": {
            "analyze": "POST /api/analyze",
            "ohlcv": "GET /api/ohlcv?ticker=AAPL&period=6mo",
            "news_by_date": "GET /api/news-by-date?ticker=AAPL&date=2025-01-20"
        }
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
