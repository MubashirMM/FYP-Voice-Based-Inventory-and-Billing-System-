from pydantic import BaseModel, Field, field_validator
from datetime import date
from typing import Optional

# ✅ Same allowed units list as in Item models
ALLOWED_UNITS = [
    # Base Weight Units
    "کلو", "گرام", "پاؤ", "چھٹانک", "سیر", "من", "بوری",

    # Volume Units
    "لیٹر", "ملی لیٹر",

    # Count Units
    "عدد", "درجن", "آدھا درجن",

    # Package Units
    "پیکٹ", "ڈبہ", "بوتل",

    # Fractional Weight Units (آدھا)
    "آدھا کلو", "آدھا گرام", "آدھا پاؤ", "آدھا چھٹانک",
    "آدھا سیر", "آدھا من", "آدھا بوری",

    # Fractional Weight Units (ڈیڑھ)
    "ڈیڑھ کلو", "ڈیڑھ گرام", "ڈیڑھ پاؤ", "ڈیڑھ چھٹانک",
    "ڈیڑھ سیر", "ڈیڑھ من", "ڈیڑھ بوری",

    # Fractional Weight Units (ڈھائی)
    "ڈھائی کلو", "ڈھائی گرام", "ڈھائی پاؤ", "ڈھائی چھٹانک",
    "ڈھائی سیر", "ڈھائی من", "ڈھائی بوری",
]


class BillItemCreate(BaseModel):
    item_name: str
    quantity: float = Field(..., gt=0, description="مقدار صفر سے زیادہ ہونی چاہیے")
    requested_unit: str
    created_date: Optional[date] = None  # Optional, defaults to today if not provided

    @field_validator("item_name")
    def name_not_empty(cls, v):
        if not v.strip():
            raise ValueError("آئٹم کا نام خالی نہیں ہو سکتا")
        return v

    @field_validator("requested_unit")
    def valid_unit(cls, v):
        if v not in ALLOWED_UNITS:
            raise ValueError("اکائی درست نہیں ہے")
        return v


class BillItemRead(BaseModel):
    billitem_id: int
    bill_id: int
    item_name: str
    unit_price: float
    quantity: float
    requested_unit: str
    total_amount: float
    created_date: date
    billitem_day: str
    billitem_month: str
    billitem_year: str
    billitem_time: str
    billitem_day_name: str

    class Config:
        from_attributes = True
