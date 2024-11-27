import pandas as pd
import numpy as np
from textblob import TextBlob
import snscrape.modules.twitter as sntwitter
import requests
from datetime import datetime, timedelta
import logging
from bs4 import BeautifulSoup
import re
from config import (
    TWITTER_CONFIG, STOCKTWITS_CONFIG,
    SENTIMENT_CORRELATION_THRESHOLD,
    MIN_SOCIAL_POSTS,
    SENTIMENT_WINDOW,
    SENTIMENT_LOOKBACK_PERIODS
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    """
    SentimentAnalyzer class for analyzing social media sentiment.

    This class handles all social media sentiment analysis, including:
    - Scraping StockTwits for trending stocks
    - Analyzing sentiment from social media posts
    - Calculating sentiment metrics and correlations
    - Detecting potential market overreactions

    The analyzer uses web scraping to gather data from StockTwits and
    implements various sentiment analysis techniques to gauge market sentiment.

    Attributes:
        logger (logging.Logger): Logger for sentiment analysis activities

    Configuration:
        The analyzer's behavior is controlled by parameters in config.py:
        - SENTIMENT_CORRELATION_THRESHOLD: Min correlation coefficient
        - MIN_SOCIAL_POSTS: Minimum posts for valid sentiment
        - SENTIMENT_WINDOW: Sentiment analysis timeframe
        - SENTIMENT_LOOKBACK_PERIODS: Correlation calculation periods
    """

    def __init__(self):
        """Initialize the sentiment analyzer."""
        self.logger = logging.getLogger(__name__)
        self._setup_apis()

    def _setup_apis(self):
        """Initialize API connections."""
        self.twitter_auth = TWITTER_CONFIG
        self.stocktwits_token = STOCKTWITS_CONFIG['ACCESS_TOKEN']

    def _scrape_stocktwits_page(self, url):
        """Scrape StockTwits page for symbols"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')

                # Find symbol links (they usually have a $ prefix)
                symbols = set()
                symbol_pattern = re.compile(r'\$([A-Z]+)')

                # Look for symbols in text content
                for text in soup.stripped_strings:
                    matches = symbol_pattern.findall(text)
                    symbols.update(matches)

                return list(symbols)
            else:
                self.logger.warning(f"Failed to fetch page {url}: {response.status_code}")
                return []

        except Exception as e:
            self.logger.error(f"Error scraping page {url}: {e}")
            return []

    def get_sentiment_data(self, symbol, lookback_hours=2):
        """Get sentiment data from multiple sources"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=lookback_hours)

        # Collect social media posts
        twitter_posts = self._get_twitter_posts(symbol, start_time, end_time)
        stocktwits_posts = self._get_stocktwits_posts(symbol, start_time, end_time)

        # Combine and analyze posts
        all_posts = twitter_posts + stocktwits_posts
        if len(all_posts) < MIN_SOCIAL_POSTS:
            logger.warning(f"Insufficient posts for {symbol}: {len(all_posts)} < {MIN_SOCIAL_POSTS}")
            return None

        # Create time series of sentiment
        sentiment_df = self._create_sentiment_timeseries(all_posts, start_time, end_time)
        return sentiment_df

    def _get_twitter_posts(self, symbol, start_time, end_time):
        """Fetch Twitter posts"""
        query = f"${symbol} lang:en -is:retweet"
        posts = []

        try:
            for tweet in sntwitter.TwitterSearchScraper(query).get_items():
                if start_time <= tweet.date <= end_time:
                    posts.append({
                        'text': tweet.content,
                        'timestamp': tweet.date,
                        'source': 'twitter'
                    })
        except Exception as e:
            logger.error(f"Error fetching Twitter data: {e}")

        return posts

    def _get_stocktwits_posts(self, symbol, start_time, end_time):
        """Fetch StockTwits posts"""
        url = f"https://api.stocktwits.com/api/2/streams/symbol/{symbol}.json"
        posts = []

        try:
            response = requests.get(url, params={'access_token': self.stocktwits_token})
            if response.status_code == 200:
                data = response.json()
                for message in data['messages']:
                    post_time = datetime.strptime(message['created_at'], '%Y-%m-%dT%H:%M:%SZ')
                    if start_time <= post_time <= end_time:
                        posts.append({
                            'text': message['body'],
                            'timestamp': post_time,
                            'source': 'stocktwits'
                        })
        except Exception as e:
            logger.error(f"Error fetching StockTwits data: {e}")

        return posts

    def _create_sentiment_timeseries(self, posts, start_time, end_time):
        """Create time series of sentiment scores"""
        # Sort posts by timestamp
        posts = sorted(posts, key=lambda x: x['timestamp'])

        # Create DataFrame with sentiment scores
        df = pd.DataFrame(posts)
        df['sentiment'] = df['text'].apply(self._analyze_text_sentiment)

        # Resample to regular intervals
        df.set_index('timestamp', inplace=True)
        interval = pd.Timedelta(SENTIMENT_WINDOW)
        resampled = df['sentiment'].resample(interval).mean()

        # Forward fill missing values up to a limit
        resampled = resampled.fillna(method='ffill', limit=2)

        return resampled

    def _analyze_text_sentiment(self, text):
        """Analyze sentiment of text using TextBlob"""
        try:
            analysis = TextBlob(text)
            return analysis.sentiment.polarity
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return 0

    def calculate_sentiment_correlation(self, sentiment_data, price_data):
        """Calculate correlation between sentiment and price movements"""
        if sentiment_data is None or price_data is None:
            return 0

        try:
            # Align and resample data to same timeframe
            df = pd.DataFrame({
                'sentiment': sentiment_data,
                'price': price_data
            })

            # Calculate returns/changes
            df['sentiment_change'] = df['sentiment'].pct_change()
            df['price_change'] = df['price'].pct_change()

            # Calculate rolling correlation
            correlation = df['sentiment_change'].rolling(
                window=SENTIMENT_LOOKBACK_PERIODS
            ).corr(df['price_change'])

            return correlation.iloc[-1] if not pd.isna(correlation.iloc[-1]) else 0

        except Exception as e:
            logger.error(f"Error calculating correlation: {e}")
            return 0

    def detect_overreaction(self, symbol, price_data):
        """Detect market overreactions based on sentiment-price correlation"""
        # Get sentiment data
        sentiment_data = self.get_sentiment_data(symbol)
        if sentiment_data is None:
            return False, 0

        # Calculate correlation
        correlation = self.calculate_sentiment_correlation(sentiment_data, price_data)

        # Check if correlation indicates overreaction
        is_overreaction = abs(correlation) >= SENTIMENT_CORRELATION_THRESHOLD

        if is_overreaction:
            logger.info(f"Overreaction detected for {symbol}. Correlation: {correlation:.2f}")

        return is_overreaction, correlation

    def get_trending_stocks(self):
        """
        Get trending stocks from StockTwits using web scraping.

        Scrapes multiple StockTwits pages to find trending and actively
        discussed stocks. Implements various pattern matching techniques
        to identify stock symbols in the HTML content.

        Returns:
            list: List of unique stock symbols that are trending
        """
        trending_stocks = set()

        # URLs to scrape
        urls = {
            'trending': 'https://stocktwits.com/symbol-rankings',
            'active': 'https://stocktwits.com/rankings/active'
        }

        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        }

        try:
            for category, url in urls.items():
                try:
                    self.logger.info(f"Scraping {category} stocks from {url}...")
                    response = requests.get(url, headers=headers, timeout=10)

                    if response.status_code == 200:
                        # Parse HTML content
                        soup = BeautifulSoup(response.text, 'html.parser')

                        # Look for stock symbols in various formats
                        # Format 1: $SYMBOL
                        dollar_symbols = soup.find_all(text=re.compile(r'\$[A-Z]{1,5}'))
                        for text in dollar_symbols:
                            match = re.search(r'\$([A-Z]{1,5})', text)
                            if match:
                                symbol = match.group(1)
                                trending_stocks.add(symbol)
                                self.logger.info(f"Found symbol: {symbol}")

                        # Format 2: Links containing symbols
                        symbol_links = soup.find_all('a', href=re.compile(r'/symbol/[A-Z]{1,5}'))
                        for link in symbol_links:
                            symbol = link['href'].split('/')[-1]
                            if re.match(r'^[A-Z]{1,5}$', symbol):
                                trending_stocks.add(symbol)
                                self.logger.info(f"Found symbol: {symbol}")

                        # Format 3: Text containing common stock references
                        stock_texts = soup.find_all(text=re.compile(r'[A-Z]{1,5}\s+(?:Stock|share|price|chart)'))
                        for text in stock_texts:
                            matches = re.findall(r'([A-Z]{1,5})\s+(?:Stock|share|price|chart)', text)
                            for symbol in matches:
                                if len(symbol) <= 5:  # Standard stock symbol length
                                    trending_stocks.add(symbol)
                                    self.logger.info(f"Found symbol: {symbol}")

                    else:
                        self.logger.warning(f"Failed to fetch {category} page: {response.status_code}")

                except Exception as e:
                    self.logger.error(f"Error scraping {category} page: {e}")
                    continue

            # Filter out common words that might be mistaken for symbols
            common_words = {'THE', 'FOR', 'AND', 'BUT', 'NOW', 'NEW', 'ALL', 'INC', 'CEO', 'CFO', 'USA'}
            trending_stocks = {s for s in trending_stocks if s not in common_words}

            self.logger.info(f"Found {len(trending_stocks)} unique trending stocks")
            return list(trending_stocks)

        except Exception as e:
            self.logger.error(f"Error getting trending stocks: {e}")
            return []

    def get_symbol_sentiment_metrics(self, symbol):
        """
        Get sentiment metrics by scraping StockTwits symbol page.

        Scrapes and analyzes the StockTwits page for a specific symbol to
        gather sentiment metrics including:
        - Message count
        - Bullish/bearish ratio
        - Watcher count
        - Sentiment changes

        Args:
            symbol (str): The stock symbol to analyze

        Returns:
            dict: Dictionary containing sentiment metrics, or None if unavailable
        """
        try:
            url = f"https://stocktwits.com/symbol/{symbol}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5'
            }

            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')

                # Initialize metrics
                metrics = {
                    'symbol': symbol,
                    'timestamp': datetime.now(),
                    'watchers': 0,
                    'posts': 0,
                    'sentiment': 0,
                    'sentiment_change': 0
                }

                # Find sentiment indicators
                bullish_count = len(soup.find_all(class_=re.compile(r'.*bullish.*', re.I)))
                bearish_count = len(soup.find_all(class_=re.compile(r'.*bearish.*', re.I)))

                # Find message count
                message_count = len(soup.find_all(class_=re.compile(r'.*message.*', re.I)))
                metrics['posts'] = message_count

                # Calculate sentiment ratio
                total_sentiment = bullish_count + bearish_count
                if total_sentiment > 0:
                    metrics['sentiment'] = (bullish_count - bearish_count) / total_sentiment

                # Find watcher count (might be in different formats)
                watcher_elements = soup.find_all(text=re.compile(r'(?:Watchers|Followers|Following):\s*[\d,]+'))
                for element in watcher_elements:
                    match = re.search(r'[\d,]+', element)
                    if match:
                        metrics['watchers'] = int(match.group().replace(',', ''))
                        break

                return metrics

            else:
                self.logger.warning(f"Failed to get metrics for {symbol}: {response.status_code}")
                return None

        except Exception as e:
            self.logger.error(f"Error getting metrics for {symbol}: {e}")
            return None

    def analyze_social_activity(self, symbol):
        """
        Analyze social activity metrics for a symbol.

        Calculates an activity score based on:
        - Recent watcher additions
        - Posting activity
        - Sentiment changes

        Args:
            symbol (str): The stock symbol to analyze

        Returns:
            tuple: (bool, float) indicating if activity is high and activity score
        """
        metrics = self.get_symbol_sentiment_metrics(symbol)
        if not metrics:
            return False, 0

        # Calculate activity score
        activity_score = 0

        # Weight recent watcher additions
        if metrics['watchers_change'] > 0:
            activity_score += min(metrics['watchers_change'] / metrics['watchers'], 1) * 0.4

        # Weight posting activity
        if metrics['posts_change'] > 0:
            activity_score += min(metrics['posts_change'] / metrics['posts'], 1) * 0.3

        # Weight sentiment change
        if abs(metrics['sentiment_change']) > 0:
            activity_score += min(abs(metrics['sentiment_change']), 1) * 0.3

        is_active = activity_score > 0.5

        if is_active:
            self.logger.info(f"High social activity detected for {symbol}:")
            self.logger.info(f"Watcher Change: {metrics['watchers_change']}")
            self.logger.info(f"Post Change: {metrics['posts_change']}")
            self.logger.info(f"Sentiment Change: {metrics['sentiment_change']:.2f}")
            self.logger.info(f"Activity Score: {activity_score:.2f}")

        return is_active, activity_score
