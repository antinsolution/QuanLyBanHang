import sqlite3
from flask import Blueprint, render_template, request, redirect, url_for, flash
from database import get_db # Import get_db từ app.py

# Khởi tạo Blueprint cho Customers
customers_bp = Blueprint('customers_bp', __name__, template_folder='../templates/customers')

# --- Customer Management ---

@customers_bp.route('/')
def customers():
    db = get_db()
    customers_data = db.execute('SELECT * FROM customers ORDER BY name').fetchall()
    return render_template('customers.html', customers=customers_data)

@customers_bp.route('/add', methods=('GET', 'POST'))
def add_customer():
    if request.method == 'POST':
        name = request.form['name'].strip()
        phone = request.form['phone'].strip()
        email = request.form['email'].strip()
        address = request.form['address'].strip()

        if not name:
            flash('Tên khách hàng không được để trống!', 'danger')
        else:
            db = get_db()
            try:
                db.execute('INSERT INTO customers (name, phone, email, address) VALUES (?, ?, ?, ?)',
                           (name, phone if phone else None, email if email else None, address if address else None))
                db.commit()
                flash('Khách hàng đã được thêm thành công!', 'success')
                return redirect(url_for('customers_bp.customers')) # Sửa lại url_for
            except Exception as e:
                flash(f'Có lỗi xảy ra khi thêm khách hàng: {e}', 'danger')

    return render_template('add_customer.html')

@customers_bp.route('/edit/<int:id>', methods=('GET', 'POST'))
def edit_customer(id):
    db = get_db()
    customer = db.execute('SELECT * FROM customers WHERE id = ?', (id,)).fetchone()

    if customer is None:
        flash('Không tìm thấy khách hàng.', 'danger')
        return redirect(url_for('customers_bp.customers')) # Sửa lại url_for

    if request.method == 'POST':
        name = request.form['name'].strip()
        phone = request.form['phone'].strip()
        email = request.form['email'].strip()
        address = request.form['address'].strip()

        if not name:
            flash('Tên khách hàng không được để trống!', 'danger')
        else:
            try:
                db.execute('UPDATE customers SET name = ?, phone = ?, email = ?, address = ? WHERE id = ?',
                           (name, phone if phone else None, email if email else None, address if address else None, id))
                db.commit()
                flash('Thông tin khách hàng đã được cập nhật!', 'success')
                return redirect(url_for('customers_bp.customers')) # Sửa lại url_for
            except Exception as e:
                flash(f'Có lỗi xảy ra khi cập nhật khách hàng: {e}', 'danger')

    return render_template('edit_customer.html', customer=customer)

@customers_bp.route('/delete/<int:id>', methods=('POST',))
def delete_customer(id):
    db = get_db()
    try:
        db.execute('DELETE FROM customers WHERE id = ?', (id,))
        db.commit()
        flash('Khách hàng đã được xóa thành công!', 'success')
    except Exception as e:
        flash(f'Không thể xóa khách hàng: {e}. Vui lòng kiểm tra lại.', 'danger')
    return redirect(url_for('customers_bp.customers')) # Sửa lại url_for