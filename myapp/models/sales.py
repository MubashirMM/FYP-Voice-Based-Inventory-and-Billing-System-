from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, ForeignKey, Date, String, Float
from datetime import date
from myapp.database.session import Base

class Sale(Base):
    __tablename__ = "sales"

    sale_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    customer_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # ✅ OPTIONAL FK - SET NULL on delete
    item_id: Mapped[int] = mapped_column(
        ForeignKey("items.item_id", ondelete="SET NULL"),
        nullable=True
    )

    # ✅ SNAPSHOT (MOST IMPORTANT) - ALWAYS PRESERVED
    item_name: Mapped[str] = mapped_column(String(100), nullable=False)

    quantity_sold: Mapped[float] = mapped_column(Float, nullable=False)

    # Optional but recommended
    unit_price: Mapped[float] = mapped_column(Float, nullable=True)
    item_unit: Mapped[str] = mapped_column(String(20), nullable=True)

    sale_date: Mapped[date] = mapped_column(Date, default=date.today)

    # Urdu date/time
    sale_day: Mapped[str] = mapped_column(String(10), default="")
    sale_month: Mapped[str] = mapped_column(String(20), default="")
    sale_year: Mapped[str] = mapped_column(String(10), default="")
    sale_time: Mapped[str] = mapped_column(String(15), default="")
    sale_day_name: Mapped[str] = mapped_column(String(15), default="")

    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False)

    # Relationships (SAFE)
    item = relationship("Item", back_populates="sales", foreign_keys=[item_id])
    user = relationship("User", back_populates="sales")