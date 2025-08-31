import os
import streamlit as st
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import json
from datetime import datetime
from dotenv import load_dotenv

# ---------------- CONFIG ----------------
load_dotenv()
SLACK_TOKEN = os.getenv("SLACK_BOT_TOKEN")   # xoxb-...
DATA_FILE = "conversations.json"

# Slack client
slack_client = WebClient(token=SLACK_TOKEN)


# ---------------- HELPERS ----------------
def load_conversations():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}


def save_conversations(convos):
    with open(DATA_FILE, "w") as f:
        json.dump(convos, f, indent=2)


def get_slack_channels():
    """Fetch list of Slack channels (name → id)"""
    try:
        response = slack_client.conversations_list(types="public_channel,private_channel")
        return {ch["name"]: ch["id"] for ch in response["channels"]}
    except SlackApiError as e:
        st.error(f"Slack channel fetch error: {e.response['error']}")
        return {}


def fetch_slack_messages(channel_id):
    """Pull latest Slack messages from a channel"""
    try:
        response = slack_client.conversations_history(channel=channel_id, limit=20)
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


def send_to_slack(channel_id, text):
    """Send message to Slack channel"""
    try:
        slack_client.chat_postMessage(channel=channel_id, text=text)
        return True
    except SlackApiError as e:
        st.error(f"Slack send error: {e.response['error']}")
        return False


# ---------------- UI ----------------
st.set_page_config(page_title="Chat App ↔ Slack", layout="wide")
st.title("💬 Teams-like Chat App (with Slack Sync)")

conversations = load_conversations()

# Slack channels
slack_channels = get_slack_channels()

# Sidebar recipient picker
st.sidebar.header("Chats")
recipient_options = list(slack_channels.keys()) + list(conversations.keys())
selected_chat = st.sidebar.selectbox("Select recipient", recipient_options)

# Build conversation thread
thread = []

# If selected is Slack channel → fetch messages
if selected_chat in slack_channels:
    slack_msgs = fetch_slack_messages(slack_channels[selected_chat])
    thread.extend(slack_msgs)

# If selected is local conversation → load local msgs
if selected_chat in conversations:
    thread.extend(conversations[selected_chat])

# Sort by time
thread = sorted(thread, key=lambda x: x.get("timestamp", ""))

# Display conversation
st.subheader(f"Conversation with {selected_chat}")
if not thread:
    st.info("No messages yet.")
for msg in thread:
    if msg.get("source") == "slack":
        st.markdown(
            f"🟣 **{msg['from']} (Slack):** {msg['message']}  \n ⏰ {msg['timestamp']}"
        )
    else:
        st.markdown(
            f"🔵 **{msg['from']} (App):** {msg['message']}  \n ⏰ {msg.get('timestamp', '')}"
        )

# Send new message
st.subheader("Send a Message")
with st.form("msg_form", clear_on_submit=True):
    name = st.text_input("Your Name")
    email = st.text_input("Your Email")
    recipient = st.text_input("Recipient (Slack channel name or local ID)")
    message = st.text_area("Message")
    submitted = st.form_submit_button("Send")

    if submitted and message.strip():
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

        # If recipient is a Slack channel name → send to Slack
        if recipient in slack_channels:
            if send_to_slack(slack_channels[recipient], f"{name}: {message}"):
                st.success(f"Message sent to Slack channel #{recipient} ✅")
        else:
            st.success("Message saved locally ✅")
