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

    # Check if user already exists
    cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
    existing_user = cursor.fetchone()

    if existing_user:
        cursor.close()
        conn.close()
        return {"success": False, "message": "Email already registered"}

    # Generate OTP
    import random
    otp = str(random.randint(100000, 999999))

    # Insert user WITH OTP (IMPORTANT)
    cursor.execute("""
        INSERT INTO users (name, email, password, otp, is_verified)
        VALUES (%s, %s, %s, %s, FALSE)
    """, (name, email, hashed_password, otp))

    conn.commit()

    cursor.close()
    conn.close()

    # Print OTP instead of email (for now)
    send_otp_email(email, otp)

    # Store email in session ONLY (not OTP)
    session['verify_email'] = email

    return {"success": True, "redirect": "/verify-otp"}


@auth_bp.route('/verify-otp')
def verify_otp_page():
    return render_template("verify_otp.html")


@auth_bp.route('/verify-otp', methods=['POST'])
def verify_otp():
    entered_otp = request.form.get('otp')

    email = session.get('verify_email')

    if not email:
        return "Session expired. Please signup again. <a href='/signup'>Go back</a>", 403

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # Get OTP from DB
    cursor.execute("SELECT otp FROM users WHERE email = %s", (email,))
    result = cursor.fetchone()

    if not result:
        cursor.close()
        conn.close()
        return "User not found", 404

    db_otp = result['otp']

    # Check OTP
    if entered_otp != db_otp:
        cursor.close()
        conn.close()
        return "Invalid OTP. <a href='/verify-otp'>Try again</a>", 403

    # Mark verified
    cursor.execute("""
        UPDATE users 
        SET is_verified = TRUE, otp = NULL 
        WHERE email = %s
    """, (email,))
    conn.commit()

    cursor.close()
    conn.close()

    # Clear session
    session.pop('verify_email', None)

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