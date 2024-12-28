# Trading Bot Deployment Guide

## Prerequisites
1. Google Cloud CLI installed
2. Project initialized (`gcloud init`)
3. Required APIs enabled:
   ```bash
   gcloud services enable cloudbuild.googleapis.com run.googleapis.com cloudscheduler.googleapis.com
   ```

## Environment Variables
Create a `.env` file with these variables (replace with your values):
```bash
ALPACA_API_KEY=your_api_key
ALPACA_SECRET_KEY=your_secret_key
ALPACA_BASE_URL=https://api.alpaca.markets
TWITTER_API_KEY=your_twitter_key
TWITTER_API_SECRET=your_twitter_secret
TWITTER_ACCESS_TOKEN=your_twitter_token
TWITTER_ACCESS_TOKEN_SECRET=your_twitter_token_secret
STOCKTWITS_ACCESS_TOKEN=your_stocktwits_token
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key
CRON_SECRET=your_cron_secret
UI_SECRET=your_ui_secret
```

## One-Command Deployment
```bash
gcloud builds submit \
  --substitutions=_ALPACA_API_KEY="your_api_key",\
_ALPACA_SECRET_KEY="your_secret_key",\
_ALPACA_BASE_URL="https://api.alpaca.markets",\
_TWITTER_API_KEY="your_twitter_key",\
_TWITTER_API_SECRET="your_twitter_secret",\
_TWITTER_ACCESS_TOKEN="your_twitter_token",\
_TWITTER_ACCESS_TOKEN_SECRET="your_twitter_token_secret",\
_STOCKTWITS_ACCESS_TOKEN="your_stocktwits_token",\
_ALPHA_VANTAGE_API_KEY="your_alpha_vantage_key",\
_CRON_SECRET="your_cron_secret",\
_UI_SECRET="your_ui_secret" \
  --region=us-central1
```

## Required Files

### 1. Dockerfile
```dockerfile
# Use Node.js base image
FROM node:18-alpine AS builder

# Set working directory
WORKDIR /app

# Install Python and dependencies
RUN apk add --no-cache python3 py3-pip gcc musl-dev python3-dev ca-certificates openssl

# Update certificates
RUN update-ca-certificates

# Install pnpm globally
RUN npm install -g pnpm@latest

# Copy package files
COPY package*.json pnpm-lock.yaml ./
COPY requirements.txt ./

# Create and activate virtual environment
RUN python3 -m venv /venv
ENV PATH="/venv/bin:$PATH"
ENV PYTHONPATH="/venv/lib/python3.12/site-packages"
ENV SSL_CERT_FILE="/etc/ssl/certs/ca-certificates.crt"
ENV REQUESTS_CA_BUNDLE="/etc/ssl/certs/ca-certificates.crt"

# Install dependencies
RUN pnpm install --frozen-lockfile
RUN pip3 install --no-cache-dir --trusted-host pypi.org --trusted-host files.pythonhosted.org pip setuptools wheel && \
    pip3 install --no-cache-dir --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt

# Copy source code
COPY . .

# Build Next.js app
RUN pnpm build

# Production image
FROM node:18-alpine

# Install Python and dependencies
RUN apk add --no-cache python3 py3-pip ca-certificates openssl

# Update certificates
RUN update-ca-certificates

# Set shell for pnpm
ENV SHELL=/bin/sh

# Install pnpm globally and ensure it's in PATH
RUN npm install -g pnpm@latest
ENV PNPM_HOME="/root/.local/share/pnpm"
ENV PATH="${PNPM_HOME}:$PATH"

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /venv /venv
ENV PATH="/venv/bin:$PATH"
ENV PYTHONPATH="/venv/lib/python3.12/site-packages"
ENV SSL_CERT_FILE="/etc/ssl/certs/ca-certificates.crt"
ENV REQUESTS_CA_BUNDLE="/etc/ssl/certs/ca-certificates.crt"

# Copy built assets from builder
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/pnpm-lock.yaml ./pnpm-lock.yaml
COPY --from=builder /app/run_bot.py ./run_bot.py
COPY --from=builder /app/trading ./trading

# Install NLTK data
RUN python3 -c "import nltk; nltk.download('vader_lexicon'); nltk.download('punkt')"

# Set environment variables
ENV NODE_ENV=production
ENV PORT=8080
ENV HOST=0.0.0.0
ENV NEXT_TELEMETRY_DISABLED=1

# Create non-root user
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nextjs -u 1001 && \
    chown -R nextjs:nodejs /app && \
    chmod -R 755 /app && \
    mkdir -p /root/nltk_data && \
    chown -R nextjs:nodejs /root/nltk_data && \
    chmod -R 755 /root/nltk_data

# Switch to non-root user
USER nextjs

# Expose port
EXPOSE 8080

# Start the application
CMD ["pnpm", "next", "start", "-p", "8080", "-H", "0.0.0.0"]
```

### 2. cloudbuild.yaml
```yaml
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/trading-bot', '.']

  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/trading-bot']

  - name: 'gcr.io/cloud-builders/gcloud'
    args:
      - 'run'
      - 'deploy'
      - 'trading-bot'
      - '--image'
      - 'gcr.io/$PROJECT_ID/trading-bot'
      - '--region'
      - 'us-central1'
      - '--platform'
      - 'managed'
      - '--allow-unauthenticated'
      - '--set-env-vars'
      - 'ALPACA_API_KEY=${_ALPACA_API_KEY},ALPACA_SECRET_KEY=${_ALPACA_SECRET_KEY},ALPACA_BASE_URL=${_ALPACA_BASE_URL},TWITTER_API_KEY=${_TWITTER_API_KEY},TWITTER_API_SECRET=${_TWITTER_API_SECRET},TWITTER_ACCESS_TOKEN=${_TWITTER_ACCESS_TOKEN},TWITTER_ACCESS_TOKEN_SECRET=${_TWITTER_ACCESS_TOKEN_SECRET},STOCKTWITS_ACCESS_TOKEN=${_STOCKTWITS_ACCESS_TOKEN},ALPHA_VANTAGE_API_KEY=${_ALPHA_VANTAGE_API_KEY},CRON_SECRET=${_CRON_SECRET},UI_SECRET=${_UI_SECRET}'

images:
  - 'gcr.io/$PROJECT_ID/trading-bot'
```

## Post-Deployment Verification

### 1. Check service status
```bash
gcloud run services describe trading-bot --platform managed --region us-central1
```

### 2. View logs
```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=trading-bot" --limit 10
```

### 3. Test the endpoint
```bash
curl -I https://trading-bot-[YOUR-PROJECT-ID].us-central1.run.app
```

## Troubleshooting

### 1. Build failures
Check build logs:
```bash
gcloud builds log [BUILD_ID]
```

### 2. Container issues
Check container logs:
```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=trading-bot" --limit 50
```

### 3. Permission issues
Ensure the service account has the necessary roles:
```bash
gcloud projects add-iam-policy-binding [PROJECT_ID] \
    --member="serviceAccount:[SERVICE_ACCOUNT]" \
    --role="roles/run.admin"
```

## Security Notes
1. Never commit `.env` files or sensitive credentials to version control
2. Use Secret Manager for production deployments
3. Regularly rotate API keys and secrets
4. Monitor service usage and set up alerts for unusual activity

## Local Development
1. Install dependencies:
```bash
pnpm install
pip install -r requirements.txt
```

2. Run the development server:
```bash
pnpm dev
```

3. Test the trading bot:
```bash
python run_bot.py
```

## Common Issues and Solutions

### SSL Certificate Issues
If you encounter SSL certificate errors:
1. Ensure certificates are properly mounted in the container
2. Verify SSL environment variables are set
3. Check if the base image has updated certificates

### Port Binding Issues
If the container fails to start due to port issues:
1. Verify PORT and HOST environment variables
2. Check for port conflicts
3. Ensure the container has proper permissions

### Memory Issues
If the container crashes due to memory:
1. Adjust memory limits in Cloud Run configuration
2. Optimize the application's memory usage
3. Consider implementing memory monitoring

## Maintenance

### Regular Updates
1. Keep dependencies updated
2. Monitor security advisories
3. Test updates in staging before production

### Monitoring
1. Set up Cloud Monitoring
2. Configure alerts for:
   - Error rates
   - Response times
   - Memory usage
   - CPU usage

### Backup
1. Regularly backup configuration
2. Document all custom settings
3. Maintain deployment history

## Support
For issues and support:
1. Check Cloud Run logs
2. Review application logs
3. Consult Google Cloud documentation
4. Open GitHub issues for bugs
