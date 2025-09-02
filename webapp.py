import os
import datetime
import streamlit as st
from dotenv import load_dotenv
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from streamlit_autorefresh import st_autorefresh   # ✅ auto-refresh

# --- Load secrets from .env ---
load_dotenv()
SLACK_BOT_TOKEN   = os.getenv("SLACK_BOT_TOKEN", "").strip()
SLACK_CHANNEL_ID  = os.getenv("SLACK_CHANNEL_ID", "").strip()

# Slack client
slack_client = WebClient(token=SLACK_BOT_TOKEN) if SLACK_BOT_TOKEN else None

st.set_page_config(page_title="Teams-like Messaging App", layout="wide")
st.title("💬 Teams-like Messaging App")

# Auto-refresh every 5s
st_autorefresh(interval=5000, limit=None, key="slack_refresher")

# ---------------- Session state ----------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = {}

# ---------------- Sidebar ----------------
st.sidebar.title("Chats")
recipient_list = list(st.session_state.chat_history.keys())
selected_recipient = st.sidebar.radio("Select a conversation", recipient_list) if recipient_list else None
if not recipient_list:
    st.sidebar.markdown("_No conversations yet_")

# ---------------- Helper: Slack sender ----------------
def send_to_slack_channel(sender_name, message_text):
    """Send message into Slack channel via bot token"""
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

def send_to_slack_user(user_email, sender_name, message_text):
    """Send message to a Slack user DM (by email lookup)"""
    if not slack_client:
        return False, "Slack client not configured."

    try:
        # 1. Find user ID from email
        resp = slack_client.users_lookupByEmail(email=user_email)
        user_id = resp["user"]["id"]

        # 2. Open a DM channel with the user
        im = slack_client.conversations_open(users=user_id)
        dm_channel_id = im["channel"]["id"]

        # 3. Send message into the DM
        slack_client.chat_postMessage(
            channel=dm_channel_id,
            text=f"*{sender_name}*: {message_text}"
        )
        return True, "ok"
    except SlackApiError as e:
        return False, e.response["error"]

# ---------------- Helper: Slack fetcher ----------------
def get_slack_username(user_id):
    """Get username from Slack user ID"""
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
        for msg in reversed(response.get("messages", [])):  # oldest first
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

# ---------------- Compose UI ----------------
st.header("Compose Message")

sender_name     = st.text_input("Your Name", value="")
sender_email    = st.text_input("Your Email", value="")
send_mode       = st.radio("Send To", ["Slack Channel", "Slack User (by email)"])
recipient_email = None

if send_mode == "Slack User (by email)":
    recipient_email = st.text_input("Recipient Slack Email", value="")
else:
    recipient_email = "slack@channel"  # fixed for channel messages

message_text    = st.text_area("Type your message here...", height=120)
sent = st.button("Send")

# ---------------- Send handler ----------------
if sent:
    if not (sender_name and sender_email and message_text):
        st.error("Please fill in all fields.")
    else:
        payload = {
            "sender": {"name": sender_name, "email": sender_email},
            "recipient": {"name": send_mode, "email": recipient_email},
            "message": message_text,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "✅ Delivered"
        }
        st.session_state.chat_history.setdefault(recipient_email, []).append(payload)

        # Send to Slack
        if send_mode == "Slack Channel":
            ok, info = send_to_slack_channel(sender_name, message_text)
        else:
            ok, info = send_to_slack_user(recipient_email, sender_name, message_text)

        if ok:
            st.success(f"Message sent via {send_mode}!")
        else:
            st.error(f"Slack send failed: {info}")

        selected_recipient = recipient_email
        st.rerun()

# ---------------- Slack sync (channel only for now) ----------------
if SLACK_BOT_TOKEN and SLACK_CHANNEL_ID:
    slack_msgs = fetch_from_slack()
    for sm in slack_msgs:
        st.session_state.chat_history.setdefault("slack@channel", [])
        if sm not in st.session_state.chat_history["slack@channel"]:
            st.session_state.chat_history["slack@channel"].append(sm)

# ---------------- Conversation view ----------------
st.markdown("---")
if selected_recipient and selected_recipient in st.session_state.chat_history:
    st.subheader(f"Conversation with {selected_recipient}")

    last_chats = st.session_state.chat_history[selected_recipient][-5:]  # show last 5

    for chat in last_chats:
        is_sender   = chat["sender"]["email"] == sender_email
        bubble_bg   = "#0078D4" if is_sender else "#E5E5EA"
        text_color  = "white" if is_sender else "black"
        align       = "flex-end" if is_sender else "flex-start"
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
else:
    st.subheader("Conversation")
    st.write("_No messages yet_")
