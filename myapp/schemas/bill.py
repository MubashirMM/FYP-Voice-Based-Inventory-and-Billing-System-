from pydantic import BaseModel, ConfigDict
from datetime import date
from typing import List,Optional


class BillItemHistoryRead(BaseModel):
    item_name: str
    unit_price: float
    quantity: float
    requested_unit: str
    total_amount: float


    model_config = ConfigDict(from_attributes=True)

class BillRead(BaseModel):
    bill_id: int
    customer_id: Optional[int]
    udhar_items_total: float
    direct_addition: float
    direct_deduction: float
    effective_total: float
    status: str
    bill_date: date
    bill_day: str
    bill_month: str
    bill_year: str
    bill_time: str
    bill_day_name: str
    items: List[BillItemHistoryRead]


    model_config = ConfigDict(from_attributes=True)
