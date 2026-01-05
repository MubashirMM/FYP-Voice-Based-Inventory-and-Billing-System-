# models/sales.py
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, ForeignKey, Date
from datetime import date
from myapp.database.session import Base
from sqlalchemy import String

class Sale(Base):
    __tablename__ = "sales"

    sale_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    customer_name: Mapped[str] = mapped_column(String, nullable=False)  # ✅ plain text name
    item_id: Mapped[int] = mapped_column(ForeignKey("items.item_id"))
    quantity_sold: Mapped[int] = mapped_column(Integer, nullable=False)
    dat: Mapped[date] = mapped_column(Date, default=date.today)
    item = relationship("Item", back_populates="sales")

    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    user = relationship("User", back_populates="sales")
