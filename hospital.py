import streamlit as st
import pandas as pd
import sqlite3
import datetime
import io
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import requests

# ----------------------------
# Slack Webhook (replace with your own)
# ----------------------------
SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/xxxx/xxxx/xxxx"

# ----------------------------
# Dummy Users
# ----------------------------
USERS = {
    "doctor111": "password123",
    "nurse222": "pass456",
}

# ----------------------------
# Database Functions
# ----------------------------
def init_db():
    conn = sqlite3.connect("patients.db")
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.close()

def save_uploaded_data(df):
    conn = sqlite3.connect("patients.db")

    # 1) Always keep a fresh snapshot (overwrite every upload)
    df.to_sql("patients_data", conn, if_exists="replace", index=False)

    # 2) Append a copy to the history table with a timestamp
    df_hist = df.copy()
    df_hist["uploaded_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    df_hist.to_sql("patients_data_history", conn, if_exists="append", index=False)

    conn.close()

def load_patients():
    conn = sqlite3.connect("patients.db")
    try:
        df = pd.read_sql("SELECT * FROM patients_data", conn)
    except:
        df = pd.DataFrame()
    conn.close()
    return df

def load_history():
    conn = sqlite3.connect("patients.db")
    try:
        df = pd.read_sql("SELECT * FROM patients_data_history", conn)
    except:
        df = pd.DataFrame()
    conn.close()
    return df

# ----------------------------
# Slack Notification
# ----------------------------
def send_slack_alert(message):
    payload = {"text": message}
    try:
        requests.post(SLACK_WEBHOOK_URL, json=payload)
    except Exception as e:
        st.error(f"Slack Error: {e}")

# ----------------------------
# PDF Report
# ----------------------------
def generate_pdf(patient):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    c.setFont("Helvetica", 14)
    c.drawString(50, 800, "Patient Report")
    c.setFont("Helvetica", 12)
    y = 770
    for key, value in patient.items():
        c.drawString(50, y, f"{key}: {value}")
        y -= 20
    c.save()
    buffer.seek(0)
    return buffer

# ----------------------------
# Login Page
# ----------------------------
def login():
    st.title("🔐 Login to The Heartbeat")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username in USERS and USERS[username] == password:
            st.session_state["logged_in"] = True
            st.success("✅ Login Successful!")
        else:
            st.error("❌ Invalid username or password")

# ----------------------------
# Patients Page
# ----------------------------
def patients_page():
    st.title("🏥 Patient Dashboard")

    # Upload Excel
    uploaded_file = st.file_uploader("📂 Upload Patient Data (Excel)", type=["xlsx", "xls"])
    if uploaded_file:
        df = pd.read_excel(uploaded_file)
        save_uploaded_data(df)
        st.success("✅ Patient data uploaded successfully!")

    # Load current patients
    df = load_patients()

    if not df.empty:
        search = st.text_input("🔍 Search Patients")
        if search:
            df = df[df["Name"].str.contains(search, case=False, na=False)]

        st.subheader("Patient List:")
        for _, row in df.iterrows():
            with st.container():
                st.write(f"👤 {row['Name']} ({row['Age']} yrs)")
                if st.button(f"View Metrics - {row['Name']}"):
                    st.json(row.to_dict())
                    pdf = generate_pdf(row.to_dict())
                    st.download_button("⬇ Download Report (PDF)", pdf, file_name=f"{row['Name']}_report.pdf")

                    # Example Slack alert
                    send_slack_alert(f"⚠ Alert: {row['Name']} data was accessed.")

    else:
        st.info("📌 No patient data available. Upload an Excel file.")

# ----------------------------
# History Page
# ----------------------------
def history_page():
    st.title("🕒 Upload History")
    df = load_history()
    if not df.empty:
        st.dataframe(df)
        st.download_button("⬇ Download History (CSV)", df.to_csv(index=False), "history.csv")
    else:
        st.info("📌 No history available yet.")

# ----------------------------
# Main App
# ----------------------------
def main():
    st.sidebar.title("📌 Navigation")
    menu = ["Home", "Patients", "Upload History"]
    choice = st.sidebar.radio("Go to", menu)

    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    if not st.session_state["logged_in"]:
        login()
    else:
        if choice == "Home":
            st.title("❤️ The Heartbeat - Home")
            st.write("Welcome to the patient monitoring dashboard.")
        elif choice == "Patients":
            patients_page()
        elif choice == "Upload History":
            history_page()

if __name__ == "__main__":
    init_db()
    main()
