try:
    from twilio.rest import Client
except ImportError:
    Client = None

import os

# ---------------------------
# TWILIO CONFIGURATION
# ---------------------------

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "your_account_sid")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "your_auth_token")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER", "+1234567890")


# ---------------------------
# SEND SMS
# ---------------------------

def send_sms(to_number, message):
    """
    Send SMS using Twilio API
    """
    if not Client:
        return "❌ Twilio not installed (pip install twilio)"

    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        msg = client.messages.create(
            body=message,
            from_=TWILIO_PHONE_NUMBER,
            to=to_number
        )
        return f"📩 Message sent, SID: {msg.sid}"

    except Exception as e:
        return f"❌ Error sending SMS: {e}"
