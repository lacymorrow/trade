# Trading Bot

A full-stack trading bot that combines technical analysis, sentiment analysis, and automated trading execution for both traditional stocks and cryptocurrencies.

## Features

- 🤖 Automated trading for stocks and cryptocurrencies
- 📊 Real-time market data analysis
- 🔍 Social media sentiment analysis
- 📈 Technical indicator calculations
- 🛡️ Built-in safety checks and risk management
- 🎯 Position sizing and portfolio management
- 🖥️ Modern web interface built with Next.js
- 📱 Responsive design with Shadcn UI
- 🚀 Deployed on Google Cloud Run

## Documentation

- [Architecture Overview](docs/architecture.md)
- [API Documentation](docs/api.md)
- [Development Guide](docs/development.md)
- [Deployment Guide](docs/deployment.md)

## Quick Start

1. **Prerequisites**
   - Python 3.8+
   - Node.js 18+
   - pnpm
   - Google Cloud CLI (for deployment)

2. **Installation**
   ```bash
   # Clone repository
   git clone <repository-url>
   cd trading-bot

   # Install dependencies
   python -m venv venv
   source venv/bin/activate  # or `venv\Scripts\activate` on Windows
   pip install -r requirements.txt

   pnpm install
   ```

3. **Configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your API credentials
   ```

4. **Run Development Servers**
   ```bash
   # Start Next.js development server
   pnpm dev

   # In another terminal, run the trading bot
   python run_bot.py --test
   ```

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Frontend UI   │────▶│   Backend API   │────▶│   Trading Core  │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │                        │
        │                       │                        │
        ▼                       ▼                        ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  User Controls  │     │  Data Analysis  │     │ Market Analysis │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## Project Structure

```
project/
├── src/                    # Frontend application
│   ├── app/               # Next.js pages and API routes
│   ├── components/        # React components
│   ├── lib/              # Utility functions
│   └── hooks/            # Custom React hooks
├── trading/              # Trading core
│   ├── core/            # Core trading components
│   ├── bots/            # Bot implementations
│   ├── analysis/        # Analysis engines
│   └── utils/           # Utilities
├── docs/                # Documentation
├── tests/               # Test suites
└── config/             # Configuration files
```

## Configuration

The bot can be configured through:
- Environment variables (`.env`)
- Configuration files (`config/`)
- Command-line arguments
- Web interface

See the [Development Guide](docs/development.md) for detailed configuration options.

## Development

See the [Development Guide](docs/development.md) for detailed instructions on:
- Setting up the development environment
- Adding new features
- Testing
- Debugging
- Performance optimization

## API

The bot provides a RESTful API and WebSocket endpoints for:
- Bot control
- Trading operations
- Market analysis
- Portfolio management

See the [API Documentation](docs/api.md) for detailed endpoint specifications.

## Deployment

See the [Deployment Guide](docs/deployment.md) for instructions on:
- Local deployment
- Cloud deployment
- Environment setup
- Monitoring
- Troubleshooting

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## Security

- Never commit API keys or secrets
- Use environment variables for sensitive data
- Follow security best practices
- Keep dependencies updated

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support:
1. Check the documentation
2. Open an issue
3. Contact the maintainers

## Acknowledgments

- [Alpaca Markets](https://alpaca.markets/) for trading API
- [Next.js](https://nextjs.org/) for the frontend framework
- [Shadcn UI](https://ui.shadcn.com/) for UI components
- [Google Cloud](https://cloud.google.com/) for hosting
