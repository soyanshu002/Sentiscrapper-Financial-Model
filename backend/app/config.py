import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
import logging

# Set up logging format
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("SentiScrapperConfig")

# Find the project directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    # API Port/Host
    PORT: int = 8000
    HOST: str = "127.0.0.1"

    # Reddit PRAW
    REDDIT_CLIENT_ID: Optional[str] = None
    REDDIT_CLIENT_SECRET: Optional[str] = None
    REDDIT_USER_AGENT: str = "SentiScrapper/1.0"

    # Twitter API
    TWITTER_BEARER_TOKEN: Optional[str] = None

    # Financial Modeling Prep (FMP)
    FMP_API_KEY: Optional[str] = None

    # Telegram API
    TELEGRAM_API_ID: Optional[str] = None
    TELEGRAM_API_HASH: Optional[str] = None

    # AlphaVantage API
    ALPHA_VANTAGE_API_KEY: Optional[str] = None

    # Gemini/LLM API Key
    GEMINI_API_KEY: Optional[str] = None

    # App directories
    DATA_DIR: Path = BASE_DIR / "backend" / "data"

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def is_reddit_configured(self) -> bool:
        return bool(self.REDDIT_CLIENT_ID and self.REDDIT_CLIENT_SECRET)

    def is_twitter_configured(self) -> bool:
        return bool(self.TWITTER_BEARER_TOKEN)

    def is_fmp_configured(self) -> bool:
        return bool(self.FMP_API_KEY)

    def is_telegram_configured(self) -> bool:
        return bool(self.TELEGRAM_API_ID and self.TELEGRAM_API_HASH)

    def is_alphavantage_configured(self) -> bool:
        return bool(self.ALPHA_VANTAGE_API_KEY)

    def is_gemini_configured(self) -> bool:
        return bool(self.GEMINI_API_KEY)

# Instantiate settings
settings = Settings()

# Ensure data directory exists
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)

logger.info(f"Loaded configuration from: {settings.model_config.get('env_file')}")
logger.info(f"Reddit configured: {settings.is_reddit_configured()}")
logger.info(f"Twitter configured: {settings.is_twitter_configured()}")
logger.info(f"FMP configured: {settings.is_fmp_configured()}")
logger.info(f"Telegram configured: {settings.is_telegram_configured()}")
logger.info(f"AlphaVantage configured: {settings.is_alphavantage_configured()}")
logger.info(f"Gemini LLM configured: {settings.is_gemini_configured()}")
