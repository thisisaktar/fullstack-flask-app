import smtplib
from email.mime.text import MIMEText
import mysql.connector
from functools import wraps
from flask import session, redirect
import os
import psycopg2
from psycopg2.extras import RealDictCursor






def send_otp_email(receiver_email, otp):

    sender_email = os.getenv("MAIL_USER")
    sender_password = os.getenv("MAIL_PASS")

    subject = "Your OTP Verification Code"
    body = f"Your OTP code is: {otp}\n\nIt expires in 5 minutes."

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = receiver_email

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(sender_email, sender_password)
    server.send_message(msg)
    server.quit()



def get_db_connection():
    return psycopg2.connect(
        os.getenv("DATABASE_URL"),
        cursor_factory=RealDictCursor
    )



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


