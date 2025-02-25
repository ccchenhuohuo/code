import pandas as pd
import numpy as np
from sqlalchemy import create_engine
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
from datetime import timedelta
import matplotlib.gridspec as gridspec
from matplotlib import rcParams

# ===================== 数据库连接及数据读取 ===================== #
db_user = 'root'           # 替换为你的MySQL用户名
db_password = 'Cyy-20030611'  # 替换为你的MySQL密码
db_host = 'localhost'      # 如果MySQL在本机，保持不变
db_port = '3306'           # 默认MySQL端口
db_name = 'stock_data'     # 替换为你的数据库名

# 创建数据库连接字符串
connection_string = f"mysql+mysqlconnector://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}?charset=utf8"
engine = create_engine(connection_string, echo=False)

# 读取 market_data 表中2018年以后的数据
query_market = "SELECT * FROM market_data WHERE Date >= '2018-01-01'"
df_market = pd.read_sql(query_market, engine)
df_market['Date'] = pd.to_datetime(df_market['Date'])

# ===================== 蒙特卡洛模拟预测方法 ===================== #
def monte_carlo_prediction(ticker_data, future_days=365, simulations=1000):
    """
    使用蒙特卡洛模拟方法预测股价
    
    ticker_data: DataFrame, 必须包含['Date', 'Close']
    future_days: 预测天数，默认为365天（一年）
    simulations: 模拟次数
    
    返回: 预测价格（取所有模拟的平均值）
    """
    print("开始蒙特卡洛模拟...")
    
    # 计算每日收益率（对数收益率）
    close_prices = ticker_data['Close'].values
    log_returns = np.log(close_prices[1:] / close_prices[:-1])
    
    # 计算参数：drift(μ)和volatility(σ)
    mu = np.mean(log_returns)
    sigma = np.std(log_returns)
    
    # 生成随机收益率路径
    np.random.seed(42)  # 设置随机种子，确保结果可复现
    
    # 预测多条路径
    simulated_paths = np.zeros((simulations, future_days))
    S0 = close_prices[-1]  # 最后一个已知价格
    
    # 模拟多条路径
    for i in range(simulations):
        # 生成随机正态分布噪声
        rand = np.random.normal(0, 1, future_days)
        # 计算每日价格: S_t = S_{t-1} * exp(drift + volatility * random)
        daily_returns = np.exp(mu + sigma * rand)
        
        # 初始化价格路径
        price_path = np.zeros(future_days)
        price_path[0] = S0 * daily_returns[0]
        
        # 生成整个价格路径
        for t in range(1, future_days):
            price_path[t] = price_path[t-1] * daily_returns[t]
            
        simulated_paths[i] = price_path
    
    # 计算所有路径的均值作为预测
    prediction = np.mean(simulated_paths, axis=0)
    print("蒙特卡洛模拟完成!")
    
    return prediction

# ===================== 主流程：对每只股票进行预测 ===================== #
future_days = 365  # 预测未来365天（一年）
mc_predictions = {}

# 设置更好的可视化风格
plt.style.use('ggplot')
colors = plt.cm.tab10.colors  # 使用matplotlib的tab10调色板

# 设置字体为支持中文的字体
rcParams['font.family'] = 'Microsoft YaHei'  # 或者 'Arial Unicode MS'

# 按 Ticker 分组，对每只股票分别预测
unique_tickers = df_market['Ticker'].unique()

for ticker in unique_tickers:
    ticker_data = df_market[df_market['Ticker'] == ticker].sort_values('Date').dropna(subset=['Close'])
    
    # 数据不足时跳过
    if len(ticker_data) < 50:
        print(f"{ticker} 数据太少，跳过...")
        continue
    
    print(f"\n===== 预测 {ticker} =====")
    
    # 蒙特卡洛模拟预测
    mc_future_prices = monte_carlo_prediction(
        ticker_data=ticker_data,
        future_days=future_days,
        simulations=1000
    )
    mc_predictions[ticker] = mc_future_prices

# ===================== 改进的可视化展示 ===================== #
# 使用GridSpec实现更灵活的布局
plt.figure(figsize=(15, 12))
gs = gridspec.GridSpec(2, 1, height_ratios=[3, 1])

# Price subplot
ax1 = plt.subplot(gs[0])
# Volume subplot
ax2 = plt.subplot(gs[1])

# 记录最后一个历史日期，用于绘制分隔线
last_date = None

# 用于图例的股票列表
legend_stocks = []

for idx, ticker in enumerate(unique_tickers):
    if ticker not in mc_predictions:
        continue
        
    # 获取该股票的数据
    ticker_data = df_market[df_market['Ticker'] == ticker].sort_values('Date')
    dates_hist = ticker_data['Date']
    close_hist = ticker_data['Close']
    volume_hist = ticker_data['Volume']
    
    # 最后一个历史日期
    last_date = dates_hist.iloc[-1]
    
    # 生成未来日期 - 确保是每天一个数据点
    future_dates = [last_date + timedelta(days=i+1) for i in range(future_days)]
    
    # 获取预测结果
    mc_pred = mc_predictions[ticker]
    
    # 使用相同的颜色
    color = colors[idx % len(colors)]
    
    # 绘制历史价格
    ax1.plot(dates_hist, close_hist, color=color, linewidth=2)
    
    # 绘制蒙特卡洛预测 - 使用与历史数据相同的线型
    ax1.plot(future_dates, mc_pred, color=color, linewidth=2,
             drawstyle='steps-post')
    
    # 在预测起点添加标记
    ax1.scatter(last_date, close_hist.iloc[-1], color=color, 
                marker='o', s=100, zorder=5)
    
    # 绘制成交量
    ax2.bar(dates_hist, volume_hist, alpha=0.3, color=color)
    
    # 添加到图例列表
    legend_stocks.append(ticker)

# 添加垂直分隔线，区分历史数据和预测数据
if last_date:
    # 在股价图中添加垂直线
    ax1.axvline(x=last_date, color='black', linestyle='-', linewidth=1.5, alpha=0.7)
    # 在成交量图中添加垂直线
    ax2.axvline(x=last_date, color='black', linestyle='-', linewidth=1.5, alpha=0.7)
    
    # 添加文本标签
    ax1.text(last_date, ax1.get_ylim()[1]*0.95, ' Prediction Start', 
             verticalalignment='top', horizontalalignment='left',
             backgroundcolor='white', fontsize=10)

# 设置主图样式
ax1.set_title('US Tech Stocks Price One-Year Prediction\n(Monte Carlo Simulation)', 
          fontsize=16, pad=20)
ax1.set_ylabel('Price (USD)', fontsize=12)
ax1.grid(True, linestyle='--', alpha=0.7)

# 简化图例 - 只显示股票代码
handles = [plt.Line2D([0], [0], color=colors[i % len(colors)], linewidth=2) 
           for i in range(len(legend_stocks))]
ax1.legend(handles, legend_stocks, title='Stock Tickers', 
           bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=10)

# 设置成交量图样式
ax2.set_xlabel('Date', fontsize=12)
ax2.set_ylabel('Volume', fontsize=12)
ax2.grid(True, linestyle='--', alpha=0.7)

# 格式化日期轴
for ax in [ax1, ax2]:
    ax.xaxis.set_major_formatter(DateFormatter('%Y-%m-%d'))
    for label in ax.get_xticklabels():
        label.set_rotation(45)
        label.set_ha('right')

# 添加水印
plt.figtext(0.99, 0.01, 'Data Source: Yahoo Finance / Analysis: Monte Carlo Simulation', 
        ha='right', va='bottom', alpha=0.5, fontsize=8)

# 自动调整布局
plt.tight_layout()

# 保存图表
plt.savefig('stock_prediction_monte_carlo_1year.png', 
        dpi=300, bbox_inches='tight')
print("\nThe prediction visualization chart has been saved as 'stock_prediction_monte_carlo_1year.png'")
plt.show()