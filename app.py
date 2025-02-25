from flask import Flask, request, jsonify, render_template
from sqlalchemy import create_engine
import pandas as pd
import random
import requests

app = Flask(__name__)

# =============== 数据库连接配置 ===============
db_user = 'root'             # 替换为你的MySQL用户名
db_password = 'Cyy-20030611' # 替换为你的MySQL密码
db_host = 'localhost'        # 如果MySQL在本机，保持不变
db_port = '3306'             # 默认MySQL端口
db_name = 'stock_data'       # 替换为你的数据库名

connection_string = f"mysql+mysqlconnector://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}?charset=utf8"
engine = create_engine(connection_string, echo=False)

# =============== 你的AI API Key（示例） ===============
OPENAI_API_KEY = "YOUR_API_KEY"  # 在真实场景下替换为你的Key并安全存储

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_stock_data', methods=['POST'])
def get_stock_data():
    """
    根据前端传入的股票代码列表，从本地数据库查询2018年后的收盘价
    """
    data = request.json
    stock_symbols = data.get("stocks", [])
    stock_data = {}

    for stock in stock_symbols:
        try:
            query = f"""
                SELECT Date, Close
                FROM market_data
                WHERE Ticker = '{stock}'
                  AND Date >= '2018-01-01'
                ORDER BY Date
            """
            df = pd.read_sql(query, engine)
            if df.empty:
                stock_data[stock] = {"error": "No data found in DB."}
                continue
            df["Date"] = df["Date"].dt.strftime('%Y-%m-%d')
            stock_data[stock] = dict(zip(df["Date"], df["Close"]))
        except Exception as e:
            stock_data[stock] = {"error": str(e)}
    return jsonify(stock_data)

@app.route('/gemini_assistant', methods=['POST'])
def gemini_assistant():
    """
    接收前端传来的文字命令，并调用真正的 AI 接口（此处以 OpenAI GPT-3.5 为例）
    你也可以替换为自己Gemini接口或其他大模型API。
    """
    data = request.json
    command = data.get("command", "")

    if not command:
        return jsonify({"response": "你没有输入任何内容。"})

    # ============ 1. 构造对OpenAI接口的请求 =============
    # 注意：如果你使用的是 Gemini 或其他AI，请按其官方文档替换
    openai_api_url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": "你是一个乐于助人的AI助手。"},
            {"role": "user", "content": command}
        ]
    }

    try:
        response = requests.post(openai_api_url, headers=headers, json=payload, timeout=15)
        if response.status_code == 200:
            r_json = response.json()
            ai_message = r_json["choices"][0]["message"]["content"]
            return jsonify({"response": ai_message})
        else:
            # 如果OpenAI返回错误
            return jsonify({"response": f"AI接口返回错误：{response.text}"})
    except Exception as e:
        return jsonify({"response": f"请求AI接口失败：{str(e)}"})

@app.route('/get_alert_levels', methods=['POST'])
def get_alert_levels():
    """
    接收股票代码，根据一定逻辑返回估值和流动性的高中低。
    这里为了演示，随机返回。
    """
    data = request.json
    stock = data.get("stock", "")
    possible_levels = ["低", "中", "高"]

    # 真实项目中，你可根据数据库/算法判断估值与流动性
    # 这里演示：全部随机
    valuation = random.choice(possible_levels)
    liquidity = random.choice(possible_levels)

    return jsonify({"valuation": valuation, "liquidity": liquidity})

if __name__ == '__main__':
    app.run(debug=True)