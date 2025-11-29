from pydantic import BaseModel

class Items(BaseModel):
    item_name: str
    stock_quantity: int
    item_unit: str
    unit_price: float

class ItemCreate(Items):
    pass

class ItemUpdate(BaseModel):
    item_name: str | None = None
    stock_quantity: int | None = None
    item_unit: str | None = None
    unit_price: float | None = None

class ItemRead(Items):
    item_id: int

    class Config:
        from_attributes = True   # ✅ required for Pydantic v2
