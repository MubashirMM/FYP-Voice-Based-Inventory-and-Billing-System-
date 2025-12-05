from pydantic import BaseModel, field_validator, ConfigDict

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
        allowed_units = ["کلو", "گرام", "پاؤ", "چھٹانک", 
    "لیٹر", "ملی لیٹر", 
    "عدد", "درجن", 
    "پیکٹ", "ڈبہ", "بوتل", "بوری",]
        if v not in allowed_units:
            raise ValueError("اکائی درست نہیں ہے")
        return v

class ItemUpdate(BaseModel):
    item_name: str | None = None
    stock_quantity: float | None = None
    item_unit: str | None = None
    unit_price: float | None = None

class ItemRead(Items):
    item_id: int

    model_config = ConfigDict(from_attributes=True) 
