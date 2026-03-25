import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# بہتر طریقہ: ان کو .env میں رکھیں
SMTP_EMAIL = "interneta1toy9@gmail.com"
SMTP_PASSWORD = "zqzc pzav wtnn ttfw"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465   # SSL port (587 issues avoid)

def send_email(to: str, subject: str, body: str):
    try:
        msg = MIMEMultipart()
        msg["From"] = SMTP_EMAIL
        msg["To"] = to
        msg["Subject"] = subject

        # HTML content
        msg.attach(MIMEText(body, "html", "utf-8"))

        # SSL connection (more stable)
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=10) as server:
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.send_message(msg)

        print("✅ ای میل کامیابی سے بھیج دی گئی")

    except Exception as e:
        print(f"❌ ای میل بھیجنے میں خرابی: {str(e)}")


# -------------------------------
# 📩 Registration Email Template
# -------------------------------
def get_registration_template() -> str:
    return """
    <div style="font-family: 'Noto Nastaliq Urdu', Arial; direction: rtl; text-align: right;">
        
        <h2 style="color: #2c3e50;">
            میرا اسٹور میں خوش آمدید 🎉
        </h2>

        <p>السلام علیکم،</p>

        <p>
            آپ کا اکاؤنٹ کامیابی سے بنا دیا گیا ہے۔
        </p>

        <p>
            ہمیں خوشی ہے کہ آپ Voice Based Urdu Grocery Inventory Management System استعمال کر رہے ہیں۔
        </p>

        <p>
            شکریہ<br>
            VBUGIMS ٹیم
        </p>
    </div>
    """


# -------------------------------
# 🔐 Password Reset Template
# -------------------------------
def get_reset_template(code: str) -> str:
    return f"""
    <div style="font-family: 'Noto Nastaliq Urdu', Arial; direction: rtl; text-align: right;">
        
        <h2 style="color: #c0392b;">
            پاس ورڈ ری سیٹ
        </h2>

        <p>السلام علیکم،</p>

        <p>
            آپ کے پاس ورڈ ری سیٹ کی درخواست موصول ہوئی ہے۔
        </p>

        <p>
            آپ کا تصدیقی کوڈ ہے:
        </p>

        <div style="
            font-size: 20px;
            font-weight: bold;
            color: #2c3e50;
            background: #f4f4f4;
            padding: 10px;
            display: inline-block;
            border-radius: 5px;
        ">
            {code}
        </div>

        <p style="margin-top: 15px;">
            اگر آپ نے یہ درخواست نہیں دی تو اس پیغام کو نظر انداز کریں۔
        </p>

        <p>
            شکریہ<br>
            میرا اسٹور ٹیم
        </p>
    </div>
    """