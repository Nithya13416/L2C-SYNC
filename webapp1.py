import os
import streamlit as st
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import json
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()
# ---------------- CONFIG ----------------
SLACK_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_CHANNEL = os.getenv("SLACK_CHANNEL_ID")  # e.g. C09D8JAP141

slack_client = WebClient(token=SLACK_TOKEN)

DATA_FILE = "conversations.json"

# ---------------- HELPERS ----------------
def load_conversations():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_conversations(convos):
    with open(DATA_FILE, "w") as f:
        json.dump(convos, f, indent=2)

def fetch_slack_messages():
    """Pull latest Slack messages and normalize them"""
    try:
        response = slack_client.conversations_history(channel=SLACK_CHANNEL, limit=20)
        messages = response.get("messages", [])
        formatted = []
        for msg in reversed(messages):  # oldest first
            formatted.append({
                "from": msg.get("user", "Slack"),
                "email": "slack@channel",
                "message": msg.get("text", ""),
                "timestamp": datetime.fromtimestamp(float(msg["ts"])).strftime("%Y-%m-%d %H:%M:%S"),
                "source": "slack"
            })
        return formatted
    except SlackApiError as e:
        st.error(f"Slack fetch error: {e.response['error']}")
        return []

def send_to_slack(text):
    """Send message to Slack channel"""
    try:
        slack_client.chat_postMessage(channel=SLACK_CHANNEL, text=text)
        return True
    except SlackApiError as e:
        st.error(f"Slack send error: {e.response['error']}")
        return False

# ---------------- UI ----------------
st.set_page_config(page_title="Chat App ↔ Slack", layout="wide")
st.title("💬 Teams-like Chat App (with Slack Sync)")

conversations = load_conversations()

# Pick a conversation
st.sidebar.header("Chats")
selected_chat = st.sidebar.selectbox("Select recipient", ["#webapp1"] + list(conversations.keys()))

# Fetch Slack messages
slack_msgs = fetch_slack_messages()

# Merge Slack messages with local messages
thread = []
if selected_chat == "#webapp1":
    thread.extend(slack_msgs)
if selected_chat in conversations:
    for msg in conversations[selected_chat]:
        thread.append(msg)

# Sort by timestamp if available
thread = sorted(thread, key=lambda x: x.get("timestamp", ""))

# Display merged conversation
st.subheader(f"Conversation with {selected_chat}")
for msg in thread:
    if msg.get("source") == "slack":
        st.markdown(
            f"🟣 **{msg['from']} (Slack):** {msg['message']}  \n ⏰ {msg['timestamp']}"
        )
    else:
        st.markdown(
            f"🔵 **{msg['from']} (App):** {msg['message']}  \n ⏰ {msg.get('timestamp', '')}"
        )

# Message form
st.subheader("Send a Message")
with st.form("msg_form", clear_on_submit=True):
    name = st.text_input("Your Name")
    email = st.text_input("Your Email")
    recipient = st.text_input("Recipient Email (or #webapp1 for Slack)")
    message = st.text_area("Message")
    submitted = st.form_submit_button("Send")

    if submitted:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_msg = {
            "from": name,
            "email": email,
            "message": message,
            "timestamp": timestamp,
            "source": "app"
        }

        # Save locally
        if recipient not in conversations:
            conversations[recipient] = []
        conversations[recipient].append(new_msg)
        save_conversations(conversations)

        # Send to Slack if targeting Slack
        if recipient == "#webapp1":
            if send_to_slack(f"{name}: {message}"):
                st.success("Message sent to Slack ✅")
        else:
            st.success("Message saved locally ✅")
