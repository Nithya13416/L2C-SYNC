import streamlit as st
import pandas as pd
import sqlite3
import datetime
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

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
            diastolic INTEGER, bmi REAL, uploaded_at TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_uploaded_data(df):
    # ✅ calculate BMI column
    df["bmi"] = df.apply(lambda x: round(x["Weight"] / ((x["Height"]/100)**2), 2), axis=1)
    df["uploaded_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # rename to match DB schema
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

    conn = sqlite3.connect("patients.db")
    df.to_sql("patients_data", conn, if_exists="append", index=False)
    conn.close()

def get_patients():
    conn = sqlite3.connect("patients.db")
    df = pd.read_sql("SELECT * FROM patients_data", conn)
    conn.close()
    return df

# ---------------------------
# PDF Export Helper
# ---------------------------
def generate_pdf(patient):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    textobject = c.beginText(50, 750)
    textobject.setFont("Helvetica", 12)

    textobject.textLine(f"Patient Report - {patient['name']}")
    textobject.textLine(f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    textobject.textLine("")
    for key, value in patient.items():
        textobject.textLine(f"{key}: {value}")

    c.drawText(textobject)
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

# ---------------------------
# Login Page
# ---------------------------
def login_page():
    col1, col2 = st.columns([2, 1])
    with col1:
        st.image(
            "https://img.freepik.com/free-vector/health-professional-team-with-heart_23-2148503275.jpg",
            use_container_width=True
        )
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
        st.dataframe(df)

    # Show patient list if DB has data
    try:
        df = get_patients()

        # 🔥 Summary bar: how many are alert?
        normal_count = df[
            (df["heart_rate"].between(60, 100)) &
            (df["temperature"].between(36, 37.5)) &
            (df["oxygen"] >= 95) &
            (df["systolic"] < 140) & (df["diastolic"] < 90)
        ].shape[0]
        alert_count = len(df) - normal_count

        col1, col2 = st.columns(2)
        col1.metric("✅ Normal Patients", normal_count)
        col2.metric("⚠️ Alert Patients", alert_count, delta=alert_count)

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

    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("🔙 Return to Patients"):
            st.session_state.page = "patients"
            st.rerun()
    with col2:
        if st.button("🔑 Back to Login"):
            st.session_state.page = "login"
            st.rerun()
    with col3:
        # 🔽 Export options
        csv = patient.to_frame().T.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download CSV", csv, "report.csv", "text/csv")

        pdf_buf = generate_pdf(patient)
        st.download_button("⬇️ Download PDF", pdf_buf, "report.pdf", "application/pdf")

    st.subheader(f"Patient: {patient['name']}")

    # Profile section
    st.image("https://cdn-icons-png.flaticon.com/512/2922/2922510.png", width=120)
    st.write(f"**Age:** {patient['age']} | **Gender:** {patient['gender']}")
    st.write(f"**Weight:** {patient['weight']} kg | **Height:** {patient['height']} cm")
    st.write(f"**Emergency Contact:** {patient['email']}")

    # ✅ Vital Cards
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("❤️ Heart Rate", f"{patient['heart_rate']} BPM",
                  "Normal" if 60 <= patient['heart_rate'] <= 100 else "⚠️")
    with col2:
        st.metric("🌡️ Temperature", f"{patient['temperature']} °C",
                  "Good" if 36 <= patient['temperature'] <= 37.5 else "⚠️")
    with col3:
        st.metric("🩸 Oxygen", f"{patient['oxygen']}%",
                  "Normal" if patient['oxygen'] >= 95 else "Low")

    # ✅ Charts for trends
    df = get_patients()
    patient_history = df[df["name"] == patient["name"]].sort_values("uploaded_at")

    if not patient_history.empty and len(patient_history) > 1:
        st.subheader("📈 Vitals Trend Over Time")
        st.line_chart(patient_history[["heart_rate", "systolic", "diastolic", "oxygen"]].set_index(patient_history["uploaded_at"]))

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
