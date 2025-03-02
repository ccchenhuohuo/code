"""
Flask Web Application for Stock Data Analysis and Prediction
Provides endpoints for stock data retrieval, AI assistant integration, and stock price prediction.
"""
# Core dependencies
from flask import Flask, request, jsonify, render_template, send_from_directory, session
from sqlalchemy import create_engine, text
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import google.generativeai as genai
from stock_api import StockAPI
import json

app = Flask(__name__)
app.secret_key = 'ISOM4007_secure_key'  # For session encryption
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

# =============== User Authentication APIs ===============
@app.route('/api/register', methods=['POST'])
def register():
    """Register a new user
    
    Returns:
        JSON response indicating registration result
    """
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    # Validate required fields
    if not username or not email or not password:
        return jsonify({'status': 'error', 'message': 'All fields are required'}), 400
    
    # Check if username or email already exists
    try:
        with engine.connect() as conn:
            # Start transaction
            trans = conn.begin()
            
            try:
                result = conn.execute(
                    text("SELECT * FROM users WHERE username = :username OR email = :email"),
                    {"username": username, "email": email}
                )
                user = result.fetchone()
                
                if user:
                    return jsonify({'status': 'error', 'message': 'Username or email already exists'}), 400
                
                # Hash password
                hashed_password = generate_password_hash(password)
                
                # Insert new user
                result = conn.execute(
                    text("INSERT INTO users (username, email, password) VALUES (:username, :email, :password)"),
                    {"username": username, "email": email, "password": hashed_password}
                )
                
                # Get newly inserted user ID
                new_user_id = result.lastrowid
                
                # Create financial account for new user with initial balance of 100,000
                conn.execute(
                    text("INSERT INTO user_accounts (user_id, balance, total_deposit) VALUES (:user_id, :balance, :total_deposit)"),
                    {"user_id": new_user_id, "balance": 100000.00, "total_deposit": 100000.00}
                )
                
                # Record initial deposit transaction
                # First get the new account ID
                result = conn.execute(
                    text("SELECT id FROM user_accounts WHERE user_id = :user_id"),
                    {"user_id": new_user_id}
                )
                account = result.fetchone()
                
                if account:
                    conn.execute(
                        text("INSERT INTO transaction_history "
                            "(user_id, account_id, transaction_type, amount, balance_after, description) "
                            "VALUES (:user_id, :account_id, 'deposit', :amount, :balance_after, :description)"),
                        {
                            "user_id": new_user_id,
                            "account_id": account[0],
                            "amount": 100000.00,
                            "balance_after": 100000.00,
                            "description": "Initial deposit - new account"
                        }
                    )
                
                # Commit transaction
                trans.commit()
                
                # Set session for the new user
                session['user_id'] = new_user_id
                session['username'] = username
                session['is_admin'] = False
                
                return jsonify({'status': 'success', 'message': 'Registration successful'}), 201
                
            except Exception as e:
                # Rollback in case of error
                trans.rollback()
                return jsonify({'status': 'error', 'message': f'Registration failed: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Database error: {str(e)}'}), 500

@app.route('/api/login', methods=['POST'])
def login():
    """User login
    
    Returns:
        JSON response indicating login result and user information
    """
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'status': 'error', 'message': 'Username and password are required'}), 400
    
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT * FROM users WHERE username = :username"),
                {"username": username}
            )
            user = result.fetchone()
            
            if not user or not check_password_hash(user.password, password):
                return jsonify({'status': 'error', 'message': 'Invalid username or password'}), 401
            
            # Update last login time
            conn.execute(
                text("UPDATE users SET last_login = NOW() WHERE id = :id"),
                {"id": user.id}
            )
            conn.commit()
            
            # Set session
            session['user_id'] = user.id
            session['username'] = user.username
            session['is_admin'] = user.is_admin
            
            return jsonify({
                'status': 'success', 
                'message': 'Login successful',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'is_admin': user.is_admin
                }
            }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Login failed: {str(e)}'}), 500

@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    """Admin login
    
    Returns:
        JSON response indicating login result and admin information
    """
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'status': 'error', 'message': 'Username and password are required'}), 400
    
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT * FROM users WHERE username = :username AND is_admin = TRUE"),
                {"username": username}
            )
            admin = result.fetchone()
            
            if not admin or not check_password_hash(admin.password, password):
                return jsonify({'status': 'error', 'message': 'Invalid admin account or password'}), 401
            
            # Update last login time
            conn.execute(
                text("UPDATE users SET last_login = NOW() WHERE id = :id"),
                {"id": admin.id}
            )
            conn.commit()
            
            # Set session
            session['user_id'] = admin.id
            session['username'] = admin.username
            session['is_admin'] = True
            
            return jsonify({
                'status': 'success', 
                'message': 'Admin login successful',
                'user': {
                    'id': admin.id,
                    'username': admin.username,
                    'email': admin.email,
                    'is_admin': admin.is_admin
                }
            }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Login failed: {str(e)}'}), 500

@app.route('/api/logout', methods=['POST'])
def logout():
    """User logout, clear session data
    
    Returns:
        JSON response indicating logout result
    """
    session.clear()
    return jsonify({'status': 'success', 'message': 'Logout successful'}), 200

@app.route('/api/login/current', methods=['GET'])
def get_current_user():
    """Get current logged-in user information
    
    Returns:
        JSON response containing current user information
    """
    if not session.get('user_id'):
        return jsonify({'status': 'error', 'message': 'Not logged in'}), 401
    
    user_id = session['user_id']
    
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT id, username, email, is_admin FROM users WHERE id = :user_id"),
                {"user_id": user_id}
            )
            user = result.fetchone()
            
            if not user:
                return jsonify({'status': 'error', 'message': 'User does not exist'}), 404
            
            user_data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_admin': user.is_admin
            }
            
            return jsonify({'status': 'success', 'user': user_data}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Failed to retrieve user information: {str(e)}'}), 500

# =============== Admin APIs ===============
@app.route('/api/admin/users', methods=['GET'])
def get_all_users():
    """Get all user list (admin only)
    
    Returns:
        JSON response containing all regular user information
    """
    if not session.get('is_admin', False):
        return jsonify({'status': 'error', 'message': 'Access denied'}), 403
    
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT id, username, email, register_date, last_login, status FROM users WHERE is_admin = FALSE")
            )
            
            # Convert row objects to dictionaries
            users = []
            for row in result:
                user = {}
                for column, value in row._mapping.items():
                    user[column] = value
                users.append(user)
            
            # Format date fields
            for user in users:
                if user['register_date']:
                    user['register_date'] = user['register_date'].strftime('%Y-%m-%d %H:%M:%S')
                if user['last_login']:
                    user['last_login'] = user['last_login'].strftime('%Y-%m-%d %H:%M:%S')
            
            return jsonify({'status': 'success', 'users': users}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Failed to retrieve users: {str(e)}'}), 500

@app.route('/api/admin/users/search', methods=['GET'])
def search_users():
    """Search for users (admin only)
    
    Returns:
        JSON response containing matched users
    """
    if not session.get('is_admin', False):
        return jsonify({'status': 'error', 'message': 'Access denied'}), 403
    
    search_term = request.args.get('term', '')
    
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT id, username, email, register_date, last_login, status FROM users "
                     "WHERE (username LIKE :term OR email LIKE :term) AND is_admin = FALSE"),
                {"term": f'%{search_term}%'}
            )
            
            # Convert row objects to dictionaries
            users = []
            for row in result:
                user = {}
                for column, value in row._mapping.items():
                    user[column] = value
                users.append(user)
            
            # Format date fields
            for user in users:
                if user['register_date']:
                    user['register_date'] = user['register_date'].strftime('%Y-%m-%d %H:%M:%S')
                if user['last_login']:
                    user['last_login'] = user['last_login'].strftime('%Y-%m-%d %H:%M:%S')
            
            return jsonify({'status': 'success', 'users': users}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Search failed: {str(e)}'}), 500

# =============== User Asset Management APIs ===============
@app.route('/api/account', methods=['GET'])
def get_user_account():
    """Get current user's financial account information
    
    Returns:
        JSON response containing user account information
    """
    if not session.get('user_id'):
        return jsonify({'status': 'error', 'message': 'Please login first'}), 401
    
    user_id = session['user_id']
    
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT * FROM user_accounts WHERE user_id = :user_id"),
                {"user_id": user_id}
            )
            account = result.fetchone()
            
            if not account:
                return jsonify({'status': 'error', 'message': 'Account does not exist'}), 404
            
            # Convert row objects to dictionaries
            account_data = {}
            for column, value in account._mapping.items():
                account_data[column] = value
            
            # Format date fields
            date_fields = ['last_deposit_time', 'last_withdrawal_time', 'create_time', 'update_time']
            for field in date_fields:
                if account_data.get(field):
                    account_data[field] = account_data[field].strftime('%Y-%m-%d %H:%M:%S')
            
            return jsonify({'status': 'success', 'account': account_data}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Failed to retrieve account information: {str(e)}'}), 500

@app.route('/api/account/deposit', methods=['POST'])
def deposit_funds():
    """Deposit funds to user account
    
    Returns:
        JSON response indicating deposit result
    """
    if not session.get('user_id'):
        return jsonify({'status': 'error', 'message': 'Please login first'}), 401
    
    data = request.json
    user_id = session['user_id']
    amount = data.get('amount')
    description = data.get('description', 'User deposit')
    
    if not amount or float(amount) <= 0:
        return jsonify({'status': 'error', 'message': 'Deposit amount must be greater than 0'}), 400
    
    try:
        with engine.connect() as conn:
            # Start transaction
            trans = conn.begin()
            
            try:
                # Get user account information
                result = conn.execute(
                    text("SELECT * FROM user_accounts WHERE user_id = :user_id FOR UPDATE"),
                    {"user_id": user_id}
                )
                account = result.fetchone()
                
                if not account:
                    trans.rollback()
                    return jsonify({'status': 'error', 'message': 'Account does not exist'}), 404
                
                # Update account balance
                new_balance = float(account.balance) + float(amount)
                new_total_deposit = float(account.total_deposit) + float(amount)
                
                conn.execute(
                    text("UPDATE user_accounts SET balance = :balance, total_deposit = :total_deposit, "
                         "last_deposit_time = NOW() WHERE id = :account_id"),
                    {
                        "balance": new_balance,
                        "total_deposit": new_total_deposit,
                        "account_id": account.id
                    }
                )
                
                # Record transaction history
                conn.execute(
                    text("INSERT INTO transaction_history "
                         "(user_id, account_id, transaction_type, amount, balance_after, description) "
                         "VALUES (:user_id, :account_id, 'deposit', :amount, :balance_after, :description)"),
                    {
                        "user_id": user_id,
                        "account_id": account.id,
                        "amount": amount,
                        "balance_after": new_balance,
                        "description": description
                    }
                )
                
                # Commit transaction
                trans.commit()
                
                return jsonify({
                    'status': 'success',
                    'message': 'Deposit successful',
                    'new_balance': new_balance
                }), 200
                
            except Exception as e:
                trans.rollback()
                raise e
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Deposit failed: {str(e)}'}), 500

@app.route('/api/account/withdraw', methods=['POST'])
def withdraw_funds():
    """Withdraw funds from user account
    
    Returns:
        JSON response indicating withdrawal result
    """
    if not session.get('user_id'):
        return jsonify({'status': 'error', 'message': 'Please login first'}), 401
    
    data = request.json
    user_id = session['user_id']
    amount = data.get('amount')
    description = data.get('description', 'User withdrawal')
    
    if not amount or float(amount) <= 0:
        return jsonify({'status': 'error', 'message': 'Withdrawal amount must be greater than 0'}), 400
    
    try:
        with engine.connect() as conn:
            # Start transaction
            trans = conn.begin()
            
            try:
                # Get user account information
                result = conn.execute(
                    text("SELECT * FROM user_accounts WHERE user_id = :user_id FOR UPDATE"),
                    {"user_id": user_id}
                )
                account = result.fetchone()
                
                if not account:
                    trans.rollback()
                    return jsonify({'status': 'error', 'message': 'Account does not exist'}), 404
                
                # Check if balance is sufficient
                if float(account.balance) < float(amount):
                    trans.rollback()
                    return jsonify({'status': 'error', 'message': 'Insufficient account balance'}), 400
                
                # Update account balance
                new_balance = float(account.balance) - float(amount)
                new_total_withdrawal = float(account.total_withdrawal) + float(amount)
                
                conn.execute(
                    text("UPDATE user_accounts SET balance = :balance, total_withdrawal = :total_withdrawal, "
                         "last_withdrawal_time = NOW() WHERE id = :account_id"),
                    {
                        "balance": new_balance,
                        "total_withdrawal": new_total_withdrawal,
                        "account_id": account.id
                    }
                )
                
                # Record transaction history
                conn.execute(
                    text("INSERT INTO transaction_history "
                         "(user_id, account_id, transaction_type, amount, balance_after, description) "
                         "VALUES (:user_id, :account_id, 'withdrawal', :amount, :balance_after, :description)"),
                    {
                        "user_id": user_id,
                        "account_id": account.id,
                        "amount": amount,
                        "balance_after": new_balance,
                        "description": description
                    }
                )
                
                # Commit transaction
                trans.commit()
                
                return jsonify({
                    'status': 'success',
                    'message': 'Withdrawal successful',
                    'new_balance': new_balance
                }), 200
                
            except Exception as e:
                trans.rollback()
                raise e
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Withdrawal failed: {str(e)}'}), 500

@app.route('/api/positions', methods=['GET'])
def get_user_positions():
    """Get current user's stock position information
    
    Returns:
        JSON response containing user position information
    """
    if not session.get('user_id'):
        return jsonify({'status': 'error', 'message': 'Please login first'}), 401
    
    user_id = session['user_id']
    
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT * FROM user_positions WHERE user_id = :user_id AND quantity > 0"),
                {"user_id": user_id}
            )
            
            # Convert row objects to dictionaries
            positions = []
            for row in result:
                position = {}
                for column, value in row._mapping.items():
                    position[column] = value
                positions.append(position)
            
            # Format date fields
            for position in positions:
                if position.get('last_update_time'):
                    position['last_update_time'] = position['last_update_time'].strftime('%Y-%m-%d %H:%M:%S')
            
            # Calculate total asset value
            total_value = sum(float(p.get('market_value', 0)) for p in positions)
            
            return jsonify({
                'status': 'success', 
                'positions': positions,
                'total_value': total_value
            }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Failed to retrieve position information: {str(e)}'}), 500

@app.route('/api/transactions', methods=['GET'])
def get_transactions():
    """Get user transaction history
    
    Returns:
        JSON response containing user transaction history
    """
    if not session.get('user_id'):
        return jsonify({'status': 'error', 'message': 'Please login first'}), 401
    
    user_id = session['user_id']
    transaction_type = request.args.get('type')  # Optional filter
    limit = int(request.args.get('limit', 50))  # Default 50 records
    
    try:
        with engine.connect() as conn:
            query = "SELECT * FROM transaction_history WHERE user_id = :user_id"
            params = {"user_id": user_id}
            
            if transaction_type:
                query += " AND transaction_type = :transaction_type"
                params["transaction_type"] = transaction_type
                
            query += " ORDER BY transaction_time DESC LIMIT :limit"
            params["limit"] = limit
            
            result = conn.execute(text(query), params)
            
            # Convert row objects to dictionaries
            transactions = []
            for row in result:
                transaction = {}
                for column, value in row._mapping.items():
                    transaction[column] = value
                transactions.append(transaction)
            
            # Format date fields
            for transaction in transactions:
                if transaction.get('transaction_time'):
                    transaction['transaction_time'] = transaction['transaction_time'].strftime('%Y-%m-%d %H:%M:%S')
            
            return jsonify({'status': 'success', 'transactions': transactions}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Failed to retrieve transactions: {str(e)}'}), 500

# =============== Order APIs ===============
@app.route('/api/orders', methods=['POST'])
def create_order():
    """Create new order and handle related financial operations
    
    Returns:
        JSON response indicating order creation result
    """
    if not session.get('user_id'):
        return jsonify({'status': 'error', 'message': 'Please login first'}), 401
    
    data = request.json
    user_id = session['user_id']
    stock_symbol = data.get('symbol')
    order_type = data.get('orderType')  # 'realtime' or 'limit'
    trade_type = data.get('tradeType')  # 'buy' or 'sell'
    price = data.get('price')
    quantity = data.get('quantity')
    
    # Validate required fields
    if not all([stock_symbol, order_type, trade_type, price, quantity]):
        return jsonify({'status': 'error', 'message': 'All order fields are required'}), 400
    
    # Convert price and quantity to numeric values
    try:
        price = float(price)
        quantity = int(quantity)
    except ValueError:
        return jsonify({'status': 'error', 'message': 'Price and quantity must be valid numbers'}), 400
    
    # Calculate order total
    order_total = price * quantity
    
    try:
        with engine.connect() as conn:
            # Start transaction
            trans = conn.begin()
            
            try:
                # Get user account information
                result = conn.execute(
                    text("SELECT * FROM user_accounts WHERE user_id = :user_id FOR UPDATE"),
                    {"user_id": user_id}
                )
                account = result.fetchone()
                
                if not account:
                    trans.rollback()
                    return jsonify({'status': 'error', 'message': 'Account does not exist'}), 404
                
                # If it's a buy order, check if balance is sufficient
                if trade_type == 'buy':
                    if float(account.balance) < order_total:
                        trans.rollback()
                        return jsonify({'status': 'error', 'message': 'Insufficient account balance'}), 400
                    
                    # Freeze funds (temporarily deduct)
                    new_balance = float(account.balance) - order_total
                    
                    conn.execute(
                        text("UPDATE user_accounts SET balance = :balance WHERE id = :account_id"),
                        {
                            "balance": new_balance,
                            "account_id": account.id
                        }
                    )
                
                # Create order
                result = conn.execute(
                    text("INSERT INTO orders (user_id, stock_symbol, order_type, trade_type, price, quantity) "
                         "VALUES (:user_id, :stock_symbol, :order_type, :trade_type, :price, :quantity)"),
                    {
                        "user_id": user_id,
                        "stock_symbol": stock_symbol,
                        "order_type": order_type,
                        "trade_type": trade_type,
                        "price": price,
                        "quantity": quantity
                    }
                )
                
                # Get newly created order ID
                result = conn.execute(text("SELECT LAST_INSERT_ID() as id"))
                order_id_row = result.fetchone()
                order_id = order_id_row._mapping['id']
                
                # If it's a realtime order, immediately process order (simulated trade)
                if order_type == 'realtime':
                    # Update order status to completed
                    conn.execute(
                        text("UPDATE orders SET status = 'completed' WHERE id = :id"),
                        {"id": order_id}
                    )
                    
                    # If it's a buy, update position
                    if trade_type == 'buy':
                        # Add transaction history
                        conn.execute(
                            text("INSERT INTO transaction_history "
                                 "(user_id, account_id, transaction_type, amount, stock_symbol, quantity, price, order_id, balance_after, description) "
                                 "VALUES (:user_id, :account_id, 'buy', :amount, :stock_symbol, :quantity, :price, :order_id, :balance_after, :description)"),
                            {
                                "user_id": user_id,
                                "account_id": account.id,
                                "amount": order_total,
                                "stock_symbol": stock_symbol,
                                "quantity": quantity,
                                "price": price,
                                "order_id": order_id,
                                "balance_after": new_balance,
                                "description": f"Purchased {quantity} shares of {stock_symbol} at {price}"
                            }
                        )
                        
                        # Check if position already exists
                        result = conn.execute(
                            text("SELECT * FROM user_positions WHERE user_id = :user_id AND stock_symbol = :stock_symbol"),
                            {"user_id": user_id, "stock_symbol": stock_symbol}
                        )
                        position = result.fetchone()
                        
                        if position:
                            # Update existing position
                            total_quantity = position.quantity + quantity
                            total_cost = float(position.total_cost) + order_total
                            avg_price = total_cost / total_quantity
                            
                            conn.execute(
                                text("UPDATE user_positions SET quantity = :quantity, average_price = :average_price, "
                                     "total_cost = :total_cost, current_price = :current_price, market_value = :market_value "
                                     "WHERE id = :id"),
                                {
                                    "quantity": total_quantity,
                                    "average_price": avg_price,
                                    "total_cost": total_cost,
                                    "current_price": price,  # Assume current price is transaction price
                                    "market_value": total_quantity * price,
                                    "id": position.id
                                }
                            )
                        else:
                            # Create new position
                            conn.execute(
                                text("INSERT INTO user_positions "
                                     "(user_id, stock_symbol, quantity, average_price, total_cost, current_price, market_value) "
                                     "VALUES (:user_id, :stock_symbol, :quantity, :average_price, :total_cost, :current_price, :market_value)"),
                                {
                                    "user_id": user_id,
                                    "stock_symbol": stock_symbol,
                                    "quantity": quantity,
                                    "average_price": price,
                                    "total_cost": order_total,
                                    "current_price": price,
                                    "market_value": quantity * price
                                }
                            )
                    
                    # If it's a sell, update position and add funds
                    elif trade_type == 'sell':
                        # Check if there's enough position to sell
                        result = conn.execute(
                            text("SELECT * FROM user_positions WHERE user_id = :user_id AND stock_symbol = :stock_symbol"),
                            {"user_id": user_id, "stock_symbol": stock_symbol}
                        )
                        position = result.fetchone()
                        
                        if not position or position.quantity < quantity:
                            trans.rollback()
                            return jsonify({'status': 'error', 'message': 'Insufficient position'}), 400
                        
                        # Calculate new position quantity and cost
                        new_quantity = position.quantity - quantity
                        new_total_cost = float(position.total_cost) * (new_quantity / position.quantity)
                        new_average_price = new_total_cost / new_quantity if new_quantity > 0 else 0
                        
                        # Update position
                        conn.execute(
                            text("UPDATE user_positions SET quantity = :quantity, average_price = :average_price, "
                                 "total_cost = :total_cost, current_price = :current_price, market_value = :market_value "
                                 "WHERE id = :id"),
                            {
                                "quantity": new_quantity,
                                "average_price": new_average_price,
                                "total_cost": new_total_cost,
                                "current_price": price,
                                "market_value": new_quantity * price,
                                "id": position.id
                            }
                        )
                        
                        # Update account balance
                        new_balance = float(account.balance) + order_total
                        conn.execute(
                            text("UPDATE user_accounts SET balance = :balance WHERE id = :account_id"),
                            {
                                "balance": new_balance,
                                "account_id": account.id
                            }
                        )
                        
                        # Add transaction history
                        conn.execute(
                            text("INSERT INTO transaction_history "
                                 "(user_id, account_id, transaction_type, amount, stock_symbol, quantity, price, order_id, balance_after, description) "
                                 "VALUES (:user_id, :account_id, 'sell', :amount, :stock_symbol, :quantity, :price, :order_id, :balance_after, :description)"),
                            {
                                "user_id": user_id,
                                "account_id": account.id,
                                "amount": order_total,
                                "stock_symbol": stock_symbol,
                                "quantity": quantity,
                                "price": price,
                                "order_id": order_id,
                                "balance_after": new_balance,
                                "description": f"Sold {quantity} shares of {stock_symbol} at {price}"
                            }
                        )
                
                # Commit transaction
                trans.commit()
                
                return jsonify({
                    'status': 'success', 
                    'message': 'Order created successfully',
                    'order_id': order_id
                }), 201
                
            except Exception as e:
                trans.rollback()
                raise e
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Failed to create order: {str(e)}'}), 500

@app.route('/api/orders', methods=['GET'])
def get_user_orders():
    """Get all orders for current user
    
    Returns:
        JSON response containing user orders
    """
    if not session.get('user_id'):
        return jsonify({'status': 'error', 'message': 'Please login first'}), 401
    
    user_id = session['user_id']
    order_type = request.args.get('type')  # Optional filter
    status = request.args.get('status')    # Optional filter
    
    try:
        with engine.connect() as conn:
            query = "SELECT * FROM orders WHERE user_id = :user_id"
            params = {"user_id": user_id}
            
            if order_type:
                query += " AND order_type = :order_type"
                params["order_type"] = order_type
                
            if status:
                query += " AND status = :status"
                params["status"] = status
                
            query += " ORDER BY order_time DESC"
            
            result = conn.execute(text(query), params)
            orders = [dict(row) for row in result]
            
            # Format date fields
            for order in orders:
                order['order_time'] = order['order_time'].strftime('%Y-%m-%d %H:%M:%S')
                order['update_time'] = order['update_time'].strftime('%Y-%m-%d %H:%M:%S')
            
            return jsonify({'status': 'success', 'orders': orders}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Failed to retrieve orders: {str(e)}'}), 500

@app.route('/api/orders/<int:order_id>', methods=['PUT'])
def update_order(order_id):
    """Update order status (e.g., cancel order)
    
    Returns:
        JSON response indicating order update result
    """
    if not session.get('user_id'):
        return jsonify({'status': 'error', 'message': 'Please login first'}), 401
    
    user_id = session['user_id']
    data = request.json
    new_status = data.get('status')
    
    if not new_status:
        return jsonify({'status': 'error', 'message': 'Missing status parameter'}), 400
    
    try:
        with engine.connect() as conn:
            # Verify if order belongs to current user
            result = conn.execute(
                text("SELECT * FROM orders WHERE id = :id AND user_id = :user_id"),
                {"id": order_id, "user_id": user_id}
            )
            order = result.fetchone()
            
            if not order:
                return jsonify({'status': 'error', 'message': 'Order does not exist or does not belong to current user'}), 404
            
            # Update order status
            conn.execute(
                text("UPDATE orders SET status = :status WHERE id = :id"),
                {"status": new_status, "id": order_id}
            )
            conn.commit()
            
            return jsonify({'status': 'success', 'message': 'Order updated successfully'}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Failed to update order: {str(e)}'}), 500

# =============== Existing routes remain unchanged ===============
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