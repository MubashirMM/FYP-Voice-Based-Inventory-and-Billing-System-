from pydantic import BaseModel, ConfigDict, field_validator
from datetime import date
from typing import Optional

class SaleCreate(BaseModel):
    customer_name: str
    item_id: Optional[int] = None
    item_name: str
    quantity_sold: float
    unit_price: Optional[float] = None
    item_unit: Optional[str] = None
    sale_date: Optional[date] = None
    
    @field_validator("quantity_sold")
    def quantity_positive(cls, v):
        if v <= 0:
            raise ValueError("مقدار صفر سے زیادہ ہونی چاہیے")
        return v
    
    @field_validator("unit_price")
    def price_positive(cls, v):
        if v is not None and v <= 0:
            raise ValueError("قیمت مثبت ہونی چاہیے")
        return v

class SaleRead(BaseModel):
    sale_id: int
    customer_name: str
    item_id: Optional[int] = None
    item_name: str
    quantity_sold: float
    unit_price: Optional[float] = None
    item_unit: Optional[str] = None
    sale_date: date
    sale_day: str
    sale_month: str
    sale_year: str
    sale_time: str
    sale_day_name: str

    model_config = ConfigDict(from_attributes=True)

class SaleUpdate(BaseModel):
    customer_name: Optional[str] = None
    item_id: Optional[int] = None
    quantity_sold: Optional[float] = None
    unit_price: Optional[float] = None
    item_unit: Optional[str] = None
    sale_date: Optional[date] = None
    
    @field_validator("quantity_sold")
    def quantity_positive(cls, v):
        if v is not None and v <= 0:
            raise ValueError("مقدار صفر سے زیادہ ہونی چاہیے")
        return v
    
    @field_validator("unit_price")
    def price_positive(cls, v):
        if v is not None and v <= 0:
            raise ValueError("قیمت مثبت ہونی چاہیے")
        return v

class SaleFilter(BaseModel):
    item_id: Optional[int] = None
    customer_name: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    skip: int = 0
    limit: int = 100