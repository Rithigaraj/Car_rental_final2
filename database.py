import sqlite3
import os

# ✅ Absolute database path (prevents path errors)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "new_cars.db")

# ---------------- CONNECT ----------------
def connect():
    return sqlite3.connect(DB_PATH)

# ---------------- CREATE TABLES ----------------
def create_tables():
    conn = connect()
    cur = conn.cursor()

    # 🚗 Cars Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS cars (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        price INTEGER NOT NULL,
        available INTEGER DEFAULT 1
    )
    """)

    # 👤 Users Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    """)

    # 👑 Admin Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS admin (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    """)

    # 📋 Bookings Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user TEXT,
        car_id INTEGER,
        car_name TEXT,
        days INTEGER,
        price INTEGER,
        total INTEGER,
        name TEXT,
        email TEXT,
        phone TEXT,
        payment TEXT,
        location TEXT
    )
    """)

    # 👑 Insert default admin (only once)
    cur.execute("SELECT * FROM admin WHERE username=?", ("admin",))
    if not cur.fetchone():
        cur.execute(
            "INSERT INTO admin (username, password) VALUES (?, ?)",
            ("admin", "1234")
        )

    conn.commit()
    conn.close()

# ---------------- RUN ----------------
if __name__ == "__main__":
    create_tables()
    print("✅ Database created successfully!")