"""
Stock Data Visualization Module
Reads stock data from database and generates Monte Carlo prediction visualizations
"""
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
from datetime import timedelta
import matplotlib.gridspec as gridspec

# ===================== Database Connection ===================== #
DB_CONFIG = {
    'user': 'root',
    'password': 'Cyy-20030611',
    'host': 'localhost',
    'port': '3306',
    'database': 'stock_data'
}

# Create database connection string
connection_string = f"mysql+mysqlconnector://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}?charset=utf8"
engine = create_engine(connection_string, echo=False)

# Read market data after 2018 from the database
query_market = "SELECT * FROM market_data WHERE Date >= '2018-01-01'"
df_market = pd.read_sql(query_market, engine)
df_market['Date'] = pd.to_datetime(df_market['Date'])

# ===================== Monte Carlo Prediction Function ===================== #
def monte_carlo_prediction(ticker_data, future_days=365, simulations=1000):
    """
    Predict stock prices using Monte Carlo simulation
    
    Args:
        ticker_data (DataFrame): Data containing ['Date', 'Close'] columns
        future_days (int): Number of days to predict into the future
        simulations (int): Number of simulation paths to generate
    
    Returns:
        ndarray: Predicted prices (average of all simulations)
    """
    print("Starting Monte Carlo simulation...")
    
    # Calculate daily log returns
    close_prices = ticker_data['Close'].values
    log_returns = np.log(close_prices[1:] / close_prices[:-1])
    
    # Calculate parameters: drift (μ) and volatility (σ)
    mu = np.mean(log_returns)
    sigma = np.std(log_returns)
    
    # Generate random return paths
    np.random.seed(42)  # Set random seed for reproducibility
    
    # Initialize simulation arrays
    simulated_paths = np.zeros((simulations, future_days))
    S0 = close_prices[-1]  # Last known price
    
    # Run Monte Carlo simulation
    for i in range(simulations):
        # Generate random normal distribution noise
        rand = np.random.normal(0, 1, future_days)
        # Calculate daily returns
        daily_returns = np.exp(mu + sigma * rand)
        
        # Initialize price path
        price_path = np.zeros(future_days)
        price_path[0] = S0 * daily_returns[0]
        
        # Generate the entire price path
        for t in range(1, future_days):
            price_path[t] = price_path[t-1] * daily_returns[t]
            
        simulated_paths[i] = price_path
    
    # Calculate mean prediction across all simulations
    prediction = np.mean(simulated_paths, axis=0)
    print("Monte Carlo simulation completed!")
    
    return prediction

# ===================== Main Process: Predict for Each Stock ===================== #
def generate_predictions_visualization():
    """
    Generate and visualize price predictions for all stocks in the dataset
    """
    future_days = 365  # Predict for one year
    mc_predictions = {}

    # Set better visualization style
    plt.style.use('ggplot')
    colors = plt.cm.tab10.colors  # Use matplotlib's tab10 color palette

    # Group by ticker and predict for each stock
    unique_tickers = df_market['Ticker'].unique()

    for ticker in unique_tickers:
        ticker_data = df_market[df_market['Ticker'] == ticker].sort_values('Date').dropna(subset=['Close'])
        
        # Skip stocks with insufficient data
        if len(ticker_data) < 50:
            print(f"{ticker} has insufficient data, skipping...")
            continue
        
        print(f"\n===== Predicting {ticker} =====")
        
        # Perform Monte Carlo simulation
        mc_future_prices = monte_carlo_prediction(
            ticker_data=ticker_data,
            future_days=future_days,
            simulations=1000
        )
        mc_predictions[ticker] = mc_future_prices

    # ===================== Visualization ===================== #
    # Use GridSpec for more flexible layout
    plt.figure(figsize=(15, 12))
    gs = gridspec.GridSpec(2, 1, height_ratios=[3, 1])

    # Create subplots
    ax1 = plt.subplot(gs[0])  # Price subplot
    ax2 = plt.subplot(gs[1])  # Volume subplot

    # Track the last historical date for drawing separator
    last_date = None

    # For legend
    legend_stocks = []

    for idx, ticker in enumerate(unique_tickers):
        if ticker not in mc_predictions:
            continue
            
        # Get stock data
        ticker_data = df_market[df_market['Ticker'] == ticker].sort_values('Date')
        dates_hist = ticker_data['Date']
        close_hist = ticker_data['Close']
        volume_hist = ticker_data['Volume']
        
        # Last historical date
        last_date = dates_hist.iloc[-1]
        
        # Generate future dates - one data point per day
        future_dates = [last_date + timedelta(days=i+1) for i in range(future_days)]
        
        # Get prediction results
        mc_pred = mc_predictions[ticker]
        
        # Use consistent color
        color = colors[idx % len(colors)]
        
        # Plot historical prices
        ax1.plot(dates_hist, close_hist, color=color, linewidth=2)
        
        # Plot Monte Carlo predictions with same line style
        ax1.plot(future_dates, mc_pred, color=color, linewidth=2,
                drawstyle='steps-post')
        
        # Add marker at prediction start point
        ax1.scatter(last_date, close_hist.iloc[-1], color=color, 
                  marker='o', s=100, zorder=5)
        
        # Plot volume
        ax2.bar(dates_hist, volume_hist, alpha=0.3, color=color)
        
        # Add to legend list
        legend_stocks.append(ticker)

    # Add vertical separator line between historical data and predictions
    if last_date:
        # Add vertical line to price chart
        ax1.axvline(x=last_date, color='black', linestyle='-', linewidth=1.5, alpha=0.7)
        # Add vertical line to volume chart
        ax2.axvline(x=last_date, color='black', linestyle='-', linewidth=1.5, alpha=0.7)
        
        # Add text label
        ax1.text(last_date, ax1.get_ylim()[1]*0.95, ' Prediction Start', 
               verticalalignment='top', horizontalalignment='left',
               backgroundcolor='white', fontsize=10)

    # Set main chart style
    ax1.set_title('US Tech Stocks Price One-Year Prediction\n(Monte Carlo Simulation)', 
            fontsize=16, pad=20)
    ax1.set_ylabel('Price (USD)', fontsize=12)
    ax1.grid(True, linestyle='--', alpha=0.7)

    # Simplify legend - show only ticker symbols
    handles = [plt.Line2D([0], [0], color=colors[i % len(colors)], linewidth=2) 
             for i in range(len(legend_stocks))]
    ax1.legend(handles, legend_stocks, title='Stock Tickers', 
             bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=10)

    # Set volume chart style
    ax2.set_xlabel('Date', fontsize=12)
    ax2.set_ylabel('Volume', fontsize=12)
    ax2.grid(True, linestyle='--', alpha=0.7)

    # Format date axis
    for ax in [ax1, ax2]:
        ax.xaxis.set_major_formatter(DateFormatter('%Y-%m-%d'))
        for label in ax.get_xticklabels():
            label.set_rotation(45)
            label.set_ha('right')

    # Add watermark
    plt.figtext(0.99, 0.01, 'Data Source: Yahoo Finance / Analysis: Monte Carlo Simulation', 
          ha='right', va='bottom', alpha=0.5, fontsize=8)

    # Adjust layout
    plt.tight_layout()

    # Save chart
    plt.savefig('stock_prediction_monte_carlo_1year.png', 
          dpi=300, bbox_inches='tight')
    print("\nThe prediction visualization chart has been saved as 'stock_prediction_monte_carlo_1year.png'")
    
    return plt

# Execute visualization if this file is run directly
if __name__ == "__main__":
    plt = generate_predictions_visualization()
    plt.show()