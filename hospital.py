import streamlit as st
import pandas as pd
import sqlite3
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io
from dotenv import load_dotenv
import requests
import os
import json

# ---------------------------
# Slack Config
# ---------------------------
load_dotenv()
SLACK_BOT_TOKEN2 = os.getenv("SLACK_BOT_TOKEN2")
SLACK_CHANNEL_ID2 = os.getenv("SLACK_CHANNEL_ID2")

def send_slack_report(patient, risks):
    """Send detailed patient vitals to Slack in text format."""
    if not SLACK_BOT_TOKEN2 or not SLACK_CHANNEL_ID2:
        st.warning("⚠️ Slack not configured (missing token or channel ID).")
        return

    message = f"*📋 Patient Vitals Report: {patient['name']}*\n"
    message += f"• Age: {patient['age']} | Gender: {patient['gender']}\n"
    message += f"• Weight: {patient['weight']} kg | Height: {patient['height']} cm\n"
    message += f"• Heart Rate: {patient['heart_rate']} BPM\n"
    message += f"• Temperature: {patient['temperature']} °C\n"
    message += f"• Oxygen: {patient['oxygen']} %\n"
    message += f"• Blood Pressure: {patient['systolic']}/{patient['diastolic']} mmHg\n"
    message += f"• BMI: {round(patient['bmi'], 2)}\n\n"

    message += "*📝 Risk Analysis:*\n"
    for r in risks:
        message += f"- {r}\n"

    url = "https://slack.com/api/chat.postMessage"
    headers = {
        "Authorization": f"Bearer {SLACK_BOT_TOKEN2}",
        "Content-Type": "application/json"
    }
    data = {"channel": SLACK_CHANNEL_ID2, "text": message}

    response = requests.post(url, headers=headers, data=json.dumps(data))

    if response.status_code != 200 or not response.json().get("ok", False):
        st.error(f"⚠️ Slack API Error: {response.text}")
    else:
        st.success("✅ Patient report sent to Slack")

# ---------------------------
# Dummy Users
# ---------------------------
USERS = {
    "doctor111": "password123",
    "nurse222": "pass456",
}

# ---------------------------
# Session State
# ---------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "page" not in st.session_state:
    st.session_state.page = "login"
if "selected_patient" not in st.session_state:
    st.session_state.selected_patient = None
if "show_form" not in st.session_state:
    st.session_state.show_form = False

# ---------------------------
# CSS
# ---------------------------
def load_css():
    st.markdown(
        """
        <style>
        .block-container { max-width: 1100px; padding-top: 2rem; }
        h1, h2, h3 { font-family: 'Segoe UI', sans-serif; }
        .card {
            background-color: white; border-radius: 16px;
            padding: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            margin-bottom: 20px; text-align: center;
        }
        .metric-value { font-size: 26px; font-weight: bold; margin-top: 10px; }
        .status { font-size: 14px; margin-top: 6px; padding: 4px 10px;
                  border-radius: 12px; display: inline-block; }
        .normal { background: #d4f8d4; color: #2e7d32; }
        .good { background: #d0f0ff; color: #0277bd; }
        .low { background: #ffe0e0; color: #c62828; }
        </style>
        """,
        unsafe_allow_html=True,
    )

# ---------------------------
# DB Helpers
# ---------------------------
def init_db():
    conn = sqlite3.connect("patients.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patients_data (
            name TEXT, age INTEGER, gender TEXT,
            weight REAL, height REAL, email TEXT,
            heart_rate INTEGER, temperature REAL,
            oxygen INTEGER, systolic INTEGER,
            diastolic INTEGER, bmi REAL
        )
    """)
    conn.commit()
    conn.close()

def save_uploaded_data(df):
    df["bmi"] = df.apply(lambda x: round(x["Weight"] / ((x["Height"]/100)**2), 2), axis=1)
    df = df.rename(columns={
        "Name": "name", "Age": "age", "Gender": "gender",
        "Weight": "weight", "Height": "height", "Email": "email",
        "HeartRate": "heart_rate", "Temperature": "temperature",
        "Oxygen": "oxygen", "Systolic": "systolic", "Diastolic": "diastolic"
    })
    conn = sqlite3.connect("patients.db")
    df.to_sql("patients_data", conn, if_exists="append", index=False)
    conn.close()

def save_manual_patient(patient):
    conn = sqlite3.connect("patients.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO patients_data 
        (name, age, gender, weight, height, email, heart_rate, temperature, oxygen, systolic, diastolic, bmi)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        patient["name"], patient["age"], patient["gender"], patient["weight"], patient["height"],
        patient["email"], patient["heart_rate"], patient["temperature"], patient["oxygen"],
        patient["systolic"], patient["diastolic"], patient["bmi"]
    ))
    conn.commit()
    conn.close()

def get_patients():
    try:
        conn = sqlite3.connect("patients.db")
        df = pd.read_sql("SELECT * FROM patients_data", conn)
        conn.close()
        return df
    except Exception:
        return pd.DataFrame()

# ---------------------------
# Risk Analysis
# ---------------------------
def get_risk_explanations(patient):
    risks = []
    if not (60 <= patient['heart_rate'] <= 100):
        risks.append("⚠️ Abnormal Heart Rate: Possible arrhythmia or stress.")
    if not (36 <= patient['temperature'] <= 37.5):
        risks.append("🌡️ Abnormal Temperature: Fever or hypothermia risk.")
    if not (18.5 <= patient['bmi'] <= 24.9):
        risks.append("⚖️ Unhealthy BMI: Obesity, diabetes, or malnutrition.")
    if not (patient['systolic'] < 140 and patient['diastolic'] < 90):
        risks.append("🩸 High Blood Pressure: Hypertension risk.")
    if patient['oxygen'] < 95:
        risks.append("🫁 Low Oxygen Level: Possible hypoxemia.")
    if not risks:
        risks.append("✅ All vitals are within healthy ranges.")
    return risks

# ---------------------------
# PDF Report
# ---------------------------
def generate_pdf_report(patient, risks):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 750, "Patient Health Report")

    c.setFont("Helvetica", 12)
    c.drawString(50, 720, f"Name: {patient['name']}")
    c.drawString(50, 700, f"Age: {patient['age']}   Gender: {patient['gender']}")
    c.drawString(50, 680, f"Email (Emergency): {patient['email']}")
    c.drawString(50, 650, f"Heart Rate: {patient['heart_rate']} BPM")
    c.drawString(50, 630, f"Temperature: {patient['temperature']} °C")
    c.drawString(50, 610, f"Oxygen: {patient['oxygen']}%")
    c.drawString(50, 590, f"Blood Pressure: {patient['systolic']}/{patient['diastolic']} mmHg")
    c.drawString(50, 570, f"BMI: {round(patient['bmi'], 2)}")

    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, 540, "Risk Analysis:")

    c.setFont("Helvetica", 12)
    y = 520
    for risk in risks:
        c.drawString(60, y, f"- {risk}")
        y -= 20

    c.save()
    buffer.seek(0)
    return buffer

# ---------------------------
# Pages
# ---------------------------
def login_page():
    st.image("https://img.freepik.com/free-vector/health-professional-team-with-heart_23-2148503275.jpg", use_container_width=True)
    st.markdown("### Sign in")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("🔐 Sign In"):
        if username in USERS and USERS[username] == password:
            st.session_state.logged_in = True
            st.session_state.page = "patients"
            st.success("Login successful ✅")
            st.rerun()
        else:
            st.error("Invalid username or password ❌")

def patients_page():
    st.title("👨‍⚕️ Patients")

    if st.button("🔙 Logout"):
        st.session_state.logged_in = False
        st.session_state.page = "login"
        st.rerun()

    st.subheader("📂 Upload Patient Data (Excel)")
    uploaded_file = st.file_uploader("Choose an Excel file", type=["xlsx", "xls"])
    if uploaded_file is not None:
        df = pd.read_excel(uploaded_file)
        save_uploaded_data(df)
        st.success("✅ Data uploaded successfully!")
        st.dataframe(df)

    if st.button("➕ Add New Patient"):
        st.session_state.show_form = True

    if st.session_state.show_form:
        st.subheader("📝 Enter Patient Details")
        with st.form("manual_form"):
            name = st.text_input("Name")
            age = st.number_input("Age", min_value=0, max_value=120)
            gender = st.selectbox("Gender", ["Male", "Female", "Other"])
            weight = st.number_input("Weight (kg)", min_value=0.0)
            height = st.number_input("Height (cm)", min_value=0.0)
            email = st.text_input("Emergency Email")
            heart_rate = st.number_input("Heart Rate (BPM)", min_value=0)
            temperature = st.number_input("Temperature (°C)", min_value=25.0, max_value=45.0)
            oxygen = st.number_input("Oxygen (%)", min_value=0, max_value=100)
            systolic = st.number_input("Systolic (mmHg)", min_value=0)
            diastolic = st.number_input("Diastolic (mmHg)", min_value=0)

            submitted = st.form_submit_button("✅ Save Patient")
            if submitted:
                bmi = round(weight / ((height/100)**2), 2) if height > 0 else 0
                patient = {
                    "name": name, "age": age, "gender": gender, "weight": weight, "height": height,
                    "email": email, "heart_rate": heart_rate, "temperature": temperature,
                    "oxygen": oxygen, "systolic": systolic, "diastolic": diastolic, "bmi": bmi
                }
                save_manual_patient(patient)
                st.success(f"✅ Patient {name} added successfully")
                st.session_state.show_form = False
                st.rerun()

    df = get_patients()
    if not df.empty:
        st.markdown("### Patient List")
        st.dataframe(df)
        for i, row in df.iterrows():
            if st.button(f"View {row['name']} Metrics", key=f"view_{i}"):
                st.session_state.selected_patient = row
                st.session_state.page = "dashboard"
                st.rerun()
    else:
        st.info("ℹ️ No patients found.")

def dashboard_page():
    load_css()
    patient = st.session_state.selected_patient
    st.title("📊 Health Dashboard")

    if st.button("⬅️ Back to Patients"):
        st.session_state.page = "patients"
        st.rerun()

    st.subheader(f"Patient: {patient['name']}")

    # --- Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("❤️ Heart Rate", f"{patient['heart_rate']} BPM")
    col2.metric("🌡️ Temperature", f"{patient['temperature']} °C")
    col3.metric("🫁 Oxygen", f"{patient['oxygen']} %")

    col4, col5, col6 = st.columns(3)
    col4.metric("⚖️ BMI", f"{round(patient['bmi'], 2)}")
    col5.metric("🩸 BP", f"{patient['systolic']}/{patient['diastolic']} mmHg")
    col6.metric("Age", f"{patient['age']} yrs")

    # --- Risks
    st.subheader("📝 Risk Analysis")
    risks = get_risk_explanations(patient)
    for r in risks:
        st.write(r)

    if st.button("📤 Send Report to Slack"):
        send_slack_report(patient, risks)

    pdf_buffer = generate_pdf_report(patient, risks)
    st.download_button(
        "📥 Download Report (PDF)",
        data=pdf_buffer,
        file_name=f"{patient['name']}_report.pdf",
        mime="application/pdf"
    )

# ---------------------------
# Main Router
# ---------------------------
init_db()

if st.session_state.page == "login":
    login_page()
elif st.session_state.page == "patients":
    patients_page()
elif st.session_state.page == "dashboard":
    dashboard_page()
