#!/bin/bash

# Set bot type
export BOT_TYPE=crypto

# Start the Flask server using the PORT environment variable
python3 run_bot.py --server-only --bot-type $BOT_TYPE --port $PORT
