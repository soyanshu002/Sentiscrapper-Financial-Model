import pandas as pd
import pandas_datareader as pdr
import datetime
import logging
import numpy as np

logger = logging.getLogger("MacroDataFetcher")

class MacroDataFetcher:
    @staticmethod
    def fetch_macro_indicators(start_date: str, end_date: str) -> pd.DataFrame:
        logger.info(f"Attempting to fetch macro data (FRED Inflation & Unemployment) from {start_date} to {end_date}...")
        try:
            # FRED codes: CPIAUCSL (Consumer Price Index), UNRATE (Unemployment Rate)
            inflation = pdr.get_data_fred('CPIAUCSL', start=start_date, end=end_date)
            unemployment = pdr.get_data_fred('UNRATE', start=start_date, end=end_date)

            macro = pd.concat([inflation, unemployment], axis=1)
            macro.columns = ['Inflation', 'Unemployment']
            macro = macro.ffill().bfill()
            
            logger.info("Successfully fetched macro data from FRED.")
            return macro
        except Exception as e:
            logger.warning(f"Could not fetch macro data from FRED ({e}). Generating simulated indices for alignment...")
            # Generate simulated indices
            date_range = pd.date_range(start=start_date, end=end_date, freq='ME')
            sim_inflation = 250.0 + np.cumsum(np.random.normal(0.5, 0.2, len(date_range)))
            sim_unemployment = 5.0 + np.cumsum(np.random.normal(0.0, 0.1, len(date_range)))
            
            # Clip unemployment to realistic bounds [3.0, 12.0]
            sim_unemployment = np.clip(sim_unemployment, 3.0, 12.0)

            macro = pd.DataFrame({
                'Inflation': sim_inflation,
                'Unemployment': sim_unemployment
            }, index=date_range)
            
            return macro

    @classmethod
    def align_macro_with_stock(cls, stock_df: pd.DataFrame, macro_df: pd.DataFrame) -> pd.DataFrame:
        """
        Merge macro data (which is usually monthly) with daily stock prices,
        using forward-fill to match the stock dates.
        """
        try:
            # Ensure index of stock_df and macro_df is datetime
            stock_df = stock_df.copy()
            stock_df['Date'] = pd.to_datetime(stock_df['Date'])
            
            macro_df = macro_df.copy()
            macro_df.index = pd.to_datetime(macro_df.index)

            # We can reindex macro_df to match the stock_df dates and forward fill
            macro_reindexed = macro_df.reindex(stock_df['Date']).ffill().bfill()
            macro_reindexed = macro_reindexed.reset_index(drop=True)
            
            # Add columns
            stock_df['Inflation'] = macro_reindexed['Inflation'].values
            stock_df['Unemployment'] = macro_reindexed['Unemployment'].values
            
            return stock_df
        except Exception as e:
            logger.error(f"Error aligning macro data with stock data: {e}")
            # Fallback: fill stock_df with default macro values if alignment fails
            stock_df['Inflation'] = 280.0
            stock_df['Unemployment'] = 5.5
            return stock_df
