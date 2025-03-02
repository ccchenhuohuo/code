# Stock Trading and Analysis Platform

A comprehensive web application for analyzing stock market data, visualizing trends, predicting future prices using Monte Carlo simulation, and simulating stock trading with virtual accounts.

## Features

- **Real-time Stock Data**: Interactive charts for real-time price and volume data
- **Historical Analysis**: Visualize and analyze historical stock performance
- **Fundamental Analysis**: View key financial metrics for selected stocks
- **AI-Powered Assistant**: Gemini AI integration for natural language financial queries
- **Price Prediction**: Monte Carlo simulation for probabilistic price forecasting
- **Trading Simulation**: Practice trading with a virtual account and track performance
- **Account Management**: User registration, authentication, and virtual fund management
- **Portfolio Tracking**: Monitor positions, profits/losses, and transaction history

## Project Structure

- `app.py`: Main Flask web application with API endpoints
- `stock_api.py`: Interface for external stock market data APIs
- `read_stock_data.py`: Data visualization and Monte Carlo simulation logic
- `obtain_stock_features.py`: Data collection and database storage utilities
- `db_init.py`: Database initialization and schema creation
- `templates/index.html`: Web frontend interface

## Setup Instructions

### Prerequisites

- Python 3.8+
- MySQL 8.0+
- Required Python packages (listed in requirements.txt)

### Database Setup

1. Create a MySQL database named `stock_data`
2. Update database credentials in the configuration section if needed:
   ```python
   DB_CONFIG = {
       'user': 'root',
       'password': 'your_password',
       'host': 'localhost',
       'port': '3306',
       'database': 'stock_data'
   }
   ```
3. Initialize the database schema:
   ```bash
   python db_init.py
   ```

### Installation

1. Clone the repository
2. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the data collection script to populate the database with stock data:
   ```bash
   python obtain_stock_features.py
   ```
4. Start the web application:
   ```bash
   python app.py
   ```
   
> **Note**: The application runs on port 5001 to avoid conflicts with MacOS AirPlay service on port 5000.

## Default Accounts

The database initialization script creates a default admin account:
- Username: admin
- Password: admin123

Regular user accounts start with 100,000 units of virtual currency for trading simulation.

## Data Sources

- Historical market data: Yahoo Finance API (via yfinance)
- Real-time quotes: Alpha Vantage API
- Fundamental data: Combination of APIs and simulated data

## Prediction Methodology

The application uses Monte Carlo simulation to generate probabilistic forecasts:

1. Calculates historical logarithmic returns
2. Determines drift (μ) and volatility (σ) parameters
3. Simulates thousands of potential price paths
4. Aggregates results to provide expected values and confidence intervals

## API Keys

- Alpha Vantage API: A demo key is included, but for production use, please obtain your own API key from [Alpha Vantage](https://www.alphavantage.co/support/#api-key).
- Gemini AI: Requires a Google API key for AI assistant functionality.

## Recent Updates

- UI has been completely translated to English
- Code has been optimized and redundant parts removed
- File naming has been standardized
- Database schema improved for better performance

## License

This project is provided for educational purposes. Please ensure you comply with all data provider terms of service.

## Disclaimer

This software is for educational and research purposes only. It is not intended to provide financial advice. Always conduct your own research before making investment decisions.

*Last updated: March 3, 2025* 