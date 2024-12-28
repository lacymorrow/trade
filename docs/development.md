# Development Guide

## Getting Started

### Prerequisites
1. Python 3.8+
2. Node.js 18+
3. pnpm
4. Git
5. Google Cloud CLI (for deployment)

### Local Development Setup

1. **Clone the Repository**
```bash
git clone <repository-url>
cd trading-bot
```

2. **Install Dependencies**
```bash
# Install Python dependencies
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt

# Install Node.js dependencies
pnpm install
```

3. **Configure Environment**
```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your credentials
nano .env
```

4. **Run Development Servers**
```bash
# Start Next.js development server
pnpm dev

# In another terminal, run the trading bot
python run_bot.py --test
```

## Project Structure

### Frontend (`src/`)
```
src/
├── app/                    # Next.js app directory
│   ├── api/               # API routes
│   ├── components/        # React components
│   └── pages/            # Page components
├── lib/                   # Utility functions
└── hooks/                 # Custom React hooks
```

### Backend (`trading/`)
```
trading/
├── core/                  # Core trading components
├── bots/                 # Bot implementations
├── analysis/             # Analysis engines
└── utils/                # Utilities
```

## Development Workflow

### 1. Code Style
- Follow PEP 8 for Python code
- Use ESLint and Prettier for TypeScript/JavaScript
- Use meaningful variable and function names
- Add comments for complex logic

### 2. Git Workflow
```bash
# Create feature branch
git checkout -b feature/new-feature

# Make changes and commit
git add .
git commit -m "feat: add new feature"

# Push changes
git push origin feature/new-feature
```

### 3. Testing
```bash
# Run Python tests
python -m pytest

# Run JavaScript tests
pnpm test

# Run specific test file
python -m pytest tests/test_bot.py
```

## Common Development Tasks

### 1. Adding a New Trading Strategy
1. Create strategy class in `trading/strategies/`
2. Implement required methods:
   - `analyze_market()`
   - `generate_signals()`
   - `execute_trade()`
3. Add configuration in `config.py`
4. Add tests in `tests/strategies/`

### 2. Adding UI Components
1. Create component in `src/components/`
2. Add styles using Tailwind CSS
3. Add to relevant pages
4. Add tests using React Testing Library

### 3. Adding API Endpoints
1. Create route in `src/app/api/`
2. Implement endpoint logic
3. Add authentication if required
4. Add tests in `tests/api/`

## Testing

### 1. Unit Tests
```bash
# Run all unit tests
python -m pytest tests/unit/

# Run with coverage
python -m pytest --cov=trading tests/unit/
```

### 2. Integration Tests
```bash
# Run integration tests
python -m pytest tests/integration/

# Run specific integration test
python -m pytest tests/integration/test_alpaca.py
```

### 3. End-to-End Tests
```bash
# Run E2E tests
pnpm test:e2e
```

## Debugging

### 1. Python Debugging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Add debug points
logger.debug("Variable value: %s", variable)
```

### 2. Frontend Debugging
```typescript
// Use React DevTools
import { useEffect } from 'react'

useEffect(() => {
  console.log('Component state:', state)
}, [state])
```

## Performance Optimization

### 1. Python Optimization
- Use profiling tools
- Optimize database queries
- Cache API responses
- Use async/await for I/O operations

### 2. Frontend Optimization
- Implement code splitting
- Use React.memo for expensive components
- Optimize images and assets
- Use proper loading states

## Error Handling

### 1. Python Exceptions
```python
try:
    # Risky operation
    result = api.execute_trade(order)
except ApiError as e:
    logger.error("API Error: %s", str(e))
    # Handle error appropriately
except Exception as e:
    logger.exception("Unexpected error")
    # Handle unexpected errors
```

### 2. Frontend Errors
```typescript
try {
  const response = await api.executeTrade(order)
} catch (error) {
  if (error instanceof ApiError) {
    // Handle API error
    toast.error(error.message)
  } else {
    // Handle unexpected error
    console.error('Unexpected error:', error)
    toast.error('An unexpected error occurred')
  }
}
```

## Configuration Management

### 1. Environment Variables
```bash
# Development
source .env.development

# Production
source .env.production
```

### 2. Feature Flags
```python
if FEATURES.get('new_trading_strategy'):
    # Implement new strategy
    strategy = NewTradingStrategy()
else:
    # Use default strategy
    strategy = DefaultStrategy()
```

## Monitoring and Logging

### 1. Application Logs
```python
# Add structured logging
logger.info("Trade executed", extra={
    'symbol': trade.symbol,
    'price': trade.price,
    'quantity': trade.quantity
})
```

### 2. Performance Metrics
```python
from prometheus_client import Counter, Gauge

trades_counter = Counter('trades_total', 'Total trades executed')
portfolio_value = Gauge('portfolio_value', 'Current portfolio value')
```

## Security Best Practices

1. **API Security**
   - Use environment variables for secrets
   - Implement rate limiting
   - Validate all inputs
   - Use HTTPS for all requests

2. **Authentication**
   - Implement JWT authentication
   - Use secure session management
   - Implement proper logout

3. **Data Security**
   - Encrypt sensitive data
   - Implement proper access control
   - Regular security audits

## Deployment

### 1. Local Testing
```bash
# Build application
pnpm build

# Test production build
pnpm start
```

### 2. Cloud Deployment
```bash
# Build and deploy to Google Cloud Run
gcloud builds submit
```

## Troubleshooting

### Common Issues

1. **API Connection Issues**
   - Check API credentials
   - Verify network connectivity
   - Check API rate limits

2. **Database Issues**
   - Check connection string
   - Verify database permissions
   - Check query performance

3. **Memory Issues**
   - Monitor memory usage
   - Check for memory leaks
   - Implement proper cleanup

## Contributing

1. **Code Reviews**
   - Follow pull request template
   - Add proper documentation
   - Include tests
   - Update relevant docs

2. **Documentation**
   - Keep README updated
   - Document API changes
   - Update architecture docs
   - Add inline comments 
