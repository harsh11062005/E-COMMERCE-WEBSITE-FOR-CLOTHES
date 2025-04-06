from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_bootstrap import Bootstrap
import mysql.connector
from functools import wraps
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
Bootstrap(app)
app.secret_key = 'your-secret-key-here'

# Database configuration
DB_CONFIG = {
    'database': 'thrifty',
    'user': 'root',
    'password': 'Sunny@2411',
    'host': 'localhost'
}

# Upload configuration
UPLOAD_FOLDER = 'static/images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def get_db_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('user_type') != 'employee' or not session.get('is_admin'):
            flash('Admin access required.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor(dictionary=True)  # This will return results as dictionaries
            cur.execute('SELECT * FROM products')
            products = cur.fetchall()
            cur.close()
            conn.close()
            return render_template('index.html', products=products)
        except mysql.connector.Error as e:
            print(f"Error: {e}")
            flash('Error loading products', 'error')
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user_type = request.form['user_type']
        
        conn = get_db_connection()
        if conn:
            try:
                cur = conn.cursor()
                
                # First check if the email exists
                if user_type == 'customer':
                    cur.execute('SELECT * FROM customers WHERE email_address = %s', (email,))
                elif user_type == 'employee':
                    cur.execute('SELECT * FROM employees WHERE email = %s', (email,))
                else:  # seller
                    cur.execute('SELECT * FROM sellers WHERE email = %s', (email,))
                
                user = cur.fetchone()
                
                if not user:
                    flash('Invalid email address', 'error')
                    return render_template('login.html')
                
                # Now check password
                if user_type == 'customer':
                    cur.execute('SELECT * FROM customers WHERE email_address = %s AND password = %s',
                              (email, password))
                elif user_type == 'employee':
                    cur.execute('SELECT * FROM employees WHERE email = %s AND password = %s',
                              (email, password))
                else:  # seller
                    cur.execute('SELECT * FROM sellers WHERE email = %s AND password = %s',
                              (email, password))
                
                user = cur.fetchone()
                
                if user:
                    session['user_id'] = user[0]  # First column is ID
                    session['user_type'] = user_type
                    
                    if user_type == 'employee':
                        session['is_admin'] = user[6]  # is_admin column
                        if user[6]:  # is_admin
                            return redirect(url_for('admin_dashboard'))
                        return redirect(url_for('employee_dashboard'))
                    elif user_type == 'seller':
                        return redirect(url_for('seller_dashboard'))
                    else:
                        return redirect(url_for('index'))
                else:
                    flash('Invalid password', 'error')
            except mysql.connector.Error as e:
                print(f"Error: {e}")
                flash('Login error', 'error')
            finally:
                cur.close()
                conn.close()
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    user_type = request.args.get('user_type', 'customer')  # Default to customer if not specified
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        
        conn = get_db_connection()
        if conn:
            try:
                cur = conn.cursor()
                
                # Check if email already exists
                if user_type == 'customer':
                    cur.execute('SELECT * FROM customers WHERE email_address = %s', (email,))
                else:  # seller
                    cur.execute('SELECT * FROM sellers WHERE email = %s', (email,))
                
                if cur.fetchone():
                    flash('Email already exists. Please use a different email.', 'error')
                    return redirect(url_for('signup', user_type=user_type))
                
                # Insert new user
                if user_type == 'customer':
                    phone = request.form['phone']
                    address = request.form['address']
                    cur.execute('INSERT INTO customers (name, email_address, password, phone_number, address) VALUES (%s, %s, %s, %s, %s)',
                              (name, email, password, phone, address))
                else:  # seller
                    cur.execute('INSERT INTO sellers (seller_name, email, password) VALUES (%s, %s, %s)',
                              (name, email, password))
                
                conn.commit()
                flash('Account created successfully! Please login.', 'success')
                return redirect(url_for('login'))
            except mysql.connector.Error as e:
                print(f"Error: {e}")
                flash('Error creating account', 'error')
            finally:
                cur.close()
                conn.close()
    
    return render_template('signup.html', user_type=user_type)

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor(dictionary=True)
            
            # Get counts
            cur.execute('SELECT COUNT(*) as count FROM customers')
            customer_count = cur.fetchone()['count']
            
            cur.execute('SELECT COUNT(*) as count FROM sellers')
            seller_count = cur.fetchone()['count']
            
            cur.execute('SELECT COUNT(*) as count FROM products')
            product_count = cur.fetchone()['count']
            
            cur.execute('SELECT COUNT(*) as count FROM orders')
            order_count = cur.fetchone()['count']
            
            # Get recent orders with customer names
            cur.execute('''
                SELECT o.*, c.name as customer_name
                FROM orders o
                JOIN customers c ON o.customer_id = c.customer_id
                ORDER BY o.order_date DESC
                LIMIT 5
            ''')
            recent_orders = cur.fetchall()
            
            cur.close()
            conn.close()
            
            return render_template('admin_dashboard.html',
                                 customer_count=customer_count,
                                 seller_count=seller_count,
                                 product_count=product_count,
                                 order_count=order_count,
                                 recent_orders=recent_orders)
        except mysql.connector.Error as e:
            print(f"Error: {e}")
            flash('Error loading dashboard', 'error')
    return redirect(url_for('index'))

@app.route('/admin/view_order/<int:order_id>')
@admin_required
def view_order(order_id):
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor(dictionary=True)
            
            # Get order details with customer info
            cur.execute('''
                SELECT o.*, c.name as customer_name, c.email_address, c.phone_number, c.address
                FROM orders o
                JOIN customers c ON o.customer_id = c.customer_id
                WHERE o.order_id = %s
            ''', (order_id,))
            order = cur.fetchone()
            
            if order:
                # Get order items
                cur.execute('''
                    SELECT od.*, p.name as product_name
                    FROM order_details od
                    JOIN products p ON od.product_id = p.product_id
                    WHERE od.order_id = %s
                ''', (order_id,))
                order_items = cur.fetchall()
                
                cur.close()
                conn.close()
                return render_template('view_order.html', order=order, items=order_items)
            
            flash('Order not found', 'error')
        except mysql.connector.Error as e:
            print(f"Error: {e}")
            flash('Error loading order details', 'error')
    return redirect(url_for('manage_orders'))

@app.route('/admin/customers')
@admin_required
def customers():
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute('SELECT * FROM customers')
            customers = cur.fetchall()
            cur.close()
            conn.close()
            return render_template('customers.html', customers=customers)
        except mysql.connector.Error as e:
            print(f"Error: {e}")
            flash('Error loading customers', 'error')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/sellers')
@admin_required
def sellers():
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute('SELECT * FROM sellers')
            sellers = cur.fetchall()
            cur.close()
            conn.close()
            return render_template('sellers.html', sellers=sellers)
        except mysql.connector.Error as e:
            print(f"Error: {e}")
            flash('Error loading sellers', 'error')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/products')
@admin_required
def products():
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute('SELECT * FROM products')
            products = cur.fetchall()
            cur.close()
            conn.close()
            return render_template('products.html', products=products)
        except mysql.connector.Error as e:
            print(f"Error: {e}")
            flash('Error loading products', 'error')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/add_employee', methods=['GET', 'POST'])
@admin_required
def add_employee():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        phone = request.form['phone']
        address = request.form['address']
        position = request.form['position']
        is_admin = 'is_admin' in request.form
        
        conn = get_db_connection()
        if conn:
            try:
                cur = conn.cursor()
                # Check if email already exists
                cur.execute('SELECT * FROM employees WHERE email = %s', (email,))
                if cur.fetchone():
                    flash('Email already exists', 'error')
                    return redirect(url_for('add_employee'))
                
                # Insert new employee
                cur.execute('''
                    INSERT INTO employees (name, email, password, phone, address, position, is_admin)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                ''', (name, email, password, phone, address, position, is_admin))
                
                conn.commit()
                cur.close()
                conn.close()
                flash('Employee added successfully', 'success')
                return redirect(url_for('admin_dashboard'))
            except mysql.connector.Error as e:
                print(f"Error: {e}")
                flash('Error adding employee', 'error')
    
    return render_template('add_employee.html')

@app.route('/admin/manage_orders')
@admin_required
def manage_orders():
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute('SELECT * FROM orders ORDER BY order_date DESC')
            orders = cur.fetchall()
            cur.close()
            conn.close()
            return render_template('manage_orders.html', orders=orders)
        except mysql.connector.Error as e:
            print(f"Error: {e}")
            flash('Error loading orders', 'error')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/sales_report')
@admin_required
def sales_report():
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute('''
                SELECT DATE(order_date) as date, COUNT(*) as total_orders, 
                       SUM(total_amount) as total_sales
                FROM orders
                GROUP BY DATE(order_date)
                ORDER BY date DESC
            ''')
            sales_data = cur.fetchall()
            cur.close()
            conn.close()
            return render_template('sales_report.html', sales_data=sales_data)
        except mysql.connector.Error as e:
            print(f"Error: {e}")
            flash('Error loading sales report', 'error')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/inventory_report')
@admin_required
def inventory_report():
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute('''
                SELECT p.*, s.seller_name
                FROM products p
                JOIN sellers s ON p.seller_id = s.seller_id
                ORDER BY p.quantity ASC
            ''')
            inventory = cur.fetchall()
            cur.close()
            conn.close()
            return render_template('inventory_report.html', inventory=inventory)
        except mysql.connector.Error as e:
            print(f"Error: {e}")
            flash('Error loading inventory report', 'error')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/remove_seller/<int:seller_id>', methods=['POST'])
@admin_required
def remove_seller(seller_id):
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            # First delete all products associated with the seller
            cur.execute('DELETE FROM products WHERE seller_id = %s', (seller_id,))
            # Then delete the seller
            cur.execute('DELETE FROM sellers WHERE seller_id = %s', (seller_id,))
            conn.commit()
            cur.close()
            conn.close()
            flash('Seller and associated products removed successfully', 'success')
        except mysql.connector.Error as e:
            print(f"Error: {e}")
            flash('Error removing seller', 'error')
    return redirect(url_for('sellers'))

@app.route('/seller/dashboard')
@login_required
def seller_dashboard():
    if session.get('user_type') != 'seller':
        flash('Seller access required', 'error')
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute('SELECT * FROM products WHERE seller_id = %s', (session['user_id'],))
            products = cur.fetchall()
            
            cur.execute('''
                SELECT o.order_id, o.order_date, o.status, o.total_amount,
                       od.quantity, p.name
                FROM orders o
                JOIN order_details od ON o.order_id = od.order_id
                JOIN products p ON od.product_id = p.product_id
                WHERE p.seller_id = %s
                ORDER BY o.order_date DESC
            ''', (session['user_id'],))
            orders = cur.fetchall()
            
            cur.close()
            conn.close()
            
            return render_template('seller_dashboard.html',
                                 products=products,
                                 orders=orders)
        except mysql.connector.Error as e:
            print(f"Error: {e}")
            flash('Error loading dashboard', 'error')
    
    return redirect(url_for('index'))

@app.route('/add_to_cart', methods=['POST'])
@login_required
def add_to_cart():
    if session.get('user_type') != 'customer':
        return jsonify({'success': False, 'message': 'Customer access required'})
    
    if 'cart' not in session:
        session['cart'] = {}
    
    product_id = request.form.get('product_id')
    quantity = int(request.form.get('quantity', 1))
    
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute('SELECT quantity FROM products WHERE product_id = %s', (product_id,))
            available = cur.fetchone()
            
            if available and available[0] >= quantity:
                if product_id in session['cart']:
                    session['cart'][product_id] += quantity
                else:
                    session['cart'][product_id] = quantity
                
                session.modified = True
                flash('Product added to cart', 'success')
            else:
                flash('Not enough stock available', 'error')
            
            cur.close()
            conn.close()
        except mysql.connector.Error as e:
            print(f"Error: {e}")
            flash('Error adding to cart', 'error')
    
    return redirect(url_for('index'))

@app.route('/cart')
@login_required
def view_cart():
    if 'cart' not in session:
        session['cart'] = {}
    
    cart_items = []
    total = 0
    
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor(dictionary=True)  # Use dictionary cursor
            
            for product_id, quantity in session['cart'].items():
                cur.execute('SELECT * FROM products WHERE product_id = %s', (product_id,))
                product = cur.fetchone()
                
                if product:
                    item_total = product['price'] * quantity
                    cart_items.append({
                        'product': product,
                        'quantity': quantity,
                        'total': item_total
                    })
                    total += item_total
            
            cur.close()
            conn.close()
        except mysql.connector.Error as e:
            print(f"Error: {e}")
            flash('Error loading cart', 'error')
    
    return render_template('cart.html', cart_items=cart_items, total=total)

@app.route('/checkout', methods=['POST'])
@login_required
def checkout():
    if 'cart' not in session or not session['cart']:
        flash('Your cart is empty', 'error')
        return redirect(url_for('view_cart'))
    
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor(dictionary=True)  # Use dictionary cursor
            
            # Create order
            cur.execute('''
                INSERT INTO orders (customer_id, total_amount)
                VALUES (%s, 0)
            ''', (session['user_id'],))
            order_id = cur.lastrowid
            
            total_amount = 0
            
            # Add order details
            for product_id, quantity in session['cart'].items():
                cur.execute('SELECT price FROM products WHERE product_id = %s', (product_id,))
                product = cur.fetchone()
                price = product['price']
                
                cur.execute('''
                    INSERT INTO order_details (order_id, product_id, quantity, price_at_time)
                    VALUES (%s, %s, %s, %s)
                ''', (order_id, product_id, quantity, price))
                
                total_amount += price * quantity
                
                # Update product quantity
                cur.execute('''
                    UPDATE products
                    SET quantity = quantity - %s
                    WHERE product_id = %s
                ''', (quantity, product_id))
            
            # Update order total
            cur.execute('''
                UPDATE orders
                SET total_amount = %s
                WHERE order_id = %s
            ''', (total_amount, order_id))
            
            conn.commit()
            session['cart'] = {}
            flash('Order placed successfully!', 'success')
        except mysql.connector.Error as e:
            conn.rollback()
            print(f"Error: {e}")
            flash('Error processing order', 'error')
        finally:
            cur.close()
            conn.close()
    
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

@app.route('/admin/view_product/<int:product_id>')
@admin_required
def view_product(product_id):
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute('''
                SELECT p.*, s.seller_name 
                FROM products p
                JOIN sellers s ON p.seller_id = s.seller_id
                WHERE p.product_id = %s
            ''', (product_id,))
            product = cur.fetchone()
            cur.close()
            conn.close()
            if product:
                return render_template('view_product.html', product=product)
            flash('Product not found', 'error')
        except mysql.connector.Error as e:
            print(f"Error: {e}")
            flash('Error loading product', 'error')
    return redirect(url_for('products'))

@app.route('/admin/delete_product/<int:product_id>', methods=['POST'])
@admin_required
def delete_product(product_id):
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute('DELETE FROM products WHERE product_id = %s', (product_id,))
            conn.commit()
            cur.close()
            conn.close()
            flash('Product deleted successfully', 'success')
        except mysql.connector.Error as e:
            print(f"Error: {e}")
            flash('Error deleting product', 'error')
    return redirect(url_for('products'))

@app.route('/admin/view_customer/<int:customer_id>')
@admin_required
def view_customer(customer_id):
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute('SELECT * FROM customers WHERE customer_id = %s', (customer_id,))
            customer = cur.fetchone()
            
            if customer:
                # Get customer's orders
                cur.execute('''
                    SELECT * FROM orders 
                    WHERE customer_id = %s 
                    ORDER BY order_date DESC
                ''', (customer_id,))
                orders = cur.fetchall()
                
                cur.close()
                conn.close()
                return render_template('view_customer.html', customer=customer, orders=orders)
            flash('Customer not found', 'error')
        except mysql.connector.Error as e:
            print(f"Error: {e}")
            flash('Error loading customer', 'error')
    return redirect(url_for('customers'))

@app.route('/admin/edit_customer/<int:customer_id>', methods=['GET', 'POST'])
@admin_required
def edit_customer(customer_id):
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        address = request.form['address']
        
        conn = get_db_connection()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute('''
                    UPDATE customers 
                    SET name = %s, email_address = %s, phone_number = %s, address = %s
                    WHERE customer_id = %s
                ''', (name, email, phone, address, customer_id))
                conn.commit()
                cur.close()
                conn.close()
                flash('Customer updated successfully', 'success')
                return redirect(url_for('customers'))
            except mysql.connector.Error as e:
                print(f"Error: {e}")
                flash('Error updating customer', 'error')
    
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute('SELECT * FROM customers WHERE customer_id = %s', (customer_id,))
            customer = cur.fetchone()
            cur.close()
            conn.close()
            if customer:
                return render_template('edit_customer.html', customer=customer)
            flash('Customer not found', 'error')
        except mysql.connector.Error as e:
            print(f"Error: {e}")
            flash('Error loading customer', 'error')
    return redirect(url_for('customers'))

@app.route('/admin/delete_customer/<int:customer_id>', methods=['POST'])
@admin_required
def delete_customer(customer_id):
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            # First delete all orders for this customer
            cur.execute('DELETE FROM orders WHERE customer_id = %s', (customer_id,))
            # Then delete the customer
            cur.execute('DELETE FROM customers WHERE customer_id = %s', (customer_id,))
            conn.commit()
            cur.close()
            conn.close()
            flash('Customer deleted successfully', 'success')
        except mysql.connector.Error as e:
            print(f"Error: {e}")
            flash('Error deleting customer', 'error')
    return redirect(url_for('customers'))

@app.route('/seller/add_product', methods=['GET', 'POST'])
@login_required
def add_product():
    if session.get('user_type') != 'seller':
        flash('Seller access required', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = float(request.form['price'])
        quantity = int(request.form['quantity'])
        seller_id = session['user_id']
        
        conn = get_db_connection()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute('''
                    INSERT INTO products (name, description, price, quantity, seller_id)
                    VALUES (%s, %s, %s, %s, %s)
                ''', (name, description, price, quantity, seller_id))
                conn.commit()
                cur.close()
                conn.close()
                flash('Product added successfully', 'success')
                return redirect(url_for('seller_dashboard'))
            except mysql.connector.Error as e:
                print(f"Error: {e}")
                flash('Error adding product', 'error')
    
    return render_template('add_product.html')

@app.route('/seller/delete_product/<int:product_id>', methods=['POST'])
@login_required
def seller_delete_product(product_id):
    if session.get('user_type') != 'seller':
        flash('Seller access required', 'error')
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            # Verify that the product belongs to this seller
            cur.execute('SELECT seller_id FROM products WHERE product_id = %s', (product_id,))
            product = cur.fetchone()
            
            if product and product[0] == session['user_id']:
                cur.execute('DELETE FROM products WHERE product_id = %s', (product_id,))
                conn.commit()
                flash('Product deleted successfully', 'success')
            else:
                flash('Product not found or access denied', 'error')
            
            cur.close()
            conn.close()
        except mysql.connector.Error as e:
            print(f"Error: {e}")
            flash('Error deleting product', 'error')
    
    return redirect(url_for('seller_dashboard'))

@app.route('/remove_from_cart/<product_id>', methods=['POST'])
@login_required
def remove_from_cart(product_id):
    if session.get('user_type') != 'customer':
        flash('Customer access required', 'error')
        return redirect(url_for('index'))
    
    if 'cart' in session and product_id in session['cart']:
        del session['cart'][product_id]
        session.modified = True
        flash('Item removed from cart', 'success')
    
    return redirect(url_for('view_cart'))

if __name__ == '__main__':
    app.run(debug=True) 