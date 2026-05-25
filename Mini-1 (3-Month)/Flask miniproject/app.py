import os
import qrcode
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecretkey_traffic_logger'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///traffic.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Models
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)

class Violation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vehicle_number = db.Column(db.String(20), nullable=False)
    violation_type = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    fine_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Unpaid')
    qr_code_path = db.Column(db.String(200), nullable=True)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def generate_qr_code(violation_id):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    url = f"http://127.0.0.1:5000/status/{violation_id}"
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    
    if not os.path.exists('static/qrcodes'):
        os.makedirs('static/qrcodes')
        
    filename = f"qr_{violation_id}.png"
    filepath = os.path.join('static/qrcodes', filename)
    img.save(filepath)
    return f"qrcodes/{filename}"

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/add_violation', methods=['GET', 'POST'])
@login_required
def add_violation():
    if request.method == 'POST':
        vehicle_number = request.form.get('vehicle_number')
        violation_type = request.form.get('violation_type')
        location = request.form.get('location')
        date_str = request.form.get('date')
        
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            date_obj = datetime.utcnow()
            
        fine_amount = request.form.get('fine_amount')
        
        if not vehicle_number or not violation_type or not location or not fine_amount:
            flash('Please fill in all fields', 'warning')
            return redirect(url_for('add_violation'))
            
        new_violation = Violation(
            vehicle_number=vehicle_number,
            violation_type=violation_type,
            location=location,
            date=date_obj,
            fine_amount=float(fine_amount)
        )
        db.session.add(new_violation)
        db.session.commit()
        
        # Once added, generate QR
        qr_path = generate_qr_code(new_violation.id)
        new_violation.qr_code_path = qr_path
        db.session.commit()
        
        flash('Violation recorded successfully!', 'success')
        return redirect(url_for('history'))
        
    return render_template('add_violation.html')

@app.route('/history', methods=['GET'])
@login_required
def history():
    search_query = request.args.get('search')
    status_filter = request.args.get('status')
    
    query = Violation.query
    
    if search_query:
        query = query.filter(Violation.vehicle_number.ilike(f'%{search_query}%'))
    if status_filter and status_filter != 'All':
        query = query.filter(Violation.status == status_filter)
        
    violations = query.order_by(Violation.date.desc()).all()
    return render_template('history.html', violations=violations)

@app.route('/update_status/<int:violation_id>', methods=['POST'])
@login_required
def update_status(violation_id):
    violation = Violation.query.get_or_404(violation_id)
    if violation.status == 'Unpaid':
        violation.status = 'Paid'
        db.session.commit()
        flash('Violation status updated to Paid!', 'success')
    return redirect(url_for('history'))

@app.route('/status/<int:violation_id>')
def status(violation_id):
    violation = Violation.query.get_or_404(violation_id)
    return render_template('status.html', violation=violation)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Create default admin user
        if not User.query.filter_by(username='Artheesh').first():
            hashed_password = bcrypt.generate_password_hash('Artheesh123').decode('utf-8')
            admin_user = User(username='Artheesh', password=hashed_password)
            db.session.add(admin_user)
            db.session.commit()
    app.run(debug=True, port=5000)
