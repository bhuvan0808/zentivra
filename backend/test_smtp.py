"""Quick SMTP test — sends a test email using .env credentials."""
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv
import os

load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
EMAIL_FROM = os.getenv("EMAIL_FROM")
EMAIL_TO = os.getenv("EMAIL_RECIPIENTS")

print(f"Host: {SMTP_HOST}:{SMTP_PORT}")
print(f"From: {EMAIL_FROM}")
print(f"To:   {EMAIL_TO}")
print()

msg = MIMEMultipart()
msg["From"] = EMAIL_FROM
msg["To"] = EMAIL_TO
msg["Subject"] = "Zentivra SMTP Test"
msg.attach(MIMEText(
    "<h2>SMTP is working!</h2><p>This is a test email from Zentivra.</p>",
    "html",
))

try:
    print("Connecting...")
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
        server.starttls()
        print("Logging in...")
        server.login(SMTP_USER, SMTP_PASSWORD)
        print("Sending...")
        server.send_message(msg)
    print("Email sent successfully!")
except Exception as e:
    print(f"Failed: {e}")
