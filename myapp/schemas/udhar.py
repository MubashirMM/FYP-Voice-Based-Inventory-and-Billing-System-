from pydantic import BaseModel, computed_field

class UdharRead(BaseModel):
    udhar_id: int
    customer_id: int
    total_amount: float
    status: str
    direct_addition: float  
    direct_deduction: float  
    
    @computed_field
    @property
    def effective_total(self) -> float:
        """Calculate effective total including direct operations"""
        return self.total_amount + self.direct_addition - self.direct_deduction
    
    @computed_field
    @property
    def effective_status(self) -> str:
        """Status based on effective total"""
        effective_total = self.total_amount + self.direct_addition - self.direct_deduction
        return "paid" if effective_total == 0 else "unpaid"

    class Config:
        from_attributes = True