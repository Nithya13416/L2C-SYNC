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

    # Example patients
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
    patient = st.session_state.selected_patient

    st.title("📊 Smartwatch Health Dashboard")

    if st.button("🔙 Return"):
        st.session_state.page = "patients"
        st.rerun()

    st.subheader(f"Welcome Back Doctor - Patient: {patient['name']}")

    # Cards Layout
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("#### Heart Rate")
        st.metric(label="Status", value="77 BPM", delta="Normal")
    with col2:
        st.markdown("#### Patient Info")
        st.text(patient["name"])
        st.text(f"Emergency Contact : {patient['email']}")
        st.text(f"Age: {patient['age']} | Gender: {patient['gender']}")
        st.text(f"Weight: {patient['weight']} | Height: {patient['height']}")
    with col3:
        st.markdown("#### Temperature")
        st.metric(label="Body Temp", value="36°C", delta="Good")

    col4, col5, col6 = st.columns(3)
    with col4:
        st.markdown("#### BMI")
        st.metric(label="Index", value="21.97", delta="Normal")
    with col5:
        st.markdown("#### Blood Pressure")
        st.metric(label="SYS/DIA", value="139/79", delta="Normal")
    with col6:
        st.markdown("#### Oxygen Level")
        st.metric(label="SpO₂", value="93%", delta="Low")

# ---------------------------
# Main Router
# ---------------------------
if st.session_state.page == "login":
    login_page()
elif st.session_state.page == "patients":
    patients_page()
elif st.session_state.page == "dashboard":
    dashboard_page()
