import tweepy
from app.config import settings
import logging
import random
from typing import List, Dict

logger = logging.getLogger("TwitterScraper")

class TwitterScraper:
    @classmethod
    def scrape_tweets(cls, keyword: str, limit: int = 30) -> List[Dict[str, str]]:
        if settings.is_twitter_configured():
            logger.info(f"Twitter API configured. Scraping tweets for '{keyword}'...")
            try:
                client = tweepy.Client(bearer_token=settings.TWITTER_BEARER_TOKEN)
                query = f"{keyword} -is:retweet lang:en"
                
                tweets = client.search_recent_tweets(
                    query=query,
                    tweet_fields=["text", "created_at"],
                    max_results=limit
                )
                
                results = []
                if tweets.data:
                    for tweet in tweets.data:
                        results.append({
                            "Text": tweet.text,
                            "Source": "Twitter",
                            "Id": tweet.id
                        })
                    logger.info(f"Successfully fetched {len(results)} tweets from Twitter.")
                    return results
                else:
                    logger.info("No tweets returned by Twitter API. Falling back to simulation.")
            except Exception as e:
                logger.error(f"Error fetching tweets from Twitter: {e}. Falling back to simulation.")
                
        return cls.generate_mock_tweets(keyword, limit)

    @staticmethod
    def generate_mock_tweets(keyword: str, limit: int) -> List[Dict[str, str]]:
        logger.info(f"Simulating Twitter scraper for '{keyword}'...")
        
        templates = [
            "Bullish breakout on {keyword}! Targets set at +10% from here. Let's go!",
            "CDSL and {keyword} are looking super strong today. Volume is crazy.",
            "Avoid {keyword} for now, indicators are bearish. Wait for correction.",
            "Bought some more {keyword} shares today. High conviction long-term play.",
            "Just look at the chart of {keyword}. MACD crossover on daily chart!",
            "Any news on {keyword}? Block deals happening in early trading hours.",
            "{keyword} quarterly results look solid. Promoter shareholding increased.",
            "Stop-loss triggered in {keyword}. Moving funds to other stocks.",
            "Technical analysis shows {keyword} is trading near its major support zone.",
            "Retail investors panic selling {keyword}. Perfect accumulation zone!"
        ]
        
        tweets = []
        count = min(limit, random.randint(10, 20))
        for i in range(count):
            text = random.choice(templates).format(keyword=keyword)
            tweets.append({
                "Text": text,
                "Source": "Twitter",
                "Id": f"mock_tweet_{i}"
            })
        return tweets
