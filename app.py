from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from pymysql import connections
from werkzeug.security import generate_password_hash, check_password_hash
import openai
import os
openai.api_key = "sk-YtE9o9q2NOjQhiKlguuNBg4S9Ak4P3T36JIFW1R63SVq94Ou"

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# 📌 Database Connection Function
db_conn = connections.Connection(
        host='ecommerce-db.cpq0omwwugu1.ap-south-1.rds.amazonaws.com',
        user='admim',
        password='ecommerce123',
        database='ecommerce-db',


)

# 📌 Home Route - Display Recommended Products
@app.route('/')
def home():
    location = None
    if 'user_id' in session:
        location = request.args.get('location', None)  # Only fetch if user is logged in

    conn = db_conn
    cursor = conn.cursor()


    if location:
        cursor.execute("SELECT * FROM products WHERE location = %s ORDER BY RAND() LIMIT 6", (location,))
    else:
        cursor.execute("SELECT * FROM products ORDER BY RAND() LIMIT 6")  # Default products

    products = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('index.html', products=products, selected_location=location)



# 📌 Signup Page (User Registration)
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        hashed_password = generate_password_hash(password)

        conn = db_conn
        cursor = conn.cursor()


        # Check if email already exists in users table
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        existing_user = cursor.fetchone()

        if existing_user:
            cursor.close()
            conn.close()
            return "Email already registered. Please log in."

        # Insert into users table
        cursor.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)", 
                       (username, email, hashed_password))
        conn.commit()

        cursor.close()
        conn.close()

        return redirect(url_for('login'))  

    return render_template('signup.html')


# 📌 Login Function (Admin & User)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if 'email' not in request.form or 'password' not in request.form:
            return "Missing email or password field", 400  

        email = request.form['email']
        password = request.form['password']

        # ✅ Separate Admin & User Login
        if email == "admin@admin.com" and password == "admin123":
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))  

        conn = db_conn
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user and check_password_hash(user[3], password):  
            session['user_id'] = user[0]
            session['username'] = user[1]
            return redirect(url_for('home'))  # ✅ Redirect to home after login

        return "Invalid credentials. Please try again."

    return render_template('login.html')

# 📌 Logout Function (Clears Admin & User Sessions)
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('admin', None)
    return redirect(url_for('login'))

# 📌 Products Page - Display All Products
@app.route('/products')
def products():
    location = request.args.get('location', 'default')  # Get location from query params
    conn = db_conn
    cursor = conn.cursor()


    if location == 'default':
        cursor.execute("SELECT * FROM products")  # Show all products by default
    else:
        cursor.execute("SELECT * FROM products WHERE location = %s", (location,))

    products = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template('products.html', products=products, selected_location=location)


# 📌 Single Product Page
@app.route('/product/<int:product_id>')
def product(product_id):
    conn = db_conn
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
    product = cursor.fetchone()
    cursor.close()
    conn.close()

    if product:
        return render_template('product.html', product=product)
    return "Product not found", 404

# 📌 Add to Cart
# 📌 Add to Cart (Fixed: No Location Filtering)
@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    if 'user_id' not in session:
        return jsonify({"message": "Please log in to add to cart"}), 401

    user_id = session['user_id']

    conn = db_conn
    cursor = conn.cursor()


    # Check if product exists before adding
    cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
    product = cursor.fetchone()

    if not product:
        cursor.close()
        conn.close()
        return jsonify({"message": "❌ Product not found"}), 400

    # Add product to cart
    cursor.execute("INSERT INTO cart (user_id, product_id) VALUES (%s, %s)", (user_id, product_id))
    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({"message": "✅ Product added to cart successfully"})


@app.route('/chatbot', methods=['POST'])
def chatbot():
    user_message = request.json.get("message")
    
    # Simple rule-based response (Modify as needed)
    responses = {
        "hello": "Hi there! How can I help you?",
        "order status": "You can check your order status in your profile.",
        "refund": "Refunds are processed within 5-7 business days.",
        "default": "I'm not sure about that. Can you rephrase?"
    }
    
    bot_response = responses.get(user_message.lower(), responses["default"])

    # If using AI-based chatbot
    # response = openai.ChatCompletion.create(
    #     model="gpt-4",
    #     messages=[{"role": "user", "content": user_message}]
    # )
    # bot_response = response["choices"][0]["message"]["content"]

    return jsonify({"response": bot_response})



# 📌 Get Cart Count (Live Update)
@app.route('/cart_count')
def cart_count():
    if 'user_id' not in session:
        return jsonify({"count": 0})

    conn = db_conn
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM cart WHERE user_id = %s", (session['user_id'],))
    count = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    return jsonify({"count": count})



# 📌 View Cart
@app.route('/cart')
def cart():
    user_id = session.get("user_id")  # Check if user is logged in
    if not user_id:
        return redirect("/login")
    conn = db_conn
    
    
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT c.id, p.pName, p.price, c.quantity
        FROM cart c
        JOIN products p ON c.product_id = p.id
        WHERE c.user_id = %s
    """, (user_id,))
    
    cart_items = cursor.fetchall()  # ✅ Fetch all cart items
    cursor.close()

    return render_template("cart.html", cart_items=cart_items) 



# 📌 Checkout Page
@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if 'user_id' not in session:
        return redirect(url_for('login'))  # ✅ User must be logged in

    user_id = session['user_id']
    print("DEBUG: User ID in session ->", user_id)  # ✅ Debugging

    conn = db_conn
    cursor = conn.cursor()


    # ✅ Check if user exists
    cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
    existing_user = cursor.fetchone()

    if not existing_user:
        print("ERROR: User ID not found!")  # ✅ Debugging
        cursor.close()
        conn.close()
        return "Error: User ID not found!", 400

    # ✅ Get cart from session (Assuming {product_id: quantity} format)
    cart = session.get('cart', {})

    if not cart:
        return "Your cart is empty!", 400  

    # ✅ Fetch product prices in one query
    product_ids = tuple(cart.keys())  # Get only product IDs
    cursor.execute(f"SELECT id, price FROM products WHERE id IN {product_ids}")
    product_prices = {row[0]: row[1] for row in cursor.fetchall()}

    # ✅ Calculate total price
    total_price = sum(product_prices[pid] * qty for pid, qty in cart.items())

    # ✅ Insert new order into `orders`
    cursor.execute(
        "INSERT INTO orders (user_id, total_price, order_date, status) VALUES (%s, %s, NOW(), 'Pending')",
        (user_id, total_price)
    )
    order_id = cursor.lastrowid  # ✅ Get last inserted order ID

    # ✅ Insert each product into `order_items`
    for product_id, quantity in cart.items():
        cursor.execute(
            "INSERT INTO order_items (order_id, product_id, quantity) VALUES (%s, %s, %s)",
            (order_id, product_id, quantity)
        )

    conn.commit()
    cursor.close()
    conn.close()

    session.pop('cart', None)  # ✅ Clear cart after checkout

    return redirect(url_for('order_confirmation', order_id=order_id))  # ✅ Redirect to confirmation page

@app.route('/order_confirmation/<int:order_id>')
def order_confirmation(order_id):
    return render_template('order_confirmation.html', order_id=order_id)

# 📌 Admin Dashboard
@app.route('/admin')
def admin_dashboard():
    if 'admin' not in session:
        return redirect(url_for('login'))

    conn = db_conn
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()

    cursor.execute("SELECT * FROM orders")
    orders = cursor.fetchall()

    cursor.close()
    conn.close()
    return render_template('admin.html', products=products, orders=orders)

# 📌 Delete Product (Admin)
@app.route('/delete_product/<int:product_id>')
def delete_product(product_id):
    if 'admin' not in session:
        return redirect(url_for('login'))

    conn = db_conn
    cursor = conn.cursor()

    cursor.execute("DELETE FROM products WHERE id = %s", (product_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('admin_dashboard'))

# 📌 Edit Product (Admin)
@app.route('/edit_product/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    conn = db_conn
    cursor = conn.cursor()


    if request.method == 'POST':
        pName = request.form['pName']
        price = request.form['price']
        description = request.form['description']

        cursor.execute("""
            UPDATE products 
            SET pName = %s, price = %s, description = %s 
            WHERE id = %s
        """, (pName, price, description, product_id))
        
        conn.commit()
        cursor.close()
        conn.close()

        return redirect(url_for('products'))  

    cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
    product = cursor.fetchone()
    cursor.close()
    conn.close()

    if not product:
        return "Product not found", 404  

    return render_template('edit_product.html', product=product)

# 📌 Update Order Status (Admin)
@app.route('/update_order_status/<int:order_id>', methods=['GET', 'POST'])
def update_order_status(order_id):
    if 'admin' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        new_status = request.form['status']
        conn = db_conn
        cursor = conn.cursor()

        cursor.execute("UPDATE orders SET status = %s WHERE id = %s", (new_status, order_id))
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('admin_dashboard'))

    return render_template('update_order.html', order_id=order_id)

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = db_conn
    cursor = conn.cursor()


    # ✅ Fetch user details
    cursor.execute("SELECT username, email FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()

    # ✅ Fetch order history
    cursor.execute("""
        SELECT id, status, order_date 
        FROM orders 
        WHERE id = %s
        ORDER BY order_date DESC
    """, (user_id,))
    orders = cursor.fetchall()

    # ✅ Fetch saved addresses
    cursor.execute("""
        SELECT address_line, city, zipcode 
        FROM addresses 
        WHERE user_id = %s
    """, (user_id,))
    addresses = cursor.fetchall()

    # ✅ Fetch wishlist
    cursor.execute("""
        SELECT p.id, p.pName, p.price, p.picture 
        FROM wishlist w
        JOIN products p ON w.product_id = p.id
        WHERE w.user_id = %s
    """, (user_id,))
    wishlist = cursor.fetchall()

    cursor.close()
    conn.close()

    # ✅ Convert fetched data to dictionaries for template rendering
    user_data = {"username": user[0], "email": user[1]} if user else {"username": "Unknown", "email": "Unknown"}

    return render_template('profile.html', user=user_data, orders=orders, addresses=addresses, wishlist=wishlist)



@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = db_conn
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        new_username = request.form['username']
        new_email = request.form['email']

        cursor.execute("UPDATE users SET username = %s, email = %s WHERE id = %s", (new_username, new_email, user_id))
        conn.commit()
        cursor.close()
        conn.close()

        return redirect(url_for('profile'))

    cursor.execute("SELECT username, email FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template('edit_profile.html', user=user)


# 📌 Run Flask App
if __name__ == '__main__':
    app.run(debug=True)
