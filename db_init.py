#!/usr/bin/env python3
"""
Database Initialization Script
Creates user and order related table structures
"""
from sqlalchemy import create_engine, text
from werkzeug.security import generate_password_hash

# Database configuration
DB_CONFIG = {
    'user': 'root',
    'password': 'Cyy-20030611',
    'host': 'localhost',
    'port': '3306',
    'database': 'stock_data'
}

def init_database():
    """Initialize database and create necessary tables"""
    # Create database connection
    connection_string = f"mysql+mysqlconnector://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}?charset=utf8"
    engine = create_engine(connection_string, echo=True)
    
    # Create users table
    users_table = """
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(50) NOT NULL UNIQUE,
        email VARCHAR(100) NOT NULL UNIQUE,
        password VARCHAR(255) NOT NULL,
        register_date DATETIME DEFAULT CURRENT_TIMESTAMP,
        last_login DATETIME,
        is_admin BOOLEAN DEFAULT FALSE,
        status ENUM('active', 'inactive', 'suspended') DEFAULT 'active'
    );
    """
    
    # Create orders table
    orders_table = """
    CREATE TABLE IF NOT EXISTS orders (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        stock_symbol VARCHAR(10) NOT NULL,
        order_type ENUM('realtime', 'limit') NOT NULL,
        trade_type ENUM('buy', 'sell') NOT NULL,
        price DECIMAL(10, 2) NOT NULL,
        quantity INT NOT NULL,
        status ENUM('pending', 'completed', 'cancelled') DEFAULT 'pending',
        order_time DATETIME DEFAULT CURRENT_TIMESTAMP,
        update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    );
    """
    
    # Create user accounts table
    user_accounts_table = """
    CREATE TABLE IF NOT EXISTS user_accounts (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        balance DECIMAL(15, 2) NOT NULL DEFAULT 0.00,
        total_deposit DECIMAL(15, 2) NOT NULL DEFAULT 0.00,
        total_withdrawal DECIMAL(15, 2) NOT NULL DEFAULT 0.00,
        last_deposit_time DATETIME,
        last_withdrawal_time DATETIME,
        status ENUM('active', 'frozen', 'closed') DEFAULT 'active',
        create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
        update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    );
    """
    
    # Create user positions table
    user_positions_table = """
    CREATE TABLE IF NOT EXISTS user_positions (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        stock_symbol VARCHAR(10) NOT NULL,
        quantity INT NOT NULL DEFAULT 0,
        average_price DECIMAL(10, 2) NOT NULL,
        total_cost DECIMAL(15, 2) NOT NULL,
        current_price DECIMAL(10, 2),
        market_value DECIMAL(15, 2),
        profit_loss DECIMAL(15, 2),
        profit_loss_percent DECIMAL(8, 2),
        last_update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id),
        UNIQUE KEY (user_id, stock_symbol)
    );
    """
    
    # Create transaction history table
    transaction_history_table = """
    CREATE TABLE IF NOT EXISTS transaction_history (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        account_id INT NOT NULL,
        transaction_type ENUM('deposit', 'withdrawal', 'buy', 'sell', 'fee', 'dividend') NOT NULL,
        amount DECIMAL(15, 2) NOT NULL,
        stock_symbol VARCHAR(10),
        quantity INT,
        price DECIMAL(10, 2),
        order_id INT,
        balance_after DECIMAL(15, 2) NOT NULL,
        transaction_time DATETIME DEFAULT CURRENT_TIMESTAMP,
        description VARCHAR(255),
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (account_id) REFERENCES user_accounts(id),
        FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE SET NULL
    );
    """
    
    # Execute SQL to create tables
    with engine.connect() as connection:
        connection.execute(text(users_table))
        connection.execute(text(orders_table))
        connection.execute(text(user_accounts_table))
        connection.execute(text(user_positions_table))
        connection.execute(text(transaction_history_table))
        
        # Check if admin account already exists
        result = connection.execute(text("SELECT COUNT(*) as count FROM users WHERE is_admin = TRUE"))
        admin_count = result.fetchone()[0]
        
        # If no admin account exists, create a default admin account
        # Password is 'admin123' (hashed)
        if admin_count == 0:
            admin_password = generate_password_hash('admin123')
            connection.execute(
                text("INSERT INTO users (username, email, password, is_admin) VALUES (:username, :email, :password, TRUE)"),
                {"username": "admin", "email": "admin@example.com", "password": admin_password}
            )
            print("Created default admin account (username: admin, password: admin123)")
        
        # Check if we need to automatically create financial accounts for new users
        connection.execute(text("""
        INSERT INTO user_accounts (user_id, balance)
        SELECT id, 100000.00
        FROM users
        WHERE id NOT IN (SELECT user_id FROM user_accounts)
        """))
        
        print("Created financial accounts for new users with initial balance of 100,000.00")
        
        connection.commit()
    
    print("Database initialization complete!")

if __name__ == "__main__":
    init_database() 