# models/udhar_item.py
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, ForeignKey, Float, Date, String
from datetime import date
from myapp.database.session import Base

class UdharItem(Base):
    __tablename__ = "udharitems"

    udharitem_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    udhar_id: Mapped[int] = mapped_column(ForeignKey("udhars.udhar_id"), nullable=False)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customer.customer_id"))

    # ✅ OPTIONAL FK (can be NULL)
    item_id: Mapped[int] = mapped_column(
        ForeignKey("items.item_id", ondelete="SET NULL"),
        nullable=True
    )

    # ✅ SNAPSHOT (THIS FIXES EVERYTHING)
    item_name: Mapped[str] = mapped_column(String(100), nullable=False)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False)

    unit_price: Mapped[float] = mapped_column(Float, nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    requested_unit: Mapped[str] = mapped_column(String(20), nullable=False)
    base_unit: Mapped[str] = mapped_column(String(20), nullable=False)
    total_amount: Mapped[float] = mapped_column(Float, nullable=False)

    created_date: Mapped[date] = mapped_column(Date, default=date.today)

    # Urdu date/time
    udhar_day: Mapped[str] = mapped_column(String(10), default="")
    udhar_month: Mapped[str] = mapped_column(String(20), default="")
    udhar_year: Mapped[str] = mapped_column(String(10), default="")
    udhar_time: Mapped[str] = mapped_column(String(15), default="")
    udhar_day_name: Mapped[str] = mapped_column(String(15), default="")

    # Relationships (SAFE now)
    customer = relationship("Customer", back_populates="udharitems")
    item = relationship("Item", back_populates="udharitems")
    user = relationship("User", back_populates="udharitems")
    udhar = relationship("Udhar", back_populates="udharitems")