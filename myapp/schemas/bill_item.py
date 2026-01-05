from pydantic import BaseModel, Field
from datetime import date

class BillItemCreate(BaseModel):
    item_name: str
    quantity: float = Field(..., gt=0, description="Quantity must be greater than zero")
    requested_unit: str

class BillItemRead(BaseModel):
    billitem_id: int
    bill_id: int
    item_name: str
    unit_price: float
    quantity: float
    requested_unit: str
    total_amount: float
    date_: date

    class Config:
        from_attributes = True
