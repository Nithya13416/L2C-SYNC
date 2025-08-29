import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

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
            diastolic INTEGER, bmi REAL,
            uploaded_at TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_uploaded_data(df):
    # ✅ calculate BMI column
    df["bmi"] = df.apply(lambda x: round(x["Weight"] / ((x["Height"]/100)**2), 2), axis=1)

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

    # add uploaded_at timestamp
    df["uploaded_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = sqlite3.connect("patients.db")
    df.to_sql("patients_data", conn, if_exists="append", index=False)
    conn.close()

def get_patients():
    conn = sqlite3.connect("patients.db")
    df = pd.read_sql("SELECT * FROM patients_data", conn)
    conn.close()
    return df

def get_patient_history(name):
    conn = sqlite3.connect("patients.db")
    df = pd.read_sql("SELECT * FROM patients_data WHERE name = ?", conn, params=(name,))
    conn.close()
    return df

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
# Vital Check Helper
# ---------------------------
def check_vitals(row):
    issues = []

    # Heart rate
    if row["heart_rate"] < 60 or row["heart_rate"] > 100:
        issues.append("Heart Rate")

    # Temperature
    if row["temperature"] < 36 or row["temperature"] > 37.5:
        issues.append("Temperature")

    # Oxygen
    if row["oxygen"] < 95:
        issues.append("Oxygen")

    # Blood pressure
    if row["systolic"] >= 140 or row["diastolic"] >= 90:
        issues.append("Blood Pressure")

    # BMI
    if row["bmi"] < 18.5 or row["bmi"] > 24.9:
        issues.append("BMI")

    return issues

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

    # Get patient history
    df_hist = get_patient_history(patient['name'])

    # ---- NEW ALERT LOGIC ----
    issues = check_vitals(patient)
    if len(issues) == 0:
        st.success("✅ Status: Normal")
    elif len(issues) == 1:
        st.warning(f"⚠️ Status: Mild Alert ({issues[0]})")
    else:
        st.error(f"🚨 Status: Critical Alert (Problems with {', '.join(issues)})")

    # Trends
    if not df_hist.empty:
        st.markdown("### 📈 Health Trends")
        st.line_chart(df_hist.set_index("uploaded_at")[["heart_rate", "temperature", "oxygen"]])

    # Show detailed metrics (cards)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
            <div class="card">
                <h4>❤️ Heart Rate</h4>
                <div class="metric-value">{patient['heart_rate']} BPM</div>
            </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
            <div class="card">
                <h4>👤 Patient Info</h4>
                <p>{patient['name']}</p>
                <p>Emergency: {patient['email']}</p>
                <p>Age: {patient['age']} | Gender: {patient['gender']}</p>
                <p>Weight: {patient['weight']} | Height: {patient['height']}</p>
            </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
            <div class="card">
                <h4>🌡️ Temperature</h4>
                <div class="metric-value">{patient['temperature']}°C</div>
            </div>
        """, unsafe_allow_html=True)

    col4, col5, col6 = st.columns(3)
    with col4:
        st.markdown(f"""
            <div class="card">
                <h4>BMI</h4>
                <div class="metric-value">{round(patient['bmi'], 2)}</div>
            </div>
        """, unsafe_allow_html=True)
    with col5:
        st.markdown(f"""
            <div class="card">
                <h4>🩸 Blood Pressure</h4>
                <div class="metric-value">{patient['systolic']}/{patient['diastolic']}</div>
            </div>
        """, unsafe_allow_html=True)
    with col6:
        st.markdown(f"""
            <div class="card">
                <h4>Oxygen Level</h4>
                <div class="metric-value">{patient['oxygen']}%</div>
            </div>
        """, unsafe_allow_html=True)

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
