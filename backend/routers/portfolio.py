"""
Portfolio Router
API Endpoints for "My Portfolios" feature.
"""

from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from typing import List, Optional
from backend import portfolio_db, portfolio_analyser, portfolio_news

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])

# --- Models ---
class CreateCategoryRequest(BaseModel):
    name: str

class AddStockRequest(BaseModel):
    ticker: str

class AnalysisRequest(BaseModel):
    category_id: Optional[int] = None
    tickers: Optional[List[str]] = None  # Allow ad-hoc analysis too
    period: str = "6mo"

# --- Endpoints ---

@router.get("/categories")
async def get_categories():
    return portfolio_db.get_categories()

@router.post("/categories")
async def create_category(request: CreateCategoryRequest):
    if not request.name.strip():
        raise HTTPException(status_code=400, detail="Category name cannot be empty")
    
    cat_id = portfolio_db.create_category(request.name.strip())
    if cat_id == -1:
        raise HTTPException(status_code=400, detail="Category name already exists")
    
    return {"id": cat_id, "name": request.name, "success": True}

@router.delete("/categories/{category_id}")
async def delete_category(category_id: int):
    portfolio_db.delete_category(category_id)
    return {"success": True}

@router.get("/categories/{category_id}/stocks")
async def get_category_stocks(category_id: int):
    stocks = portfolio_db.get_stocks(category_id)
    return {"category_id": category_id, "stocks": stocks}

@router.post("/categories/{category_id}/stocks")
async def add_stock(category_id: int, request: AddStockRequest):
    success = portfolio_db.add_stock(category_id, request.ticker)
    if not success:
        return {"success": False, "message": "Stock already exists in this category"}
    return {"success": True, "ticker": request.ticker.upper()}

@router.delete("/categories/{category_id}/stocks/{ticker}")
async def delete_stock(category_id: int, ticker: str):
    portfolio_db.delete_stock(category_id, ticker)
    return {"success": True}

@router.post("/analysis")
async def analyze_portfolio(request: AnalysisRequest):
    tickers = []
    
    # Get tickers from category if ID provided
    if request.category_id:
        db_tickers = portfolio_db.get_stocks(request.category_id)
        tickers.extend(db_tickers)
    
    # Add ad-hoc tickers if provided
    if request.tickers:
        tickers.extend(request.tickers)
        
    # Remove duplicates
    tickers = list(set(tickers))
    
    if not tickers:
        return {"error": "No stocks found to analyze", "success": False}
        
    # Perform Analysis
    result = portfolio_analyser.fetch_and_normalize_data(tickers, request.period)
    
    if "error" in result:
        return {"success": False, "error": result["error"]}
        
    return {"success": True, "data": result}
    
@router.get("/categories/{category_id}/news")
async def get_portfolio_news(category_id: int, limit: int = 50):
    """Get aggregated news for all stocks in the category"""
    news_items = portfolio_news.fetch_portfolio_news(category_id)
    return {"category_id": category_id, "news": news_items[:limit]}
