import streamlit as st

# -------------------
# Dummy Users
# -------------------
USERS = {"doctor111": "password123"}

# -------------------
# Dummy Patients
# -------------------
PATIENTS = {
    "saif": {
        "name": "saif ben hmida",
        "email": "ss@gmail.com",
        "age": 54,
        "gender": "Men",
        "weight": 62,
        "height": 168,
        "heart_rate": 77,
        "temperature": 36,
        "bmi": 21.97,
        "bp_sys": 139,
        "bp_dia": 79,
        "oxygen": 93,
    }
}

# -------------------
# Session Init
# -------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "page" not in st.session_state:
    st.session_state.page = "login"
if "selected_patient" not in st.session_state:
    st.session_state.selected_patient = None

# -------------------
# LOGIN PAGE
# -------------------
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
                st.experimental_rerun()
            else:
                st.error("Invalid username or password ❌")

# -------------------
# PATIENT SELECTION PAGE
# -------------------
def patients_page():
    st.title("👩‍⚕️ Patients List")
    for pid, details in PATIENTS.items():
        if st.button(f"📂 {details['name']}"):
            st.session_state.selected_patient = pid
            st.session_state.page = "dashboard"
            st.experimental_rerun()

# -------------------
# DASHBOARD PAGE
# -------------------
def dashboard_page():
    patient = PATIENTS[st.session_state.selected_patient]

    # Top navigation
    col1, col2, col3 = st.columns([1, 3, 1])
    with col1:
        if st.button("⬅️ Return"):
            st.session_state.page = "patients"
            st.experimental_rerun()
    with col2:
        st.subheader("Dashboard")
    with col3:
        st.text_input("🔍 Search...")

    st.markdown(f"## Welcome Back Doctor")

    # Layout
    col1, col2, col3 = st.columns(3)

    # Heart Rate
    with col1:
        st.markdown("### Heart Rate")
        st.metric(label="", value=f"{patient['heart_rate']} BPM")
        st.success("Normal" if 60 <= patient['heart_rate'] <= 100 else "Abnormal")

    # Patient Info (Center)
    with col2:
        st.markdown("### Patient Info")
        st.markdown(f"**{patient['name']}**")
        st.markdown(f"📧 {patient['email']}")
        st.write(f"**Age:** {patient['age']} | **Gender:** {patient['gender']}")
        st.write(f"**Weight:** {patient['weight']} | **Height:** {patient['height']}")

    # Temperature
    with col3:
        st.markdown("### Temperature")
        st.metric(label="", value=f"{patient['temperature']}°C")
        st.success("Good" if 36 <= patient['temperature'] <= 37 else "Bad")

    # Second row
    col4, col5, col6 = st.columns(3)

    # BMI
    with col4:
        st.markdown("### BMI")
        st.metric(label="", value=f"{patient['bmi']:.2f}")
        st.success("Normal" if 18.5 <= patient['bmi'] <= 24.9 else "Abnormal")

    # Blood Pressure
    with col5:
        st.markdown("### Systolic & Diastolic Pressure")
        st.write(f"**Sys:** {patient['bp_sys']}")
        st.write(f"**Dia:** {patient['bp_dia']}")
        if patient['bp_sys'] < 140 and patient['bp_dia'] < 90:
            st.success("Normal")
        else:
            st.error("High")

    # Oxygen
    with col6:
        st.markdown("### Oxygen Level")
        st.metric(label="", value=f"{patient['oxygen']}%")
        st.success("Good" if patient['oxygen'] >= 95 else "Low")

# -------------------
# MAIN APP
# -------------------
if not st.session_state.logged_in:
    login_page()
else:
    if st.session_state.page == "patients":
        patients_page()
    elif st.session_state.page == "dashboard":
        dashboard_page()
