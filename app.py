from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime
import sqlite3

app = Flask(__name__)

# ---------- DATABASE ----------
def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
    CREATE TABLE IF NOT EXISTS patients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        age TEXT,
        symptoms TEXT,
        priority TEXT,
        doctor TEXT,
        done INTEGER,
        date TEXT
    )
    """)
    conn.commit()
    conn.close()

init_db()

# ---------- SPECIALIST LOGIC ----------
def assign_specialist(symptoms):
    s = symptoms.lower()

    if "heart" in s or "chest pain" in s:
        return "Cardiologist", "High"
    elif "brain" in s or "headache" in s:
        return "Neurologist", "Medium"
    elif "bone" in s or "fracture" in s:
        return "Orthopedic", "Medium"
    elif any(word in s for word in ["skin", "rash", "allergy", "itching", "acne"]):
        return "Dermatologist", "Low"
    elif "fever" in s or "cough" in s:
        return "General Physician", "Low"
    else:
        return "General Physician", "Low"

# ---------- HOME ----------
@app.route("/")
def home():
    return render_template("index.html")

# ---------- PATIENT ----------
@app.route("/patient", methods=["GET", "POST"])
def patient():
    if request.method == "POST":
        name = request.form.get("name")
        age = request.form.get("age")
        symptoms = request.form.get("symptoms")

        if not name or not age or not symptoms:
            return "Missing data", 400

        specialist, priority = assign_specialist(symptoms)

        conn = get_db()
        conn.execute(
            "INSERT INTO patients (name, age, symptoms, priority, doctor, done, date) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (name, age, symptoms, priority, specialist, 0, str(datetime.now().date()))
        )
        conn.commit()
        conn.close()

    conn = get_db()
    patients = conn.execute("SELECT * FROM patients WHERE done = 0").fetchall()
    conn.close()

    return render_template("patient.html", patients=patients)

# ---------- DOCTOR ----------
@app.route("/doctor")
def doctor():
    conn = get_db()
    rows = conn.execute("SELECT * FROM patients WHERE done = 0").fetchall()
    conn.close()

    grouped = {}
    for p in rows:
        grouped.setdefault(p["doctor"], []).append(p)

    return render_template("doctor.html", grouped=grouped)

# ---------- COMPLETE ----------
@app.route("/complete/<int:pid>")
def complete(pid):
    conn = get_db()
    conn.execute("UPDATE patients SET done = 1 WHERE id = ?", (pid,))
    conn.commit()
    conn.close()
    return redirect(url_for("doctor"))

# ---------- RUN ----------
if __name__ == "__main__":
    app.run()
