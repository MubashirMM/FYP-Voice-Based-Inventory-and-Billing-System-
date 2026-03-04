from pydantic import BaseModel, field_validator, ConfigDict, computed_field
from typing import Optional
from datetime import date
from myapp.utils.urdu_date import format_full_date_urdu

# ✅ Allowed units list
ALLOWED_UNITS = [
    "کلو", "گرام", "پاؤ", "چھٹانک", "سیر", "من", "بوری",
    "لیٹر", "ملی لیٹر",
    "عدد", "درجن", "آدھا درجن",
    "پیکٹ", "ڈبہ", "بوتل",
    "آدھا کلو", "آدھا گرام", "آدھا پاؤ", "آدھا چھٹانک",
    "آدھا سیر", "آدھا من", "آدھا بوری",
    "ڈیڑھ کلو", "ڈیڑھ گرام", "ڈیڑھ پاؤ", "ڈیڑھ چھٹانک",
    "ڈیڑھ سیر", "ڈیڑھ من", "ڈیڑھ بوری",
    "ڈھائی کلو", "ڈھائی گرام", "ڈھائی پاؤ", "ڈھائی چھٹانک",
    "ڈھائی سیر", "ڈھائی من", "ڈھائی بوری",
]

# Base schema
class Items(BaseModel):
    item_name: str
    stock_quantity: float
    item_unit: str
    unit_price: float
    created_date: Optional[date] = None  # stored as Date in DB

# Create schema
class ItemCreate(BaseModel):
    item_name: str
    item_unit: str
    unit_price: float
    stock_quantity: float

    @field_validator("unit_price")
    def price_positive(cls, v):
        if v <= 0:
            raise ValueError("قیمت مثبت ہونی چاہیے")
        return v

    @field_validator("stock_quantity")
    def stock_non_negative(cls, v):
        if v < 0:
            raise ValueError("اسٹاک منفی نہیں ہو سکتا")
        return v

    @field_validator("item_unit")
    def valid_unit(cls, v):
        if v not in ALLOWED_UNITS:
            raise ValueError("اکائی درست نہیں ہے")
        return v

# Update schema
class ItemUpdate(BaseModel):
    item_name: Optional[str] = None
    stock_quantity: Optional[float] = None
    item_unit: Optional[str] = None
    unit_price: Optional[float] = None

    @field_validator("unit_price")
    def price_positive(cls, v):
        if v is not None and v <= 0:
            raise ValueError("قیمت مثبت ہونی چاہیے")
        return v

    @field_validator("stock_quantity")
    def stock_non_negative(cls, v):
        if v is not None and v < 0:
            raise ValueError("اسٹاک منفی نہیں ہو سکتا")
        return v

    @field_validator("item_unit")
    def valid_unit(cls, v):
        if v is not None and v not in ALLOWED_UNITS:
            raise ValueError("اکائی درست نہیں ہے")
        return v

# Read schema
class ItemRead(Items):
    item_id: int
    user_id: int
    created_date: Optional[date] = None

    @computed_field
    @property
    def created_date_urdu(self) -> str:
        return format_full_date_urdu(self.created_date)

    model_config = ConfigDict(from_attributes=True)
