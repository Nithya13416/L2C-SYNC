import os
import sqlite3
import datetime
import streamlit as st
from dotenv import load_dotenv
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from streamlit_autorefresh import st_autorefresh

# ---------------------------
# Load environment variables
# ---------------------------
load_dotenv()
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN", "").strip()
SLACK_CHANNEL_ID = os.getenv("SLACK_CHANNEL_ID", "").strip()
slack_client = WebClient(token=SLACK_BOT_TOKEN) if SLACK_BOT_TOKEN else None

st.set_page_config(page_title="Hospital Messaging & Patient Dashboard", layout="wide")

# ---------------------------
# Session state setup
# ---------------------------
if "page" not in st.session_state:
    st.session_state.page = "login"
if "chat_history" not in st.session_state:
    st.session_state.chat_history = {}

# ---------------------------
# Database Setup
# ---------------------------
def init_db():
    conn = sqlite3.connect("hospital.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            age INTEGER,
            condition TEXT,
            admitted_on DATE
        )
    """)
    conn.commit()
    conn.close()

def add_patient(name, age, condition):
    conn = sqlite3.connect("hospital.db")
    c = conn.cursor()
    c.execute("INSERT INTO patients (name, age, condition, admitted_on) VALUES (?, ?, ?, ?)",
              (name, age, condition, datetime.date.today()))
    conn.commit()
    conn.close()

def get_patients():
    conn = sqlite3.connect("hospital.db")
    c = conn.cursor()
    c.execute("SELECT * FROM patients")
    rows = c.fetchall()
    conn.close()
    return rows

# ---------------------------
# Slack Helpers
# ---------------------------
def send_to_slack_channel(sender_name, message_text):
    """Send message directly into Slack channel via bot token"""
    if not slack_client or not SLACK_CHANNEL_ID:
        return False, "Slack client not configured."
    try:
        slack_client.chat_postMessage(
            channel=SLACK_CHANNEL_ID,
            text=f"*{sender_name}*: {message_text}"
        )
        return True, "ok"
    except SlackApiError as e:
        return False, e.response["error"]

def get_slack_username(user_id):
    try:
        if not slack_client:
            return "Unknown"
        resp = slack_client.users_info(user=user_id)
        return resp["user"]["profile"].get("real_name", "Unknown")
    except Exception:
        return "Unknown"

def fetch_from_slack():
    """Fetch last 10 messages from Slack channel"""
    if not slack_client or not SLACK_CHANNEL_ID:
        return []
    try:
        response = slack_client.conversations_history(channel=SLACK_CHANNEL_ID, limit=10)
        messages = []
        for msg in reversed(response.get("messages", [])):
            user_id = msg.get("user", None)
            sender_name = get_slack_username(user_id) if user_id else "Slack Bot"
            messages.append({
                "sender": {"name": sender_name, "email": "slack@channel"},
                "recipient": {"name": "You", "email": "local@app"},
                "message": msg.get("text", ""),
                "timestamp": datetime.datetime.fromtimestamp(float(msg["ts"])).strftime("%Y-%m-%d %H:%M:%S"),
                "status": "📥 Received"
            })
        return messages
    except SlackApiError as e:
        st.error(f"Slack fetch error: {e.response['error']}")
        return []

# ---------------------------
# Pages
# ---------------------------
def login_page():
    st.title("🔐 Hospital Portal Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username == "admin" and password == "admin":  # demo creds
            st.session_state.page = "patients"
            st.success("Login successful!")
            st.rerun()
        else:
            st.error("Invalid credentials")

def patients_page():
    st.title("🏥 Patient Management")

    with st.form("add_patient_form"):
        name = st.text_input("Patient Name")
        age = st.number_input("Age", min_value=0, max_value=120, step=1)
        condition = st.text_area("Condition / Notes")
        submit = st.form_submit_button("Add Patient")
        if submit:
            add_patient(name, age, condition)
            st.success(f"✅ Patient {name} added successfully!")

    st.subheader("Patient Records")
    patients = get_patients()
    if patients:
        for p in patients:
            st.markdown(f"- **{p[1]}** (Age {p[2]}), Condition: {p[3]}, Admitted: {p[4]}")
    else:
        st.info("No patients yet.")

    if st.button("📊 View Metrics"):
        st.session_state.page = "dashboard"
        st.rerun()

def dashboard_page():
    st.title("📊 Hospital Dashboard & Messaging")

    # Auto-refresh every 5s
    st_autorefresh(interval=5000, limit=None, key="slack_refresher")

    # ---- Messaging Section ----
    st.subheader("💬 Teams-like Messaging")
    sender_name = st.text_input("Your Name", value="")
    sender_email = st.text_input("Your Email", value="")
    recipient_email = "slack@channel"
    message_text = st.text_area("Type your message here...", height=120)

    if st.button("Send Message"):
        if not (sender_name and sender_email and message_text):
            st.error("Please fill in all fields.")
        else:
            payload = {
                "sender": {"name": sender_name, "email": sender_email},
                "recipient": {"name": "Slack Channel", "email": recipient_email},
                "message": message_text,
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "status": "✅ Delivered"
            }
            st.session_state.chat_history.setdefault(recipient_email, []).append(payload)
            ok, info = send_to_slack_channel(sender_name, message_text)
            if ok:
                st.success("Message sent to Slack channel!")
            else:
                st.error(f"Slack send failed: {info}")
            st.rerun()

    if SLACK_BOT_TOKEN and SLACK_CHANNEL_ID:
        slack_msgs = fetch_from_slack()
        for sm in slack_msgs:
            st.session_state.chat_history.setdefault("slack@channel", [])
            if sm not in st.session_state.chat_history["slack@channel"]:
                st.session_state.chat_history["slack@channel"].append(sm)

    st.markdown("---")
    st.subheader("Conversation with Slack Channel")
    chats = st.session_state.chat_history.get("slack@channel", [])
    for chat in chats[-5:]:  # last 5 messages
        is_sender = chat["sender"]["email"] == sender_email
        bubble_bg = "#0078D4" if is_sender else "#E5E5EA"
        text_color = "white" if is_sender else "black"
        align = "flex-end" if is_sender else "flex-start"
        avatar_text = chat["sender"]["name"][:2].upper()
        st.markdown(
            f"""
            <div style='display:flex; justify-content:{align}; margin: 10px 0;'>
              <div style='display:flex; align-items:flex-end; gap:10px;'>
                <div style='width:40px;height:40px;background:#555;border-radius:50%;
                            color:white;display:flex;align-items:center;justify-content:center;font-weight:bold;'>
                  {avatar_text}
                </div>
                <div style='background:{bubble_bg};color:{text_color};padding:12px 14px;border-radius:12px;max-width:60%;'>
                  <b>{chat['sender']['name']}</b><br/>
                  {chat['message']}<br/>
                  <span style='font-size:.8em;opacity:.75;'>{chat['timestamp']} {chat['status']}</span>
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # ---- Metrics Section ----
    st.markdown("---")
    st.subheader("📈 Metrics")
    patients = get_patients()
    st.metric("Total Patients", len(patients))
    st.metric("Today's Date", datetime.date.today())

    if st.button("⬅️ Back to Patients"):
        st.session_state.page = "patients"
        st.rerun()

# ---------------------------
# Router
# ---------------------------
init_db()

if st.session_state.page == "login":
    login_page()
elif st.session_state.page == "patients":
    patients_page()
elif st.session_state.page == "dashboard":
    dashboard_page()
