# Deployment Guide

## Overview

The trading system supports multiple bot types and deployment environments:
1. Cryptocurrency trading bot (24/7 operation)
2. Stock trading bot (market hours operation)
3. Local, cloud, or container deployment

## Local Deployment

### Prerequisites

1. **System Requirements**
   - Python 3.8+
   - pip package manager
   - Git
   - 2GB RAM minimum
   - Stable internet connection

2. **API Credentials**
   - Alpaca trading account
   - Paper trading API keys
   - Live trading API keys (optional)

### Setup Steps

1. **Clone Repository**
   ```bash
   git clone <repository-url>
   cd trade
   ```

2. **Create Python Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Unix/macOS
   venv\Scripts\activate     # Windows
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

### Running Locally

1. **Test Mode**
   ```bash
   # Crypto bot
   python run_bot.py --bot-type crypto --single-run

   # Stock bot
   python run_bot.py --bot-type stock --single-run
   ```

2. **Production Mode**
   ```bash
   # Crypto bot (24/7)
   python run_bot.py --bot-type crypto

   # Stock bot (market hours)
   python run_bot.py --bot-type stock
   ```

## Cloud Deployment

### Google Cloud Run

1. **Prerequisites**
   - Google Cloud account
   - gcloud CLI installed
   - Docker installed

2. **Build Container**
   ```bash
   # Build for crypto bot
   docker build -t gcr.io/$PROJECT_ID/crypto-bot \
     --build-arg BOT_TYPE=crypto .

   # Build for stock bot
   docker build -t gcr.io/$PROJECT_ID/stock-bot \
     --build-arg BOT_TYPE=stock .
   ```

3. **Push to Container Registry**
   ```bash
   # Push crypto bot
   docker push gcr.io/$PROJECT_ID/crypto-bot

   # Push stock bot
   docker push gcr.io/$PROJECT_ID/stock-bot
   ```

4. **Deploy to Cloud Run**
   ```bash
   # Deploy crypto bot
   gcloud run deploy crypto-bot \
     --image gcr.io/$PROJECT_ID/crypto-bot \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated

   # Deploy stock bot
   gcloud run deploy stock-bot \
     --image gcr.io/$PROJECT_ID/stock-bot \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated
   ```

### Environment Variables

1. **Required Variables**
   ```
   ALPACA_API_KEY=your_key
   ALPACA_SECRET_KEY=your_secret
   ALPACA_BASE_URL=https://paper-api.alpaca.markets
   BOT_TYPE=crypto|stock
   ```

2. **Optional Variables**
   ```
   LOG_LEVEL=INFO
   ALPHA_VANTAGE_API_KEY=your_key
   ```

## Container Deployment

### Dockerfile

```dockerfile
# Base image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Set bot type argument
ARG BOT_TYPE=crypto
ENV BOT_TYPE=$BOT_TYPE

# Run the bot
CMD ["python", "run_bot.py", "--bot-type", "${BOT_TYPE}"]
```

### Docker Commands

1. **Build Images**
   ```bash
   # Build crypto bot
   docker build -t crypto-bot \
     --build-arg BOT_TYPE=crypto .

   # Build stock bot
   docker build -t stock-bot \
     --build-arg BOT_TYPE=stock .
   ```

2. **Run Containers**
   ```bash
   # Run crypto bot
   docker run -d \
     --name crypto-bot \
     --env-file .env \
     crypto-bot

   # Run stock bot
   docker run -d \
     --name stock-bot \
     --env-file .env \
     stock-bot
   ```

3. **View Logs**
   ```bash
   # Crypto bot logs
   docker logs -f crypto-bot

   # Stock bot logs
   docker logs -f stock-bot
   ```

## Monitoring

### Logging

1. **Log Configuration**
   ```python
   logging.basicConfig(
       level=logging.INFO,
       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
   )
   ```

2. **Log Files**
   - Application logs
   - Trade logs
   - Error logs

### Health Checks

1. **API Connectivity**
   - Regular API status checks
   - Connection monitoring
   - Rate limit tracking

2. **Bot Status**
   - Trading status
   - Position monitoring
   - Performance metrics

3. **Market Status**
   - Crypto: 24/7 monitoring
   - Stocks: Market hours check

## Security

### API Keys

1. **Key Management**
   - Use environment variables
   - Never commit keys
   - Rotate regularly

2. **Access Control**
   - Minimal permissions
   - IP restrictions
   - Rate limiting

### Data Security

1. **Storage**
   - Secure credentials
   - Encrypted data
   - Regular backups

2. **Transmission**
   - HTTPS only
   - Secure API endpoints
   - Data validation

## Maintenance

### Updates

1. **Dependencies**
   ```bash
   pip install --upgrade -r requirements.txt
   ```

2. **Application Code**
   ```bash
   git pull origin main
   ```

### Backup

1. **Configuration**
   - Environment variables
   - Trading parameters
   - API credentials

2. **Data**
   - Trading history
   - Performance metrics
   - Log files

## Troubleshooting

### Common Issues

1. **Connection Problems**
   - Check API credentials
   - Verify network connectivity
   - Monitor rate limits

2. **Performance Issues**
   - Check resource usage
   - Monitor memory leaks
   - Review log files

### Recovery Steps

1. **Bot Failure**
   ```bash
   # Stop bots
   docker stop crypto-bot stock-bot

   # Check logs
   docker logs crypto-bot
   docker logs stock-bot

   # Restart bots
   docker start crypto-bot stock-bot
   ```

2. **Data Issues**
   - Verify data integrity
   - Check API responses
   - Clear cache if needed

## Scaling

### Horizontal Scaling

1. **Multiple Instances**
   - Separate configurations
   - Load balancing
   - Data synchronization

2. **Resource Allocation**
   - CPU requirements
   - Memory usage
   - Network bandwidth

### Performance Optimization

1. **Caching**
   - Market data
   - API responses
   - Trading signals

2. **Resource Usage**
   - Memory management
   - CPU optimization
   - Network efficiency
