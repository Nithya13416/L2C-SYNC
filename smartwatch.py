import streamlit as st

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
    st.title("👨‍⚕️ Patients List")

    if st.button("🔙 Logout"):
        st.session_state.logged_in = False
        st.session_state.page = "login"
        st.rerun()

    patients = [
        {"name": "Saif Ben Hmida", "age": 54, "gender": "Male", "weight": 62, "height": 168, "email": "ss@gmail.com"},
        {"name": "John Doe", "age": 45, "gender": "Male", "weight": 75, "height": 172, "email": "john@gmail.com"},
    ]

    for i, patient in enumerate(patients):
        if st.button(f"📋 View {patient['name']}'s Dashboard", key=i):
            st.session_state.selected_patient = patient
            st.session_state.page = "dashboard"
            st.rerun()

# ---------------------------
# Dashboard Page
# ---------------------------
def dashboard_page():
    load_css()
    patient = st.session_state.selected_patient

    st.title("📊 Smartwatch Health Dashboard")

    if st.button("🔙 Return"):
        st.session_state.page = "patients"
        st.rerun()

    st.subheader(f"Welcome Back Doctor - Patient: {patient['name']}")

    # First row
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            f"""
            <div class="card">
                <h4>❤️ Heart Rate</h4>
                <div class="metric-value">77 BPM</div>
                <div class="status normal">Normal</div>
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
                <div class="metric-value">36°C</div>
                <div class="status good">Good</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Second row
    col4, col5, col6 = st.columns(3)
    with col4:
        st.markdown(
            """
            <div class="card">
                <h4>BMI</h4>
                <div class="metric-value">21.97</div>
                <div class="status normal">Normal</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col5:
        st.markdown(
            """
            <div class="card">
                <h4>🩸 Blood Pressure</h4>
                <div class="metric-value">139/79</div>
                <div class="status normal">Normal</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col6:
        st.markdown(
            """
            <div class="card">
                <h4>Oxygen Level</h4>
                <div class="metric-value">93%</div>
                <div class="status low">Low</div>
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
