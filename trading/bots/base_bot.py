import ssl
import urllib3

# Disable SSL verification (for testing only)
ssl._create_default_https_context = ssl._create_unverified_context
urllib3.disable_warnings()

import os
import alpaca_trade_api as tradeapi
from alpaca_trade_api.rest import REST
from datetime import datetime, timedelta
import logging
import pandas as pd
import numpy as np
from typing import List, Dict, Optional
import time
import json
from trading.utils.sentiment import analyze_sentiment
from trading.utils.technical import calculate_technical_indicators
from trading.utils.movement import analyze_price_movement
import config
import requests
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager

# Custom adapter to disable SSL verification
class NoVerifyAdapter(HTTPAdapter):
    def init_poolmanager(self, connections, maxsize, block=False):
        self.poolmanager = PoolManager(
            num_pools=connections,
            maxsize=maxsize,
            block=block,
            cert_reqs=ssl.CERT_NONE,
            assert_hostname=False
        )

# Create a session with the custom adapter
session = requests.Session()
session.mount('https://', NoVerifyAdapter())
session.verify = False

class BaseBot:
    def __init__(self, bot_type: str):
        self.bot_type = bot_type
        self.logger = logging.getLogger(bot_type)

        # Initialize Alpaca API client with custom session
        self.api = REST(
            key_id=os.getenv('ALPACA_API_KEY'),
            secret_key=os.getenv('ALPACA_SECRET_KEY'),
            base_url=os.getenv('ALPACA_BASE_URL'),
            api_version='v2',
            http_session=session
        )

        self.symbols = []
        self.positions = {}
        self.account = None
        self.trading_capital = config.TRADING_CAPITAL
        self.max_position_size = config.MAX_POSITION_SIZE
        self.max_portfolio_exposure = config.MAX_PORTFOLIO_EXPOSURE

        # Initialize bot
        self.initialize()

# ... existing code ...
