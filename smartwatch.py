import streamlit as st
from datetime import datetime
import random

# ------------------------
# Setup
# ------------------------
st.set_page_config(page_title="⌚ Smartwatch Health Dashboard", layout="wide")

# ------------------------
# Fake user & patient data
# ------------------------
USERS = {"doctor111": "password123"}

PATIENTS = [
    {"name": "Mr X", "age": 54, "gender": "Male", "weight": 62, "height": 168, "contact": "x_contact@gmail.com"},
    {"name": "Mr Y", "age": 47, "gender": "Male", "weight": 70, "height": 172, "contact": "y_contact@gmail.com"},
    {"name": "Mr Z", "age": 60, "gender": "Male", "weight": 80, "height": 175, "contact": "z_contact@gmail.com"},
    {"name": "saif ben hmida", "age": 54, "gender": "Male", "weight": 62, "height": 168, "contact": "ss@gmail.com"},
]

# ------------------------
# Utility
# ------------------------
def generate_metrics():
    return {
        "heart_rate": random.randint(60, 100),
        "temperature": round(random.uniform(35.5, 37.5), 1),
        "bmi": round(random.uniform(18, 28), 2),
        "systolic_bp": random.randint(110, 150),
        "diastolic_bp": random.randint(70, 95),
        "spo2": random.randint(90, 100),
    }

# ------------------------
# Session State Setup
# ------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "page" not in st.session_state:
    st.session_state.page = "login"
if "selected_patient" not in st.session_state:
    st.session_state.selected_patient = None
if "patients" not in st.session_state:
    st.session_state.patients = PATIENTS.copy()

# ------------------------
# Login Page
# ------------------------
if not st.session_state.logged_in:
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
            else:
                st.error("Invalid username or password ❌")
    st.stop()

# ------------------------
# Patients Page
# ------------------------
if st.session_state.page == "patients":
    st.sidebar.title("Dashboard")
    st.title("👨‍⚕️ My Patients")

    # --- Search bar ---
    search = st.text_input("🔎 Search Users", "")
    if st.button("Reset"):
        search = ""

    # --- Add patient form ---
    with st.expander("➕ Add New Patient"):
        with st.form("add_patient_form", clear_on_submit=True):
            name = st.text_input("Full Name")
            age = st.number_input("Age", min_value=0, max_value=120, step=1)
            gender = st.selectbox("Gender", ["Male", "Female", "Other"])
            weight = st.number_input("Weight (kg)", min_value=1, max_value=300, step=1)
            height = st.number_input("Height (cm)", min_value=30, max_value=250, step=1)
            contact = st.text_input("Emergency Contact (email or phone)")
            submitted = st.form_submit_button("✅ Add Patient")

            if submitted:
                new_patient = {
                    "name": name,
                    "age": age,
                    "gender": gender,
                    "weight": weight,
                    "height": height,
                    "contact": contact,
                }
                st.session_state.patients.append(new_patient)
                st.success(f"Patient **{name}** added successfully!")

    st.markdown("---")

    # --- Patient List ---
    for p in st.session_state.patients:
        if search.lower() in p["name"].lower():
            col1, col2 = st.columns([3, 1])
            col1.markdown(f"**{p['name']}**")
            if col2.button("View User Metrics", key=p["name"]):
                st.session_state.selected_patient = p
                st.session_state.page = "details"

# ------------------------
# Patient Details Page
# ------------------------
elif st.session_state.page == "details":
    patient = st.session_state.selected_patient
    metrics = generate_metrics()

    st.sidebar.button("⬅ Return", on_click=lambda: st.session_state.update({"page": "patients"}))
    st.title(f"👋 Welcome Back Doctor")
    st.markdown(f"### {patient['name']}")
    st.markdown(f"📧 Emergency Contact: {patient['contact']}")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("❤️ Heart Rate", f"{metrics['heart_rate']} BPM", "Normal")
    with col2:
        st.metric("🌡 Temperature", f"{metrics['temperature']} °C", "Good")
    with col3:
        st.metric("⚖ BMI", f"{metrics['bmi']}", "Normal")

    col4, col5, col6 = st.columns(3)
    with col4:
        st.metric("🩸 Blood Pressure", f"{metrics['systolic_bp']}/{metrics['diastolic_bp']} mmHg", "Normal")
    with col5:
        st.metric("🫁 Oxygen", f"{metrics['spo2']}%", "Good" if metrics['spo2'] > 92 else "Low")
    with col6:
        st.metric("📊 Age/Height/Weight", f"{patient['age']} yrs / {patient['height']} cm / {patient['weight']} kg")
