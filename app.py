from flask import Flask, request, redirect, session, render_template
from database import create_tables, connect

app = Flask(__name__)
app.secret_key = "secret123"

create_tables()

# ================= HOME =================
@app.route("/")
def home():
    conn = connect()
    cars = conn.execute("SELECT * FROM cars WHERE available=1").fetchall()
    conn.close()
    return render_template("index.html", cars=cars)

# ================= REGISTER =================
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = connect()
        try:
            conn.execute(
                "INSERT INTO users (username,password) VALUES (?,?)",
                (username,password)
            )
            conn.commit()
        except:
            return "⚠ User already exists"
        finally:
            conn.close()

        return redirect("/login_user")

    return render_template("register.html")

# ================= USER LOGIN =================
@app.route("/login_user", methods=["GET","POST"])
def login_user():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = connect()
        user = conn.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username,password)
        ).fetchone()
        conn.close()

        if user:
            session["user"] = username
            return redirect("/")
        else:
            return "❌ Invalid login"

    return render_template("login_user.html")

# ================= ADMIN LOGIN =================
@app.route("/login", methods=["GET","POST"])
def login_admin():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = connect()
        admin = conn.execute(
            "SELECT * FROM admin WHERE username=? AND password=?",
            (username,password)
        ).fetchone()
        conn.close()

        if admin:
            session.clear()  # 🔥 IMPORTANT FIX
            session["admin"] = username
            return redirect("/admin")
        else:
            return "❌ Invalid admin login"

    return render_template("login.html")

# ================= ADMIN PAGE =================
@app.route("/admin")
def admin():
    if "admin" not in session:
        return redirect("/login")

    conn = connect()

    cars = conn.execute("SELECT * FROM cars").fetchall()
    bookings = conn.execute("SELECT * FROM bookings").fetchall()

    revenue = conn.execute("SELECT SUM(total) FROM bookings").fetchone()[0]
    if revenue is None:
        revenue = 0

    conn.close()

    return render_template("admin.html", cars=cars, bookings=bookings, revenue=revenue)

# ================= ADD CAR =================
@app.route("/add_car", methods=["POST"])
def add_car():
    if "admin" not in session:
        return "Access denied"

    name = request.form["name"]
    price = request.form["price"]

    conn = connect()
    conn.execute(
        "INSERT INTO cars (name,price,available) VALUES (?,?,1)",
        (name,price)
    )
    conn.commit()
    conn.close()

    return redirect("/admin")

# ================= DELETE CAR =================
@app.route("/delete_car/<int:id>")
def delete_car(id):
    if "admin" not in session:
        return "Access denied"

    conn = connect()
    conn.execute("DELETE FROM cars WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect("/admin")

# ================= BOOK CAR =================
@app.route("/book", methods=["POST"])
def book():
    try:
        car_name = request.form["car_name"]
        days = int(request.form["days"])

        name = request.form["name"]
        email = request.form["email"]
        phone = request.form["phone"]
        payment = request.form["payment"]

        conn = connect()

        # ✅ GET car price from database
        car = conn.execute("SELECT price FROM cars WHERE name=?", (car_name,)).fetchone()
        
        if car:
            price_per_day = car[0]
            total = price_per_day * days   # ✅ FIXED HERE
        else:
            return "Car not found"

        # ✅ STORE total in DB
        conn.execute("""
            INSERT INTO bookings (car_name, days, total, name, email, phone, payment)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (car_name, days, total, name, email, phone, payment))

        conn.commit()
        conn.close()

        return f"Booking Successful! Total: ₹{total}"

    except Exception as e:
        return str(e)

# ================= CANCEL =================
@app.route("/cancel", methods=["POST"])
def cancel():
    if "admin" not in session:
        return "Access denied"

    booking_id = request.form["booking_id"]

    conn = connect()
    conn.execute("DELETE FROM bookings WHERE id=?", (booking_id,))
    conn.commit()
    conn.close()

    return redirect("/admin")

# ================= CLEAR BOOKINGS =================
@app.route("/clear_bookings", methods=["POST"])
def clear():
    if "admin" not in session:
        return "Access denied"

    conn = connect()
    conn.execute("DELETE FROM bookings")
    conn.commit()
    conn.close()

    return redirect("/admin")

# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)