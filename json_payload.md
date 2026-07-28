Request JSON Payload (Sent by Frontend)

{
  "ticker": "RELIANCE",
  "model_type": "Random Forest",
  "start_date": "2015-01-01"
}


Response JSON Payload (Returned by Backend)

{
  "ticker": "RELIANCE",
  "model_type": "Random Forest",
  "average_sentiment": 0.2458,
  "sentiment_details": [
    {
      "text": "Reliance Q1 results show strong digital and retail growth, bullish long term.",
      "source": "Reddit",
      "compound": 0.5859
    },
    {
      "text": "Reliance stock consolidating near key 3000 support level.",
      "source": "Twitter",
      "compound": 0.1263
    },
    {
      "text": "Swing target achieved for RELIANCE.NS, accumulation recommended on dips.",
      "source": "Telegram",
      "compound": 0.3612
    },
    {
      "text": "Reliance Retail expands store network across tier-2 cities.",
      "source": "News",
      "compound": 0.2960
    }
  ],
  "historical_data": [
    {
      "Date": "2026-07-24",
      "Open": 3020.0,
      "High": 3055.0,
      "Low": 3012.0,
      "Close": 3045.5,
      "RSI": 58.42,
      "MACD": 12.35,
      "Weighted_Sentiment": 0.2145
    },
    {
      "Date": "2026-07-25",
      "Open": 3045.5,
      "High": 3080.0,
      "Low": 3040.0,
      "Close": 3072.0,
      "RSI": 62.15,
      "MACD": 15.80,
      "Weighted_Sentiment": 0.2458
    }
  ],
  "forecast_data": [
    {
      "Date": "2026-07-28",
      "Predicted_Close": 3085.40
    },
    {
      "Date": "2026-07-29",
      "Predicted_Close": 3098.20
    },
    {
      "Date": "2026-07-30",
      "Predicted_Close": 3110.50
    },
    {
      "Date": "2026-07-31",
      "Predicted_Close": 3122.80
    },
    {
      "Date": "2026-08-01",
      "Predicted_Close": 3135.10
    }
  ],
  "metrics": {
    "mse": 142.35,
    "mae": 9.82,
    "r2": 0.842,
    "directional_accuracy": 0.685,
    "test_actual": [3010.0, 3025.5, 3045.5, 3072.0],
    "test_predicted": [3005.2, 3028.1, 3040.8, 3068.5]
  },
  "recommendation": "# SentiScrapper Financial Report: **RELIANCE**\n**Date**: 2026-07-27\n**Final Advice**: `BUY`\n\n### Summary\nStrong Bullish Action Recommended. Technical indicators align with positive social sentiment and forecasting model projection.\n\n---\n\n### Trading Recommendation Details\n- **Current Close Price**: Rs. 3072.00\n- **5-Day Forecast Target**: Rs. 3135.10 (+2.05%)\n- **Tactical Target Level**: Rs. 3225.60\n- **Stop-Loss Protection**: Rs. 2918.40\n\n---\n\n### Scoring Breakdown (Score: +4.0)\n- **Positive**: Model predicts a bullish price trend (+2.05% over next 5 days).\n- **Positive**: Social sentiment is bullish (Compound Score: 0.25).\n- **Positive**: MACD diff is positive (bullish momentum).\n- **Positive**: Trading above 50-day moving average (short-term uptrend).\n\n---\n\n### Macroeconomic Context\n- Latest Inflation Index (FRED CPI): 313.20\n- Unemployment Rate (FRED UNRATE): 4.10%\n",
  "agent_logs": [
    "[17:40:01] [Data Collection Agent] Initializing market data search for RELIANCE...",
    "[17:40:02] [Data Collection Agent] Retrieved 2400 daily price records with technical indicators calculated.",
    "[17:40:02] [Data Collection Agent] Fetched inflation (CPI) and unemployment (UNRATE) indices.",
    "[17:40:03] [Sentiment Agent] Starting multi-channel social harvesting for keyword 'RELIANCE'...",
    "[17:40:04] [Sentiment Agent] Scraped 30 Reddit posts, 20 tweets, 20 Telegram messages.",
    "[17:40:04] [Sentiment Agent] Average Corpus Polarity Compound Score: +0.2458",
    "[17:40:05] [Quant Agent] Fitting quantitative pipeline using 'Random Forest' engine...",
    "[17:40:06] [Quant Agent] Model trained. Validation Metrics: MSE=142.3500, MAE=9.8200, R²=0.8420",
    "[17:40:06] [Quant Agent] Projecting future prices for the next 5 days...",
    "[17:40:07] [Portfolio Manager] Final Portfolio recommendation report compiled successfully."
  ]
}
