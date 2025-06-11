import sqlite3
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from database import get_db # Import get_db từ app.py

# Khởi tạo Blueprint cho Products
# template_folder='../templates/products' sẽ cho phép Blueprint tìm templates trong thư mục templates/products/
products_bp = Blueprint('products_bp', __name__, template_folder='../templates/products')

# --- Product Management ---

@products_bp.route('/')
def products():
    db = get_db()
    products = db.execute('SELECT * FROM products ORDER BY name').fetchall()
    return render_template('products.html', products=products)

@products_bp.route('/add', methods=('GET', 'POST'))
def add_product():
    if request.method == 'POST':
        name = request.form['name'].strip()
        price_str = request.form['price'].strip()
        stock_str = request.form['stock'].strip()

        if not name or not price_str or not stock_str:
            flash('Vui lòng điền đầy đủ tất cả các trường!', 'danger')
        else:
            try:
                price = float(price_str)
                stock = int(stock_str)
                if price <= 0 or stock < 0:
                    flash('Giá phải dương và tồn kho không thể âm!', 'danger')
                    return render_template('add_product.html')

                db = get_db()
                db.execute('INSERT INTO products (name, price, stock) VALUES (?, ?, ?)',
                           (name, price, stock))
                db.commit()
                flash('Sản phẩm đã được thêm thành công!', 'success')
                return redirect(url_for('products_bp.products'))
            except ValueError:
                flash('Giá và số lượng tồn kho phải là số hợp lệ!', 'danger')
            except sqlite3.IntegrityError:
                flash(f'Sản phẩm "{name}" đã tồn tại. Vui lòng chọn tên khác.', 'danger')

    return render_template('add_product.html')

@products_bp.route('/edit/<int:id>', methods=('GET', 'POST'))
def edit_product(id):
    db = get_db()
    product = db.execute('SELECT * FROM products WHERE id = ?', (id,)).fetchone()

    if product is None:
        flash('Không tìm thấy sản phẩm.', 'danger')
        return redirect(url_for('products_bp.products'))

    if request.method == 'POST':
        name = request.form['name'].strip()
        price_str = request.form['price'].strip()
        stock_str = request.form['stock'].strip() 

        if not name or not price_str or not stock_str:
            flash('Vui lòng điền đầy đủ tất cả các trường!', 'danger')
        else:
            try:
                price = float(price_str)
                stock = int(stock_str)
                if price <= 0 or stock < 0:
                    flash('Giá phải dương và tồn kho không thể âm!', 'danger')
                    return render_template('edit_product.html', product=product)

                db.execute('UPDATE products SET name = ?, price = ?, stock = ? WHERE id = ?',
                           (name, price, stock, id))
                db.commit()
                flash('Sản phẩm đã được cập nhật thành công!', 'success')
                return redirect(url_for('products_bp.products'))
            except ValueError:
                flash('Giá và số lượng tồn kho phải là số hợpomaly!', 'danger')
            except sqlite3.IntegrityError:
                flash(f'Sản phẩm "{name}" đã tồn tại. Vui lòng chọn tên khác.', 'danger')

    return render_template('edit_product.html', product=product)

@products_bp.route('/delete/<int:id>', methods=('POST',))
def delete_product(id):
    db = get_db()
    db.execute('DELETE FROM products WHERE id = ?', (id,))
    db.commit()
    flash('Sản phẩm đã được xóa thành công!', 'success')
    return redirect(url_for('products_bp.products'))

# --- Inventory Management (Manual Stock Adjustment) ---

@products_bp.route('/adjust_stock/<int:id>', methods=('GET', 'POST'))
def adjust_stock(id):
    db = get_db()
    product = db.execute('SELECT * FROM products WHERE id = ?', (id,)).fetchone()

    if product is None:
        flash('Không tìm thấy sản phẩm.', 'danger')
        return redirect(url_for('products_bp.products'))

    if request.method == 'POST':
        adjustment_type = request.form['adjustment_type']
        quantity_str = request.form['quantity'].strip()

        if not quantity_str:
            flash('Vui lòng nhập số lượng điều chỉnh.', 'danger')
            return render_template('adjust_stock.html', product=product)

        try:
            quantity = int(quantity_str)
            if quantity <= 0:
                flash('Số lượng phải là số nguyên dương.', 'danger')
                return render_template('adjust_stock.html', product=product)

            new_stock = product['stock']
            if adjustment_type == 'increase':
                new_stock += quantity
                flash_msg = f'Đã tăng tồn kho của "{product["name"]}" thêm {quantity}.'
            elif adjustment_type == 'decrease':
                if new_stock < quantity:
                    flash(f'Không đủ tồn kho để giảm. Tồn kho hiện tại: {new_stock}.', 'danger')
                    return render_template('adjust_stock.html', product=product)
                new_stock -= quantity
                flash_msg = f'Đã giảm tồn kho của "{product["name"]}" bớt {quantity}.'
            else:
                flash('Loại điều chỉnh không hợp lệ.', 'danger')
                return render_template('adjust_stock.html', product=product)

            db.execute('UPDATE products SET stock = ? WHERE id = ?', (new_stock, id))
            db.commit()
            flash(flash_msg, 'success')
            return redirect(url_for('products_bp.products'))

        except ValueError:
            flash('Số lượng phải là số nguyên hợp lệ.', 'danger')
        
    return render_template('adjust_stock.html', product=product)

# --- API for Product Search (Tạm thời đặt ở đây, có thể tách riêng nếu API phức tạp hơn) ---
@products_bp.route('/api/search') # Đường dẫn đầy đủ sẽ là /products/api/search
def api_product_search():
    query = request.args.get('q', '').strip()
    db = get_db()
    if query:
        products = db.execute(
            'SELECT id, name, price, stock FROM products WHERE name LIKE ? AND stock > 0 ORDER BY name LIMIT 10',
            ('%' + query + '%',)
        ).fetchall()
        return jsonify([dict(product) for product in products])
    return jsonify([])