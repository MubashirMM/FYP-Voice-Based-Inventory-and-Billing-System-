# models/sales.py
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, ForeignKey, Date, String
from datetime import date
from myapp.database.session import Base

class Sale(Base):
    __tablename__ = "sales"

    sale_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    customer_name: Mapped[str] = mapped_column(String, nullable=False)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.item_id"))
    quantity_sold: Mapped[int] = mapped_column(Integer, nullable=False)

    # Original date field (kept for compatibility)
    sale_date: Mapped[date] = mapped_column(Date, default=date.today)
    
    # Urdu date/time fields
    sale_day: Mapped[str] = mapped_column(String(10), nullable=False, default="")
    sale_month: Mapped[str] = mapped_column(String(20), nullable=False, default="")
    sale_year: Mapped[str] = mapped_column(String(10), nullable=False, default="")
    sale_time: Mapped[str] = mapped_column(String(15), nullable=False, default="")
    sale_day_name: Mapped[str] = mapped_column(String(15), nullable=False, default="")
    
    item = relationship("Item", back_populates="sales")
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    user = relationship("User", back_populates="sales")
