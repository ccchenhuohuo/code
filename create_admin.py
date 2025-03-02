from sqlalchemy import create_engine, text
from werkzeug.security import generate_password_hash
import os
from datetime import datetime
import secrets

# 数据库连接配置 - 与app.py匹配
DB_CONFIG = {
    'user': 'root',
    'password': 'Cyy-20030611',
    'host': 'localhost',
    'port': '3306',
    'database': 'stock_data'
}

# 创建SQLAlchemy引擎
connection_string = f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}?charset=utf8"
engine = create_engine(connection_string, echo=False)

def create_admin_user():
    """创建管理员用户"""
    username = 'admin'
    password = 'admin123'  # 简单密码用于测试，实际环境应使用更强密码
    email = 'admin@system.com'
    
    # 生成密码哈希
    password_hash = generate_password_hash(password)
    
    try:
        with engine.connect() as conn:
            # 检查管理员用户是否已存在
            result = conn.execute(
                text("SELECT id FROM users WHERE username = :username OR email = :email"),
                {'username': username, 'email': email}
            )
            
            if result.fetchone():
                print("管理员账户已存在，更新为管理员权限...")
                conn.execute(
                    text("UPDATE users SET is_admin = TRUE WHERE username = :username OR email = :email"),
                    {'username': username, 'email': email}
                )
            else:
                print("创建新的管理员账户...")
                # 插入管理员用户
                conn.execute(
                    text("INSERT INTO users (username, password, email, register_date, last_login, status, is_admin) "
                         "VALUES (:username, :password, :email, NOW(), NOW(), 'active', TRUE)"),
                    {
                        'username': username,
                        'password': password_hash,
                        'email': email
                    }
                )
            
            conn.commit()
            print(f"管理员账户已创建/更新成功。用户名: {username}, 密码: {password}")
            
    except Exception as e:
        print(f"创建管理员账户时出错: {str(e)}")

if __name__ == "__main__":
    create_admin_user() 