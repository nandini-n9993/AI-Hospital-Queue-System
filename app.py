from flask import Flask, render_template, request

app = Flask(__name__)

# Dummy patient data (you can replace with AI logic later)
patients = []

def calculate_priority(symptoms):
    symptoms = symptoms.lower()
    if "chest pain" in symptoms or "heart" in symptoms:
        return "High"
    elif "fever" in symptoms or "cough" in symptoms:
        return "Medium"
    else:
        return "Low"

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/patient", methods=["GET", "POST"])
def patient():
    if request.method == "POST":
        name = request.form["name"]
        symptoms = request.form["symptoms"]

        priority = calculate_priority(symptoms)

        patients.append({
            "name": name,
            "symptoms": symptoms,
            "priority": priority
        })

        return render_template("patient.html", message="Appointment Submitted!")

    return render_template("patient.html")

@app.route("/doctor")
def doctor():
    # Sort patients by priority
    priority_order = {"High": 1, "Medium": 2, "Low": 3}
    sorted_patients = sorted(patients, key=lambda x: priority_order[x["priority"]])

    return render_template("doctor.html", patients=sorted_patients)

if __name__ == "__main__":
    app.run()
