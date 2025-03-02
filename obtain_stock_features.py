"""
Stock Data Collection Module
Fetches and stores financial data for technology stocks using Yahoo Finance API
"""
import yfinance as yf
import pandas as pd
from sqlalchemy import create_engine

# Define list of major US tech company stock symbols
TECH_TICKERS = ["AAPL", "MSFT", "AMZN", "GOOGL", "META", "NFLX", "TSLA"]

# Database configuration
DB_CONFIG = {
    'user': 'root',
    'password': 'Cyy-20030611',
    'host': 'localhost',
    'port': '3306',
    'database': 'stock_data'
}

def fetch_stock_data():
    """
    Fetch stock data for all tickers and organize into structured DataFrames
    
    Returns:
        tuple: Four DataFrames containing market data, fundamental data, 
               balance sheet data, and income statement data
    """
    # Create empty DataFrames to store different types of data
    market_data = pd.DataFrame()
    fundamental_data = pd.DataFrame()
    balance_sheet_data = pd.DataFrame()
    income_statement_data = pd.DataFrame()
    
    for ticker in TECH_TICKERS:
        print(f"Fetching data for {ticker}...")
        
        # Get stock information
        stock = yf.Ticker(ticker)
        
        # Get historical price data
        hist = stock.history(period="10y")
        
        # Get financial data
        info = stock.info
        financials = stock.financials
        balance_sheet = stock.balance_sheet
        cash_flow = stock.cashflow
        
        # Market data table (OHLCV)
        market_data = pd.concat([market_data, pd.DataFrame({
            'Ticker': ticker,
            'Date': hist.index,
            'Open': hist['Open'],
            'High': hist['High'],
            'Low': hist['Low'],
            'Close': hist['Close'],
            'Volume': hist['Volume']
        })], ignore_index=True)
        
        # Fundamental data table
        fundamental_data = pd.concat([fundamental_data, pd.DataFrame({
            'Ticker': ticker,
            'Date': pd.Timestamp.now(),
            'MarketCap': info.get('marketCap', None),
            'PE_Ratio': info.get('trailingPE', None),
            'PB_Ratio': info.get('priceToBook', None),
            'DividendYield': info.get('dividendYield', None),
            'Revenue': financials.loc['Total Revenue'].values[0] if 'Total Revenue' in financials.index else None,
            'NetIncome': financials.loc['Net Income'].values[0] if 'Net Income' in financials.index else None,
            'OperatingCashFlow': cash_flow.loc['Operating Cash Flow'].values[0] if 'Operating Cash Flow' in cash_flow.index else None
        }, index=[0])], ignore_index=True)
        
        # Balance sheet table
        balance_sheet_data = pd.concat([balance_sheet_data, pd.DataFrame({
            'Ticker': ticker,
            'Date': balance_sheet.columns[0],
            'CurrentAssets': balance_sheet.loc['Total Current Assets'].values[0] if 'Total Current Assets' in balance_sheet.index else None,
            'NonCurrentAssets': balance_sheet.loc['Total Non Current Assets'].values[0] if 'Total Non Current Assets' in balance_sheet.index else None,
            'CurrentLiabilities': balance_sheet.loc['Total Current Liabilities'].values[0] if 'Total Current Liabilities' in balance_sheet.index else None,
            'NonCurrentLiabilities': balance_sheet.loc['Total Non Current Liabilities'].values[0] if 'Total Non Current Liabilities' in balance_sheet.index else None
        }, index=[0])], ignore_index=True)
        
        # Income statement table
        income_statement_data = pd.concat([income_statement_data, pd.DataFrame({
            'Ticker': ticker,
            'Date': financials.columns[0],
            'Revenue': financials.loc['Total Revenue'].values[0] if 'Total Revenue' in financials.index else None,
            'CostOfRevenue': financials.loc['Cost Of Revenue'].values[0] if 'Cost Of Revenue' in financials.index else None,
            'OperatingIncome': financials.loc['Operating Income'].values[0] if 'Operating Income' in financials.index else None,
            'IncomeBeforeTax': financials.loc['Income Before Tax'].values[0] if 'Income Before Tax' in financials.index else None,
            'NetIncome': financials.loc['Net Income'].values[0] if 'Net Income' in financials.index else None
        }, index=[0])], ignore_index=True)
    
    return market_data, fundamental_data, balance_sheet_data, income_statement_data

def save_to_database(market_data, fundamental_data, balance_sheet_data, income_statement_data):
    """
    Save all collected data to MySQL database
    
    Args:
        market_data (DataFrame): Market price and volume data
        fundamental_data (DataFrame): Key financial metrics
        balance_sheet_data (DataFrame): Balance sheet information
        income_statement_data (DataFrame): Income statement information
    """
    # Create database connection string
    connection_string = f"mysql+mysqlconnector://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}?charset=utf8"
    engine = create_engine(connection_string, echo=False)
    
    # Write data to MySQL database
    market_data.to_sql(name='market_data', con=engine, if_exists='replace', index=False)
    fundamental_data.to_sql(name='fundamental_data', con=engine, if_exists='replace', index=False)
    balance_sheet_data.to_sql(name='balance_sheet', con=engine, if_exists='replace', index=False)
    income_statement_data.to_sql(name='income_statement', con=engine, if_exists='replace', index=False)
    
    print("Data successfully written to MySQL database!")

def print_data_samples(market_data, fundamental_data, balance_sheet_data, income_statement_data):
    """
    Print sample rows from each DataFrame for verification
    
    Args:
        market_data (DataFrame): Market price and volume data
        fundamental_data (DataFrame): Key financial metrics
        balance_sheet_data (DataFrame): Balance sheet information
        income_statement_data (DataFrame): Income statement information  
    """
    print("Market Data:")
    print(market_data.head(7))
    print("\nFundamental Data:")
    print(fundamental_data.head(7))
    print("\nBalance Sheet Data:")
    print(balance_sheet_data.head(7))
    print("\nIncome Statement Data:")
    print(income_statement_data.head(7))

if __name__ == "__main__":
    # Fetch all stock data
    market_data, fundamental_data, balance_sheet_data, income_statement_data = fetch_stock_data()
    
    # Print sample data for verification
    print_data_samples(market_data, fundamental_data, balance_sheet_data, income_statement_data)
    
    # Save all data to database
    save_to_database(market_data, fundamental_data, balance_sheet_data, income_statement_data)

