# sales_management_app/app.py

import webbrowser
import threading
import time
import os
from flask import Flask, render_template

# Import các hàm database từ module database.py MỚI
from database import get_db, close_connection, init_db

# Import các Blueprints
from blueprints.products import products_bp
from blueprints.sales import sales_bp
from blueprints.customers import customers_bp

app = Flask(__name__)
app.secret_key = 'day_la_mot_chuoi_bi_mat_rat_bao_mat_cua_ban_hay_thay_doi_no' 

# Gán hàm close_connection vào teardown_appcontext
app.teardown_appcontext(close_connection)

# --- Đăng ký các Blueprints ---
app.register_blueprint(products_bp, url_prefix='/products')
app.register_blueprint(sales_bp, url_prefix='/sales')
app.register_blueprint(customers_bp, url_prefix='/customers')

# --- Main Route (Trang chủ) ---
@app.route('/')
def index():
    db = get_db() # Sử dụng get_db từ database.py
    cursor = db.cursor()
    total_products = cursor.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    total_sales_transactions = cursor.execute("SELECT COUNT(*) FROM sales").fetchone()[0]
    total_revenue = cursor.execute("SELECT SUM(total_amount) FROM sales").fetchone()[0]
    if total_revenue is None:
        total_revenue = 0
    total_customers = cursor.execute("SELECT COUNT(*) FROM customers").fetchone()[0]

    return render_template('index.html', 
                           total_products=total_products, 
                           total_sales_transactions=total_sales_transactions,
                           total_revenue=total_revenue,
                           total_customers=total_customers)

# --- Function to open the browser automatically ---
def open_browser():
    time.sleep(1.5) 
    webbrowser.open_new("http://127.0.0.1:5000/")

# --- Run the app ---
if __name__ == '__main__':
    init_db(app) # Truyền đối tượng app vào init_db
    if not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        threading.Thread(target=open_browser).start()
    app.run(host='127.0.0.1', port=5000, debug=False)