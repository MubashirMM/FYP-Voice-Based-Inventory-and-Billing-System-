import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
import os

# Best practice: Use environment variables
SMTP_EMAIL = "interneta1toy9@gmail.com"
SMTP_PASSWORD = "bnmk dhvq rhvu lbto"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

def send_email(to: str, subject: str, body: str):
    msg = MIMEMultipart()
    msg["From"] = SMTP_EMAIL
    msg["To"] = to
    msg["Subject"] = subject

   
    msg.attach(MIMEText(body, "plain", "utf-8"))

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.send_message(msg)

def get_registration_template() -> str:
    return """
السلام علیکم،

VBUGIMS میں خوش آمدید!

آپ کا اکاؤنٹ کامیابی سے بنا دیا گیا ہے۔
ہمیں خوشی ہے کہ آپ Voice Based Urdu Grocery Inventory Management System استعمال کر رہے ہیں۔

شکریہ
VBUGIMS ٹیم
"""

def get_reset_template(code: str) -> str:
    return f"""
السلام علیکم،

آپ کے پاس ورڈ ری سیٹ کی درخواست موصول ہوئی ہے۔

آپ کا تصدیقی کوڈ ہے:
{code}

اگر آپ نے یہ درخواست نہیں دی تو اس پیغام کو نظر انداز کریں۔

شکریہ
VBUGIMS(Voice Based Urdu Grocery Inventory Management System) ٹیم
"""