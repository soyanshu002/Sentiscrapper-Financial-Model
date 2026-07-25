from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import pandas as pd
import numpy as np
import logging
from typing import List, Dict, Union, Any

logger = logging.getLogger("SentimentAnalyzer")

class SentimentAnalyzer:
    def __init__(self):
        self.analyzer = SentimentIntensityAnalyzer()

    def analyze_texts(self, texts: List[Union[str, Dict[str, str]]]) -> Dict[str, Union[float, List[Dict[str, Any]]]]:
        """
        Analyze a list of strings or dicts and return detailed metrics and the average compound score.
        """
        if not texts:
            return {"average_compound": 0.0, "details": []}

        scores = []
        details = []
        for item in texts:
            if isinstance(item, dict):
                text = item.get("text", "")
                source = item.get("source", "Unknown")
            else:
                text = item
                source = "Unknown"

            score = self.analyzer.polarity_scores(text)
            scores.append(score["compound"])
            details.append({
                "text": text,
                "Source": source,
                "positive": score["pos"],
                "neutral": score["neu"],
                "negative": score["neg"],
                "compound": score["compound"]
            })

        avg_compound = float(np.mean(scores))
        logger.info(f"Analyzed {len(texts)} texts. Average compound score: {avg_compound:.4f}")
        
        return {
            "average_compound": avg_compound,
            "details": details
        }

    @staticmethod
    def calculate_weighted_sentiment_history(df_length: int, avg_sentiment: float, days: int = 10, decay_factor: float = 0.9) -> List[float]:
        """
        Calculates weighted sentiment for historical days.
        Simulates slight variations in historical daily sentiment (centered around the scraped average sentiment)
        and computes the decay-weighted moving sum.
        """
        # Generate raw daily sentiments around avg_sentiment
        np.random.seed(42)  # For deterministic runs
        raw_sentiments = np.random.normal(loc=avg_sentiment, scale=0.15, size=df_length)
        raw_sentiments = np.clip(raw_sentiments, -1.0, 1.0)

        weighted_sentiments = []
        for i in range(df_length):
            if i < days:
                window = raw_sentiments[0 : i + 1]
            else:
                window = raw_sentiments[i - days + 1 : i + 1]
            
            # Apply decay weights (most recent index has highest weight = 1, oldest has decay_factor**(window_len-1))
            weights = np.array([decay_factor ** j for j in range(len(window))][::-1])
            weighted_sum = np.sum(window * weights)
            weighted_sentiments.append(float(weighted_sum))

        return weighted_sentiments

    @staticmethod
    def project_future_sentiment(last_weighted_sentiment: float, avg_sentiment: float, future_days: int = 5, decay_factor: float = 0.9) -> List[float]:
        """
        Projects weighted sentiment into the future. Sentiment decays back toward the baseline (avg_sentiment)
        over time.
        """
        future_sentiments = []
        current_val = last_weighted_sentiment
        for _ in range(future_days):
            # Future sentiment decays towards the baseline average sentiment
            current_val = current_val * decay_factor + avg_sentiment * (1 - decay_factor)
            future_sentiments.append(float(current_val))
        return future_sentiments
