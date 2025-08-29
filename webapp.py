import os
import datetime
import requests
import streamlit as st
from dotenv import load_dotenv

# --- Load secrets from .env ---
load_dotenv()
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "").strip()

st.set_page_config(page_title="Teams-like Messaging App (Slack)", layout="wide")
st.title("💬 Teams-like Messaging App → Slack (Webhook Only)")

# ---------------- Session state ----------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = {}

# ---------------- Sidebar ----------------
st.sidebar.title("Chats")
recipient_list = list(st.session_state.chat_history.keys())
selected_recipient = st.sidebar.radio("Select a conversation", recipient_list) if recipient_list else None
if not recipient_list:
    st.sidebar.markdown("_No conversations yet_")

# ---------------- Helper: Slack webhook sender ----------------
def send_to_slack_webhook(sender_name, recipient_name, message_text):
    if not SLACK_WEBHOOK_URL:
        return False, "SLACK_WEBHOOK_URL not configured."

    blocks = [
        {"type": "header", "text": {"type": "plain_text", "text": "New message from Streamlit"}},
        {"type": "section", "fields": [
            {"type": "mrkdwn", "text": f"*From:*\n{sender_name}"},
            {"type": "mrkdwn", "text": f"*To:*\n{recipient_name}"},
        ]},
        {"type": "section", "text": {"type": "mrkdwn", "text": f"*Message:*\n{message_text}"}},
        {"type": "context", "elements": [
            {"type": "mrkdwn", "text": f"Sent at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"}
        ]},
    ]
    payload = {"text": f"Message from {sender_name} to {recipient_name}", "blocks": blocks}

    try:
        r = requests.post(SLACK_WEBHOOK_URL, json=payload, timeout=10)
        ok = (r.status_code == 200 and r.text.strip().lower() == "ok")
        return ok, (r.text if not ok else "ok")
    except Exception as e:
        return False, str(e)

# ---------------- Compose UI ----------------
st.header("Compose Message")

sender_name     = st.text_input("Your Name", value="")
sender_email    = st.text_input("Your Email", value="")
recipient_name  = st.text_input("Recipient Name", value="")
recipient_email = st.text_input("Recipient Email (used as conversation key)", value="")
message_text    = st.text_area("Type your message here...", height=120)

sent = st.button("Send")

# ---------------- Send handler ----------------
if sent:
    if not (sender_name and sender_email and recipient_name and recipient_email and message_text):
        st.error("Please fill in all fields.")
    else:
        payload = {
            "sender": {"name": sender_name, "email": sender_email},
            "recipient": {"name": recipient_name, "email": recipient_email},
            "message": message_text,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "✅ Delivered"
        }
        st.session_state.chat_history.setdefault(recipient_email, []).append(payload)

        ok, info = send_to_slack_webhook(sender_name, recipient_name, message_text)
        if ok:
            st.success("Message sent to Slack!")
        else:
            st.error(f"Slack send failed: {info}")

        selected_recipient = recipient_email

# ---------------- Conversation view ----------------
st.markdown("---")
if selected_recipient and selected_recipient in st.session_state.chat_history:
    st.subheader(f"Conversation between {selected_recipient} and you")
    for chat in st.session_state.chat_history[selected_recipient]:
        is_sender   = chat["sender"]["email"] == sender_email
        bubble_bg   = "#0078D4" if is_sender else "#E5E5EA"
        text_color  = "white" if is_sender else "black"
        align       = "flex-end" if is_sender else "flex-start"
        avatar_text = (chat["sender"]["name"] if is_sender else chat["recipient"]["name"])[:2].upper()

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
