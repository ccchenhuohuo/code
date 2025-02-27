from alpha_vantage.timeseries import TimeSeries
from flask import jsonify

class StockAPI:
    def __init__(self, api_key='CWL9SQIO1FD94H98'):
        self.ts = TimeSeries(key=api_key)
    
    def get_stock_details(self, symbol):
        try:
            # 获取实时数据
            data, meta_data = self.ts.get_quote_endpoint(symbol=symbol)
            
            # 格式化返回数据
            return {
                'name': f"{symbol}",  # Alpha Vantage API不直接提供公司名称
                'price': float(data['05. price']),
                'change': float(data['09. change']),
                'changePercent': float(data['10. change percent'].strip('%')),
                'open': float(data['02. open']),
                'high': float(data['03. high']),
                'low': float(data['04. low']),
                'volume': int(data['06. volume']),
                'latest_trading_day': data['07. latest trading day'],
                'previous_close': float(data['08. previous close'])
            }
        except Exception as e:
            return {'error': str(e)}
    
    def get_monthly_data(self, symbol):
        try:
            data, meta_data = self.ts.get_monthly(symbol=symbol)
            return {'data': data, 'meta_data': meta_data}
        except Exception as e:
            return {'error': str(e)}
    
    def get_company_fundamentals(self, symbol):
        try:
            # 这里模拟返回公司基本面数据
            # 实际项目中应该从真实API获取这些数据
            return {
                'CompanyInfo': {
                    'Symbol': symbol,
                    'Name': 'International Business Machines',
                    'Description': 'International Business Machines Corporation (IBM) is an American multinational technology company...',
                    'Exchange': 'NYSE',
                    'Currency': 'USD',
                    'Country': 'USA',
                    'Sector': 'TECHNOLOGY',
                    'Industry': 'COMPUTER & OFFICE EQUIPMENT',
                    'Address': '1 NEW ORCHARD ROAD, ARMONK, NY, US',
                    'OfficialSite': 'https://www.ibm.com'
                },
                'FinancialMetrics': {
                    'MarketCap': '237,231,210,000',
                    'EBITDA': '13,703,000,000',
                    'PERatio': '39.85',
                    'PEGRatio': '1.747',
                    'BookValue': '29.49',
                    'DividendPerShare': '6.67',
                    'DividendYield': '2.61%',
                    'EPS': '6.42',
                    'RevenuePerShare': '68.08',
                    'ProfitMargin': '9.6%',
                    'OperatingMargin': '21.9%'
                },
                'Performance': {
                    'ROA': '4.15%',
                    'ROE': '24.1%',
                    'Revenue': '62,753,001,000',
                    'GrossProfit': '35,550,999,000',
                    'QuarterlyEarningsGrowth': '-12.8%',
                    'QuarterlyRevenueGrowth': '1.0%'
                },
                'MarketAnalysis': {
                    'AnalystTargetPrice': '254.51',
                    'AnalystRatings': {
                        'StrongBuy': 2,
                        'Buy': 5,
                        'Hold': 9,
                        'Sell': 2,
                        'StrongSell': 1
                    },
                    'ValuationMetrics': {
                        'TrailingPE': '39.85',
                        'ForwardPE': '23.47',
                        'PriceToSales': '3.78',
                        'PriceToBook': '8.69',
                        'EVToRevenue': '4.479',
                        'EVToEBITDA': '23.08'
                    }
                },
                'TechnicalIndicators': {
                    'Beta': '0.754',
                    '52WeekHigh': '265.09',
                    '52WeekLow': '157.33',
                    '50DayMA': '236.53',
                    '200DayMA': '207.91',
                    'SharesOutstanding': '927,264,000'
                }
            }
        except Exception as e:
            return {'error': str(e)} 