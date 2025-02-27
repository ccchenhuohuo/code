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