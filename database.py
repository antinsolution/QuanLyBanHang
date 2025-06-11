# sales_management_app/database.py

import sqlite3
from flask import g # Import g từ Flask để sử dụng trong get_db

# Tên file database
DATABASE = 'sales.db'

def get_db():
    """Mở kết nối database nếu chưa có, và thiết lập row_factory."""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row  # Trả về hàng dưới dạng dictionary/Row object
        db.execute("PRAGMA foreign_keys = ON") # Bật Foreign Key Enforcement
    return db

def close_connection(exception):
    """Đóng kết nối database khi context ứng dụng kết thúc."""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db(app): # app được truyền vào để sử dụng app.app_context()
    """Khởi tạo các bảng database nếu chúng chưa tồn tại."""
    with app.app_context(): # Cần context của ứng dụng để sử dụng get_db()
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                price REAL NOT NULL,
                stock INTEGER NOT NULL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT,
                email TEXT,
                address TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_date TEXT NOT NULL,
                total_amount REAL NOT NULL,
                customer_id INTEGER,
                FOREIGN KEY (customer_id) REFERENCES customers (id) ON DELETE SET NULL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sale_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                price_at_sale REAL NOT NULL,
                FOREIGN KEY (sale_id) REFERENCES sales (id),
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
        ''')
        db.commit()

# Bạn có thể thêm một hàm để gọi init_db từ bên ngoài nếu muốn
# Hoặc cứ gọi trực tiếp init_db(app) từ app.py