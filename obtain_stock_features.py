# python3 -m venv ISOM4007data
# source ISOM4007data/bin/activate
# touch main.py
# python main.py
# pip install requests
# deactivate
# pip freeze > requirements.txt
# python3 -m venv ISOM4007data
# source ISOM4007data/bin/activate
# pip install -r requirements.txt
# pip list

import yfinance as yf
import pandas as pd
from sqlalchemy import create_engine

# 定义美国七姐妹的股票代码
tickers = ["AAPL", "MSFT", "AMZN", "GOOGL", "META", "NFLX", "TSLA"]

# 创建四个空的 DataFrame 来存储不同类型的数据
market_data = pd.DataFrame()
fundamental_data = pd.DataFrame()
balance_sheet_data = pd.DataFrame()
income_statement_data = pd.DataFrame()

for ticker in tickers:
    # 获取股票信息
    stock = yf.Ticker(ticker)
    
    # 获取历史价格数据
    hist = stock.history(period="10y")
    
    # 获取财务数据
    info = stock.info
    financials = stock.financials
    balance_sheet = stock.balance_sheet
    cash_flow = stock.cashflow
    
    # 基本行情数据表
    market_data = pd.concat([market_data, pd.DataFrame({
        'Ticker': ticker,
        'Date': hist.index,
        'Open': hist['Open'],
        'High': hist['High'],
        'Low': hist['Low'],
        'Close': hist['Close'],
        'Volume': hist['Volume']
    })], ignore_index=True)
    
    # 基本面数据表
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
    
    # 资产负债表
    balance_sheet_data = pd.concat([balance_sheet_data, pd.DataFrame({
        'Ticker': ticker,
        'Date': balance_sheet.columns[0],
        'CurrentAssets': balance_sheet.loc['Total Current Assets'].values[0] if 'Total Current Assets' in balance_sheet.index else None,
        'NonCurrentAssets': balance_sheet.loc['Total Non Current Assets'].values[0] if 'Total Non Current Assets' in balance_sheet.index else None,
        'CurrentLiabilities': balance_sheet.loc['Total Current Liabilities'].values[0] if 'Total Current Liabilities' in balance_sheet.index else None,
        'NonCurrentLiabilities': balance_sheet.loc['Total Non Current Liabilities'].values[0] if 'Total Non Current Liabilities' in balance_sheet.index else None
    }, index=[0])], ignore_index=True)
    
    # 利润表
    income_statement_data = pd.concat([income_statement_data, pd.DataFrame({
        'Ticker': ticker,
        'Date': financials.columns[0],
        'Revenue': financials.loc['Total Revenue'].values[0] if 'Total Revenue' in financials.index else None,
        'CostOfRevenue': financials.loc['Cost Of Revenue'].values[0] if 'Cost Of Revenue' in financials.index else None,
        'OperatingIncome': financials.loc['Operating Income'].values[0] if 'Operating Income' in financials.index else None,
        'IncomeBeforeTax': financials.loc['Income Before Tax'].values[0] if 'Income Before Tax' in financials.index else None,
        'NetIncome': financials.loc['Net Income'].values[0] if 'Net Income' in financials.index else None
    }, index=[0])], ignore_index=True)

# 输出数据示例
print("Market Data:")
print(market_data.head(7))
print("\nFundamental Data:")
print(fundamental_data.head(7))
print("\nBalance Sheet Data:")
print(balance_sheet_data.head(7))
print("\nIncome Statement Data:")
print(income_statement_data.head(7))

# ----------------- 数据写入 MySQL -----------------

# MySQL 数据库连接参数
db_user = 'root'
db_password = 'Cyy-20030611'
db_host = 'localhost'
db_port = '3306'
db_name = 'stock_data'

# 创建数据库连接字符串
connection_string = f"mysql+mysqlconnector://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}?charset=utf8"
engine = create_engine(connection_string, echo=False)

# 将数据写入 MySQL 数据库
market_data.to_sql(name='market_data', con=engine, if_exists='replace', index=False)
fundamental_data.to_sql(name='fundamental_data', con=engine, if_exists='replace', index=False)
balance_sheet_data.to_sql(name='balance_sheet', con=engine, if_exists='replace', index=False)
income_statement_data.to_sql(name='income_statement', con=engine, if_exists='replace', index=False)

print("数据已成功写入 MySQL 数据库！")

