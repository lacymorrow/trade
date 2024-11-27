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

    def get_sentiment_data(self, symbol, lookback_hours=1):
        """Get sentiment data from multiple sources"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=lookback_hours)

        # Collect social media posts
        twitter_posts = self._get_twitter_posts(symbol, start_time, end_time)
        stocktwits_posts = self._get_stocktwits_posts(symbol, start_time, end_time)

        # Combine and analyze posts
        all_posts = twitter_posts + stocktwits_posts
        if len(all_posts) < MIN_SOCIAL_POSTS:
            # Use cached sentiment if available
            cached_sentiment = self._get_cached_sentiment(symbol)
            if cached_sentiment is not None:
                return cached_sentiment

            # If no posts but symbol is trending, assign base sentiment
            if symbol in self.get_trending_stocks():
                logger.info(f"Using base sentiment for trending symbol {symbol}")
                return pd.Series([0.1], index=[end_time])  # Slight bullish bias for trending stocks

            logger.warning(f"Insufficient posts for {symbol}: {len(all_posts)} < {MIN_SOCIAL_POSTS}")
            return None

        # Create time series of sentiment
        sentiment_df = self._create_sentiment_timeseries(all_posts, start_time, end_time)
        self._cache_sentiment(symbol, sentiment_df)
        return sentiment_df

    def _get_cached_sentiment(self, symbol):
        """Get cached sentiment data"""
        # Implement simple in-memory cache
        if hasattr(self, '_sentiment_cache'):
            cache_entry = self._sentiment_cache.get(symbol)
            if cache_entry and (datetime.now() - cache_entry['timestamp']).seconds < 300:  # 5 min cache
                return cache_entry['data']
        return None

    def _cache_sentiment(self, symbol, sentiment_data):
        """Cache sentiment data"""
        if not hasattr(self, '_sentiment_cache'):
            self._sentiment_cache = {}
        self._sentiment_cache[symbol] = {
            'data': sentiment_data,
            'timestamp': datetime.now()
        }

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
            # Clean text
            text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
            text = re.sub(r'\@\w+|\#\w+', '', text)

            # Analyze sentiment
            analysis = TextBlob(text)

            # Amplify sentiment based on keywords
            score = analysis.sentiment.polarity

            # Bullish keywords
            if re.search(r'\b(buy|long|bullish|calls|moon|rocket|squeeze)\b', text.lower()):
                score = min(1.0, score + 0.3)

            # Bearish keywords
            if re.search(r'\b(sell|short|bearish|puts|dump|crash)\b', text.lower()):
                score = max(-1.0, score - 0.3)

            return score
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

        Args:
            symbol (str): The stock symbol to analyze

        Returns:
            tuple: (bool, float) indicating if activity is high and activity score
        """
        # Get StockTwits metrics
        st_metrics = self.get_symbol_sentiment_metrics(symbol)
        if not st_metrics:
            return False, 0

        # Calculate activity score (now 100% weight on StockTwits)
        activity_score = 0

        # Base activity (50% weight)
        watchers = st_metrics.get('watchers', 0)
        posts = st_metrics.get('posts', 0)
        sentiment = st_metrics.get('sentiment', 0)

        if watchers > 0:
            activity_score += min(watchers / 500, 1) * 0.2  # Scaled by watchers (more lenient)
        if posts > 0:
            activity_score += min(posts / 25, 1) * 0.15  # Scaled by post count (more lenient)
        if abs(sentiment) > 0:
            activity_score += min(abs(sentiment), 1) * 0.15  # Scale by sentiment strength

        # Recent activity changes (50% weight)
        watchers_change = st_metrics.get('watchers_change', 0)
        posts_change = st_metrics.get('posts_change', 0)
        sentiment_change = st_metrics.get('sentiment_change', 0)

        if watchers > 0 and watchers_change > 0:
            activity_score += min(watchers_change / watchers, 1) * 0.2
        if posts > 0 and posts_change > 0:
            activity_score += min(posts_change / posts, 1) * 0.15
        if abs(sentiment_change) > 0:
            activity_score += min(abs(sentiment_change), 1) * 0.15

        # Lower threshold and add logging
        is_active = activity_score > 0.3  # Reduced from 0.5

        if is_active:
            self.logger.info(f"High social activity detected for {symbol}:")
            self.logger.info(f"Watchers: {watchers} (Change: {watchers_change})")
            self.logger.info(f"Posts: {posts} (Change: {posts_change})")
            self.logger.info(f"Sentiment: {sentiment:.2f} (Change: {sentiment_change:.2f})")
            self.logger.info(f"Activity Score: {activity_score:.2f}")
        else:
            self.logger.debug(f"Low social activity for {symbol} (Score: {activity_score:.2f})")

        return is_active, activity_score

    def _get_twitter_metrics(self, symbol, lookback_hours=24):
        """Get Twitter metrics for a symbol."""
        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=lookback_hours)

            # Get recent tweets
            tweets = self._get_twitter_posts(symbol, start_time, end_time)
            if not tweets:
                return None

            # Calculate metrics
            tweet_count = len(tweets)

            # Calculate engagement
            total_engagement = sum(
                tweet.get('likes', 0) + tweet.get('retweets', 0) * 2
                for tweet in tweets
            )

            # Calculate sentiment
            sentiments = [
                self._analyze_text_sentiment(tweet['text'])
                for tweet in tweets
            ]
            avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0

            # Calculate tweet velocity (change)
            recent_tweets = [
                t for t in tweets
                if (end_time - t['timestamp']).total_seconds() <= 3600  # Last hour
            ]
            tweet_change = len(recent_tweets)

            return {
                'tweet_count': tweet_count,
                'engagement': total_engagement,
                'sentiment': avg_sentiment,
                'tweet_change': tweet_change
            }

        except Exception as e:
            self.logger.error(f"Error getting Twitter metrics: {e}")
            return None
