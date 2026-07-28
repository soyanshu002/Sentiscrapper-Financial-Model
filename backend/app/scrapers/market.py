import pandas as pd
import numpy as np
import yfinance as yf
from ta.utils import dropna
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.volatility import AverageTrueRange
from ta.trend import MACD, SMAIndicator
import logging

logger = logging.getLogger("MarketDataFetcher")

class MarketDataFetcher:
    @staticmethod
    def clean_ticker(ticker: str) -> str:
        ticker = ticker.strip().upper()
        # If it doesn't end with .NS or .BO (and doesn't look like a standard US ticker like AAPL)
        # we default it to .NS for Indian equities as per the user's project design
        if len(ticker) > 0 and "." not in ticker:
            logger.info(f"Appending '.NS' to ticker: {ticker}")
            return f"{ticker}.NS"
        return ticker

    @classmethod
    def fetch_and_calculate(cls, ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
        cleaned_ticker = cls.clean_ticker(ticker)
        logger.info(f"Downloading historical data for {cleaned_ticker} from {start_date} to {end_date}...")
        
        try:
            # Try primary cleaned ticker
            df = yf.download(cleaned_ticker, start=start_date, end=end_date, progress=False)
            
            # If primary ticker returned empty, try fallback variants (e.g. without .NS or with .BO)
            if df.empty and "." in cleaned_ticker:
                raw_sym = cleaned_ticker.split(".")[0]
                logger.info(f"Retrying download for fallback raw ticker: {raw_sym}")
                df = yf.download(raw_sym, start=start_date, end=end_date, progress=False)
            
            if df.empty:
                logger.warning(f"yfinance download empty for {cleaned_ticker}. Triggering synthetic market failover...")
                return cls.generate_synthetic_stock_data(cleaned_ticker, start_date, end_date)

            # Reset index to make Date a column
            df = df.reset_index()

            # Handle multi-index columns from yfinance (common in newer yfinance versions)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = [col[0] if col[0] else col[1] for col in df.columns]

            # Standardize columns to standard casing
            col_mapping = {c: c.capitalize() for c in df.columns if c.lower() in ['date', 'open', 'high', 'low', 'close', 'volume', 'adj close']}
            df = df.rename(columns=col_mapping)
            if 'Adj close' in df.columns:
                df = df.rename(columns={'Adj close': 'AdjClose'})

            logger.info("Successfully fetched market data. Computing technical indicators...")
            df = cls.calculate_indicators(df)
            return df
        except Exception as e:
            logger.warning(f"Error fetching market data for {ticker} ({e}). Triggering synthetic market failover...")
            return cls.generate_synthetic_stock_data(cleaned_ticker, start_date, end_date)

    @staticmethod
    def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
        # Ensure we operate on float types
        for col in ['Close', 'High', 'Low', 'Volume']:
            if col in df.columns:
                # If df[col] is a Series of Series or contains arrays (due to multi-index), squeeze it
                if len(df[col].shape) > 1:
                    df[col] = df[col].iloc[:, 0]
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        df = df.dropna(subset=['Close', 'High', 'Low'])

        # 1. RSI (Relative Strength Index)
        rsi_ind = RSIIndicator(df['Close'], window=14)
        df['RSI'] = rsi_ind.rsi()

        # 2. MACD
        macd_ind = MACD(df['Close'], window_slow=26, window_fast=12, window_sign=9)
        df['MACD'] = macd_ind.macd()
        df['MACD_Signal'] = macd_ind.macd_signal()
        df['MACD_Diff'] = macd_ind.macd_diff()

        # 3. Simple Moving Averages (50, 100, 200)
        df['SMA_50'] = SMAIndicator(df['Close'], window=50).sma_indicator()
        df['SMA_100'] = SMAIndicator(df['Close'], window=100).sma_indicator()
        df['SMA_200'] = SMAIndicator(df['Close'], window=200).sma_indicator()

        # 4. Stochastic Oscillator
        stoch_ind = StochasticOscillator(df['High'], df['Low'], df['Close'], window=14, smooth_window=3)
        df['Stoch_K'] = stoch_ind.stoch()
        df['Stoch_D'] = stoch_ind.stoch_signal()

        # 5. ATR (Average True Range)
        df['ATR'] = AverageTrueRange(df['High'], df['Low'], df['Close'], window=14).average_true_range()

        # Forward fill any missing indicator variables
        df = df.ffill().bfill()
        return df
