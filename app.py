from flask import Flask, render_template, request, redirect, session
import sqlite3, os, uuid
from config import *
import smtplib

app = Flask(__name__)
app.secret_key = "secret123"

DATABASE = "reservations.db"

# ---------- DB ----------
def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS reservations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        phone TEXT,
        email TEXT,
        date TEXT,
        time TEXT,
        guests INTEGER,
        token TEXT,
        status TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

def get_db():
    return sqlite3.connect(DATABASE)

# ---------- 逻辑 ----------
def check_business_hours(time):
    hour = int(time.split(":")[0])
    return OPEN_HOUR <= hour <= CLOSE_HOUR

def slot_available(date, time, guests):

    conn = get_db()
    c = conn.cursor()

    c.execute("""
        SELECT SUM(guests) FROM reservations
        WHERE date=? AND time=? AND status='active'
    """,(date,time))

    total = c.fetchone()[0]
    conn.close()

    if total is None:
        total = 0

    return total + guests <= CAPACITY

# ---------- Email ----------
def send_email(email, token):

    cancel_link = f"https://your-site.onrender.com/cancel/{token}"

    msg = f"Reservation confirmed.\nCancel: {cancel_link}"

    try:
        server = smtplib.SMTP("smtp.gmail.com",587)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        server.sendmail(EMAIL_USER, email, msg)
        server.quit()
    except:
        print("Email failed")

# ---------- Routes ----------
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/reserve", methods=["POST"])
def reserve():

    name = request.form["name"]
    phone = request.form["phone"]
    email = request.form["email"]
    date = request.form["date"]
    time = request.form["time"]
    guests = int(request.form["guests"])

    if not check_business_hours(time):
        return "Closed at that time"

    if not slot_available(date, time, guests):
        return "Restaurant full"

    token = str(uuid.uuid4())

    conn = get_db()
    c = conn.cursor()

    c.execute("""
        INSERT INTO reservations
        (name,phone,email,date,time,guests,token,status)
        VALUES (?,?,?,?,?,?,?,'active')
    """,(name,phone,email,date,time,guests,token))

    conn.commit()
    conn.close()

    send_email(email, token)

    return render_template("success.html")

@app.route("/cancel/<token>")
def cancel(token):

    conn = get_db()
    c = conn.cursor()

    c.execute("UPDATE reservations SET status='cancelled' WHERE token=?", (token,))

    conn.commit()
    conn.close()

    return "Reservation cancelled"

# ---------- Admin ----------
@app.route("/admin/login", methods=["GET","POST"])
def login():

    if request.method == "POST":
        if request.form["password"] == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect("/admin")

    return render_template("login.html")

@app.route("/admin")
def admin():

    if "admin" not in session:
        return redirect("/admin/login")

    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT * FROM reservations ORDER BY date,time")
    rows = c.fetchall()

    conn.close()

    return render_template("admin.html", rows=rows)

# ---------- RUN ----------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)