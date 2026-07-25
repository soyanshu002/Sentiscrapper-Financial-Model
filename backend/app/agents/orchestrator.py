import pandas as pd
import numpy as np
import datetime
import logging
import asyncio
from typing import Dict, Any, List, Tuple

from app.scrapers.market import MarketDataFetcher
from app.scrapers.macro import MacroDataFetcher
from app.scrapers.reddit import RedditScraper
from app.scrapers.twitter import TwitterScraper
from app.scrapers.telegram import TelegramScraper
from app.scrapers.news import NewsScraper

from app.models.sentiment import SentimentAnalyzer
from app.models.forecaster import ForecasterPipeline

logger = logging.getLogger("MultiAgentOrchestrator")

class MultiAgentOrchestrator:
    def __init__(self, model_dir: str = "backend/data/models"):
        self.pipeline = ForecasterPipeline(model_dir)
        self.sentiment_analyzer = SentimentAnalyzer()
        self.logs: List[str] = []

    def log_step(self, agent_name: str, message: str):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        log_msg = f"[{timestamp}] [{agent_name}] {message}"
        self.logs.append(log_msg)
        logger.info(log_msg)

    async def run_analysis(self, ticker: str, model_type: str = "Random Forest", start_date: str = "2015-01-01", end_date: str = None) -> Dict[str, Any]:
        self.logs = []
        if end_date is None:
            end_date = datetime.date.today().strftime("%Y-%m-%d")

        # --- STEP 1: DATA COLLECTION AGENT ---
        self.log_step("Data Collection Agent", f"Initializing market data search for {ticker}...")
        try:
            stock_data = MarketDataFetcher.fetch_and_calculate(ticker, start_date, end_date)
            self.log_step("Data Collection Agent", f"Retrieved {len(stock_data)} daily price records with technical indicators calculated.")
            
            macro_data = MacroDataFetcher.fetch_macro_indicators(start_date, end_date)
            self.log_step("Data Collection Agent", "Fetched inflation (CPI) and unemployment (UNRATE) indices.")
            
            # Align them
            df = MacroDataFetcher.align_macro_with_stock(stock_data, macro_data)
            self.log_step("Data Collection Agent", "Aligned market price indices with macroeconomic indicators successfully.")
        except Exception as e:
            self.log_step("Data Collection Agent", f"CRITICAL ERROR in Data Collection: {e}")
            raise

        # --- STEP 2: SENTIMENT MINING AGENT ---
        self.log_step("Sentiment Agent", f"Starting multi-channel social harvesting for keyword '{ticker}'...")
        
        # Scrape Reddit (async)
        reddit_task = RedditScraper.scrape_posts(ticker, limit=30)
        # Scrape Telegram (async)
        telegram_task = TelegramScraper.scrape_channel_messages(ticker, limit=20)
        # Scrape Twitter (blocking, wrapped or fast)
        tweets = TwitterScraper.scrape_tweets(ticker, limit=20)
        # Scrape News (blocking)
        moneycontrol_news = NewsScraper.scrape_moneycontrol(ticker)
        yfinance_news = NewsScraper.scrape_yfinance_news(ticker)

        reddit_posts, telegram_messages = await asyncio.gather(reddit_task, telegram_task)

        self.log_step("Sentiment Agent", f"Scraped {len(reddit_posts)} Reddit posts, {len(tweets)} tweets, {len(telegram_messages)} Telegram messages.")
        self.log_step("Sentiment Agent", f"Scraped {len(moneycontrol_news)} Moneycontrol articles, {len(yfinance_news)} Yahoo headlines.")

        # Combine text elements for polarity calculations with sources
        text_corpus = []
        text_corpus.extend([{"text": p["Title"], "source": "Reddit"} for p in reddit_posts])
        text_corpus.extend([{"text": t["Text"], "source": "Twitter"} for t in tweets])
        text_corpus.extend([{"text": m["Text"], "source": "Telegram"} for m in telegram_messages])
        text_corpus.extend([{"text": n["Title"], "source": "News"} for n in moneycontrol_news])
        text_corpus.extend([{"text": y["Title"], "source": "News"} for y in yfinance_news])

        self.log_step("Sentiment Agent", f"Running VADER Sentiment analysis on a corpus of {len(text_corpus)} items...")
        sentiment_res = self.sentiment_analyzer.analyze_texts(text_corpus)
        avg_sentiment = sentiment_res["average_compound"]
        
        self.log_step("Sentiment Agent", f"Average Corpus Polarity Compound Score: {avg_sentiment:+.4f}")
        
        # Append decay-weighted sentiment column
        self.log_step("Sentiment Agent", "Generating rolling decay-weighted sentiment values for time-series features...")
        df['Weighted_Sentiment'] = self.sentiment_analyzer.calculate_weighted_sentiment_history(len(df), avg_sentiment)
        
        # --- STEP 3: QUANTITATIVE ANALYST AGENT ---
        self.log_step("Quant Agent", f"Fitting quantitative pipeline using '{model_type}' engine...")
        X, y = self.pipeline.preprocess_data(df, is_training=True)
        self.log_step("Quant Agent", "Handled missing feature inputs with KNN imputation.")

        # Fit model
        eval_metrics = {}
        if model_type.lower() == "lstm":
            # LSTM requires sequential prep
            eval_metrics = self.pipeline.train_lstm(X, y, df['Close'], epochs=10)
        else:
            # Default to Random Forest
            eval_metrics = self.pipeline.train_random_forest(X, y, df['Close'])

        self.log_step("Quant Agent", f"Model trained. Validation Metrics: MSE={eval_metrics['mse']:.4f}, MAE={eval_metrics['mae']:.4f}, R²={eval_metrics['r2']:.4f}")
        self.log_step("Quant Agent", f"Backtest Directional Accuracy: {eval_metrics['directional_accuracy']*100:.2f}%")

        # Predict future 5 days
        self.log_step("Quant Agent", "Projecting future prices for the next 5 days...")
        last_row = df.iloc[-1].copy()
        
        future_dates = pd.date_range(start=last_row['Date'], periods=6, freq='D')[1:]
        
        if model_type.lower() == "lstm":
            future_predictions = self.pipeline.predict_future_lstm(df, future_days=5)
        else:
            future_predictions = self.pipeline.predict_future_rf(last_row, future_days=5)

        future_df = pd.DataFrame({
            "Date": future_dates.strftime("%Y-%m-%d"),
            "Predicted_Close": future_predictions
        })
        
        for idx, row in future_df.iterrows():
            self.log_step("Quant Agent", f"Day {idx+1} ({row['Date']}): Forecasted Close = {row['Predicted_Close']:.2f}")

        # --- STEP 4: PORTFOLIO MANAGER AGENT ---
        self.log_step("Portfolio Manager", "Synthesizing market indicators, macro factors, and predictive trends...")
        recommendation = self.generate_recommendation(ticker, df, future_df, avg_sentiment, eval_metrics, model_type)
        self.log_step("Portfolio Manager", "Final Portfolio recommendation report compiled successfully.")

        # Structure response
        return {
            "ticker": ticker,
            "model_type": model_type,
            "average_sentiment": avg_sentiment,
            "sentiment_details": sentiment_res["details"][:20],  # Return top 20 items for list view
            "historical_data": df[['Date', 'Close', 'Open', 'High', 'Low', 'RSI', 'MACD', 'Weighted_Sentiment']].tail(60).to_dict(orient="records"), # Last 60 days
            "forecast_data": future_df.to_dict(orient="records"),
            "metrics": {
                "mse": eval_metrics["mse"],
                "mae": eval_metrics["mae"],
                "r2": eval_metrics["r2"],
                "directional_accuracy": eval_metrics["directional_accuracy"],
                "test_actual": eval_metrics["test_actual"][-30:],  # Last 30 points for chart alignment
                "test_predicted": eval_metrics["test_predicted"][-30:]
            },
            "recommendation": recommendation,
            "agent_logs": self.logs
        }

    def generate_recommendation(self, ticker: str, df: pd.DataFrame, future_df: pd.DataFrame, avg_sentiment: float, metrics: Dict[str, Any], model_type: str) -> str:
        last_price = float(df['Close'].iloc[-1])
        first_forecast = future_df['Predicted_Close'].iloc[0]
        final_forecast = future_df['Predicted_Close'].iloc[-1]
        
        forecast_return = ((final_forecast - last_price) / last_price) * 100
        
        # Extract signals
        last_rsi = float(df['RSI'].iloc[-1])
        last_macd_diff = float(df['MACD_Diff'].iloc[-1])
        last_sma50 = float(df['SMA_50'].iloc[-1])
        last_sma200 = float(df['SMA_200'].iloc[-1])
        
        # Compile a signal score
        score = 0
        reasons = []
        
        # 1. Price Forecast Direction
        if forecast_return > 2.0:
            score += 2
            reasons.append(f"Model predicts a bullish price trend (+{forecast_return:.2f}% over next 5 days).")
        elif forecast_return < -2.0:
            score -= 2
            reasons.append(f"Model predicts a bearish price drop ({forecast_return:.2f}% over next 5 days).")
        else:
            reasons.append(f"Model predicts minor sideways consolidation ({forecast_return:+.2f}%).")
            
        # 2. VADER Sentiment
        if avg_sentiment > 0.15:
            score += 1
            reasons.append(f"Social sentiment is bullish (Compound Score: {avg_sentiment:.2f}).")
        elif avg_sentiment < -0.15:
            score -= 1
            reasons.append(f"Social sentiment is bearish (Compound Score: {avg_sentiment:.2f}).")
        else:
            reasons.append("Social sentiment is neutral/mixed.")

        # 3. Technical Indicators
        if last_rsi < 30:
            score += 1
            reasons.append(f"RSI is oversold at {last_rsi:.1f} (potential bounce candidate).")
        elif last_rsi > 70:
            score -= 1
            reasons.append(f"RSI is overbought at {last_rsi:.1f} (potential consolidation/reversal).")
            
        if last_macd_diff > 0:
            score += 1
            reasons.append("MACD diff is positive (bullish momentum).")
        else:
            score -= 1
            reasons.append("MACD diff is negative (bearish momentum).")

        if last_price > last_sma50:
            score += 1
            reasons.append("Trading above 50-day moving average (short-term uptrend).")
        else:
            score -= 1
            reasons.append("Trading below 50-day moving average (short-term weakness).")

        # Determine Recommendation
        if score >= 3:
            rec = "BUY"
            action_desc = "Strong Bullish Action Recommended. Technical indicators align with positive social sentiment and forecasting model projection."
        elif score >= 1:
            rec = "ACCUMULATE / WEAK BUY"
            action_desc = "Moderate buying interest. Accumulate on minor dips. Technical indicators are neutral-to-bullish, backed by steady sentiment."
        elif score <= -3:
            rec = "SELL"
            action_desc = "Strong Bearish Action Recommended. Sell/Reduce exposure. Forecast drop, negative sentiment indicators, and bearish moving averages."
        elif score <= -1:
            rec = "REDUCE / WEAK SELL"
            action_desc = "Moderate bearish signals. Consider trimming positions. Short-term momentum is slowing down."
        else:
            rec = "HOLD / NEUTRAL"
            action_desc = "Market is in equilibrium. Hold current positions. Wait for a clearer breakout in sentiment or price indicators."

        # Target/Stop Loss calculation
        if rec in ["BUY", "ACCUMULATE / WEAK BUY"]:
            target = last_price * (1.0 + max(forecast_return/100, 0.05))
            stop_loss = last_price * 0.95
        else:
            target = last_price * 0.95
            stop_loss = last_price * (1.0 + abs(forecast_return/100) if forecast_return < 0 else 1.05)

        # Build Markdown
        report = f"""# SentiScrapper Financial Report: **{ticker}**
**Date**: {datetime.date.today().strftime('%Y-%m-%d')}
**Final Advice**: `{rec}`

### Summary
{action_desc}

---

### Trading Recommendation Details
- **Current Close Price**: Rs. {last_price:.2f}
- **5-Day Forecast Target**: Rs. {final_forecast:.2f} ({forecast_return:+.2f}%)
- **Tactical Target Level**: Rs. {target:.2f}
- **Stop-Loss Protection**: Rs. {stop_loss:.2f}

---

### Scoring Breakdown (Score: {score:+.1f})
{chr(10).join([f'- **{"Positive" if s.startswith("Model predicts a bullish") or s.startswith("Social sentiment is bullish") or "oversold" in s or "positive" in s or "above" in s else "Negative" if "bearish" in s or "overbought" in s or "below" in s else "Neutral"}**: {s}' for s in reasons])}

---

### Macroeconomic Context
- Latest Inflation Index (FRED CPI): {float(df['Inflation'].iloc[-1]):.2f}
- Unemployment Rate (FRED UNRATE): {float(df['Unemployment'].iloc[-1]):.2f}%

*Disclaimer: This analysis is generated by an automated multi-agent framework utilizing mathematical forecasting models and social polarity scoring. It does not constitute formal financial planning advice. Invest at your own risk.*
"""
        return report
