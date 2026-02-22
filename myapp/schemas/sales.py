# schemas/sales.py
from pydantic import BaseModel
from datetime import date
from typing import Optional

class SaleRead(BaseModel):
    sale_id: int
    customer_name: str
    item_id: int
    quantity_sold: float
    sale_date: date
    sale_day: str
    sale_month: str
    sale_year: str
    sale_time: str
    sale_day_name: str
    
    class Config:
        from_attributes = True
