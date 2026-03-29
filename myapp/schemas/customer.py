from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional

class CustomerCreate(BaseModel):
    customer_name: str
    
    @field_validator("customer_name")
    def name_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("گاہک کا نام خالی نہیں ہو سکتا")
        return v.strip()

class CustomerUpdate(BaseModel):
    customer_name: Optional[str] = None
    
    @field_validator("customer_name")
    def name_not_empty(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError("گاہک کا نام خالی نہیں ہو سکتا")
        return v.strip() if v else v

class CustomerRead(BaseModel):
    customer_id: int
    customer_name: str
    user_id: int
    
    model_config = ConfigDict(from_attributes=True)