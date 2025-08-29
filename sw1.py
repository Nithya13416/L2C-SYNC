import streamlit as st
import random

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
if "patients" not in st.session_state:
    st.session_state.patients = [
        {"name": "Saif Ben Hmida", "age": 54, "gender": "Male", "weight": 62, "height": 168, "email": "ss@gmail.com"},
        {"name": "John Doe", "age": 45, "gender": "Male", "weight": 75, "height": 172, "email": "john@gmail.com"},
        {"name": "Jane Smith", "age": 38, "gender": "Female", "weight": 58, "height": 160, "email": "jane@gmail.com"},
    ]

# ---------------------------
# Inject CSS for Styling
# ---------------------------
def load_css():
    st.markdown(
        """
        <style>
        /* General */
        .block-container {
            max-width: 1100px;
            padding-top: 2rem;
        }
        h1, h2, h3 {
            font-family: 'Segoe UI', sans-serif;
        }

        /* Card Style */
        .card {
            background-color: white;
            border-radius: 16px;
            padding: 20px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            margin-bottom: 20px;
            text-align: center;
        }
        .card h4 {
            margin-bottom: 10px;
        }
        .metric-value {
            font-size: 26px;
            font-weight: bold;
            margin-top: 10px;
        }
        .status {
            font-size: 14px;
            margin-top: 6px;
            padding: 4px 10px;
            border-radius: 12px;
            display: inline-block;
        }
        .normal { background: #d4f8d4; color: #2e7d32; }
        .good { background: #d0f0ff; color: #0277bd; }
        .low { background: #ffe0e0; color: #c62828; }
        </style>
        """,
        unsafe_allow_html=True,
    )

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
# Patients List Page
# ---------------------------
def patients_page():
    st.title("👨‍⚕️ My Patients")

    if st.button("🔙 Logout"):
        st.session_state.logged_in = False
        st.session_state.page = "login"
        st.rerun()

    # Search and Reset
    st.markdown("### Filters:")
    search_term = st.text_input("Search Users")
    if st.button("Reset"):
        search_term = ""

    # Filter patients
    filtered_patients = [
        p for p in st.session_state.patients if search_term.lower() in p["name"].lower()
    ]

    # Patients list
    for i, patient in enumerate(filtered_patients):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(patient["name"])
        with col2:
            if st.button("View User Metrics", key=f"view_{i}"):
                st.session_state.selected_patient = patient
                st.session_state.page = "dashboard"
                st.rerun()

    # Add new patient
    with st.expander("➕ Add New Patient"):
        name = st.text_input("Full Name")
        age = st.number_input("Age", min_value=1, max_value=120, step=1)
        gender = st.selectbox("Gender", ["Male", "Female", "Other"])
        weight = st.number_input("Weight (kg)", min_value=1, max_value=200)
        height = st.number_input("Height (cm)", min_value=50, max_value=220)
        email = st.text_input("Email")

        if st.button("Add Patient"):
            if name and email:
                st.session_state.patients.append(
                    {"name": name, "age": age, "gender": gender,
                     "weight": weight, "height": height, "email": email}
                )
                st.success(f"Patient {name} added successfully ✅")
                st.rerun()
            else:
                st.error("Name and Email are required ❌")

# ---------------------------
# Dashboard Page (with random health metrics)
# ---------------------------
def dashboard_page():
    load_css()
    patient = st.session_state.selected_patient

    st.title("📊 Smartwatch Health Dashboard")

    if st.button("🔙 Return"):
        st.session_state.page = "patients"
        st.rerun()

    st.subheader(f"Welcome Back Doctor - Patient: {patient['name']}")

    # Generate random readings
    heart_rate = random.randint(60, 120)
    temperature = round(random.uniform(35.5, 38.5), 1)
    oxygen = random.randint(85, 100)
    systolic = random.randint(100, 150)
    diastolic = random.randint(60, 95)
    bmi = round(patient["weight"] / ((patient["height"]/100) ** 2), 2)

    # First row
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            f"""
            <div class="card">
                <h4>❤️ Heart Rate</h4>
                <div class="metric-value">{heart_rate} BPM</div>
                <div class="status {'normal' if 60 <= heart_rate <= 100 else 'low'}">
                    {'Normal' if 60 <= heart_rate <= 100 else 'Alert'}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f"""
            <div class="card">
                <h4>👤 Patient Info</h4>
                <p>{patient['name']}</p>
                <p>Emergency: {patient['email']}</p>
                <p>Age: {patient['age']} | Gender: {patient['gender']}</p>
                <p>Weight: {patient['weight']} | Height: {patient['height']}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            f"""
            <div class="card">
                <h4>🌡️ Temperature</h4>
                <div class="metric-value">{temperature}°C</div>
                <div class="status {'good' if 36 <= temperature <= 37.5 else 'low'}">
                    {'Good' if 36 <= temperature <= 37.5 else 'Alert'}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Second row
    col4, col5, col6 = st.columns(3)
    with col4:
        st.markdown(
            f"""
            <div class="card">
                <h4>BMI</h4>
                <div class="metric-value">{bmi}</div>
                <div class="status {'normal' if 18.5 <= bmi <= 24.9 else 'low'}">
                    {'Normal' if 18.5 <= bmi <= 24.9 else 'Alert'}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col5:
        st.markdown(
            f"""
            <div class="card">
                <h4>🩸 Blood Pressure</h4>
                <div class="metric-value">{systolic}/{diastolic}</div>
                <div class="status {'normal' if systolic<140 and diastolic<90 else 'low'}">
                    {'Normal' if systolic<140 and diastolic<90 else 'Alert'}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col6:
        st.markdown(
            f"""
            <div class="card">
                <h4>Oxygen Level</h4>
                <div class="metric-value">{oxygen}%</div>
                <div class="status {'normal' if oxygen>=95 else 'low'}">
                    {'Normal' if oxygen>=95 else 'Low'}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ---------------------------
# Main Router
# ---------------------------
if st.session_state.page == "login":
    login_page()
elif st.session_state.page == "patients":
    patients_page()
elif st.session_state.page == "dashboard":
    dashboard_page()
