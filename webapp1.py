import os
import time
import datetime
import streamlit as st
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# -------------------- CONFIG --------------------
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN", "")
SLACK_CHANNEL = os.getenv("SLACK_CHANNEL", "#general")

slack_client = WebClient(token=SLACK_BOT_TOKEN) if SLACK_BOT_TOKEN else None
SLACK_CHANNEL_ID = None

if slack_client:
    try:
        # Resolve channel ID
        resp = slack_client.conversations_list()
        for c in resp["channels"]:
            if c["name"] == SLACK_CHANNEL.strip("#"):
                SLACK_CHANNEL_ID = c["id"]
    except SlackApiError as e:
        st.error(f"Slack channel error: {e.response['error']}")

# -------------------- STATE --------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# -------------------- User cache --------------------
# ---------------- Slack user cache ----------------
user_cache = {}

def get_slack_username(user_id):
    """Resolve Slack user ID into real name (cached)"""
    if user_id in user_cache:
        return user_cache[user_id]

    try:
        response = slack_client.users_info(user=user_id)
        real_name = response["user"]["real_name"] or response["user"]["name"]
        user_cache[user_id] = real_name
        return real_name
    except SlackApiError:
        return user_id  # fallback to ID if API fails


# -------------------- Slack fetch --------------------
def fetch_from_slack():
    """Fetch recent 2 messages from Slack"""
    if not slack_client or not SLACK_CHANNEL_ID:
        return []

    try:
        response = slack_client.conversations_history(channel=SLACK_CHANNEL_ID, limit=2)
        messages = []
        for msg in reversed(response.get("messages", [])):
            user_id = msg.get("user")
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

# -------------------- Send to Slack --------------------
def send_to_slack(text):
    """Send a message to Slack"""
    if not slack_client or not SLACK_CHANNEL_ID:
        return False
    try:
        slack_client.chat_postMessage(channel=SLACK_CHANNEL_ID, text=text)
        return True
    except SlackApiError as e:
        st.error(f"Slack send error: {e.response['error']}")
        return False

# -------------------- UI --------------------
st.set_page_config(page_title="Teams-like Messaging", layout="wide")
st.title("💬 Conversation with Slack Channel")

# Auto-refresh every 5s
from streamlit_autorefresh import st_autorefresh

# Auto-refresh every 5s
st_autorefresh(interval=5000, limit=None, key="slack_refresher")

# Fetch latest Slack messages
slack_msgs = fetch_from_slack()
if slack_msgs:
    # Avoid duplicates: only add new messages
    existing_texts = {m["message"] for m in st.session_state.messages}
    for m in slack_msgs:
        if m["message"] not in existing_texts:
            st.session_state.messages.append(m)

# Show last 2 messages only
for msg in st.session_state.messages[-2:]:
    is_sender = msg["sender"]["email"] != "slack@channel"
    bubble_color = "#0A84FF" if is_sender else "#F1F1F1"
    align = "flex-end" if is_sender else "flex-start"
    text_color = "white" if is_sender else "black"

    st.markdown(
        f"""
        <div style="display:flex; justify-content:{align}; margin:5px;">
            <div style="background:{bubble_color}; color:{text_color};
                        padding:10px; border-radius:12px; max-width:60%;">
                <b>{msg['sender']['name']}</b><br>
                {msg['message']}<br>
                <span style="font-size:10px;">{msg['timestamp']} | {msg['status']}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Input box
with st.form("send_form", clear_on_submit=True):
    text = st.text_input("Type a message...", "")
    submitted = st.form_submit_button("Send")
    if submitted and text.strip():
        success = send_to_slack(text)
        if success:
            st.session_state.messages.append({
                "sender": {"name": "You", "email": "local@app"},
                "recipient": {"name": "Slack Channel", "email": "slack@channel"},
                "message": text,
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "status": "✅ Delivered"
            })
            st.experimental_rerun()
