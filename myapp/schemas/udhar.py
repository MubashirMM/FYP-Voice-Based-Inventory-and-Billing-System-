from pydantic import BaseModel, computed_field

class UdharRead(BaseModel):
    udhar_id: int
    customer_id: int
    total_amount: float
    status: str
    direct_addition: float  
    direct_deduction: float  

    class Config:
        from_attributes = True
