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

from myapp.config import settings

SMTP_EMAIL = settings.SMTP_EMAIL
SMTP_PASSWORD = settings.SMTP_PASSWORD

SYSTEM_NAME = "VBUGIMS - 360 آسان اسٹور"

# Multiple SMTP configurations for fallback
SMTP_CONFIGS = [
    {"server": "smtp.gmail.com", "port": 465, "use_tls": True, "start_tls": False},  # SSL
    {"server": "smtp.gmail.com", "port": 587, "use_tls": False, "start_tls": True},  # TLS
    {"server": "smtp.gmail.com", "port": 25, "use_tls": False, "start_tls": False},  # Unencrypted (fallback)
]

_smtp_connection: Optional[aiosmtplib.SMTP] = None
_connection_lock = asyncio.Lock()
_current_config_index = 0

async def get_smtp_connection():
    """Get or create SMTP connection with fallback configurations"""
    global _smtp_connection, _current_config_index
    
    async with _connection_lock:
        if _smtp_connection is None or not _smtp_connection.is_connected:
            # Try each configuration
            for i, config in enumerate(SMTP_CONFIGS):
                try:
                    logger.info(f"Attempting SMTP connection with config {i+1}: {config['server']}:{config['port']}")
                    
                    smtp = aiosmtplib.SMTP(
                        hostname=config["server"],
                        port=config["port"],
                        use_tls=config["use_tls"],
                        timeout=10
                    )
                    await smtp.connect()
                    
                    if config["start_tls"]:
                        await smtp.starttls()
                    
                    await smtp.login(SMTP_EMAIL, SMTP_PASSWORD)
                    
                    _smtp_connection = smtp
                    _current_config_index = i
                    logger.info(f"✅ SMTP connected with config {i+1}")
                    return _smtp_connection
                    
                except Exception as e:
                    logger.warning(f"Config {i+1} failed: {str(e)}")
                    continue
            
            raise Exception("All SMTP configurations failed")
    
    return _smtp_connection

async def send_email_async(to: str, subject: str, body: str):
    """Async version - non-blocking email sending with retry"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            smtp = await get_smtp_connection()
            
            msg = MIMEMultipart()
            msg["From"] = formataddr((SYSTEM_NAME, SMTP_EMAIL))
            msg["To"] = to
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "html", "utf-8"))
            
            await smtp.send_message(msg)
            logger.info(f"✅ Email sent to {to} - Subject: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Email error to {to} (attempt {attempt+1}/{max_retries}): {str(e)}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2)  # Wait before retry
                # Force reconnect on next attempt
                global _smtp_connection
                _smtp_connection = None
            else:
                logger.error(f"❌ Failed to send email to {to} after {max_retries} attempts")
                return False

# Keep sync version for backward compatibility
def send_email(to: str, subject: str, body: str):
    """Sync wrapper - schedules async email sending without blocking"""
    try:
        loop = asyncio.get_running_loop()
        asyncio.create_task(send_email_async(to, subject, body))
    except RuntimeError:
        asyncio.run(send_email_async(to, subject, body))

# ======================
# TEMPLATES
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
        <p style="margin-top:15px; color:#e74c3c;">
            ⚠️ یہ کوڈ 15 منٹ کے لیے درست ہوگا۔
        </p>
        """
    )

def password_changed_template(username: str):
    return base_template(
        "🔒 پاس ورڈ تبدیل ہو گیا",
        f"{username}، آپ کا پاس ورڈ کامیابی سے تبدیل ہو گیا ہے۔ اگر آپ نے یہ تبدیلی نہیں کی تو براہ کرم فوری طور پر ہم سے رابطہ کریں۔"
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