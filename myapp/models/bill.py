from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, Float, Date, String
from datetime import date
from myapp.database.session import Base

class Bill(Base):
    __tablename__ = "bills"

    bill_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customer.customer_id"), nullable=True,index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False)

    udhar_items_total: Mapped[float] = mapped_column(Float, default=0.0)
    direct_addition: Mapped[float] = mapped_column(Float, default=0.0)
    direct_deduction: Mapped[float] = mapped_column(Float, default=0.0)
    effective_total: Mapped[float] = mapped_column(Float, default=0.0)

    status: Mapped[str] = mapped_column(String(10), default="unpaid")
    bill_date: Mapped[date] = mapped_column(Date, default=date.today)
    
    # Urdu date/time fields - Bill specific
    bill_day: Mapped[str] = mapped_column(String(10), nullable=False, default="")
    bill_month: Mapped[str] = mapped_column(String(20), nullable=False, default="")
    bill_year: Mapped[str] = mapped_column(String(10), nullable=False, default="")
    bill_time: Mapped[str] = mapped_column(String(15), nullable=False, default="")
    bill_day_name: Mapped[str] = mapped_column(String(15), nullable=False, default="")

    items = relationship("BillItemHistory", back_populates="bill", cascade="all, delete-orphan")
    user = relationship("User", back_populates="bills")
    billitems = relationship("BillItem", back_populates="bill", cascade="all, delete-orphan")
