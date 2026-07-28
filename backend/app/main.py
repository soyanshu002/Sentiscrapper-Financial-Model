from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import os
import uvicorn
import logging
from app.agents.orchestrator import MultiAgentOrchestrator
from app.reports.excel_generator import ExcelReportGenerator
from app.config import settings

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SentiScrapperAPI")

app = FastAPI(
    title="SentiScrapper Financial API",
    description="Multi-Agent Stock Forecasting & Sentiment Scrapper Engine",
    version="1.0.0"
)

# CORS Setup
allowed_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174"
]
if os.getenv("ALLOWED_ORIGINS"):
    allowed_origins.extend([o.strip() for o in os.getenv("ALLOWED_ORIGINS").split(",")])

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if os.getenv("ALLOW_ALL_ORIGINS", "true").lower() == "true" else allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalysisRequest(BaseModel):
    model_config = {"protected_namespaces": ()}
    ticker: str = Field(..., example="RELIANCE")
    model_type: str = Field("Random Forest", description="Model engine to use: 'Random Forest' or 'LSTM'")
    start_date: Optional[str] = Field("2015-01-01", description="Date string in format YYYY-MM-DD")

class AnalysisResponse(BaseModel):
    model_config = {"protected_namespaces": ()}
    ticker: str
    model_type: str
    average_sentiment: float
    sentiment_details: List[Dict[str, Any]]
    historical_data: List[Dict[str, Any]]
    forecast_data: List[Dict[str, Any]]
    metrics: Dict[str, Any]
    recommendation: str
    agent_logs: List[str]

@app.post("/api/analyze", response_model=AnalysisResponse)
@app.post("/api/analyze/", response_model=AnalysisResponse)
async def analyze_stock(request: AnalysisRequest):
    logger.info(f"Received analysis request for {request.ticker} using {request.model_type}")
    try:
        orchestrator = MultiAgentOrchestrator()
        result = await orchestrator.run_analysis(
            ticker=request.ticker,
            model_type=request.model_type,
            start_date=request.start_date
        )
        return result
    except Exception as e:
        logger.error(f"Error processing stock analysis for {request.ticker}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while compiling stock analysis: {str(e)}"
        )

@app.post("/api/export/excel")
@app.post("/api/export/excel/")
async def export_excel_report(data: Dict[str, Any]):
    try:
        excel_stream = ExcelReportGenerator.generate_workbook(data)
        ticker = data.get("ticker", "Stock")
        filename = f"SentiScrapper_Financial_Model_{ticker}.xlsx"
        return StreamingResponse(
            excel_stream,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        logger.error(f"Error generating Excel report: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate Excel report: {str(e)}"
        )

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "gpu_available": len(settings.is_reddit_configured()) > 0 or True, # Default to true
        "config": {
            "reddit_configured": settings.is_reddit_configured(),
            "twitter_configured": settings.is_twitter_configured(),
            "telegram_configured": settings.is_telegram_configured(),
            "alphavantage_configured": settings.is_alphavantage_configured(),
            "gemini_configured": settings.is_gemini_configured()
        }
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=True)
