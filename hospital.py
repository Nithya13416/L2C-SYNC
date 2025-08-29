import datetime
import sqlite3
import streamlit as st
import pandas as pd
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter

# =======================================
# Database Functions
# =======================================
def save_uploaded_data(df):
    conn = sqlite3.connect("patients.db")

    # Overwrite main table
    df.to_sql("patients_data", conn, if_exists="replace", index=False)

    # Append with timestamp to history
    df_hist = df.copy()
    df_hist["uploaded_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    df_hist.to_sql("patients_data_history", conn, if_exists="append", index=False)

    conn.close()


def get_patient_history(name):
    conn = sqlite3.connect("patients.db")
    query = "SELECT * FROM patients_data_history WHERE name = ?"
    df = pd.read_sql(query, conn, params=(name,))
    conn.close()
    return df


# =======================================
# Risk & Explanation Helpers
# =======================================
def overall_risk_label(n_issues: int) -> str:
    if n_issues == 0:
        return "Normal"
    elif n_issues == 1:
        return "Mild Alert"
    else:
        return "Critical Alert"


def explain_heart_rate(hr: float):
    normal = "60–100 BPM"
    if hr < 60:
        return ("Low", normal,
                "Below normal (bradycardia). Could be athlete training, fatigue, dehydration, or meds.",
                ["Re-check at rest", "Hydrate", "Seek care if dizziness or chest pain"])
    elif hr > 100:
        return ("High", normal,
                "Above normal (tachycardia). Could be stress, fever, dehydration, or stimulants.",
                ["Rest", "Hydrate", "Avoid caffeine", "Seek care if >120 BPM or with symptoms"])
    else:
        return ("Normal", normal, "Within expected range.", [])


def explain_temperature(temp_c: float):
    normal = "36.0–37.5 °C"
    if temp_c < 36.0:
        return ("Low", normal, "Below normal; may be error, cold exposure, or thyroid issue.",
                ["Re-check", "Warm up", "Consult doctor if persistent"])
    elif temp_c > 37.5:
        return ("High", normal, "Fever; may indicate infection.",
                ["Hydrate", "Rest", "Take fever reducer if advised", "Seek care if >38.5 °C"])
    else:
        return ("Normal", normal, "Within expected range.", [])


def explain_oxygen(spo2: float):
    normal = "≥95 %"
    if spo2 < 92:
        return ("Low", normal, "Low oxygen; possible lung/heart issue.",
                ["Sit upright", "Re-check", "Seek urgent care if symptoms"])
    elif spo2 < 95:
        return ("Borderline", normal, "Slightly low; may be transient.",
                ["Re-check after 5 min", "Ensure good sensor contact"])
    else:
        return ("Normal", normal, "Within expected range.", [])


def explain_bp(sys: float, dia: float):
    normal = "<140 / <90 mmHg"
    if sys >= 140 or dia >= 90:
        return ("High", normal, "Elevated BP; increases long-term cardiovascular risk.",
                ["Re-check after 5 min", "Reduce salt/stress", "Consult doctor"])
    else:
        return ("Normal", normal, "Within target range.", [])


def explain_bmi(bmi: float):
    normal = "18.5–24.9"
    if bmi < 18.5:
        return ("Low", normal, "Underweight; risk of nutrient deficiency.",
                ["Review diet", "Consider nutritionist"])
    elif bmi > 24.9:
        return ("High", normal, "Overweight; higher metabolic and heart risk.",
                ["Increase activity", "Balanced diet", "Weight management support"])
    else:
        return ("Normal", normal, "Within healthy range.", [])


def build_vital_explanations(p):
    items = []
    hr_status, hr_norm, hr_meaning, hr_actions = explain_heart_rate(float(p["heart_rate"]))
    items.append(("Heart Rate", f"{p['heart_rate']} BPM", hr_status, hr_norm, hr_meaning, hr_actions))

    t_status, t_norm, t_meaning, t_actions = explain_temperature(float(p["temperature"]))
    items.append(("Temperature", f"{p['temperature']} °C", t_status, t_norm, t_meaning, t_actions))

    ox_status, ox_norm, ox_meaning, ox_actions = explain_oxygen(float(p["oxygen"]))
    items.append(("Oxygen", f"{p['oxygen']} %", ox_status, ox_norm, ox_meaning, ox_actions))

    bp_status, bp_norm, bp_meaning, bp_actions = explain_bp(float(p["systolic"]), float(p["diastolic"]))
    items.append(("Blood Pressure", f"{p['systolic']}/{p['diastolic']} mmHg", bp_status, bp_norm, bp_meaning, bp_actions))

    bmi_status, bmi_norm, bmi_meaning, bmi_actions = explain_bmi(float(p["bmi"]))
    items.append(("BMI", f"{round(float(p['bmi']), 2)}", bmi_status, bmi_norm, bmi_meaning, bmi_actions))

    return items


# =======================================
# PDF Report Generator
# =======================================
def generate_report(patient):
    filename = f"{patient['name']}_report.pdf"
    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(f"<b>Patient Report: {patient['name']}</b>", styles["Heading1"]))
    story.append(Spacer(1, 12))

    # Overall risk
    issues = build_vital_explanations(patient)
    risk = overall_risk_label(sum(1 for i in issues if i[2] != "Normal"))
    story.append(Paragraph(f"Overall Risk Level: <b>{risk}</b>", styles["Heading2"]))
    story.append(Spacer(1, 12))

    # Vital explanations
    for (label, value, status, normal, meaning, actions) in issues:
        story.append(Paragraph(f"<b>{label}</b>: {value} ({status})", styles["Heading3"]))
        story.append(Paragraph(f"Expected: {normal}", styles["Normal"]))
        story.append(Paragraph(f"Meaning: {meaning}", styles["Normal"]))
        if actions:
            story.append(Paragraph("Suggested Actions:", styles["Italic"]))
            story.append(ListFlowable(
                [ListItem(Paragraph(a, styles["Normal"])) for a in actions],
                bulletType="bullet"
            ))
        story.append(Spacer(1, 8))

    # Disclaimer
    story.append(Spacer(1, 12))
    story.append(Paragraph("<b>Notes</b>", styles["Heading2"]))
    story.append(Paragraph(
        "This report is informational and does not replace clinical judgment. "
        "If severe symptoms occur (chest pain, severe shortness of breath, fainting), seek medical attention immediately.",
        styles["Italic"]
    ))

    doc.build(story)
    return filename


# =======================================
# Dashboard Page
# =======================================
def dashboard_page():
    patient = st.session_state.selected_patient
    st.title("📊 Smartwatch Health Dashboard")

    if st.button("🔙 Return to Patients"):
        st.session_state.page = "patients"
        st.rerun()

    st.subheader(f"Patient: {patient['name']}")

    # History
    df_hist = get_patient_history(patient['name'])

    # Risk status
    issues = build_vital_explanations(patient)
    n_issues = sum(1 for i in issues if i[2] != "Normal")
    risk = overall_risk_label(n_issues)

    if risk == "Normal":
        st.success("✅ Status: Normal")
    elif risk == "Mild Alert":
        st.warning(f"⚠️ Status: Mild Alert ({[i[0] for i in issues if i[2] != 'Normal'][0]})")
    else:
        st.error(f"🚨 Status: Critical Alert (Problems with {', '.join([i[0] for i in issues if i[2] != 'Normal'])})")

    # Trends
    if not df_hist.empty:
        st.markdown("### 📈 Health Trends")
        st.line_chart(df_hist.set_index("uploaded_at")[["heart_rate", "temperature", "oxygen"]])


# =======================================
# Login Page
# =======================================



USERS = {
    "doctor111": "password123",
    "nurse222": "pass456",
}
def login_page():
    st.title("🏥 Hospital Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username == "admin" and password == "admin":  # simple login
            st.session_state.page = "patients"
            st.rerun()
        else:
            st.error("Invalid credentials")

            # =======================================
# Main App
# =======================================
def main():
    if "page" not in st.session_state:
        st.session_state.page = "login"
    if "selected_patient" not in st.session_state:
        st.session_state.selected_patient = None

    if st.session_state.page == "login":
        login_page()
    elif st.session_state.page == "patients":
        st.title("👨‍⚕️ Patients List")

        conn = sqlite3.connect("patients.db")
        try:
            df = pd.read_sql("SELECT * FROM patients_data", conn)
        except:
            df = pd.DataFrame()
        conn.close()

        if df.empty:
            st.warning("⚠️ No patient data found. Please upload.")
            uploaded = st.file_uploader("Upload patient CSV", type=["csv"])
            if uploaded:
                df = pd.read_csv(uploaded)
                save_uploaded_data(df)
                st.success("✅ Data uploaded successfully!")
                st.rerun()
        else:
            st.dataframe(df)

            selected = st.selectbox("Select Patient", df["name"].tolist())
            if st.button("Open Dashboard"):
                st.session_state.selected_patient = df[df["name"] == selected].iloc[0].to_dict()
                st.session_state.page = "dashboard"
                st.rerun()

    elif st.session_state.page == "dashboard":
        dashboard_page()


if __name__ == "__main__":
    main()

