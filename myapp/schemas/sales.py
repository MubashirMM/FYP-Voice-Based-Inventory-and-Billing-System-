# schemas/sales.py
from pydantic import BaseModel
from datetime import date

class SaleRead(BaseModel):
    sale_id: int
    customer_id: int
    item_id: int
    quantity_sold: float
    dat: date
    class Config:
        from_attributes = True
