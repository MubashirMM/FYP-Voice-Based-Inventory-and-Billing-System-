from pydantic import BaseModel

from pydantic import BaseModel, Field

class ShopBase(BaseModel):
    shop_name: str = Field(..., min_length=1)
    # make address required and non-empty; Pydantic will reject null or missing values
    address: str = Field(..., min_length=1)

class ShopCreate(ShopBase):
    pass

class ShopUpdate(BaseModel):
    shop_name: str | None = None
    address: str | None = None

class ShopRead(ShopBase):
    shop_id: int
    class Config:
        from_attributes = True
