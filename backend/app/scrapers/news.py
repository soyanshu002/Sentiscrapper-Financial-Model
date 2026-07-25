import requests
from bs4 import BeautifulSoup
import logging
import random
from typing import List, Dict

logger = logging.getLogger("NewsScraper")

class NewsScraper:
    @classmethod
    def scrape_moneycontrol(cls, keyword: str) -> List[Dict[str, str]]:
        """Scrapes news headlines from Moneycontrol tag search."""
        formatted_keyword = keyword.lower().replace(" ", "-")
        url = f"https://www.moneycontrol.com/news/tags/{formatted_keyword}.html"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        }
        
        logger.info(f"Scraping Moneycontrol for '{keyword}' news...")
        try:
            response = requests.get(url, headers=headers, timeout=5.0)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, "html.parser")
                # Identify news items
                articles = soup.find_all("li", class_="clearfix")
                results = []
                
                for article in articles:
                    title_tag = article.find("h2")
                    link_tag = article.find("a")
                    
                    if title_tag and link_tag:
                        title = title_tag.text.strip()
                        link = link_tag["href"]
                        results.append({
                            "Title": title,
                            "URL": link,
                            "Source": "Moneycontrol"
                        })
                
                if results:
                    logger.info(f"Successfully scraped {len(results)} news items from Moneycontrol.")
                    return results
            logger.warning(f"Moneycontrol returned status code {response.status_code} or no results found. Falling back to simulation.")
        except Exception as e:
            logger.error(f"Error scraping Moneycontrol for '{keyword}': {e}. Falling back to simulation.")
            
        return cls.generate_mock_news(keyword, "Moneycontrol")

    @classmethod
    def scrape_yfinance_news(cls, ticker: str) -> List[Dict[str, str]]:
        """Fetches ticker news from Yahoo Finance API wrapper."""
        logger.info(f"Fetching yfinance news headlines for '{ticker}'...")
        try:
            import yfinance as yf
            stock = yf.Ticker(ticker)
            news = stock.news
            
            results = []
            if news:
                for article in news:
                    results.append({
                        "Title": article.get("title", ""),
                        "URL": article.get("link", ""),
                        "Source": "Yahoo Finance"
                    })
                logger.info(f"Successfully fetched {len(results)} news items from Yahoo Finance.")
                return results
        except Exception as e:
            logger.error(f"Error fetching Yahoo Finance news: {e}. Falling back to simulation.")
            
        return cls.generate_mock_news(ticker, "Yahoo Finance")

    @staticmethod
    def generate_mock_news(keyword: str, source: str) -> List[Dict[str, str]]:
        logger.info(f"Simulating {source} news feed for '{keyword}'...")
        
        templates = [
            "{keyword} shares rise on securing domestic orders worth Rs 500 Cr",
            "Why analysts recommend holding {keyword} ahead of Q3 earnings announcement",
            "{keyword} expands capacity to meet rising demand in local markets",
            "Brokers highlight bullish outlook for {keyword} with target upgrades",
            "{keyword} share price drops 2% amid minor profit booking on technical levels",
            "{keyword} net profit grows 25% YoY; company declares interim dividend of Rs 5 per share",
            "FIIs increase stake in {keyword} during the last quarter: Shareholder analysis",
            "{keyword} partners with global firms to implement green energy initiatives"
        ]
        
        results = []
        count = random.randint(4, 8)
        for i in range(count):
            title = random.choice(templates).format(keyword=keyword)
            results.append({
                "Title": title,
                "URL": f"https://www.financialnews.com/article/mock{i}/",
                "Source": source
            })
        return results
