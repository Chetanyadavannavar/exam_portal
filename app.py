from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "secret123"  # change this to a secure key for production

DB_PATH = "users.db"

# -------------------
# Initialize Database
# -------------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  fullname TEXT,
                  email TEXT,
                  username TEXT UNIQUE,
                  password TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS results
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  score INTEGER,
                  total INTEGER,
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY(user_id) REFERENCES users(id))''')
    conn.commit()
    conn.close()

# -------------------
# Helpers
# -------------------
def get_user_by_username(username):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, fullname, email, username, password FROM users WHERE username = ?", (username,))
    row = c.fetchone()
    conn.close()
    return row

# -------------------
# Register Route
# -------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        fullname = request.form["fullname"]
        email = request.form["email"]
        username = request.form["username"]
        password = generate_password_hash(request.form["password"])  # store hashed password

        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("INSERT INTO users (fullname, email, username, password) VALUES (?, ?, ?, ?)",
                      (fullname, email, username, password))
            conn.commit()
            conn.close()

            flash("Registration successful! Please log in.", "success")
            return redirect(url_for("login"))

        except sqlite3.IntegrityError:
            flash("Username already exists. Choose another.", "error")
            return redirect(url_for("register"))

    return render_template("register.html")


# -------------------
# Login Route
# -------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = get_user_by_username(username)
        if user and check_password_hash(user[4], password):  # user[4] is password
            session["username"] = username
            session["user_id"] = user[0]
            flash("Login successful!", "success")
            return redirect(url_for("instruction"))
        else:
            flash("Invalid username or password", "error")
            return redirect(url_for("login"))

    return render_template("login.html")


# -------------------
# Instruction (Restricted) Page (home)
# -------------------
@app.route("/")
def instruction():
    if "username" not in session:
        return redirect(url_for("login"))
    return render_template("instruction.html", username=session.get("username"))


# -------------------
# Exam Page (restricted)
# -------------------
@app.route("/exam")
def exam():
    if "username" not in session:
        flash("Please log in to start the exam", "error")
        return redirect(url_for("login"))
    return render_template("exam.html")


# -------------------
# Result Page
# -------------------
@app.route("/result", methods=["POST"])
def result():
    if "username" not in session:
        return redirect(url_for("login"))

    # correct answers
    answers = {
        "q1": "New Delhi",
        "q2": "Mahatma Gandhi",
        "q3": "Pacific Ocean",
        "q4": "Mars",
        "q5": "Amazon"
    }
    score = 0
    for q, correct_ans in answers.items():
        if request.form.get(q) == correct_ans:
            score += 1

    # save result
    user_id = session.get("user_id")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO results (user_id, score, total) VALUES (?, ?, ?)", (user_id, score, len(answers)))
    conn.commit()
    conn.close()

    return render_template("result.html", score=score, total=len(answers))


# -------------------
# Logout Route
# -------------------
@app.route("/logout")
def logout():
    session.pop("username", None)
    session.pop("user_id", None)
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


# -------------------
# Run the app
# -------------------
if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=8000)
