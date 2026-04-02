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
        age TEXT,from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "secret_medical_key"

# ---------- DB ----------
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db_connection() as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            age INTEGER,
            symptoms TEXT,
            severity INTEGER,
            chronic INTEGER,
            emergency INTEGER DEFAULT 0,
            score REAL,
            status TEXT DEFAULT 'Waiting'
        )''')
init_db()

# ---------- AI ----------
def calculate_priority_score(severity, age, chronic, emergency, waiting):
    age_weight = 10 if (age < 5 or age > 60) else 2
    emergency_boost = 100 if emergency == 1 else 0
    return (severity * 15) + (chronic * 10) + age_weight + emergency_boost - (waiting * 0.5)

def suggest_doctor(symptoms):
    s = symptoms.lower()
    if "chest" in s or "heart" in s:
        return "Cardiologist"
    elif "skin" in s:
        return "Dermatologist"
    elif "eye" in s:
        return "Ophthalmologist"
    elif "headache" in s or "brain" in s:
        return "Neurologist"
    elif "bone" in s or "joint" in s:
        return "Orthopedic"
    elif "fever" in s or "cough" in s:
        return "General Physician"
    elif "stomach" in s:
        return "Gastroenterologist"
    return "General Physician"

# ---------- CLEAR ONLY DONE ----------
def clear_done_patients():
    with get_db_connection() as conn:
        conn.execute("DELETE FROM patients WHERE status = 'Done'")
        conn.commit()

# ---------- ROUTES ----------
@app.route('/')
def index():
    clear_done_patients()  # clears only completed patients
    return render_template('index.html')

@app.route('/book', methods=['POST'])
def book():
    name = request.form.get('name')
    age = int(request.form.get('age'))
    symptoms = request.form.get('symptoms')
    severity = int(request.form.get('severity'))
    chronic = int(request.form.get('chronic'))

    with get_db_connection() as conn:
        waiting = conn.execute("SELECT COUNT(*) FROM patients").fetchone()[0]

        emergency = 1 if severity == 3 or age > 65 else 0
        score = calculate_priority_score(severity, age, chronic, emergency, waiting)

        conn.execute("""
            INSERT INTO patients (name, age, symptoms, severity, chronic, emergency, score)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (name, age, symptoms, severity, chronic, emergency, score))

        conn.commit()

    return redirect(url_for('patient_view'))

@app.route('/patient_view')
def patient_view():
    with get_db_connection() as conn:
        patients = conn.execute("SELECT * FROM patients").fetchall()

    patients = [dict(p) for p in patients]

    for p in patients:
        p['doctor'] = suggest_doctor(p['symptoms'])

    patients.sort(key=lambda x: (x['status'] == 'Done', -x['score']))

    return render_template('patient.html', patients=patients, now=datetime.now())

@app.route('/doctor_view')
def doctor_view():
    with get_db_connection() as conn:
        patients = conn.execute("SELECT * FROM patients").fetchall()

    patients = [dict(p) for p in patients]

    for p in patients:
        p['doctor'] = suggest_doctor(p['symptoms'])

    # group by specialization
    queues = {}
    for p in patients:
        doc = p['doctor']
        if doc not in queues:
            queues[doc] = []
        queues[doc].append(p)

    return render_template('doctor.html', queues=queues, now=datetime.now())

@app.route('/set_emergency/<int:id>')
def set_emergency(id):
    with get_db_connection() as conn:
        conn.execute("UPDATE patients SET emergency = 1, score = score + 500 WHERE id = ?", (id,))
        conn.commit()

    return redirect(url_for('doctor_view'))

@app.route('/mark_done/<int:id>')
def mark_done(id):
    with get_db_connection() as conn:
        conn.execute("UPDATE patients SET status = 'Done' WHERE id = ?", (id,))
        conn.commit()

    return redirect(url_for('doctor_view'))

if __name__ == '__main__':
    app.run(debug=True)
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
