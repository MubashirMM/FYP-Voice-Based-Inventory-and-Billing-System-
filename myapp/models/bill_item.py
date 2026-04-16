# from sqlalchemy.orm import Mapped, mapped_column, relationship
# from sqlalchemy import Integer, Float, ForeignKey, String, Date
# from datetime import date
# from myapp.database.session import Base

# class BillItem(Base):
#     __tablename__ = "billitems"

#     billitem_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

#     bill_id: Mapped[int] = mapped_column(ForeignKey("bills.bill_id"))

#     # ✅ OPTIONAL FK
#     item_id: Mapped[int] = mapped_column(
#         ForeignKey("items.item_id", ondelete="SET NULL"),
#         nullable=True
#     )

#     # ✅ SNAPSHOT (REQUIRED)
#     item_name: Mapped[str] = mapped_column(String(100), nullable=False)

#     unit_price: Mapped[float] = mapped_column(Float, nullable=False)
#     quantity: Mapped[float] = mapped_column(Float, nullable=False)
#     requested_unit: Mapped[str] = mapped_column(String(20), nullable=False)
#     total_amount: Mapped[float] = mapped_column(Float, nullable=False)

#     # Optional (recommended)
#     item_unit: Mapped[str] = mapped_column(String(20), nullable=True)

#     created_date: Mapped[date] = mapped_column(Date, default=date.today)

#     # Urdu date/time
#     billitem_day: Mapped[str] = mapped_column(String(10), default="")
#     billitem_month: Mapped[str] = mapped_column(String(20), default="")
#     billitem_year: Mapped[str] = mapped_column(String(10), default="")
#     billitem_time: Mapped[str] = mapped_column(String(15), default="")
#     billitem_day_name: Mapped[str] = mapped_column(String(15), default="")

#     user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False)

#     # Relationships (no dependency)
#     bill = relationship("Bill", back_populates="billitems")
#     item = relationship("Item", back_populates="billitems")
#     user = relationship("User", back_populates="billitems")


from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, Float, ForeignKey, String, Date
from datetime import date
from myapp.database.session import Base

class BillItem(Base):
    __tablename__ = "billitems"

    billitem_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # ✅ MAKE bill_id NULLABLE (for cart items without a bill)
    bill_id: Mapped[int] = mapped_column(ForeignKey("bills.bill_id"), nullable=True)  # Changed to nullable=True

    # ✅ OPTIONAL FK
    item_id: Mapped[int] = mapped_column(
        ForeignKey("items.item_id", ondelete="SET NULL"),
        nullable=True
    )

    # ✅ SNAPSHOT (REQUIRED)
    item_name: Mapped[str] = mapped_column(String(100), nullable=False)

    unit_price: Mapped[float] = mapped_column(Float, nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    requested_unit: Mapped[str] = mapped_column(String(20), nullable=False)
    total_amount: Mapped[float] = mapped_column(Float, nullable=False)

    # Optional (recommended)
    item_unit: Mapped[str] = mapped_column(String(20), nullable=True)

    created_date: Mapped[date] = mapped_column(Date, default=date.today)

    # Urdu date/time
    billitem_day: Mapped[str] = mapped_column(String(10), default="")
    billitem_month: Mapped[str] = mapped_column(String(20), default="")
    billitem_year: Mapped[str] = mapped_column(String(10), default="")
    billitem_time: Mapped[str] = mapped_column(String(15), default="")
    billitem_day_name: Mapped[str] = mapped_column(String(15), default="")

    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    
    # ✅ NEW FIELD: Track if item is in cart or billed
    is_pending: Mapped[int] = mapped_column(default=1)  # 1 = in cart, 0 = billed
    base_quantity: Mapped[float] = mapped_column(Float, nullable=True)  # Store converted quantity

    # Relationships (no dependency)
    bill = relationship("Bill", back_populates="billitems")
    item = relationship("Item", back_populates="billitems")
    user = relationship("User", back_populates="billitems")