# Deployment Guide

## Overview

The trading bot can be deployed in multiple environments:
1. Local deployment for development and testing
2. Cloud deployment for production use
3. Container deployment for scalability

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
   python run_bot.py --single-run
   ```

2. **Production Mode**
   ```bash
   python run_bot.py
   ```

## Cloud Deployment

### Google Cloud Run

1. **Prerequisites**
   - Google Cloud account
   - gcloud CLI installed
   - Docker installed

2. **Build Container**
   ```bash
   docker build -t gcr.io/$PROJECT_ID/trade-app .
   ```

3. **Push to Container Registry**
   ```bash
   docker push gcr.io/$PROJECT_ID/trade-app
   ```

4. **Deploy to Cloud Run**
   ```bash
   gcloud run deploy trade-app \
     --image gcr.io/$PROJECT_ID/trade-app \
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

# Run the bot
CMD ["python", "run_bot.py"]
```

### Docker Commands

1. **Build Image**
   ```bash
   docker build -t trade-bot .
   ```

2. **Run Container**
   ```bash
   docker run -d \
     --name trade-bot \
     --env-file .env \
     trade-bot
   ```

3. **View Logs**
   ```bash
   docker logs -f trade-bot
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
   # Stop bot
   docker stop trade-bot

   # Check logs
   docker logs trade-bot

   # Restart bot
   docker start trade-bot
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
