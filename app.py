from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime

app = Flask(__name__)

patients = []

# AI-like specialization suggestion
def assign_specialist(symptoms):
    s = symptoms.lower()
    if "heart" in s or "chest pain" in s:
        return "Cardiologist", "High"
    elif "brain" in s or "headache" in s:
        return "Neurologist", "Medium"
    elif "bone" in s or "fracture" in s:
        return "Orthopedic", "Medium"
    elif "fever" in s or "cough" in s:
        return "General Physician", "Low"
    else:
        return "General Physician", "Low"

# Remove old completed patients (daily reset logic)
def clean_old_data():
    today = datetime.now().date()
    global patients
    patients = [p for p in patients if p["date"] == today and not p["done"]]

@app.route("/")
def home():
    clean_old_data()
    return render_template("index.html")

@app.route("/patient", methods=["GET", "POST"])
def patient():
    clean_old_data()

    if request.method == "POST":
        name = request.form["name"]
        age = request.form["age"]
        symptoms = request.form["symptoms"]

        specialist, priority = assign_specialist(symptoms)

        patients.append({
            "id": len(patients),
            "name": name,
            "age": age,
            "symptoms": symptoms,
            "priority": priority,
            "doctor": specialist,
            "done": False,
            "date": datetime.now().date()
        })

        return render_template("patient.html", success=True, specialist=specialist, priority=priority)

    return render_template("patient.html", patients=patients)

@app.route("/doctor")
def doctor():
    clean_old_data()

    grouped = {}
    for p in patients:
        if not p["done"]:
            grouped.setdefault(p["doctor"], []).append(p)

    return render_template("doctor.html", grouped=grouped)

@app.route("/complete/<int:pid>")
def complete(pid):
    for p in patients:
        if p["id"] == pid:
            p["done"] = True
    return redirect(url_for("doctor"))

if __name__ == "__main__":
    app.run()
