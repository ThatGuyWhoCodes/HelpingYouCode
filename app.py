from flask import Flask, render_template, redirect, url_for, request
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import db, User, Product

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Home (Customer view)
@app.route('/')
def index():
    products = Product.query.all()
    return render_template('index.html', products=products)

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['email']).first()
        if user and user.password == request.form['password']:
            login_user(user)
            return redirect(url_for('dashboard'))
    return render_template('login.html')

# Logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# Producer Dashboard
@app.route('/dashboard')
@login_required
def dashboard():
    products = Product.query.filter_by(owner_id=current_user.id).all()
    return render_template('dashboard.html', products=products)

# Add Product
@app.route('/add-product', methods=['POST'])
@login_required
def add_product():
    product = Product(
        name=request.form['name'],
        price=request.form['price'],
        stock=request.form['stock'],
        owner_id=current_user.id
    )
    db.session.add(product)
    db.session.commit()
    return redirect(url_for('dashboard'))

# Public Products Page
@app.route('/products')
def products():
    products = Product.query.all()
    return render_template('products.html', products=products)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
