from flask import Blueprint, render_template, request, session, redirect



from .utils import get_db_connection
from .utils import login_required, admin_required


admin_bp = Blueprint("admin", __name__)

@admin_bp.route('/admin')
@login_required
@admin_required
def admin_dashboard():

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Total Users
    cursor.execute("SELECT COUNT(*) AS total_users FROM users")
    total_users = cursor.fetchone()['total_users']

    # Total Slots
    cursor.execute("SELECT COUNT(*) AS total_slots FROM slots")
    total_slots = cursor.fetchone()['total_slots']

    # Total Bookings
    cursor.execute("SELECT COUNT(*) AS total_bookings FROM bookings")
    total_bookings = cursor.fetchone()['total_bookings']

    # Available Slots
    cursor.execute("SELECT COUNT(*) AS available_slots FROM slots WHERE is_booked = FALSE")
    available_slots = cursor.fetchone()['available_slots']

    # Get all slots for listing
    cursor.execute("SELECT * FROM slots")
    slots = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "admin.html",
        total_users=total_users,
        total_slots=total_slots,
        total_bookings=total_bookings,
        available_slots=available_slots,
        slots=slots
    )

@admin_bp.route('/admin/add-slot', methods=['POST'])
@login_required
@admin_required
def add_slot():

    csrf_token = request.form.get('csrf_token')
    if csrf_token != session.get('_csrf_token'):
        return "CSRF validation failed", 403

    slot_time = request.form.get('slot_time')

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO slots (slot_time, is_booked) VALUES (%s, FALSE)",
        (slot_time,)
    )

    conn.commit()
    cursor.close()
    conn.close()

    return redirect('/admin')




@admin_bp.route('/admin/delete-slot', methods=['POST'])
@login_required
@admin_required
def delete_slot():

    slot_id = request.form.get('slot_id')
    csrf_token = request.form.get('csrf_token')

    if csrf_token != session.get('_csrf_token'):
        return "CSRF validation failed", 403

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM bookings WHERE slot_id = %s", (slot_id,))
    cursor.execute("DELETE FROM slots WHERE id = %s", (slot_id,))

    conn.commit()
    cursor.close()
    conn.close()

    return redirect('/admin')





@admin_bp.route('/admin/bookings')
@login_required
@admin_required
def admin_bookings():

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT 
            users.name,
            users.email,
            slots.slot_time
        FROM bookings
        JOIN users ON bookings.user_id = users.id
        JOIN slots ON bookings.slot_id = slots.id
        ORDER BY slots.slot_time
    """)

    bookings = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("admin_bookings.html", bookings=bookings)


