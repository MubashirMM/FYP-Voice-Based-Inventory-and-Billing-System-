# models/sales.py
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, ForeignKey, Date
from datetime import date
from myapp.database.session import Base

class Sale(Base):
    __tablename__ = "sales"

    sale_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customer.customer_id"))
    item_id: Mapped[int] = mapped_column(ForeignKey("items.item_id"))
    quantity_sold: Mapped[int] = mapped_column(Integer, nullable=False)  # in requested unit (normalized to item_unit)
    dat: Mapped[date] = mapped_column(Date, default=date.today)  # date-only

    customer = relationship("Customer", back_populates="sales")
    item = relationship("Item", back_populates="sales")
