from flask import Flask, render_template, request, redirect
import sqlite3
import os

app = Flask(__name__)

DATABASE = "reservations.db"

def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS reservations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        phone TEXT,
        date TEXT,
        time TEXT,
        guests INTEGER
    )
    """)

    conn.commit()
    conn.close()

init_db()

def get_db():
    return sqlite3.connect(DATABASE)

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/reserve", methods=["POST"])
def reserve():

    name = request.form["name"]
    phone = request.form["phone"]
    date = request.form["date"]
    time = request.form["time"]
    guests = request.form["guests"]

    conn = get_db()
    c = conn.cursor()

    # 防止重复预订
    c.execute(
        "SELECT * FROM reservations WHERE date=? AND time=?",
        (date, time)
    )

    existing = c.fetchone()

    if existing:
        conn.close()
        return "Sorry, this time slot is already booked."

    c.execute(
        "INSERT INTO reservations (name,phone,date,time,guests) VALUES (?,?,?,?,?)",
        (name, phone, date, time, guests)
    )

    conn.commit()
    conn.close()

    return redirect("/")


@app.route("/admin")
def admin():

    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT * FROM reservations ORDER BY date,time")

    reservations = c.fetchall()

    conn.close()

    return render_template("admin.html", reservations=reservations)


if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    app.run(host="0.0.0.0", port=port)