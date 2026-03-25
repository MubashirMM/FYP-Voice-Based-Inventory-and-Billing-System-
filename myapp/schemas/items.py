from pydantic import BaseModel, field_validator, ConfigDict, computed_field
from typing import Optional
from datetime import date

from myapp.utils.urdu_date import format_full_date_urdu


# =========================
# Base Schema
# =========================
class Items(BaseModel):
    item_name: str
    stock_quantity: float
    item_unit: str
    unit_price: float
    created_date: Optional[date] = None


# =========================
# Create Schema - NO UNIT RESTRICTION
# =========================
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

    # No restriction on item_unit - any string is allowed
    # (User can enter "کلو", "بوری", "kg", "piece", "dozen", etc.)


# =========================
# Update Schema - NO UNIT RESTRICTION
# =========================
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

    # No restriction on item_unit during update either


# =========================
# Read Schema
# =========================
class ItemRead(Items):
    item_id: int
    user_id: int
    created_date: Optional[date] = None

    @computed_field
    @property
    def created_date_urdu(self) -> str:
        if self.created_date:
            return format_full_date_urdu(self.created_date)
        return ""

    model_config = ConfigDict(from_attributes=True)