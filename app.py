# Flask: Used to create a web application and handle HTTP requests
from flask import Flask, request, jsonify, render_template, send_from_directory
# SQLAlchemy: Used as an ORM (Object-Relational Mapping) tool for database operations
from sqlalchemy import create_engine
import pandas as pd
import random
import google.generativeai as genai  # Modify the import method
from stock_api import StockAPI
import os

app = Flask(__name__)
stock_api = StockAPI()

# =============== Database connection configuration ===============
db_user = 'root'             # Replace with your MySQL user name
db_password = 'Cyy-20030611' # Replace with your MySQL password
db_host = 'localhost'        # Keep as is if MySQL is on the same machine
db_port = '3306'             # Default MySQL port
db_name = 'stock_data'       # Replace with your database name

connection_string = f"mysql+mysqlconnector://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}?charset=utf8"
engine = create_engine(connection_string, echo=False)

# =============== Gemini configuration ===============
GEMINI_API_KEY = "AIzaSyDYcL5BBKz812t_66bbBq0h3xm9v6DOG-M"
genai.configure(api_key=GEMINI_API_KEY)

# Get the list of available models
models = genai.list_models()
model = genai.GenerativeModel('gemini-2.0-flash')

@app.route('/')
def index():
    return send_from_directory('.', 'templates/index.html')

@app.route('/get_stock_data', methods=['POST'])
def get_stock_data():
    """
    Receive the stock code list from the front end, query the closing price after 2018 from the local database
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
    Receive the text command from the front end and call the Gemini AI interface for conversation
    """
    data = request.json
    command = data.get("command", "")

    if not command:
        return jsonify({"response": "You didn't input anything."})

    try:
        # Create a chat session
        chat = model.start_chat(history=[])
        
        # Send a message and get the response
        response = chat.send_message(
            command,
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                candidate_count=1,
                max_output_tokens=2048,
            )
        )
        
        # Get the response text
        response_text = response.text
        
        # If the response is empty, return an error message
        if not response_text:
            return jsonify({"response": "Sorry, I can't generate a response right now. Please try again later."})
            
        return jsonify({"response": response_text})
    except Exception as e:
        return jsonify({"response": f"Failed to request the Gemini AI interface: {str(e)}"})

@app.route('/get_alert_levels', methods=['POST'])
def get_alert_levels():
    """
    Receive the stock code, return the high, medium, and low valuation and liquidity according to a certain logic.
    Here, for demonstration purposes, the random return is used.
    """
    data = request.json
    stock = data.get("stock", "")
    possible_levels = ["low", "medium", "high"]

    # In a real project, you can determine the valuation and liquidity based on the database/algorithm
    # Here, for demonstration purposes, all are randomly returned
    valuation = random.choice(possible_levels)
    liquidity = random.choice(possible_levels)

    return jsonify({"valuation": valuation, "liquidity": liquidity})

@app.route('/get_stock_details')
def get_stock_details():
    symbol = request.args.get('symbol', '')
    if not symbol:
        return jsonify({'error': 'Stock symbol is required'})
    
    result = stock_api.get_stock_details(symbol)
    return jsonify(result)

@app.route('/get_monthly_data')
def get_monthly_data():
    symbol = request.args.get('symbol', '')
    if not symbol:
        return jsonify({'error': 'Stock symbol is required'})
    
    result = stock_api.get_monthly_data(symbol)
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)