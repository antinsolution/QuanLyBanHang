import sqlite3
from flask import Blueprint, render_template, request, redirect, url_for, flash
import datetime
from database import get_db # Import get_db từ app.py

# Import customers_bp để có thể dùng url_for tới customers (ví dụ trong template)
# Tuy nhiên, nếu chỉ cần dữ liệu khách hàng cho form add_sale, bạn có thể query trực tiếp.
# from blueprints.customers import customers_bp # Không cần import nếu chỉ query DB

# Khởi tạo Blueprint cho Sales
sales_bp = Blueprint('sales_bp', __name__, template_folder='../templates/sales')

# --- Sales Management ---

@sales_bp.route('/')
def sales():
    db = get_db()
    sales_data = db.execute('''
        SELECT s.id, s.sale_date, s.total_amount, COUNT(si.id) AS num_items, c.name AS customer_name
        FROM sales s
        LEFT JOIN sale_items si ON s.id = si.sale_id
        LEFT JOIN customers c ON s.customer_id = c.id
        GROUP BY s.id
        ORDER BY s.sale_date DESC
    ''').fetchall()
    return render_template('sales.html', sales=sales_data)

@sales_bp.route('/add', methods=('GET', 'POST'))
def add_sale():
    db = get_db()
    customers = db.execute('SELECT id, name, phone FROM customers ORDER BY name').fetchall()

    if request.method == 'POST':
        customer_id = request.form.get('customer_id')
        if customer_id == 'none' or not customer_id:
            customer_id = None
        else:
            customer_id = int(customer_id)

        product_ids = request.form.getlist('item_product_id[]')
        quantities = request.form.getlist('item_quantity[]')
        prices_at_sale = request.form.getlist('item_price_at_sale[]')

        selected_products_data = []
        total_amount = 0
        has_error = False

        conn = get_db()
        cursor = conn.cursor()

        product_stock_map = {}
        if product_ids:
            placeholders = ','.join('?' * len(product_ids))
            query = f"SELECT id, name, stock FROM products WHERE id IN ({placeholders})" # Lấy thêm tên để thông báo lỗi rõ hơn
            for p in cursor.execute(query, tuple(product_ids)).fetchall():
                product_stock_map[p['id']] = {'stock': p['stock'], 'name': p['name']}
        
        for i in range(len(product_ids)):
            try:
                p_id = int(product_ids[i])
                qty = int(quantities[i])
                price_at_sale = float(prices_at_sale[i])

                if qty <= 0:
                    flash(f'Số lượng sản phẩm không hợp lệ cho sản phẩm ID: {p_id}.', 'danger')
                    has_error = True
                    break

                product_info = product_stock_map.get(p_id)
                if not product_info:
                    flash(f'Sản phẩm với ID {p_id} không tồn tại hoặc đã hết hàng.', 'danger')
                    has_error = True
                    break

                actual_stock = product_info['stock']
                product_name = product_info['name']

                if qty > actual_stock:
                    flash(f'Sản phẩm "{product_name}" không đủ tồn kho. Yêu cầu: {qty}, Tồn: {actual_stock}.', 'danger')
                    has_error = True
                    break
                
                selected_products_data.append({
                    'product_id': p_id,
                    'quantity': qty,
                    'price_at_sale': price_at_sale
                })
                total_amount += qty * price_at_sale

            except ValueError:
                flash('Dữ liệu sản phẩm không hợp lệ (số lượng hoặc giá).', 'danger')
                has_error = True
                break

        if not selected_products_data or has_error:
            return render_template('add_sale.html', products=[], customers=customers)

        try:
            sale_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            cursor.execute('INSERT INTO sales (sale_date, total_amount, customer_id) VALUES (?, ?, ?)', 
                           (sale_date, total_amount, customer_id))
            sale_id = cursor.lastrowid

            for item in selected_products_data:
                cursor.execute('INSERT INTO sale_items (sale_id, product_id, quantity, price_at_sale) VALUES (?, ?, ?, ?)',
                               (sale_id, item['product_id'], item['quantity'], item['price_at_sale']))
                cursor.execute('UPDATE products SET stock = stock - ? WHERE id = ?', (item['quantity'], item['product_id']))
            
            conn.commit()
            flash('Giao dịch bán hàng đã được ghi nhận thành công!', 'success')
            return redirect(url_for('sales_bp.sales')) # Sửa lại url_for

        except Exception as e:
            conn.rollback()
            flash(f'Có lỗi xảy ra khi ghi nhận giao dịch: {e}', 'danger')
            print(f"Error during sale transaction: {e}")
            return render_template('add_sale.html', products=[], customers=customers)

    return render_template('add_sale.html', products=[], customers=customers)

@sales_bp.route('/detail/<int:sale_id>')
def sale_detail(sale_id):
    db = get_db()
    sale = db.execute('''
        SELECT s.*, c.name AS customer_name
        FROM sales s
        LEFT JOIN customers c ON s.customer_id = c.id
        WHERE s.id = ?
    ''', (sale_id,)).fetchone()
    
    if sale is None:
        flash('Không tìm thấy giao dịch này.', 'danger')
        return redirect(url_for('sales_bp.sales')) # Sửa lại url_for

    sale_items = db.execute('''
        SELECT si.quantity, si.price_at_sale, p.name 
        FROM sale_items si
        JOIN products p ON si.product_id = p.id
        WHERE si.sale_id = ?
    ''', (sale_id,)).fetchall()

    return render_template('sale_detail.html', sale=sale, sale_items=sale_items)