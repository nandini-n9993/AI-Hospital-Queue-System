from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime

app = Flask(__name__)

patients = []

# Specialist + priority logic
def assign_specialist(symptoms):
    s = symptoms.lower()

    if "heart" in s or "chest pain" in s:
        return "Cardiologist", "High"
    elif "brain" in s or "headache" in s or "seizure" in s:
        return "Neurologist", "Medium"
    elif "bone" in s or "fracture" in s or "joint" in s:
        return "Orthopedic", "Medium"
    elif any(word in s for word in ["skin", "rash", "allergy", "itching", "acne"]):
        return "Dermatologist", "Low"
    elif "fever" in s or "cough" in s or "cold" in s:
        return "General Physician", "Low"
    else:
        return "General Physician", "Low"

# Clean completed patients daily
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
        name = request.form.get("name")
        age = request.form.get("age")
        symptoms = request.form.get("symptoms")

        if not name or not age or not symptoms:
            return "Missing data", 400

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

        return render_template(
            "patient.html",
            success=True,
            specialist=specialist,
            priority=priority,
            patients=patients
        )

    return render_template("patient.html", patients=patients)

@app.route("/doctor")
def doctor():
    clean_old_data()

    grouped = {}

    for p in patients:
        try:
            if not p.get("done", False):
                doctor = p.get("doctor", "General Physician")
                grouped.setdefault(doctor, []).append(p)
        except:
            pass  # prevents crash

    return render_template("doctor.html", grouped=grouped)

@app.route("/complete/<int:pid>")
def complete(pid):
    for p in patients:
        if p.get("id") == pid:
            p["done"] = True
    return redirect(url_for("doctor"))

if __name__ == "__main__":
    app.run()
