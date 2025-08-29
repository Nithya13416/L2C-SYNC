import streamlit as st
import os
import pandas as pd
import sqlite3
import datetime
import io
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from dotenv import load_dotenv
import requests


SLACK_WEBHOOK_URL2 = os.getenv("SLACK_WEBHOOK_URL2", "").strip()
# ---------------------------
# Dummy Users
# ---------------------------
USERS = {
    "doctor111": "password123",
    "nurse222": "pass456",
}

# ---------------------------
# Session State Initialization
# ---------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "page" not in st.session_state:
    st.session_state.page = "login"
if "selected_patient" not in st.session_state:
    st.session_state.selected_patient = None

# ---------------------------
# Load CSS for styling
# ---------------------------
def load_css():
    st.markdown(
        """
        <style>
        .block-container { max-width: 1200px; padding-top: 2rem; }
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
# Database Helper Functions
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
            diastolic INTEGER, bmi REAL,
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_uploaded_data(df):
    df["bmi"] = df.apply(lambda x: round(x["Weight"] / ((x["Height"]/100)**2), 2), axis=1)
    df = df.rename(columns={
        "Name": "name",
        "Age": "age",
        "Gender": "gender",
        "Weight": "weight",
        "Height": "height",
        "Email": "email",
        "HeartRate": "heart_rate",
        "Temperature": "temperature",
        "Oxygen": "oxygen",
        "Systolic": "systolic",
        "Diastolic": "diastolic"
    })
    df["timestamp"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect("patients.db")
    df.to_sql("patients_data", conn, if_exists="append", index=False)  # ✅ append instead of replace
    conn.close()

def get_patients():
    conn = sqlite3.connect("patients.db")
    df = pd.read_sql("SELECT * FROM patients_data", conn)
    conn.close()
    return df

# ---------------------------
# PDF Report Generator
# ---------------------------
def generate_pdf(patient):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    c.setFont("Helvetica", 14)
    c.drawString(100, 800, f"Patient Health Report - {patient['name']}")
    c.setFont("Helvetica", 12)
    y = 760
    for key, value in patient.items():
        c.drawString(100, y, f"{key}: {value}")
        y -= 20
    c.save()
    buffer.seek(0)
    return buffer

# ---------------------------
# Slack Alerts
# ---------------------------
def send_slack_alert(patient, message):
    data = {
        "text": f"🚨 Alert for {patient['name']} ({patient['age']} yrs)\n{message}"
    }
    requests.post(SLACK_WEBHOOK_URL2, json=data)

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

    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("🔙 Logout"):
            st.session_state.logged_in = False
            st.session_state.page = "login"
            st.rerun()
    with col2:
        if st.button("🔑 Back to Login"):
            st.session_state.page = "login"
            st.rerun()

    # Upload Excel file
    st.subheader("📂 Upload Patient Data (Excel)")
    uploaded_file = st.file_uploader("Choose an Excel file", type=["xlsx", "xls"])
    if uploaded_file is not None:
        df = pd.read_excel(uploaded_file)
        save_uploaded_data(df)
        st.success("✅ Data uploaded & saved successfully!")

    # Patient Search
    st.subheader("🔍 Search Patients")
    search_name = st.text_input("Enter patient name to search")
    
    # Show patient list if DB has data
    try:
        df = get_patients()
        if search_name:
            df = df[df['name'].str.contains(search_name, case=False, na=False)]
        
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
        st.info("ℹ️ No patient data found. Please upload an Excel file.")

# ---------------------------
# Dashboard Page
# ---------------------------
def dashboard_page():
    load_css()
    patient = st.session_state.selected_patient
    st.title("📊 Smartwatch Health Dashboard")

    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("🔙 Return to Patients"):
            st.session_state.page = "patients"
            st.rerun()
    with col2:
        if st.button("📄 Download PDF Report"):
            pdf = generate_pdf(patient)
            st.download_button("Download Report", data=pdf, file_name=f"{patient['name']}_report.pdf")

    st.subheader(f"Patient: {patient['name']}")

    # Gamified summary
    alerts = []
    if not (60 <= patient['heart_rate'] <= 100): alerts.append("❤️ Heart Rate")
    if not (36 <= patient['temperature'] <= 37.5): alerts.append("🌡️ Temperature")
    if not (95 <= patient['oxygen']): alerts.append("🫁 Oxygen")
    if not (patient['systolic'] < 140 and patient['diastolic'] < 90): alerts.append("🩸 Blood Pressure")
    if not (18.5 <= patient['bmi'] <= 24.9): alerts.append("⚖️ BMI")

    if alerts:
        st.error(f"🚨 Critical Issues: {', '.join(alerts)}")
        send_slack_alert(patient, f"Critical health issues detected: {', '.join(alerts)}")
    else:
        st.success("✅ Patient vitals are normal.")

    # Charts (history)
    history = get_patients()
    history = history[history['name'] == patient['name']]
    st.line_chart(history.set_index("timestamp")[["heart_rate", "oxygen", "temperature"]])

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
