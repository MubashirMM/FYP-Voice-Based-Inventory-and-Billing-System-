from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, Float, ForeignKey, String, Date
from datetime import date
from myapp.database.session import Base

class BillItem(Base):
    __tablename__ = "billitems"

    @property 
    def item_name(self): 
        return self.item.item_name if self.item else None

    billitem_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    bill_id: Mapped[int] = mapped_column(ForeignKey("bills.bill_id"))
    item_id: Mapped[int] = mapped_column(ForeignKey("items.item_id"))

    unit_price: Mapped[float] = mapped_column(Float, nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    requested_unit: Mapped[str] = mapped_column(String(20), nullable=False)
    total_amount: Mapped[float] = mapped_column(Float, nullable=False)
    created_date: Mapped[date] = mapped_column(Date, default=date.today)
    
    # Urdu date/time fields - BillItem specific
    billitem_day: Mapped[str] = mapped_column(String(10), nullable=False, default="")
    billitem_month: Mapped[str] = mapped_column(String(20), nullable=False, default="")
    billitem_year: Mapped[str] = mapped_column(String(10), nullable=False, default="")
    billitem_time: Mapped[str] = mapped_column(String(15), nullable=False, default="")
    billitem_day_name: Mapped[str] = mapped_column(String(15), nullable=False, default="")

    # User scoping
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    # Relationships
    bill = relationship("Bill", back_populates="billitems")
    item = relationship("Item", back_populates="billitems", lazy="joined")
    user = relationship("User", back_populates="billitems")
