import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import twitter
from textblob import TextBlob
import re
from typing import Dict, List, Tuple, Optional
from config import TWITTER_CONFIG

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SocialDataEngine:
    def __init__(self):
        self.cache = {}  # Cache for tweet data
        self.twitter_api = twitter.Api(
            consumer_key=TWITTER_CONFIG['API_KEY'],
            consumer_secret=TWITTER_CONFIG['API_SECRET'],
            access_token_key=TWITTER_CONFIG['ACCESS_TOKEN'],
            access_token_secret=TWITTER_CONFIG['ACCESS_TOKEN_SECRET']
        )

    def clean_tweet(self, text: str) -> str:
        """Clean tweet text."""
        text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
        text = re.sub(r'\@\w+|\#\w+', '', text)
        text = text.strip()
        return text

    def get_historical_tweets(self, symbol: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Get historical tweets for a symbol."""
        try:
            cache_key = f"{symbol}_{start_date.date()}_{end_date.date()}"
            if cache_key in self.cache:
                return self.cache[cache_key]

            # Build query
            cashtag = f"${symbol}"
            tweets = []
            max_id = None

            while len(tweets) < 1000:  # Limit to 1000 tweets
                try:
                    # Get tweets
                    new_tweets = self.twitter_api.GetSearch(
                        term=cashtag,
                        count=100,
                        max_id=max_id,
                        lang='en'
                    )

                    if not new_tweets:
                        break

                    for tweet in new_tweets:
                        tweet_date = datetime.strptime(tweet.created_at, '%a %b %d %H:%M:%S +0000 %Y')

                        if tweet_date < start_date:
                            break

                        if tweet_date <= end_date:
                            # Clean and analyze tweet
                            clean_text = self.clean_tweet(tweet.text)
                            if not clean_text:
                                continue

                            blob = TextBlob(clean_text)
                            sentiment = blob.sentiment.polarity

                            tweets.append({
                                'timestamp': tweet_date,
                                'text': clean_text,
                                'sentiment': sentiment,
                                'likes': tweet.favorite_count,
                                'retweets': tweet.retweet_count,
                                'user_followers': tweet.user.followers_count,
                                'is_verified': tweet.user.verified
                            })

                    max_id = new_tweets[-1].id - 1

                except twitter.error.TwitterError as e:
                    logger.error(f"Twitter API error: {str(e)}")
                    break

            df = pd.DataFrame(tweets)
            if not df.empty:
                df.set_index('timestamp', inplace=True)
                df.sort_index(inplace=True)

                # Calculate engagement score
                df['engagement'] = (df['likes'] + df['retweets'] * 2) * \
                                 (np.log1p(df['user_followers']) / 10) * \
                                 (1.5 if df['is_verified'] else 1.0)

                # Calculate weighted sentiment
                df['weighted_sentiment'] = df['sentiment'] * df['engagement']

                # Resample to 15-minute intervals
                resampled = df.resample('15T').agg({
                    'sentiment': 'mean',
                    'weighted_sentiment': 'sum',
                    'engagement': 'sum',
                    'likes': 'sum',
                    'retweets': 'sum'
                }).fillna(0)

                self.cache[cache_key] = resampled
                return resampled

            return pd.DataFrame()

        except Exception as e:
            logger.error(f"Error getting historical tweets for {symbol}: {str(e)}")
            return pd.DataFrame()

    def analyze_social_impact(self, tweets_df: pd.DataFrame, price_df: pd.DataFrame) -> Dict[str, float]:
        """Analyze correlation between social metrics and price movements."""
        try:
            if tweets_df.empty or price_df.empty:
                return {}

            # Align timestamps
            tweets_df = tweets_df.reindex(price_df.index, method='ffill')

            # Calculate price changes
            price_df['returns'] = price_df['Close'].pct_change()

            # Calculate correlations
            sentiment_corr = tweets_df['weighted_sentiment'].corr(price_df['returns'])
            engagement_corr = tweets_df['engagement'].corr(price_df['returns'])

            # Calculate lead-lag relationships
            sentiment_lead = []
            engagement_lead = []

            for i in range(1, 5):  # Test 1-4 periods ahead
                sentiment_lead.append(
                    tweets_df['weighted_sentiment'].shift(i).corr(price_df['returns'])
                )
                engagement_lead.append(
                    tweets_df['engagement'].shift(i).corr(price_df['returns'])
                )

            # Find optimal lead time
            max_sentiment_lead = max(sentiment_lead)
            max_engagement_lead = max(engagement_lead)
            optimal_sentiment_lag = sentiment_lead.index(max_sentiment_lead) + 1
            optimal_engagement_lag = engagement_lead.index(max_engagement_lead) + 1

            return {
                'sentiment_correlation': sentiment_corr,
                'engagement_correlation': engagement_corr,
                'max_sentiment_lead_correlation': max_sentiment_lead,
                'max_engagement_lead_correlation': max_engagement_lead,
                'optimal_sentiment_lag': optimal_sentiment_lag,
                'optimal_engagement_lag': optimal_engagement_lag
            }

        except Exception as e:
            logger.error(f"Error analyzing social impact: {str(e)}")
            return {}

    def find_high_impact_events(self, tweets_df: pd.DataFrame, price_df: pd.DataFrame,
                              min_price_move: float = 0.02) -> List[Dict]:
        """Find historical events where social metrics preceded significant price moves."""
        try:
            if tweets_df.empty or price_df.empty:
                return []

            # Calculate rolling metrics
            window = 12  # 3-hour window (12 * 15 minutes)
            tweets_df['sentiment_ma'] = tweets_df['weighted_sentiment'].rolling(window).mean()
            tweets_df['engagement_ma'] = tweets_df['engagement'].rolling(window).mean()

            # Calculate price changes
            price_df['forward_returns'] = price_df['Close'].pct_change(periods=4).shift(-4)  # 1-hour forward returns

            # Find significant price moves
            significant_moves = price_df[abs(price_df['forward_returns']) > min_price_move].index

            # Analyze social metrics before each significant move
            events = []
            for timestamp in significant_moves:
                try:
                    # Get social metrics for 3 hours before price move
                    start_idx = tweets_df.index.get_loc(timestamp) - window
                    if start_idx < 0:
                        continue

                    pre_move_data = tweets_df.iloc[start_idx:tweets_df.index.get_loc(timestamp)]

                    if pre_move_data.empty:
                        continue

                    # Calculate social metrics
                    avg_sentiment = pre_move_data['weighted_sentiment'].mean()
                    total_engagement = pre_move_data['engagement'].sum()
                    sentiment_trend = np.polyfit(range(len(pre_move_data)),
                                               pre_move_data['weighted_sentiment'], 1)[0]
                    engagement_trend = np.polyfit(range(len(pre_move_data)),
                                                pre_move_data['engagement'], 1)[0]

                    # Record event
                    events.append({
                        'timestamp': timestamp,
                        'price_move': price_df.loc[timestamp, 'forward_returns'],
                        'pre_move_sentiment': avg_sentiment,
                        'pre_move_engagement': total_engagement,
                        'sentiment_trend': sentiment_trend,
                        'engagement_trend': engagement_trend,
                        'tweet_count': len(pre_move_data)
                    })

                except Exception as e:
                    logger.error(f"Error analyzing event at {timestamp}: {str(e)}")
                    continue

            return sorted(events, key=lambda x: abs(x['price_move']), reverse=True)

        except Exception as e:
            logger.error(f"Error finding high impact events: {str(e)}")
            return []

    def calculate_social_signals(self, tweets_df: pd.DataFrame, lookback_window: int = 48) -> Dict[str, float]:
        """Calculate current social signals based on historical patterns."""
        try:
            if tweets_df.empty:
                return {}

            # Get recent data
            recent_data = tweets_df.iloc[-lookback_window:]

            if recent_data.empty:
                return {}

            # Calculate sentiment metrics
            sentiment_mean = recent_data['weighted_sentiment'].mean()
            sentiment_std = recent_data['weighted_sentiment'].std()
            sentiment_zscore = (recent_data['weighted_sentiment'].iloc[-1] - sentiment_mean) / sentiment_std \
                             if sentiment_std > 0 else 0

            # Calculate engagement metrics
            engagement_mean = recent_data['engagement'].mean()
            engagement_std = recent_data['engagement'].std()
            engagement_zscore = (recent_data['engagement'].iloc[-1] - engagement_mean) / engagement_std \
                              if engagement_std > 0 else 0

            # Calculate trends
            sentiment_trend = np.polyfit(range(len(recent_data)), recent_data['weighted_sentiment'], 1)[0]
            engagement_trend = np.polyfit(range(len(recent_data)), recent_data['engagement'], 1)[0]

            # Calculate acceleration
            sentiment_accel = np.polyfit(range(len(recent_data)), recent_data['weighted_sentiment'], 2)[0]
            engagement_accel = np.polyfit(range(len(recent_data)), recent_data['engagement'], 2)[0]

            return {
                'current_sentiment': recent_data['weighted_sentiment'].iloc[-1],
                'sentiment_zscore': sentiment_zscore,
                'sentiment_trend': sentiment_trend,
                'sentiment_acceleration': sentiment_accel,
                'current_engagement': recent_data['engagement'].iloc[-1],
                'engagement_zscore': engagement_zscore,
                'engagement_trend': engagement_trend,
                'engagement_acceleration': engagement_accel
            }

        except Exception as e:
            logger.error(f"Error calculating social signals: {str(e)}")
            return {}
