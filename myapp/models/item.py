from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, DECIMAL, Integer
from myapp.database.session import Base

class Item(Base):
    __tablename__ = "items"   # ✅ lowercase plural is best practice

    item_id: Mapped[int] = mapped_column(primary_key=True)
    item_name: Mapped[str] = mapped_column(String(50))
    item_unit: Mapped[str] = mapped_column(String(50))
    unit_price: Mapped[float] = mapped_column(DECIMAL(10, 2))
    stock_quantity: Mapped[int] = mapped_column(Integer)
