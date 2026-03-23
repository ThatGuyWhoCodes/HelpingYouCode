from flask import Flask, render_template, redirect, url_for, request
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import db, User, Product, Order, OrderItem, ProducerProfile

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)

cart = []  # simple cart (easy for exam explanation)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ----------------------
# PUBLIC ROUTES
# ----------------------
@app.route('/')
def index():
    products = Product.query.all()
    return render_template('index.html', products=products)

@app.route('/products')
def products():
    products = Product.query.all()
    return render_template('products.html', products=products)

# ----------------------
# AUTH
# ----------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['email']).first()
        if user and user.password == request.form['password']:
            login_user(user)
            return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')

# ----------------------
# PRODUCER DASHBOARD
# ----------------------
@app.route('/dashboard')
@login_required
def dashboard():
    products = Product.query.filter_by(owner_id=current_user.id).all()
    profile = ProducerProfile.query.filter_by(user_id=current_user.id).first()
    return render_template('dashboard.html', products=products, profile=profile)

@app.route('/add-product', methods=['POST'])
@login_required
def add_product():
    product = Product(
        name=request.form['name'],
        price=float(request.form['price']),
        stock=int(request.form['stock']),
        owner_id=current_user.id
    )
    db.session.add(product)
    db.session.commit()
    return redirect('/dashboard')

@app.route('/update-profile', methods=['POST'])
@login_required
def update_profile():
    profile = ProducerProfile.query.filter_by(user_id=current_user.id).first()
    if not profile:
        profile = ProducerProfile(user_id=current_user.id)

    profile.story = request.form['story']
    profile.methods = request.form['methods']

    db.session.add(profile)
    db.session.commit()
    return redirect('/dashboard')

# ----------------------
# CART + CHECKOUT
# ----------------------
@app.route('/add-to-cart/<int:id>')
def add_to_cart(id):
    cart.append(id)
    return redirect('/products')

@app.route('/cart')
def view_cart():
    items = Product.query.filter(Product.id.in_(cart)).all()
    return render_template('cart.html', items=items)

@app.route('/checkout', methods=['POST'])
@login_required
def checkout():
    delivery = request.form['delivery']
    time = request.form['time']

    items = Product.query.filter(Product.id.in_(cart)).all()
    total = sum(item.price for item in items)

    order = Order(
        user_id=current_user.id,
        total_price=total,
        delivery_type=delivery,
        scheduled_time=time
    )
    db.session.add(order)
    db.session.commit()

    for item in items:
        db.session.add(OrderItem(order_id=order.id, product_id=item.id, quantity=1))

    # Loyalty points
    current_user.loyalty_points += int(total)

    db.session.commit()
    cart.clear()

    return redirect('/')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
