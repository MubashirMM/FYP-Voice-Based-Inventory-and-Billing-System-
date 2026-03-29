from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import date
from typing import Optional


# =========================
# User Input Schema (API)
# =========================
class UdharCreateRequest(BaseModel):
    """Schema for creating Udhar item - accepts any unit"""

    customer_name: str
    item_name: str
    quantity: float = Field(gt=0, description="Quantity must be greater than 0")
    unit: str
    created_date: Optional[date] = None

    @field_validator("quantity")
    def quantity_positive(cls, v):
        if v <= 0:
            raise ValueError("مقدار صفر یا منفی نہیں ہو سکتی")
        return v

    model_config = ConfigDict(str_to_lower=False)


# =========================
# Internal DB Schema
# =========================
class UdharCreateDB(BaseModel):
    """Internal schema for database layer"""

    customer_id: int

    # ✅ OPTIONAL FK (item may be deleted)
    item_id: Optional[int] = None

    # ✅ SNAPSHOT (main source of truth)
    item_name: str

    unit_price: float
    quantity: float              # stored in base unit
    requested_unit: str          # user input unit
    total_amount: float

    created_date: date = Field(default_factory=date.today)


# =========================
# Response Schema
# =========================
class UdharRead(BaseModel):
    udharitem_id: int
    customer_id: int
    customer_name: str

    item_id: Optional[int]
    item_name: str

    unit_price: float

    quantity: float              # in base unit
    base_unit: str               # ✅ NEW
    requested_unit: str          # user input

    total_amount: float
    created_date: date

    udhar_day: str
    udhar_month: str
    udhar_year: str
    udhar_time: str
    udhar_day_name: str

    model_config = ConfigDict(from_attributes=True)