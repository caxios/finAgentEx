"""
Analysis Router - /api/analyze endpoint
"""

from fastapi import APIRouter, HTTPException
import sys
import os

# Add parent directories to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from graph import analyze_stock
from backend.schemas.models import AnalyzeRequest, AnalyzeResponse

router = APIRouter(prefix="/api", tags=["analysis"])


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest):
    """
    Analyze a stock ticker using the Multi-Agent System.
    Returns trading decision with confidence and reasoning.
    """
    ticker = request.ticker.upper().strip()
    
    if not ticker:
        raise HTTPException(status_code=400, detail="Ticker is required")
    
    if len(ticker) > 10:
        raise HTTPException(status_code=400, detail="Invalid ticker format")
    
    try:
        print(f"\n{'='*60}")
        print(f"API Request: Analyzing {ticker}")
        print(f"{'='*60}")
        
        signal = analyze_stock(ticker)
        
        if signal:
            return AnalyzeResponse(
                ticker=ticker,
                decision=signal.decision.value,
                confidence=signal.confidence,
                timeframe=signal.timeframe,
                reasoning=signal.reasoning,
                risk_factors=signal.risk_factors,
                success=True
            )
        else:
            return AnalyzeResponse(
                ticker=ticker,
                decision="HOLD",
                confidence=0.3,
                timeframe="Unknown",
                reasoning="Analysis failed to produce a result",
                risk_factors="System error - manual review required",
                success=False,
                error="Analysis returned no signal"
            )
            
    except Exception as e:
        print(f"Error analyzing {ticker}: {e}")
        return AnalyzeResponse(
            ticker=ticker,
            decision="HOLD",
            confidence=0.0,
            timeframe="Unknown",
            reasoning=f"Error during analysis: {str(e)}",
            risk_factors="System error",
            success=False,
            error=str(e)
        )
