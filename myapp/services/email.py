# myapp/services/email_async.py
import os
import asyncio
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Replace lines 15-17 in email_async.py
from myapp.config import settings

SMTP_EMAIL = settings.SMTP_EMAIL
SMTP_PASSWORD = settings.SMTP_PASSWORD

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465

SYSTEM_NAME = "VBUGIMS - میرا اسٹور"

# Connection pool for SMTP
_smtp_connection: Optional[aiosmtplib.SMTP] = None
_connection_lock = asyncio.Lock()

async def get_smtp_connection():
    """Get or create SMTP connection (reused across requests)"""
    global _smtp_connection
    
    async with _connection_lock:
        if _smtp_connection is None or not _smtp_connection.is_connected:
            _smtp_connection = aiosmtplib.SMTP(
                hostname=SMTP_SERVER,
                port=SMTP_PORT,
                use_tls=True,
                timeout=10
            )
            await _smtp_connection.connect()
            await _smtp_connection.login(SMTP_EMAIL, SMTP_PASSWORD)
            logger.info("SMTP connection established")
    
    return _smtp_connection

async def send_email_async(to: str, subject: str, body: str):
    """Async version - non-blocking email sending"""
    try:
        smtp = await get_smtp_connection()
        
        msg = MIMEMultipart()
        msg["From"] = formataddr((SYSTEM_NAME, SMTP_EMAIL))
        msg["To"] = to
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "html", "utf-8"))
        
        await smtp.send_message(msg)
        logger.info(f"✅ Email sent to {to}")
        
    except Exception as e:
        logger.error(f"❌ Email error to {to}: {str(e)}")
        # Don't raise - email failure shouldn't break the API

# Keep sync version for backward compatibility (but make it non-blocking)
def send_email(to: str, subject: str, body: str):
    """Sync wrapper - schedules async email sending without blocking"""
    try:
        # Try to get running event loop
        loop = asyncio.get_running_loop()
        # Already in async context - create task
        asyncio.create_task(send_email_async(to, subject, body))
    except RuntimeError:
        # No running loop - create new loop (for scripts)
        asyncio.run(send_email_async(to, subject, body))

# ======================
# TEMPLATES (Keep as is)
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

def low_stock_template(item_name: str, stock: float, unit: str):
    return base_template(
        "⚠️ کم اسٹاک الرٹ",
        f"""
        آئٹم: <b>{item_name}</b><br>
        موجودہ اسٹاک: <b>{stock} {unit}</b><br><br>

        ⚠️ اسٹاک کم ہو رہا ہے، براہ کرم جلدی ری اسٹاک کریں۔
        """
    )