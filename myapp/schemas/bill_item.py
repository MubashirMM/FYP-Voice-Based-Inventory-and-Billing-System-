from pydantic import BaseModel, Field, ConfigDict,field_validator
from datetime import date
from typing import Optional


class BillItemCreate(BaseModel):
    """User input for creating bill item - any unit allowed"""
    item_name: str
    quantity: float = Field(..., gt=0, description="مقدار صفر سے زیادہ ہونی چاہیے")
    requested_unit: str
    created_date: Optional[date] = None

    @field_validator("item_name")
    def name_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("آئٹم کا نام خالی نہیں ہو سکتا")
        return v.strip()

    # NO unit validation here → Any unit is accepted
    # Conversion check will be done in CRUD layer


class BillItemRead(BaseModel):
    """Response schema"""
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

    model_config = ConfigDict(from_attributes=True)