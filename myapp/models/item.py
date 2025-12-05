# models/item.py
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DECIMAL, Integer
from myapp.database.session import Base

class Item(Base):
    __tablename__ = "items"

    item_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    item_name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    item_unit: Mapped[str] = mapped_column(String(20), nullable=False)  # e.g., "kilo", "liter", "packet"
    unit_price: Mapped[float] = mapped_column(DECIMAL(10, 2), nullable=False)  # price per item_unit
    stock_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # inventory in item_unit units

    sales = relationship("Sale", back_populates="item")
    udharitems = relationship("UdharItem", back_populates="item")
