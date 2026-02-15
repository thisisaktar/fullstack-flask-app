from flask import Blueprint, render_template, request, session, redirect, flash
from .utils import get_db_connection, login_required


user_bp = Blueprint("user", __name__)



@user_bp.route('/dashboard')
@login_required
def dashboard():
    print("Session user_id:", session.get('user_id'))
    user_id = session['user_id']

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT name, email FROM users WHERE id = %s",
        (user_id,)
    )

    user = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template("dashboard.html", user=user)
   



@user_bp.route('/slots')
@login_required
def get_slots():

    if 'user_id' not in session:
        return redirect('/')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM slots WHERE is_booked = FALSE"
    )

    slots = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("slots.html", slots=slots)






@user_bp.route('/book/<int:slot_id>')
@login_required
def book_slot(slot_id):

    user_id = session['user_id']

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # ✅ Atomic update: book only if free
    cursor.execute("""
        UPDATE slots
        SET is_booked = TRUE
        WHERE id = %s AND is_booked = FALSE
    """, (slot_id,))

    # If no row was updated → slot already booked
    if cursor.rowcount == 0:
        cursor.close()
        conn.close()
        flash("Slot already booked", "error")
        return redirect('/slots')


    # Save booking
    cursor.execute("""
        INSERT INTO bookings (user_id, slot_id)
        VALUES (%s, %s)
    """, (user_id, slot_id))

    conn.commit()
    cursor.close()
    conn.close()

    flash("Slot booked successfully!", "success")
    return redirect('/dashboard')







@user_bp.route('/cancel', methods=['POST'])
@login_required
def cancel_booking():

    slot_id = request.form.get('slot_id')
    csrf_token = request.form.get('csrf_token')

    if csrf_token != session.get('_csrf_token'):
        return "CSRF validation failed", 403

    user_id = session['user_id']

    conn = get_db_connection()
    cursor = conn.cursor()

    # delete booking
    cursor.execute(
        "DELETE FROM bookings WHERE user_id=%s AND slot_id=%s",
        (user_id, slot_id)
    )

    # free slot
    cursor.execute(
        "UPDATE slots SET is_booked=FALSE WHERE id=%s",
        (slot_id,)
    )

    conn.commit()
    cursor.close()
    conn.close()

    return redirect('/my-bookings')





@user_bp.route('/my-bookings')
@login_required
def my_bookings():

    if 'user_id' not in session:
        return redirect('/')

    user_id = session['user_id']

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT slots.id AS slot_id, slots.slot_time
        FROM bookings
        JOIN slots ON bookings.slot_id = slots.id
        WHERE bookings.user_id = %s
    """, (user_id,))


    bookings = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("my_bookings.html", bookings=bookings)

