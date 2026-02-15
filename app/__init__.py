from flask import Flask, session, redirect, render_template
from datetime import timedelta
import secrets
import os
from dotenv import load_dotenv

load_dotenv()




app = Flask(__name__)


app.config.update(
    SESSION_COOKIE_HTTPONLY=True,   
    SESSION_COOKIE_SAMESITE='Lax',   
)

app.secret_key = os.getenv("SECRET_KEY")
app.permanent_session_lifetime = timedelta(minutes=30)


from .auth import auth_bp
app.register_blueprint(auth_bp)

from .utils import get_db_connection


from .admin import admin_bp
app.register_blueprint(admin_bp)


from .user import user_bp
app.register_blueprint(user_bp)




def generate_csrf_token():
    if '_csrf_token' not in session:
        session['_csrf_token'] = secrets.token_hex(16)
    return session['_csrf_token']

app.jinja_env.globals['csrf_token'] = generate_csrf_token




@app.route('/')
def landing():
    if 'user_id' in session:
        return redirect('/dashboard')
    return render_template("landing.html")























