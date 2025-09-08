import streamlit as st
import pandas as pd
import sqlite3
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io
import requests   # ✅ for Slack Webhook
import os

# ---------------------------
# Dummy Users
# ---------------------------
USERS = {
    "doctor111": "password123",
    "nurse222": "pass456",
}

# ---------------------------
# Slack Webhook URL
# ---------------------------
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")  # Load from environment

def send_slack_message(message: str):
    """Send a message to Slack if webhook URL is configured"""
    if SLACK_WEBHOOK_URL:
        try:
            response = requests.post(
                SLACK_WEBHOOK_URL, json={"text": message},
                headers={"Content-Type": "application/json"}
            )
            if response.status_code != 200:
                st.error(f"Slack error: {response.text}")
        except Exception as e:
            st.error(f"Slack send failed: {e}")

# ---------------------------
# Session State Initialization
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
# Load CSS
# ---------------------------
def load_css():
    st.markdown(
        """
        <style>
        .block-container { max-width: 1100px; padding-top: 2rem; }
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
# Database Functions
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
    df.to_sql("patients_data", conn, if_exists="replace", index=False)
    conn.close()

    # 🔔 Slack notify
    send_slack_message(f"📂 {len(df)} patients uploaded via Excel.")

def get_patients():
    conn = sqlite3.connect("patients.db")
    df = pd.read_sql("SELECT * FROM patients_data", conn)
    conn.close()
    return df

# ---------------------------
# Health Risk Analysis
# ---------------------------
def get_risk_explanations(patient):
    risks = []
    if not (60 <= patient['heart_rate'] <= 100):
        risks.append("⚠️ Abnormal Heart Rate")
    if not (36 <= patient['temperature'] <= 37.5):
        risks.append("🌡️ Abnormal Temperature")
    if not (18.5 <= patient['bmi'] <= 24.9):
        risks.append("⚖️ Unhealthy BMI")
    if not (patient['systolic'] < 140 and patient['diastolic'] < 90):
        risks.append("🩸 High Blood Pressure")
    if patient['oxygen'] < 95:
        risks.append("🫁 Low Oxygen Level")
    if not risks:
        risks.append("✅ All vitals are normal.")
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
# Login Page
# ---------------------------
def login_page():
    col1, col2 = st.columns([2, 1])
    with col1:
        st.image("https://img.freepik.com/free-vector/health-professional-team-with-heart_23-2148503275.jpg", use_container_width=True)
    with col2:
        st.markdown("### Sign in")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("🔐 Sign In with Username"):
            if username in USERS and USERS[username] == password:
                st.session_state.logged_in = True
                st.session_state.page = "patients"
                st.success("Login successful ✅")
                st.rerun()
            else:
                st.error("Invalid username or password ❌")

# ---------------------------
# Patients Page
# ---------------------------
def patients_page():
    st.title("👨‍⚕️ My Patients")

    if st.button("🔙 Logout"):
        st.session_state.logged_in = False
        st.session_state.page = "login"
        st.rerun()

    # Add Patient Button
    if not st.session_state.show_form:
        if st.button("➕ Add New Patient"):
            st.session_state.show_form = True
            st.rerun()
    else:
        st.subheader("✍️ Enter New Patient Details")
        with st.form("manual_entry_form"):
            name = st.text_input("Name")
            age = st.number_input("Age", min_value=0, max_value=120, step=1)
            gender = st.selectbox("Gender", ["Male", "Female", "Other"])
            weight = st.number_input("Weight (kg)", min_value=1.0, step=0.1)
            height = st.number_input("Height (cm)", min_value=30.0, step=0.1)
            email = st.text_input("Emergency Email")
            heart_rate = st.number_input("Heart Rate (BPM)", min_value=20, max_value=200, step=1)
            temperature = st.number_input("Temperature (°C)", min_value=30.0, max_value=45.0, step=0.1)
            oxygen = st.number_input("Oxygen Level (%)", min_value=50, max_value=100, step=1)
            systolic = st.number_input("Systolic BP", min_value=50, max_value=250, step=1)
            diastolic = st.number_input("Diastolic BP", min_value=30, max_value=150, step=1)

            submitted = st.form_submit_button("✅ Save Patient")
            cancel = st.form_submit_button("❌ Cancel")

            if submitted:
                bmi = round(weight / ((height / 100) ** 2), 2)
                conn = sqlite3.connect("patients.db")
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO patients_data 
                    (name, age, gender, weight, height, email, heart_rate, temperature, oxygen, systolic, diastolic, bmi)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (name, age, gender, weight, height, email, heart_rate, temperature, oxygen, systolic, diastolic, bmi))
                conn.commit()
                conn.close()

                st.success(f"✅ Patient {name} added successfully!")
                st.session_state.show_form = False

                # 🔔 Slack notify
                send_slack_message(f"👤 New Patient Added: {name}, Age {age}, HR {heart_rate}, Temp {temperature}")

                st.rerun()
            if cancel:
                st.session_state.show_form = False
                st.rerun()

    # Upload Excel
    st.subheader("📂 Upload Patient Data (Excel)")
    uploaded_file = st.file_uploader("Choose an Excel file", type=["xlsx", "xls"])
    if uploaded_file is not None:
        df = pd.read_excel(uploaded_file)
        save_uploaded_data(df)
        st.dataframe(df)

    # Patient List
    try:
        df = get_patients()
        st.markdown("### Patient List:")
        for i, row in df.iterrows():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"👤 {row['name']} ({row['age']} yrs)")
            with col2:
                if st.button("View Metrics", key=f"view_{i}"):
                    st.session_state.selected_patient = row
                    st.session_state.page = "dashboard"
                    st.rerun()
    except Exception:
        st.info("ℹ️ No patient data found. Please upload or add manually.")

# ---------------------------
# Dashboard Page
# ---------------------------
def dashboard_page():
    load_css()
    patient = st.session_state.selected_patient
    st.title("📊 Smartwatch Health Dashboard")

    if st.button("🔙 Return to Patients"):
        st.session_state.page = "patients"
        st.rerun()

    st.subheader(f"Patient: {patient['name']}")

    # Risks
    risks = get_risk_explanations(patient)
    st.subheader("📝 Detailed Risk Analysis")
    for r in risks:
        st.write(r)

    # 🔔 Slack alert for abnormal vitals
    if any("⚠️" in r or "🌡️" in r or "🩸" in r or "🫁" in r for r in risks):
        send_slack_message(f"🚨 Alert: {patient['name']} has risks! {', '.join(risks)}")

    # PDF
    pdf_buffer = generate_pdf_report(patient, risks)
    st.download_button(
        label="📥 Download Patient Report (PDF)",
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
