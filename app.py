from flask import Flask, render_template, request, redirect, url_for, flash
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
