# Trading Bot Runbook

## Local Development
```bash
# Run locally
python3 run_bot.py --server-only --bot-type crypto

# Test local endpoints
curl http://localhost:8080/health
curl http://localhost:8080/status
curl http://localhost:8080/start
curl http://localhost:8080/stop
```

## Cloud Deployment
```bash
# Deploy to Cloud Run
gcloud run deploy trade-bot \
  --source . \
  --region us-west1 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars="ALPACA_API_KEY=AKGUEMUAJ5YNUBJ1RI1B,ALPACA_SECRET_KEY=bCK6QwP40XrOSn33qtEsSz0ZzqzcFESoVVdnpg1W,ALPACA_BASE_URL=https://api.alpaca.markets,BOT_TYPE=crypto"

# Get service URL
gcloud run services describe trade-bot --region us-west1 --format='value(status.url)'
```

## Production Endpoints
```bash
# Replace {URL} with the service URL from above command
curl {URL}/health
curl {URL}/status
curl {URL}/start
curl {URL}/stop
```

Example with current URL:
```bash
# Health check
curl https://trade-bot-859059000466.us-west1.run.app/health

# Check bot status
curl https://trade-bot-859059000466.us-west1.run.app/status

# Start the bot
curl https://trade-bot-859059000466.us-west1.run.app/start

# Stop the bot
curl https://trade-bot-859059000466.us-west1.run.app/stop
```

## Monitoring
```bash
# View logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=trade-bot" --limit 50

# Check service status
gcloud run services describe trade-bot --region us-west1
``` 
