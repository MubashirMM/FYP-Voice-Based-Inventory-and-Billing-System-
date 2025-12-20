from pydantic import BaseModel, field_validator, ConfigDict
from typing import Optional

# Common allowed units list
ALLOWED_UNITS = [
    "کلو", "گرام", "پاؤ", "چھٹانک",
    "لیٹر", "ملی لیٹر",
    "عدد", "درجن",
    "پیکٹ", "ڈبہ", "بوتل", "بوری",
]

class Items(BaseModel):
    item_name: str
    stock_quantity: float
    item_unit: str
    unit_price: float


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


class ItemRead(Items):
    item_id: int

    model_config = ConfigDict(from_attributes=True)
