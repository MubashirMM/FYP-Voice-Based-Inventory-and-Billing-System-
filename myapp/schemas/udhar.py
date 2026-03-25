from pydantic import BaseModel, computed_field
from datetime import date

class UdharRead(BaseModel):
    udhar_id: int
    customer_id: int
    customer_name: str   # ✅ include name
    subtotal: float
    direct_addition: float
    direct_deduction: float
    total: float
    status: str
    created_date: date | None
    paid_date: date | None

    # Urdu formatted dates
    @computed_field
    @property
    def created_date_urdu(self) -> str:
        from myapp.utils.urdu_date import format_full_date_urdu
        return format_full_date_urdu(self.created_date)

    @computed_field
    @property
    def paid_date_urdu(self) -> str:
        from myapp.utils.urdu_date import format_full_date_urdu
        return format_full_date_urdu(self.paid_date)

    class Config:
        from_attributes = True
