from flask import Flask, request, redirect, session, render_template, flash, jsonify, url_for
from database import create_tables, migrate_tables, connect, ADMIN_SECRET_CODE
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = "secret123"

# Initialize DB
create_tables()
migrate_tables()

# ================= DECORATORS =================
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please login to access this page.", "error")
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session or session.get("role") != "admin":
            flash("Access denied. Admin privileges required.", "error")
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated

# ================= HELPERS =================
def calculate_pricing(price_per_day, days, start_date_str):
    base = price_per_day * days
    surcharge = 0
    try:
        start_dt = datetime.strptime(start_date_str, "%Y-%m-%d")
        if start_dt.weekday() >= 5: # Sat/Sun
            surcharge = base * 0.20
    except (ValueError, TypeError): pass

    discount = 0
    if days > 5: discount = base * 0.10

    subtotal = base + surcharge - discount
    gst = subtotal * 0.18
    total = subtotal + gst

    return {
        "base": round(base, 2),
        "surcharge": round(surcharge, 2),
        "discount": round(discount, 2),
        "gst": round(gst, 2),
        "total": round(total, 2),
    }

# ================= ROUTES =================

@app.route("/")
def home():
    conn = connect()
    cars = conn.execute("SELECT * FROM cars WHERE available=1").fetchall()
    conn.close()
    return render_template("index.html", cars=cars)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        secret_code = request.form.get("secret_code", "").strip()

        if not username or not password:
            flash("Username and password are required.", "error")
            return redirect("/register")

        role = "admin" if secret_code == ADMIN_SECRET_CODE else "user"
        
        conn = connect()
        try:
            hashed_pw = generate_password_hash(password)
            conn.execute(
                "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                (username, hashed_pw, role)
            )
            conn.commit()
            flash(f"Account created as {role}! Please login.", "success")
            return redirect("/login")
        except Exception:
            flash("Username already exists.", "error")
            return redirect("/register")
        finally:
            conn.close()

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        conn = connect()
        user = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        conn.close()

        print(f"DEBUG LOGIN: Attempting '{username}'")
        if user:
            is_match = check_password_hash(user["password"], password)
            print(f"DEBUG LOGIN: User found. PW Match: {is_match}")
        else:
            print(f"DEBUG LOGIN: User '{username}' NOT found.")

        if user and check_password_hash(user["password"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]
            
            flash(f"Welcome back, {username}!", "success")
            if user["role"] == "admin":
                return redirect("/admin")
            return redirect("/")
        else:
            flash("Invalid credentials.", "error")
            return redirect("/login")

    return render_template("login_user.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect("/")

@app.route("/dashboard")
@login_required
def dashboard():
    conn = connect()
    bookings = conn.execute(
        "SELECT * FROM bookings WHERE user=? ORDER BY id DESC",
        (session["username"],)
    ).fetchall()
    conn.close()
    return render_template("dashboard.html", bookings=bookings)

# ================= ADMIN ROUTES =================

@app.route("/admin")
@admin_required
def admin():
    conn = connect()
    cars = conn.execute("SELECT * FROM cars").fetchall()
    bookings = conn.execute("SELECT * FROM bookings ORDER BY id DESC").fetchall()
    users = conn.execute("SELECT id, username, role FROM users ORDER BY id DESC").fetchall()

    revenue = conn.execute("SELECT SUM(total) FROM bookings WHERE status='active'").fetchone()[0] or 0
    total_bookings = conn.execute("SELECT COUNT(*) FROM bookings").fetchone()[0]
    total_cars = conn.execute("SELECT COUNT(*) FROM cars").fetchone()[0]
    total_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]

    most_booked = conn.execute(
        "SELECT car_name, COUNT(*) as cnt FROM bookings GROUP BY car_name ORDER BY cnt DESC LIMIT 1"
    ).fetchone()
    most_booked_name = most_booked["car_name"] if most_booked else "N/A"

    conn.close()
    return render_template(
        "admin.html",
        cars=cars,
        bookings=bookings,
        users=users,
        revenue=round(revenue, 2),
        total_bookings=total_bookings,
        total_cars=total_cars,
        total_users=total_users,
        most_booked=most_booked_name
    )

@app.route("/add_car", methods=["POST"])
@admin_required
def add_car():
    name, price, image_url = request.form.get("name"), request.form.get("price"), request.form.get("image_url")
    if name and price:
        conn = connect()
        conn.execute("INSERT INTO cars (name, price, image_url) VALUES (?, ?, ?)", (name, price, image_url))
        conn.commit()
        conn.close()
        flash("Car added!", "success")
    return redirect("/admin")

@app.route("/delete_car/<int:id>")
@admin_required
def delete_car(id):
    conn = connect()
    conn.execute("DELETE FROM cars WHERE id=?", (id,))
    conn.commit()
    conn.close()
    flash("Car deleted.", "success")
    return redirect("/admin")

@app.route("/delete_user/<int:id>")
@admin_required
def delete_user(id):
    conn = connect()
    user = conn.execute("SELECT username FROM users WHERE id=?", (id,)).fetchone()
    if user:
        conn.execute("DELETE FROM bookings WHERE user=?", (user["username"],))
        conn.execute("DELETE FROM users WHERE id=?", (id,))
        conn.commit()
        flash("User deleted.", "success")
    conn.close()
    return redirect("/admin")

# ================= BOOKING =================

@app.route("/book", methods=["POST"])
@login_required
def book():
    try:
        car_name = request.form.get("car_name")
        days = int(request.form.get("days", 0))
        name, email, phone, payment, start_date = request.form.get("name"), request.form.get("email"), request.form.get("phone"), request.form.get("payment"), request.form.get("start_date")

        conn = connect()
        car = conn.execute("SELECT id, price FROM cars WHERE name=?", (car_name,)).fetchone()
        if not car: return redirect("/")

        pricing = calculate_pricing(car["price"], days, start_date)
        conn.execute("""
            INSERT INTO bookings (user, car_id, car_name, days, price, total, name, email, phone, payment, start_date, status, gst, discount, surcharge)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?, ?)
        """, (session["username"], car["id"], car_name, days, car["price"], pricing["total"], name, email, phone, payment, start_date, pricing["gst"], pricing["discount"], pricing["surcharge"]))
        conn.commit()
        conn.close()
        flash("Booking successful!", "success")
        return redirect("/dashboard")
    except Exception as e:
        flash(f"Error: {e}", "error")
        return redirect("/")

@app.route("/cancel_booking/<int:id>")
@login_required
def cancel_booking(id):
    conn = connect()
    conn.execute("UPDATE bookings SET status='cancelled' WHERE id=? AND user=?", (id, session["username"]))
    conn.commit()
    conn.close()
    flash("Booking cancelled.", "success")
    return redirect("/dashboard")

@app.route("/api/calculate_price", methods=["POST"])
def api_calculate_price():
    data = request.get_json()
    p = calculate_pricing(int(data.get("price_per_day", 0)), int(data.get("days", 0)), data.get("start_date"))
    return jsonify(p)

if __name__ == "__main__":
    app.run(debug=True)