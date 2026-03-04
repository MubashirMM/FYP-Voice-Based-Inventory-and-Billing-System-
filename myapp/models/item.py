# models/item.py
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DECIMAL, Integer,ForeignKey,UniqueConstraint
from myapp.database.session import Base
from sqlalchemy import Float
from datetime import date
from sqlalchemy import Date
class Item(Base):
    __tablename__ = "items"

    item_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id:Mapped[int]=mapped_column(ForeignKey("users.user_id"),nullable=True)
    item_name: Mapped[str] = mapped_column(String(50), nullable=False)
    item_unit: Mapped[str] = mapped_column(String(20), nullable=False)  # e.g., "kilo", "liter", "packet"
    unit_price: Mapped[float] = mapped_column(DECIMAL(10, 2), nullable=False)  # price per item_unit
    stock_quantity: Mapped[int] = mapped_column(Float, nullable=False, default=0.0)  # inventory in item_unit units
    created_date: Mapped[date] = mapped_column(Date, default=date.today)

    sales = relationship("Sale", back_populates="item")
    udharitems = relationship("UdharItem", back_populates="item")
    __table_args__ = (
        UniqueConstraint("item_name", "user_id", name="uq_item_name_per_user"),
    ) 

    owner = relationship("User", back_populates="items")
    billitems = relationship("BillItem", back_populates="item", cascade="all, delete-orphan")

