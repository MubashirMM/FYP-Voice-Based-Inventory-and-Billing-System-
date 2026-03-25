from pydantic import BaseModel, Field, ConfigDict,field_validator
from datetime import date
from typing import Optional


# =========================
# User Input Schema (for API)
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

    # NO unit validation here → Any unit is allowed
    # Conversion check will be done in CRUD using UnitConverter

    model_config = ConfigDict(str_to_lower=False)  # Preserve Urdu text as-is


# =========================
# Internal DB Schema (Optional - if you use it)
# =========================
class UdharCreateDB(BaseModel):
    """Internal schema for database layer"""
    customer_id: int
    item_id: int
    unit_price: float
    quantity: float          # This will be in item's base unit
    requested_unit: str      # Original unit entered by user
    total_amount: float
    created_date: date = Field(default_factory=date.today)


# =========================
# Response Schema
# =========================
class UdharRead(BaseModel):
    udharitem_id: int
    customer_id: int
    customer_name: str
    item_id: int
    item_name: str
    unit_price: float
    quantity: float          # This is in item's stored unit
    requested_unit: str      # What user originally entered
    total_amount: float
    created_date: date
    udhar_day: str
    udhar_month: str
    udhar_year: str
    udhar_time: str
    udhar_day_name: str

    model_config = ConfigDict(from_attributes=True)