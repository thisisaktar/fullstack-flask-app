
from email.mime.text import MIMEText
from functools import wraps
from flask import session, redirect
import os
import psycopg2
from psycopg2.extras import RealDictCursor


def send_otp_email(email, otp):
    print(f"OTP for {email}: {otp}")

def get_db_connection():
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    return conn


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect('/')
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or not session.get('is_admin'):
            return "Access denied", 403
        return f(*args, **kwargs)
    return decorated_function