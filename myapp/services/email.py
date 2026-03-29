import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr

SMTP_EMAIL = os.getenv("SMTP_EMAIL", "interneta1toy9@gmail.com")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "zqzc pzav wtnn ttfw")
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465

SYSTEM_NAME = "VBUGIMS - میرا اسٹور"


# ======================
# SEND EMAIL
# ======================
def send_email(to: str, subject: str, body: str):
    try:
        msg = MIMEMultipart()
        msg["From"] = formataddr((SYSTEM_NAME, SMTP_EMAIL))
        msg["To"] = to
        msg["Subject"] = subject

        msg.attach(MIMEText(body, "html", "utf-8"))

        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=10) as server:
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.send_message(msg)

        print(f"✅ Email sent to {to}")

    except Exception as e:
        print(f"❌ Email error: {str(e)}")


# ======================
# BASE TEMPLATE (UI)
# ======================
def base_template(title: str, message: str, extra: str = ""):
    return f"""
    <div style="font-family: Arial; background:#f4f6f8; padding:20px; direction: rtl;">
        <div style="max-width:500px; margin:auto; background:white; padding:25px;
                    border-radius:10px; box-shadow:0 2px 10px rgba(0,0,0,0.1); text-align:right;">
            
            <h2 style="color:#2c3e50;">{title}</h2>
            
            <p style="font-size:15px; color:#333;">
                {message}
            </p>

            {extra}

            <hr style="margin-top:20px;">
            <p style="font-size:12px; color:gray;">
                شکریہ،<br>
                VBUGIMS ٹیم
            </p>
        </div>
    </div>
    """


# ======================
# TEMPLATES
# ======================

def registration_template(username: str):
    return base_template(
        "🎉 خوش آمدید",
        f"{username}، آپ کا اکاؤنٹ کامیابی سے بنا دیا گیا ہے۔ اب آپ سسٹم استعمال کر سکتے ہیں۔"
    )


def login_template(username: str):
    return base_template(
        "🔐 لاگ ان",
        f"{username}، آپ نے کامیابی سے لاگ ان کیا ہے۔ اگر یہ آپ نہیں تھے تو براہ کرم پاس ورڈ تبدیل کریں۔"
    )


def voice_login_template(username: str):
    return base_template(
        "🎤 وائس لاگ ان",
        f"{username}، آپ نے وائس کے ذریعے لاگ ان کیا ہے۔"
    )


def voice_samples_template(username: str):
    return base_template(
        "🎤 وائس محفوظ",
        f"{username}، آپ کی آواز کامیابی سے محفوظ کر لی گئی ہے۔"
    )


def profile_update_template(username: str, email: str):
    return base_template(
        "✅ پروفائل اپڈیٹ",
        f"نام: {username}<br>ای میل: {email}"
    )


def password_reset_template(code: str):
    return base_template(
        "🔐 پاس ورڈ ری سیٹ",
        "براہ کرم نیچے دیا گیا کوڈ استعمال کریں:",
        f"""
        <div style="font-size:20px; font-weight:bold; background:#ecf0f1;
                    padding:10px; border-radius:5px; display:inline-block;">
            {code}
        </div>
        """
    )


def password_changed_template(username: str):
    return base_template(
        "🔒 پاس ورڈ تبدیل ہو گیا",
        f"{username}، آپ کا پاس ورڈ کامیابی سے تبدیل ہو گیا ہے۔"
    )


def account_deleted_template(username: str):
    return base_template(
        "🗑 اکاؤنٹ ڈیلیٹ",
        f"{username}، آپ کا اکاؤنٹ کامیابی سے ڈیلیٹ کر دیا گیا ہے۔<br><br>ہماری سروس استعمال کرنے کا شکریہ 🙏"
    )