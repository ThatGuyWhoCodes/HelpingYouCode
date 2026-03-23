from flask import Flask, render_template, redirect, url_for, request, session
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Product, Order, OrderItem

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ----------------------
# AUTH (HASHED PASSWORDS)
# ----------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        hashed = generate_password_hash(request.form['password'])
        user = User(
            email=request.form['email'],
            password=hashed,
            role='customer'
        )
        db.session.add(user)
        db.session.commit()
        return redirect('/login')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['email']).first()
        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect('/')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')

# ----------------------
# SESSION CART
# ----------------------
@app.route('/add-to-cart/<int:id>')
def add_to_cart(id):
    cart = session.get('cart', [])
    cart.append(id)
    session['cart'] = cart
    return redirect('/products')

@app.route('/cart')
def cart():
    cart = session.get('cart', [])
    items = Product.query.filter(Product.id.in_(cart)).all()
    return render_template('cart.html', items=items)

# ----------------------
# CHECKOUT + ORDER STATUS
# ----------------------
@app.route('/checkout', methods=['POST'])
@login_required
def checkout():
    cart = session.get('cart', [])
    items = Product.query.filter(Product.id.in_(cart)).all()

    total = sum(i.price for i in items)

    order = Order(
        user_id=current_user.id,
        total_price=total,
        delivery_type=request.form['delivery'],
        scheduled_time=request.form['time'],
        status="Pending"
    )
    db.session.add(order)
    db.session.commit()

    for item in items:
        db.session.add(OrderItem(order_id=order.id, product_id=item.id, quantity=1))

    current_user.loyalty_points += int(total)

    db.session.commit()
    session['cart'] = []

    return redirect('/orders')

# ----------------------
# VIEW ORDERS (TRACKING)
# ----------------------
@app.route('/orders')
@login_required
def orders():
    orders = Order.query.filter_by(user_id=current_user.id).all()
    return render_template('orders.html', orders=orders)

# ----------------------
# ADMIN PANEL
# ----------------------
@app.route('/admin')
@login_required
def admin():
    if current_user.role != 'admin':
        return "Access denied"

    orders = Order.query.all()
    return render_template('admin.html', orders=orders)

@app.route('/update-order/<int:id>')
@login_required
def update_order(id):
    if current_user.role != 'admin':
        return "Access denied"

    order = Order.query.get(id)
    order.status = request.args.get('status')
    db.session.commit()
    return redirect('/admin')

# ----------------------
# PRODUCTS
# ----------------------
@app.route('/')
def index():
    products = Product.query.all()
    return render_template('index.html', products=products)

@app.route('/products')
def products():
    products = Product.query.all()
    return render_template('products.html', products=products)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
