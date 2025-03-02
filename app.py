"""
Flask Web Application for Stock Data Analysis and Prediction
Provides endpoints for stock data retrieval, AI assistant integration, and stock price prediction.
"""
# Core dependencies
from flask import Flask, request, jsonify, render_template, send_from_directory
from sqlalchemy import create_engine
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import google.generativeai as genai
from stock_api import StockAPI

app = Flask(__name__)
stock_api = StockAPI()

# =============== Database configuration ===============
DB_CONFIG = {
    'user': 'root',
    'password': 'Cyy-20030611',
    'host': 'localhost',
    'port': '3306',
    'database': 'stock_data'
}

connection_string = f"mysql+mysqlconnector://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}?charset=utf8"
engine = create_engine(connection_string, echo=False)

# =============== Gemini AI configuration ===============
GEMINI_API_KEY = "AIzaSyDYcL5BBKz812t_66bbBq0h3xm9v6DOG-M"
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

@app.route('/')
def index():
    """Serve the main application page"""
    return send_from_directory('templates', 'index.html')

@app.route('/get_stock_data', methods=['POST'])
def get_stock_data():
    """
    Retrieve stock closing prices from database for requested stock symbols
    
    Returns:
        JSON with stock data organized by symbol
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
                stock_data[stock] = {"error": "No data found in database"}
                continue
            df["Date"] = df["Date"].dt.strftime('%Y-%m-%d')
            stock_data[stock] = dict(zip(df["Date"], df["Close"]))
        except Exception as e:
            stock_data[stock] = {"error": str(e)}
    
    return jsonify(stock_data)

@app.route('/gemini_assistant', methods=['POST'])
def gemini_assistant():
    """
    Process natural language queries using Gemini AI
    
    Returns:
        JSON with AI-generated response
    """
    data = request.json
    command = data.get("command", "")

    if not command:
        return jsonify({"response": "No input provided"})

    try:
        chat = model.start_chat(history=[])
        response = chat.send_message(
            command,
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                candidate_count=1,
                max_output_tokens=2048,
            )
        )
        
        response_text = response.text
        if not response_text:
            return jsonify({"response": "No response generated. Please try again."})
            
        return jsonify({"response": response_text})
    except Exception as e:
        return jsonify({"response": f"Error: {str(e)}"})

@app.route('/get_stock_details')
def get_stock_details():
    """
    Get detailed information for a specific stock symbol
    
    Returns:
        JSON with stock details from the API
    """
    symbol = request.args.get('symbol', '')
    if not symbol:
        return jsonify({'error': 'Stock symbol is required'})
    
    result = stock_api.get_stock_details(symbol)
    return jsonify(result)

@app.route('/get_monthly_data')
def get_monthly_data():
    """
    Get monthly historical data for a specific stock symbol
    
    Returns:
        JSON with monthly stock data
    """
    symbol = request.args.get('symbol', '')
    if not symbol:
        return jsonify({'error': 'Stock symbol is required'})
    
    result = stock_api.get_monthly_data(symbol)
    return jsonify(result)

@app.route('/api/fundamentals/<symbol>')
def get_fundamentals(symbol):
    """
    Get fundamental financial metrics for a specific stock symbol
    
    Returns:
        JSON with fundamental data
    """
    if not symbol:
        return jsonify({'error': 'Stock symbol is required'})
    
    result = stock_api.get_company_fundamentals(symbol)
    return jsonify(result)

@app.route('/predict_monte_carlo', methods=['POST'])
def predict_monte_carlo():
    """
    Generate stock price predictions using Monte Carlo simulation
    
    Returns:
        JSON with prediction data including dates, prices, and sample paths
    """
    data = request.json
    stock_symbols = data.get("stocks", [])
    future_days = data.get("future_days", 180)  # Default predict for 6 months
    simulations = data.get("simulations", 1000)  # Default number of simulations
    sample_paths = data.get("sample_paths", 100)  # Default return 100 sample paths
    
    if not stock_symbols:
        return jsonify({"error": "Stock symbols required"})
    
    predictions = {}
    
    for symbol in stock_symbols:
        try:
            # Get historical data from database
            query = f"""
                SELECT Date, Close
                FROM market_data
                WHERE Ticker = '{symbol}'
                  AND Date >= '2018-01-01'
                ORDER BY Date
            """
            df = pd.read_sql(query, engine)
            
            if df.empty:
                predictions[symbol] = {"error": "No data found in database"}
                continue
                
            # Calculate daily log returns
            close_prices = df['Close'].values
            log_returns = np.log(close_prices[1:] / close_prices[:-1])
            
            # Calculate parameters: drift(μ) and volatility(σ)
            mu = np.mean(log_returns)
            sigma = np.std(log_returns)
            
            # Set random seed for reproducibility
            np.random.seed(42)  
            
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
            
            # Get sample paths (if requested)
            sample_indices = np.random.choice(simulations, min(sample_paths, simulations), replace=False)
            sampled_paths = simulated_paths[sample_indices].tolist()
            
            # Generate future dates
            last_date = df['Date'].iloc[-1]
            future_dates = [(last_date + timedelta(days=i+1)).strftime('%Y-%m-%d') 
                            for i in range(future_days)]
            
            # Format response data
            predictions[symbol] = {
                "dates": future_dates,
                "prices": prediction.tolist(),
                "last_date": last_date.strftime('%Y-%m-%d'),
                "last_price": float(close_prices[-1]),
                "sample_paths": sampled_paths
            }
            
        except Exception as e:
            predictions[symbol] = {"error": str(e)}
    
    return jsonify(predictions)

if __name__ == '__main__':
    # For production, consider setting debug=False and using a proper WSGI server
    app.run(debug=True, port=5001)  # Changed port from 5000 to 5001 to avoid conflicts with AirPlay