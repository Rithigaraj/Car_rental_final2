import sqlite3
import os
from werkzeug.security import generate_password_hash

# Absolute database path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "new_cars.db")

# Admin registration secret code
ADMIN_SECRET_CODE = "LUXEDRIVE2026"

# ---------------- CONNECT ----------------
def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ---------------- CREATE TABLES ----------------
def create_tables():
    conn = connect()
    cur = conn.cursor()

    # Cars Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS cars (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        price INTEGER NOT NULL,
        available INTEGER DEFAULT 1,
        image_url TEXT DEFAULT ''
    )
    """)

    # Unified Users Table - start with minimum, migration will add role
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    """)

    # Bookings Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user TEXT,
        car_id INTEGER,
        car_name TEXT,
        days INTEGER,
        price INTEGER,
        total REAL,
        name TEXT,
        email TEXT,
        phone TEXT,
        payment TEXT,
        location TEXT,
        start_date TEXT,
        status TEXT DEFAULT 'active',
        gst REAL DEFAULT 0,
        discount REAL DEFAULT 0,
        surcharge REAL DEFAULT 0
    )
    """)

    # Seed sample cars
    cur.execute("SELECT COUNT(*) FROM cars")
    if cur.fetchone()[0] == 0:
        sample_cars = [
            ("Mercedes-Benz C-Class", 4500, 1, "https://images.unsplash.com/photo-1618843479313-40f8afb4b4d8?w=600&h=400&fit=crop"),
            ("BMW 3 Series", 4000, 1, "https://images.unsplash.com/photo-1555215695-3004980ad54e?w=600&h=400&fit=crop"),
            ("Audi A4", 3800, 1, "https://images.unsplash.com/photo-1606664515524-ed2f786a0bd6?w=600&h=400&fit=crop"),
            ("Tesla Model 3", 5000, 1, "https://images.unsplash.com/photo-1560958089-b8a1929cea89?w=600&h=400&fit=crop"),
            ("Porsche 911", 8000, 1, "https://images.unsplash.com/photo-1503376780353-7e6692767b70?w=600&h=400&fit=crop"),
            ("Range Rover Sport", 6000, 1, "https://images.unsplash.com/photo-1606016159991-dfe4f2746ad5?w=600&h=400&fit=crop"),
        ]
        cur.executemany(
            "INSERT INTO cars (name, price, available, image_url) VALUES (?, ?, ?, ?)",
            sample_cars
        )

    conn.commit()
    conn.close()

# ---------------- MIGRATION ----------------
def migrate_tables():
    conn = connect()
    cur = conn.cursor()

    # Add role to users table if missing
    cur.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in cur.fetchall()]
    if "role" not in columns:
        cur.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user'")
    
    # Handle Bookings migration (start_date, status, gst, discount, surcharge)
    cur.execute("PRAGMA table_info(bookings)")
    columns = [col[1] for col in cur.fetchall()]
    new_cols = {
        "start_date": "TEXT",
        "status": "TEXT DEFAULT 'active'",
        "gst": "REAL DEFAULT 0",
        "discount": "REAL DEFAULT 0",
        "surcharge": "REAL DEFAULT 0",
    }
    for col_name, col_type in new_cols.items():
        if col_name not in columns:
            cur.execute(f"ALTER TABLE bookings ADD COLUMN {col_name} {col_type}")

    # Seed default admin after role column is guaranteed to exist
    cur.execute("SELECT * FROM users WHERE username=?", ("admin",))
    if not cur.fetchone():
        hashed_pw = generate_password_hash("1234")
        cur.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            ("admin", hashed_pw, "admin")
        )
    else:
        # Ensure existing admin has admin role
        cur.execute("UPDATE users SET role='admin' WHERE username='admin'")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_tables()
    migrate_tables()
    print("Database system updated to unified role-based model!")