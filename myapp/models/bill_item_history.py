from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, Float, String
from myapp.database.session import Base

class BillItemHistory(Base):
    __tablename__ = "bill_item_history"

    history_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    bill_id: Mapped[int] = mapped_column(ForeignKey("bills.bill_id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False)

    item_name: Mapped[str] = mapped_column(String(50))
    unit_price: Mapped[float] = mapped_column(Float)
    quantity: Mapped[float] = mapped_column(Float)
    requested_unit: Mapped[str] = mapped_column(String(20))
    total_amount: Mapped[float] = mapped_column(Float)

    bill = relationship("Bill", back_populates="items")
    user = relationship("User", back_populates="bill_items")
