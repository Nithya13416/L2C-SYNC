import os
from datetime import datetime
import requests
import streamlit as st
from dotenv import load_dotenv
import random

# ------------------------
# Setup
# ------------------------

st.set_page_config(page_title="⌚ Smartwatch Chat Monitor", layout="centered")
st.title("⌚ Smartwatch Health Chat")

# Load Slack webhook URL from Streamlit secrets
SLACK_WEBHOOK_URL2 = os.getenv("SLACK_WEBHOOK_URL2", "").strip()


# ------------------------
# Simulate Smartwatch Reading
# ------------------------

def get_random_reading():
    return {
        "heart_rate": random.randint(60, 140),
        "systolic_bp": random.randint(100, 160),
        "diastolic_bp": random.randint(60, 100),
        "spo2": random.randint(90, 100),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "device": random.choice(["Watch A", "Watch B", "Watch C"])
    }

# ------------------------
# Slack Integration
# ------------------------

def send_to_slack(reading):
    if not SLACK_WEBHOOK_URL2:
        return {"status": "error", "message": "Slack webhook not configured"}

    message = (
        f"*📢 Smartwatch Alert from {reading['device']}*\n"
        f"> 🫀 *Heart Rate:* {reading['heart_rate']} bpm\n"
        f"> 💉 *Blood Pressure:* {reading['systolic_bp']}/{reading['diastolic_bp']} mmHg\n"
        f"> 🫁 *SpO₂:* {reading['spo2']}%\n"
        f"> 🕒 *Time:* {reading['timestamp']}"
    )

    payload = {"text": message}
    response = requests.post(SLACK_WEBHOOK_URL2, json=payload)
    return {"status": "ok" if response.status_code == 200 else "error", "code": response.status_code}

# ------------------------
# Streamlit Session State
# ------------------------

if "readings" not in st.session_state:
    st.session_state.readings = []

# ------------------------
# UI: Buttons
# ------------------------

st.markdown("---")
col1, col2 = st.columns(2)

with col1:
    if st.button("📥 Generate New Reading"):
        new_reading = get_random_reading()
        st.session_state.readings.append(new_reading)

with col2:
    if st.button("📤 Send Latest to Slack"):
        if st.session_state.readings:
            latest = st.session_state.readings[-1]
            result = send_to_slack(latest)
            if result["status"] == "ok":
                st.success("✅ Sent to Slack!")
            else:
                st.error(f"❌ Failed to send (Status {result.get('code', '-')})")
        else:
            st.warning("No readings to send yet.")

st.markdown("---")

# ------------------------
# UI: Chat Style Bubbles
# ------------------------

st.subheader("💬 Smartwatch Readings")

for reading in reversed(st.session_state.readings):
    color = "#E0F7FA"
    if reading["heart_rate"] > 120 or reading["spo2"] < 92:
        color = "#FFEBEE"  # red-ish background for alerts

    st.markdown(
        f"""
        <div style='background-color:{color}; padding:15px; border-radius:10px; margin-bottom:10px;'>
            <b>📟 {reading['device']}</b><br>
            🫀 <b>Heart Rate:</b> {reading['heart_rate']} bpm<br>
            💉 <b>BP:</b> {reading['systolic_bp']}/{reading['diastolic_bp']} mmHg<br>
            🫁 <b>SpO₂:</b> {reading['spo2']}%<br>
            <div style='text-align:right; font-size:0.8em; color:#555;'>{reading['timestamp']}</div>
        </div>
        """,
        unsafe_allow_html=True
    )
