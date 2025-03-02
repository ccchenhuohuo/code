# MySQL Database Integration Guide

This document provides instructions for deploying and using MySQL database integration with the stock trading system.

## Feature List

The integration implements the following features:

1. User registration, login, and authentication system
2. Admin interface and user management functions
3. Real-time trading order functionality
4. User order history viewing and management
5. User asset management (financial accounts, position information)
6. Transaction history recording

## Prerequisites

- Python 3.8+
- MySQL 8.0+
- Flask and related dependencies

## Installation Steps

### 1. Ensure MySQL service is running

Run MySQL service locally and ensure it can be connected using the following configuration:

```
Username: root
Password: Cyy-20030611
Host: localhost
Port: 3306
Database name: stock_data
```

If using a different configuration, please update the DB_CONFIG in `app.py` and `db_init.py`.

### 2. Create database

In MySQL, create the `stock_data` database (if it doesn't exist):

```sql
CREATE DATABASE IF NOT EXISTS stock_data;
```

### 3. Install Python dependencies

```bash
pip install flask sqlalchemy flask-sqlalchemy mysql-connector-python werkzeug
```

### 4. Initialize database

Run the database initialization script:

```bash
python db_init.py
```

This script will create the necessary database tables and add a default admin account.

### 5. Start the application

```bash
python app.py
```

The application will start at http://localhost:5001.

## Default Account Information

The initialization script creates a default admin account:

- Username: admin
- Email: admin@example.com
- Password: admin123

## Usage Instructions

### User Operations

1. **Register a new account**:
   - Click the "Register now" link on the login screen
   - Fill in username, email, and password
   - Click the "Register" button to complete registration

2. **Login to system**:
   - Enter username and password on the login screen
   - Click the "Login" button

3. **View and place stock orders**:
   - Search for a stock in the "Real-time price" page
   - Fill in the order form
   - Click "Place order" button to submit the order

4. **View account and positions**:
   - Navigate to the "Account & Trading" section
   - View account balance, positions, and transaction history
   - Use the deposit functionality to add funds to your account

### Admin Operations

1. **Login to admin panel**:
   - Click "Admin portal" on the login screen
   - Enter admin credentials
   - Click "Login"

2. **Manage users**:
   - View the list of all registered users
   - Search for specific users
   - View detailed information for each user

## API Documentation

The system provides the following key API endpoints:

### Authentication APIs
- `POST /api/register` - Register a new user
- `POST /api/login` - User login
- `POST /api/admin/login` - Admin login
- `POST /api/logout` - Logout (clear session)

### User Management APIs
- `GET /api/login/current` - Get current logged-in user info
- `GET /api/admin/users` - Get all users (admin only)
- `GET /api/admin/users/search` - Search users (admin only)

### Account Management APIs
- `GET /api/account` - Get user account information
- `POST /api/account/deposit` - Deposit funds
- `POST /api/account/withdraw` - Withdraw funds
- `GET /api/positions` - Get user stock positions
- `GET /api/transactions` - Get transaction history

### Order APIs
- `POST /api/orders` - Create new order
- `GET /api/orders` - Get user orders
- `PUT /api/orders/<order_id>` - Update order status

## Database Schema

The system uses the following main tables:

1. `users` - User information and authentication
2. `user_accounts` - User financial accounts
3. `user_positions` - User stock positions
4. `orders` - Trading orders
5. `transaction_history` - Record of all financial transactions

For detailed table structures, please refer to `db_init.py`.

## Security Notes

- User passwords are hashed before storage
- Session management is implemented for authentication
- Transaction operations use database transactions to ensure data integrity

## Troubleshooting

If you encounter issues:

1. Ensure MySQL service is running
2. Verify database connection parameters
3. Check console logs for specific error messages
4. Ensure all dependencies are installed correctly

## Future Improvements

1. Enhanced user permission management
2. Improved transaction processing with status tracking
3. Multi-factor authentication for security
4. Real-time account value updates based on market prices
5. Enhanced admin dashboard with analytics 