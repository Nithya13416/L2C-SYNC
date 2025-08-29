import streamlit as st
import pandas as pd

# ---------------- Helper Functions ---------------- #

def load_excel(file):
    df = pd.read_excel(file)
    st.session_state.patients = df.to_dict(orient="records")  # list of dicts

def get_status(value, vital):
    """Return status text and color based on vital type."""
    if vital == "HeartRate":
        if 60 <= value <= 100: return ("Normal", "🟢")
        elif 50 <= value < 60 or 100 < value <= 110: return ("Warning", "🟠")
        else: return ("Critical", "🔴")
    elif vital == "Temperature":
        if 36 <= value <= 37.5: return ("Good", "🟢")
        elif 37.5 < value <= 38.5: return ("Fever", "🟠")
        else: return ("High Risk", "🔴")
    elif vital == "Oxygen":
        if value >= 95: return ("Normal", "🟢")
        elif 90 <= value < 95: return ("Low", "🟠")
        else: return ("Critical", "🔴")
    elif vital == "BloodPressure":
        sys, dia = value
        if 90 <= sys <= 140 and 60 <= dia <= 90: return ("Normal", "🟢")
        elif sys < 90 or dia < 60: return ("Low", "🟠")
        elif sys > 140 or dia > 90: return ("High", "🟠")
        else: return ("Critical", "🔴")
    return ("Unknown", "⚪")

# ---------------- Page Functions ---------------- #

def patients_page():
    st.title("🏥 Patient Management")

    uploaded_file = st.file_uploader("📂 Upload Patient Excel", type=["xlsx"])
    if uploaded_file:
        load_excel(uploaded_file)
        st.success("✅ Patients loaded successfully!")

    if st.session_state.patients:
        st.subheader("Patient List:")
        for patient in st.session_state.patients:
            if st.button(patient["Name"]):
                st.session_state.selected_patient = patient
                st.session_state.page = "dashboard"
                st.rerun()
    else:
        st.info("ℹ️ No patient data found. Please upload an Excel file.")

def dashboard_page():
    patient = st.session_state.selected_patient
    if not patient:
        st.warning("⚠️ No patient selected")
        return

    if st.button("⬅️ Back to Patients"):
        st.session_state.page = "patients"
        st.rerun()

    st.header(f"👨‍⚕️ Patient Dashboard - {patient['Name']}")

    # ---- Patient Info ----
    st.subheader("🧑 Patient Info")
    st.write(f"**Age:** {patient['Age']} | **Gender:** {patient['Gender']}")
    st.write(f"**Weight:** {patient['Weight']} kg | **Height:** {patient['Height']} cm")
    st.write(f"**Email:** {patient['Email']}")

    # ---- Vitals ----
    st.subheader("📊 Vitals")

    col1, col2, col3 = st.columns(3)

    with col1:
        status, color = get_status(patient["HeartRate"], "HeartRate")
        st.metric("❤️ Heart Rate", f"{patient['HeartRate']} BPM", f"{color} {status}")

        bmi = round(patient["Weight"] / ((patient["Height"]/100)**2), 2)
        st.metric("📊 BMI", bmi)

    with col2:
        status, color = get_status(patient["Temperature"], "Temperature")
        st.metric("🌡️ Temperature", f"{patient['Temperature']}°C", f"{color} {status}")

        status, color = get_status((patient["Systolic"], patient["Diastolic"]), "BloodPressure")
        st.metric("🩸 Blood Pressure", f"{patient['Systolic']}/{patient['Diastolic']}", f"{color} {status}")

    with col3:
        status, color = get_status(patient["Oxygen"], "Oxygen")
        st.metric("🫁 Oxygen Level", f"{patient['Oxygen']}%", f"{color} {status}")

# ---------------- Main App ---------------- #

if "page" not in st.session_state:
    st.session_state.page = "patients"
if "patients" not in st.session_state:
    st.session_state.patients = []
if "selected_patient" not in st.session_state:
    st.session_state.selected_patient = None

if st.session_state.page == "patients":
    patients_page()
elif st.session_state.page == "dashboard":
    dashboard_page()
