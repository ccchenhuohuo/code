# Stock Analysis and Prediction Platform

A comprehensive web application for analyzing stock market data, visualizing trends, and predicting future prices using Monte Carlo simulation.

## Features

- **Stock Data Visualization**: Interactive charts for historical price and volume data
- **Fundamental Analysis**: View key financial metrics for selected stocks
- **AI-Powered Assistant**: Gemini AI integration for natural language financial queries
- **Price Prediction**: Monte Carlo simulation for probabilistic price forecasting
- **Data Collection**: Automated gathering of market and fundamental data

## Project Structure

- `app.py`: Main Flask web application
- `stock_api.py`: Interface for external stock market data APIs
- `read_stock_data.py`: Data visualization and Monte Carlo simulation
- `obtain_stock_features.py`: Data collection and database storage
- `templates/index.html`: Web frontend interface

## Setup Instructions

### Prerequisites

- Python 3.8+
- MySQL database
- Required Python packages (see below)

### Database Setup

1. Create a MySQL database named `stock_data`
2. Update database credentials in the configuration section of each script if needed:
   ```python
   DB_CONFIG = {
       'user': 'root',
       'password': 'your_password',
       'host': 'localhost',
       'port': '3306',
       'database': 'stock_data'
   }
   ```

### Installation

1. Clone the repository
2. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the data collection script to populate the database:
   ```bash
   python obtain_stock_features.py
   ```
4. Start the web application:
   ```bash
   python app.py
   ```
   
> **Note**: The application runs on port 5001 to avoid conflicts with MacOS AirPlay service on port 5000.

## Data Sources

- Historical market data: Yahoo Finance API (via yfinance)
- Real-time quotes: Alpha Vantage API
- Fundamental data: Combination of APIs and mock data for demonstration

## Prediction Methodology

The application uses Monte Carlo simulation to generate probabilistic forecasts for stock prices:

1. Calculates historical logarithmic returns
2. Determines drift (μ) and volatility (σ) parameters
3. Simulates thousands of potential price paths
4. Aggregates results to provide expected values and confidence intervals

## API Keys

- The application uses Alpha Vantage API for some data retrieval. A demo key is included, but for production use, please obtain your own API key from [Alpha Vantage](https://www.alphavantage.co/support/#api-key).
- Gemini AI functionality requires a Google API key, which should be updated in the application configuration.

## License

This project is provided for educational purposes. Please ensure you comply with all data provider terms of service.

## Disclaimer

This software is for educational and research purposes only. It is not intended to provide financial advice. Always conduct your own research before making investment decisions. 