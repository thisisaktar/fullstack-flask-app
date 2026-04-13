from flask import Blueprint, render_template, request, session, redirect
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import random
from psycopg2.extras import RealDictCursor
from .utils import send_otp_email, get_db_connection


auth_bp = Blueprint("auth", __name__)


@auth_bp.route('/login')
def login_page():
    if 'user_id' in session:
        return redirect('/dashboard')
    return render_template("login.html")


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if not user:
        return {"success": False, "message": "Invalid email or password"}, 401

    if not user['is_verified']:
        return {"success": False, "message": "Please verify your email first."}, 403

    if not check_password_hash(user['password'], password):
        return {"success": False, "message": "Invalid email or password"}, 401

    session.permanent = True
    session['user_id'] = user['id']
    session['is_admin'] = user['is_admin']

    if user['is_admin']:
        return {"success": True, "redirect": "/admin"}
    else:
        return {"success": True, "redirect": "/dashboard"}


@auth_bp.route('/signup', methods=['GET'])
def signup_page():
    if 'user_id' in session:
        return redirect('/dashboard')
    return render_template("signup.html")


@auth_bp.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')

    if not name or not email or not password:
        return {"success": False, "message": "All fields are required."}, 400

    hashed_password = generate_password_hash(password)

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
    existing_user = cursor.fetchone()
    cursor.close()
    conn.close()

    if existing_user:
        return {"success": False, "message": "Email already registered"}

    # Generate OTP and store signup info in session
    otp = str(random.randint(100000, 999999))
    session['signup_name'] = name
    session['signup_email'] = email
    session['signup_password'] = hashed_password
    session['signup_otp'] = otp
    session['signup_otp_expiry'] = (datetime.now() + timedelta(minutes=5)).isoformat()

    send_otp_email(email, otp)

    return {"success": True, "redirect": "/verify-otp"}


@auth_bp.route('/verify-otp')
def verify_otp_page():
    return render_template("verify_otp.html")


@auth_bp.route('/verify-otp', methods=['POST'])
def verify_otp():
    entered_otp = request.form.get('otp')
    stored_otp = session.get('signup_otp')
    expiry_time = session.get('signup_otp_expiry')

    if not stored_otp or not expiry_time:
        return "Session expired. Please signup again. <a href='/signup'>Go back</a>", 403

    if datetime.now() > datetime.fromisoformat(expiry_time):
        session.pop('signup_otp', None)
        session.pop('signup_otp_expiry', None)
        return "OTP expired. Please signup again. <a href='/signup'>Go back</a>", 403

    if entered_otp != stored_otp:
        return "Invalid OTP. <a href='/verify-otp'>Try again</a>", 403

    name = session.get('signup_name')
    email = session.get('signup_email')
    password = session.get('signup_password')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (name, email, password, is_verified) VALUES (%s, %s, %s, TRUE)",
        (name, email, password)
    )
    conn.commit()
    cursor.close()
    conn.close()

    # Clear signup session data
    for key in ['signup_name', 'signup_email', 'signup_password', 'signup_otp', 'signup_otp_expiry']:
        session.pop(key, None)

    return redirect('/login')


@auth_bp.route('/resend-otp')
def resend_otp():
    email = session.get('signup_email')

    if not email:
        return redirect('/signup')

    otp = str(random.randint(100000, 999999))
    session['signup_otp'] = otp
    session['signup_otp_expiry'] = (datetime.now() + timedelta(minutes=5)).isoformat()

    send_otp_email(email, otp)

    return "New OTP sent to your email. <a href='/verify-otp'>Go back</a>"


@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect('/')