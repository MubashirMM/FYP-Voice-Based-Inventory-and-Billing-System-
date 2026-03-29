from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DECIMAL, Integer, ForeignKey, UniqueConstraint
from myapp.database.session import Base
from sqlalchemy import Float
from datetime import date
from sqlalchemy import Date

class Item(Base):
    __tablename__ = "items"

    item_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id"),
        nullable=False
    )

    item_name: Mapped[str] = mapped_column(String(50), nullable=False)
    item_unit: Mapped[str] = mapped_column(String(20), nullable=False)
    unit_price: Mapped[float] = mapped_column(DECIMAL(10, 2), nullable=False)
    stock_quantity: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    created_date: Mapped[date] = mapped_column(Date, default=date.today)

    # Relationships with SET NULL on delete
    sales = relationship("Sale", back_populates="item", foreign_keys="Sale.item_id")
    udharitems = relationship("UdharItem", back_populates="item", foreign_keys="UdharItem.item_id")
    billitems = relationship("BillItem", back_populates="item", foreign_keys="BillItem.item_id")

    owner = relationship("User", back_populates="items")

    __table_args__ = (
        UniqueConstraint("item_name", "user_id", name="uq_item_name_per_user"),
    )