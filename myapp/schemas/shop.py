from pydantic import BaseModel

class ShopBase(BaseModel):
    shop_name: str
    address: str | None = None

class ShopCreate(ShopBase):
    pass

class ShopUpdate(BaseModel):
    shop_name: str | None = None
    address: str | None = None

class ShopRead(ShopBase):
    shop_id: int
    class Config:
        from_attributes = True
