import asyncpraw
from app.config import settings
import logging
import random
from typing import List, Dict

logger = logging.getLogger("RedditScraper")

class RedditScraper:
    @classmethod
    async def scrape_posts(cls, keyword: str, limit: int = 50) -> List[Dict[str, str]]:
        if settings.is_reddit_configured():
            logger.info(f"Reddit API keys configured. Scraping Reddit for '{keyword}'...")
            try:
                # Initialize asyncpraw client
                reddit = asyncpraw.Reddit(
                    client_id=settings.REDDIT_CLIENT_ID,
                    client_secret=settings.REDDIT_CLIENT_SECRET,
                    user_agent=settings.REDDIT_USER_AGENT
                )
                
                subreddit = await reddit.subreddit("IndianStockMarket")
                posts = []
                
                # Search posts
                async for post in subreddit.search(keyword, limit=limit):
                    posts.append({
                        "Title": post.title,
                        "Body": post.selftext or "",
                        "Source": "Reddit",
                        "URL": post.url
                    })
                
                await reddit.close()
                logger.info(f"Successfully scraped {len(posts)} posts from Reddit.")
                return posts
            except Exception as e:
                logger.error(f"Error scraping Reddit: {e}. Falling back to simulation.")
        
        # Fallback to simulation
        return cls.generate_mock_posts(keyword, limit)

    @staticmethod
    def generate_mock_posts(keyword: str, limit: int) -> List[Dict[str, str]]:
        logger.info(f"Simulating Reddit scraper for '{keyword}'...")
        
        # Generic templates
        templates = [
            "Thoughts on {keyword} at current levels? Looks like a strong breakout.",
            "Is {keyword} a long-term buy or a swing trade option?",
            "What is happening with {keyword} today? Huge volume spike!",
            "My detailed fundamental analysis on {keyword} for 2026.",
            "Avoid {keyword} for a while. Technicals show heavily overbought conditions.",
            "Why I am accumulating {keyword} shares in every dip.",
            "Will {keyword} beat earnings estimates next week?",
            "{keyword} chart analysis: RSI is showing bullish divergence on daily charts.",
            "Is anyone else holding {keyword} since IPO? Planning to book profit.",
            "Great support at current price levels for {keyword}. Expecting bounce back."
        ]
        
        posts = []
        count = min(limit, random.randint(15, 30))
        for i in range(count):
            tpl = random.choice(templates)
            title = tpl.format(keyword=keyword)
            posts.append({
                "Title": title,
                "Body": f"Here is my analysis on {keyword}. The company has solid fundamentals, strong cash flows, and recent government orders/promoter buying. Technical support seems to be holding well. What are your views?",
                "Source": "Reddit",
                "URL": f"https://www.reddit.com/r/IndianStockMarket/comments/mock{i}/"
            })
            
        return posts
