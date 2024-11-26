import twitter
import requests
from textblob import TextBlob
from config import TWITTER_CONFIG, STOCKTWITS_CONFIG, MIN_TWEETS, SENTIMENT_THRESHOLD
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    def __init__(self):
        self.twitter_api = twitter.Api(
            consumer_key=TWITTER_CONFIG['API_KEY'],
            consumer_secret=TWITTER_CONFIG['API_SECRET'],
            access_token_key=TWITTER_CONFIG['ACCESS_TOKEN'],
            access_token_secret=TWITTER_CONFIG['ACCESS_TOKEN_SECRET']
        )

    def analyze_twitter_sentiment(self, symbol, max_tweets=100):
        try:
            query = f"${symbol} OR #{symbol}"
            tweets = self.twitter_api.GetSearch(term=query, count=max_tweets, lang='en')

            if len(tweets) < MIN_TWEETS:
                logger.warning(f"Not enough tweets found for {symbol}")
                return None

            sentiments = []
            for tweet in tweets:
                analysis = TextBlob(tweet.text)
                sentiments.append(analysis.sentiment.polarity)

            avg_sentiment = sum(sentiments) / len(sentiments)
            logger.info(f"Average sentiment for {symbol}: {avg_sentiment}")
            return avg_sentiment

        except Exception as e:
            logger.error(f"Error analyzing Twitter sentiment: {str(e)}")
            return None

    def analyze_stocktwits_sentiment(self, symbol):
        try:
            url = f"https://api.stocktwits.com/api/2/streams/symbol/{symbol}.json"
            response = requests.get(url)
            data = response.json()

            if 'messages' not in data:
                return None

            messages = data['messages']
            if len(messages) < MIN_TWEETS:
                return None

            sentiments = []
            for message in messages:
                if 'entities' in message and 'sentiment' in message['entities']:
                    if message['entities']['sentiment']['basic'] == 'Bullish':
                        sentiments.append(1)
                    elif message['entities']['sentiment']['basic'] == 'Bearish':
                        sentiments.append(-1)

            if not sentiments:
                return None

            avg_sentiment = sum(sentiments) / len(sentiments)
            logger.info(f"StockTwits sentiment for {symbol}: {avg_sentiment}")
            return avg_sentiment

        except Exception as e:
            logger.error(f"Error analyzing StockTwits sentiment: {str(e)}")
            return None

    def get_combined_sentiment(self, symbol):
        twitter_sentiment = self.analyze_twitter_sentiment(symbol)
        stocktwits_sentiment = self.analyze_stocktwits_sentiment(symbol)

        sentiments = [s for s in [twitter_sentiment, stocktwits_sentiment] if s is not None]
        if not sentiments:
            return None

        combined_sentiment = sum(sentiments) / len(sentiments)
        return combined_sentiment if abs(combined_sentiment) >= SENTIMENT_THRESHOLD else None
