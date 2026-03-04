"""
Urdu Date/Time utilities for converting dates to Urdu format
"""

# Urdu months
URDU_MONTHS = [
    "جنوری", "فروری", "مارچ", "اپریل", "مئی", "جون",
    "جولائی", "اگست", "ستمبر", "اکتوبر", "نومبر", "دسمبر"
]

# Urdu days of the week
URDU_DAYS = [
    "پیر", "منگل", "بدھ", "جمعرات", "جمعہ", "ہفتہ", "اتوار"
]

# Urdu day numbers (1-31)
URDU_DAY_NUMBERS = [
    "پہلی", "دوسری", "تیسری", "چوتھی", "پانچویں", "چھٹی", "ساتویں", "آٹھویں", "نوویں", "دسویں",
    "گیارہویں", "بارہویں", "تیرہویں", "چودہویں", "پندرہویں", "سولہویں", "سترہویں", "اٹھارہویں", "انیسویں", "بیسویں",
    "اکیسویں", "بائیسویں", "تیئیسویں", "چوبیسویں", "پچیسویں", "چھبیسویں", "ستائیسویں", "اٹھائیسویں", "انتیسویں", "تیسویں", "اکتیسویں"
]

def get_urdu_month(month_number: int) -> str:
    """Get Urdu month name from month number (1-12)"""
    if 1 <= month_number <= 12:
        return URDU_MONTHS[month_number - 1]
    return ""

def get_urdu_day_name(day_of_week: int) -> str:
    """Get Urdu day name from day of week (0=Monday, 6=Sunday)"""
    if 0 <= day_of_week <= 6:
        return URDU_DAYS[day_of_week]
    return ""

def get_urdu_day_number(day: int) -> str:
    """Get Urdu day number as word (1-31)"""
    if 1 <= day <= 31:
        return URDU_DAY_NUMBERS[day - 1]
    return ""

def convert_date_to_urdu(date_obj, prefix: str = "sale") -> dict:
    """
    Convert a date object to Urdu components
    """
    if date_obj is None:
        return {
            f"{prefix}_day": "",
            f"{prefix}_month": "",
            f"{prefix}_year": "",
            f"{prefix}_day_name": ""
        }
    
    day = date_obj.day
    month = date_obj.month
    year = date_obj.year
    weekday = date_obj.weekday()  # 0=Monday, 6=Sunday
    
    return {
        f"{prefix}_day": get_urdu_day_number(day),   # Urdu ordinal day
        f"{prefix}_month": get_urdu_month(month),
        f"{prefix}_year": str(year),
        f"{prefix}_day_name": get_urdu_day_name(weekday)
    }

def convert_datetime_to_urdu(datetime_obj, prefix: str = "sale") -> dict:
    """
    Convert a datetime object to Urdu components including time
    """
    if datetime_obj is None:
        return {
            f"{prefix}_day": "",
            f"{prefix}_month": "",
            f"{prefix}_year": "",
            f"{prefix}_time": "",
            f"{prefix}_day_name": ""
        }
    
    date_parts = convert_date_to_urdu(datetime_obj.date(), prefix)
    
    hour = datetime_obj.hour
    minute = datetime_obj.minute
    
    # Urdu AM/PM
    period = "صبح" if hour < 12 else "شام"
    
    hour_12 = hour if hour <= 12 else hour - 12
    if hour_12 == 0:
        hour_12 = 12
    
    time_str = f"{hour_12:02d}:{minute:02d} {period}"
    
    return {
        f"{prefix}_day": date_parts[f"{prefix}_day"],
        f"{prefix}_month": date_parts[f"{prefix}_month"],
        f"{prefix}_year": date_parts[f"{prefix}_year"],
        f"{prefix}_time": time_str,
        f"{prefix}_day_name": date_parts[f"{prefix}_day_name"]
    }

def get_current_datetime_urdu() -> dict:
    """Get current datetime in Urdu format"""
    from datetime import datetime
    return convert_datetime_to_urdu(datetime.now())

def get_current_date_urdu() -> dict:
    """Get current date in Urdu format"""
    from datetime import date
    return convert_date_to_urdu(date.today())

def format_full_date_urdu(date_obj) -> str:
    """Return full Urdu date like '12 فروری 2022'"""
    if date_obj is None:
        return ""
    day = str(date_obj.day)  # numeric day
    month = get_urdu_month(date_obj.month)
    year = str(date_obj.year)
    return f"{day} {month} {year}"

from datetime import datetime,date

def parse_user_date(date_str: str) -> date:
    """
    Parse user-provided date string into a Python date object.
    Supports 'YYYY-MM-DD', 'DD-MM-YYYY', 'DD/MM/YYYY'.
    """
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    raise ValueError("Invalid date format. Use YYYY-MM-DD or DD-MM-YYYY.")
