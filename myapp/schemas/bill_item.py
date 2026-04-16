# from pydantic import BaseModel, Field, ConfigDict,field_validator
# from datetime import date
# from typing import Optional


# class BillItemCreate(BaseModel):
#     """User input for creating bill item - any unit allowed"""
#     item_name: str
#     quantity: float = Field(..., gt=0, description="مقدار صفر سے زیادہ ہونی چاہیے")
#     requested_unit: str
#     created_date: Optional[date] = None

#     @field_validator("item_name")
#     def name_not_empty(cls, v):
#         if not v or not v.strip():
#             raise ValueError("آئٹم کا نام خالی نہیں ہو سکتا")
#         return v.strip()

#     # NO unit validation here → Any unit is accepted
#     # Conversion check will be done in CRUD layer


# class BillItemRead(BaseModel):
#     """Response schema"""
#     billitem_id: int
#     bill_id: Optional[int]=None
#     item_name: str
#     item_unit:str
#     unit_price: float
#     quantity: float
#     requested_unit: str
#     total_amount: float
#     created_date: date
#     billitem_day: str
#     billitem_month: str
#     billitem_year: str
#     billitem_time: str
#     billitem_day_name: str

#     model_config = ConfigDict(from_attributes=True)

    # bill_item_schemas.py

from pydantic import BaseModel, Field, ConfigDict, field_validator
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


class BillItemRead(BaseModel):
    """Response schema for individual bill items"""
    billitem_id: int
    bill_id: Optional[int] = None  # ✅ Already Optional
    item_name: str
    item_unit: str
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


# ✅ NEW SCHEMA: For cart items (same as BillItemRead but explicit)
class CartItemRead(BillItemRead):
    """Cart item response (same as BillItemRead but with bill_id=None)"""
    pass


# ✅ NEW SCHEMA: For adding item to cart
class AddToCartRequest(BaseModel):
    """Request to add item to cart"""
    item_name: str
    quantity: float = Field(..., gt=0)
    requested_unit: str


# ✅ NEW SCHEMA: For generating bill response
class GeneratedBillResponse(BaseModel):
    """Response after generating bill from cart"""
    bill_id: int
    customer_name: str
    total_amount: float
    status: str
    bill_date: date
    bill_day: str
    bill_month: str
    bill_year: str
    bill_time: str
    bill_day_name: str
    items: list[BillItemRead]
    message: str = "✅ بل کامیابی سے جنریٹ ہو گیا"


# ✅ NEW SCHEMA: For cart summary
class CartSummary(BaseModel):
    """Cart summary response"""
    total_items: int
    total_quantity: float
    total_amount: float
    items: list[CartItemRead]