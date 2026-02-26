# schemas/udharitem.py
from pydantic import BaseModel, field_validator, ConfigDict, Field
from datetime import date
from typing import Optional

class UdharCreateRequest(BaseModel):
    """User input schema - accepts names"""
    customer_name: str
    item_name: str
    quantity: float = Field(gt=0, description="Quantity must be greater than 0")
    unit: str
    date_: Optional[date] = None  # Optional, will default to today if not provided
    
    @field_validator("unit")
    def validate_unit(cls, v):
        allowed_units = [
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
        if v not in allowed_units:
            raise ValueError(f"اکائی درست نہیں ہے۔ درست اکائیاں: {', '.join(allowed_units)}")
        return v
    
    @field_validator("quantity")
    def quantity_positive(cls, v):
        if v <= 0:
            raise ValueError("مقدار صفر یا منفی نہیں ہو سکتی")
        return v
    
    model_config = ConfigDict(str_to_lower=False)  # Keep Urdu case

class UdharCreateDB(BaseModel):
    """Database creation schema - uses IDs"""
    customer_id: int
    item_id: int
    unit_price: float
    quantity: float
    requested_unit: str
    total_amount: float
    date_: date = Field(default_factory=date.today)  # Default to today

class UdharRead(BaseModel):
    """Response schema"""
    udharitem_id: int
    customer_id: int
    item_id: int
    unit_price: float
    quantity: float
    requested_unit: str
    total_amount: float
    date_: date
    udhar_day: str
    udhar_month: str
    udhar_year: str
    udhar_time: str
    udhar_day_name: str
    
    model_config = ConfigDict(from_attributes=True)
