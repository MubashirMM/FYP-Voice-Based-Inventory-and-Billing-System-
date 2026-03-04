from sqlalchemy import Date, Integer, Float, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from myapp.database.session import Base
from datetime import date

class Udhar(Base):
    __tablename__ = "udhars"

    udhar_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customer.customer_id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False)

    subtotal: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    direct_addition: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    direct_deduction: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    total: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    status: Mapped[str] = mapped_column(String(20), nullable=False, default="unpaid")

    created_date: Mapped[date] = mapped_column(Date, default=date.today)
    paid_date: Mapped[date] = mapped_column(Date, nullable=True)

    # Urdu date/time fields
    udhar_day: Mapped[str] = mapped_column(String(10), default="")
    udhar_month: Mapped[str] = mapped_column(String(20), default="")
    udhar_year: Mapped[str] = mapped_column(String(10), default="")
    udhar_time: Mapped[str] = mapped_column(String(15), default="")
    udhar_day_name: Mapped[str] = mapped_column(String(15), default="")

    paid_day: Mapped[str] = mapped_column(String(10), default="")
    paid_month: Mapped[str] = mapped_column(String(20), default="")
    paid_year: Mapped[str] = mapped_column(String(10), default="")
    paid_time: Mapped[str] = mapped_column(String(15), default="")
    paid_day_name: Mapped[str] = mapped_column(String(15), default="")

    customer = relationship("Customer", back_populates="udhar")
    user = relationship("User", back_populates="udhars")
    udharitems = relationship("UdharItem", back_populates="udhar", cascade="all, delete-orphan")

    def calculate_totals(self):
        """Recalculate subtotal and total based on items and adjustments"""
        self.subtotal = sum(item.total_amount for item in self.udharitems)
        self.total = self.subtotal + self.direct_addition - self.direct_deduction
