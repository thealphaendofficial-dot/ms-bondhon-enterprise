import os
import random
import smtplib
from datetime import timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from flask import Flask, redirect, render_template, request, session, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'bondhon_enterprise_kuolaura_juri_fresh_start_key'

# সেশন পার্মানেন্ট এবং ৩০ দিনের জন্য লগইন ধরে রাখার কনফিগারেশন
app.permanent_session_lifetime = timedelta(days=30)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bondhon_house_v4.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
db = SQLAlchemy(app)

class TeamUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    mobile = db.Column(db.String(15), nullable=False)
    profile_pic = db.Column(db.String(200), default='default.png')
    role = db.Column(db.String(20), nullable=False)

class FocusGrid(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    union_name = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    lat = db.Column(db.String(20), nullable=False)
    lng = db.Column(db.String(20), nullable=False)
    is_locked = db.Column(db.Boolean, default=False)
    locked_by_name = db.Column(db.String(100), nullable=True)
    locked_by_email = db.Column(db.String(100), nullable=True)
    locked_by_phone = db.Column(db.String(20), nullable=True)
    locked_by_img = db.Column(db.String(200), nullable=True)
    user_designation = db.Column(db.String(20), nullable=True)

# --- জিমেইল ওটিপি কনফিগারেশন ---
SENDER_EMAIL = "thealphaendofficial@gmail.com"  # আপনার জিমেইল দিন
SENDER_PASSWORD = "gpoq cwzp ropr tkon"  # গুগলের দেওয়া সেই ১৬ অক্ষরের অ্যাপ পাসওয়ার্ড দিন
MANAGEMENT_PASSWORD = "admin123" 

def send_otp_email(receiver_email, otp):
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = receiver_email
    msg['Subject'] = "MS Bondhon Enterprise - Verification Code"
    body = f"আপনার লগইন ওটিপি কোডটি হলো: {otp}\n\nএটি দিয়ে ড্যাশবোর্ডে লগইন করুন।"
    msg.attach(MIMEText(body, 'plain'))
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, receiver_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Email Error: {e}")
        return False

@app.route('/', methods=['GET', 'POST'])
def login():
    if session.get('logged_in'):
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        email = request.form['email']
        user = TeamUser.query.filter_by(email=email).first()
        if not user:
            return "<h3>এই জিমেইলটি নিবন্ধিত নয়। দয়া করে আগে রেজিস্টার করুন। <a href='/register'>রেজিস্ট্রেশন পেজ</a></h3>"
        
        otp = str(random.randint(100000, 999999))
        session['temp_email'] = user.email
        session['temp_otp'] = otp
        session['temp_role'] = user.role
        session['temp_name'] = user.name
        session['temp_mobile'] = user.mobile
        session['temp_profile_pic'] = user.profile_pic
        
        if send_otp_email(email, otp):
            return render_template('login.html', step='verify')
        return "<h3>ওটিপি পাঠানো যায়নি। জিমেইল কনফিগারেশন বা অ্যাপ পাসওয়ার্ড চেক করুন।</h3>"
    return render_template('login.html', step='login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        mobile = request.form['mobile']
        email = request.form['email']
        role = request.form['user_role']
        
        file = request.files.get('profile_pic')
        filename = 'default.png'
        if file and file.filename != '':
            filename = secure_filename(f"{mobile}_{file.filename}")
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            
        existing_user = TeamUser.query.filter_by(email=email).first()
        if existing_user:
            return "<h3>এই জিমেইল দিয়ে অলরেডি অ্যাকাউন্ট আছে! <a href='/'>লগইন করুন</a></h3>"
            
        new_user = TeamUser(email=email, name=name, mobile=mobile, profile_pic=filename, role=role)
        db.session.add(new_user)
        db.session.commit()
        
        otp = str(random.randint(100000, 999999))
        session['temp_email'] = email
        session['temp_otp'] = otp
        session['temp_role'] = role
        session['temp_name'] = name
        session['temp_mobile'] = mobile
        session['temp_profile_pic'] = filename
        
        if send_otp_email(email, otp):
            return render_template('login.html', step='verify')
        return "<h3>ইউজার নিবন্ধিত হয়েছে কিন্তু ওটিপি যায়নি। আপনার জিমেইল সেটিংস চেক করুন।</h3>"
    return render_template('login.html', step='register')

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if session.get('logged_in'):
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        password = request.form['password']
        role = request.form['user_role'] 
        if password == MANAGEMENT_PASSWORD:
            session.permanent = True  # লগইন আজীবনের জন্য ধরে রাখবে (যতক্ষণ না লগআউট করবে)
            session['email'] = f"{role} Panel"
            session['role'] = role
            session['name'] = role
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
        return "<h3>ভুল পাসওয়ার্ড! <a href='/admin_login'>আবার চেষ্টা করুন</a></h3>"
    return render_template('login.html', step='admin')

@app.route('/verify', methods=['GET', 'POST'])
def verify():
    if 'temp_otp' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        user_otp = request.form['otp']
        if user_otp == session['temp_otp']:
            session.permanent = True  # লগইন সেশন স্থায়ী করা হলো
            session['email'] = session['temp_email']
            session['role'] = session['temp_role']
            session['name'] = session['temp_name']
            session['mobile'] = session['temp_mobile']
            session['profile_pic'] = session['temp_profile_pic']
            session['logged_in'] = True
            
            # টেম্পোরারি সেশন ডেটা ডিলিট
            session.pop('temp_otp', None)
            return redirect(url_for('dashboard'))
        return "<h3>ভুল OTP! <a href='/'>পুনরায় চেষ্টা করুন</a></h3>"

@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    grids = FocusGrid.query.all()
    grouped_grids = {}
    for grid in grids:
        if grid.union_name not in grouped_grids:
            grouped_grids[grid.union_name] = []
        grouped_grids[grid.union_name].append(grid)
        
    return render_template('dashboard.html', grouped_grids=grouped_grids)

@app.route('/lock_grid/<int:grid_id>', methods=['POST'])
def lock_grid(grid_id):
    if not session.get('logged_in') or session.get('role') not in ['DSO', 'DSR']:
        return redirect(url_for('login'))
    
    grid = FocusGrid.query.get(grid_id)
    if grid and not grid.is_locked:
        grid.is_locked = True
        grid.locked_by_name = session.get('name')
        grid.locked_by_email = session.get('email')
        grid.locked_by_phone = session.get('mobile')
        grid.locked_by_img = session.get('profile_pic')
        grid.user_designation = session.get('role') 
        db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/release_grid/<int:grid_id>', methods=['POST'])
def release_grid(grid_id):
    if not session.get('logged_in') or session.get('role') not in ['DSO', 'DSR']:
        return redirect(url_for('login'))
    grid = FocusGrid.query.get(grid_id)
    if grid and grid.locked_by_email == session['email']:
        grid.is_locked = False
        grid.locked_by_name = None
        grid.locked_by_email = None
        grid.locked_by_phone = None
        grid.locked_by_img = None
        grid.user_designation = None
        db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

def seed_grids():
    if FocusGrid.query.count() == 0:
        raw_data = {
            "Kulaura": [("ফোকাস গ্রিড ১", "24.4960360", "92.0208120"), ("ফোকাস গ্রিড ২", "24.5016400", "92.0272444"), ("ফোকাস গ্রিড ৩", "24.4680977", "92.0311658"), ("ফোকাস গ্রিড ৪", "24.5009600", "92.0557400")],
            "Kulaura Paurashava": [("ফোকাস গ্রিড ১", "24.5066320", "92.0388870")],
            "Purba Juri": [("ফোকাস গ্রিড ১", "24.5775200", "92.1595100"), ("ফোকাস গ্রিড ২", "24.6020900", "92.1806300"), ("ফোকাস গ্রিড ৩", "24.5701980", "92.1747190"), ("ফোকাস গ্রিড ৪", "24.6111000", "92.1855600")],
            "Paschim Juri": [("ফোকাস গ্রিড ১", "24.6065800", "92.1313800")],
            "Sagarnal": [("ফোকাস গ্রিড ১", "24.5693436", "92.1175063"), ("ফোকাস গ্রিড ২", "24.4770800", "92.1357200"), ("ফোকাস গ্রিড ৩", "24.5612400", "92.1452700"), ("ফোকাস গ্রিড ৪", "24.4767200", "92.1403590")],
            "Fultala": [("ফোকাস গ্রিড ১", "24.4510830", "92.1525280"), ("ফোকাস গ্রিড ২", "24.4460000", "92.1561500")],
            "Goalbari": [("ফোকাস গ্রিড ১", "24.5661800", "92.1479000"), ("ফোকাস গ্রিড ২", "24.5300300", "92.2025500")],
            "Karmadha": [("ফোকাস গ্রিড ১", "24.4372701", "92.0217259"), ("ফোকাস গ্রিড ২", "24.3968212", "92.0259192"), ("ফোকাস গ্রিড ৩", "24.4590300", "92.0379800")],
            "Kadirpur": [("ফোকাস গ্রিড ১", "24.5184900", "92.0001070"), ("ফোকাস গ্রিড ২", "24.5117300", "92.0004600"), ("ফোকাস গ্রিড ৩", "24.5065222", "92.0230639")],
            "Joychandi": [("ফোকাস গ্রিড ১", "24.5276480", "92.0674080")],
            "Hajipur": [("ফোকাস গ্রিড ১", "24.4326570", "91.9349610"), ("ফোকাস গ্রিড ২", "24.4086000", "91.9406400")],
            "Brahman Bazar": [("ফোকাস গ্রিড ১", "24.5300400", "91.9636630"), ("ফোকাস গ্রিড ২", "24.5523477", "91.9814124")],
            "Bhukshimail": [("ফোকাস গ্রিড ১", "24.5548511", "92.0208136"), ("ফোকাস গ্রিড ২", "24.5602700", "92.0173600"), ("ফোকাস গ্রিড ৩", "24.5936820", "92.0284240"), ("ফোকাস গ্রিড ৪", "24.6006167", "92.0255482"), ("ফোকাস গ্রিড ৫", "24.5690283", "92.0516481"), ("ফোকাস গ্রিড６", "24.5599200", "92.0495300")],
            "Bhatera": [("ফোকাস গ্রিড ১", "24.6107700", "91.9863400"), ("ফোকাস গ্রিড ২", "24.6269100", "91.9820100"), ("ফোকাস গ্রিড ৩", "24.6302500", "91.9898330")],
            "Baramchal": [("ফোকাস গ্রিড ১", "24.5734200", "91.9773400")],
            "Prithim Pasha": [("ফোকাস গ্রিড ১", "24.4173580", "92.0195610")],
            "Sharifpur": [("ফোকাস গ্রিড ১", "24.3873900", "91.9556200")]
        }
        for u_name, grids in raw_data.items():
            for g_name, lat, lng in grids:
                db.session.add(FocusGrid(union_name=u_name, name=g_name, lat=lat, lng=lng))
        db.session.commit()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        seed_grids()
    app.run(debug=True, port=8080)

